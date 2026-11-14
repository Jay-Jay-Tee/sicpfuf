"""
sicpfuf/__main__.py — the command line.

    python3 -m sicpfuf program.py             run a program (as Python §4)
    python3 -m sicpfuf program.py -v 2        ... as Python §2      (-v 1, -v 2, -v 3, -v 4)
    python3 -m sicpfuf -c "print(2 ** 100)"   run a one-liner

    x-ray flags
      --subst          show the SUBSTITUTION MODEL, step by step        (§1 and §2)
      --estep          show the ENVIRONMENT MODEL, step by step         (the "e-stepper")
      --trace NAMES    draw the call tree of these functions            (--trace fib,helper)
      --env            draw the ENVIRONMENT DIAGRAM when the program ends
      --steps          report time (steps, calls) and space (calls waiting at once)
      --tokens         show the lexer's output and stop
      --ast            show the parser's tree and stop
      --typed          check the type annotations first                 (Python §4 Typed)
      --out FOLDER     save the pictures and sounds the program makes   (rune, curve, sound)

A program can also choose its own chapter with a first line like   # chapter 2

Why a THREAD? A tree-walking interpreter uses several Python stack frames per
function call of your program. To let a program have 1024 calls waiting (the
limit of Source Academy's Python), we run it in a thread with a big stack.
"""

import argparse
import ctypes
import re
import sys
import threading

from .errors import SicpSyntaxError, SicpError, format_syntax_error, format_runtime_error
from .interpreter import Interpreter
from .lexer import tokenize, format_tokens
from .nodes import format_ast
from .parser import parse

CHAPTER_LINE = re.compile(r"#\s*(?:chapter|§|python\s*§)\s*([1-4])\b", re.I)


def run_with_big_stack(fn):
    """Run fn() in a big-stack thread; Ctrl-C still interrupts it."""
    sys.setrecursionlimit(1_000_000)
    threading.stack_size(512 * 1024 * 1024)
    box = {}

    def target():
        try:
            box["result"] = fn()
        except BaseException as e:            # hand everything back to the main thread
            box["error"] = e

    t = threading.Thread(target=target, daemon=True)
    t.start()
    while t.is_alive():
        try:
            t.join(0.05)
        except KeyboardInterrupt:
            # deliver the Ctrl-C into the worker thread (a CPython trick)
            ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_ulong(t.ident),
                                                       ctypes.py_object(KeyboardInterrupt))
    if "error" in box:
        raise box["error"]
    return box.get("result")


def chapter_of(source, flag):
    if flag is not None:
        return flag
    first = source.lstrip("\n").split("\n", 1)[0]
    m = CHAPTER_LINE.match(first.strip())
    return int(m.group(1)) if m else 4


def format_error(interp, e, filename):
    lines = interp.sources.get(filename)
    if isinstance(e, SicpSyntaxError):
        return format_syntax_error(e, lines)
    if isinstance(e, SicpError):
        return format_runtime_error(e, lines)
    if isinstance(e, RecursionError):
        return ("RecursionError\nRecursionError: the structure is nested too deeply for sicpfuf to handle")
    return f"{type(e).__name__}: {e}"


def run_program(source, filename, args):
    chapter = chapter_of(source, args.chapter)
    if args.estep:
        from .xray.estepper import EnvStepper
        interp = EnvStepper(chapter, typed=args.typed)
    else:
        interp = Interpreter(chapter, typed=args.typed)
    interp.out_dir = args.out
    interp.out_stem = args.stem
    code = 0
    try:
        tree = interp.load_source(source, filename)
        if args.typed:
            from .xray import typecheck
            typecheck.check(interp, tree, filename)
        if args.subst:
            from .xray import stepper
            stepper.run(interp, tree, filename, limit=args.max_steps)
        else:
            if args.trace:
                from .xray import calltree
                calltree.trace_names(interp, [n for n in args.trace.split(",") if n])
            interp.run_tree(tree)
    except KeyboardInterrupt:
        sys.stdout.flush()
        print("\nKeyboardInterrupt", file=sys.stderr)
        code = 130
    except (SicpSyntaxError, SicpError, RecursionError) as e:
        sys.stdout.flush()
        print(format_error(interp, e, filename), file=sys.stderr)
        code = 1
    sys.stdout.flush()
    if args.env and code == 0:
        from .xray import envdiagram
        envdiagram.show(interp, None, "end of program")
    if args.steps:
        print(f"[steps] time: {interp.steps:,} steps, {interp.calls:,} function calls   "
              f"space: at most {interp.max_seen:,} calls waiting at once", file=sys.stderr)
    return code


def main(argv=None):
    ap = argparse.ArgumentParser(prog="sicpfuf", description="sicpfuf: Python §1-§4 with x-ray vision")
    ap.add_argument("file", nargs="?", help="a program file (omit for the interactive prompt)")
    ap.add_argument("-c", dest="code", help="program passed as a string")
    ap.add_argument("-v", "--chapter", type=int, choices=(1, 2, 3, 4), default=None,
                    help="which Python § to run (default: 4, or the file's `# chapter N` line)")
    ap.add_argument("--subst", action="store_true", help="show the substitution model step by step")
    ap.add_argument("--max-steps", type=int, default=400, help="--subst: stop after this many steps")
    ap.add_argument("--estep", action="store_true", help="show the environment model step by step")
    ap.add_argument("--trace", metavar="NAMES", help="draw the call tree of these functions (comma separated)")
    ap.add_argument("--env", action="store_true", help="draw the environment diagram at the end")
    ap.add_argument("--steps", action="store_true", help="report steps, calls and space used")
    ap.add_argument("--tokens", action="store_true", help="print the token stream and stop")
    ap.add_argument("--ast", action="store_true", help="print the syntax tree and stop")
    ap.add_argument("--typed", action="store_true", help="check type annotations first (Python §4 Typed)")
    ap.add_argument("--out", default=None, metavar="FOLDER",
                    help="save pictures (SVG) and sounds (WAV) made by show / draw_connected / play here")
    ap.add_argument("--stem", default=None, help=argparse.SUPPRESS)     # file name prefix for --out
    args = ap.parse_args(argv)

    if args.code is None and args.file is None:
        from .repl import repl
        return repl(args.chapter or 4)

    if args.code is not None:
        source, filename = args.code, "<string>"
    else:
        try:
            with open(args.file, encoding="utf-8") as f:
                source = f.read()
        except OSError as e:
            print(f"sicpfuf: can't open file '{args.file}': {e.strerror}", file=sys.stderr)
            return 2
        filename = args.file

    if args.tokens or args.ast:
        try:
            if args.tokens:
                print(format_tokens(tokenize(source, filename)))
            if args.ast:
                print(format_ast(parse(source, filename)))
        except SicpSyntaxError as e:
            print(format_syntax_error(e, source.split("\n")), file=sys.stderr)
            return 1
        return 0

    return run_with_big_stack(lambda: run_program(source, filename, args))


if __name__ == "__main__":
    sys.exit(main())
