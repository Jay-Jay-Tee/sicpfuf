"""Readiness gating for opening the textbook in VS Code, without binding sockets."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import re
import sys
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('serve_book', ROOT / 'scripts/serve_book.py')
book = importlib.util.module_from_spec(spec)
spec.loader.exec_module(book)


class BookLauncherTests(unittest.TestCase):
    def run_launcher(self):
        output = io.StringIO()
        with patch.object(sys, 'argv', ['serve_book.py']), contextlib.redirect_stdout(output):
            status = book.main()
        return status, output.getvalue()

    def test_existing_book_is_reused_without_starting_another_server(self):
        with patch.object(book, 'ready', return_value=True), patch.object(book.subprocess, 'Popen') as start:
            status, output = self.run_launcher()
        self.assertEqual(status, 0)
        start.assert_not_called()
        self.assertIn('ready http://127.0.0.1:8000/sicpfuf/book/', output)

    def test_browser_readiness_is_reported_only_after_book_responds(self):
        process = Mock()
        process.poll.side_effect = [None, None, 0]
        process.wait.return_value = 0
        with patch.object(book, 'ready', side_effect=[False, False, True]), \
                patch.object(book.subprocess, 'Popen', return_value=process) as start, \
                patch.object(book.time, 'sleep'):
            status, output = self.run_launcher()
        self.assertEqual(status, 0)
        self.assertEqual(output.count('sicpfuf textbook: ready '), 1)
        self.assertEqual(start.call_args[1]['cwd'], str(ROOT))
        self.assertEqual(start.call_args[0][0][-3:], ['serve', '--dev-addr', '127.0.0.1:8000'])
        process.wait.assert_called_once_with()
        process.terminate.assert_not_called()

    def test_failed_server_never_releases_the_browser(self):
        process = Mock(returncode=1)
        process.poll.return_value = 1
        with patch.object(book, 'ready', return_value=False), \
                patch.object(book.subprocess, 'Popen', return_value=process):
            status, output = self.run_launcher()
        self.assertEqual(status, 1)
        self.assertNotIn('sicpfuf textbook: ready ', output)

    def test_startup_timeout_stops_the_child_server(self):
        process = Mock()
        process.poll.return_value = None
        with patch.object(book, 'ready', return_value=False), \
                patch.object(book.subprocess, 'Popen', return_value=process), \
                patch.object(book.time, 'monotonic', side_effect=[0, 41]), \
                contextlib.redirect_stderr(io.StringIO()):
            status, output = self.run_launcher()
        self.assertEqual(status, 1)
        self.assertNotIn('sicpfuf textbook: ready ', output)
        process.terminate.assert_called_once_with()
        process.wait.assert_called_once_with(timeout=3)

    def test_local_launches_wait_for_the_actual_readiness_signal(self):
        launches = json.loads((ROOT / '.vscode/launch.json').read_text())['configurations']
        tasks = json.loads((ROOT / '.vscode/tasks.json').read_text())['tasks']
        by_label = {task['label']: task for task in tasks}
        books = [config for config in launches if config['url'] == 'http://127.0.0.1:8000/sicpfuf/book/']
        self.assertTrue(books)
        with patch.object(book, 'ready', return_value=True):
            status, output = self.run_launcher()
        self.assertEqual(status, 0)
        for config in books:
            task = by_label[config['preLaunchTask']]
            matcher = task['problemMatcher']['background']
            self.assertTrue(task['isBackground'])
            self.assertTrue(re.search(matcher['beginsPattern'], output, re.M))
            self.assertTrue(re.search(matcher['endsPattern'], output, re.M))


if __name__ == '__main__':
    unittest.main()
