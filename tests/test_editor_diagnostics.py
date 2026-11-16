"""Live checks use the interpreter's rules without evaluating the program."""
import unittest
import io
from unittest.mock import patch

from sicpfuf.interpreter import Interpreter
from sicpfuf.ui.checking import check_source


class EditorDiagnosticsTests(unittest.TestCase):
    def test_ordinary_functions_need_no_annotations(self):
        self.assertEqual(check_source('def square(x):\n    return x * x\nprint(square(3))\n'),
                         {'ok': True, 'error': None, 'diagnostics': []})

    def test_syntax_and_name_locations(self):
        syntax = check_source('def f(x)\n    return x\n')
        self.assertFalse(syntax['ok'])
        self.assertEqual(syntax['diagnostics'], [{'line': 1, 'column': 9, 'message': "expected ':'"}])
        name = check_source('x = 1\nprint(missing)\n')['diagnostics'][0]
        self.assertEqual((name['line'], name['column']), (2, 7))
        self.assertIn("'missing'", name['message'])

    def test_selected_chapter_controls_checks(self):
        source = 'a = 1\na = 2\n'
        self.assertIn('NameReassignmentError', check_source(source, 1)['error'])
        self.assertTrue(check_source(source, 3)['ok'])
        self.assertFalse(check_source('xs = [1, 2]\n', 1)['ok'])

    def test_user_code_is_never_evaluated(self):
        source = 'print(input("prompt"))\nprint(1 // 0)\nerror("boom")\nwhile True:\n    pass\n'
        interp = Interpreter(3, out=io.StringIO())
        with patch('sicpfuf.ui.checking.Interpreter', return_value=interp), \
                patch.object(interp, 'eval', side_effect=AssertionError('executed user code')):
            self.assertTrue(check_source(source, 3)['ok'])
        self.assertEqual(interp.out.getvalue(), '')

    def test_typed_checks_are_optional_and_preserve_all_errors(self):
        source = 'a: int = "bad"\nb: str = 1\n'
        self.assertTrue(check_source('a = "bad"\nprint(a + 1)\n', 4)['ok'])
        self.assertIn('FeatureNotSupportedError', check_source(source, 4)['error'])
        errors = check_source(source, 4, True)['diagnostics']
        self.assertEqual([(e['line'], e['column']) for e in errors], [(1, 10), (2, 10)])
        self.assertTrue(check_source('def f(x):\n    return x\n', 4)['ok'])

    def test_invalid_configuration(self):
        for chapter, typed in ((True, False), (5, False), (2, True), (4, 'yes')):
            with self.subTest(chapter=chapter, typed=typed), self.assertRaises(ValueError):
                check_source('', chapter, typed)
