"""CLI modes must honour their advertised language and never skip checking silently."""

from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CLITests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, "-m", "sicpfuf", *args], cwd=ROOT,
                              input="", text=True, capture_output=True, timeout=10)

    def test_typed_prompt_is_rejected_instead_of_becoming_untyped(self):
        result = self.run_cli("--typed")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("interactive prompt does not support typed checking", result.stderr)

    def test_typed_rejects_incompatible_modes_before_execution(self):
        for flags in (("--chapter", "1"), ("--subst",)):
            with self.subTest(flags=flags):
                result = self.run_cli("--typed", *flags, "-c", 'print("must not run")')
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertIn("--typed requires Python §4", result.stderr)

    def test_typed_selects_chapter_four_over_a_file_header(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "example.py"
            path.write_text("# chapter 1\nxs: list[int] = [1, 2]\nprint(xs[0])\n")
            result = self.run_cli("--typed", str(path))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "1\n")


if __name__ == "__main__":
    unittest.main()
