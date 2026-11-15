"""Serializable histories for the built-in UI, using the real interpreter.

Snapshots contain strings, never live values: rewinding a mutation must not change
an earlier picture. The UI runs this in an isolated local subprocess.
"""

import io

from ..errors import SicpError, SicpSyntaxError, format_syntax_error, format_runtime_error
from ..values import Closure
from ..interpreter import Interpreter
from .envdiagram import Snapshot, frame_name, fn_name
from .estepper import EnvStepper
from . import svg
from .stepper import Stepper


class TraceLimit(Exception):
    pass


class BrowserStepper(EnvStepper):
    def __init__(self, chapter=3, typed=False, graphics=True, max_steps=250):
        self.recording = False
        self.history = []
        self.line = 0
        self.operations = 0
        self.graphics = graphics
        self.max_steps = max_steps
        super().__init__(chapter=chapter, out=io.StringIO(), max_depth=80, typed=typed)
        self.diagrams = True
        self.recording = True

    def visit_node(self, method, node, env):
        if self.recording:
            self.operations += 1
            if self.operations > 15000:
                raise TraceLimit("Execution stopped after 15,000 operations. Try a smaller input.")
        previous = self.line
        if not node.lib:
            self.line = node.line
        try:
            return method(node, env)
        finally:
            self.line = previous

    def exec(self, node, env):
        return self.visit_node(super().exec, node, env)

    def eval(self, node, env):
        return self.visit_node(super().eval, node, env)

    def write(self, text):
        if self.out.tell() + len(text) > 16000:
            raise TraceLimit("Output stopped at 16,000 characters. Try printing less.")
        self.out.write(text)
        if self.recording:
            self.capture("Program output")

    def note(self, text):
        if self.recording:
            self.capture(text)

    def capture(self, message, line=None):
        if len(self.history) >= self.max_steps:
            raise TraceLimit(f"Trace stopped at {self.max_steps} steps. Increase --max-steps to see more.")
        snapshot = Snapshot(self)
        frames = []
        data = []
        seen = set()
        for env in sorted(snapshot.frames.values(), key=lambda e: e.serial):
            names = list(env.vars)
            if env.scope is not None:
                names += sorted(env.scope.local_names - env.vars.keys())
            bindings = []
            for name in names:
                value = env.vars.get(name)
                function = fn_name(value) if type(value) is Closure and not value.prelude else None
                bindings.append({"name": name, "value": snapshot.value_text(value)
                                 if name in env.vars else "(unassigned)", "function": function})
                if self.graphics and type(value) is list and id(value) not in seen and len(data) < 6:
                    seen.add(id(value))
                    data.append({"label": frame_name(env) + "." + name,
                                 "svg": svg.box_pointer(value)})
            frames.append({"id": frame_name(env), "parent": frame_name(env.parent),
                           "call": env.name + "(" + ", ".join(env.args or []) + ")"
                           if env.kind == "function" else "Whole program",
                           "current": env is snapshot.current, "bindings": bindings})
        functions = [{"id": fn_name(f), "params": f.params + (["*" + f.vararg] if f.vararg else []),
                      "line": f.node.line, "source": snapshot.source(f.node.line),
                      "env": frame_name(f.env)}
                     for f in sorted(snapshot.functions.values(), key=lambda f: f.serial)]
        self.history.append({"message": message, "line": self.line if line is None else line,
                             "frames": frames, "functions": functions, "data": data,
                             "diagram": svg.environment(snapshot, interactive=True) if self.graphics else None,
                             "output": self.out.getvalue()})


