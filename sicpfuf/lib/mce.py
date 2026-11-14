"""
sicpfuf/lib/mce.py — helpers for the METACIRCULAR EVALUATOR (from §4).

    parse("x = 1 + 2")

turns program TEXT into a TREE made of tagged linked lists:

    llist("assignment", llist("name", "x"),
          llist("binary_operator_combination", "+", llist("literal", 1), llist("literal", 2)))

Every node is a llist whose head is a TAG (a string) saying what kind of
component it is. An evaluator written in Python §4 can then take programs
apart with head and tail: that is "data as programs".

The shapes below are exactly the ones Source Academy's parse produces.
"""

import io
import tokenize as py_tokenize

from .. import nodes as N
from ..errors import SicpError, SicpSyntaxError
from ..values import type_name, a

NAMES = ("parse", "tokenize", "apply_in_underlying_python")


def llist(*items):
    result = None
    for x in reversed(items):
        result = [x, result]
    return result


def name_node(name):
    return llist("name", name)


def sequence(stmts):
    """One statement stands for itself; several become a "sequence"."""
    if len(stmts) == 1:
        return transform(stmts[0])
    return llist("sequence", llist(*[transform(s) for s in stmts]))


def else_or_pass(stmts):
    return llist("pass_statement") if not stmts else sequence(stmts)


def parameters(params):
    out = [name_node(p.name) for p in params.args]
    if params.vararg:
        out.append(llist("rest_element", name_node(params.vararg)))
    return llist(*out)


def unsupported(what):
    raise SicpError("SyntaxError", f"parse: {what} are not supported in parse trees")


def transform(node):
    cls = type(node)
    if cls is N.Module:
        return sequence(node.body)
    if cls is N.ExprStmt:
        return transform(node.value)
    if cls is N.Constant:
        return llist("literal", node.value)
    if cls is N.Name:
        return name_node(node.id)
    if cls is N.BinOp:
        return llist("binary_operator_combination", node.op, transform(node.left), transform(node.right))
    if cls is N.Compare:
        if len(node.ops) > 1:
            unsupported("chained comparisons")
        if node.ops[0] in ("in", "not in"):
            unsupported("membership operators")
        return llist("binary_operator_combination", node.ops[0],
                     transform(node.left), transform(node.comparators[0]))
    if cls is N.BoolOp:                               # a and b and c  is  (a and b) and c
        tree = transform(node.values[0])
        for operand in node.values[1:]:
            tree = llist("logical_composition", node.op, tree, transform(operand))
        return tree
    if cls is N.UnaryOp:
        op = {"-": "-unary", "+": "+unary"}.get(node.op, node.op)
        return llist("unary_operator_combination", op, transform(node.operand))
    if cls is N.Assign:
        target = node.targets[0]
        if type(target) is N.Subscript:
            return llist("list_assignment", transform(target.value), transform(target.index),
                         transform(node.value))
        if type(target) is not N.Name or len(node.targets) > 1:
            unsupported("these assignments")
        return llist("assignment", transform(target), transform(node.value))
    if cls is N.If:
        return llist("conditional_statement", transform(node.test), sequence(node.body),
                     else_or_pass(node.orelse))
    if cls is N.IfExp:
        return llist("conditional_expression", transform(node.test), transform(node.body),
                     transform(node.orelse))
    if cls is N.While:
        return llist("while_loop", transform(node.test), sequence(node.body))
    if cls is N.For:
        it = node.iter
        if not (type(it) is N.Call and type(it.func) is N.Name and it.func.id == "range"
                and 1 <= len(it.args) <= 3 and type(node.target) is N.Name):
            unsupported("for loops without range()")
        return llist("for_loop", name_node(node.target.id),
                     llist("range_args", *[transform(x) for x in it.args]), sequence(node.body))
    if cls is N.FunctionDef:
        return llist("function_definition", name_node(node.name), parameters(node.params),
                     sequence(node.body))
    if cls is N.Lambda:
        return llist("lambda_expression", parameters(node.params), transform(node.body))
    if cls is N.Return:
        if node.value is None:
            unsupported("return statements without a value")
        return llist("return_statement", transform(node.value))
    if cls is N.Call:
        if node.keywords:
            unsupported("keyword arguments")
        return llist("application", transform(node.func), llist(*[transform(x) for x in node.args]))
    if cls is N.ListExpr:
        return llist("list_expression", llist(*[transform(x) for x in node.elts]))
    if cls is N.Subscript:
        return llist("list_access", transform(node.value), transform(node.index))
    if cls is N.Starred:
        return llist("starred_expression", transform(node.value))
    if cls is N.ImportFrom:
        return llist("import_from", node.module, llist(*[alias.name for alias in node.names]))
    if cls is N.Global:
        return llist("global_statement", llist(*[name_node(n) for n in node.names]))
    if cls is N.Nonlocal:
        return llist("nonlocal_statement", llist(*[name_node(n) for n in node.names]))
    if cls is N.Pass:
        return llist("pass_statement")
    if cls is N.Break:
        return llist("break_statement")
    if cls is N.Continue:
        return llist("continue_statement")
    unsupported(cls.__name__ + " components")


def make(interp):
    from . import builtin
    from ..parser import parse as parse_text

    def parse(program):
        if type(program) is not str:
            raise SicpError("TypeError", f"parse expects a string, but got {a(type_name(program))}")
        try:
            tree = parse_text(program + "\n", "<parse>")
        except SicpSyntaxError as e:
            raise SicpError("SyntaxError", f"parse: {e.msg} (line {e.line} of the program text)") from None
        return transform(tree)

    def tokenize(program):
        if type(program) is not str:
            raise SicpError("TypeError", f"tokenize expects a string, but got {a(type_name(program))}")
        skipped = (py_tokenize.COMMENT, py_tokenize.NL, py_tokenize.ENDMARKER)
        tokens = []
        try:
            for token in py_tokenize.generate_tokens(io.StringIO(program).readline):
                if token.type in skipped or (token.type == py_tokenize.NEWLINE and token.string == ""):
                    continue
                tokens.append("" if token.type == py_tokenize.INDENT else token.string)
        except (py_tokenize.TokenError, IndentationError, SyntaxError) as e:
            raise SicpError("SyntaxError", f"tokenize: {e}") from None
        return llist(*tokens)

    def apply_in_underlying_python(interp_, node, fun, args_llist):
        """Call the REAL function `fun` with the items of a linked list as its arguments.
        This is how the metacircular evaluator runs primitive functions like + and print."""
        args = []
        while type(args_llist) is list and len(args_llist) == 2:
            args.append(args_llist[0])
            args_llist = args_llist[1]
        if args_llist is not None:
            raise SicpError("TypeError", "apply_in_underlying_python(f, xs) expects a linked list as xs")
        return interp_.apply(fun, args, node)

    return {
        "parse": builtin("parse", parse, 1),
        "tokenize": builtin("tokenize", tokenize, 1),
        "apply_in_underlying_python": builtin("apply_in_underlying_python", apply_in_underlying_python,
                                              2, -1, True),
    }
