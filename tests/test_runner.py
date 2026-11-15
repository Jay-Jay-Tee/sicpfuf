"""Regression checks for cases that the test runner itself must not accept."""
import contextlib
import importlib.util
import io
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("sicpfuf_test_runner", Path(__file__).with_name("run_tests.py"))
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class RunnerTests(unittest.TestCase):
    def test_silent_crash_is_not_a_successful_empty_program(self):
        with patch.object(runner, "run", return_value=(-11, "", "")):
            result = runner.run_case(["python3"], 1, "x = 1\n")
        self.assertEqual(result["error"], "ProcessExit(-11)")

    def test_missing_snapshot_fails_without_writing_one(self):
        with TemporaryDirectory() as folder:
            script = Path(folder) / "example.py"
            script.write_text("print(7)\n")
            with patch.object(runner, "ROOT", folder), patch.object(runner, "EXPECTED", str(Path(folder) / "expected.json")), \
                 patch.object(runner, "load_cases", return_value=[]), \
                 patch.object(runner.glob, "glob", side_effect=lambda pattern: [str(script)] if "xray" in pattern else []), \
                 patch.object(runner, "run", return_value=(0, "7\n", "")), \
                 patch.object(sys, "argv", ["run_tests.py"]), contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(runner.main(), 1)
            self.assertIn("no expected output recorded", out.getvalue())
            self.assertFalse(script.with_suffix(".expected").exists())


if __name__ == "__main__":
    unittest.main()
