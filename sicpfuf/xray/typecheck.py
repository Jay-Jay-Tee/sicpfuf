"""
sicpfuf/xray/typecheck.py — the TYPE CHECKER of Python §4 Typed.

    python3 -m sicpfuf prog.py -v 4 --typed

Python §4 Typed is Python §4 plus TYPE ANNOTATIONS:

    def length2(xs: LList[int]) -> int:
        return 0 if is_none(xs) else 1 + length2(tail(xs))

    sq: Callable[[int], int] = lambda x: x * x

Before the program runs, this file reads the whole program and works out the TYPE
of every expression, without running anything. If some line can go wrong ("you pass
a str where an int is wanted", "head of a list that may be empty") the program is
REJECTED with all the errors, and nothing runs. Otherwise the program runs as plain
Python §4: the annotations change nothing at run time.

Source Academy's implementation (py-slang) uses Pyright, a real Python type checker,
for this. sicpfuf has its own, much smaller checker, written to be READ. It follows
Pyright's rules and words its messages as py-slang does, so the same program gets
the same verdict and (mostly) the same messages.

THE BIG IDEAS IN THIS FILE

  1. TYPES ARE VALUES TOO.  Every type is a small Python object: Prim('int'),
     PairT(head, tail), FuncT(params, ret), Union(...), Alias('LList', [int]) ...
     (section 1)

  2. ASSIGNABILITY.  "Can a value of type S go where type T is wanted?"
     int can go where float is wanted; int can go where int | None is wanted;
     LList[int] can NOT go where Pair[int, ...] is wanted (it may be None).
     (`assignable`, section 3)

  3. INFERENCE, outside-in and inside-out.  The type of `1 + 2` is worked out from
     its parts (inside-out). But a lambda has no annotations, so it gets its
     parameter types from WHERE IT IS USED: the declared type of a variable, or
     the parameter of the function it is passed to (outside-in, "the EXPECTED
     type"). (section 5)

  4. FLOW.  The checker walks the program like the interpreter would, but on
     types. After `if is_none(xs): return 0`, it knows that xs is a pair: that is
     NARROWING. Each point of the program has a STATE: the type each name has
     there. Two branches meet → their states are JOINED (types united).
     (sections 4 and 6)

  5. GENERICS.  `def head[H, T](p: Pair[H, T]) -> H` works for any H and T.
     At each call the checker SOLVES the type variables from the arguments:
     head(pair(1, "a")) has H = int, T = str, so the call has type int. (section 5)
"""

import re

from .. import nodes as N
from ..errors import SicpSyntaxError
from ..parser import parse


# =====================================================================================
# 1. TYPES
# =====================================================================================
# Every type has a KEY: a tuple that says what it is. Two types are the same type
# exactly when their keys are equal. show() gives the type as a student writes it.

class Type:
    def key(self):
        raise NotImplementedError

    def __eq__(self, other):
        return isinstance(other, Type) and self.key() == other.key()

    def __hash__(self):
        return hash(self.key())

    def __repr__(self):
        return show(self)


class Prim(Type):
    """int, float, complex, str, bool, None, object, and the checker's LiteralString."""

    def __init__(self, name):
        self.name = name

    def key(self):
        return ("prim", self.name)


class StrLit(Prim):
    """A str that is known to come from a string LITERAL ("abc"). It is the same type as
    str, except for one detail of Pyright that shows in messages: a literal times an int
    is a "LiteralString"."""

    def __init__(self):
        super().__init__("str")


class Unknown(Type):
    """A type the checker could not work out. `report=True`: Pyright would not know it
    either (after an error, or a lambda without a context), and an assignment of it is
    reported. `report=False`: a name sicpfuf knows but has no type for (a module's
    functions): never reported."""

    def __init__(self, report):
        self.report = report

    def key(self):
        return ("unknown", self.report)


class AnyT(Type):
    """What the checker knows of the parts of an `object` after is_pair(x) or is_list(x):
    anything at all. (It is no type a program can write; messages show it as object.)"""

    def key(self):
        return ("any",)


class Never(Type):
    """The type of something that never produces a value: error(...) does not return."""

    def key(self):
        return ("never",)


class Unbound(Type):
    """(Not a real type.) A name of this scope that has no value yet at this point."""

    def key(self):
        return ("unbound",)


class PairT(Type):
    def __init__(self, head, tail):
        self.head, self.tail = head, tail

    def key(self):
        return ("pair", self.head.key(), self.tail.key())


class ListT(Type):
    def __init__(self, elem):
        self.elem = elem

    def key(self):
        return ("list", self.elem.key())


class FuncT(Type):
    """A function type.  params: [(name, type)];  `named`: a def or lambda (messages say
    `(x: int) -> int`) or a Callable[...] (messages say `(int) -> int`).
    `vararg`: (name, type) of *xs.  `required`: how many params need an argument.
    `tparams`: the type variables of a generic function.  `name`: for messages."""

    def __init__(self, params, ret, named=True, name=None, vararg=None, tparams=(),
                 required=None, posonly=False, any_params=False):
        self.params, self.ret, self.named, self.name = list(params), ret, named, name
        self.vararg, self.tparams, self.posonly, self.any_params = vararg, tuple(tparams), posonly, any_params
        self.required = len(self.params) if required is None else required

    def key(self):
        return ("func", tuple(t.key() for _, t in self.params), self.ret.key(),
                self.vararg[1].key() if self.vararg else None, self.any_params,
                tuple(v.key() for v in self.tparams))


class Union(Type):
    def __init__(self, members):
        self.members = tuple(members)

    def key(self):
        return ("union", frozenset(m.key() for m in self.members))


class TVar(Type):
    """A TYPE VARIABLE, the A in `def ident[A](x: A) -> A`. `owner` tells apart the A of
    two different functions."""

    def __init__(self, name, owner):
        self.name, self.owner = name, owner

    def key(self):
        return ("tvar", self.name, self.owner)


class Alias(Type):
    """A named type: LList[int], Stream[str], or the program's own `type Rat = ...`.
    Its meaning is in ALIASES (expand() looks it up). `bare` only changes how it is
    SHOWN: inside its own definition Pyright writes LList, not LList[int]."""

    def __init__(self, name, args, bare=False):
        self.name, self.args, self.bare = name, tuple(args), bare

    def key(self):
        return ("alias", self.name, tuple(a.key() for a in self.args))


INT, FLOAT, COMPLEX, STR, BOOL = Prim("int"), Prim("float"), Prim("complex"), Prim("str"), Prim("bool")
NONE, OBJECT, LITSTR, RANGE = Prim("None"), Prim("object"), Prim("LiteralString"), Prim("range")
STRLIT = StrLit()
UNK, UNMODELED, NEVER, UNBOUND, ANY = Unknown(True), Unknown(False), Never(), Unbound(), AnyT()
NUMBERS = ("int", "float", "complex")

# What an alias means: name → (its type parameters, its definition). LList and Stream are
# predeclared; `type X = ...` statements add more.
_X = TVar("X", "alias")
PREDECLARED_ALIASES = {
    "LList": ([_X], Union([PairT(_X, Alias("LList", [_X], bare=True)), NONE])),
    "Stream": ([_X], Union([PairT(_X, FuncT([], Alias("Stream", [_X], bare=True), named=False)), NONE])),
}
ALIASES = dict(PREDECLARED_ALIASES)


def union(types):
    """The union of some types, flattened, without repeats. Never disappears in a union,
    and a single type is just itself."""
    out, seen = [], set()
    for t in types:
        for m in (t.members if isinstance(t, Union) else (t,)):
            if isinstance(m, (Never, Unbound)) or m.key() in seen:
                continue
            seen.add(m.key())
            out.append(m)
    if not out:
        return NEVER
    return out[0] if len(out) == 1 else Union(out)


def widen(t):
    """Forget that a str came from a literal (what a variable remembers for later)."""
    if isinstance(t, StrLit) or t is LITSTR:
        return STR
    if isinstance(t, Union):
        return union(widen(m) for m in t.members)
    return t


def unbare(t):
    return Alias(t.name, t.args) if isinstance(t, Alias) and t.bare else t


def expand(t):
    """LList[int] → Pair[int, LList[int]] | None: the meaning of an alias, one level deep."""
    params, body = ALIASES[t.name]
    return subst(body, dict(zip(params, t.args)))


def members(t):
    """The alternatives of a type: the members of a union, with aliases expanded."""
    if isinstance(t, Alias) and t.name in ALIASES:
        return members(expand(t))
    if isinstance(t, Union):
        out = []
        for m in t.members:
            out.extend(members(m))
        return out
    return [t]


