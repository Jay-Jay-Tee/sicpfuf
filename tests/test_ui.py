"""Local UI tests without binding a port, so they work in restricted runners."""

import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sicpfuf.__main__ import main
from sicpfuf.ui import make_handler, run_trace, serve


class Request:
    def __init__(self, data):
        self.input = io.BytesIO(data)
        self.output = io.BytesIO()

    def makefile(self, *args, **kwargs):
        return self.input

    def sendall(self, data):
        self.output.write(data)


class UITests(unittest.TestCase):
    def request(self, path, data=None, origin=None, host="127.0.0.1:8765"):
        body = json.dumps(data).encode() if data is not None else b""
        headers = [f"{'POST' if data is not None else 'GET'} {path} HTTP/1.0", f"Host: {host}"]
        if origin:
            headers.append("Origin: " + origin)
        if body:
            headers.extend(["Content-Type: application/json", "Content-Length: " + str(len(body))])
        request = Request(("\r\n".join(headers) + "\r\n\r\n").encode() + body)
        make_handler({"source": "print(7)", "chapter": 2, "mode": "environment", "filename": "demo.py"})(
            request, ("127.0.0.1", 12345), SimpleNamespace(server_address=("127.0.0.1", 8765)))
        header, content = request.output.getvalue().split(b"\r\n\r\n", 1)
        return int(header.split()[1]), content

    def test_serves_ui_assets_and_initial_program(self):
        for path in ("/", "/ui.js", "/ui.css", "/api/session"):
            with self.subTest(path=path):
                status, body = self.request(path)
                self.assertEqual(status, 200)
                self.assertTrue(body)
        _, body = self.request("/api/session")
        self.assertEqual(json.loads(body)["source"], "print(7)")

    def test_only_ui_assets_are_served(self):
        self.assertEqual(self.request("/../README.md")[0], 404)
        self.assertEqual(self.request("/examples.json")[0], 404)

    def test_rejects_unrelated_origins_and_hosts(self):
        self.assertEqual(self.request("/api/session", origin="https://unrelated.test")[0], 403)
        self.assertEqual(self.request("/", host="unrelated.test:8765")[0], 403)

    def test_trace_api_uses_isolated_interpreter(self):
        status, body = self.request("/api/trace", {"source": "print(6 * 7)", "chapter": 2, "mode": "environment"})
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["steps"][-1]["output"], "42\n")

    def test_request_validation(self):
        for data in ({}, [], {"source": 7},
                     {"source": "", "chapter": True, "mode": "environment"},
                     {"source": "", "chapter": 2, "mode": "unknown"}):
            with self.subTest(data=data):
                self.assertEqual(self.request("/api/trace", data)[0], 400)

    def test_both_models_and_fresh_runs(self):
        for mode in ("environment", "substitution"):
            result = run_trace("def f(x):\n    return x * x\nprint(f(3))\n", 2, mode)
            self.assertIsNone(result["error"])
            self.assertEqual(result["steps"][-1]["output"], "9\n")
        run_trace("x = 7\n", 2, "environment")
        self.assertIsNotNone(run_trace("print(x)\n", 2, "environment")["error"])

    def test_timeout_is_reported(self):
        with patch("sicpfuf.ui.subprocess.run", side_effect=subprocess.TimeoutExpired("trace", 10)):
            self.assertIn("10 seconds", run_trace("", 2, "environment")["error"])

    def test_program_input_in_both_models(self):
        for mode in ("environment", "substitution"):
            with self.subTest(mode=mode):
                result = run_trace('name = input("Name: ")\nprint(name)\n', 2, mode, "Ada\n")
                self.assertIsNone(result["error"])
                self.assertEqual(result["steps"][-1]["output"], "Name: Ada\n")

    def test_typed_trace_checks_before_execution(self):
        result = run_trace('print("should not run")\nx: int = "wrong"\n', 4, "environment", typed=True)
        self.assertIn("StaticTypeError", result["error"])
        self.assertEqual(result["steps"][-1]["output"], "")
        good = run_trace('def square(x: int) -> int:\n    return x * x\nprint(square(3))\n', 4, "environment", typed=True)
        self.assertIsNone(good["error"])
        self.assertEqual(good["steps"][-1]["output"], "9\n")

    def test_typed_api_rejects_other_chapters_and_substitution(self):
        for chapter, mode in ((2, "environment"), (4, "substitution")):
            status, body = self.request("/api/trace", {"source": "", "chapter": chapter, "mode": mode, "typed": True})
            self.assertEqual(status, 400)

    def test_cli_opens_ui_without_entering_repl(self):
        with patch("sicpfuf.ui.serve", return_value=0) as opened:
            self.assertEqual(main(["--ui", "--no-browser"]), 0)
        self.assertEqual(opened.call_args.args, (None, None, 2, "environment"))
        self.assertEqual(opened.call_args.kwargs, {"port": 0, "open_browser": False, "typed": False})

    def test_cli_loads_file_and_chapter(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "test.py"
            path.write_text("# chapter 3\nprint(7)\n")
            with patch("sicpfuf.ui.serve", return_value=0) as opened:
                self.assertEqual(main(["--ui", str(path), "--no-browser", "--port", "8765"]), 0)
            self.assertEqual(opened.call_args.args[:3], (path.read_text(), str(path), 3))

    def test_cli_selects_substitution(self):
        with patch("sicpfuf.ui.serve", return_value=0) as opened:
            self.assertEqual(main(["--ui", "--subst", "-c", "print(7)"]), 0)
        self.assertEqual(opened.call_args.args, ("print(7)", "<string>", 2, "substitution"))

    def test_cli_opens_typed_interfaces(self):
        with patch("sicpfuf.ui.serve", return_value=0) as opened:
            self.assertEqual(main(["--ui", "--typed", "-c", "x: int = 1"]), 0)
        self.assertEqual(opened.call_args.args[2], 4)
        self.assertTrue(opened.call_args.kwargs["typed"])
        with patch("sicpfuf.ui.terminal.start", return_value=0) as opened:
            self.assertEqual(main(["--tui", "--typed", "-c", "x: int = 1"]), 0)
        self.assertEqual(opened.call_args.args[2], 4)
        self.assertTrue(opened.call_args.kwargs["typed"])

    def test_ui_only_flags_require_browser_ui(self):
        for arguments in (["--no-browser"], ["--tui", "--port", "8765"], ["--ui", "--tui"]):
            with self.subTest(arguments=arguments), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as result:
                    main(arguments)
                self.assertEqual(result.exception.code, 2)

    def test_cli_reports_unavailable_port(self):
        with patch("sicpfuf.ui.serve", side_effect=OSError("port unavailable")), contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertEqual(main(["--ui", "--no-browser"]), 2)
        self.assertIn("port unavailable", err.getvalue())

    def test_cli_rejects_substitution_with_state(self):
        with contextlib.redirect_stderr(io.StringIO()) as err:
            with self.assertRaises(SystemExit) as result:
                main(["--ui", "--subst", "-v", "3"])
        self.assertEqual(result.exception.code, 2)
        self.assertIn("use --estep", err.getvalue())

    def test_server_closes_on_ctrl_c(self):
        with patch("sicpfuf.ui.ThreadingHTTPServer") as server_class, patch("sicpfuf.ui.webbrowser.open") as browser:
            server = server_class.return_value
            server.server_address = ("127.0.0.1", 8765)
            server.serve_forever.side_effect = KeyboardInterrupt
            with contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(serve(open_browser=False), 0)
            browser.assert_not_called()
            server.server_close.assert_called_once()
            self.assertIn("http://127.0.0.1:8765/", out.getvalue())


if __name__ == "__main__":
    unittest.main()
