"""
sicpfuf/xray/envdiagram.py — the ENVIRONMENT DIAGRAM, as text.

    show_env()          (anywhere in a program)        or        --env   (at the end)

What you would draw by hand, sicpfuf prints:

    global env
        balance_maker: fn#1
        w: fn#2
    E1: make_withdraw(100)          enclosing environment: global env
        balance: 50
    function objects
        fn#1  parameters: balance   body: line 1  def make_withdraw(balance):   environment: global env
        fn#2  parameters: amount    body: line 2  def withdraw(amount):         environment: E1

HOW TO READ IT
  * A FRAME is a table of bindings  name: value.  "global env" is the frame of your
    whole program; E1, E2, ... are the frames made by function CALLS, in the order
    they were made.
  * Every frame except the global one says which frame it ENCLOSING environment is.
    That is the frame where the called function was CREATED, never the caller's.
  * A FUNCTION OBJECT is "two circles": its code (parameters and body) and the
    environment it was created in. fn#1, fn#2, ... are numbered in order of creation.
  * A frame that would be empty (a call of a function with no parameters and no
    local names) is left out, as in hand-drawn diagrams.
  * `name: (unassigned)` means the name belongs to this frame, but the line that
    gives it a value has not run yet.
"""

from ..values import Closure, Builtin, short, show_atom

MAX_VISIT = 5000


def real_frame(env):
    """Skip frames that are not drawn (library frames, and frames with no bindings)."""
    while env is not None and env.kind == "function" and env.serial == 0:
        env = env.parent
    return env


def frame_name(env):
    env = real_frame(env)
    if env is None or env.kind in ("builtins", "library"):
        return "built-ins env"
    if env.kind == "program":
        return "global env"
    return f"E{env.serial}"


def fn_name(closure):
    return f"fn#{closure.serial}"


class Snapshot:
    """Everything that is reachable right now: frames, function objects, shared data."""

    def __init__(self, interp, current=None):
        self.interp = interp
        self.stack = [real_frame(e) for e in interp.envs if e is not None]
        self.current = real_frame(current if current is not None else
                                  (interp.envs[-1] if interp.envs and interp.envs[-1] is not None
                                   else interp.program_env))
        self.frames = {}                # id(env) → env   (function frames to draw)
        self.functions = {}             # serial → closure
        self.refs = {}                  # id(list) → how many bindings point straight at it
        self.labels = {}
        self.visited = 0
        self.add_frame(interp.program_env)
        for env in self.stack:
            self.add_frame(env)
        self.add_frame(self.current)

    def add_frame(self, env):
        env = real_frame(env)
        if env is None or env.kind in ("builtins", "library") or id(env) in self.frames:
            return
        self.frames[id(env)] = env
        self.add_frame(env.parent)
        for value in list(env.vars.values()):
            if type(value) is list:
                self.refs[id(value)] = self.refs.get(id(value), 0) + 1
            self.visit(value)

    def visit(self, value):
        """Find the function objects (and through them, the frames) that a value keeps alive."""
        stack, seen = [value], set()
        while stack and self.visited < MAX_VISIT:
            v = stack.pop()
            self.visited += 1
            if type(v) is Closure:
                if not v.prelude and v.serial not in self.functions:
                    self.functions[v.serial] = v
                    self.add_frame(v.env)
            elif type(v) is list and id(v) not in seen:
                seen.add(id(v))
                stack.extend(v)

    def value_text(self, v):
        if type(v) is Closure:
            return fn_name(v) if not v.prelude else repr(v)
        if type(v) is Builtin:
            return repr(v)
        if type(v) is list:
            text = self.list_text(v)
            if self.refs.get(id(v), 0) > 1:             # two names for ONE object: make that visible
                if id(v) not in self.labels:
                    self.labels[id(v)] = len(self.labels) + 1
                return f"@{self.labels[id(v)]} {text}"
            return text
        return show_atom(v)

    def list_text(self, v, depth=0):
        if depth > 30:
            return "..."
        parts = []
        for x in v[:12]:
            parts.append(self.list_text(x, depth + 1) if type(x) is list else
                         fn_name(x) if type(x) is Closure and not x.prelude else short(x, 30))
        if len(v) > 12:
            parts.append("...")
        return "[" + ", ".join(parts) + "]"

    def source(self, line):
        lines = self.interp.sources.get(next(iter(self.interp.sources), None)) if self.interp.sources else None
        for name, src in self.interp.sources.items():
            if not name.startswith("<") or name in ("<string>", "<sicpfuf>", "<repl>"):
                lines = src
        if lines and 0 < line <= len(lines):
            text = lines[line - 1].strip()
            return text if len(text) <= 48 else text[:45] + "..."
        return ""

    def render(self, label=None):
        out = [f"-- environment diagram{': ' + str(label) if label is not None else ''} --"]
        frames = sorted(self.frames.values(), key=lambda e: e.serial)
        for env in frames:
            if env.kind == "program":
                head = "global env"
            else:
                args = ", ".join(short(x, 20) for x in (env.args or []))
                head = f"E{env.serial}: {env.name}({args})"
                head = f"{head:<28}  enclosing environment: {frame_name(env.parent)}"
            if env is self.current and (len(frames) > 1 or env.kind != "program"):
                head += "    <-- current environment"
            elif any(env is s for s in self.stack):
                head += "    (waiting)"
            out.append(head)
            names = list(env.vars)
            if env.scope is not None:
                names += sorted(n for n in env.scope.local_names if n not in env.vars)
            if not names:
                out.append("    (no bindings)")
            for name in names:
                if name in env.vars:
                    out.append(f"    {name}: {self.value_text(env.vars[name])}")
                else:
                    out.append(f"    {name}: (unassigned)")
        if self.functions:
            out.append("function objects")
            rows = []
            for serial in sorted(self.functions):
                f = self.functions[serial]
                params = ", ".join(f.params + (["*" + f.vararg] if f.vararg else [])) or "(none)"
                rows.append((fn_name(f), params, f"line {f.node.line}  {self.source(f.node.line)}",
                             frame_name(f.env)))
            w1 = max(len(r[1]) for r in rows)
            w2 = max(len(r[2]) for r in rows)
            for name, params, body, env in rows:
                out.append(f"    {name:<6} parameters: {params:<{w1}}   body: {body:<{w2}}   environment: {env}")
        if self.labels:
            out.append("(the same @number means the SAME object: `is` would say True)")
        return "\n".join(out)


def show(interp, node=None, label=None):
    snapshot = Snapshot(interp)
    interp.write(snapshot.render(label) + "\n")
    if getattr(interp, "out_dir", None):             # with --out FOLDER: also save a picture
        from . import svg
        from ..modules.rune_module import save_figure
        name = save_figure(interp, "env", "svg", svg.environment(snapshot, label))
        if not getattr(interp, "out_stem", None):
            interp.write(f"[saved {name}]\n")
