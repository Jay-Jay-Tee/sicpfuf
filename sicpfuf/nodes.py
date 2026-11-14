"""
sicpfuf/nodes.py — the shapes of the ABSTRACT SYNTAX TREE (AST).

The parser turns tokens into a TREE of these objects. For example

    total = price * 2

becomes

    Assign
    ├─ targets: Name id='total'
    └─ value: BinOp op='*'
       ├─ left: Name id='price'
       └─ right: Constant value=2

SYLLABUS LESSONS IN THIS FILE
  * Classes & objects, inheritance  — every node is a class; they all inherit from
                                      Node, and split into Expr (produces a value)
                                      and Stmt (does something).
  * Polymorphism                    — the interpreter treats every node the same way
                                      ("evaluate it") but each class behaves differently.
  * Trees                           — the whole program is one tree; Module is the root.

@dataclass writes __init__ and __repr__ for us, a nice example of a *decorator*
generating code. Real Python has the same idea in its `ast` module:
    python3 -c "import ast; print(ast.dump(ast.parse('x = 1 + 2'), indent=2))"
"""

from dataclasses import dataclass, field, fields
from typing import List, Optional, Any


class Node:
    """Base class for every tree node. `line` and `col` are filled in by the parser."""
    line = 0
    col = 0
    lib = False                 # True for nodes of library code (so error reports can skip them)


class Expr(Node):
    """Something that produces a VALUE:  3,  x + 1,  f(2),  [a, b]"""


class Stmt(Node):
    """Something that DOES something:  x = 3,  if ...:,  return x"""
    contains_yield = False      # set by scopes.py; tells the interpreter to run it lazily


# ============================================================== expressions
@dataclass
class Constant(Expr):
    value: Any                  # 42, 3.14, "hi", True, None


@dataclass
class Name(Expr):
    id: str                     # a variable name


@dataclass
class FormattedValue(Expr):     # one {expr!r:spec} piece of an f-string
    value: Expr
    conversion: Optional[str]   # 'r', 's', 'a' or None
    spec: Optional[Expr]        # the part after ':'  (itself an f-string!)
    debug_text: Optional[str]   # for f"{x=}" this is "x="


@dataclass
class FString(Expr):
    parts: List[Expr]           # Constants and FormattedValues, joined at runtime


@dataclass
class ListExpr(Expr):
    elts: List[Expr]


@dataclass
class TupleExpr(Expr):
    elts: List[Expr]


@dataclass
class SetExpr(Expr):
    elts: List[Expr]


@dataclass
class DictExpr(Expr):
    keys: List[Optional[Expr]]  # None key means  **other_dict
    values: List[Expr]


@dataclass
class Starred(Expr):            # *xs inside a call or a list/tuple/set display
    value: Expr


@dataclass
class BinOp(Expr):
    left: Expr
    op: str                     # '+', '-', '*', '/', '//', '%', '**', '&', '|', ...
    right: Expr


@dataclass
class UnaryOp(Expr):
    op: str                     # '-', '+', '~', 'not'
    operand: Expr


@dataclass
class BoolOp(Expr):
    op: str                     # 'and' / 'or'
    values: List[Expr]


@dataclass
class Compare(Expr):            # a < b <= c   →  left=a, ops=['<','<='], comparators=[b,c]
    left: Expr
    ops: List[str]
    comparators: List[Expr]


@dataclass
class IfExp(Expr):              # body if test else orelse
    test: Expr
    body: Expr
    orelse: Expr


@dataclass
class Param(Node):
    name: str
    default: Optional[Expr]
    annotation: Optional[Expr] = None   # def f(x: int)  (only typed §4 uses these)


@dataclass
class Params(Node):
    args: List[Param]           # normal parameters
    vararg: Optional[str]       # *args
    kwonly: List[Param]         # parameters after *args (must be passed by keyword)
    kwarg: Optional[str]        # **kwargs


@dataclass
class Lambda(Expr):
    params: Params
    body: Expr


@dataclass
class Keyword(Node):
    name: Optional[str]         # None means **mapping
    value: Expr


@dataclass
class Call(Expr):
    func: Expr
    args: List[Expr]
    keywords: List[Keyword]


@dataclass
class Attribute(Expr):          # value.attr
    value: Expr
    attr: str


@dataclass
class Subscript(Expr):          # value[index]
    value: Expr
    index: Expr


@dataclass
class Slice(Expr):              # lower:upper:step
    lower: Optional[Expr]
    upper: Optional[Expr]
    step: Optional[Expr]


@dataclass
class Comprehension(Node):      # for target in iter if cond1 if cond2
    target: Expr
    iter: Expr
    ifs: List[Expr]


@dataclass
class ListComp(Expr):
    elt: Expr
    generators: List[Comprehension]


@dataclass
class SetComp(Expr):
    elt: Expr
    generators: List[Comprehension]


