"""Tree output is a program representation, usable without opening the UI."""
import io
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from sicpfuf.interpreter import Interpreter
from sicpfuf.xray.treedrawing import TreeDrawing, draw, MAX_NODES


def llist(*values):
    result = None
    for value in reversed(values):
        result = [value, result]
    return result


class TreeDrawingTests(unittest.TestCase):
    def test_nested_llists_have_branches_and_leaves(self):
        value = llist(1, llist(2, 3), 4)
        picture = TreeDrawing(value)
        self.assertEqual(picture.text(), 'llist\n├── 1\n├── llist\n│   ├── 2\n│   └── 3\n└── 4')
        root = ET.fromstring(picture.svg())
        self.assertEqual(len([node for node in root.iter() if node.tag.endswith('title')]), 6)
        self.assertEqual(value, llist(1, llist(2, 3), 4))

    def test_binary_nodes_keep_left_right_and_empty_branches(self):
        value = llist(8, llist(3, None, None), None)
        self.assertEqual(draw(value, 'binary'),
                         '8\n├── left: 3\n│   ├── left: ∅\n│   └── right: ∅\n└── right: ∅')
        self.assertEqual(draw(None), '∅')
        with self.assertRaisesRegex(ValueError, 'expects llist'):
            draw(llist(1, 2), 'binary')
        with self.assertRaisesRegex(ValueError, 'expects llist'):
            draw(llist(1, 2, None), 'binary')

    def test_sharing_and_cycles_have_references_instead_of_duplicate_trees(self):
        branch = llist(2, 3)
        text = draw(llist(branch, branch))
        self.assertEqual(text.count('├── 2'), 1)
        self.assertEqual(text.count('[#1]'), 1)
        self.assertIn('↪ #1 (shared)', text)
        cycle = [1, None]
        cycle[1] = cycle
        self.assertEqual(draw(cycle), 'pair [#1]\n├── head: 1\n└── tail: ↪ #1 (cycle)')
        self.assertIs(cycle[1], cycle)

    def test_shared_tail_is_shown_explicitly(self):
        suffix = llist(7, 8)
        text = draw(llist(suffix, [6, suffix]))
        self.assertIn('tail: ↪ #1 (shared)', text)
        self.assertEqual(text.count('├── 7'), 1)

    def test_large_or_deep_structures_are_abbreviated(self):
        wide = TreeDrawing(llist(*range(2000)))
        self.assertEqual(wide.count, MAX_NODES)
        self.assertIn('node limit', wide.text())
        deep = 1
        for _ in range(1000):
            deep = llist(deep)
        self.assertIn('depth/traversal limit', draw(deep))

    def test_svg_labels_are_escaped(self):
        picture = ET.fromstring(TreeDrawing(llist('<script>alert(1)</script>')).svg())
        self.assertFalse(any(node.tag.endswith('script') for node in picture.iter()))
        self.assertIn('<script>', ''.join(picture.itertext()))

    def test_cli_exports_tree_files_beside_the_other_representations(self):
        with TemporaryDirectory() as folder:
            path = Path(folder)
            program = path / 'example.py'
            program.write_text('t = llist(1, llist(2,3), 4)\nprint_llist(t)\ndraw_data(t)\ndraw_tree(t)\ndraw_tree(None)\n')
            result = subprocess.run([sys.executable, '-m', 'sicpfuf', str(program), '-v', '2',
                                     '--out', str(path / 'pictures'), '--stem', 'example'],
                                    cwd=str(ROOT), capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('llist(1, llist(2, 3), 4)', result.stdout)
            self.assertIn('│   ├── 2', result.stdout)
            self.assertEqual({item.name for item in (path / 'pictures').iterdir()},
                             {'example-data-1.svg', 'example-tree-1.svg', 'example-tree-2.svg'})
            for image in (path / 'pictures').iterdir():
                ET.fromstring(image.read_text())

    def test_draw_tree_returns_its_input_and_reports_invalid_modes(self):
        output = io.StringIO()
        Interpreter(3, out=output).run_source('t = llist(1)\nprint(draw_tree(t) is t)\n')
        self.assertEqual(output.getvalue(), 'llist\n└── 1\nTrue\n')
        from sicpfuf.errors import SicpError
        for mode in ('"unknown"', '7'):
            with self.assertRaises(SicpError):
                Interpreter(2).run_source('draw_tree(None, ' + mode + ')\n')

    def test_typed_program_can_use_the_same_helper(self):
        result = subprocess.run([sys.executable, '-m', 'sicpfuf', '-v', '4', '--typed', '-c',
                                 't: LList[int] = llist(1,2)\ndraw_tree(t)\n'],
                                cwd=str(ROOT), capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('├── 1\n└── 2', result.stdout)


if __name__ == '__main__':
    unittest.main()
