"""
sicpfuf/interpreter.py — WALKS THE TREE and makes things happen.

The whole idea fits in two methods:

    eval(expr_node, env)   →  returns a VALUE        (for Expr nodes)
    exec(stmt_node, env)   →  does something         (for Stmt nodes)

Each kind of node has its own method (eval_BinOp, exec_If, ...) and a dict maps
node class → method.

Three things make Python §1-§4 different from full Python, and all three live here:

  1. BOOLEANS ONLY.   A condition must be exactly True or False. `if n:` is an error.
  2. STRICT OPERATORS. 1 + "a", "ab" * 3 and True + True are errors. Nothing is
                       converted behind your back.
  3. PROPER TAIL CALLS. `return f(...)` with nothing left to do afterwards does NOT
                       keep the caller waiting. An ITERATIVE PROCESS written with
                       recursion therefore runs in constant space (see call_closure).

Statements don't raise exceptions to signal `break`, `continue` or `return`. They
RETURN a signal (BREAK, CONTINUE or a ReturnValue) that each enclosing block passes
upwards until a loop or a function call handles it.
"""

import operator
import sys

from . import nodes as N
from .chapters import check_program
from .env import Environment
from .errors import SicpError
from .parser import parse
from .values import Closure, Builtin, TailCall, type_name, a

# ------------------------------------------------------------- signals
BREAK = "<break>"
CONTINUE = "<continue>"


class ReturnValue:
    __slots__ = ("value",)

    def __init__(self, value):
        self.value = value


RETURN_NONE = ReturnValue(None)

ARITH = {
    "+": operator.add, "-": operator.sub, "*": operator.mul, "/": operator.truediv,
    "//": operator.floordiv, "%": operator.mod, "**": operator.pow,
}
ORDER = {"<": operator.lt, ">": operator.gt, "<=": operator.le, ">=": operator.ge}
COMPLEX_OPS = ("+", "-", "*", "/", "**")
NUMBER = (int, float)
MAX_EQUALITY_STEPS = 5_000_000


def structurally_equal(x, y, forbid=None):
    """Is x == y?  Pairs and lists are compared item by item, all the way down.

    Written with an explicit STACK instead of recursion, so that comparing two
    linked lists with 100 000 items doesn't run out of Python stack.
    `forbid` is called on every pair of values first (§1/§2 use it to reject bools).
    """
    stack = [(x, y)]
    budget = MAX_EQUALITY_STEPS
    while stack:
        p, q = stack.pop()
        if forbid is not None:
            forbid(p, q)
        if p is q:
            continue
        tp, tq = type(p), type(q)
        if tp is list and tq is list:
            if len(p) != len(q):
                return False
            for i in range(len(p) - 1, -1, -1):     # reversed, so the FIRST items are compared first
                stack.append((p[i], q[i]))
            budget -= len(p)
            if budget < 0:
                raise SicpError("RecursionError", "== did not finish (is one of the structures circular?)")
            continue
        if tp is list or tq is list:
            return False
        if not p == q:
            return False
    return True


def identical(x, y):
    """`x is y` in Python §3/§4: the SAME object. Numbers, strings, booleans and None
    have no identity of their own, so for them `is` just compares the values."""
    if x is y:
        return True
    tx = type(x)
    if tx is not type(y):
        return False
    if tx is list or tx is Closure or tx is Builtin:
        return False
    return x == y


