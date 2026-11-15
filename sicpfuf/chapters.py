"""
sicpfuf/chapters.py — the CHAPTER CHECKER: is this program really Python §1, §2, §3 or §4?

The course language grows chapter by chapter:

    §1   names, functions, conditionals, lambda           (no reassignment, no loops)
    §2   + pairs and linked lists                         (still no reassignment)
    §3   + reassignment, loops, lists [...], mutation, streams
    §4   + parse(...) and friends for the metacircular evaluator

The parser accepts almost all of Python. This file then walks the finished tree
ONCE, before anything runs, and rejects three kinds of mistake:

  1. a FEATURE your chapter doesn't have  ("for loops" in §1, "x += 1" anywhere)
  2. a name that is used but DECLARED nowhere                    (NameNotFoundError)
  3. in §1 and §2, giving a name a value TWICE                   (NameReassignmentError)

Because the check runs before the program does, these errors appear even if the
offending line would never be reached, and nothing is printed first.

Rule 3 is what makes the SUBSTITUTION MODEL work: if a name can never change,
you may always replace the name by its value.
"""

from . import nodes as N
from .errors import SicpSyntaxError, suggest
from .scopes import scan_block

BITWISE = {"&", "|", "^", "<<", ">>"}
MODULES = ("rune", "curve", "sound", "repeat")


class Scope:
    """What the checker knows about one function body (or the whole program)."""

    def __init__(self, kind, names, parent=None, info=None, params=()):
        self.kind = kind                    # 'program' or 'function'
        self.names = set(names)             # every name DECLARED in this scope
        self.parent = parent
        self.info = info                    # ScopeInfo from scopes.py (functions only)
        self.given = set(params)            # names that already HAVE a value (for rule 3)
        self.loops = 0                      # how many loops are we inside? (for break / continue)


