"""Behavioral checks for the built-in UI's serialized execution history."""

import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sicpfuf.xray.playground import trace


def binding(step, frame, name):
    return next(b["value"] for f in step["frames"] if f["id"] == frame
                for b in f["bindings"] if b["name"] == name)


class PlaygroundTests(unittest.TestCase):
    def test_examples_and_output_match(self):
        examples = json.loads((Path(__file__).resolve().parents[1] /
                               "sicpfuf/ui/examples.json").read_text())
        expected = ["15\n17\n", "13\n", "6\n", "7\n15\n", "99\nTrue\n", "24\n", "6\n", "10\n", "4\n"]
        self.assertEqual(len(examples), len(expected))
        for example, output in zip(examples, expected):
            with self.subTest(example=example["id"]):
                result = trace(example["source"], example["chapter"], example.get("mode", "environment"))
                self.assertIsNone(result["error"])
                self.assertEqual(result["steps"][-1]["output"], output)
                json.dumps(result)  # no live interpreter objects cross the worker boundary

    def test_mutation_does_not_rewrite_history(self):
        result = trace("xs = pair(1, None)\nys = xs\nset_head(ys, 9)\n")
        before = next(s for s in result["steps"] if s["message"].startswith("Assigned ys"))
        after = next(s for s in result["steps"] if s["message"].startswith("Changed the head"))
        self.assertIn("[1, None]", binding(before, "global env", "xs"))
        self.assertIn("[9, None]", binding(after, "global env", "xs"))
        self.assertEqual(binding(after, "global env", "xs"), binding(after, "global env", "ys"))
        self.assertNotEqual(before["data"][0]["svg"], after["data"][0]["svg"])

    def test_closure_keeps_its_creation_frame(self):
        result = trace("def make(x):\n    return lambda y: x + y\nf = make(2)\nprint(f(3))\n")
        final = result["steps"][-1]
        closure = next(f for f in final["functions"] if f["env"] == "E1")
        self.assertEqual(closure["line"], 2)
        self.assertEqual(binding(final, "E1", "x"), "2")
        self.assertEqual(final["output"], "5\n")

    def test_lexical_parent_is_not_caller(self):
        result = trace("x = 10\ndef f(y):\n    return x + y\ndef g(x):\n    a = f(3)\n    return a\nprint(g(100))\n")
        call = next(s for s in result["steps"] if s["message"].startswith("Called f"))
        current = next(f for f in call["frames"] if f["current"])
        self.assertEqual(current["parent"], "global env")
        self.assertEqual(call["line"], 5)

    def test_unreachable_frames_and_closure_cycles_stay_in_history(self):
        source = "def add(a, b):\n    def add(c, d):\n        return c + d\n    return add(a, b)\nprint(add(5, 6))\n"
        result = trace(source, 2)
        self.assertIsNone(result["error"])
        final = result["steps"][-1]
        frames = {frame["id"]: frame for frame in final["frames"]}
        self.assertEqual(set(frames), {"global env", "E1", "E2"})
        self.assertTrue(frames["global env"]["reachable"])
        self.assertFalse(frames["E1"]["reachable"])
        self.assertFalse(frames["E2"]["reachable"])
        self.assertEqual(binding(final, "E1", "add"), "fn#2")
        self.assertEqual(binding(final, "E2", "c"), "5")
        self.assertFalse(next(fn for fn in final["functions"] if fn["id"] == "fn#2")["reachable"])
        self.assertIn('class="unreachable" data-reachable="false"', final["diagram"])
        call = next(step for step in result["steps"] if step["message"].startswith("Tail call"))
        self.assertTrue(next(frame for frame in call["frames"] if frame["id"] == "E1")["reachable"])
        self.assertEqual(result["steps"][0]["frames"][0]["bindings"], [])

    def test_returned_frame_kept_alive_by_a_closure_is_not_grey(self):
        result = trace("def make(x):\n    return lambda y: x + y\nf = make(2)\nprint(f(3))\n", 2)
        frames = {frame["id"]: frame for frame in result["steps"][-1]["frames"]}
        self.assertTrue(frames["E1"]["reachable"])
        self.assertFalse(frames["E1"]["on_stack"])
        self.assertFalse(frames["E2"]["reachable"])

    def test_errors_preserve_output_and_history(self):
        result = trace("print(7)\nx = 1 / 0\n")
        self.assertIn("ZeroDivisionError", result["error"])
        self.assertEqual(result["steps"][-1]["output"], "7\n")
        self.assertEqual(result["steps"][-1]["line"], 2)
        syntax = trace("def f(:\n")
        self.assertIn("SyntaxError", syntax["error"])

    def test_loops_are_bounded_even_without_trace_events(self):
        result = trace("while True:\n    pass\n")
        self.assertIn("15,000 operations", result["error"])
        self.assertLessEqual(len(result["steps"]), 250)

    def test_many_events_are_bounded(self):
        result = trace("x = 0\nwhile True:\n    x = x + 1\n")
        self.assertIn("250 steps", result["error"])
        self.assertEqual(len(result["steps"]), 250)

    def test_tail_calls_and_library_calls(self):
        result = trace("def loop(n, acc):\n    return acc if n == 0 else loop(n - 1, acc + n)\nprint(loop(5, 0))\nprint(length(llist(1, 2, 3)))\n")
        self.assertIsNone(result["error"])
        self.assertEqual(result["steps"][-1]["output"], "15\n3\n")
        self.assertTrue(any(s["message"].startswith("Tail call") for s in result["steps"]))

    def test_chapter_rules_apply_to_edited_code(self):
        result = trace("xs = [1, 2]\n", chapter=1)
        self.assertIsNotNone(result["error"])

    def test_terminal_histories_omit_graphics_without_changing_execution(self):
        source = "def f(x):\n    return x + 1\nprint(f(3))\n"
        graphic = trace(source, 2)
        text = trace(source, 2, graphics=False)
        for shown, plain in zip(graphic["steps"], text["steps"]):
            self.assertEqual(shown["frames"], plain["frames"])
            self.assertEqual(shown["functions"], plain["functions"])
            self.assertEqual(shown["output"], plain["output"])
            self.assertIsNone(plain["diagram"])
        self.assertLess(len(json.dumps(text)), len(json.dumps(graphic)) // 2)

    def test_environment_diagram_has_inspectable_frames_and_functions(self):
        import xml.etree.ElementTree as ET
        result = trace("def f(x):\n    return x + 1\nprint(f(2))\n")
        call = next(s for s in result["steps"] if s["message"].startswith("Called f"))
        picture = ET.fromstring(call["diagram"])
        self.assertEqual({g.attrib["data-frame"] for g in picture.iter() if "data-frame" in g.attrib},
                         {"global env", "E1"})
        self.assertTrue(any(g.attrib.get("data-function") == "fn#1" for g in picture.iter()))
        self.assertTrue(any(g.attrib.get("marker-end") == "url(#arrow)" for g in picture.iter()))

    def test_substitution_records_actual_reductions(self):
        result = trace("def square(x):\n    return x * x\nprint(square(2 + 1))\n", 1, "substitution")
        self.assertIsNone(result["error"])
        expressions = [s["expression"] for s in result["steps"]]
        self.assertIn("print(square(3))", expressions)
        self.assertIn("print(3 * 3)", expressions)
        self.assertIn("print(9)", expressions)
        self.assertEqual(result["steps"][-1]["output"], "9\n")

    def test_substitution_keeps_printed_output_separate(self):
        result = trace("print(1 + 2)\nprint(4 + 5)\n", 1, "substitution")
        self.assertEqual(result["steps"][-1]["output"], "3\n9\n")
        before = next(s for s in result["steps"] if s["expression"] == "print(4 + 5)")
        self.assertEqual(before["output"], "3\n")

    def test_substitution_refuses_state_and_is_bounded(self):
        self.assertIn("e-stepper", trace("x = 1\n", 3, "substitution")["error"])
        result = trace("def loop(x):\n    return loop(x)\nloop(0)\n", 1, "substitution")
        self.assertIsNotNone(result["error"])
        self.assertLessEqual(len(result["steps"]), 250)

    def test_substitution_reports_errors_without_losing_output(self):
        result = trace("print(7)\nprint(1 / 0)\n", 1, "substitution")
        self.assertIn("ZeroDivisionError", result["error"])
        self.assertEqual(result["steps"][-1]["output"], "7\n")


if __name__ == "__main__":
    unittest.main()
