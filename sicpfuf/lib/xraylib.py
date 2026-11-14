"""
sicpfuf/lib/xraylib.py — the X-RAY builtins. They exist ONLY in sicpfuf (not in
Source Academy), and they exist in every chapter:

    trace(f, a, b)      run f(a, b) and draw the tree of calls it makes
    measure(f, a, b)    run f(a, b) and report time (calls, steps) and space (calls waiting)
    show_env()          draw the environment diagram at this very moment
    draw_data(x)        draw the box-and-pointer diagram of x   (that one IS in Source Academy)
"""


def make(interp):
    from . import builtin

    def trace(interp_, node, f, *args):
        from ..xray import calltree
        return calltree.trace(interp_, node, f, args)

    def measure(interp_, node, f, *args):
        from ..xray import calltree
        return calltree.measure(interp_, node, f, args)

    def show_env(interp_, node, *label):
        from ..xray import envdiagram
        envdiagram.show(interp_, node, label[0] if label else None)
        return None

    return {
        "trace": builtin("trace", trace, 1, None, True),
        "measure": builtin("measure", measure, 1, None, True),
        "show_env": builtin("show_env", show_env, 0, 1, True),
    }
