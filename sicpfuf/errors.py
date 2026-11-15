"""
sicpfuf/errors.py — turning failures into messages a human can learn from.

Every error sicpfuf prints starts with the same first line as Source Academy's
Python (py-slang) would print:

    TypeError at line 3              <- WHAT kind of error, and WHERE
        return a + "s"               <- the offending line
    TypeError: can't use + between an int and a str        <- what went wrong
      called from line 5: print(f(1))                      <- how we got there
    sicpfuf hint: ...                <- the usual cause, in plain words

There are two families:

  * SicpSyntaxError — found BEFORE the program runs (by the lexer, the parser,
    or the chapter checker in chapters.py). Nothing has been printed yet.
  * SicpError       — happens WHILE the program runs. Everything printed before
    the error stays printed.
"""

import difflib


class SicpSyntaxError(Exception):
    """Raised before the program runs. `kind` is the name shown on the first line."""

    def __init__(self, msg, filename="<sicpfuf>", line=0, col=1, kind="SyntaxError", hint=None):
        super().__init__(msg)
        self.msg, self.filename, self.line, self.col, self.kind, self.hint = msg, filename, line, col, kind, hint


class SicpError(Exception):
    """Raised while the program runs. `kind` is e.g. 'TypeError', 'ZeroDivisionError'."""

    def __init__(self, kind, msg, line=None, hint=None):
        super().__init__(msg)
        self.kind, self.msg, self.line, self.hint = kind, msg, line, hint
        self.calls = None           # filled in by the interpreter: [(function name, call line), ...]
        self.in_library = False     # did it happen inside a library function such as map?


class UserError(SicpError):
    """Raised by the program itself, by calling error(...)."""

    def __init__(self, text, line=None):
        super().__init__("Error", text, line)


def suggest(name, candidates):
    """'did you mean ...?' — difflib finds the closest spelling."""
    close = difflib.get_close_matches(name, [c for c in candidates if not c.startswith("_")], n=1, cutoff=0.7)
    return close[0] if close else None


def source_line(lines, n):
    if lines and n and 0 < n <= len(lines):
        return lines[n - 1]
    return None


def format_syntax_error(err, lines):
    if err.kind == "Missing type annotation":          # Python §4 Typed (xray/typecheck.py)
        out = [f"Missing type annotation: {err.msg} (line {err.line}, col {err.col})"]
        last = f"MissingTypeAnnotationError: {err.msg}"
    elif err.kind.startswith("Feature not supported"):
        out = [f"{err.kind} (line {err.line}, col {err.col})"]
        last = f"FeatureNotSupportedError: {err.msg}"
    else:
        out = [f"{err.kind} at line {err.line}"]
        last = f"{err.kind}: {err.msg}"
    text = source_line(lines, err.line)
    if text is not None:
        stripped = text.lstrip()
        out.append("    " + stripped.rstrip())
        if err.col and err.col > 0:
            caret = max(0, err.col - 1 - (len(text) - len(stripped)))
            out.append("    " + " " * caret + "^")
    out.append(last)
    hint = err.hint or syntax_hint(err)
    if hint:
        out.append(f"sicpfuf hint: {hint}")
    return "\n".join(out)


def syntax_hint(err):
    m = err.msg
    if err.kind == "IndentationError" or "indent" in m:
        return ("Python uses indentation to group statements. Every line of a block must start at "
                "exactly the same column. Use 4 spaces, and never mix tabs and spaces.")
    if "expected ':'" in m:
        return "if / elif / else / while / for / def lines must end with a colon ':'"
    if "'=='" in m or "cannot assign" in m:
        return "to COMPARE use '==' ; a single '=' means 'give this name a value'."
    if "unterminated string" in m:
        return "every string needs a closing quote of the same kind it started with."
    if "never closed" in m or "unmatched" in m:
        return "count your brackets: every ( [ needs a matching ) ]."
    return None


