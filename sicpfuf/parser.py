"""
sicpfuf/parser.py — turns a flat list of TOKENS into a TREE (see nodes.py).

This is a RECURSIVE-DESCENT parser: one method per grammar rule, and the
methods call each other (and themselves) recursively, so the shape of the
call stack mirrors the shape of the tree being built.

OPERATOR PRECEDENCE — why does 1 + 2 * 3 give 7 and not 9?
Each level only knows how to parse ITS operator, and asks the next (tighter)
level for its operands:

    expression   →  lambda / ternary  (a if c else b)
    or_test      →  a or b
    and_test     →  a and b
    not_test     →  not a
    comparison   →  a < b == c   in   not in   is   is not
    bit_or       →  a | b
    bit_xor      →  a ^ b
    bit_and      →  a & b
    shift        →  a << b
    arith        →  a + b   a - b
    term         →  a * b   a / b   a // b   a % b
    factor       →  -a   +a   ~a
    power        →  a ** b            (right-associative: 2**3**2 == 2**9)
    primary      →  atom followed by  (call)  [index]  .attribute
    atom         →  42  "hi"  name  (…)  […]  {…}

Because `term` is *below* `arith`, `*` binds tighter than `+`.
This is exactly the ladder in Python's own grammar.

The parser accepts (nearly) all of Python's syntax, far more than Python §1-§4
allow. That is on purpose: chapters.py walks the finished tree and reports
"this feature is not in your chapter" with a helpful message, instead of a bare
"invalid syntax".  (This file is shared with pfuf, sicpfuf's sibling project.)
"""

from . import nodes as N
from .lexer import (tokenize, NAME, NUMBER, STRING, FSTRING, OP, KEYWORD,
                    NEWLINE, INDENT, DEDENT, EOF)
from .errors import SicpSyntaxError
from .scopes import analyze_function

COMPARE_OPS = {"<", ">", "==", ">=", "<=", "!="}
AUG_OPS = {"+=", "-=", "*=", "/=", "//=", "%=", "**=", "&=", "|=", "^=", "<<=", ">>="}
CLOSING = {"(": ")", "[": "]", "{": "}"}


