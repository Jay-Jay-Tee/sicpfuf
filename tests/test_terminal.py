import contextlib
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sicpfuf.ui.terminal import model_lines, start
from sicpfuf.xray.playground import trace


class TerminalTests(unittest.TestCase):
    def test_model_contains_frames_bindings_and_closures(self):
        history = trace("def f(x):\n    return x + 1\nprint(f(2))\n", 2)
        step = next(s for s in history["steps"] if s["message"].startswith("Called f"))
        text = "\n".join(model_lines(step, "environment"))
        self.assertIn("E1  [current]", text)
        self.assertIn("x = 2", text)
        self.assertIn("enclosing -> global env", text)
        self.assertIn("FUNCTION OBJECTS", text)

    def test_substitution_and_errors(self):
        step = trace("print(2 + 3)\n", 1, "substitution")["steps"][1]
        text = "\n".join(model_lines(step, "substitution", "test error"))
        self.assertIn("EXPRESSION", text)
        self.assertIn("ERROR\ntest error", text)

    def test_noninteractive_launch_fails_with_help(self):
        with patch("sys.stdin", io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as out:
            self.assertEqual(start(), 2)
        self.assertIn("interactive terminal", out.getvalue())


if __name__ == "__main__":
    unittest.main()
