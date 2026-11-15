import io
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sicpfuf.interpreter import Interpreter
from sicpfuf.modules.rune_module import terminal_colour


class Terminal(io.StringIO):
    def isatty(self):
        return True


class ModuleTests(unittest.TestCase):
    def test_coloured_terminal_runes(self):
        out = Terminal()
        with patch.dict(os.environ, {"TERM": "xterm-256color"}, clear=True):
            Interpreter(1, out=out).run_source("from rune import show, red, blue, square, stack\nshow(stack(red(square), blue(square)))\n")
        self.assertIn("\033[48;2;244;67;54m", out.getvalue())
        self.assertIn("\033[48;2;33;150;243m", out.getvalue())
        self.assertIn("\033[0m│", out.getvalue())

    def test_captured_output_stays_plain(self):
        out = io.StringIO()
        Interpreter(1, out=out).run_source("from rune import show, red, square\nshow(red(square))\n")
        self.assertNotIn("\033[", out.getvalue())
        self.assertIn("█", out.getvalue())

    def test_no_color_and_dumb_terminals(self):
        with patch.dict(os.environ, {"NO_COLOR": ""}, clear=True):
            self.assertFalse(terminal_colour(Terminal()))
        with patch.dict(os.environ, {"TERM": "dumb"}, clear=True):
            self.assertFalse(terminal_colour(Terminal()))

    def test_repeat_module_matches_documented_combinators(self):
        out = io.StringIO()
        Interpreter(1, out=out).run_source('''from repeat import repeat, repeat_apply, twice, thrice
def add_two(x):
    return x + 2
print(repeat(add_two, 0)(7))
print(repeat(add_two, 4)(1))
print(repeat_apply(add_two, 4, 1))
print(twice(add_two)(1), thrice(add_two)(1))
''')
        self.assertEqual(out.getvalue(), "7\n9\n9\n5 7\n")


if __name__ == "__main__":
    unittest.main()