class Parser:
    def __init__(self, tokens, filename="<sicpfuf>"):
        self.tokens = tokens
        self.pos = 0
        self.filename = filename
        self.func_depth = 0     # are we inside a def?  (return / yield need this)
        self.loop_depth = 0     # are we inside a loop? (break / continue need this)

    # ------------------------------------------------------------ token helpers
    @property
    def tok(self):
        return self.tokens[self.pos]

    def peek(self, k=1):
        i = min(self.pos + k, len(self.tokens) - 1)
        return self.tokens[i]

    def next(self):
        t = self.tokens[self.pos]
        if t.type != EOF:
            self.pos += 1
        return t

    def check(self, type_, value=None):
        t = self.tok
        return t.type == type_ and (value is None or t.value == value)

    def check_op(self, value):
        return self.check(OP, value)

    def check_kw(self, value):
        return self.check(KEYWORD, value)

    def match_op(self, value):
        if self.check_op(value):
            return self.next()
        return None

    def match_kw(self, value):
        if self.check_kw(value):
            return self.next()
        return None

    def error(self, msg, tok=None):
        t = tok or self.tok
        raise SicpSyntaxError(msg, self.filename, t.line, t.col)

    def expect_op(self, value, msg=None):
        if not self.check_op(value):
            if value in (")", "]", "}"):
                self.error(msg or f"expected '{value}' (a bracket was never closed?)")
            self.error(msg or f"expected '{value}'")
        return self.next()

    def expect_kw(self, value):
        if not self.check_kw(value):
            self.error(f"expected '{value}'")
        return self.next()

    def expect_name(self, what="a name"):
        if not self.check(NAME):
            t = self.tok
            if t.type == KEYWORD:
                self.error(f"'{t.value}' is a keyword and can't be used as {what}")
            self.error(f"expected {what}")
        return self.next().value

    def mk(self, cls, tok, *args):
        node = cls(*args)
        node.line = tok.line
        node.col = tok.col
        return node

    # ================================================================= program
    def parse_module(self):
        start = self.tok
        body = []
        while not self.check(EOF):
            if self.match(NEWLINE):
                continue
            body.extend(self.statement())
        return self.mk(N.Module, start, body)

    def match(self, type_):
        if self.check(type_):
            return self.next()
        return None

    # ============================================================== statements
    def statement(self):
        """Returns a LIST of statements (a line like `a = 1; b = 2` holds two)."""
        t = self.tok
        if t.type == INDENT:
            raise SicpSyntaxError("unexpected indent", self.filename, t.line, 1, kind="IndentationError")
        if t.type == KEYWORD:
            handler = {
                "if": self.if_stmt, "while": self.while_stmt, "for": self.for_stmt,
                "def": self.def_stmt, "class": self.class_stmt, "try": self.try_stmt,
                "with": self.with_stmt,
            }.get(t.value)
            if handler:
                return [handler()]
        if t.type == OP and t.value == "@":
            return [self.decorated()]
        return self.simple_line()

    def simple_line(self):
        stmts = [self.simple_stmt()]
        if self.check_op(";"):
            self.error("';' is not part of Python §1-§4: write one statement per line")
        if not (self.match(NEWLINE) or self.check(EOF) or self.check(DEDENT)):
            self.error("invalid syntax (two statements on one line? use a new line or ';')")
        return stmts

    def block(self):
        """The indented body after a ':'.  Also allows `if x: y` on one line."""
        if self.check_op("="):
            self.error("invalid syntax. Maybe you meant '==' instead of '='?")
        self.expect_op(":", "expected ':'")
        if not self.match(NEWLINE):
            return self.simple_line()
        while self.match(NEWLINE):
            pass
        if not self.match(INDENT):
            raise SicpSyntaxError("expected an indented block", self.filename, self.tok.line,
                                  self.tok.col, kind="IndentationError")
        body = []
        while not self.check(DEDENT) and not self.check(EOF):
            if self.match(NEWLINE):
                continue
            body.extend(self.statement())
        self.match(DEDENT)
        return body

    # ---------------------------------------------------------- simple ones
    def simple_stmt(self):
        t = self.tok
        if t.type == KEYWORD:
            kw = t.value
            if kw == "pass":
                self.next(); return self.mk(N.Pass, t)
            if kw in ("break", "continue"):
                self.next()             # (chapters.py checks that we are inside a loop)
                return self.mk(N.Break if kw == "break" else N.Continue, t)
            if kw == "return":
                self.next()
                if self.func_depth == 0:
                    self.error("'return' outside function", t)
                value = None if self.at_stmt_end() else self.expr_list()
                return self.mk(N.Return, t, value)
            if kw == "yield":
                self.next()
                if self.func_depth == 0:
                    self.error("'yield' outside function", t)
                if self.match_kw("from"):
                    return self.mk(N.YieldFrom, t, self.expression())
                value = None if self.at_stmt_end() else self.expr_list()
                return self.mk(N.Yield, t, value)
            if kw in ("global", "nonlocal"):
                self.next()
                names = [self.expect_name()]
                while self.match_op(","):
                    names.append(self.expect_name())
                return self.mk(N.Global if kw == "global" else N.Nonlocal, t, names)
            if kw == "import":
                return self.import_stmt()
            if kw == "from":
                return self.from_import()
            if kw == "raise":
                self.next()
                exc = None if self.at_stmt_end() else self.expression()
                if self.match_kw("from"):       # `raise X from Y` — we keep X, ignore Y
                    self.expression()
                return self.mk(N.Raise, t, exc)
            if kw == "assert":
                self.next()
                test = self.expression()
                msg = self.expression() if self.match_op(",") else None
                return self.mk(N.Assert, t, test, msg)
            if kw == "del":
                self.next()
                targets = [self.primary_or_target()]
                while self.match_op(","):
                    targets.append(self.primary_or_target())
                for tg in targets:
                    self.check_target(tg, "delete")
                return self.mk(N.Delete, t, targets)
        return self.expr_or_assign()

    def at_stmt_end(self):
        return self.check(NEWLINE) or self.check(EOF) or self.check_op(";") or self.check(DEDENT)

    def primary_or_target(self):
        return self.bit_or()

    def expr_or_assign(self):
        t = self.tok
        first = self.expr_list(allow_star=True)

        # x: int = 5   (type annotations are parsed and then ignored, just like at runtime in Python)
        if self.check_op(":") and isinstance(first, (N.Name, N.Attribute, N.Subscript)):
            self.next()
            annotation = self.expression()
            value = self.expr_list() if self.match_op("=") else None
            return self.mk(N.AnnAssign, t, first, annotation, value)

        if self.check_op("="):
            targets = [first]
            while self.match_op("="):
                if self.check_kw("yield"):
                    self.error("`yield` is not part of Python §1-§4")
                targets.append(self.expr_list(allow_star=True))
            value = targets.pop()
            for tg in targets:
                self.check_target(tg, "assign to")
            return self.mk(N.Assign, t, targets, value)

        if self.tok.type == OP and self.tok.value in AUG_OPS:
            op = self.next().value[:-1]           # '+=' → '+'
            if not isinstance(first, (N.Name, N.Attribute, N.Subscript)):
                self.error(f"'{type(first).__name__}' is an illegal expression for augmented assignment", t)
            return self.mk(N.AugAssign, t, first, op, self.expr_list())

        if isinstance(first, N.Starred):
            self.error("can't use starred expression here", t)
        return self.mk(N.ExprStmt, t, first)

    def check_target(self, node, verb):
        if isinstance(node, (N.Name, N.Attribute, N.Subscript)):
            return
        if isinstance(node, (N.TupleExpr, N.ListExpr)):
            for e in node.elts:
                if isinstance(e, N.Starred):
                    self.error("starred assignment (a, *rest = ...) is not part of Python §1-§4")
                self.check_target(e, verb)
            return
        what = {N.Call: "function call", N.Constant: "literal", N.Compare: "comparison",
                N.BinOp: "expression"}.get(type(node), "expression")
        msg = f"cannot {verb} {what}"
        if verb == "assign to" and what in ("literal", "function call"):
            msg += " (did you mean '==' ?)"
        raise SicpSyntaxError(msg, self.filename, node.line, 1)

    def dotted_name(self):
        name = self.expect_name("a module name")
        while self.match_op("."):
            name += "." + self.expect_name("a module name")
        return name

    def import_stmt(self):
        t = self.next()
        names = []
        while True:
            name = self.dotted_name()
            asname = self.expect_name() if self.match_kw("as") else None
            names.append(self.mk(N.Alias, t, name, asname))
            if not self.match_op(","):
                break
        return self.mk(N.Import, t, names)

    def from_import(self):
        t = self.next()
        module = self.dotted_name()
        self.expect_kw("import")
        if self.match_op("*"):
            return self.mk(N.ImportFrom, t, module, [self.mk(N.Alias, t, "*", None)])
        paren = self.match_op("(")
        names = []
        while True:
            name = self.expect_name()
            asname = self.expect_name() if self.match_kw("as") else None
            names.append(self.mk(N.Alias, t, name, asname))
            if not self.match_op(","):
                break
            if paren and self.check_op(")"):
                break
        if paren:
            self.expect_op(")")
        return self.mk(N.ImportFrom, t, module, names)

    # -------------------------------------------------------- compound ones
    def if_stmt(self):
        t = self.next()                      # 'if' or 'elif'
        test = self.expression()
        body = self.block()
        orelse = []
        if self.check_kw("elif"):
            orelse = [self.if_stmt()]        # elif = an if nested inside else. Recursion!
        elif self.match_kw("else"):
            orelse = self.block()
        return self.mk(N.If, t, test, body, orelse)

    def loop_body(self):
        self.loop_depth += 1
        try:
            return self.block()
        finally:
            self.loop_depth -= 1

    def while_stmt(self):
        t = self.next()
        test = self.expression()
        body = self.loop_body()
        orelse = self.block() if self.match_kw("else") else []
        return self.mk(N.While, t, test, body, orelse)

    def for_stmt(self):
        t = self.next()
        target = self.target_list()
        self.expect_kw("in")
        it = self.expr_list()
        body = self.loop_body()
        orelse = self.block() if self.match_kw("else") else []
        return self.mk(N.For, t, target, it, body, orelse)

    def target_list(self):
        """Loop / comprehension targets:  x    i, x    (k, v)"""
        t = self.tok
        first = self.bit_or()
        if not self.check_op(","):
            self.check_target(first, "assign to")
            return first
        elts = [first]
        while self.match_op(","):
            if self.check_kw("in"):
                break
            elts.append(self.bit_or())
        node = self.mk(N.TupleExpr, t, elts)
        self.check_target(node, "assign to")
        return node

    def decorated(self):
        decorators = []
        while self.match_op("@"):
            decorators.append(self.expression())
            if not self.match(NEWLINE):
                self.error("expected a new line after the decorator")
        if self.check_kw("def"):
            node = self.def_stmt()
        elif self.check_kw("class"):
            node = self.class_stmt()
        else:
            self.error("a decorator must be followed by 'def' or 'class'")
        node.decorators = decorators
        return node

    def def_stmt(self):
        t = self.next()
        name = self.expect_name("a function name")
        self.expect_op("(", "expected '(' after the function name")
        params = self.params(closing=")")
        self.expect_op(")")
        returns = self.expression() if self.match_op("->") else None    # def f() -> int
        saved_loop = self.loop_depth
        self.func_depth += 1
        self.loop_depth = 0                # `break` inside a def doesn't belong to an outer loop
        try:
            body = self.block()
        finally:
            self.func_depth -= 1
            self.loop_depth = saved_loop
        node = self.mk(N.FunctionDef, t, name, params, body, [], returns)
        analyze_function(node, self.filename)          # work out locals/globals (scopes.py)
        return node

    def params(self, closing):
        """Parameter list for def (closing=')') or lambda (closing=':')."""
        t = self.tok
        args, kwonly, vararg, kwarg = [], [], None, None
        seen_default = False
        names = set()

        def add_name(n, tok):
            if n in names:
                self.error(f"duplicate argument '{n}' in function definition", tok)
            names.add(n)

        while not self.check_op(closing):
            tok = self.tok
            if self.match_op("**"):
                kwarg = self.expect_name("a parameter name")
                add_name(kwarg, tok)
                self.skip_annotation(closing)
                self.match_op(",")
                break
            if self.match_op("*"):
                if vararg is not None:
                    self.error("only one *args parameter is allowed")
                if self.check(NAME):
                    vararg = self.expect_name()
                    add_name(vararg, tok)
                    self.skip_annotation(closing)
                else:
                    vararg = ""                 # bare `*` → following params are keyword-only
            else:
                pname = self.expect_name("a parameter name")
                add_name(pname, tok)
                annotation = self.skip_annotation(closing)
                default = None
                if self.match_op("="):
                    default = self.expression()
                    seen_default = True
                elif seen_default and vararg is None:
                    self.error("non-default argument follows default argument", tok)
                p = self.mk(N.Param, tok, pname, default, annotation)
                (kwonly if vararg is not None else args).append(p)
            if not self.match_op(","):
                break
        return self.mk(N.Params, t, args, vararg or None, kwonly, kwarg)

    def skip_annotation(self, closing):
        """`x: int` in a def's parameter list. Returns the annotation expression (or None)."""
        if closing == ")" and self.match_op(":"):
            return self.expression()
        return None

    def class_stmt(self):
        t = self.next()
        name = self.expect_name("a class name")
        bases = []
        if self.match_op("("):
            while not self.check_op(")"):
                bases.append(self.expression())
                if not self.match_op(","):
                    break
            self.expect_op(")")
        saved = (self.func_depth, self.loop_depth)
        self.func_depth, self.loop_depth = 0, 0
        try:
            body = self.block()
        finally:
            self.func_depth, self.loop_depth = saved
        return self.mk(N.ClassDef, t, name, bases, body, [])

    def try_stmt(self):
        t = self.next()
        body = self.block()
        handlers, orelse, finalbody = [], [], []
        while self.check_kw("except"):
            ht = self.next()
            etype, name = None, None
            if not self.check_op(":"):
                etype = self.expression()
                if self.match_kw("as"):
                    name = self.expect_name()
            handlers.append(self.mk(N.ExceptHandler, ht, etype, name, self.block()))
        if self.match_kw("else"):
            if not handlers:
                self.error("'else' after 'try' needs at least one 'except'")
            orelse = self.block()
        if self.match_kw("finally"):
            finalbody = self.block()
        if not handlers and not finalbody:
            self.error("expected 'except' or 'finally' block")
        return self.mk(N.Try, t, body, handlers, orelse, finalbody)

    def with_stmt(self):
        t = self.next()
        items = []
        while True:
            it = self.tok
            ctx = self.expression()
            target = None
            if self.match_kw("as"):
                target = self.bit_or()
                self.check_target(target, "assign to")
            items.append(self.mk(N.WithItem, it, ctx, target))
            if not self.match_op(","):
                break
        return self.mk(N.With, t, items, self.block())

    # ============================================================= expressions
    def expr_list(self, allow_star=False):
        """`a`  or  `a, b, c` (a tuple without brackets, as in  return x, y)."""
        t = self.tok
        first = self.star_or_expr() if allow_star else self.expression()
        if not self.check_op(","):
            return first
        elts = [first]
        while self.match_op(","):
            if self.at_stmt_end() or self.check_op("=") or self.check_op(":") or \
                    (self.tok.type == OP and self.tok.value in AUG_OPS):
                break
            elts.append(self.star_or_expr() if allow_star else self.expression())
        return self.mk(N.TupleExpr, t, elts)

    def star_or_expr(self):
        t = self.tok
        if self.match_op("*"):
            return self.mk(N.Starred, t, self.bit_or())
        return self.expression()

    def expression(self):
        t = self.tok
        if self.check_kw("lambda"):
            return self.lambda_expr()
        if self.check_kw("yield"):
            self.error("`yield` is not part of Python §1-§4")
        body = self.or_test()
        if self.match_kw("if"):
            test = self.or_test()
            self.expect_kw("else")
            orelse = self.expression()
            return self.mk(N.IfExp, t, test, body, orelse)
        return body

    def lambda_expr(self):
        t = self.next()
        params = self.params(closing=":")
        self.expect_op(":")
        body = self.expression()
        node = self.mk(N.Lambda, t, params, body)
        analyze_function(node, self.filename)
        return node

    def or_test(self):
        t = self.tok
        left = self.and_test()
        if not self.check_kw("or"):
            return left
        values = [left]
        while self.match_kw("or"):
            values.append(self.and_test())
        return self.mk(N.BoolOp, t, "or", values)

    def and_test(self):
        t = self.tok
        left = self.not_test()
        if not self.check_kw("and"):
            return left
        values = [left]
        while self.match_kw("and"):
            values.append(self.not_test())
        return self.mk(N.BoolOp, t, "and", values)

    def not_test(self):
        t = self.tok
        if self.match_kw("not"):
            return self.mk(N.UnaryOp, t, "not", self.not_test())
        return self.comparison()

    def comparison(self):
        t = self.tok
        left = self.bit_or()
        ops, rights = [], []
        while True:
            tok = self.tok
            if tok.type == OP and tok.value in COMPARE_OPS:
                ops.append(self.next().value)
            elif self.check_kw("in"):
                self.next(); ops.append("in")
            elif self.check_kw("not") and self.peek().type == KEYWORD and self.peek().value == "in":
                self.next(); self.next(); ops.append("not in")
            elif self.check_kw("is"):
                self.next()
                ops.append("is not" if self.match_kw("not") else "is")
            else:
                break
            rights.append(self.bit_or())
        if not ops:
            return left
        return self.mk(N.Compare, t, left, ops, rights)

    def binary_level(self, next_level, operators):
        """Shared loop for left-associative levels:  a - b - c  ==  (a - b) - c"""
        t = self.tok
        left = next_level()
        while self.tok.type == OP and self.tok.value in operators:
            op = self.next().value
            left = self.mk(N.BinOp, t, left, op, next_level())
        return left

    def bit_or(self):
        return self.binary_level(self.bit_xor, ("|",))

    def bit_xor(self):
        return self.binary_level(self.bit_and, ("^",))

    def bit_and(self):
        return self.binary_level(self.shift, ("&",))

    def shift(self):
        return self.binary_level(self.arith, ("<<", ">>"))

    def arith(self):
        return self.binary_level(self.term, ("+", "-"))

    def term(self):
        return self.binary_level(self.factor, ("*", "/", "//", "%", "@"))

    def factor(self):
        t = self.tok
        if t.type == OP and t.value in ("-", "+", "~"):
            self.next()
            return self.mk(N.UnaryOp, t, t.value, self.factor())
        return self.power()

    def power(self):
        t = self.tok
        base = self.primary()
        if self.match_op("**"):
            # right side is a *factor*, which can contain another **  →  right-associative
            return self.mk(N.BinOp, t, base, "**", self.factor())
        return base

    def primary(self):
        node = self.atom()
        while True:
            t = self.tok
            if self.match_op("("):
                node = self.call(node, t)
            elif self.match_op("["):
                node = self.mk(N.Subscript, t, node, self.subscript())
                self.expect_op("]")
            elif self.match_op("."):
                node = self.mk(N.Attribute, t, node, self.expect_name("an attribute name"))
            else:
                return node

    def call(self, func, t):
        args, keywords = [], []
        while not self.check_op(")"):
            at = self.tok
            if self.match_op("*"):
                args.append(self.mk(N.Starred, at, self.expression()))
            elif self.match_op("**"):
                keywords.append(self.mk(N.Keyword, at, None, self.expression()))
            elif self.check(NAME) and self.peek().type == OP and self.peek().value == "=":
                name = self.next().value
                self.next()
                keywords.append(self.mk(N.Keyword, at, name, self.expression()))
            else:
                if keywords:
                    self.error("positional argument follows keyword argument")
                arg = self.expression()
                if self.check_kw("for"):            # f(x for x in xs)
                    arg = self.mk(N.GeneratorExp, at, arg, self.comp_for())
                args.append(arg)
            if not self.match_op(","):
                break
        self.expect_op(")")
        return self.mk(N.Call, t, func, args, keywords)

    def subscript(self):
        t = self.tok
        items = [self.slice_item()]
        while self.match_op(","):
            if self.check_op("]"):
                break
            items.append(self.slice_item())
        return items[0] if len(items) == 1 else self.mk(N.TupleExpr, t, items)

    def slice_item(self):
        t = self.tok
        lower = upper = step = None
        if not self.check_op(":"):
            lower = self.expression()
            if not self.check_op(":"):
                return lower                       # plain index: xs[i]
        self.expect_op(":")
        if not self.check_op(":") and not self.check_op("]") and not self.check_op(","):
            upper = self.expression()
        if self.match_op(":"):
            if not self.check_op("]") and not self.check_op(","):
                step = self.expression()
        return self.mk(N.Slice, t, lower, upper, step)

    # ------------------------------------------------------------------ atoms
    def atom(self):
        t = self.tok
        if t.type == NUMBER:
            self.next(); return self.mk(N.Constant, t, t.value)
        if t.type in (STRING, FSTRING):
            return self.strings()
        if t.type == NAME:
            self.next(); return self.mk(N.Name, t, t.value)
        if t.type == KEYWORD and t.value in ("True", "False", "None"):
            self.next()
            return self.mk(N.Constant, t, {"True": True, "False": False, "None": None}[t.value])
        if t.type == OP:
            if t.value == "(":
                return self.paren()
            if t.value == "[":
                return self.list_display()
            if t.value == "{":
                return self.brace_display()
            if t.value in (")", "]", "}"):
                self.error(f"unmatched '{t.value}'")
        if t.type in (NEWLINE, EOF):
            self.error("invalid syntax (the line ended too early, is something missing?)")
        if t.type == KEYWORD:
            self.error(f"invalid syntax: '{t.value}' can't be used here")
        self.error("invalid syntax")

    def strings(self):
        """Adjacent string literals are joined:  "ab" "cd"  ==  "abcd"."""
        t = self.tok
        parts, any_f = [], False
        while self.tok.type in (STRING, FSTRING):
            s = self.next()
            if s.type == FSTRING:
                any_f = True
                parts.extend(self.parse_fstring(s.value, s))
            else:
                parts.append(self.mk(N.Constant, s, s.value))
        kinds = {type(p.value) for p in parts if isinstance(p, N.Constant)}
        if bytes in kinds and (str in kinds or any_f):
            self.error("cannot mix bytes and nonbytes literals", t)
        if bytes in kinds:
            return self.mk(N.Constant, t, b"".join(p.value for p in parts))
        if not any_f:
            return self.mk(N.Constant, t, "".join(p.value for p in parts))
        return self.mk(N.FString, t, parts)

    def parse_fstring(self, text, tok):
        """Split  'Hi {name!r:>10}, {{literal}}'  into constant and {expression} parts.
        Each {expression} is handed to a brand-new Lexer + Parser. Recursion!"""
        parts, buf, i = [], [], 0
        while i < len(text):
            ch = text[i]
            if ch == "{" and text[i:i + 2] == "{{":
                buf.append("{"); i += 2; continue
            if ch == "}" and text[i:i + 2] == "}}":
                buf.append("}"); i += 2; continue
            if ch == "}":
                self.error("f-string: single '}' is not allowed (write '}}' for a literal brace)", tok)
            if ch != "{":
                buf.append(ch); i += 1; continue
            if buf:
                parts.append(self.mk(N.Constant, tok, "".join(buf))); buf = []
            # find the matching '}' (respecting nested brackets and quotes)
            depth, j, quote = 0, i + 1, None
            while j < len(text):
                c = text[j]
                if quote:
                    if c == quote:
                        quote = None
                elif c in "'\"":
                    quote = c
                elif c in "([{":
                    depth += 1
                elif c in ")]}":
                    if c == "}" and depth == 0:
                        break
                    depth -= 1
                j += 1
            else:
                self.error("f-string: expecting '}'", tok)
            inner = text[i + 1:j]
            i = j + 1
            parts.append(self.fstring_field(inner, tok))
        if buf:
            parts.append(self.mk(N.Constant, tok, "".join(buf)))
        return parts

    def fstring_field(self, inner, tok):
        # split off  :spec  and  !conversion  at bracket depth 0
        depth, quote, cut = 0, None, len(inner)
        for k, c in enumerate(inner):
            if quote:
                if c == quote:
                    quote = None
            elif c in "'\"":
                quote = c
            elif c in "([{":
                depth += 1
            elif c in ")]}":
                depth -= 1
            elif depth == 0 and c == ":":
                cut = k
                break
            elif depth == 0 and c == "!" and inner[k + 1:k + 2] in ("r", "s", "a") \
                    and inner[k + 2:k + 3] in ("", ":"):
                cut = k
                break
        expr_text, rest = inner[:cut], inner[cut:]
        conversion = spec = None
        if rest.startswith("!"):
            conversion, rest = rest[1], rest[2:]
        if rest.startswith(":"):
            spec_text = rest[1:]
            spec_parts = self.parse_fstring(spec_text, tok) if "{" in spec_text else \
                [self.mk(N.Constant, tok, spec_text)]
            spec = self.mk(N.FString, tok, spec_parts)
        debug = None
        stripped = expr_text.rstrip()
        if stripped.endswith("=") and not stripped.endswith(("==", "!=", "<=", ">=")):
            debug = expr_text                      # f"{x=}"  shows  x=<value>
            expr_text = stripped[:-1]
            if conversion is None and spec is None:
                conversion = "r"
        if not expr_text.strip():
            self.error("f-string: empty expression not allowed", tok)
        sub = Parser(tokenize("(" + expr_text.strip() + ")", self.filename, tok.line - 1), self.filename)
        expr = sub.expression()
        return self.mk(N.FormattedValue, tok, expr, conversion, spec, debug)

    def paren(self):
        t = self.next()                                   # '('
        if self.match_op(")"):
            return self.mk(N.TupleExpr, t, [])
        first = self.star_or_expr()
        if self.check_kw("for"):
            node = self.mk(N.GeneratorExp, t, first, self.comp_for())
            self.expect_op(")")
            return node
        if self.match_op(")"):
            return first                                  # just grouping: (a + b)
        elts = [first]
        while self.match_op(","):
            if self.check_op(")"):
                break
            elts.append(self.star_or_expr())
        self.expect_op(")")
        return self.mk(N.TupleExpr, t, elts)              # (a, b)  or  (a,)

    def list_display(self):
        t = self.next()                                   # '['
        if self.match_op("]"):
            return self.mk(N.ListExpr, t, [])
        first = self.star_or_expr()
        if self.check_kw("for"):
            node = self.mk(N.ListComp, t, first, self.comp_for())
            self.expect_op("]")
            return node
        elts = [first]
        while self.match_op(","):
            if self.check_op("]"):
                break
            elts.append(self.star_or_expr())
        self.expect_op("]")
        return self.mk(N.ListExpr, t, elts)

    def brace_display(self):
        t = self.next()                                   # '{'
        if self.match_op("}"):
            return self.mk(N.DictExpr, t, [], [])         # {} is a DICT, not a set!
        if self.match_op("**"):
            keys, values = [None], [self.bit_or()]
            return self.dict_rest(t, keys, values)
        first = self.star_or_expr()
        if self.match_op(":"):
            value = self.expression()
            if self.check_kw("for"):
                node = self.mk(N.DictComp, t, first, value, self.comp_for())
                self.expect_op("}")
                return node
            return self.dict_rest(t, [first], [value])
        if self.check_kw("for"):
            node = self.mk(N.SetComp, t, first, self.comp_for())
            self.expect_op("}")
            return node
        elts = [first]
        while self.match_op(","):
            if self.check_op("}"):
                break
            elts.append(self.star_or_expr())
        self.expect_op("}")
        return self.mk(N.SetExpr, t, elts)

    def dict_rest(self, t, keys, values):
        while self.match_op(","):
            if self.check_op("}"):
                break
            if self.match_op("**"):
                keys.append(None); values.append(self.bit_or())
                continue
            keys.append(self.expression())
            self.expect_op(":")
            values.append(self.expression())
        self.expect_op("}")
        return self.mk(N.DictExpr, t, keys, values)

    def comp_for(self):
        """for x in xs if c   (one or more times)"""
        gens = []
        while self.check_kw("for"):
            t = self.next()
            target = self.target_list()
            self.expect_kw("in")
            it = self.or_test()
            ifs = []
            while self.match_kw("if"):
                ifs.append(self.or_test())
            gens.append(self.mk(N.Comprehension, t, target, it, ifs))
        return gens


def parse(source, filename="<sicpfuf>"):
    return Parser(tokenize(source, filename), filename).parse_module()
