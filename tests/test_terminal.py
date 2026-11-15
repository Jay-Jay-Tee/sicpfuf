import contextlib
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sicpfuf.ui.terminal import model_lines, source_rows, start
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
        self.assertTrue(text.startswith("E1  [current]"))
        program = '\n'.join(model_lines(step, 'environment', view='program'))
        self.assertTrue(program.startswith('REMAINING PROGRAM'))
        self.assertIn('E1 ⟦', program)

    def test_code_wraps_without_losing_long_lines(self):
        source = "def f(x):\n    return x if x == 0 else f(x - 1)\n"
        rows = source_rows(source, 2, 18, 20)
        joined = "".join(text[4:] for number, text in rows if number == 2)
        self.assertEqual(joined, source.splitlines()[1])

    def test_fibonacci_example_finishes_with_configured_limit(self):
        program = "def fib_iter(a, b, count):\n    return b if count == 0 else fib_iter(a + b, a, count - 1)\ndef fast_fib(n):\n    return fib_iter(1, 0, n)\nprint(fast_fib(10), fast_fib(20), fast_fib(100))\n"
        small = trace(program, 4, graphics=False)
        self.assertIn("250 steps", small["error"])
        complete = trace(program, 4, graphics=False, max_steps=4000)
        self.assertIsNone(complete["error"])
        self.assertEqual(complete["steps"][-1]["output"], "55 6765 354224848179261915075\n")

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