def subst(t, m, unsolved=None):
    """Replace type variables by what `m` says. A variable that `m` does not know stays,
    or becomes `unsolved` if that is given (Pyright makes it Unknown)."""
    if not m and unsolved is None:
        return t
    if isinstance(t, TVar):
        if t in m:
            return m[t]
        return t if unsolved is None else unsolved
    if isinstance(t, PairT):
        return PairT(subst(t.head, m, unsolved), subst(t.tail, m, unsolved))
    if isinstance(t, ListT):
        return ListT(subst(t.elem, m, unsolved))
    if isinstance(t, Union):
        return union(subst(x, m, unsolved) for x in t.members)
    if isinstance(t, Alias):
        return Alias(t.name, [subst(a, m, unsolved) for a in t.args], t.bare)
    if isinstance(t, FuncT):
        return FuncT([(n, subst(p, m, unsolved)) for n, p in t.params], subst(t.ret, m, unsolved),
                     t.named, t.name, t.vararg and (t.vararg[0], subst(t.vararg[1], m, unsolved)),
                     [v for v in t.tparams if v not in m], t.required, t.posonly, t.any_params)
    return t


def contains(t, test):
    """Does `test` hold for t or any type inside it?"""
    if test(t):
        return True
    if isinstance(t, PairT):
        return contains(t.head, test) or contains(t.tail, test)
    if isinstance(t, ListT):
        return contains(t.elem, test)
    if isinstance(t, Union):
        return any(contains(m, test) for m in t.members)
    if isinstance(t, Alias):
        return any(contains(a, test) for a in t.args)
    if isinstance(t, FuncT):
        return (any(contains(p, test) for _, p in t.params) or contains(t.ret, test)
                or bool(t.vararg and contains(t.vararg[1], test)))
    return False


def partly_unknown(t):
    return contains(t, lambda x: isinstance(x, Unknown) and x.report)


# ------------------------------------------------------------------ showing a type
def show(t):
    if isinstance(t, Prim):
        return t.name
    if isinstance(t, Unknown):
        return "Unknown"
    if isinstance(t, Never):
        return "Never"
    if isinstance(t, AnyT):
        return "Any"
    if isinstance(t, TVar):
        return t.name
    if isinstance(t, PairT):
        return f"Pair[{show(t.head)}, {show(t.tail)}]"
    if isinstance(t, ListT):
        return f"list[{show(t.elem)}]"
    if isinstance(t, Alias):
        if t.bare or not t.args:
            return t.name
        return f"{t.name}[{', '.join(show(a) for a in t.args)}]"
    if isinstance(t, Union):
        return " | ".join(f"({show(m)})" if isinstance(m, FuncT) else show(m) for m in t.members)
    if isinstance(t, FuncT):
        if t.any_params:
            params = ["..."]
        elif t.named:
            params = [f"{n}: {show(p)}" for n, p in t.params]
            if t.vararg:
                params.append(f"*{t.vararg[0]}: {show(t.vararg[1])}")
            elif t.posonly and params:
                params.append("/")
        else:
            params = [show(p) for _, p in t.params]
        ret = show(t.ret)
        if isinstance(t.ret, (FuncT, Union)):
            ret = f"({ret})"
        return f"({', '.join(params)}) -> {ret}"
    return "?"


def article(text):
    return ("an " if text[:1].lower() in "aeiou" else "a ") + text


def show_aliases(text):
    """As py-slang's messages.ts: Pyright writes an expanded linked list as
    `Pair[int, LList] | None`; show it as LList[int] (and the same for streams)."""
    i = 0
    while True:
        at = text.find("Pair[", i)
        if at < 0:
            return text
        depth, args, start, j = 0, [], at + 5, at + 4
        while j < len(text):
            c = text[j]
            if c in "[(":
                depth += 1
            elif c in "])":
                depth -= 1
                if depth == 0:
                    args.append(text[start:j].strip())
                    break
            elif c == "," and depth == 1:
                args.append(text[start:j].strip())
                start = j + 1
            j += 1
        i = at + 1
        if len(args) == 2 and text[j + 1:].startswith(" | None"):
            alias = {"LList": "LList", "() -> Stream": "Stream", f"LList[{args[0]}]": "LList",
                     f"() -> Stream[{args[0]}]": "Stream"}.get(args[1])
            if alias:
                text = f"{text[:at]}{alias}[{args[0]}]{text[j + 1 + len(' | None'):]}"
                i = at


# =====================================================================================
# 2. THE PREDECLARED NAMES and their types (from py-slang's src/typecheck/prelude.pyi)
# =====================================================================================
# Written in Python §4 Typed itself, and read with sicpfuf's own parser. (AnyArgs stands
# for the `...` of Callable[..., object]; NoReturn: the function never returns.)
PRELUDE = """
def error(*object: object) -> NoReturn: pass
def breakpoint() -> None: pass
def time_time() -> float: pass
def random_random() -> float: pass
def arity(f: Callable[AnyArgs, object]) -> int: pass
def real(x: complex) -> float: pass
def imag(x: complex) -> float: pass
def set_timeout(f: Callable[[], object], t: int | float) -> None: pass
def clear_all_timeout() -> None: pass
def is_none(x: object) -> bool: pass
def is_boolean(x: object) -> bool: pass
def is_integer(x: object) -> bool: pass
def is_float(x: object) -> bool: pass
def is_complex(x: object) -> bool: pass
def is_number(x: object) -> bool: pass
def is_string(x: object) -> bool: pass
def is_function(x: object) -> bool: pass
def is_list(x: object) -> bool: pass
def pair[H, T](h: H, t: T) -> Pair[H, T]: pass
def head[H, T](p: Pair[H, T]) -> H: pass
def tail[H, T](p: Pair[H, T]) -> T: pass
def is_pair(x: object) -> bool: pass
def llist[A](*xs: A) -> LList[A]: pass
def is_llist(x: object) -> bool: pass
def print_llist[A](xs: LList[A]) -> None: pass
def llist_to_string[A](xs: LList[A]) -> str: pass
def length[A](xs: LList[A]) -> int: pass
def map[A, B](f: Callable[[A], B], xs: LList[A]) -> LList[B]: pass
def filter[A](pred: Callable[[A], bool], xs: LList[A]) -> LList[A]: pass
def reduce[A, B](f: Callable[[A, B], B], initial: B, xs: LList[A]) -> B: pass
def for_each[A](f: Callable[[A], object], xs: LList[A]) -> bool: pass
def build_llist[A](f: Callable[[int], A], n: int) -> LList[A]: pass
def enum_llist(start: int, end: int) -> LList[int]: pass
def reverse[A](xs: LList[A]) -> LList[A]: pass
def append[A](xs: LList[A], ys: LList[A]) -> LList[A]: pass
def member[A](v: A, xs: LList[A]) -> LList[A]: pass
def remove[A](v: A, xs: LList[A]) -> LList[A]: pass
def remove_all[A](v: A, xs: LList[A]) -> LList[A]: pass
def llist_ref[A](xs: LList[A], n: int) -> A: pass
def draw_data[A](value1: A, *values: object) -> A: pass
def set_head[H, T](p: Pair[H, T], v: H) -> None: pass
def set_tail[H, T](p: Pair[H, T], v: T) -> None: pass
def stream[A](*xs: A) -> Stream[A]: pass
def is_stream(x: object) -> bool: pass
def stream_tail[H, T](s: Pair[H, Callable[[], T]]) -> T: pass
def stream_ref[A](s: Stream[A], n: int) -> A: pass
def stream_length[A](s: Stream[A]) -> int: pass
def stream_map[A, B](f: Callable[[A], B], s: Stream[A]) -> Stream[B]: pass
def stream_filter[A](pred: Callable[[A], bool], s: Stream[A]) -> Stream[A]: pass
def stream_for_each[A](f: Callable[[A], object], s: Stream[A]) -> bool: pass
def stream_reverse[A](s: Stream[A]) -> Stream[A]: pass
def stream_append[A](s: Stream[A], t: Stream[A]) -> Stream[A]: pass
def stream_member[A](v: A, s: Stream[A]) -> Stream[A]: pass
def stream_remove[A](v: A, s: Stream[A]) -> Stream[A]: pass
def stream_remove_all[A](v: A, s: Stream[A]) -> Stream[A]: pass
def build_stream[A](f: Callable[[int], A], n: int) -> Stream[A]: pass
def enum_stream(start: int, end: int) -> Stream[int]: pass
def integers_from(start: int) -> Stream[int]: pass
def llist_to_stream[A](xs: LList[A]) -> Stream[A]: pass
def stream_to_llist[A](s: Stream[A]) -> LList[A]: pass
def eval_stream[A](s: Stream[A], n: int) -> LList[A]: pass
def math_atan2(y: int | float, x: int | float) -> float: pass
def math_ceil(x: int | float) -> int: pass
def math_floor(x: int | float) -> int: pass
def math_trunc(x: int | float) -> int: pass
def math_comb(n: int, k: int) -> int: pass
def math_factorial(n: int) -> int: pass
def math_isqrt(n: int) -> int: pass
def math_perm(n: int, k: int = 0) -> int: pass
def math_gcd(*integers: int) -> int: pass
def math_lcm(*integers: int) -> int: pass
def math_copysign(x: int | float, y: int | float) -> float: pass
def math_fma(x: int | float, y: int | float, z: int | float) -> float: pass
def math_fmod(x: int | float, y: int | float) -> float: pass
def math_pow(x: int | float, y: int | float) -> float: pass
def math_remainder(x: int | float, y: int | float) -> float: pass
def math_ldexp(x: int | float, i: int) -> float: pass
def math_log(x: int | float, base: int | float = 0) -> float: pass
def math_nextafter(x: int | float, y: int | float, steps: int = 0) -> float: pass
def math_isfinite(x: int | float) -> bool: pass
def math_isinf(x: int | float) -> bool: pass
def math_isnan(x: int | float) -> bool: pass
"""
# the math functions of one number that give a float
for _name in ("acos acosh asin asinh atan atanh cbrt cos cosh degrees erf erfc exp exp2 expm1 fabs "
              "gamma lgamma log10 log1p log2 radians sin sinh sqrt tan tanh ulp").split():
    PRELUDE += f"def math_{_name}(x: int | float) -> float: pass\n"
