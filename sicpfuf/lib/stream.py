"""
sicpfuf/lib/stream.py — STREAMS (from §3): linked lists whose tail is computed LATER.

A stream is either None, or a pair whose TAIL IS A FUNCTION of no arguments that
returns the rest of the stream when you call it:

    pair(1, lambda: pair(2, lambda: None))

The tail is "wrapped up" (delayed) in a lambda, so nothing after the first item
is computed until someone asks. That is how a stream can be infinite:

    def integers_from(n):
        return pair(n, lambda: integers_from(n + 1))

Only stream(...) is written in ordinary Python. The rest is PRELUDE, plain
Python §3. Read each function and ask: is it LAZY (does it return at once and
leave work in a lambda) or does it walk the whole stream right now?
"""

NAMES = ("stream", "stream_tail", "is_stream", "llist_to_stream", "stream_to_llist", "stream_length",
         "stream_map", "build_stream", "stream_for_each", "stream_reverse", "stream_append",
         "stream_member", "stream_remove", "stream_remove_all", "stream_filter", "enum_stream",
         "integers_from", "eval_stream", "stream_ref")


def make(interp):
    from . import builtin
    from ..values import Builtin

    def stream(*items):
        """stream(1, 2, 3): the stream with exactly these items."""
        if not items:
            return None
        rest = items[1:]
        return [items[0], Builtin("anonymous stream", lambda: stream(*rest), 0, 0)]

    return {"stream": builtin("stream", stream, 0, None)}


PRELUDE = '''
def stream_tail(xs):
    if is_pair(xs):
        the_tail = tail(xs)
        if is_function(the_tail):
            return the_tail()
        else:
            return error(the_tail, "stream_tail(xs) expects a function as the tail of the argument pair xs, but encountered ")
    else:
        return error(xs, "stream_tail(xs) expects a pair as argument xs, but encountered ")

def is_stream(xs):
    return is_none(xs) or (is_pair(xs) and is_function(tail(xs))
                           and arity(tail(xs)) == 0 and is_stream(stream_tail(xs)))

def llist_to_stream(xs):
    return None if is_none(xs) else pair(head(xs), lambda: llist_to_stream(tail(xs)))

def stream_to_llist(xs):
    return None if is_none(xs) else pair(head(xs), stream_to_llist(stream_tail(xs)))

def stream_length(xs):
    return 0 if is_none(xs) else 1 + stream_length(stream_tail(xs))

def stream_map(f, s):
    return None if is_none(s) else pair(f(head(s)), lambda: stream_map(f, stream_tail(s)))

def stream_filter(p, s):
    return (None
            if is_none(s)
            else pair(head(s), lambda: stream_filter(p, stream_tail(s)))
            if p(head(s))
            else stream_filter(p, stream_tail(s)))

def build_stream(fun, n):
    def build(i):
        return None if i >= n else pair(fun(i), lambda: build(i + 1))
    return build(0)

def stream_for_each(fun, xs):
    if is_none(xs):
        return True
    else:
        fun(head(xs))
        return stream_for_each(fun, stream_tail(xs))

def stream_reverse(xs):
    def rev(original, reversed_so_far):
        return (reversed_so_far
                if is_none(original)
                else rev(stream_tail(original), pair(head(original), lambda: reversed_so_far)))
    return rev(xs, None)

def stream_append(xs, ys):
    return ys if is_none(xs) else pair(head(xs), lambda: stream_append(stream_tail(xs), ys))

def stream_member(x, s):
    return None if is_none(s) else s if head(s) == x else stream_member(x, stream_tail(s))

def stream_remove(v, xs):
    return (None
            if is_none(xs)
            else stream_tail(xs)
            if v == head(xs)
            else pair(head(xs), lambda: stream_remove(v, stream_tail(xs))))

def stream_remove_all(v, xs):
    return (None
            if is_none(xs)
            else stream_remove_all(v, stream_tail(xs))
            if v == head(xs)
            else pair(head(xs), lambda: stream_remove_all(v, stream_tail(xs))))

def enum_stream(start, end):
    return None if start > end else pair(start, lambda: enum_stream(start + 1, end))

def integers_from(n):
    return pair(n, lambda: integers_from(n + 1))

def eval_stream(s, n):
    def es(s, n):
        return llist(head(s)) if n == 1 else pair(head(s), es(stream_tail(s), n - 1))
    return None if n == 0 else es(s, n)

def stream_ref(s, n):
    return head(s) if n == 0 else stream_ref(stream_tail(s), n - 1)
'''