class Checker:
    def __init__(self, chapter, builtin_names, module_exports, filename="<sicpfuf>", typed=False):
        self.chapter = chapter
        self.builtins = set(builtin_names)
        self.module_exports = module_exports        # {'rune': {'show', 'heart', ...}, ...}
        self.filename = filename
        self.typed = typed
        self.scope = None
        self.header_ranges = set()                  # ids of the `range` names in for-loop headers

    # ------------------------------------------------------------------ errors
    def unsupported(self, feature, node):
        where = f"Python §{self.chapter}" if feature in EARLY_ONLY else "Python §1-§4"
        message = RULE_MESSAGES.get(feature, f"{where} does not have this: {feature}")
        raise SicpSyntaxError(message,
                              self.filename, node.line, node.col,
                              kind=f"Feature not supported in this sublanguage: {feature}",
                              hint=FEATURE_HINTS.get(feature))

    def fail(self, kind, msg, node, hint=None):
        raise SicpSyntaxError(msg, self.filename, node.line, node.col, kind=kind, hint=hint)

    # ------------------------------------------------------------------ entry
    def check(self, tree):
        info = {"assigned": set(), "global": set(), "nonlocal": set()}
        scan_block(tree.body, info)
        names = set(info["assigned"])
        names |= self.names_made_global(tree.body)
        self.scope = Scope("program", names)
        self.block(tree.body)

    def names_made_global(self, stmts):
        """A function that says `global x` and assigns x DECLARES x for the whole program."""
        found = set()

        def walk(body):
            for s in body:
                if isinstance(s, N.FunctionDef):
                    found.update(s.scope.global_names)
                    walk(s.body)
                elif isinstance(s, (N.If, N.While, N.For)):
                    walk(s.body)
                    walk(s.orelse)
        walk(stmts)
        return found

    # ------------------------------------------------------------------ statements
    def block(self, stmts):
        for s in stmts:
            self.stmt(s)

    def stmt(self, s):
        method = getattr(self, "s_" + type(s).__name__, None)
        if method is None:
            self.unsupported(STATEMENT_FEATURES.get(type(s).__name__, "this kind of statement"), s)
        method(s)

    def s_ExprStmt(self, s):
        self.expr(s.value)

    def s_Pass(self, s):
        if self.chapter < 3:
            self.unsupported("pass statements", s)

    def s_Break(self, s):
        if self.chapter < 3:
            self.unsupported("break statements", s)
        if self.scope.loops == 0:
            self.fail("SyntaxError", "'break' outside loop", s)

    def s_Continue(self, s):
        if self.chapter < 3:
            self.unsupported("continue statements", s)
        if self.scope.loops == 0:
            self.fail("SyntaxError", "'continue' not properly in loop", s)

    def s_Global(self, s):
        if self.chapter < 3:
            self.unsupported("global statements", s)

    def s_Nonlocal(self, s):
        if self.chapter < 3:
            self.unsupported("nonlocal statements", s)
        for name in s.names:
            sc, ok = self.scope.parent, False
            while sc is not None and sc.kind == "function":
                if name in sc.names:
                    ok = True
                    break
                sc = sc.parent
            if not ok:
                self.fail("SyntaxError", f"no binding for nonlocal '{name}' found", s,
                          "nonlocal only reaches names of an ENCLOSING FUNCTION. For a name of the "
                          "whole program, use `global`.")

    def s_Return(self, s):
        if s.value is not None:
            self.expr(s.value)

    def s_Assert(self, s):
        self.unsupported("assertion messages" if s.msg is not None else "assert statements", s)

    def s_Assign(self, s):
        if len(s.targets) > 1:
            self.fail("SyntaxError", "chained assignment (a = b = ...) is not part of Python §1-§4", s,
                      "write one assignment per line.")
        target = s.targets[0]
        if isinstance(target, N.ListExpr):
            self.fail("SyntaxError", "assignment to a list of names is not part of Python §1-§4", s)
        if isinstance(target, N.TupleExpr):
            self.unsupported("assignment to several names (a, b = ...)", s)
        if isinstance(target, N.Attribute):
            self.unsupported("assignment to attributes (a.b = ...)", s)
        if isinstance(target, N.Subscript):
            self.expr(s.value)
            self.expr(target)                 # xs[i] = v changes a list; it does not declare a name
            return
        self.declare(target.id, target)
        self.expr(s.value)

    def s_AnnAssign(self, s):
        if not self.typed:
            self.unsupported("annotated assignment statements", s)
        if s.value is None:
            self.unsupported("declarations without a value", s)
        self.declare(s.target.id, s.target)
        self.expr(s.value)

    def s_TypeAlias(self, s):                    # type Rat = Pair[int, int]
        if not self.typed:
            self.unsupported("type statements", s)
        # (the type itself is checked by xray/typecheck.py; it is not a value)

    def s_AugAssign(self, s):
        self.unsupported(f"augmented assignment ({s.op}=)", s)

    def s_If(self, s):
        self.expr(s.test)
        self.block(s.body)
        self.block(s.orelse)

    def s_While(self, s):
        if s.orelse:
            self.fail("SyntaxError", "`while ... else` is not part of Python §1-§4", s)
        if self.chapter < 3:
            self.unsupported("while loops", s)
        self.expr(s.test)
        self.loop_body(s.body)

    def loop_body(self, stmts):
        self.scope.loops += 1
        try:
            self.block(stmts)
        finally:
            self.scope.loops -= 1

    def s_For(self, s):
        if s.orelse:
            self.fail("SyntaxError", "`for ... else` is not part of Python §1-§4", s)
        if self.chapter < 3:
            self.unsupported("for loops", s)
        if not isinstance(s.target, N.Name):
            self.unsupported("unpacking in for loops (for a, b in ...)", s)
        it = s.iter
        if not (isinstance(it, N.Call) and isinstance(it.func, N.Name) and it.func.id == "range"
                and 1 <= len(it.args) <= 3 and not it.keywords):
            self.unsupported("for loops must use range() — e.g. for i in range(n)", s)
        self.header_ranges.add(id(it.func))
        self.declare(s.target.id, s.target)
        self.expr(it)
        self.loop_body(s.body)

    def s_ImportFrom(self, s):
        if any(alias.name == "*" for alias in s.names):
            self.fail("SyntaxError", "import * is not part of Python §1-§4", s)
        exports = self.module_exports.get(s.module)
        if exports is None:
            self.fail("ModuleNotFoundError", f"there is no module named '{s.module}'", s,
                      "sicpfuf has these modules: " + ", ".join(MODULES) + ".")
        for alias in s.names:
            if alias.name == "*":
                self.unsupported("import *", s)
            if alias.name not in exports:
                close = suggest(alias.name, exports)
                self.fail("ImportError", f"module '{s.module}' has no name '{alias.name}'", s,
                          f"did you mean '{close}'?" if close else None)
            self.declare(alias.asname or alias.name, s)

    def s_FunctionDef(self, s):
        if s.decorators:
            self.unsupported("decorators", s.decorators[0])
        self.declare(s.name, s)
        self.function(s, s.name)

    # ------------------------------------------------------------------ declarations
    def declare(self, name, node):
        if self.chapter >= 3 and name == "range":
            self.fail("SyntaxError", "'range' is reserved and cannot be redefined", node)
        if self.chapter < 3:
            if name in self.scope.given:
                self.fail("NameReassignmentError", f"the name '{name}' already has a value", node,
                          "in Python §1 and §2 a name gets its value ONCE and keeps it. That is what "
                          "lets you replace a name by its value (the substitution model). "
                          "Pick a new name instead. (A parameter counts as already having a value, and "
                          "so does a name assigned in the other branch of an if/else.)")
            self.scope.given.add(name)

    def function(self, node, name):
        params = node.params
        for p in params.args + params.kwonly:
            if p.default is not None:
                self.unsupported("default values of parameters (name=value)", node)
        if params.kwarg:
            self.unsupported("keyword parameters (**kwargs)", node)
        if params.kwonly:
            self.fail("SyntaxError", "keyword-only parameters are not part of Python §1-§4", node)
        if params.vararg and self.chapter < 3:
            self.unsupported("rest parameters (*name)", node)
        if not self.typed:
            if getattr(node, "type_params", None):
                self.unsupported("type parameters", node)
            for p in params.args:
                if p.annotation is not None:
                    self.unsupported("type annotations", p)
            if getattr(node, "returns", None) is not None:
                self.unsupported("type annotations", node)
        names = [p.name for p in params.args] + ([params.vararg] if params.vararg else [])
        if self.chapter >= 3 and "range" in names:
            self.fail("SyntaxError", "'range' is reserved and cannot be redefined", node)
        outer = self.scope
        self.scope = Scope("function", node.scope.local_names, outer, node.scope, names)
        try:
            if isinstance(node, N.Lambda):
                self.expr(node.body)
            else:
                self.block(node.body)
        finally:
            self.scope = outer

    # ------------------------------------------------------------------ expressions
    def expr(self, e):
        method = getattr(self, "e_" + type(e).__name__, None)
        if method is None:
            self.unsupported(EXPRESSION_FEATURES.get(type(e).__name__, "this kind of expression"), e)
        method(e)

    def e_FString(self, e):
        self.fail("SyntaxError", "f-strings are not part of Python §1-§4", e,
                  "build the string with + and str(...):  \"n is \" + str(n)")

    def e_Constant(self, e):
        if isinstance(e.value, bytes):
            self.unsupported("bytes literals", e)

    def e_Name(self, e):
        name = e.id
        if name == "range" and id(e) not in self.header_ranges:
            if self.chapter >= 3:
                self.fail("SyntaxError",
                          "'range' can only be used in a for-loop header, as in 'for i in range(n):'", e,
                          "write `for i in range(n):`. In Python §3 and §4 range is not a function "
                          "you can call or store anywhere else.")
            self.not_found(e)
        if name == "range":
            return
        sc = self.scope
        while sc is not None:
            info = sc.info
            if info is not None and name in info.global_names:
                sc = self.program_scope()
                continue
            if name in sc.names:
                return
            sc = sc.parent
        if name in self.builtins:
            return
        self.not_found(e)

    def program_scope(self):
        sc = self.scope
        while sc.parent is not None:
            sc = sc.parent
        return sc

    def not_found(self, e):
        visible = set(self.builtins)
        sc = self.scope
        while sc is not None:
            visible |= sc.names
            sc = sc.parent
        close = suggest(e.id, visible)
        hint = f"did you mean '{close}'?" if close else (
            "every name must be declared somewhere: by `name = ...`, by `def name(...)`, as a parameter, "
            "or by `from module import name`.")
        if close is None and e.id in LATER_NAMES and self.chapter < LATER_NAMES[e.id]:
            hint = f"'{e.id}' only exists from Python §{LATER_NAMES[e.id]} on. This program runs as §{self.chapter}."
        self.fail("NameNotFoundError", f"the name '{e.id}' is not found in the current or enclosing "
                  f"environment(s)", e, hint)

    def e_ListExpr(self, e):
        if self.chapter < 3:
            self.unsupported("list literals", e)
        for x in e.elts:
            if isinstance(x, N.Starred):
                self.unsupported("unpacking in list displays ([*a, b])", e)
            self.expr(x)

    def e_Subscript(self, e):
        if self.chapter < 3:
            self.unsupported("subscript expressions", e)
        if isinstance(e.index, N.Slice):
            self.unsupported("slices (a[i:j])", e)
        self.expr(e.value)
        self.expr(e.index)

    def e_BinOp(self, e):
        if e.op in BITWISE:
            self.unsupported(f"bitwise operators ({e.op})", e)
        if e.op == "@":
            self.unsupported("matrix multiplication (@)", e)
        self.expr(e.left)
        self.expr(e.right)

    def e_UnaryOp(self, e):
        if e.op == "~":
            self.unsupported("bitwise operators (~)", e)
        self.expr(e.operand)

    def e_BoolOp(self, e):
        for v in e.values:
            self.expr(v)

    def e_Compare(self, e):
        if len(e.ops) > 1:
            self.unsupported("chained comparisons (a < b < c)", e)
        if e.ops[0] in ("is", "is not") and self.chapter < 3:
            self.unsupported("is operator", e)
        self.expr(e.left)
        self.expr(e.comparators[0])

    def e_IfExp(self, e):
        self.expr(e.test)
        self.expr(e.body)
        self.expr(e.orelse)

    def e_Lambda(self, e):
        self.function(e, "(anonymous)")

    def e_Call(self, e):
        for k in e.keywords:
            self.unsupported("dictionary unpacking (**)" if k.name is None
                             else "keyword arguments (name=value)", e)
        self.expr(e.func)
        for arg in e.args:
            if isinstance(arg, N.Starred):
                if self.chapter < 3:
                    self.unsupported("spread expressions (*expr)", arg)
                self.expr(arg.value)
            elif isinstance(arg, N.GeneratorExp):
                self.unsupported("generator expressions", arg)
            else:
                self.expr(arg)

    def e_Starred(self, e):
        self.unsupported("spread expressions (*expr)", e)


