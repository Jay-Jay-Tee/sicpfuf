"""
sicpfuf/xray/estepper.py — the ENVIRONMENT MODEL, one step at a time (the "e-stepper").

    python3 -m sicpfuf program.py --estep

Every time the program touches the environment, a line says what happened and WHERE:

    Assigned x = 0 in the global frame
    Defined f: function object fn#1, created in the global environment
    Called f(5): new frame E1, whose enclosing environment is the global environment
    Looked up x: not in E2, found in frame E1: 5
    Returned 6 from E1

These are exactly the rules you apply by hand when you draw an environment diagram:

    name lookup     start in the current frame, follow the enclosing-environment arrows outwards
    def / lambda    make a function object that REMEMBERS the current environment
    call            make a new frame, whose enclosing environment is the one the function
                    object remembers (NOT the caller's), bind the parameters, run the body there
    assignment      change the binding in the frame the name belongs to
                    (the current one, unless the function says nonlocal / global)

A lookup that finds the name in the CURRENT frame, or among the built-ins, is not
reported (there are too many of those). What the program prints is marked `output:`.
"""

from .. import nodes as N
from ..interpreter import Interpreter
from ..values import Closure, short
from .envdiagram import real_frame, frame_name, fn_name


def the(env_name):
    return "the global environment" if env_name == "global env" else \
        "the built-ins environment" if env_name == "built-ins env" else f"environment {env_name}"


def frame_of(env_name):
    return "the global frame" if env_name == "global env" else f"frame {env_name}"


class StepHook:
    def __init__(self, stepper):
        self.stepper = stepper
        self.envs = []

    def enter(self, func, args, tail, env):
        s = self.stepper
        if func.prelude:
            if not tail:
                self.envs.append(None)
            return
        call = f"{func.name}({', '.join(s.show(x) for x in args)})"
        parent = the(frame_name(func.env))
        if env.serial:
            text = f"new frame E{env.serial}, whose enclosing environment is {parent}"
            unassigned = sorted(n for n in func.scope.local_names if n not in env.vars)
            if unassigned:
                text += f" (local name{'s' if len(unassigned) > 1 else ''} " \
                        f"{', '.join(unassigned)}: unassigned so far)"
        else:
            text = f"the new frame would have no bindings, so the body runs in {parent}"
        if tail:
            self.envs[-1] = env
            s.note(f"Tail call {call}: {text}")
        else:
            self.envs.append(env)
            s.note(f"Called {call}: {text}")

    def leave(self, result):
        env = self.envs.pop()
        if env is not None:
            self.stepper.note(f"Returned {self.stepper.show(result)} from {frame_name(env)}")

    def failed(self, error):
        self.envs.pop()


class EnvStepper(Interpreter):
    """An Interpreter that reports every change to the environment."""

    def __init__(self, *args, **kwargs):
        self.at_line_start = True
        super().__init__(*args, **kwargs)
        self.hook = StepHook(self)

    def show(self, v):
        if type(v) is Closure and not v.prelude:
            return f"function object {fn_name(v)}"
        return short(v, 50)

    def note(self, text):
        if not self.at_line_start:
            self.out.write("\n")
        self.out.write(text + "\n")
        self.at_line_start = True

    def write(self, text):                      # everything the PROGRAM prints is marked
        for piece in text.splitlines(True):
            if self.at_line_start:
                self.out.write("    output: ")
            self.out.write(piece)
            self.at_line_start = piece.endswith("\n")

    def exec_Assign(self, node, env):
        target = node.targets[0]
        if node.lib:                            # inside a library function: not your code, no report
            return super().exec_Assign(node, env)
        if target.__class__ is not N.Name:
            super().exec_Assign(node, env)
            self.note(f"Changed an item of a list (line {node.line})")
            return None
        value = self.eval(node.value, env)
        where = env.target_env(target.id)
        env.assign(target.id, value)
        how = ""
        if env.scope is not None and target.id in env.scope.nonlocal_names:
            how = " (nonlocal)"
        elif env.scope is not None and target.id in env.scope.global_names:
            how = " (global)"
        self.note(f"Assigned {target.id} = {self.show(value)} in {frame_of(frame_name(where))}{how}")
        return None

    def exec_FunctionDef(self, node, env):
        super().exec_FunctionDef(node, env)
        if node.lib:
            return
        f = env.lookup(node.name)
        self.note(f"Defined {node.name}: function object {fn_name(f)}, created in {the(frame_name(env))}")

    def eval_Lambda(self, node, env):
        f = super().eval_Lambda(node, env)
        if node.lib:
            return f
        self.note(f"Evaluated a lambda expression: function object {fn_name(f)}, "
                  f"created in {the(frame_name(env))}")
        return f

    def eval_Name(self, node, env):
        value = env.lookup(node.id, node.line)
        if node.lib:
            return value
        here = real_frame(env)
        e = env
        while e is not None and node.id not in e.vars:
            sc = e.scope
            e = e.program if sc is not None and node.id in sc.global_names else e.parent
        found = real_frame(e)
        if found is not here and found is not None and found.kind in ("program", "function"):
            self.note(f"Looked up {node.id}: not in {frame_of(frame_name(here)).replace('the ', '')}, "
                      f"found in {frame_of(frame_name(found))}: {self.show(value)}")
        return value