@dataclass
class DictComp(Expr):
    key: Expr
    value: Expr
    generators: List[Comprehension]


@dataclass
class GeneratorExp(Expr):
    elt: Expr
    generators: List[Comprehension]


# =============================================================== statements
@dataclass
class Module(Stmt):
    body: List[Stmt]


@dataclass
class ExprStmt(Stmt):
    value: Expr


@dataclass
class Assign(Stmt):             # a = b = value   → targets=[a, b]
    targets: List[Expr]
    value: Expr


@dataclass
class AnnAssign(Stmt):          # x: int = 5      (value may be None for a bare `x: int`)
    target: Expr
    annotation: Expr
    value: Optional[Expr]


@dataclass
class AugAssign(Stmt):          # x += 1
    target: Expr
    op: str
    value: Expr


@dataclass
class If(Stmt):
    test: Expr
    body: List[Stmt]
    orelse: List[Stmt]          # elif is just an If inside orelse!


@dataclass
class While(Stmt):
    test: Expr
    body: List[Stmt]
    orelse: List[Stmt]          # runs if the loop ended WITHOUT break


@dataclass
class For(Stmt):
    target: Expr
    iter: Expr
    body: List[Stmt]
    orelse: List[Stmt]


@dataclass
class Break(Stmt):
    pass


@dataclass
class Continue(Stmt):
    pass


@dataclass
class Pass(Stmt):
    pass


@dataclass
class Return(Stmt):
    value: Optional[Expr]


@dataclass
class Yield(Stmt):              # parsed only so chapters.py can say "not in §1-§4"
    value: Optional[Expr]


@dataclass
class YieldFrom(Stmt):          # yield from iterable  → yield each item in turn
    value: Expr


@dataclass
class FunctionDef(Stmt):
    name: str
    params: Params
    body: List[Stmt]
    decorators: List[Expr]
    returns: Optional[Expr] = None      # def f() -> int   (only typed §4 uses these)


@dataclass
class ClassDef(Stmt):
    name: str
    bases: List[Expr]
    body: List[Stmt]
    decorators: List[Expr]


@dataclass
class Global(Stmt):
    names: List[str]


@dataclass
class Nonlocal(Stmt):
    names: List[str]


@dataclass
class Alias(Node):              # `name as asname`
    name: str
    asname: Optional[str]


@dataclass
class Import(Stmt):
    names: List[Alias]


@dataclass
class ImportFrom(Stmt):
    module: str
    names: List[Alias]          # name '*' means "import everything"


@dataclass
class Raise(Stmt):
    exc: Optional[Expr]


@dataclass
class ExceptHandler(Node):
    type: Optional[Expr]        # None means bare `except:`
    name: Optional[str]
    body: List[Stmt]


@dataclass
class Try(Stmt):
    body: List[Stmt]
    handlers: List[ExceptHandler]
    orelse: List[Stmt]          # runs if NO exception happened
    finalbody: List[Stmt]       # ALWAYS runs


@dataclass
class Assert(Stmt):
    test: Expr
    msg: Optional[Expr]


@dataclass
class Delete(Stmt):
    targets: List[Expr]


@dataclass
class WithItem(Node):
    context: Expr
    target: Optional[Expr]


@dataclass
class With(Stmt):
    items: List[WithItem]
    body: List[Stmt]


# ===================================================== pretty-printing a tree
def format_ast(node):
    """Draw the tree with box characters. Used by  `python3 -m sicpfuf --ast file.py`.

    This is a RECURSIVE function on a TREE: print this node, then
    call yourself on every child with a longer prefix.
    """
    lines = []

    def label(n):
        parts = [type(n).__name__]
        for f in fields(n):
            v = getattr(n, f.name)
            if isinstance(v, list) and v and not any(isinstance(x, Node) for x in v):
                parts.append(f"{f.name}={v!r}")          # e.g. ops=['<', '<=']
            elif not isinstance(v, (Node, list)) and v is not None:
                parts.append(f"{f.name}={v!r}")
        return "  ".join(parts)

    def children(n):
        out = []
        for f in fields(n):
            v = getattr(n, f.name)
            if isinstance(v, Node):
                out.append((f.name, v))
            elif isinstance(v, list) and v and all(isinstance(x, Node) for x in v):
                for i, x in enumerate(v):
                    out.append((f"{f.name}[{i}]" if len(v) > 1 else f.name, x))
        return out

    def walk(n, prefix, is_last, name):
        connector = "" if name is None else ("└─ " if is_last else "├─ ")
        tag = "" if name is None else f"{name}: "
        lines.append(f"{prefix}{connector}{tag}{label(n)}")
        kids = children(n)
        child_prefix = prefix + ("" if name is None else ("   " if is_last else "│  "))
        for i, (cname, c) in enumerate(kids):
            walk(c, child_prefix, i == len(kids) - 1, cname)

    walk(node, "", True, None)
    return "\n".join(lines)
