"""Published-rule reductions checked against actual, pinned upstream histories."""
import gzip
import json
import random
import re
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from conformance.steps import check
from sicpfuf.xray.playground import trace
from sicpfuf.xray.svg import reduction_environment


class ReductionTests(unittest.TestCase):
    def test_pointer_graph_uses_horizontal_tails_and_vertical_heads(self):
        result = trace('a = pair(1,2)\nb = llist(3,4)\nc = pair(a,b)\nd = pair(c,b)\nboth = pair(d,c)\n', 3)
        picture = ET.fromstring(result['steps'][-1]['diagram'])
        objects = {node.attrib['data-object']: tuple(map(float, node.attrib['data-bounds'].split(',')))
                   for node in picture.iter() if 'data-object' in node.attrib}
        self.assertEqual(len(objects), 6)
        self.assertLess(float(picture.attrib['height']), 500)
        root, head, last = objects['#6'], objects['#5'], objects['#4']
        self.assertEqual(root[1], last[1])
        self.assertGreater(last[0], root[0])
        self.assertEqual(root[0], head[0])
        self.assertGreater(head[1], root[1])
        self.assert_pointer_corridors_avoid_boxes(picture)

    def assert_pointer_corridors_avoid_boxes(self, picture):
        boxes = {node.attrib['data-node-id']: tuple(map(float, node.attrib['data-bounds'].split(',')))
                 for node in picture.iter() if 'data-object' in node.attrib or 'data-function' in node.attrib}
        for edge in picture.iter():
            if edge.attrib.get('data-edge-kind') != 'reference':
                continue
            points = [tuple(map(float, pair)) for pair in re.findall(r'[ML](-?[\d.]+),(-?[\d.]+)', edge.attrib['d'])]
            self.assertGreaterEqual(len(points), 2)
            for (ax, ay), (bx, by) in zip(points, points[1:]):
                self.assertTrue(ax == bx or ay == by)
                for key, (x, y, w, h) in boxes.items():
                    if key in (edge.attrib['data-source'], edge.attrib['data-target']):
                        continue
                    crosses = (min(ax, bx) < x + w and max(ax, bx) > x
                               and min(ay, by) < y + h and max(ay, by) > y)
                    self.assertFalse(crosses, (edge.attrib, key))

    def test_shared_cycles_and_multirow_arrays_have_unobstructed_pointer_routes(self):
        rng = random.Random(571)
        for count in (1, 3, 8, 14):
            for _ in range(6):
                heap = [{'id': '#' + str(i), 'kind': 'list', 'isGarbage': False,
                         'elements': [({'kind': 'ref', 'objectId': '#' + str(rng.randrange(count))}
                                       if rng.random() < .5 else {'kind': 'literal', 'display': str(j)})
                                      for j in range(rng.randrange(10))]}
                        for i in range(count)]
                store = {'heap': heap, 'activeFrameId': 'Global', 'frames': [
                    {'id': 'Global', 'parentId': None, 'isGarbage': False,
                     'bindings': [{'name': 'root', 'value': {'kind': 'ref', 'objectId': '#0'}}]}]}
                with self.subTest(count=count, heap=heap):
                    picture = ET.fromstring(reduction_environment(store, {}, {}))
                    self.assert_pointer_corridors_avoid_boxes(picture)
                    self.assertEqual(len([node for node in picture.iter() if 'data-object' in node.attrib]), count)

    def test_global_points_to_visible_collapsed_builtins(self):
        result = trace('print(1)\n')
        for step in (result['steps'][0], result['steps'][-1]):
            picture = ET.fromstring(step['diagram'])
            builtins = next(node for node in picture.iter() if 'data-builtins' in node.attrib)
            self.assertIn(':::pre-declared names:::', ''.join(builtins.itertext()))
            self.assertTrue(any(node.attrib.get('data-parent') == 'Builtins' and
                                node.attrib.get('marker-end') == 'url(#arrow)' for node in picture.iter()))
            self.assertEqual([frame['id'] for frame in step['store']['frames']], ['Global'])

    def test_function_environment_links_curve_to_distinct_parent_ports(self):
        result = trace('def f(x):\n    return x\ndef g(x):\n    return x+1\n')
        picture = ET.fromstring(result['steps'][-1]['diagram'])
        links = [node for node in picture.iter() if node.attrib.get('data-edge-kind') == 'environment']
        self.assertEqual(len(links), 2)
        self.assertEqual({node.attrib['data-target'] for node in links}, {'Global'})
        self.assertEqual(len({node.attrib['d'].split()[-1] for node in links}), 2)
        self.assertTrue(all(' C' in node.attrib['d'] and ' H' not in node.attrib['d'] for node in links))

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
