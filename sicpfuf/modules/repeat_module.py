"""
sicpfuf/modules/repeat_module.py —  from repeat import repeat_apply

    repeat_apply(f, n, x)   is   f(f(...f(x)...))   with f applied n times

It is three lines of Python §1. Writing it yourself is a classic exercise:
one version gives a RECURSIVE process, the other an ITERATIVE one.
"""

NAMES = ("repeat_apply", "repeat", "twice", "thrice")

SOURCE = '''
def repeat_apply(pat, n, init):
    return init if n == 0 else repeat_apply(pat, n - 1, pat(init))

def repeat(pat, n):
    return lambda init: repeat_apply(pat, n, init)

def twice(pat):
    return repeat(pat, 2)

def thrice(pat):
    return repeat(pat, 3)
'''


def make(interp):
    from ..env import Environment
    from ..parser import parse
    from ..interpreter import mark_library
    env = Environment("library", interp.library_env, name="repeat")
    interp.loading_library = True
    try:
        tree = parse(SOURCE, "<repeat module>")
        mark_library(tree)
        interp.exec_block(tree.body, env)
    finally:
        interp.loading_library = False
    return {name: env.vars[name] for name in NAMES}