class Interpreter:
    def __init__(self, chapter=4, max_depth=1024, out=None, typed=False):
        if chapter not in (1, 2, 3, 4):
            raise ValueError("chapter must be 1, 2, 3 or 4")
        self.chapter = chapter
        self.typed = typed
        self.max_depth = max_depth     # how many calls may be WAITING at once (py-slang: 1024)
        self.out = out or sys.stdout
        self.steps = 0                 # every node evaluated adds 1          (a measure of TIME)
        self.calls = 0                 # how many function calls were made
        self.depth = 0                 # calls waiting for an answer right now (a measure of SPACE)
        self.max_seen = 0              # the deepest `depth` ever got
        self.frames = []               # [(function name, line of the call)] for error messages
        self.envs = []                 # the frame of every call that is running or waiting right now
        self.frame_count = 0           # numbers the frames E1, E2, ... for environment diagrams
        self.closure_count = 0
        self.sources = {}              # filename → list of source lines
        self.hook = None               # x-ray tools plug in here (see xray/calltree.py)
        self.loading_library = False
        self.modules = {}

        # dict-based dispatch: node class → bound method
        self._eval, self._exec = {}, {}
        for cls in vars(N).values():
            if isinstance(cls, type) and issubclass(cls, N.Node):
                for prefix, table in (("eval_", self._eval), ("exec_", self._exec)):
                    m = getattr(self, prefix + cls.__name__, None)
                    if m is not None:
                        table[cls] = m

        from . import lib                         # (imported here to avoid an import cycle)
        self.lib = lib
        self.builtins_env = Environment("builtins", name="builtins")
        self.library_env = Environment("library", self.builtins_env, name="library")
        self.program_env = Environment("program", self.library_env, name="program")
        lib.install(self)

    # ================================================================ running
    def write(self, text):
        self.out.write(text)

    def load_source(self, source, filename="<sicpfuf>"):
        """text → checked tree. Raises SicpSyntaxError if it is not a valid program."""
        self.sources[filename] = source.replace("\r\n", "\n").split("\n")
        tree = parse(source, filename)
        check_program(tree, self.chapter, self.lib.names(self), self.lib.module_exports(),
                      filename, self.typed, self.lib.later_names(self.chapter))
        return tree

    def run_source(self, source, filename="<sicpfuf>"):
        tree = self.load_source(source, filename)
        self.run_tree(tree)
        return self.program_env

    def run_tree(self, tree):
        self.exec_block(tree.body, self.program_env)

    def run_library(self, source, name):
        """Library functions that are themselves written in Python §2/§3 (map, filter, ...)."""
        self.loading_library = True
        try:
            tree = parse(source, f"<{name} library>")
            mark_library(tree)
            self.exec_block(tree.body, self.library_env)
        finally:
            self.loading_library = False

    # ================================================================ core: exec / eval
    def exec(self, node, env):
        self.steps += 1
        return self._exec[node.__class__](node, env)

    def exec_block(self, stmts, env):
        for s in stmts:
            r = self.exec(s, env)
            if r is not None:
                return r
        return None

    def eval(self, node, env):
        self.steps += 1
        return self._eval[node.__class__](node, env)

    def eval_tail(self, node, env):
        """Evaluate an expression whose value is the function's ANSWER (a `return`
        expression, or a lambda's body).

        If that expression is a call f(...), we don't make the call here. We hand
        back a note (TailCall) saying "the answer is whatever f(...) gives", and
        call_closure's loop makes the call AFTER this function's frame is done.
        The same goes for both branches of `a if p else b` and for the LAST
        operand of `and` / `or`: nothing is left to do after them either.
        """
        cls = node.__class__
        if cls is N.Call:
            self.steps += 1
            func = self.eval(node.func, env)
            args = self.eval_args(node.args, env)
            t = type(func)
            if t is Closure:
                return TailCall(func, args, node)
            if t is Builtin:
                return self.call_builtin(func, args, node)
            raise SicpError("TypeError", f"'{type_name(func)}' object is not callable", node.line)
        if cls is N.IfExp:
            self.steps += 1
            test = self.eval(node.test, env)
            if test is True:
                return self.eval_tail(node.body, env)
            if test is False:
                return self.eval_tail(node.orelse, env)
            raise self.not_a_bool("conditional expression condition", test, node)
        if cls is N.BoolOp:
            self.steps += 1
            stop = node.op == "or"                  # `or` stops at the first True, `and` at the first False
            for operand in node.values[:-1]:
                v = self.eval(operand, env)
                if v is stop:
                    return v
                if v is not (not stop):
                    raise self.not_a_bool(f"left operand of '{node.op}'", v, node)
            return self.eval_tail(node.values[-1], env)
        return self.eval(node, env)

    def not_a_bool(self, what, value, node):
        return SicpError("TypeError", f"{what} must be bool, not {type_name(value)}", node.line)

    # ================================================================ simple statements
    def exec_ExprStmt(self, node, env):
        self.eval(node.value, env)

    def exec_Pass(self, node, env):
        return None

    def exec_Break(self, node, env):
        return BREAK

    def exec_Continue(self, node, env):
        return CONTINUE

    def exec_Return(self, node, env):
        if node.value is None:
            return RETURN_NONE
        return ReturnValue(self.eval_tail(node.value, env))

    def exec_Global(self, node, env):          # already handled by scopes.py before running
        return None

    exec_Nonlocal = exec_Global

    def exec_Assign(self, node, env):
        target = node.targets[0]
        if target.__class__ is N.Name:
            env.assign(target.id, self.eval(node.value, env))
            return None
        # xs[i] = value : the right-hand side first, then the list, then the index
        value = self.eval(node.value, env)
        obj = self.eval(target.value, env)
        index = self.eval(target.index, env)
        if type(obj) is not list:
            raise SicpError("TypeError", f"can't assign to an item of {a(type_name(obj))} (only lists)",
                            node.line)
        obj[self.check_index(obj, index, node)] = value
        return None

    def exec_AnnAssign(self, node, env):       # x: int = 5   (typed §4: the type is checked before running)
        env.assign(node.target.id, self.eval(node.value, env))

    def check_index(self, seq, index, node):
        if type(index) is not int:
            raise SicpError("TypeError", f"list indices must be integers, not {type_name(index)}", node.line)
        n = len(seq)
        if not -n <= index < n:
            kind = "string" if type(seq) is str else "list"
            raise SicpError("IndexError", f"{kind} index out of range: index {index}, but the {kind} "
                            f"has {n} item{'' if n == 1 else 's'}", node.line)
        return index

    # ================================================================ control flow
    def exec_If(self, node, env):
        test = self.eval(node.test, env)
        if test is True:
            return self.exec_block(node.body, env)
        if test is False:
            if node.orelse:
                return self.exec_block(node.orelse, env)
            return None
        raise self.not_a_bool("if condition", test, node)

    def exec_While(self, node, env):
        while True:
            test = self.eval(node.test, env)
            if test is False:
                return None
            if test is not True:
                raise self.not_a_bool("while condition", test, node)
            r = self.exec_block(node.body, env)
            if r is not None:
                if r is BREAK:
                    return None
                if r is CONTINUE:
                    continue
                return r                       # a `return` inside the loop

    def exec_For(self, node, env):
        # for i in range(...):   the range is worked out ONCE, before the first round
        args = [self.eval(arg, env) for arg in node.iter.args]
        for v in args:
            if type(v) is not int:
                raise SicpError("TypeError", f"range() needs integers, not {a(type_name(v))}", node.line)
        if len(args) == 3 and args[2] == 0:
            raise SicpError("ValueError", "range() arg 3 must not be zero", node.line)
        name = node.target.id
        for i in range(*args):
            self.steps += 1
            env.assign(name, i)
            r = self.exec_block(node.body, env)
            if r is not None:
                if r is BREAK:
                    return None
                if r is CONTINUE:
                    continue
                return r
        return None

    # ================================================================ definitions
    def exec_FunctionDef(self, node, env):
        env.assign(node.name, self.make_closure(node, env, node.name, False))

    def make_closure(self, node, env, name, is_lambda):
        """A function VALUE = the code + the environment it was created in."""
        params = node.params
        library = self.loading_library or node.lib
        closure = Closure(node, env, name, [p.name for p in params.args], params.vararg,
                          is_lambda, node.scope, library)
        if not library:
            self.closure_count += 1
            closure.serial = self.closure_count
        return closure

    def exec_ImportFrom(self, node, env):
        module = self.lib.load_module(self, node.module)
        for alias in node.names:
            env.assign(alias.asname or alias.name, module[alias.name])

    # ================================================================ expressions
    def eval_Constant(self, node, env):
        return node.value

    def eval_Name(self, node, env):
        return env.lookup(node.id, node.line)

    def eval_ListExpr(self, node, env):
        return [self.eval(e, env) for e in node.elts]

    def eval_Subscript(self, node, env):
        obj = self.eval(node.value, env)
        index = self.eval(node.index, env)
        t = type(obj)
        if t is not list and t is not str:
            raise SicpError("TypeError", f"{a(type_name(obj))} can't be indexed with [ ] (only lists and strings)",
                            node.line)
        return obj[self.check_index(obj, index, node)]

    def eval_Lambda(self, node, env):
        return self.make_closure(node, env, "(anonymous)", True)

    def eval_IfExp(self, node, env):
        test = self.eval(node.test, env)
        if test is True:
            return self.eval(node.body, env)
        if test is False:
            return self.eval(node.orelse, env)
        raise self.not_a_bool("conditional expression condition", test, node)

    def eval_BoolOp(self, node, env):
        # SHORT-CIRCUIT: stop as soon as the answer is known.
        #   False and f()  →  False   (f is never called)
        # Every operand except the last MUST be a boolean. The last one is simply the answer.
        stop = node.op == "or"
        for operand in node.values[:-1]:
            v = self.eval(operand, env)
            if v is stop:
                return v
            if v is not (not stop):
                raise self.not_a_bool(f"left operand of '{node.op}'", v, node)
        return self.eval(node.values[-1], env)

    def eval_UnaryOp(self, node, env):
        v = self.eval(node.operand, env)
        op = node.op
        t = type(v)
        if op == "not":
            if t is bool:
                return not v
            raise SicpError("TypeError", f"operand of 'not' must be bool, not {type_name(v)}", node.line)
        if t is int or t is float or t is complex:
            return -v if op == "-" else v
        raise SicpError("TypeError", f"bad operand type for unary {op}: {type_name(v)}", node.line)

    def eval_BinOp(self, node, env):
        x = self.eval(node.left, env)
        y = self.eval(node.right, env)
        op = node.op
        tx, ty = type(x), type(y)
        try:
            if (tx is int or tx is float) and (ty is int or ty is float):
                return ARITH[op](x, y)
            if tx is str and ty is str and op == "+":
                return x + y
            if tx is complex or ty is complex:
                if (tx is complex or tx in NUMBER) and (ty is complex or ty in NUMBER) and op in COMPLEX_OPS:
                    return ARITH[op](x, y)
            elif op == "*" and self.chapter >= 3:
                if tx is list and ty is int:       # [0] * 3  →  [0, 0, 0]
                    return x * y
                if ty is list and tx is int:
                    return y * x
        except ZeroDivisionError:
            raise SicpError("ZeroDivisionError", "division by zero", node.line) from None
        except OverflowError as e:
            raise SicpError("OverflowError", str(e), node.line) from None
        raise SicpError("TypeError", f"unsupported operand type(s) for {op}: {type_name(x)} and {type_name(y)}",
                        node.line)

    def eval_Compare(self, node, env):
        x = self.eval(node.left, env)
        y = self.eval(node.comparators[0], env)
        op = node.ops[0]
        if op == "==" or op == "!=":
            return self.equal(x, y, node) is (op == "==")
        tx, ty = type(x), type(y)
        if op in ORDER:
            if (tx is int or tx is float) and (ty is int or ty is float):
                return ORDER[op](x, y)
            if tx is str and ty is str:
                return ORDER[op](x, y)                 # alphabetical ("lexicographic") order
            if self.chapter >= 3 and tx in (int, float, bool) and ty in (int, float, bool):
                return ORDER[op](x, y)                 # §3/§4: True counts as 1, False as 0
            raise SicpError("TypeError", f"unsupported operand type(s) for {op}: "
                            f"{type_name(x)} and {type_name(y)}", node.line)
        if op == "is":
            return identical(x, y)
        if op == "is not":
            return not identical(x, y)
        raise SicpError("TypeError", f"unsupported operand type(s) for {op}: {type_name(x)} and {type_name(y)}",
                        node.line)

    def equal(self, x, y, node):
        """x == y.  In §1 and §2, booleans and functions may not be compared at all."""
        tx, ty = type(x), type(y)
        if tx is float and x != x or ty is float and y != y:      # nan equals nothing, not even itself
            return False
        if self.chapter >= 3:
            if tx is not list and ty is not list:
                return x == y
            return structurally_equal(x, y)

        def forbid(p, q):
            tp, tq = type(p), type(q)
            if tp is bool or tq is bool or tp is Closure or tq is Closure or tp is Builtin or tq is Builtin:
                raise SicpError("TypeError", f"unsupported operand type(s) for {node.ops[0]}: "
                                f"{type_name(p)} and {type_name(q)}", node.line)
        forbid(x, y)
        if tx is not list and ty is not list:
            return x == y
        return structurally_equal(x, y, forbid)

    # ---------------------------------------------------------------- calls
    def eval_args(self, arg_nodes, env):
        args = []
        for arg in arg_nodes:
            if arg.__class__ is N.Starred:             # f(*xs)   (§3 and §4)
                v = self.eval(arg.value, env)
                if type(v) is not list:
                    raise SicpError("TypeError", f"can only spread a list with *, not {a(type_name(v))}", arg.line)
                args.extend(v)
            else:
                args.append(self.eval(arg, env))
        return args

    def eval_Call(self, node, env):
        func = self.eval(node.func, env)               # 1. the function expression
        args = self.eval_args(node.args, env)          # 2. the arguments, left to right  (APPLICATIVE ORDER)
        t = type(func)
        if t is Closure:
            return self.call_closure(func, args, node) # 3. apply
        if t is Builtin:
            return self.call_builtin(func, args, node)
        raise SicpError("TypeError", f"'{type_name(func)}' object is not callable", node.line)

    def apply(self, func, args, node=None):
        """Call any function value. Used by builtins that take functions (and by the x-ray tools)."""
        t = type(func)
        if t is Closure:
            return self.call_closure(func, args, node)
        if t is Builtin:
            return self.call_builtin(func, args, node)
        raise SicpError("TypeError", f"'{type_name(func)}' object is not callable", node.line if node else None)

    def call_builtin(self, func, args, node):
        n = len(args)
        line = node.line if node is not None else None
        if n < func.min_args or (func.max_args is not None and n > func.max_args):
            raise SicpError("TypeError", arity_message(func.name, func.min_args, func.max_args, n), line)
        try:
            if func.needs_interp:
                return func.fn(self, node, *args)
            return func.fn(*args)
        except SicpError as e:
            if e.line is None:
                e.line = line
            raise
        except (TypeError, ValueError, ZeroDivisionError, OverflowError, IndexError) as e:
            raise SicpError(type(e).__name__, str(e), line) from None

    def new_frame(self, func, args, node):
        """Rule 2 of the environment model: a NEW frame, whose enclosing environment
        is the one the function was CREATED in. Parameters get the argument values."""
        params = func.params
        n = len(params)
        if len(args) != n if func.vararg is None else len(args) < n:
            line = node.line if node is not None else None
            raise SicpError("TypeError", arity_message(func.name, n, n if func.vararg is None else None,
                                                       len(args)), line)
        env = Environment("function", func.env, func.name, func.scope)
        vars_ = env.vars
        for i in range(n):
            vars_[params[i]] = args[i]
        if func.vararg is not None:
            vars_[func.vararg] = list(args[n:])
        if not func.prelude:
            # Frames are numbered E1, E2, ... for environment diagrams. A frame that would
            # hold NO bindings (no parameters, no local names) is not numbered: diagrams leave
            # empty frames out, and the body simply runs "in" the enclosing environment.
            if vars_ or func.scope.local_names:
                self.frame_count += 1
                env.serial = self.frame_count
            env.call_line = node.line if node is not None else 0
            env.args = args
        return env

    def call_closure(self, func, args, node):
        """Call a function the program defined.

        The `while True` loop is the TRAMPOLINE that gives us proper tail calls:
        when the body's answer is "whatever g(...) returns" (a TailCall note), we
        don't call g from INSIDE this call. We throw the old frame away, and go
        round the loop with g. `depth` (the number of calls that are waiting)
        does not grow, so an iterative process can run for a million rounds.
        """
        if self.depth >= self.max_depth:
            raise SicpError("RecursionError", "maximum recursion depth exceeded",
                            node.line if node is not None else None)
        self.depth += 1
        if self.depth > self.max_seen:
            self.max_seen = self.depth
        frames = self.frames
        frames.append((func.name, node.line if node is not None and not node.lib else 0))
        entry = node                   # the call in YOUR code that got us here (for error reports)
        envs = self.envs
        envs.append(None)
        hook = self.hook
        try:
            tail = False
            while True:
                env = self.new_frame(func, args, node)
                envs[-1] = env
                self.calls += 1
                if hook is not None:
                    hook.enter(func, args, tail, env)
                if func.is_lambda:
                    result = self.eval_tail(func.node.body, env)
                else:
                    r = self.exec_block(func.node.body, env)
                    result = None if r is None else r.value        # no `return` → None
                if type(result) is TailCall:
                    func, args, node = result.func, result.args, result.node
                    if not node.lib:
                        entry = node
                    frames[-1] = (func.name, 0 if node.lib else node.line)
                    tail = True
                    continue
                if hook is not None:
                    hook.leave(result)
                return result
        except SicpError as e:
            if e.calls is None:                        # remember HOW we got here, for the error message
                e.calls = frames[:]
                e.in_library = func.prelude
            if e.in_library and entry is not None and not entry.lib:
                e.line = entry.line                    # blame the line of YOUR call into the library
                e.in_library = False
            if hook is not None:
                hook.failed(e)
            raise
        finally:
            frames.pop()
            envs.pop()
            self.depth -= 1


def arity_message(name, lo, hi, given):
    if hi is None:
        need = f"at least {lo} argument{'' if lo == 1 else 's'}"
    elif lo == hi:
        need = f"exactly {lo} argument{'' if lo == 1 else 's'}"
    else:
        need = f"{lo} to {hi} arguments"
    return f"{name}() takes {need} ({given} given)"


def mark_library(node):
    """Flag every node of a library's tree, so error reports point at YOUR call instead."""
    if isinstance(node, N.Node):
        node.lib = True
        for value in vars(node).values():
            mark_library(value)
    elif isinstance(node, list):
        for item in node:
            mark_library(item)
