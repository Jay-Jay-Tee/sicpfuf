"""
sicpfuf/modules — things you must IMPORT before using them:

    from rune import show, heart, beside
    from curve import draw_connected, make_point
    from sound import make_sound, play
    from repeat import repeat_apply

Module names are not built into the language. That is the difference between a
BUILTIN name (always there) and an IMPORTED name (declared by the import statement).
"""

import importlib

MODULE_NAMES = ("rune", "curve", "sound", "repeat")
_exports = None


def exports():
    """{'rune': {'show', 'heart', ...}, ...} without building the modules."""
    global _exports
    if _exports is None:
        _exports = {}
        for name in MODULE_NAMES:
            try:
                mod = importlib.import_module(f"{__name__}.{name}_module")
            except ImportError:
                continue
            _exports[name] = set(mod.NAMES)
    return _exports


def load(interp, name):
    """The dict of values a `from name import ...` can pick from (built once per run)."""
    if name not in interp.modules:
        mod = importlib.import_module(f"{__name__}.{name}_module")
        interp.modules[name] = mod.make(interp)
    return interp.modules[name]
