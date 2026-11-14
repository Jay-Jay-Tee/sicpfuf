"""
sicpfuf/xray/stepper.py — the SUBSTITUTION MODEL, one step at a time.

    python3 -m sicpfuf program.py -v 1 --subst

    factorial(3)
    -> 1 if 3 == 1 else 3 * factorial(3 - 1)
    -> 1 if False else 3 * factorial(3 - 1)
    -> 3 * factorial(3 - 1)
    -> 3 * factorial(2)
    ...
    -> 3 * (2 * 1)             <- the DEFERRED OPERATIONS of a recursive process
    -> 3 * 2
    -> 6

THE RULES (applicative order, the way Python really evaluates):

    operator combination    evaluate the operands, left to right; then apply the operator
    conditional expression  evaluate the predicate; then keep ONE of the two branches
    function application    evaluate the function expression and the arguments, left to right;
                            then, if the function is PRIMITIVE (print, pair, map, ...), just do it;
                            if it is one of YOURS, replace the application by the function's
                            return expression, with every parameter replaced by its argument

This only works because, in Python §1 and §2, a name gets a value once and keeps
it. So `--subst` refuses Python §3 and §4: once there is reassignment, you need
the environment model (`--estep`).

HOW IT IS BUILT. A program is a tree. One STEP finds the leftmost-innermost
part that can be reduced, and builds a new tree with that part replaced. The
tree is then printed again as text. A function body with several statements is
first rewritten as ONE expression:

    if p: return a  else: return b     becomes     a if p else b
    y = e, then the rest               becomes     { y = e; the rest }
"""

import copy

from .. import nodes as N
from ..errors import SicpError, SicpSyntaxError
from ..interpreter import arity_message
from ..values import Builtin, Closure, show_atom, short, type_name

MAX_SILENT_STEPS = 2_000_000


# ------------------------------------------------------------------ extra tree nodes
class Val(N.Expr):
    """A finished VALUE that has no literal form: a pair, a list, a library function."""

    def __init__(self, value):
        self.value = value


class Fun(N.Expr):
    """The value of a function defined INSIDE another function (after substitution)."""

    def __init__(self, name, params, body, group):
        self.name, self.params, self.body, self.group = name, params, body, group


class Let(N.Expr):
    """{ name = value; body }"""

    def __init__(self, name, value, body):
        self.name, self.value, self.body = name, value, body


class LetFun(N.Expr):
    """{ def name(params): fbody; rest }"""

    def __init__(self, name, params, fbody, rest):
        self.name, self.params, self.fbody, self.rest = name, params, fbody, rest


class Seq(N.Expr):
    """{ first; rest }   (an expression statement, then the rest of the body)"""

    def __init__(self, first, rest):
        self.first, self.rest = first, rest


def const(value, line=0):
    node = N.Constant(value)
    node.line = line
    return node


ATOMS = (int, float, complex, str, bool, type(None))


def block_term(stmts):
    """Rewrite the statements of a function body as ONE expression (see the top of this file)."""
    if not stmts:
        return const(None)
    s, rest = stmts[0], stmts[1:]
    cls = type(s)
    if cls is N.Return:
        return s.value if s.value is not None else const(None, s.line)
    if cls is N.If:
        node = N.IfExp(s.test, block_term(s.body + rest), block_term(s.orelse + rest))
        node.line = s.line
        return node
    if cls is N.Assign:
        node = Let(s.targets[0].id, s.value, block_term(rest))
    elif cls is N.FunctionDef:
        node = LetFun(s.name, [p.name for p in s.params.args], block_term(s.body), block_term(rest))
    elif cls is N.ExprStmt:
        node = Seq(s.value, block_term(rest))
    else:
        raise SicpError("SyntaxError", f"--subst can't step through this kind of statement "
                        f"({cls.__name__}) inside a function", s.line)
    node.line = s.line
    return node


# ------------------------------------------------------------------ tree → text
PREC = {"or": 3, "and": 4, "not": 5, "+": 7, "-": 7, "*": 8, "/": 8, "//": 8, "%": 8, "**": 10}
COMPARE, UNARY, ATOM = 6, 9, 11


