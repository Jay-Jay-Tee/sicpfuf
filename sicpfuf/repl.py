"""
sicpfuf/repl.py — the interactive prompt (Read → Eval → Print → Loop).

    python3 -m sicpfuf -v 2

    §2> llist(1, 2, 3)
    [1, [2, [3, None]]]
    §2> :env                     the environment diagram so far
    §2> :draw llist(1, 2)        box-and-pointer diagram of any expression
    §2> :ast x = 1 + 2 * 3       the syntax tree of any code
    §2> :tokens if x: pass       the tokens of any code

Unlike a program file, the prompt SHOWS the value of an expression you type
(a program file needs print for that).
"""

import sys

from . import nodes as N
from .chapters import check_program
from .errors import SicpSyntaxError, SicpError
from .interpreter import Interpreter
from .lexer import Lexer, tokenize, format_tokens
from .parser import parse
from .values import to_repr

HELP = """sicpfuf prompt commands:
  :env           draw the environment diagram
  :draw EXPR     draw the box-and-pointer diagram of EXPR
  :tokens CODE   show how CODE is split into tokens
  :ast CODE      show the syntax tree of CODE
  :steps         how much work has been done so far
  :help          this text
  :quit          leave (or Ctrl-D)
Blocks (def, if, while, for): keep typing; finish with an empty line."""


def needs_more(lines):
    text = "\n".join(lines)
    if lines[0].rstrip().endswith(":"):
        return lines[-1].strip() != "" if len(lines) > 1 else True
    try:
        lx = Lexer(text)
        lx.tokenize()
        return lx.depth > 0                       # an open ( or [ → keep reading
    except SicpSyntaxError as e:
        return "unterminated" in e.msg and ('"""' in text or "'''" in text)


def repl(chapter=4):
    from .__main__ import run_with_big_stack, format_error
    try:
        import readline  # noqa: F401  (gives arrow-key history)
    except ImportError:
        pass
    interp = Interpreter(chapter)
    env = interp.program_env
    print(f"sicpfuf 1.0, Python §{chapter}.  :help for commands, Ctrl-D to quit.")
    while True:
        try:
            lines = [input(f"§{chapter}> ")]
            while needs_more(lines):
                lines.append(input("...> "))
        except EOFError:
            print()
            return 0
        except KeyboardInterrupt:
            print("\nKeyboardInterrupt")
            continue
        text = "\n".join(lines).rstrip()
        if not text.strip():
            continue
        cmd, _, rest = text.partition(" ")
        if text.startswith(":") and cmd != ":draw":
            try:
                if cmd in (":q", ":quit", ":exit"):
                    return 0
                elif cmd == ":help":
                    print(HELP)
                elif cmd == ":tokens":
                    print(format_tokens(tokenize(rest, "<repl>")))
                elif cmd == ":ast":
                    print(N.format_ast(parse(rest, "<repl>")))
                elif cmd == ":steps":
                    print(f"{interp.steps:,} steps, {interp.calls:,} function calls, "
                          f"at most {interp.max_seen:,} calls waiting at once")
                elif cmd == ":env":
                    from .xray import envdiagram
                    envdiagram.show(interp)
                else:
                    print(f"unknown command {cmd}. Try :help")
            except SicpSyntaxError as e:
                print(format_error(interp, e, "<repl>"), file=sys.stderr)
            continue
        if cmd == ":draw":
            text = f"draw_data({rest})" if chapter >= 2 else rest

        def run_entry():
            interp.sources["<repl>"] = text.split("\n")
            tree = parse(text, "<repl>")
            known = interp.lib.names(interp) | set(env.vars)
            check_program(tree, chapter, known, interp.lib.module_exports(), "<repl>")
            body = tree.body
            if body and isinstance(body[-1], N.ExprStmt):
                interp.exec_block(body[:-1], env)
                value = interp.eval(body[-1].value, env)
                if value is not None and cmd != ":draw":
                    print(to_repr(value))
            else:
                interp.exec_block(body, env)

        try:
            run_with_big_stack(run_entry)
        except KeyboardInterrupt:
            print("\nKeyboardInterrupt")
        except (SicpSyntaxError, SicpError, RecursionError) as e:
            sys.stdout.flush()
            print(format_error(interp, e, "<repl>"), file=sys.stderr)
        finally:
            del interp.frames[:], interp.envs[:]
            interp.depth = 0