CONSTANTS = {f"math_{n}": FLOAT for n in ("e", "inf", "nan", "pi", "tau")}

# The type predicates NARROW the type of their argument (`TypeIs` in the prelude):
# in the true branch of `if is_none(xs):` xs is None, in the false branch it is not.
# is_float and is_complex only narrow the true branch (`TypeGuard`): an int counts as
# a float to the checker, but is_float(5) is False when the program runs.
PREDICATES = {
    "is_none": lambda m: m == NONE,
    "is_boolean": lambda m: m == BOOL,
    "is_integer": lambda m: m == INT,
    "is_string": lambda m: m == STR,
    "is_number": lambda m: isinstance(m, Prim) and m.name in NUMBERS,
    "is_pair": lambda m: isinstance(m, PairT),
    "is_function": lambda m: isinstance(m, FuncT),
    "is_list": lambda m: isinstance(m, ListT),
}
PREDICATE_TYPES = {"is_none": NONE, "is_boolean": BOOL, "is_integer": INT, "is_string": STR,
                   "is_number": Union([INT, FLOAT, COMPLEX]), "is_pair": PairT(ANY, ANY),
                   "is_function": FuncT([], OBJECT, any_params=True), "is_list": ListT(ANY)}
GUARDS = {"is_float": FLOAT, "is_complex": COMPLEX}

# Python's own builtins that Python §4 has: their types (typeshed's, simplified) are
# worked out in Checker.builtin_call.
TYPESHED = {"print", "len", "abs", "max", "min", "round", "input", "repr", "str", "complex",
            "int", "float", "bool", "range"}

OVERLOADED = {"tail", "stream_tail"}


class Solution(dict):
    """What each type variable of a call is: {A: int, ...}. `fixed`: the variables that an
    invariant position (inside a Pair or a list) decided, which another argument cannot widen."""

    def __init__(self):
        super().__init__()
        self.fixed = set()


LIST_INDEX = "slice[SupportsIndex | None, SupportsIndex | None, SupportsIndex | None]"


# =====================================================================================
# 3. DIAGNOSTICS (what is wrong, and where)
# =====================================================================================
class Diagnostic:
    def __init__(self, line, col, message, unknown=False):
        self.line, self.col, self.message, self.unknown = line, col, message, unknown


NONE_HINT = ". The value can be None: test for that first, for example with is_none(...)"


def start(e):
    """(line, column from 0) where an expression starts, as Pyright counts: a call, an
    operator, a subscript start where their leftmost part starts."""
    while True:
        if isinstance(e, N.BinOp):
            e = e.left
        elif isinstance(e, N.Compare):
            e = e.left
        elif isinstance(e, N.BoolOp):
            e = e.values[0]
        elif isinstance(e, N.IfExp):
            e = e.body
        elif isinstance(e, (N.Call, N.Subscript, N.Attribute)):
            e = e.func if isinstance(e, N.Call) else e.value
        else:
            return e.line, max(0, e.col - 1)


class StaticTypeErrors(SicpSyntaxError):
    """All the type errors of a program: it is not run, and each is reported."""

    def __init__(self, diagnostics, filename):
        first = diagnostics[0]
        super().__init__(first.message, filename, first.line, first.col + 1, kind="StaticTypeError")
        self.diagnostics = diagnostics

    def report(self, lines):
        out, hints_given = [], set()
        for i, d in enumerate(self.diagnostics):
            if i:
                out.append("")
            out.append(f"StaticTypeError at line {d.line}")
            if lines and 0 < d.line <= len(lines):
                text = lines[d.line - 1]
                stripped = text.lstrip()
                out.append("    " + stripped.rstrip())
                out.append("    " + " " * max(0, d.col - (len(text) - len(stripped))) + "^")
            out.append(f"StaticTypeError: {d.message}")
            hint = hint_for(d.message)
            if hint and hint not in hints_given:
                hints_given.add(hint)
                out.append(f"sicpfuf hint: {hint}")
        n = len(self.diagnostics)
        out.append("")
        out.append(f"{n} type error{'' if n == 1 else 's'}: the program was not run.")
        return "\n".join(out)


def hint_for(message):
    """The usual cause of each kind of type error, in plain words."""
    if "must return value on all code paths" in message:
        return ("some way through the function reaches its end without a `return`, and then it returns "
                "None. Add the missing `else:` branch or a final `return`.")
    if message.endswith(NONE_HINT[2:]) or "for \"None\"" in message or '"None" is not subscriptable' in message:
        return ("a linked list (LList) or a stream can be None: the EMPTY list. Test it first, as in "
                "`0 if is_none(xs) else head(xs)` or `if is_none(xs): return ...`: after that test the "
                "checker knows that xs is a pair.")
    if message.startswith("A condition must be a bool"):
        return ("conditions (if, while, ... if ... else ..., not, and, or) must be exactly True or False. "
                "Write the comparison out: `if n != 0:` or `if not is_none(xs):`.")
    if "cannot be determined" in message:
        return ("a lambda gets the types of its parameters from WHERE IT IS USED: a declared variable "
                "(`f: Callable[[int], int] = lambda x: x + 1`) or a parameter of the function it is passed "
                "to. An empty list needs a declared type: `xs: list[int] = []`.")
    if " expects " in message or "cannot be assigned to parameter" in message:
        return ("the argument's type must fit the type the function DECLARES for that parameter. A "
                "Callable fits when it takes the same parameter types and returns a fitting type.")
    if "declared type" in message:
        return ("a name declared with a type (`x: int = 0`, or a parameter) keeps that type: every "
                "assignment to it must give it a value of that type. An int fits where a float is "
                "declared, and a value of type T fits where T | None is declared.")
    if "return type" in message:
        return "what a `return` gives back must fit the return type written after `->` in the def."
    if message.startswith("Operator"):
        return ("the operator does not work for these types: numbers and strings don't mix (use str(n)), "
                "and True and False are not numbers.")
    if "is not defined" in message or "is unbound" in message:
        return "every name needs a value before it is used: by `name = ...`, `def name(...)` or as a parameter."
    if "positional argument" in message or "Argument missing" in message or "Arguments missing" in message:
        return "count the arguments in the call and the parameters in the def: they must match."
    if "cannot be indexed" in message:
        return "to the checker a pair is not a list: read its parts with head(p) and tail(p)."
    if "not callable" in message:
        return "only a function can be called with (...)."
    return None


# =====================================================================================
# 4. SCOPES
# =====================================================================================
class Scope:
    """What the checker knows about one function (or lambda, or the whole program)."""

    def __init__(self, kind, parent, snapshot=None, func=None):
        self.kind = kind                # 'module', 'function' or 'lambda'
        self.parent = parent
        self.snapshot = snapshot        # the parent's STATE when this function was made
        self.func = func                # the FuncT of a def (for `return`)
        self.locals = set()             # the names this scope binds
        self.globals = set()
        self.nonlocals = set()
        self.declared = {}              # name → its DECLARED type (annotation, parameter, def)
        self.rhs = {}                   # name → the expressions assigned to it, in the code
        self.count = {}                 # name → how many times it is bound
        self.tvars = dict(parent.tvars) if parent else {}   # type parameters in scope


class Capture:
    def __init__(self):
        self.diags = []