def trace(source, chapter=3, mode="environment", typed=False, graphics=True, max_steps=250):
    """Return a bounded, JSON-safe trace; retain useful history on user errors."""
    if mode == "substitution":
        return substitution_trace(source, chapter, max_steps)
    interp = BrowserStepper(chapter, typed=typed, graphics=graphics, max_steps=max_steps)
    error = None
    interp.capture("Ready. Step forward to start the program.")
    try:
        tree = interp.load_source(source, typecheck=typed)
        interp.run_tree(tree)
        interp.capture("Program finished.")
    except (SicpError, SicpSyntaxError) as exc:
        lines = source.splitlines()
        error = (exc.report(lines) if hasattr(exc, "report") else
                 format_syntax_error(exc, lines) if isinstance(exc, SicpSyntaxError)
                 else format_runtime_error(exc, lines))
        if len(interp.history) < max_steps:
            interp.capture("Program stopped: " + str(exc), line=exc.line or 0)
    except (TraceLimit, RecursionError) as exc:
        error = str(exc)
    return {"steps": interp.history, "error": error}


class SubstitutionInterpreter(Interpreter):
    """Keep program output separate from the substitution model's printed terms."""

    def __init__(self, chapter):
        self.operations = 0
        self.ready = False
        self.recorder = None
        super().__init__(chapter=chapter, out=io.StringIO(), max_depth=80)
        self.ready = True

    def tick(self):
        if self.ready:
            self.operations += 1
            if self.operations > 15000:
                raise TraceLimit("Execution stopped after 15,000 operations. Try a smaller input.")

    def exec(self, node, env):
        self.tick()
        return super().exec(node, env)

    def eval(self, node, env):
        self.tick()
        return super().eval(node, env)

    def write(self, text):
        if self.recorder.output.tell() + len(text) > 16000:
            raise TraceLimit("Output stopped at 16,000 characters. Try printing less.")
        self.recorder.output.write(text)
        self.recorder.capture("Program output", self.recorder.last_line or "")


class SubstitutionRecorder(Stepper):
    def __init__(self, interp, max_steps=250):
        super().__init__(interp, limit=max_steps)
        self.history = []
        self.output = io.StringIO()
        self.line = 0
        interp.recorder = self

    def capture(self, message, expression=""):
        if len(self.history) >= self.limit:
            raise TraceLimit(f"Trace stopped at {self.limit} steps. Increase --max-steps to see more.")
        self.history.append({"message": message, "line": self.line, "expression": expression,
                             "frames": [], "functions": [], "data": [],
                             "output": self.output.getvalue()})

    def step(self, term):
        self.interp.tick()
        return super().step(term)

    def show(self, prefix, term, first=False):
        text = prefix + self.text(term)
        if not first and text == self.last_line:
            return
        self.last_line = text
        self.capture("Start expression" if first else "Substitute and reduce", text)

    def statement(self, node):
        previous = self.line
        self.line = node.line
        try:
            super().statement(node)
            if node.__class__.__name__ == "FunctionDef":
                self.capture("Defined " + node.name + "; its body runs when called.")
        finally:
            self.line = previous


def substitution_trace(source, chapter, max_steps=250):
    interp = SubstitutionInterpreter(chapter)
    recorder = SubstitutionRecorder(interp, max_steps)
    error = None
    recorder.capture("Ready. Step forward to start the program.")
    try:
        if chapter > 2:
            raise SicpSyntaxError("The substitution stepper supports Python §1 and §2. "
                                  "Choose the e-stepper for mutation and state.", line=1)
        tree = interp.load_source(source)
        for node in tree.body:
            recorder.statement(node)
        recorder.capture("Program finished.", recorder.last_line or "")
    except (SicpError, SicpSyntaxError) as exc:
        lines = source.splitlines()
        error = (format_syntax_error(exc, lines) if isinstance(exc, SicpSyntaxError)
                 else format_runtime_error(exc, lines))
        if len(recorder.history) < max_steps:
            recorder.line = exc.line or recorder.line
            recorder.capture("Program stopped: " + str(exc), recorder.last_line or "")
    except (TraceLimit, RecursionError) as exc:
        error = str(exc)
    return {"steps": recorder.history, "error": error}
