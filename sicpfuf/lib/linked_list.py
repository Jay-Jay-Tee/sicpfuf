"""
sicpfuf/lib/linked_list.py — pairs and linked lists (the LINKED LISTS library, from §2).

THE WHOLE DATA STRUCTURE IS ONE IDEA:

    pair(h, t)      glue two values together          head(p) → h      tail(p) → t

A LINKED LIST ("llist") is either None (the empty llist), or a pair whose tail
is a llist:

    llist(1, 2, 3)   is   pair(1, pair(2, pair(3, None)))   and prints as   [1, [2, [3, None]]]

Only six functions are written in ordinary Python below. Everything else is in
PRELUDE: plain Python §2, built from those six. Notice how each one is either

    * an ITERATIVE process (carries an accumulator, ends in a tail call), or
    * written in CONTINUATION-PASSING STYLE (append, reduce),

so that none of them piles up deferred operations, however long the llist is.
"""

from ..errors import SicpError
from ..values import to_repr, short, is_pair

NAMES = ("pair", "head", "tail", "is_pair", "llist", "print_llist", "draw_data",
         "is_llist", "length", "map", "build_llist", "for_each", "llist_to_string", "reverse",
         "append", "member", "remove", "remove_all", "enum_llist", "llist_ref", "reduce", "filter")


def make(interp):
    from . import builtin

    def pair(h, t):
        return [h, t]                 # THE PAIR SECRET: a pair is a list with exactly two items

    def llist(*items):
        result = None
        for x in reversed(items):
            result = [x, result]
        return result

    def head(p):
        if type(p) is list and len(p) == 2:
            return p[0]
        raise SicpError("TypeError", f"head(xs) expects a pair as argument xs, but encountered {short(p)}")

    def tail(p):
        if type(p) is list and len(p) == 2:
            return p[1]
        raise SicpError("TypeError", f"tail(xs) expects a pair as argument xs, but encountered {short(p)}")

    def print_llist(interp_, node, x):
        """Show x in LLIST NOTATION:  llist(1, 2, 3)  instead of  [1, [2, [3, None]]]."""
        interp_.write(llist_notation(x) + "\n")
        return None

    def draw_data(interp_, node, *xs):
        """Draw the box-and-pointer diagram of each argument. Returns the first one."""
        from ..xray import boxpointer
        for x in xs:
            interp_.write(boxpointer.draw(x) + "\n")
        return xs[0]

    return {
        "pair": builtin("pair", pair, 2),
        "llist": builtin("llist", llist, 0, None),
        "is_pair": builtin("is_pair", is_pair, 1),
        "head": builtin("head", head, 1),
        "tail": builtin("tail", tail, 1),
        "print_llist": builtin("print_llist", print_llist, 1, -1, True),
        "draw_data": builtin("draw_data", draw_data, 1, None, True),
    }


def make_mutators():
    """PAIR MUTATORS (from §3): change a pair that already exists."""
    from . import builtin

    def set_head(p, value):
        if type(p) is list and len(p) == 2:
            p[0] = value
            return None
        raise SicpError("TypeError", f"set_head(p, x) expects a pair as argument p, but encountered {short(p)}")

    def set_tail(p, value):
        if type(p) is list and len(p) == 2:
            p[1] = value
            return None
        raise SicpError("TypeError", f"set_tail(p, x) expects a pair as argument p, but encountered {short(p)}")

    def is_list(x):
        return type(x) is list

    return {"set_head": builtin("set_head", set_head, 2), "set_tail": builtin("set_tail", set_tail, 2),
            "is_list": builtin("is_list", is_list, 1)}


def is_proper_llist(x):
    seen = 0
    while type(x) is list and len(x) == 2:
        x = x[1]
        seen += 1
        if seen > 1_000_000:          # a circular structure never reaches None
            return False
    return x is None


def llist_notation(x, depth=0):
    if depth > 200:
        return "..."
    if x is None:
        return "llist()"
    if not is_pair(x):
        return to_repr(x)
    if not is_proper_llist(x):
        return "[" + llist_notation(x[0], depth + 1) + ", " + llist_notation(x[1], depth + 1) + "]"
    parts = []
    while x is not None:
        parts.append(llist_notation(x[0], depth + 1))
        x = x[1]
    return "llist(" + ", ".join(parts) + ")"


PRELUDE = '''
def is_llist(xs):
    return is_none(xs) or (is_pair(xs) and is_llist(tail(xs)))

def length(xs):
    def count(ys, so_far):
        return so_far if is_none(ys) else count(tail(ys), so_far + 1)
    return count(xs, 0)

def reverse(xs):
    def rev(original, reversed_so_far):
        return (reversed_so_far
                if is_none(original)
                else rev(tail(original), pair(head(original), reversed_so_far)))
    return rev(xs, None)

def map(f, xs):
    def go(ys, done):
        return reverse(done) if is_none(ys) else go(tail(ys), pair(f(head(ys)), done))
    return go(xs, None)

def filter(pred, xs):
    def go(ys, kept):
        if is_none(ys):
            return reverse(kept)
        elif pred(head(ys)):
            return go(tail(ys), pair(head(ys), kept))
        else:
            return go(tail(ys), kept)
    return go(xs, None)

def reduce(f, initial, xs):
    def go(ys, cont):
        return (cont(initial)
                if is_none(ys)
                else go(tail(ys), lambda reduced_tail: cont(f(head(ys), reduced_tail))))
    return go(xs, lambda x: x)

def append(xs, ys):
    def go(zs, cont):
        return (cont(ys)
                if is_none(zs)
                else go(tail(zs), lambda appended_tail: cont(pair(head(zs), appended_tail))))
    return go(xs, lambda x: x)

def member(v, xs):
    if is_none(xs):
        return None
    elif v == head(xs):
        return xs
    else:
        return member(v, tail(xs))

def remove(v, xs):
    def go(ys, kept):
        if is_none(ys):
            return reverse(kept)
        elif v == head(ys):
            return append(reverse(kept), tail(ys))
        else:
            return go(tail(ys), pair(head(ys), kept))
    return go(xs, None)

def remove_all(v, xs):
    def go(ys, kept):
        if is_none(ys):
            return reverse(kept)
        elif v == head(ys):
            return go(tail(ys), kept)
        else:
            return go(tail(ys), pair(head(ys), kept))
    return go(xs, None)

def enum_llist(start, end):
    def go(n, built):
        return reverse(built) if n > end else go(n + 1, pair(n, built))
    return go(start, None)

def build_llist(fun, n):
    def go(i, built):
        return built if i < 0 else go(i - 1, pair(fun(i), built))
    return go(n - 1, None)

def for_each(fun, xs):
    if is_none(xs):
        return True
    else:
        fun(head(xs))
        return for_each(fun, tail(xs))

def llist_ref(xs, n):
    if is_none(xs):
        return error("llist_ref: index out of bounds")
    elif n == 0:
        return head(xs)
    else:
        return llist_ref(tail(xs), n - 1)

def llist_to_string(xs):
    def go(ys, cont):
        if is_none(ys):
            return cont("None")
        elif is_pair(ys):
            return go(head(ys), lambda h: go(tail(ys), lambda t: cont("[" + h + ", " + t + "]")))
        else:
            return cont(repr(ys))
    return go(xs, lambda x: x)
'''
