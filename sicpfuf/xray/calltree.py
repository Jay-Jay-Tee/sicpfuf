"""
sicpfuf/xray/calltree.py — watch the calls a function makes.

    trace(fact, 4)            →  draws the CALL TREE of fact(4)
    measure(fact, 4)          →  how much TIME (calls, steps) and SPACE (calls waiting)

Every call that has to WAIT for another call's answer makes the picture one
level deeper. That is the difference you are asked about again and again:

    RECURSIVE PROCESS                      ITERATIVE PROCESS
    → fact(3)                              → fact_iter(1, 1, 3)
    │  → fact(2)                           ↻ fact_iter(1, 2, 3)
    │  │  → fact(1)                        ↻ fact_iter(2, 3, 3)
    │  │  ← 1                              ↻ fact_iter(6, 4, 3)
    │  ← 2                                 ← 6
    ← 6
    deferred operations pile up            nothing waits: ↻ marks a TAIL CALL,
    (the tree goes right)                  which REPLACES the call that made it
"""

from ..errors import SicpError
from ..values import Closure, short, type_name, a


class TreeHook:
    """Plugged into Interpreter.call_closure: told about every call and every return."""

    def __init__(self, interp, wanted):
        self.interp = interp
        self.wanted = wanted            # function value → should it be shown?
        self.levels = []                # for every call that is running or waiting: was it shown?
        self.depth = 0                  # how many SHOWN calls are waiting (= the indentation)
        self.deepest = 0

    def enter(self, func, args, tail, env):
        if not tail:
            self.levels.append(False)
        if not self.wanted(func):
            return
        shown = self.levels[-1]
        indent = "│  " * (self.depth - 1 if shown else self.depth)
        arrow = "↻" if shown else "→"
        self.interp.write(f"{indent}{arrow} {func.name}({', '.join(short(x, 30) for x in args)})\n")
        if not shown:
            self.levels[-1] = True
            self.depth += 1
            self.deepest = max(self.deepest, self.depth)

    def leave(self, result):
        if self.levels.pop():
            self.depth -= 1
            self.interp.write(f"{'│  ' * self.depth}← {short(result, 60)}\n")

    def failed(self, error):
        if self.levels.pop():
            self.depth -= 1
            self.interp.write(f"{'│  ' * self.depth}✗ {error.kind}\n")


def trace_names(interp, names):
    """--trace fib,helper : show every call of the functions with these names."""
    wanted = set(names)
    interp.hook = TreeHook(interp, lambda func: func.name in wanted and not func.prelude)


def need_function(what, f):
    if type(f) is not Closure:
        raise SicpError("TypeError", f"{what} expects a function that your program defined as its first "
                        f"argument, but got {a(type_name(f))}")


def trace(interp, node, f, args):
    """trace(f, a, b): call f(a, b), drawing every call of f on the way. Returns f's answer."""
    need_function("trace(f, ...)", f)
    saved = interp.hook
    interp.hook = TreeHook(interp, lambda func: func.node is f.node)
    try:
        return interp.call_closure(f, list(args), node)
    finally:
        interp.hook = saved


def measure(interp, node, f, args):
    """measure(f, a, b): call f(a, b) and report the work it did. Returns f's answer.

        time   = how many function calls and how many evaluation steps
        space  = the largest number of calls that were waiting at the same moment
    """
    need_function("measure(f, ...)", f)
    steps, calls, depth, deepest = interp.steps, interp.calls, interp.depth, interp.max_seen
    interp.max_seen = depth
    try:
        result = interp.call_closure(f, list(args), node)
    finally:
        used = interp.max_seen - depth
        interp.max_seen = max(deepest, interp.max_seen)
    shown = ", ".join(short(x, 20) for x in args)
    interp.write(f"[measure] {f.name}({shown}): {plural(interp.calls - calls, 'call')}, {plural(interp.steps - steps, 'step')}, "
                 f"at most {used:,} waiting at once\n")
    return result


def plural(n, word):
    return f"{n:,} {word}" + ("" if n == 1 else "s")
