"""
sicpfuf/lib/misc.py — the MISC library: print, error, type questions, a few helpers.

Every function here exists in all four chapters.
"""

import random
import time

from ..errors import SicpError, UserError
from ..values import Closure, Builtin, to_str, to_repr, type_name, a, is_function


def make(interp):
    from . import builtin

    # ------------------------------------------------------------ output and errors
    def b_print(interp_, node, *args):
        """print(a, b, ...) shows the values on one line, separated by spaces.
        A string on its own is shown WITHOUT quotes; inside a pair or list it has quotes."""
        interp_.write(" ".join([to_str(x) for x in args]) + "\n")
        return None

    def b_error(*args):
        """error(a, b, ...) stops the whole program with the message "Error: a b ..."."""
        raise UserError(" ".join([to_str(x) for x in args]))

    def b_input(interp_, node, *prompt):
        if prompt:
            interp_.write(to_str(prompt[0]))
        interp_.out.flush()
        try:
            return input()
        except EOFError:
            return ""

    def b_str(*args):
        return to_str(args[0]) if args else ""

    def b_repr(x):
        return to_repr(x)

    # ------------------------------------------------------------ type questions
    def is_none(x):
        return x is None

    def is_integer(x):
        return type(x) is int

    def is_float(x):
        return type(x) is float

    def is_complex(x):
        return type(x) is complex

    def is_number(x):
        return type(x) in (int, float, complex)      # booleans are NOT numbers here

    def is_string(x):
        return type(x) is str

    def is_boolean(x):
        return type(x) is bool

    def arity(f):
        """How many arguments does f take? (For *rest functions: the fixed ones.)"""
        if type(f) is Closure:
            return len(f.params)
        if type(f) is Builtin:
            return f.min_args
        raise SicpError("TypeError", f"arity(f) expects a function, but got {a(type_name(f))}")

    # ------------------------------------------------------------ numbers
    def need_number(name, x, allow_complex=False):
        t = type(x)
        if t is int or t is float or (allow_complex and t is complex):
            return
        raise SicpError("TypeError", f"{name} expects a number, but got {a(type_name(x))}")

    def b_abs(x):
        need_number("abs(x)", x, True)
        return abs(x)

    def extreme(name, pick):
        def f(*args):
            if all(type(x) in (int, float) for x in args) or all(type(x) is str for x in args):
                return pick(args)
            raise SicpError("TypeError", f"{name}(...) needs all numbers or all strings, but got "
                            + ", ".join(type_name(x) for x in args))
        return f

    def b_round(x, *ndigits):
        need_number("round(x)", x)
        if not ndigits or ndigits[0] is None:
            return round(x)                       # round half to EVEN: round(2.5) is 2, round(3.5) is 4
        if type(ndigits[0]) is not int:
            raise SicpError("TypeError", f"round(x, n) expects an integer n, but got {a(type_name(ndigits[0]))}")
        if type(x) is float and ndigits[0] >= 0:
            # round the number AS WRITTEN (2.675 → 2.68), half to even, like Source Academy
            import decimal
            step = decimal.Decimal(1).scaleb(-ndigits[0])
            return float(decimal.Decimal(repr(x)).quantize(step, rounding=decimal.ROUND_HALF_EVEN))
        return round(x, ndigits[0])

    def b_len(x):
        if type(x) is str or type(x) is list:
            return len(x)
        raise SicpError("TypeError", f"len(x) expects a list or a string, but got {a(type_name(x))}")

    def b_complex(*args):
        for x in args:
            if type(x) not in (int, float, complex, bool, str):
                raise SicpError("TypeError", f"complex() can't use {a(type_name(x))}")
        try:
            return complex(*args)
        except (TypeError, ValueError) as e:
            raise SicpError(type(e).__name__, str(e)) from None

    def real(z):
        if type(z) is not complex:
            raise SicpError("TypeError", f"real(z) expects a complex number, but got {a(type_name(z))}")
        return z.real

    def imag(z):
        if type(z) is not complex:
            raise SicpError("TypeError", f"imag(z) expects a complex number, but got {a(type_name(z))}")
        return z.imag

    return {
        "print": builtin("print", b_print, 0, None, True),
        "error": builtin("error", b_error, 0, None),
        "input": builtin("input", b_input, 0, 1, True),
        "str": builtin("str", b_str, 0, 1),
        "repr": builtin("repr", b_repr, 1),
        "is_none": builtin("is_none", is_none, 1),
        "is_integer": builtin("is_integer", is_integer, 1),
        "is_float": builtin("is_float", is_float, 1),
        "is_complex": builtin("is_complex", is_complex, 1),
        "is_number": builtin("is_number", is_number, 1),
        "is_string": builtin("is_string", is_string, 1),
        "is_boolean": builtin("is_boolean", is_boolean, 1),
        "is_function": builtin("is_function", is_function, 1),
        "arity": builtin("arity", arity, 1),
        "abs": builtin("abs", b_abs, 1),
        "max": builtin("max", extreme("max", max), 2, None),
        "min": builtin("min", extreme("min", min), 2, None),
        "round": builtin("round", b_round, 1, 2),
        "len": builtin("len", b_len, 1),
        "complex": builtin("complex", b_complex, 0, 2),
        "real": builtin("real", real, 1),
        "imag": builtin("imag", imag, 1),
        "random_random": builtin("random_random", random.random, 0),
        "time_time": builtin("time_time", time.time, 0),
        "breakpoint": builtin("breakpoint", lambda *args: None, 0, None),
    }
