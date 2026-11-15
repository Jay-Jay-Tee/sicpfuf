"""The built-in stepper UI. Python's standard library is all it needs."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import subprocess
import sys
import webbrowser

ASSETS = Path(__file__).parent
MAX_REQUEST = 100_000
DEFAULT_SOURCE = "def square(x):\n    return x * x\n\nprint(square(2 + 1))\n"


def run_trace(source, chapter, mode):
    """A fresh subprocess bounds expensive operations as well as interpreter steps."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "sicpfuf.ui", "--trace"],
            input=json.dumps({"source": source, "chapter": chapter, "mode": mode}),
            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd=str(ASSETS.parents[1]), timeout=10,
        )
    except subprocess.TimeoutExpired:
        return {"steps": [], "error": "Stopped after 10 seconds. Try a smaller program."}
    if result.returncode:
        return {"steps": [], "error": "The stepper could not finish: " + result.stderr[-2000:]}
    return json.loads(result.stdout)


def make_handler(session):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

        def send(self, status, body, content_type="application/json; charset=utf-8"):
            if isinstance(body, (dict, list)):
                body = json.dumps(body)
            if isinstance(body, str):
                body = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def local_request(self):
            host = "127.0.0.1:" + str(self.server.server_address[1])
            if self.headers.get("Host") != host or self.headers.get("Origin", "http://" + host) != "http://" + host:
                self.send(403, {"error": "Open the local URL printed by sicpfuf."})
                return False
            return True

        def do_GET(self):
            if not self.local_request():
                return
            path = self.path.split("?", 1)[0]
            if path == "/api/session":
                self.send(200, session)
                return
            assets = {"/": ("index.html", "text/html; charset=utf-8"),
                      "/ui.js": ("ui.js", "text/javascript; charset=utf-8"),
                      "/ui.css": ("ui.css", "text/css; charset=utf-8")}
            if path not in assets:
                self.send(404, {"error": "Not found"})
                return
            filename, content_type = assets[path]
            self.send(200, (ASSETS / filename).read_bytes(), content_type)

        def do_POST(self):
            if not self.local_request():
                return
            if self.path != "/api/trace":
                self.send(404, {"error": "Not found"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= MAX_REQUEST:
                    raise ValueError("Use a program smaller than 100 KB.")
                if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                    raise ValueError("Expected a JSON request.")
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict) or not isinstance(data.get("source"), str):
                    raise ValueError("Expected source code.")
                chapter, mode = data.get("chapter"), data.get("mode")
                if type(chapter) is not int or chapter not in (1, 2, 3, 4):
                    raise ValueError("Choose Python §1, §2, §3 or §4.")
                if mode not in ("environment", "substitution"):
                    raise ValueError("Choose the environment or substitution stepper.")
            except (ValueError, UnicodeError) as exc:
                self.send(400, {"error": str(exc)})
                return
            self.send(200, run_trace(data["source"], chapter, mode))

    return Handler


def serve(source=None, filename=None, chapter=2, mode="environment", port=0, open_browser=True):
    session = {"source": DEFAULT_SOURCE if source is None else source,
               "filename": filename or "Untitled", "chapter": chapter, "mode": mode}
    server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(session))
    server.daemon_threads = True
    url = "http://127.0.0.1:" + str(server.server_address[1]) + "/"
    print("sicpfuf stepper: " + url, flush=True)
    print("Ctrl-C stops the UI. Edits in the UI do not change your file.", flush=True)
    if open_browser:
        try:
            webbrowser.open(url)
        except webbrowser.Error:
            pass  # the printed URL still works on machines without a browser command
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStepper closed.")
    finally:
        server.server_close()
    return 0