STATEMENT_FEATURES = {
    "ClassDef": "classes", "Try": "exceptions (try/except/finally)", "Raise": "exceptions (raise)",
    "With": "with statements", "Delete": "del statements",
    "Import": "import statements (use from ... import ...)",
    "Yield": "generators (yield)", "YieldFrom": "generators (yield from)",
}

EXPRESSION_FEATURES = {
    "TupleExpr": "tuples", "DictExpr": "dictionaries", "SetExpr": "set displays",
    "ListComp": "list comprehensions", "SetComp": "set comprehensions",
    "DictComp": "dictionary comprehensions", "GeneratorExp": "generator expressions",
    "Attribute": "attribute access (a.b)", "Slice": "slices (a[i:j])",
    "FString": "f-strings", "FormattedValue": "f-strings",
}

# features that are really RULES (they read badly as "X is not part of ...")
RULE_MESSAGES = {
    "for loops must use range() — e.g. for i in range(n)":
        "a for loop can only go over range(...), as in: for i in range(n):",
}

# features that a LATER chapter does have (the message names your chapter, not "§1-§4")
EARLY_ONLY = {
    "list literals", "subscript expressions", "while loops", "for loops", "break statements",
    "continue statements", "global statements", "nonlocal statements", "pass statements",
    "rest parameters (*name)", "spread expressions (*expr)", "is operator",
}

