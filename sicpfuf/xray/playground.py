"""Serializable histories for the built-in UI, using the real interpreter.

Snapshots contain strings, never live values: rewinding a mutation must not change
an earlier picture. The UI runs this in an isolated local subprocess.
"""

import io

from ..errors import SicpError, SicpSyntaxError, format_syntax_error, format_runtime_error
from ..interpreter import Interpreter
from .stepper import Stepper


class TraceLimit(Exception):
    pass


def trace(source, chapter=3, mode="environment", typed=False, graphics=True, max_steps=250):
    """Return bounded histories from the selected execution model."""
    if mode == "substitution":
        return substitution_trace(source, chapter, max_steps)
    from .reduction_trace import trace as environment_trace
    return environment_trace(source, chapter, typed, graphics, max_steps)


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
