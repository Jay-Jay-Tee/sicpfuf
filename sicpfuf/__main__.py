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
      --ui             open the built-in visual steppers locally
      --out FOLDER     save the pictures and sounds the program makes   (rune, curve, sound)
      --with FILE      run FILE first, then the program                 (--with examples/mce.py)

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
        if hasattr(e, "report"):                  # type errors (xray/typecheck.py): all of them
            return e.report(lines)
        return format_syntax_error(e, lines)
    if isinstance(e, SicpError):
        return format_runtime_error(e, lines)
    if isinstance(e, RecursionError):
        return ("RecursionError\nRecursionError: the structure is nested too deeply for sicpfuf to handle")
    return f"{type(e).__name__}: {e}"


def load_prelude(interp, path):
    """--with FILE: run FILE first (up to its `# DEMO` line), so the program can build on it.
    Used for "here is the evaluator; now change one function" exercises."""
    from .interpreter import mark_library
    with open(path, encoding="utf-8") as f:
        text = f.read()
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("# DEMO"):
            lines = lines[:i]
            break
    tree = interp.load_source("\n".join(lines) + "\n", path)
    mark_library(tree)                      # errors are reported at the line of YOUR program
    interp.run_tree(tree)


def run_program(source, filename, args):
    chapter = 4 if args.typed else chapter_of(source, args.chapter)
    if args.estep:
        from .xray.estepper import EnvStepper
        interp = EnvStepper(chapter, typed=args.typed)
    else:
        interp = Interpreter(chapter, typed=args.typed)
    if args.env:
        interp.diagrams = True
    interp.out_dir = args.out
    interp.out_stem = args.stem
    code = 0
    try:
        if args.prelude:
            load_prelude(interp, args.prelude)
        tree = interp.load_source(source, filename, typecheck=args.typed)     # --typed: types first
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
    ap.add_argument("--max-steps", type=int, default=400, help="steppers: stop after this many steps (default: 400)")
    ap.add_argument("--estep", action="store_true", help="show the environment model step by step")
    ap.add_argument("--trace", metavar="NAMES", help="draw the call tree of these functions (comma separated)")
    ap.add_argument("--env", action="store_true", help="draw the environment diagram at the end")
    ap.add_argument("--steps", action="store_true", help="report steps, calls and space used")
    ap.add_argument("--tokens", action="store_true", help="print the token stream and stop")
    ap.add_argument("--ast", action="store_true", help="print the syntax tree and stop")
    ap.add_argument("--typed", action="store_true", help="check type annotations first (Python §4 Typed)")
    ap.add_argument("--ui", action="store_true", help="open the built-in visual steppers in your browser")
    ap.add_argument("--tui", action="store_true", help="open the stepper inside the terminal")
    ap.add_argument("--no-browser", action="store_true", help="--ui: print the URL without opening a browser")
    ap.add_argument("--port", type=int, default=0, help="--ui: local port (default: choose a free port)")
    ap.add_argument("--out", default=None, metavar="FOLDER",
                    help="save pictures (SVG) and sounds (WAV) made by show / draw_connected / play here")
    ap.add_argument("--with", dest="prelude", metavar="FILE", default=None,
                    help="run FILE first (up to its `# DEMO` line), then the program")
    ap.add_argument("--stem", default=None, help=argparse.SUPPRESS)     # file name prefix for --out
    args = ap.parse_args(argv)
    if args.ui and args.tui:
        ap.error("choose --ui or --tui")
    if (args.no_browser or args.port) and not args.ui:
        ap.error("--no-browser and --port require --ui")
    if args.typed and (args.subst or args.chapter not in (None, 4)):
        ap.error("--typed requires Python §4 and cannot be combined with --subst")

    if args.code is None and args.file is None and not (args.ui or args.tui):
        if args.typed:
            ap.error("--typed needs a file, -c, --ui or --tui; the interactive prompt does not support typed checking")
        from .repl import repl
        return repl(args.chapter or 4)

    if (args.ui or args.tui) and args.code is None and args.file is None:
        source, filename = None, None
    elif args.code is not None:
        source, filename = args.code, "<string>"
    else:
        try:
            with open(args.file, encoding="utf-8") as f:
                source = f.read()
        except OSError as e:
            print(f"sicpfuf: can't open file '{args.file}': {e.strerror}", file=sys.stderr)
            return 2
        filename = args.file

    if args.ui or args.tui:
        if not 2 <= args.max_steps <= 5000:
            ap.error("UI --max-steps must be between 2 and 5000")
        if not 0 <= args.port <= 65535:
            ap.error("--port must be between 0 and 65535")
        if args.prelude or args.tokens or args.ast or args.trace or args.out or args.env or args.steps:
            ap.error("the stepper UI supports -v, --subst, --estep and --typed; use other x-ray flags separately")
        from .ui import serve
        chapter = chapter_of(source, args.chapter) if source is not None else args.chapter or 2
        if args.typed:
            chapter = 4
        first_line = (source or "").lstrip("\n").split("\n", 1)[0].strip()
        if args.subst and args.chapter is None and not CHAPTER_LINE.match(first_line):
            chapter = 2
        if args.subst and chapter > 2:
            ap.error("the substitution stepper needs Python §1 or §2; use --estep for §3 and §4")
        if args.tui:
            from .ui.terminal import start
            return start(source, filename, chapter, "substitution" if args.subst else "environment",
                         typed=args.typed, max_steps=args.max_steps)
        try:
            return serve(source, filename, chapter, "substitution" if args.subst else "environment",
                         port=args.port, open_browser=not args.no_browser, typed=args.typed, max_steps=args.max_steps)
        except OSError as exc:
            print(f"sicpfuf: could not start the UI: {exc}", file=sys.stderr)
            return 2

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
