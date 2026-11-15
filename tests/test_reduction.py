"""Published-rule reductions checked against actual, pinned upstream histories."""
import gzip
import json
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from conformance.steps import check
from sicpfuf.xray.playground import trace


class ReductionTests(unittest.TestCase):
    def test_programs_and_live_stores_match_reference_at_each_step(self):
        fixture = Path(__file__).parent / 'conformance/environment.json.gz'
        data = json.loads(gzip.decompress(fixture.read_bytes()))
        self.assertEqual(len(data['cases']), 59)
        for case in data['cases']:
            with self.subTest(case=case['id']):
                difference = check(case)
                if case['id'].endswith('/subscript-evaluation-order'):
                    # Upstream activeInList visits the target first, although
                    # its reducer (correctly) evaluates the RHS first.
                    self.assertEqual(difference, "state[10].activeFrameId: 'E1' != 'Global'")
                    self.assertIsNone(check(case, ignore_active_frame=True))
                else:
                    self.assertIsNone(difference)

    def test_ui_records_before_and_after_one_contraction(self):
        result = trace('print(2 + 3 * 4)\n')
        steps = result['steps']
        self.assertEqual(len(steps), 8)
        self.assertEqual(steps[1]['phase'], 'beforeMarker')
        self.assertEqual(steps[2]['phase'], 'afterMarker')
        self.assertIn('(3 * 4)', steps[1]['program'])
        self.assertIn('12', steps[2]['program'])
        self.assertEqual(steps[5]['output'], '')
        self.assertEqual(steps[6]['output'], '14\n')

    def test_shared_and_cyclic_lists_have_one_heap_destination(self):
        result = trace('a = [1,2]\nb = a\na[1] = a\n')
        final = result['steps'][-1]
        heap = final['store']['heap']
        self.assertEqual(len(heap), 1)
        self.assertEqual(heap[0]['elements'][1], {'kind': 'ref', 'objectId': heap[0]['id']})
        picture = ET.fromstring(final['diagram'])
        self.assertEqual(len([node for node in picture.iter() if 'data-object' in node.attrib]), 1)
        arrows = [node for node in picture.iter() if node.attrib.get('data-target') == heap[0]['id']]
        self.assertEqual(len(arrows), 3)  # a, b, and the list's second cell

    def test_dead_frame_alias_still_reflects_live_list_mutation(self):
        result = trace('def f(xs):\n    return 0\na = [1]\nf(a)\na[0] = 9\n', graphics=False)
        final = result['steps'][-1]
        old = next(frame for frame in final['frames'] if frame['id'] == 'E1')
        self.assertFalse(old['reachable'])
        self.assertEqual(old['bindings'][0]['value'], '[9]')
        initial_call = next(step for step in result['steps'] if step['message'].startswith('Called f'))
        self.assertEqual(next(frame for frame in initial_call['frames'] if frame['id'] == 'E1')['bindings'][0]['value'], '[1]')

    def test_typed_aliases_are_checked_then_erased(self):
        result = trace('type I = int\ndef f(x: I) -> I:\n    return x+1\nprint(f(2))\n', 4, typed=True)
        self.assertIsNone(result['error'])
        self.assertEqual(result['steps'][-1]['output'], '3\n')
        self.assertNotIn('type I', result['steps'][0]['program'])

    def test_invalid_range_preserves_a_useful_error(self):
        result = trace('print(7)\nfor i in range(1,3,0):\n    pass\n')
        self.assertIn('ValueError', result['error'])
        self.assertEqual(result['steps'][-1]['output'], '7\n')

    def test_unassigned_name_reports_the_source_line(self):
        result = trace('x = 1\ndef f():\n    print(x)\n    x = 2\nf()\n')
        self.assertIn('UnassignedLocalError at line 3', result['error'])
        self.assertEqual(result['steps'][-1]['line'], 3)

    def test_limit_stops_before_an_unrecorded_application(self):
        result = trace('error("this call must wait")\n', max_steps=2)
        self.assertEqual(len(result['steps']), 2)
        self.assertIn('Trace stopped at 2 steps', result['error'])


if __name__ == '__main__':
    unittest.main()
