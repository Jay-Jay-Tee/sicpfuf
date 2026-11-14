"""
sicpfuf/lib/mathlib.py — the MATH library.

Python has a `math` module (math.sqrt, math.pi). Python §1-§4 have no modules with
dots, so every name is spelled with an underscore instead:  math_sqrt(2),  math_pi.
"""

import math

from ..errors import SicpError
from ..values import type_name, a

CONSTANTS = {"math_pi": math.pi, "math_e": math.e, "math_tau": math.tau,
             "math_inf": math.inf, "math_nan": math.nan}

# name → how many arguments (a pair means "from .. to")
FUNCTIONS = {
    "acos": 1, "acosh": 1, "asin": 1, "asinh": 1, "atan": 1, "atan2": 2, "atanh": 1, "cbrt": 1,
    "ceil": 1, "comb": 2, "copysign": 2, "cos": 1, "cosh": 1, "degrees": 1, "erf": 1, "erfc": 1,
    "exp": 1, "exp2": 1, "expm1": 1, "fabs": 1, "factorial": 1, "floor": 1, "fma": 3, "fmod": 2,
    "gamma": 1, "gcd": (0, None), "isfinite": 1, "isinf": 1, "isnan": 1, "isqrt": 1, "lcm": (0, None),
    "ldexp": 2, "lgamma": 1, "log": (1, 2), "log10": 1, "log1p": 1, "log2": 1, "nextafter": 2,
    "perm": (1, 2), "pow": 2, "radians": 1, "remainder": 2, "sin": 1, "sinh": 1, "sqrt": 1,
    "tan": 1, "tanh": 1, "trunc": 1, "ulp": 1,
}

FALLBACKS = {      # for older Pythons that lack these
    "cbrt": lambda x: math.copysign(abs(x) ** (1 / 3), x),
    "exp2": lambda x: 2.0 ** x,
    "fma": lambda x, y, z: x * y + z,
}


def wrap(name, fn):
    def call(*args):
        for x in args:
            if type(x) is not int and type(x) is not float:
                raise SicpError("TypeError", f"math_{name} expects numbers, but got {a(type_name(x))}")
        try:
            return fn(*args)
        except ValueError:
            raise SicpError("ValueError", f"math domain error: math_{name} can't take "
                            + ", ".join(repr(x) for x in args)) from None
        except OverflowError:
            raise SicpError("OverflowError", "math range error") from None
    return call


def make():
    from . import builtin
    out = dict(CONSTANTS)
    for name, count in FUNCTIONS.items():
        fn = getattr(math, name, None) or FALLBACKS[name]
        lo, hi = count if isinstance(count, tuple) else (count, count)
        out["math_" + name] = builtin("math_" + name, wrap(name, fn), lo, hi)
    return out