# =====================================================================================
# 5. THE CHECKER
# =====================================================================================
class Checker:
    def __init__(self, known_names, filename):
        self.known = set(known_names)       # names sicpfuf has (some have no type here)
        self.filename = filename
        self.diags = []
        self.captures = []                  # see capture(): diagnostics that may be thrown away
        self.state = {}                     # name → its type HERE (None: this point is unreachable)
        self.scope = None
        self.jobs = []                      # function bodies, checked after the code around them
        self.loops = []                     # for break/continue: [break states, continue states]
        self.defining = None                # the alias being defined (for `bare`)
        self.computing, self.assigned_cache = set(), {}
        self.prelude = self.read_prelude()

    # ------------------------------------------------------------- diagnostics
    def diag(self, where, message, unknown=False):
        if isinstance(where, tuple):
            line, col = where
        else:
            line, col = start(where)
        message = re.sub(r"([\[,] ?)Any\b", r"\1object", show_aliases(message))
        d = Diagnostic(line, col, message, unknown)
        (self.captures[-1].diags if self.captures else self.diags).append(d)

    def capture(self):
        """Run a piece of checking 'on trial': its diagnostics go into a box, which the
        caller can look at and throw away. (Used to try an expected type first.)"""
        checker = self

        class Box:
            def __enter__(self):
                self.box = Capture()
                checker.captures.append(self.box)
                return self.box

            def __exit__(self, *exc):
                checker.captures.pop()

        return Box()

    @property
    def silent(self):
        return bool(self.captures)

    # ------------------------------------------------------------- 5a. annotations → types
    def read_prelude(self):
        out = {}
        tree = parse(PRELUDE, "<typed prelude>")
        self.scope = Scope("module", None)
        for d in tree.body:
            out[d.name] = self.def_type(d, posonly=True)
        return out

    def def_type(self, d, posonly=False):
        """The type of a def, from its annotations: FuncT with names."""
        saved = self.scope.tvars
        tparams = [TVar(n, d.name + str(id(d))) for n in d.type_params]
        self.scope.tvars = dict(saved, **{v.name: v for v in tparams})
        try:
            params = [(p.name, self.to_type(p.annotation) if p.annotation is not None else UNK)
                      for p in d.params.args]
            required = sum(1 for p in d.params.args if p.default is None)
            vararg = None
            if d.params.vararg:
                ann = getattr(d.params, "vararg_annotation", None)
                vararg = (d.params.vararg, self.to_type(ann) if ann is not None else UNK)
            ret = self.to_type(d.returns) if d.returns is not None else UNK
        finally:
            self.scope.tvars = saved
        return FuncT(params, ret, True, d.name, vararg, tparams, required, posonly)

    def to_type(self, e):
        """An annotation (parsed as an ordinary expression) → a type."""
        if isinstance(e, N.Constant) and e.value is None:
            return NONE
        if isinstance(e, N.BinOp) and e.op == "|":
            return union([self.to_type(e.left), self.to_type(e.right)])
        if isinstance(e, N.Name):
            name = e.id
            simple = {"int": INT, "float": FLOAT, "complex": COMPLEX, "str": STR, "bool": BOOL,
                      "object": OBJECT, "NoReturn": NEVER, "list": ListT(UNK)}
            if name in self.scope.tvars:
                return self.scope.tvars[name]
            if name in simple:
                return simple[name]
            if name in ALIASES:
                params = ALIASES[name][0]
                return Alias(name, [UNK] * len(params), bare=(name == self.defining))
            if name == "Pair":
                return PairT(UNK, UNK)
            if name == "Callable":
                return FuncT([], UNK, named=False, any_params=True)
            self.diag(e, f'"{name}" is not defined')
            return UNMODELED
        if isinstance(e, N.Subscript) and isinstance(e.value, N.Name):
            name = e.value.id
            items = e.index.elts if isinstance(e.index, N.TupleExpr) else [e.index]
            if name == "Callable" and len(items) == 2:
                if isinstance(items[0], N.Name) and items[0].id == "AnyArgs":
                    return FuncT([], self.to_type(items[1]), named=False, any_params=True)
                params = items[0].elts if isinstance(items[0], N.ListExpr) else [items[0]]
                return FuncT([(None, self.to_type(p)) for p in params], self.to_type(items[1]), named=False)
            args = [self.to_type(x) for x in items]
            if name == "Pair" and len(args) == 2:
                return PairT(*args)
            if name == "list" and len(args) == 1:
                return ListT(args[0])
            if name in ALIASES:
                return Alias(name, args, bare=(name == self.defining))
        self.diag(e, "This is not a type")
        return UNMODELED

    # ------------------------------------------------------------- 5b. assignability
    def assignable(self, s, d, seen=None):
        """Can a value of type s go where type d is wanted?"""
        if s.key() == d.key():
            return True
        if isinstance(s, (Unknown, Never, AnyT)) or isinstance(d, (Unknown, AnyT)) or d == OBJECT:
            return True
        seen = set() if seen is None else seen
        if isinstance(s, Alias) or isinstance(d, Alias):
            k = (s.key(), d.key())
            if k in seen:                       # a recursive type: assume yes (coinduction)
                return True
            seen.add(k)
            if isinstance(s, Alias) and isinstance(d, Alias) and s.name == d.name:
                return all(self.same(a, b, seen) for a, b in zip(s.args, d.args))
            if isinstance(s, Alias):
                return self.assignable(expand(s), d, seen)
            return self.assignable(s, expand(d), seen)
        if isinstance(s, Union):
            return all(self.assignable(m, d, seen) for m in s.members)
        if isinstance(d, Union):
            return any(self.assignable(s, m, seen) for m in d.members)
        if isinstance(s, Prim) and isinstance(d, Prim):
            # the NUMERIC TOWER: an int fits where a float or complex is wanted.
            return (s.name == d.name or (s.name, d.name) in
                    {("int", "float"), ("int", "complex"), ("float", "complex"), ("LiteralString", "str")})
        if isinstance(s, PairT) and isinstance(d, PairT):
            # pairs can be changed (set_head), so their types must match EXACTLY (invariance)
            return self.same(s.head, d.head, seen) and self.same(s.tail, d.tail, seen)
        if isinstance(s, ListT) and isinstance(d, ListT):
            return self.same(s.elem, d.elem, seen)
        if isinstance(s, FuncT) and isinstance(d, FuncT):
            if s.tparams:                       # a generic function: be lenient
                s = subst(s, {v: UNMODELED for v in s.tparams})
            if d.any_params:
                return self.assignable(s.ret, d.ret, seen)
            if s.any_params:
                return True
            n = len(d.params)
            if n < s.required or (n > len(s.params) and not s.vararg):
                return False
            for i, (_, dp) in enumerate(d.params):
                sp = s.params[i][1] if i < len(s.params) else s.vararg[1]
                if not self.assignable(dp, sp, seen):  # parameters: the other way round!
                    return False
            return self.assignable(s.ret, d.ret, seen)
        return False

    def same(self, a, b, seen=None):
        return self.assignable(a, b, seen) and self.assignable(b, a, seen)

    def none_fails(self, s, d):
        """Is None the (first) part of s that does not fit d? Then the message gets the hint
        "The value can be None"."""
        for m in members(s):
            if not self.assignable(m, d):
                return m == NONE
        return False

    # ------------------------------------------------------------- 5c. solving type variables
    def solve(self, p, a, m, tv, invariant=False):
        """Match a parameter type p (with the callee's type variables tv) against an argument
        type a, and write what each variable must be into m."""
        if isinstance(a, Unknown) or isinstance(a, Never):
            return
        if isinstance(p, TVar) and p in tv:
            a = unbare(widen(a))
            if p not in m:
                m[p] = a
                if invariant:
                    m.fixed.add(p)
            elif not invariant and p not in m.fixed and not self.assignable(a, m[p]):
                # a plain parameter: `llist(1, "a")` makes A = int | str
                m[p] = a if self.assignable(m[p], a) else union([m[p], a])
            return
        if not contains(p, lambda x: isinstance(x, TVar) and x in tv):
            return
        if isinstance(p, Alias) and isinstance(a, Alias) and p.name == a.name:
            for x, y in zip(p.args, a.args):
                self.solve(x, y, m, tv, True)
            return
        if isinstance(a, Alias):
            return self.solve(p, expand(a), m, tv, invariant)
        if isinstance(p, Alias):
            return self.solve(expand(p), a, m, tv, invariant)
        if isinstance(a, Union):
            for x in a.members:
                self.solve(p, x, m, tv, invariant)
            return
        if isinstance(p, Union):
            for x in p.members:
                if not contains(x, lambda y: isinstance(y, TVar) and y in tv) and self.assignable(a, x):
                    return                      # it fits an arm without variables
            for x in p.members:
                if type(x) is type(a) or isinstance(x, TVar):
                    self.solve(x, a, m, tv, invariant)
            return
        if isinstance(p, PairT) and isinstance(a, PairT):
            self.solve(p.head, a.head, m, tv, True)
            self.solve(p.tail, a.tail, m, tv, True)
        elif isinstance(p, ListT) and isinstance(a, ListT):
            self.solve(p.elem, a.elem, m, tv, True)
        elif isinstance(p, FuncT) and isinstance(a, FuncT):
            for (_, x), (_, y) in zip(p.params, a.params):
                self.solve(x, y, m, tv, invariant)
            self.solve(p.ret, a.ret, m, tv, invariant)

    # ------------------------------------------------------------- 5d. names
    def lookup(self, name, node):
        st, sc = self.state, self.scope
        t = st.get(name)
        if t is not None and t is not UNBOUND:
            return t
        if name in sc.locals and name not in sc.globals and name not in sc.nonlocals:
            if sc.kind != "module":
                self.diag(node, f'"{name}" is unbound')
                return UNK
        else:
            # a name of an enclosing function, or of the program (or `global`)
            s, snap = sc.parent, sc.snapshot
            if name in sc.globals:
                while s is not None and s.kind != "module":
                    snap, s = s.snapshot, s.parent
            while s is not None:
                if name in s.locals and not (s.kind != "module" and name in s.globals):
                    return self.outer_type(s, name, snap)
                snap, s = s.snapshot, s.parent
        # the predeclared names
        if name in CONSTANTS:
            return CONSTANTS[name]
        if name in self.prelude:
            return self.prelude[name]
        if name in TYPESHED or name in self.known:
            return UNMODELED
        self.diag(node, f'"{name}" is not defined')
        return UNK

    def outer_type(self, s, name, snap):
        """The type of a name of an ENCLOSING scope, seen from a function inside it. If the
        name is bound only once, its type where the function was made is the type it will
        always have; otherwise it is the declared type, or all the types it is given."""
        if s.count.get(name, 0) <= 1 and snap and snap.get(name, UNBOUND) is not UNBOUND:
            return snap[name]
        if name in s.declared:
            return s.declared[name]
        if s.rhs.get(name):
            return self.all_assigned(s, name, snap)
        if name in CONSTANTS or name in self.prelude:
            return CONSTANTS.get(name) or self.prelude[name]
        return UNMODELED

    def all_assigned(self, s, name, snap):
        """The union of the types of ALL the values a name of scope s is given (wherever
        they are in s: also the ones further down, which have not been checked yet)."""
        k = (id(s), name)
        if k in self.computing:
            return UNMODELED
        if k not in self.assigned_cache:
            self.computing.add(k)
            saved = (self.scope, self.state)
            types = []
            try:
                for value in s.rhs[name]:
                    if isinstance(value, Type):
                        types.append(value)
                        continue
                    self.scope, self.state = s, dict(snap or {})
                    with self.capture():
                        types.append(widen(self.infer(value)))
            finally:
                self.scope, self.state = saved
                self.computing.discard(k)
            self.assigned_cache[k] = union(types)
        return self.assigned_cache[k]

    def declared_type(self, name):
        """The declared type of a name that is assigned here (and the scope it belongs to)."""
        sc = self.scope
        if name in sc.globals:
            while sc.parent is not None:
                sc = sc.parent
        elif name in sc.nonlocals:
            sc = sc.parent
            while sc is not None and name not in sc.locals:
                sc = sc.parent
            if sc is None:
                return None, self.scope
        return sc.declared.get(name), sc

    # ------------------------------------------------------------- 5e. expressions
    def infer(self, e, expected=None):
        """The type of expression e (and report what is wrong inside it). `expected`: the
        type the context wants, if any: it gives lambdas their parameter types."""
        method = getattr(self, "e_" + type(e).__name__, None)
        if method is None:
            for child in children(e):
                self.infer(child)
            return UNMODELED
        return method(e, expected)

    def e_Constant(self, e, expected):
        v = e.value
        if v is None:
            return NONE
        if isinstance(v, bool):
            return BOOL
        if isinstance(v, int):
            return INT
        if isinstance(v, float):
            return FLOAT
        if isinstance(v, complex):
            return COMPLEX
        if isinstance(v, str):
            return STRLIT
        return UNMODELED

    def e_Name(self, e, expected):
        return self.lookup(e.id, e)

    def e_ListExpr(self, e, expected):
        exp = None
        for m in members(expected) if expected is not None else []:
            if isinstance(m, ListT):
                exp = m
        if exp is not None:
            with self.capture() as box:
                ok = all(self.assignable(self.infer(x, exp.elem), exp.elem) for x in e.elts)
            if ok and not box.diags:
                return exp
        types = [widen(self.infer(x)) for x in e.elts]
        if not types:
            return ListT(UNK)
        if all(t == types[0] for t in types):
            return ListT(types[0])
        return ListT(UNK)                         # mixed items: Pyright gives up (see the tests)

    def e_IfExp(self, e, expected):
        saved = self.state
        yes, no = self.cond(e.test)
        types = []
        for st, part in ((yes, e.body), (no, e.orelse)):
            if st is not None:
                self.state = st
                types.append(self.infer(part, expected))
        self.state = saved
        return union(types)

    def e_BoolOp(self, e, expected):
        saved = self.state
        self.cond(e)
        self.state = saved
        return BOOL

    def e_UnaryOp(self, e, expected):
        if e.op == "not":
            saved = self.state
            self.cond(e.operand)
            self.state = saved
            return BOOL
        t = self.infer(e.operand)
        results, bad = [], []
        for m in members(t):
            if isinstance(m, Unknown):
                return m
            if isinstance(m, Prim) and m.name in NUMBERS:
                results.append(m)
            else:
                bad.append(m)
        if not bad:
            return union(results)
        if all(b == NONE for b in bad) and len(members(t)) > 1:
            self.diag(e, f'Operator "{e.op}" not supported for "None"')
        else:
            self.diag(e, f'Operator "{e.op}" not supported for type "{show(t)}"')
        return UNK

    def e_BinOp(self, e, expected):
        left, right = self.infer(e.left), self.infer(e.right)
        return self.operator(e, e.op, left, right, e.right)

    def e_Compare(self, e, expected):
        left = self.infer(e.left)
        for op, right_node in zip(e.ops, e.comparators):
            right = self.infer(right_node)
            self.operator(e, op, left, right, right_node)
            left = right
        return BOOL

    def operator(self, e, op, left, right, right_node):
        """The type of `left op right`, following Python §4's operator table."""
        if isinstance(left, Unknown) or isinstance(right, Unknown):
            return UNK if (getattr(left, "report", False) or getattr(right, "report", False)) else UNMODELED
        if op in ("==", "!=", "is", "is not", "in", "not in"):
            return BOOL
        results, failed = [], []
        for a in members(left):
            for b in members(right):
                t = self.prim_op(op, a, b, right_node)
                if t is None:
                    failed.append((a, b))
                else:
                    results.append(t)
        if not failed:
            return union(results)
        if all(a == NONE for a, _ in failed) and NONE not in members(right) and len(members(left)) > 1:
            self.diag(e, f'Operator "{op}" not supported for "None"')
        else:
            self.diag(e, f'Operator "{op}" not supported for types "{show(left)}" and "{show(right)}"')
        return UNK

    def prim_op(self, op, a, b, right_node):
        if isinstance(a, (Unknown, Never)) or isinstance(b, (Unknown, Never)):
            return UNMODELED
        num = lambda t: isinstance(t, Prim) and t.name in NUMBERS
        text = lambda t: isinstance(t, Prim) and t.name in ("str", "LiteralString")
        if op in ("<", "<=", ">", ">="):
            ordered = lambda t: num(t) or t == BOOL          # bools compare as 1 and 0
            ok = ((ordered(a) and ordered(b)) or (text(a) and text(b))
                  or (isinstance(a, ListT) and isinstance(b, ListT)))
            return BOOL if ok else None
        if num(a) and num(b):
            rank = max(NUMBERS.index(a.name), NUMBERS.index(b.name))
            if op in ("//", "%") and rank == 2:
                return None
            if op == "/":
                return Prim(NUMBERS[max(rank, 1)])
            if op == "**" and rank == 0:
                # int ** int is an int only for an exponent that is a literal >= 0
                sign = literal_sign(right_node)
                return INT if sign == 1 else FLOAT if sign == -1 else Union([INT, FLOAT])
            return Prim(NUMBERS[rank])
        if text(a) and text(b) and op == "+":
            return STRLIT if isinstance(a, StrLit) and isinstance(b, StrLit) else STR
        if op == "*" and ((text(a) and b == INT) or (a == INT and text(b))):
            lit = a if text(a) else b
            return LITSTR if isinstance(lit, StrLit) or lit is LITSTR else STR
        if op == "%" and text(a):
            return STR
        if isinstance(a, ListT) and isinstance(b, ListT) and op == "+":
            return ListT(union([a.elem, b.elem]))
        if op == "*" and ((isinstance(a, ListT) and b == INT) or (a == INT and isinstance(b, ListT))):
            return a if isinstance(a, ListT) else b
        return None

    def e_Attribute(self, e, expected):
        """x.attr: not part of Python §4 (chapters.py rejects it after the types are checked),
        but Pyright already complains when a number or a pair has no such attribute."""
        t = self.infer(e.value)
        for m in members(t):
            name = ("Pair" if isinstance(m, PairT) else m.name if isinstance(m, Prim) and
                    m.name in ("int", "float", "bool", "complex") else None)
            if name and e.attr not in ("real", "imag", "conjugate"):
                self.diag((e.line, e.col), f'Cannot access attribute "{e.attr}" for class "{name}"')
                return UNK
        return UNMODELED

    def e_Subscript(self, e, expected):
        t = self.infer(e.value)
        index = self.infer(e.index)
        results = []
        for m in members(t):
            if isinstance(m, Unknown):
                results.append(m)
            elif isinstance(m, ListT) or m == STR or isinstance(m, StrLit):
                if not self.assignable(index, INT) or index == BOOL:
                    self.diag(e, 'No overloads for "__getitem__" match the provided arguments')
                    if isinstance(m, ListT):
                        self.diag(e, f"__getitem__ expects s to be {LIST_INDEX}, but got {show(index)}")
                    else:
                        self.diag(e, f"__getitem__ expects key to be SupportsIndex | {LIST_INDEX}, "
                                     f"but got {show(index)}")
                    return UNK
                results.append(m.elem if isinstance(m, ListT) else STR)
            elif isinstance(m, PairT):
                self.diag(e, f"A pair cannot be indexed ({show(m)}): use head(...) and tail(...)")
                results.append(UNK)
            elif m == NONE:
                self.diag(e, 'Object of type "None" is not subscriptable')
                results.append(UNK)
            else:
                self.diag(e, f"A value of type {show(m)} cannot be indexed")
                results.append(UNK)
        return union(results)

    def e_Lambda(self, e, expected):
        """A lambda's parameters get their types from the EXPECTED type."""
        names = [p.name for p in e.params.args]
        exp = None
        for m in members(expected) if expected is not None else []:
            if isinstance(m, FuncT) and not m.any_params:
                exp = m
        types = []
        for i, n in enumerate(names):
            types.append(exp.params[i][1] if exp is not None and i < len(exp.params) else UNK)
        for p, t in zip(e.params.args, types):
            if partly_unknown(t):
                self.diag((p.line, p.col - 1), f"The type of the parameter {p.name} cannot be determined: a "
                          f"lambda gets its parameter types from where it is used, for example "
                          f"f: Callable[[int], int] = lambda {p.name}: ...", unknown=True)
        scope = Scope("lambda", self.scope, snapshot=dict(self.state) if self.state is not None else {})
        scope.locals = set(names)
        scope.count = {n: 1 for n in names}
        scope.declared = dict(zip(names, types))
        saved = (self.scope, self.state)
        self.scope, self.state = scope, dict(zip(names, types))
        try:
            ret_expected = None
            if exp is not None and not partly_unknown(exp.ret):
                ret_expected = exp.ret
            ret = self.infer(e.body, ret_expected)
        finally:
            self.scope, self.state = saved
        if partly_unknown(ret):
            self.diag(e.body, "The type of what this lambda returns cannot be determined", unknown=True)
        return FuncT(list(zip(names, types)), widen(ret), named=True)

    # ------------------------------------------------------------- 5f. calls
    def e_Call(self, e, expected):
        f = e.func
        if isinstance(f, N.Name):
            ft = self.lookup(f.id, f)
            if ft is UNMODELED and f.id in TYPESHED and not self.shadowed(f.id):
                return self.builtin_call(f.id, e)
        else:
            ft = self.infer(f)
        if isinstance(ft, Unknown):
            for a in e.args:
                self.infer(a)
            return ft
        callable_ = [m for m in members(ft) if isinstance(m, FuncT)]
        if len(callable_) != len(members(ft)) or not callable_:
            for a in e.args:
                self.infer(a)
            others = [m for m in members(ft) if not isinstance(m, FuncT)]
            if callable_ and all(m == NONE for m in others):
                self.diag(f, 'Object of type "None" cannot be called')
            else:
                self.diag(f, f'Object of type "{show(ft)}" is not callable')
            return UNK
        if len(callable_) > 1:
            for a in e.args:
                self.infer(a)
            return union(unbare(c.ret) for c in callable_)
        return self.apply(callable_[0], e, expected)

    def shadowed(self, name):
        sc = self.scope
        while sc is not None:
            if name in sc.locals:
                return True
            sc = sc.parent
        return False

    def apply(self, ft, e, expected):
        """Check a call of a function of type ft, and give the type of its result."""
        args = e.args
        unknown_vars = {v: UNK for v in ft.tparams}
        if any(isinstance(a, N.Starred) for a in args) or ft.any_params:
            for a in args:
                self.infer(a.value if isinstance(a, N.Starred) else a)
            return unbare(subst(ft.ret, unknown_vars))
        n = len(ft.params)
        if len(args) > n and ft.vararg is None:
            self.diag(args[n], f"Expected {n} positional argument{'' if n == 1 else 's'}")
            for a in args:
                self.infer(a)
            return unbare(subst(ft.ret, unknown_vars))
        if len(args) < ft.required:
            missing = [name for name, _ in ft.params[len(args):ft.required]]
            if ft.named:
                if len(missing) == 1:
                    msg = f'Argument missing for parameter "{missing[0]}"'
                else:
                    msg = "Arguments missing for parameters " + ", ".join(f'"{x}"' for x in missing)
            else:
                k = len(missing)
                msg = f"Expected {k} more positional argument{'' if k == 1 else 's'}"
            self.diag(e, msg)
            for a in args:
                self.infer(a)
            return unbare(subst(ft.ret, unknown_vars))
        slots = []
        for i, a in enumerate(args):
            name, p = ft.params[i] if i < n else ft.vararg
            slots.append((a, p, name))
        if ft.tparams:
            tv = set(ft.tparams)
            if expected is not None and not isinstance(expected, Unknown) and ft.name not in OVERLOADED:
                # first try with what the context wants: llist() where an LList[int] is wanted
                m0 = Solution()
                self.solve(ft.ret, expected, m0, tv, True)
                if m0:
                    with self.capture() as box:
                        result = self.match_args(ft, slots, m0, tv)
                    if not box.diags and self.assignable(result, expected):
                        return result
            return self.match_args(ft, slots, Solution(), tv)
        return self.match_args(ft, slots, None, set())

    def match_args(self, ft, slots, m, tv):
        # lambdas last: they need the types that the other arguments tell
        order = [s for s in slots if not isinstance(s[0], N.Lambda)] + [s for s in slots if isinstance(s[0], N.Lambda)]
        failed = False
        for arg, p, pname in order:
            pm = subst(p, m) if m else p
            open_vars = [v for v in tv if v not in (m or {})]
            exp = pm
            if open_vars and contains(pm, lambda x: isinstance(x, TVar) and x in tv):
                # a lambda gets Unknown for what is not known yet; other arguments get nothing
                exp = subst(pm, {v: UNK for v in open_vars}) if isinstance(arg, N.Lambda) else None
            t = self.infer(arg, exp)
            if m is not None:
                self.solve(p, t, m, tv)
            target = subst(p, {v: m.get(v, UNMODELED) for v in tv}) if m is not None else p
            if not self.assignable(t, target):
                failed = True
                if ft.name:
                    msg = f"{ft.name} expects {pname} to be {show(p)}, but got {show(t)}"
                else:
                    msg = f'Argument of type "{show(t)}" cannot be assigned to parameter of type "{show(pm)}"'
                if self.none_fails(t, target):
                    msg += NONE_HINT
                self.diag(arg, msg)
            elif partly_unknown(t):
                self.diag(arg, "The type of this argument cannot be determined", unknown=True)
        if failed and ft.name in OVERLOADED:
            return UNK                  # (in the prelude tail and stream_tail are overloaded)
        result = unbare(subst(ft.ret, {v: (m or {}).get(v, UNK) for v in tv}))
        if ft.name == "tail" and isinstance(result, AnyT):
            return Alias("LList", [ANY])    # (the first overload of tail in the prelude)
        return result

    def builtin_call(self, name, e):
        """Python's own builtins (their types are typeshed's, simplified)."""
        args = [self.infer(a.value if isinstance(a, N.Starred) else a) for a in e.args]
        for a, t in zip(e.args, args):
            if partly_unknown(t):
                self.diag(a, "The type of this argument cannot be determined", unknown=True)
        if name == "print":
            return NONE
        if name in ("str", "repr", "input"):
            return STR
        if name in ("int", "float", "bool", "complex"):
            return {"int": INT, "float": FLOAT, "bool": BOOL, "complex": COMPLEX}[name]
        if name == "range":
            for a, t in zip(e.args, args):
                if not self.assignable(t, INT) or t == BOOL:
                    self.diag(a, f'Argument of type "{show(t)}" cannot be assigned to parameter of type "int"')
            return RANGE
        if name == "len":
            if len(args) == 1:
                t = args[0]
                if not all(isinstance(m, (ListT, Unknown)) or m == STR for m in members(t)):
                    self.diag(e.args[0], f"len expects obj to be Sized, but got {show(t)}")
            return INT
        if name == "round":
            return INT if len(args) <= 1 or args[0] == INT else FLOAT
        if name == "abs":
            return args[0] if args and isinstance(args[0], Prim) and args[0].name in NUMBERS else UNMODELED
        if name in ("max", "min"):
            items = args
            if len(args) == 1 and isinstance(args[0], ListT):
                return args[0].elem
            if items and all(isinstance(t, Prim) and t.name in ("int", "float") for t in items):
                return FLOAT if FLOAT in items else INT
            if items and all(t == STR or isinstance(t, StrLit) for t in items):
                return STR
            return UNMODELED
        return UNMODELED

    # ------------------------------------------------------------- 6. conditions and NARROWING
    def check_condition(self, t, e):
        if all(isinstance(m, (Unknown, Never)) or m == BOOL for m in members(t)):
            return
        self.diag(e, f"A condition must be a bool, but this is {article(show(t))}")

    def cond(self, e):
        """Check a CONDITION. Gives two states: the types of the names when it is True, and
        when it is False (None: that cannot happen)."""
        st = self.state
        if isinstance(e, N.UnaryOp) and e.op == "not":
            yes, no = self.cond(e.operand)
            return no, yes
        if isinstance(e, N.BoolOp):
            stop_on = e.op == "or"                    # or: stops at the first True
            exits, cur = [], st
            for v in e.values:
                if cur is None:                       # the rest cannot be reached
                    break
                self.state = cur
                yes, no = self.cond(v)
                exits.append(yes if stop_on else no)
                cur = no if stop_on else yes
            self.state = st
            if stop_on:
                return join(exits), cur
            return cur, join(exits)
        target, test = narrowing_test(e)
        if target is not None:
            self.infer(e)                             # (checks the call itself)
            current = self.state_type(target, e)
            yes, no = narrow(current, test)
            out = []
            for nt in (yes, no):
                if isinstance(nt, Never):
                    out.append(None)
                else:
                    s2 = dict(st)
                    s2[target] = nt
                    out.append(s2)
            return out[0], out[1]
        t = self.infer(e)
        self.check_condition(t, e)
        if isinstance(e, N.Name) and not isinstance(t, Unknown):
            # (an error, but Pyright still narrows it: `if xs:` is never None inside)
            yes, no = union(m for m in members(t) if m != NONE), \
                union(m for m in members(t) if not isinstance(m, (PairT, FuncT)))
            out = []
            for nt in (yes, no):
                s2 = dict(st)
                s2[e.id] = nt if not isinstance(nt, Never) else t
                out.append(None if isinstance(nt, Never) else s2)
            return out[0], out[1]
        return st, (dict(st) if st is not None else None)

    def join(self, states):
        """join() (below), and then: a name with a declared type that has all of its declared
        type again is shown as the declared type (LList[int], not Pair[int, LList[int]] | None)."""
        out = join(states)
        if out:
            for name, t in out.items():
                if isinstance(t, Union):
                    d = self.declared_type(name)[0]
                    if d is not None and self.same(t, d):
                        out[name] = d
        return out

    def state_type(self, name, node):
        with self.capture():
            return self.lookup(name, node)

    # ------------------------------------------------------------- 7. statements
    def block(self, stmts):
        for s in stmts:
            if self.state is None:                  # unreachable code is not checked
                return
            method = getattr(self, "s_" + type(s).__name__, None)
            if method is not None:
                method(s)

    def s_ExprStmt(self, s):
        t = self.infer(s.value)
        if isinstance(t, Never):
            self.state = None                       # error(...) does not come back

    def s_Pass(self, s):
        pass

    def s_Break(self, s):
        if self.loops:
            self.loops[-1][0].append(self.state)
        self.state = None

    def s_Continue(self, s):
        if self.loops:
            self.loops[-1][1].append(self.state)
        self.state = None

    def s_Return(self, s):
        func = self.scope.func
        if s.value is None:
            t, where = NONE, (s.line, s.col - 1)
        else:
            t = self.infer(s.value, func.ret if func else None)
            where = start(s.value)
        if func is not None and not self.assignable(t, func.ret):
            msg = f'Type "{show(t)}" is not assignable to return type "{show(func.ret)}"'
            if self.none_fails(t, func.ret):
                msg += NONE_HINT
            self.diag(where, msg)
        self.state = None

    def s_Assign(self, s):
        target = s.targets[0]
        if isinstance(target, N.Name):
            self.assign(target, s.value)
        elif isinstance(target, N.Subscript):
            self.assign_item(target, s.value)
        else:
            self.infer(s.value)

    def s_AnnAssign(self, s):
        if s.value is not None and isinstance(s.target, N.Name):
            self.assign(s.target, s.value)

    def assign(self, target, value):
        name = target.id
        declared, _ = self.declared_type(name)
        t = self.infer(value, declared)
        narrowed = t
        if declared is not None:
            if not self.assignable(t, declared):
                msg = f'Type "{show(t)}" is not assignable to declared type "{show(declared)}"'
                if self.none_fails(t, declared):
                    msg += NONE_HINT
                self.diag(value, msg)
                narrowed = declared
            elif isinstance(t, Unknown) and not t.report:
                narrowed = declared
        if partly_unknown(narrowed) and not (isinstance(value, N.ListExpr) and not value.elts):
            self.diag(target, f"The type of {name} cannot be determined: declare it, as in "
                              f"{name}: list[int] = []", unknown=True)
        self.state[name] = narrowed

    def assign_item(self, target, value):
        container = self.infer(target.value)
        index = self.infer(target.index)
        lists = [m for m in members(container) if isinstance(m, ListT)]
        if lists and len(lists) == len(members(container)):
            elem = lists[0].elem
            t = self.infer(value, elem)
            if not self.assignable(index, INT) or index == BOOL:
                self.diag(target, 'No overloads for "__setitem__" match the provided arguments')
                self.diag(target, f"__setitem__ expects key to be SupportsIndex, but got {show(index)}")
            elif not self.assignable(t, elem):
                self.diag(target, 'No overloads for "__setitem__" match the provided arguments')
                self.diag(target, f"__setitem__ expects value to be {show(elem)}, but got {show(t)}")
            return
        self.infer(value)
        for m in members(container):
            if not isinstance(m, (ListT, Unknown)):
                self.diag(target, f'"__setitem__" method not defined on type "{show(m)}"')
                return

    def s_If(self, s):
        yes, no = self.cond(s.test)
        ends = []
        for st, body in ((yes, s.body), (no, s.orelse)):
            if st is not None:
                self.state = dict(st)
                self.block(body)
                ends.append(self.state)
        self.state = self.join(ends)

    def loop(self, enter, body):
        """A loop: check the body over and over (silently) until the states stop growing —
        the types a name can have at the top of the loop are the types it has on entry, or
        at the end of any earlier time round. Then check it once more, for real."""
        entry, cur = self.state, self.state
        for _ in range(6):
            with self.capture():
                self.loops.append([[], []])
                self.state = dict(cur)
                inside, _ = enter()
                if inside is not None:
                    self.state = inside
                    self.block(body)
                breaks, conts = self.loops.pop()
            new = self.join([entry, self.state] + conts)
            if same_state(new, cur):
                break
            cur = new
        self.loops.append([[], []])
        self.state = dict(cur)
        inside, outside = enter()
        if inside is not None:
            self.state = inside
            self.block(body)
        breaks, _ = self.loops.pop()
        self.state = self.join([outside] + breaks)

    def s_While(self, s):
        forever = isinstance(s.test, N.Constant) and s.test.value is True

        def enter():
            yes, no = self.cond(s.test)
            return yes, (None if forever else no)
        self.loop(enter, s.body)

    def s_For(self, s):
        it = self.infer(s.iter)
        elem = UNMODELED
        if it == RANGE:
            elem = INT
        elif isinstance(it, ListT):
            elem = it.elem
        elif it == STR or isinstance(it, StrLit):
            elem = STR
        name = s.target.id if isinstance(s.target, N.Name) else None

        def enter():
            st = dict(self.state)
            if name:
                st[name] = elem
            return st, dict(self.state)
        self.loop(enter, s.body)

    def s_FunctionDef(self, s):
        ft = self.def_type(s)
        self.state[s.name] = ft
        if not self.silent:
            self.jobs.append((s, ft, self.scope, dict(self.state)))

    def s_ImportFrom(self, s):
        for a in s.names:
            self.state[a.asname or a.name] = UNMODELED      # (modules have no types here)

    # ------------------------------------------------------------- 8. functions and the program
    def prescan(self, scope, body, params=()):
        """Before a scope is checked: what does it DECLARE, and how often is each name bound?"""
        for p in params:
            scope.count[p] = 1

        def walk(stmts):
            for s in stmts:
                if isinstance(s, (N.Assign, N.AnnAssign)):
                    targets = s.targets if isinstance(s, N.Assign) else [s.target]
                    for t in targets:
                        if isinstance(t, N.Name):
                            scope.count[t.id] = scope.count.get(t.id, 0) + 1
                            if s.value is not None:
                                scope.rhs.setdefault(t.id, []).append(s.value)
                    if isinstance(s, N.AnnAssign) and isinstance(s.target, N.Name):
                        if s.target.id not in scope.declared:
                            scope.declared[s.target.id] = self.to_type(s.annotation)
                elif isinstance(s, N.FunctionDef):
                    scope.count[s.name] = scope.count.get(s.name, 0) + 1
                    scope.declared[s.name] = self.def_type(s)
                    rebinds(s)
                elif isinstance(s, N.For):
                    if isinstance(s.target, N.Name):
                        scope.count[s.target.id] = 2
                        scope.rhs.setdefault(s.target.id, []).append(INT)
                    walk(s.body)
                elif isinstance(s, (N.If, N.While)):
                    walk(s.body)
                    walk(s.orelse)

        def rebinds(fn):
            # a function inside that says `nonlocal x` / `global x` can change x at any time
            for inner in fn.scope.nonlocal_names | fn.scope.global_names:
                scope.count[inner] = 99
            for s in all_defs(fn.body):
                rebinds(s)
        walk(body)

    def check_program(self, tree):
        self.read_aliases(tree.body)
        info = {"assigned": set(), "global": set(), "nonlocal": set()}
        from ..scopes import scan_block
        scan_block(tree.body, info)
        scope = Scope("module", None)
        scope.locals = set(info["assigned"]) | globals_made(tree.body)
        self.scope = scope
        self.prescan(scope, tree.body)
        for d in all_defs(tree.body, deep=True):
            for g in d.scope.global_names:
                scope.count[g] = 99
        self.state = {n: UNBOUND for n in scope.locals}
        self.block(tree.body)
        while self.jobs:
            self.check_function(*self.jobs.pop(0))

    def read_aliases(self, body):
        """`type Name = ...` statements: first all the names (they may refer to each other),
        then their meanings."""
        stmts = [s for s in walk_statements(body) if isinstance(s, N.TypeAlias)]
        for s in stmts:
            ALIASES[s.name] = ([TVar(p, "type " + s.name) for p in s.params], UNMODELED)
        for s in stmts:
            params = ALIASES[s.name][0]
            saved = (self.scope.tvars if self.scope else {}, self.defining)
            if self.scope is None:
                self.scope = Scope("module", None)
            self.scope.tvars = dict(saved[0], **{v.name: v for v in params})
            self.defining = s.name
            try:
                ALIASES[s.name] = (params, self.to_type(s.value))
            finally:
                self.scope.tvars, self.defining = saved

    def check_function(self, node, ft, parent, snapshot):
        scope = Scope("function", parent, snapshot=snapshot, func=ft)
        scope.locals = set(node.scope.local_names)
        scope.globals = set(node.scope.global_names)
        scope.nonlocals = set(node.scope.nonlocal_names)
        scope.tvars.update({v.name: v for v in ft.tparams})
        names = [n for n, _ in ft.params] + ([ft.vararg[0]] if ft.vararg else [])
        types = [t for _, t in ft.params] + ([ListT(ft.vararg[1])] if ft.vararg else [])
        scope.declared.update(zip(names, types))
        self.scope = scope
        self.prescan(scope, node.body, names)
        self.state = {n: UNBOUND for n in scope.locals}
        self.state.update(zip(names, types))
        self.block(node.body)
        if self.state is not None and not self.assignable(NONE, ft.ret):
            where = start(node.returns) if node.returns is not None else (node.line, node.col - 1)
            self.diag(where, f'Function with declared return type "{show(ft.ret)}" must return value '
                             f'on all code paths' + NONE_HINT)


