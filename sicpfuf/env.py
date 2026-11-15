"""
sicpfuf/env.py — where names LIVE: the ENVIRONMENT MODEL, as code.

An environment is a chain of FRAMES. Each frame is a small table (name → value)
with an arrow to its ENCLOSING frame:

      builtins   print, pair, head, math_sqrt, ...
         ▲
      library    map, filter, reduce, ... (written in Python §2 itself)
         ▲
      program    the names YOUR program defines at the top level ("global frame")
         ▲
      f(3)       a new frame for every function CALL: parameters + local names

The two rules of the environment model are both in this file and interpreter.py:

  1. To look a name up, start in the current frame and follow the arrows
     outwards until you find it                              (Environment.lookup)
  2. To call a function, make a NEW frame whose arrow points to the frame the
     function was CREATED in (not the one it was called from!), put the
     arguments in it, and run the body there                 (Interpreter.call_closure)
"""

from .errors import SicpError, suggest


class Environment:
    __slots__ = ("vars", "parent", "kind", "name", "scope", "serial", "program", "call_line", "args")

    def __init__(self, kind, parent=None, name="", scope=None):
        self.vars = {}            # THE frame: name → value
        self.parent = parent      # the enclosing frame (None for builtins)
        self.kind = kind          # 'builtins' | 'library' | 'program' | 'function'
        self.name = name          # the function's name, for messages and diagrams
        self.scope = scope        # ScopeInfo for function frames (from scopes.py), else None
        self.serial = 0           # numbering for environment diagrams (E1, E2, ...)
        self.call_line = 0
        self.args = None
        if kind == "program":
            self.program = self
        elif parent is not None:
            self.program = parent.program
        else:
            self.program = None

    # ---------------------------------------------------------------- reading
    def lookup(self, name, line=None):
        """Rule 1: look here, then follow the arrows outwards."""
        env = self
        while env is not None:
            vars_ = env.vars
            if name in vars_:
                return vars_[name]
            sc = env.scope
            if sc is not None:
                if name in sc.local_names:
                    # The name belongs to THIS function's frame, but has no value yet.
                    if env is not self:
                        raise SicpError("NameError",
                                        f"cannot access free variable '{name}' where it is not associated with a value in enclosing scope",
                                        line)
                    raise SicpError("UnassignedLocalError",
                                    f"cannot access local variable '{name}' where it is not associated with a value",
                                    line)
                if name in sc.global_names:
                    env = env.program          # `global x`: skip straight to the program frame
                    continue
            env = env.parent
        hint = None
        close = suggest(name, self.visible_names())
        if close:
            hint = f"did you mean '{close}'?"
        raise SicpError("NameError", f"name '{name}' is not defined", line, hint)

    def visible_names(self):
        names, env = set(), self
        while env is not None:
            names.update(env.vars)
            env = env.parent
        return names

    # ---------------------------------------------------------------- writing
    def target_env(self, name):
        """Which frame does `name = value` write into?"""
        sc = self.scope
        if sc is not None:
            if name in sc.global_names:
                return self.program
            if name in sc.nonlocal_names:
                env = self.parent
                while env is not None and env.kind == "function":
                    if name in env.vars or name in env.scope.local_names:
                        return env
                    env = env.parent
                return None
        return self

    def assign(self, name, value):
        target = self.target_env(name)
        if target is None:
            raise SicpError("SyntaxError", f"no binding for nonlocal '{name}' found")
        target.vars[name] = value

    def __repr__(self):
        return f"<Environment {self.kind} {self.name}: {sorted(self.vars)}>"
