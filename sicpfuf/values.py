"""
sicpfuf/values.py — what a VALUE is, and how values are shown.

Python §1-§4 have very few kinds of value:

    int  float  complex  str  bool  None        ← sicpfuf uses Python's own
    list   [1, 2, 3]                            ← Python's own list (from §3)
    pair   pair(1, 2)                           ← a list with exactly TWO items!
    function                                    ← Closure (yours) or Builtin (the library's)

THE PAIR SECRET.  In Source Academy's Python, pair(h, t) simply builds the
two-item list [h, t]. That is why print(pair(1, 2)) shows [1, 2], why
llist(1, 2, 3) shows [1, [2, [3, None]]], and why (in §3) is_pair([1, 2]) is True.

A Closure is "a function that remembers where it was born": the tree of its
body (node) plus the environment it was created in (env). In the environment
model you draw it as two circles: one points at the code, one at the frame.
"""


class Closure:
    __slots__ = ("node", "env", "name", "params", "vararg", "is_lambda", "scope", "prelude", "serial")

    def __init__(self, node, env, name, params, vararg, is_lambda, scope, prelude=False):
        self.node = node              # the FunctionDef / Lambda tree
        self.env = env                # the environment the function was CREATED in
        self.name = name              # 'f', or '(anonymous)' for a lambda
        self.params = params          # ['x', 'y']
        self.vararg = vararg          # name of *rest parameter, or None  (§3 and §4)
        self.is_lambda = is_lambda
        self.scope = scope            # ScopeInfo from scopes.py
        self.prelude = prelude        # True for library functions written in Python §2/§3 itself
        self.serial = 0               # numbering for environment diagrams (0 = not numbered yet)

    def __repr__(self):
        return f"<function {self.name}>"


class Builtin:
    """A library function implemented in Python (pair, head, print, math_sqrt, ...)."""
    __slots__ = ("name", "fn", "min_args", "max_args", "needs_interp")

    def __init__(self, name, fn, min_args=0, max_args=None, needs_interp=False):
        self.name, self.fn, self.min_args, self.max_args = name, fn, min_args, max_args
        self.needs_interp = needs_interp        # fn(interp, node, *args) instead of fn(*args)

    def __repr__(self):
        return f"<built-in function {self.name}>"


class TailCall:
    """Not a value! A note that says "the answer is whatever THIS call returns".
    See call_closure in interpreter.py: this is how tail calls avoid piling up."""
    __slots__ = ("func", "args", "node")

    def __init__(self, func, args, node):
        self.func, self.args, self.node = func, args, node


def is_function(v):
    return type(v) is Closure or type(v) is Builtin


def is_pair(v):
    return type(v) is list and len(v) == 2


def type_name(v):
    """The name used in error messages."""
    t = type(v)
    if v is None:
        return "None"
    if t is bool:
        return "bool"
    if t is int:
        return "int"
    if t is float:
        return "float"
    if t is complex:
        return "complex"
    if t is str:
        return "str"
    if t is list:
        return "pair" if len(v) == 2 else "list"
    if t is Closure or t is Builtin:
        return "function"
    return t.__name__


def a(name):
    """'an int' / 'a str' / 'None' — for readable error messages."""
    if name == "None":
        return "None"
    return ("an " if name[0] in "aeiou" else "a ") + name


# ====================================================================== showing values
def show_float(x):
    return repr(x)              # Python's own rule: 1.0, 0.1, 1e+16, inf, nan


def show_string(s):
    """repr of a string: single quotes, unless it has a ' and no " (same rule as Python)."""
    quote = '"' if ("'" in s and '"' not in s) else "'"
    out = [quote]
    for ch in s:
        if ch == quote or ch == "\\":
            out.append("\\" + ch)
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\r":
            out.append("\\r")
        elif ch == "\t":
            out.append("\\t")
        elif not ch.isprintable():
            code = ord(ch)
            out.append(f"\\x{code:02x}" if code < 0x100 else f"\\u{code:04x}" if code < 0x10000 else f"\\U{code:08x}")
        else:
            out.append(ch)
    out.append(quote)
    return "".join(out)


