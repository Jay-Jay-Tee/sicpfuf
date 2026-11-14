"""
sicpfuf/lib — the names that exist before your program starts.

    chapter   what is added
    -------   ------------------------------------------------------------------
    §1        MISC (print, error, is_number, ...) and MATH (math_sqrt, math_pi, ...)
    §2        LINKED LISTS (pair, head, tail, llist, map, filter, reduce, ...)
    §3        PAIR MUTATORS (set_head, set_tail), LISTS (is_list), STREAMS (stream_tail, ...)
    §4        MCE (parse, tokenize, apply_in_underlying_python)

Two kinds of library function live here:

  * BUILTINS are written in ordinary Python (pair, head, print, math_sqrt, ...).
  * The rest (map, filter, reduce, stream_map, ...) are written in Python §2/§3
    ITSELF, in the `PRELUDE` strings of linked_list.py and stream.py, and are
    run through this very interpreter when it starts. Read them: they are the
    best worked examples of linked-list and stream programming you can find.

Modules (rune, curve, sound, repeat) are not here. They live in sicpfuf/modules
and only exist after `from rune import ...`.
"""

from ..values import Builtin
from . import misc, mathlib, linked_list, stream, mce, xraylib

# which chapter introduces which library names (for "that name only exists from §3 on")
CHAPTER_OF = {}
for _name in linked_list.NAMES:
    CHAPTER_OF[_name] = 2
for _name in stream.NAMES + ("set_head", "set_tail", "is_list"):
    CHAPTER_OF[_name] = 3
for _name in mce.NAMES:
    CHAPTER_OF[_name] = 4


def install(interp):
    """Fill the builtins frame (and run the preludes) for interp.chapter."""
    b = interp.builtins_env.vars
    b.update(misc.make(interp))
    b.update(mathlib.make())
    b.update(xraylib.make(interp))
    if interp.chapter >= 2:
        b.update(linked_list.make(interp))
        interp.run_library(linked_list.PRELUDE, "linked list")
    if interp.chapter >= 3:
        b.update(linked_list.make_mutators())
        b.update(stream.make(interp))
        interp.run_library(stream.PRELUDE, "stream")
    if interp.chapter >= 4:
        b.update(mce.make(interp))


def names(interp):
    return set(interp.builtins_env.vars) | set(interp.library_env.vars)


def later_names(chapter):
    return {n: c for n, c in CHAPTER_OF.items() if c > chapter}


def module_exports():
    from .. import modules
    return modules.exports()


def load_module(interp, name):
    from .. import modules
    return modules.load(interp, name)


def builtin(name, fn, lo=0, hi=-1, needs_interp=False):
    """hi=-1 means "exactly lo arguments"; hi=None means "any number from lo up"."""
    return Builtin(name, fn, lo, lo if hi == -1 else hi, needs_interp)