class Stepper:
    def __init__(self, interp, limit=400):
        self.interp = interp
        self.limit = limit
        self.printed = 0
        self.functions = {}             # name → (parameter names, body as one expression)
        self.globals = {}               # name → value (a tree), for  name = ...  at the top level
        self.imported = {}              # name → value, for  from module import name
        self.wrappers = {}              # id(function tree) → (tree, stand-in for library functions)
        self.unwrap = {}                # id(stand-in) → function tree
        self.silent = False
        self.last_line = None
        interp._eval[Val] = lambda node, env: node.value

    # ---------------------------------------------------------------- showing
    def text(self, t, prec=0):
        cls = type(t)
        if cls is N.Constant:
            s = show_atom(t.value)
            return f"({s})" if s.startswith("-") and prec > UNARY else s
        if cls is N.Name:
            return t.id
        if cls is Fun:
            return t.name
        if cls is Val:
            return short(t.value, 10 ** 6)
        if cls is N.Lambda:
            s = f"lambda {', '.join(p.name for p in t.params.args)}: {self.text(t.body, 1)}".replace("lambda :", "lambda:")
            return f"({s})" if prec > 1 else s
        if cls is N.IfExp:
            s = f"{self.text(t.body, 3)} if {self.text(t.test, 3)} else {self.text(t.orelse, 2)}"
            return f"({s})" if prec > 2 else s
        if cls is N.BoolOp:
            p = PREC[t.op]
            s = f" {t.op} ".join(self.text(v, p + 1) for v in t.values)
            return f"({s})" if prec > p else s
        if cls is N.UnaryOp:
            if t.op == "not":
                s = "not " + self.text(t.operand, 5)
                return f"({s})" if prec > 5 else s
            s = t.op + self.text(t.operand, UNARY)
            return f"({s})" if prec > UNARY else s
        if cls is N.Compare:
            s = f"{self.text(t.left, COMPARE + 1)} {t.ops[0]} {self.text(t.comparators[0], COMPARE + 1)}"
            return f"({s})" if prec > COMPARE else s
        if cls is N.BinOp:
            p = PREC[t.op]
            if t.op == "**":
                s = f"{self.text(t.left, p + 1)} ** {self.text(t.right, UNARY)}"
            else:
                s = f"{self.text(t.left, p)} {t.op} {self.text(t.right, p + 1)}"
            return f"({s})" if prec > p else s
        if cls is N.Call:
            return f"{self.text(t.func, ATOM)}({', '.join(self.text(x) for x in t.args)})"
        parts = []                                  # a block: { a = 1; def g(...): ...; rest }
        while True:
            cls = type(t)
            if cls is Let:
                parts.append(f"{t.name} = {self.text(t.value)}")
                t = t.body
            elif cls is LetFun:
                parts.append(f"def {t.name}({', '.join(t.params)}): ...")
                t = t.rest
            elif cls is Seq:
                parts.append(self.text(t.first))
                t = t.rest
            else:
                parts.append(self.text(t))
                break
        return "{ " + "; ".join(parts) + " }"

    # ---------------------------------------------------------------- values
    def is_value(self, t):
        cls = type(t)
        if cls is N.Constant or cls is Val or cls is N.Lambda or cls is Fun:
            return True
        return cls is N.Name and t.id not in self.globals

    def real(self, t):
        """The actual Python value of a value-tree (to hand to a primitive or library function)."""
        cls = type(t)
        if cls is N.Constant or cls is Val:
            return t.value
        if cls is N.Name:
            if t.id in self.functions:
                return self.stand_in(("global", t.id), t, t.id, len(self.functions[t.id][0]))
            if t.id in self.imported:
                return self.imported[t.id]
            return self.interp.program_env.lookup(t.id, t.line)
        if cls is N.Lambda:
            return self.stand_in(id(t), t, "(anonymous)", len(t.params.args))
        return self.stand_in(id(t), t, t.name, len(t.params))

    def stand_in(self, key, tree, name, n_params):
        """A library function such as map can't call a tree. So we give it a stand-in that,
        when called, quietly runs the substitution model on  tree(arguments)."""
        if key not in self.wrappers:
            def call(*args):
                node = N.Call(tree, [self.tree_of(x) for x in args], [])
                node.line = getattr(tree, "line", 0)
                return self.real(self.finish(node))
            wrapper = Builtin(name, call, n_params, n_params, label=f"<function {name}>")
            self.wrappers[key] = (tree, wrapper)
            self.unwrap[id(wrapper)] = tree
        return self.wrappers[key][1]

    def tree_of(self, value):
        if id(value) in self.unwrap:
            return self.unwrap[id(value)]
        return const(value) if type(value) in ATOMS else Val(value)

    def finish(self, t):
        """Reduce t all the way to a value WITHOUT printing (used inside library calls)."""
        count = 0
        while not self.is_value(t):
            t = self.step(t)
            count += 1
            if count > MAX_SILENT_STEPS:
                raise SicpError("RecursionError", "the substitution did not finish (no base case?)",
                                getattr(t, "line", None))
        return t

    # ---------------------------------------------------------------- substitution
    def subst(self, t, m):
        """t with every free occurrence of the names in m replaced by their values."""
        if not m:
            return t
        cls = type(t)
        if cls is N.Name:
            return m.get(t.id, t)
        if cls is N.Constant or cls is Val or cls is Fun:
            return t
        new = copy.copy(t)
        if cls is N.BinOp:
            new.left, new.right = self.subst(t.left, m), self.subst(t.right, m)
        elif cls is N.UnaryOp:
            new.operand = self.subst(t.operand, m)
        elif cls is N.Compare:
            new.left, new.comparators = self.subst(t.left, m), [self.subst(t.comparators[0], m)]
        elif cls is N.BoolOp:
            new.values = [self.subst(v, m) for v in t.values]
        elif cls is N.IfExp:
            new.test, new.body, new.orelse = self.subst(t.test, m), self.subst(t.body, m), self.subst(t.orelse, m)
        elif cls is N.Call:
            new.func, new.args = self.subst(t.func, m), [self.subst(x, m) for x in t.args]
        elif cls is N.Lambda:                       # the lambda's own parameters SHADOW outer names
            new.body = self.subst(t.body, without(m, [p.name for p in t.params.args]))
        elif cls is Let:
            new.value, new.body = self.subst(t.value, m), self.subst(t.body, without(m, [t.name]))
        elif cls is LetFun:
            new.fbody = self.subst(t.fbody, without(m, [t.name] + t.params))
            new.rest = self.subst(t.rest, without(m, [t.name]))
        elif cls is Seq:
            new.first, new.rest = self.subst(t.first, m), self.subst(t.rest, m)
        else:
            raise SicpError("SyntaxError", f"--subst can't handle {cls.__name__} here", getattr(t, "line", None))
        return new

    # ---------------------------------------------------------------- one step
    def step(self, t):
        """t is not a value. Returns t with its leftmost-innermost reducible part reduced."""
        cls = type(t)
        if cls is N.Name:                           # a name of the program: replace it by its value
            return self.globals[t.id]
        if cls is N.BinOp:
            if not self.is_value(t.left):
                return self.replace(t, left=self.step(t.left))
            if not self.is_value(t.right):
                return self.replace(t, right=self.step(t.right))
            return self.compute(t, left=t.left, right=t.right)
        if cls is N.UnaryOp:
            if not self.is_value(t.operand):
                return self.replace(t, operand=self.step(t.operand))
            return self.compute(t, operand=t.operand)
        if cls is N.Compare:
            if not self.is_value(t.left):
                return self.replace(t, left=self.step(t.left))
            if not self.is_value(t.comparators[0]):
                return self.replace(t, comparators=[self.step(t.comparators[0])])
            new = copy.copy(t)
            new.left, new.comparators = Val(self.real(t.left)), [Val(self.real(t.comparators[0]))]
            return self.tree_of(self.interp.eval(new, self.interp.program_env))
        if cls is N.BoolOp:
            first = t.values[0]
            if not self.is_value(first):
                return self.replace(t, values=[self.step(first)] + t.values[1:])
            v = self.real(first)
            if type(v) is not bool:
                raise SicpError("TypeError", f"left operand of '{t.op}' must be bool, not {type_name(v)}", t.line)
            if v is (t.op == "or"):                 # the answer is known: the rest is NOT evaluated
                return first
            return t.values[1] if len(t.values) == 2 else self.replace(t, values=t.values[1:])
        if cls is N.IfExp:
            if not self.is_value(t.test):
                return self.replace(t, test=self.step(t.test))
            v = self.real(t.test)
            if type(v) is not bool:
                raise SicpError("TypeError", f"conditional expression condition must be bool, "
                                f"not {type_name(v)}", t.line)
            return t.body if v else t.orelse
        if cls is N.Call:
            if not self.is_value(t.func):
                return self.replace(t, func=self.step(t.func))
            for i, arg in enumerate(t.args):
                if not self.is_value(arg):
                    return self.replace(t, args=t.args[:i] + [self.step(arg)] + t.args[i + 1:])
            return self.apply(t)
        if cls is Let:
            if not self.is_value(t.value):
                return self.replace(t, value=self.step(t.value))
            return self.subst(t.body, {t.name: t.value})
        if cls is LetFun:                           # local functions next to each other may call each other
            group, node = {}, t
            while type(node) is LetFun:
                group[node.name] = Fun(node.name, node.params, node.fbody, group)
                node = node.rest
            self.silent = True
            return self.subst(node, group)
        if cls is Seq:
            if not self.is_value(t.first):
                return self.replace(t, first=self.step(t.first))
            self.silent = True
            return t.rest
        raise SicpError("SyntaxError", f"--subst can't handle {cls.__name__} here", getattr(t, "line", None))

    def replace(self, t, **changes):
        new = copy.copy(t)
        for name, value in changes.items():
            setattr(new, name, value)
        return new

    def compute(self, t, **operands):
        """Apply an operator to finished operands (the real interpreter does the arithmetic)."""
        new = copy.copy(t)
        for name, operand in operands.items():
            setattr(new, name, Val(self.real(operand)))
        return self.tree_of(self.interp.eval(new, self.interp.program_env))

    def apply(self, t):
        f, args = t.func, t.args
        cls = type(f)
        if cls is N.Name and f.id in self.functions:
            params, body = self.functions[f.id]
            name, m = f.id, {}
        elif cls is N.Lambda:
            params, body, name, m = [p.name for p in f.params.args], f.body, "(anonymous)", {}
        elif cls is Fun:
            params, body, name, m = f.params, f.body, f.name, dict(f.group)
        else:                                       # a primitive or library function: just do it
            fn = self.real(f)
            if type(fn) is not Builtin and type(fn) is not Closure:
                raise SicpError("TypeError", f"'{type_name(fn)}' object is not callable", t.line)
            value = self.interp.apply(fn, [self.real(x) for x in args], t)
            self.silent = False
            return self.tree_of(value)
        if len(params) != len(args):
            raise SicpError("TypeError", arity_message(name, len(params), len(params), len(args)), t.line)
        m.update(zip(params, args))
        return self.subst(body, m)

    # ---------------------------------------------------------------- driving
    def show(self, prefix, t, first=False):
        if self.printed >= self.limit:
            raise StopStepping()
        line = prefix + self.text(t)
        if not first and line == self.last_line:    # (-9 computed from -9: nothing new to see)
            return
        self.last_line = line
        self.interp.out.write(("" if first else "-> ") + line + "\n")
        if not first:
            self.printed += 1

    def reduce(self, t, prefix="", hide_none=False):
        """Print t, then every step, until t is a value. Returns the value-tree."""
        self.show(prefix, t, first=True)
        while not self.is_value(t):
            self.silent = False
            t = self.step(t)
            if self.silent or (hide_none and type(t) is N.Constant and t.value is None):
                continue
            self.show(prefix, t)
        return t

    def statement(self, s):
        cls = type(s)
        if cls is N.FunctionDef:
            self.functions[s.name] = ([p.name for p in s.params.args], block_term(s.body))
            self.globals.pop(s.name, None)
        elif cls is N.Assign:
            name = s.targets[0].id
            value = self.reduce(s.value, prefix=f"{name} = ")
            self.interp.out.write("\n")
            self.functions.pop(name, None)
            if type(value) is N.Name:               # another name for an existing function
                if value.id in self.functions:
                    self.functions[name] = self.functions[value.id]
                    return
                value = Val(self.real(value))
            self.globals[name] = value
        elif cls is N.ExprStmt:
            self.reduce(s.value, hide_none=True)
            self.interp.out.write("\n")
        elif cls is N.If:
            test = self.reduce(s.test, prefix="if ")
            v = self.real(test)
            if type(v) is not bool:
                raise SicpError("TypeError", f"if condition must be bool, not {type_name(v)}", s.line)
            self.interp.out.write("\n")
            for inner in (s.body if v else s.orelse):
                self.statement(inner)
        elif cls is N.ImportFrom:
            module = self.interp.lib.load_module(self.interp, s.module)
            for alias in s.names:
                self.imported[alias.asname or alias.name] = module[alias.name]
        else:
            raise SicpError("SyntaxError", f"--subst can't step through {cls.__name__} at the top level", s.line)


class StopStepping(Exception):
    pass


def without(m, names):
    if not any(n in m for n in names):
        return m
    return {k: v for k, v in m.items() if k not in names}


def run(interp, tree, filename, limit=400):
    if interp.chapter > 2:
        raise SicpSyntaxError(
            "the substitution model only works for Python §1 and §2", filename, 1, 0,
            hint="from §3 on, names can be REASSIGNED, so a name can no longer be replaced by its value. "
                 "Run with -v 1 or -v 2, or use --estep to step through the environment model instead.")
    stepper = Stepper(interp, limit)
    real_write = interp.write

    def write(text):                                # what the program prints, marked as such
        real_write("".join("    output: " + line for line in text.splitlines(True)))
    interp.write = write
    try:
        for s in tree.body:
            stepper.statement(s)
    except StopStepping:
        interp.out.write(f"... stopped after {limit} steps (see more with --max-steps N)\n")
    finally:
        interp.write = real_write