FEATURE_HINTS = {
    "for loops": "loops arrive in Python §3. In §1 and §2, repeat things with recursion.",
    "while loops": "loops arrive in Python §3. In §1 and §2, repeat things with recursion.",
    "list literals": "[...] lists arrive in Python §3. In §2, build a linked list with llist(1, 2, 3) or pair(1, None).",
    "subscript expressions": "xs[i] arrives in Python §3. For a linked list use llist_ref(xs, i), head and tail.",
    "is operator": "`is` arrives in Python §3. Compare numbers and strings with ==.",
    "pass statements": "`pass` arrives in Python §3.",
    "global statements": "`global` arrives in Python §3, together with reassignment.",
    "nonlocal statements": "`nonlocal` arrives in Python §3, together with reassignment.",
    "tuples": "there are no tuples in Python §1-§4. Did a stray comma sneak in? For two values, use pair(a, b).",
    "attribute access (a.b)": "there are no methods in Python §1-§4: write len(xs) and not xs.length, "
                              "math_sqrt(x) and not math.sqrt(x). Lists cannot grow (no xs.append).",
    "chained comparisons (a < b < c)": "write the two comparisons out: `a < b and b < c`.",
    "f-strings": "build the string with + and str(...): \"n is \" + str(n).",
    "keyword arguments (name=value)": "pass arguments by position only.",
    "default values of parameters (name=value)": "every parameter must be passed explicitly.",
    "for loops must use range() — e.g. for i in range(n)":
        "a for loop can only count: `for i in range(len(xs)):` and then use xs[i].",
    "dictionaries": "there are no dictionaries in Python §1-§4. Use a list, or a linked list of pairs.",
    "list comprehensions": "use a loop, or map/filter on a linked list.",
    "slices (a[i:j])": "there are no slices in Python §1-§4. Copy the items in a loop.",
    "assignment to several names (a, b = ...)": "write one assignment per line (use a temporary name to swap).",
    "import statements (use from ... import ...)": "write `from rune import show, heart`.",
}
for _op in ("+", "-", "*", "/", "//", "%", "**"):
    FEATURE_HINTS[f"augmented assignment ({_op}=)"] = f"write it out in full: x = x {_op} ..."

# names that appear only from a later chapter on (for a friendlier NameNotFoundError)
LATER_NAMES = {}


def check_program(tree, chapter, builtin_names, module_exports, filename="<sicpfuf>", typed=False,
                  later_names=None):
    """Raise SicpSyntaxError if `tree` is not a valid Python §`chapter` program."""
    if later_names:
        LATER_NAMES.update(later_names)
    Checker(chapter, builtin_names, module_exports, filename, typed).check(tree)
