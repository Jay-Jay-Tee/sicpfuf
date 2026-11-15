"""Keep editor declarations aligned with the interpreter's public names."""
import ast
import builtins
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from sicpfuf.interpreter import Interpreter


def names(path):
    tree = ast.parse(path.read_text())
    return {node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))} | {
        node.target.id for node in tree.body if isinstance(node, ast.AnnAssign)}


class EditorHintsTests(unittest.TestCase):
    def test_extra_builtins_have_editor_declarations(self):
        interp = Interpreter(4)
        public = {name for name in set(interp.builtins_env.vars) | set(interp.library_env.vars)
                  if not name.startswith("_") and name not in vars(builtins)}
        self.assertTrue(public <= names(ROOT / "typings/__builtins__.pyi"))

    def test_module_exports_have_editor_declarations(self):
        interp = Interpreter(4)
        for module in ("rune", "curve", "sound", "repeat"):
            with self.subTest(module=module):
                self.assertEqual(set(interp.lib.load_module(interp, module)),
                                 names(ROOT / "typings" / module / "__init__.pyi"))


if __name__ == "__main__":
    unittest.main()