# ------------------------------------------------------------------ helpers for flow
def join(states):
    """Two (or more) ways meet: each name has any of the types it had on any way."""
    states = [s for s in states if s is not None]
    if not states:
        return None
    if len(states) == 1:
        return dict(states[0])
    out = {}
    for name in states[0]:
        if all(name in s for s in states):
            out[name] = union(s[name] for s in states) if not all(s[name] is UNBOUND for s in states) else UNBOUND
            if isinstance(out[name], Never):
                out[name] = UNBOUND
    return out


def same_state(a, b):
    if a is None or b is None:
        return a is b
    return a.keys() == b.keys() and all(a[k].key() == b[k].key() for k in a)


def narrowing_test(e):
    """Does condition e narrow a name? Gives (the name, a test) or (None, None).
       is_none(x), is_pair(x), ...      x is None      x is not None"""
    if isinstance(e, N.Call) and isinstance(e.func, N.Name) and len(e.args) == 1 \
            and isinstance(e.args[0], N.Name):
        if e.func.id in PREDICATES or e.func.id in GUARDS:
            return e.args[0].id, e.func.id
    if isinstance(e, N.Compare) and len(e.ops) == 1 and isinstance(e.left, N.Name) \
            and isinstance(e.comparators[0], N.Constant) and e.comparators[0].value is None \
            and e.ops[0] in ("is", "is not", "==", "!="):
        return e.left.id, ("is_none" if e.ops[0] in ("is", "==") else "not is_none")
    return None, None