def format_runtime_error(err, lines):
    if isinstance(err, UserError):                 # error("...") prints just its message
        out = [f"Error: {err.msg}".rstrip()]
        if err.line:
            out.append(f"  (error(...) was called at line {err.line})")
        return "\n".join(out)
    out = [f"{err.kind} at line {err.line}" if err.line else err.kind]
    text = source_line(lines, err.line)
    if text is not None:
        out.append("    " + text.strip())
    out.append(f"{err.kind}: {err.msg}")
    # the calls that were waiting, innermost first; runs of the same call are folded into one line
    groups = []
    for entry in reversed(err.calls or []):
        if not entry[1]:                      # a call made from inside the library: not your code
            continue
        if groups and groups[-1][0] == entry:
            groups[-1][1] += 1
        else:
            groups.append([entry, 1])
    for (name, line), count in groups[:6]:
        text = source_line(lines, line)
        where = f": {text.strip()}" if text is not None else ""
        times = f"  (x{count})" if count > 1 else ""
        out.append(f"  in {name}, called from line {line}{where}{times}")
    if len(groups) > 6:
        out.append(f"  ... and {len(groups) - 6} more ...")
    hint = err.hint or runtime_hint(err.kind, err.msg)
    if hint:
        out.append(f"sicpfuf hint: {hint}")
    return "\n".join(out)


def runtime_hint(kind, msg):
    """Pattern-match common error messages to an explanation."""
    if kind == "RecursionError":
        return ("more than 1024 calls were waiting for an answer at the same time. Either the BASE CASE is "
                "never reached, or the function is a deep RECURSIVE PROCESS (it has deferred operations). "
                "A tail call (`return f(...)` with nothing left to do afterwards) does not pile up: "
                "rewrite it as an ITERATIVE process with an accumulator.")
    if kind == "UnassignedLocalError":
        return ("the function assigns to this name somewhere in its body, so the name lives in the function's "
                "own frame for the WHOLE body, even on lines before the assignment. To change a name of an "
                "enclosing function use `nonlocal`, and for a global name use `global` (Python §3 and §4).")
    if kind == "NameError":
        return ("the name is declared in your program, but the line that gives it a value has not run yet. "
                "Statements run from top to bottom.")
    if kind == "ZeroDivisionError":
        return "check the divisor before dividing, for example with a base case `if n == 0`."
    if kind == "IndexError":
        return "a list with n items has indexes 0 .. n-1 (and -1 .. -n counting from the end)."
    if kind == "TypeError":
        if "condition" in msg or "'not'" in msg or "'and'" in msg or "'or'" in msg:
            return ("Python §1-§4 are stricter than full Python: a condition must be exactly True or False. "
                    "Write the comparison out, for example `if n != 0:` or `if not is_none(xs):`.")
        if "head" in msg or "tail" in msg:
            if "None" in msg:
                return ("you took the head or tail of None, the EMPTY linked list. The usual cause is a "
                        "missing base case: check `is_none(xs)` before `head(xs)` / `tail(xs)`.")
            return "head and tail only work on a pair. Check with is_pair(x) what you really have."
        if "==" in msg or "!=" in msg:
            return ("in Python §1 and §2, == and != don't accept booleans or functions. Use the boolean itself "
                    "(`if done:` instead of `if done == True:`), or `not done`.")
        if "NoneType" in msg or "None" in msg:
            return ("a value is None where you need something else. Usually a function forgot to `return` "
                    "(then it returns None), or you went past the end of a linked list.")
        if "str" in msg and ("+" in msg or "*" in msg):
            return "numbers and strings don't mix in §1-§4. Convert with str(n) first, and there is no \"ab\" * 3."
        if "bool" in msg:
            return "True and False are not numbers in §1-§4: no arithmetic on booleans."
        if "argument" in msg:
            return "count the arguments in the call and the parameters in the `def`: they must match exactly."
        if "not callable" in msg or "not a function" in msg:
            return "you put () after something that isn't a function. Did a name get a non-function value?"
    return None