def show_atom(v):
    """Anything that is NOT a list, as it appears INSIDE a list (strings get quotes)."""
    t = type(v)
    if v is None:
        return "None"
    if t is bool:
        return "True" if v else "False"
    if t is float:
        return show_float(v)
    if t is int or t is complex:
        return str(v)
    if t is str:
        return show_string(v)
    return repr(v)                      # Closure / Builtin


MAX_NESTING = 100           # deeper than this prints as ...<truncated>
SPLIT_AT = 80               # longer than this gets split over several lines


class _Dag:
    """A value on its way to becoming text. kind: 't' text, 'p' pair, 'a' longer/shorter list."""
    __slots__ = ("kind", "text", "elems", "length")

    def __init__(self, kind, text, elems, length):
        self.kind, self.text, self.elems, self.length = kind, text, elems, length


def _to_dag(value):
    ancestors = set()               # ids of the lists we are INSIDE right now (to catch cycles)
    memo = {}                       # id(list) → finished _Dag (so shared structure is done once)

    def convert(v):
        if type(v) is not list:
            s = show_atom(v)
            return _Dag("t", s, None, len(s)), False
        if id(v) in ancestors:                       # a list that contains itself
            return _Dag("t", "[...]", None, 5), True
        if len(ancestors) > MAX_NESTING:
            return _Dag("t", "...<truncated>", None, 14), False
        done = memo.get(id(v))
        if done is not None:
            return done, False
        ancestors.add(id(v))
        converted = [convert(x) for x in v]
        ancestors.discard(id(v))
        circular = any(c for _, c in converted)
        elems = [d for d, _ in converted]
        if len(v) == 2:
            length = elems[0].length + elems[1].length + 4
            dag = _Dag("p", None, elems, length)
        else:
            length = 2 + max(0, len(elems) - 1) * 2 + sum(d.length for d in elems)
            dag = _Dag("a", None, elems, length)
        if not circular:
            memo[id(v)] = dag
        return dag, circular

    return convert(value)[0]


def _one_line(dag, out):
    if dag.kind == "t":
        out.append(dag.text)
    else:
        out.append("[")
        for i, e in enumerate(dag.elems):
            if i:
                out.append(", ")
            _one_line(e, out)
        out.append("]")
    return out


def _layout(dag, memo):
    """Decide, bottom-up, which lists fit on one line. Returns ('line', dag) or
    ('block', first_prefix, rest_prefix, [children])."""
    got = memo.get(id(dag))
    if got is not None:
        return got
    if dag.kind == "t":
        result = ("line", dag)
    else:
        kids = [_layout(e, memo) for e in dag.elems]
        too_long = dag.length - 2 > SPLIT_AT
        if too_long or any(k[0] != "line" for k in kids):
            # a pair's tail lines up under its own '[', a longer list indents its items
            result = ("block", "[ ", "" if dag.kind == "p" else "  ", kids)
        else:
            result = ("line", dag)
    memo[id(dag)] = result
    return result


def _render(tree, sep, out):
    if tree[0] == "line":
        _one_line(tree[1], out)
        return
    _, first, rest, kids = tree
    out.append(first)
    _render(kids[0], sep + " " * len(first), out)
    for k in kids[1:]:
        out.append(",")
        out.append(sep + rest)
        _render(k, sep + rest, out)
    out.append("]")


def show_list(value):
    """Lists and pairs, the way Source Academy prints them: on one line if short,
    otherwise one item per line."""
    dag = _to_dag(value)
    out = []
    _render(_layout(dag, {}), "\n", out)
    return "".join(out)


def to_str(v):
    """What print(v) and str(v) show: a string on its own has NO quotes."""
    t = type(v)
    if t is str:
        return v
    if t is list:
        return show_list(v)
    return show_atom(v)


def to_repr(v):
    """What repr(v) shows: strings always get quotes."""
    if type(v) is list:
        return show_list(v)
    return show_atom(v)


def short(v, width=40):
    """A one-line, length-limited picture of a value, for traces and diagrams."""
    if type(v) is list:
        text = "".join(_one_line(_to_dag(v), []))
    else:
        text = show_atom(v)
    return text if len(text) <= width else text[:width - 3] + "..."