def narrow(t, test):
    """The type of a name when `test` is True, and when it is False."""
    if test == "not is_none":
        yes, no = narrow(t, "is_none")
        return no, yes
    if isinstance(t, Unknown):
        return t, t
    if test in GUARDS:
        return GUARDS[test], t
    keep, rest = [], []
    for m in members(t):
        if PREDICATES[test](m):
            keep.append(m)
        elif m == OBJECT or isinstance(m, (TVar, Unknown)):
            keep.append(PREDICATE_TYPES[test])     # an object may be anything
            rest.append(m)
        else:
            rest.append(m)
    yes = union(keep)
    no = t if len(rest) == len(members(t)) else union(rest)
    return yes, no


def literal_sign(e):
    """+1 for an int literal >= 0 (2), -1 for a negative one (-1), else 0."""
    if isinstance(e, N.Constant) and type(e.value) is int:
        return 1
    if isinstance(e, N.UnaryOp) and e.op == "-" and isinstance(e.operand, N.Constant) \
            and type(e.operand.value) is int:
        return -1 if e.operand.value != 0 else 1
    return 0


def children(e):
    from dataclasses import fields
    out = []
    for f in fields(e):
        v = getattr(e, f.name)
        for x in (v if isinstance(v, list) else [v]):
            if isinstance(x, N.Expr):
                out.append(x)
    return out


