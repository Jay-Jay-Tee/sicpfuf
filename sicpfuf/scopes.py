"""
sicpfuf/scopes.py — decide, BEFORE running, which names are local to each function.

This is the most surprising rule in Python, and the cause of UnboundLocalError:

    count = 0
    def bump():
        print(count)    # UnboundLocalError!  ...but why? count exists globally!
        count = 1       # <- because THIS line makes `count` local for the WHOLE function

Python does not decide line by line. When it COMPILES a function, it scans the whole
body, and any name that is ASSIGNED anywhere in it (=, +=, for x in, def x, import x,
except E as x, ...) becomes a local variable of that function, unless the function
says `global count` or `nonlocal count`.

sicpfuf does exactly the same scan here (CPython's version lives in Python/symtable.c,
and you can poke at it with the `symtable` module). In Python §3 the error is called
UnassignedLocalError, and in the ENVIRONMENT MODEL it has a neat explanation: the
name already has a slot in the function's new frame, but the slot is still empty.

(This file is shared with pfuf, sicpfuf's sibling project.)

SYLLABUS LESSONS: scope and lifetime of variables, sets (set difference!),
recursion over a tree.
"""

from . import nodes as N
from .errors import SicpSyntaxError


def target_names(target, out):
    """Collect names bound by an assignment target:  a   (a, b)   [x, (y, z)]"""
    if isinstance(target, N.Name):
        out.add(target.id)
    elif isinstance(target, (N.TupleExpr, N.ListExpr)):
        for e in target.elts:
            target_names(e, out)
    elif isinstance(target, N.Starred):
        target_names(target.value, out)
    # Attribute (obj.x = ...) and Subscript (xs[0] = ...) don't create variables.


def scan_block(stmts, info):
    """Walk statements; returns True if any of them contains a `yield`.
    Doesn't go INTO nested def/class bodies (they get their own scope)."""
    found = False
    for s in stmts:
        if scan_stmt(s, info):
            s.contains_yield = True
            found = True
    return found


def scan_stmt(s, info):
    assigned, globals_, nonlocals = info["assigned"], info["global"], info["nonlocal"]
    if isinstance(s, (N.Yield, N.YieldFrom)):
        return True
    if isinstance(s, N.Assign):
        for t in s.targets:
            target_names(t, assigned)
    elif isinstance(s, N.AnnAssign):
        if s.value is not None:
            target_names(s.target, assigned)
    elif isinstance(s, N.AugAssign):
        target_names(s.target, assigned)
    elif isinstance(s, N.Delete):
        for t in s.targets:
            target_names(t, assigned)
    elif isinstance(s, (N.FunctionDef, N.ClassDef)):
        assigned.add(s.name)                      # `def f` assigns the name f
    elif isinstance(s, N.Import):
        for a in s.names:
            assigned.add(a.asname or a.name.split(".")[0])
    elif isinstance(s, N.ImportFrom):
        for a in s.names:
            if a.name != "*":
                assigned.add(a.asname or a.name)
    elif isinstance(s, N.Global):
        globals_.update(s.names)
    elif isinstance(s, N.Nonlocal):
        nonlocals.update(s.names)
    elif isinstance(s, N.For):
        target_names(s.target, assigned)
        a = scan_block(s.body, info)
        b = scan_block(s.orelse, info)
        return a or b
    elif isinstance(s, N.While):
        a = scan_block(s.body, info)
        b = scan_block(s.orelse, info)
        return a or b
    elif isinstance(s, N.If):
        a = scan_block(s.body, info)
        b = scan_block(s.orelse, info)
        return a or b
    elif isinstance(s, N.With):
        for item in s.items:
            if item.target is not None:
                target_names(item.target, assigned)
        return scan_block(s.body, info)
    elif isinstance(s, N.Try):
        found = scan_block(s.body, info)
        for h in s.handlers:
            if h.name:
                assigned.add(h.name)
            found = scan_block(h.body, info) or found
        found = scan_block(s.orelse, info) or found
        found = scan_block(s.finalbody, info) or found
        return found
    return False


class ScopeInfo:
    """What the interpreter needs to know about a function's variables."""

    def __init__(self, local_names, global_names, nonlocal_names, is_generator):
        self.local_names = frozenset(local_names)
        self.global_names = frozenset(global_names)
        self.nonlocal_names = frozenset(nonlocal_names)
        self.is_generator = is_generator


def param_names(params):
    names = [p.name for p in params.args] + [p.name for p in params.kwonly]
    if params.vararg:
        names.append(params.vararg)
    if params.kwarg:
        names.append(params.kwarg)
    return names


def analyze_function(node, filename="<sicpfuf>"):
    """Attach `node.scope` (a ScopeInfo) to a FunctionDef or Lambda node."""
    params = set(param_names(node.params))
    info = {"assigned": set(params), "global": set(), "nonlocal": set()}
    is_gen = False
    if isinstance(node, N.FunctionDef):
        is_gen = scan_block(node.body, info)
    clash = (info["global"] | info["nonlocal"]) & params
    if clash:
        name = sorted(clash)[0]
        raise SicpSyntaxError(f"name '{name}' is parameter and global/nonlocal", filename, node.line)
    both = info["global"] & info["nonlocal"]
    if both:
        raise SicpSyntaxError(f"name '{sorted(both)[0]}' is nonlocal and global", filename, node.line)
    # set difference: everything assigned, minus what was declared global/nonlocal
    local = info["assigned"] - info["global"] - info["nonlocal"]
    node.scope = ScopeInfo(local, info["global"], info["nonlocal"], is_gen)
    return node.scope