def walk_statements(body):
    for s in body:
        yield s
        if isinstance(s, N.FunctionDef):
            yield from walk_statements(s.body)
        elif isinstance(s, (N.If, N.While, N.For)):
            yield from walk_statements(s.body)
            yield from walk_statements(s.orelse)


def all_defs(body, deep=False):
    for s in walk_statements(body):
        if isinstance(s, N.FunctionDef):
            yield s


def globals_made(body):
    found = set()
    for d in all_defs(body):
        found |= set(d.scope.global_names)
    return found


def tidy(diags):
    """As py-slang does: an "unknown type" that follows from another mistake on the same
    line is left out; the rest is in the order of the program."""
    mistakes = {d.line for d in diags if not d.unknown}
    out, seen = [], set()
    for d in sorted(diags, key=lambda d: (d.line, d.col)):
        if d.unknown and d.line in mistakes:
            continue
        k = (d.line, d.col, d.message)
        if k not in seen:
            seen.add(k)
            out.append(d)
    return out


# =====================================================================================
# 9. THE RULES ON ANNOTATIONS (checked first; the first broken rule is reported)
# =====================================================================================
TYPING_MODULES = ("typing", "typing_extensions", "collections.abc")


def check_rules(tree, filename):
    """Every def annotates every parameter and its return type; a declaration has a value;
    types need no import."""
    def fail(kind, msg, node, hint):
        raise SicpSyntaxError(msg, filename, node.line, node.col, kind=kind, hint=hint)

    for s in walk_statements(tree.body):
        if isinstance(s, N.FunctionDef):
            params = list(s.params.args)
            for p in params:
                if p.annotation is None:
                    fail("Missing type annotation",
                         f"parameter '{p.name}' of function '{s.name}' needs a type, as in '{p.name}: int'", p,
                         "in Python §4 Typed every parameter of a def has a type, and so does what it "
                         "returns: def area(w: int, h: int) -> int:")
            if s.params.vararg and getattr(s.params, "vararg_annotation", None) is None:
                v = s.params.vararg
                fail("Missing type annotation",
                     f"parameter '{v}' of function '{s.name}' needs a type, as in '{v}: int'", s, None)
            if s.returns is None:
                fail("Missing type annotation",
                     f"function '{s.name}' needs a return type, as in 'def {s.name}(...) -> int:'", s,
                     "write the type of what the function returns after ->, and -> None if it returns nothing.")
        elif isinstance(s, N.AnnAssign) and s.value is None:
            fail("Feature not supported in this sublanguage: declarations without a value",
                 "declarations without a value are not part of Python §4 Typed", s,
                 "give the name its first value where you declare it: `total: int = 0`.")
        elif isinstance(s, N.ImportFrom) and s.module in TYPING_MODULES:
            feature = (f"imports of types from {s.module} (Callable, Pair, LList and Stream are "
                       f"predeclared, and there is no Any)")
            fail(f"Feature not supported in this sublanguage: {feature}",
                 f"{feature} are not part of Python §4 Typed", s,
                 "Callable, Pair, LList and Stream need no import. For a function that works for any type, "
                 "use a type parameter: def ident[A](x: A) -> A:")


# =====================================================================================
# 10. THE ENTRY POINT
# =====================================================================================
def check(interp, tree, filename):
    """Check a parsed program. Raises SicpSyntaxError (a broken rule) or StaticTypeErrors."""
    check_rules(tree, filename)
    ALIASES.clear()
    ALIASES.update(PREDECLARED_ALIASES)
    known = interp.lib.names(interp) | set(interp.program_env.vars)
    checker = Checker(known, filename)
    checker.check_program(tree)
    diags = tidy(checker.diags)
    if diags:
        raise StaticTypeErrors(diags, filename)
