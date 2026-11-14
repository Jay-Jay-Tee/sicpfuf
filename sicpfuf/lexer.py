"""
sicpfuf/lexer.py — turns source TEXT into a list of TOKENS.

    "x = 10 + y"   →   NAME('x')  OP('=')  NUMBER(10)  OP('+')  NAME('y')  NEWLINE

SYLLABUS LESSONS IN THIS FILE
  * Strings & string manipulation  — we walk the source one character at a time,
                                      slice substrings, handle escape sequences.
  * Stacks                          — INDENT/DEDENT tokens come from an *indent stack*.
                                      This is exactly how CPython's own tokenizer does it.
  * Dictionaries / sets             — keyword and operator tables are O(1) lookups.
  * Classes (dataclass)             — each Token is a tiny object.

Compare with real Python:   python3 -m tokenize yourfile.py
and with sicpfuf:           python3 -m sicpfuf --tokens yourfile.py

(This file is shared with pfuf, sicpfuf's sibling project. It tokenizes ALL of
Python's surface syntax; chapters.py later decides what each chapter §1-§4 allows.)
"""

from dataclasses import dataclass

from .errors import SicpSyntaxError


# --------------------------------------------------------------------------
# Token kinds
# --------------------------------------------------------------------------
NAME, NUMBER, STRING, FSTRING, OP, KEYWORD = "NAME", "NUMBER", "STRING", "FSTRING", "OP", "KEYWORD"
NEWLINE, INDENT, DEDENT, EOF = "NEWLINE", "INDENT", "DEDENT", "EOF"

# A *set* gives O(1) membership tests: "is this word a keyword?"
KEYWORDS = {
    "False", "None", "True", "and", "as", "assert", "break", "class", "continue",
    "def", "del", "elif", "else", "except", "finally", "for", "from", "global",
    "if", "import", "in", "is", "lambda", "nonlocal", "not", "or", "pass",
    "raise", "return", "try", "while", "with", "yield",
}

# Operators, longest first, so "**=" wins over "**" which wins over "*".
OPERATORS = sorted([
    "**=", "//=", ">>=", "<<=",
    "**", "//", "==", "!=", "<=", ">=", "->", "+=", "-=", "*=", "/=", "%=",
    "&=", "|=", "^=", "<<", ">>",
    "+", "-", "*", "/", "%", "<", ">", "=", "(", ")", "[", "]", "{", "}",
    ",", ":", ".", ";", "@", "&", "|", "^", "~",
], key=len, reverse=True)

OPENERS, CLOSERS = "([{", ")]}"

ESCAPES = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\", "'": "'", '"': '"',
           "0": "\0", "a": "\a", "b": "\b", "f": "\f", "v": "\v", "\n": ""}


@dataclass
class Token:
    type: str       # one of the kinds above
    value: object   # 'x', 10, '+', ...
    line: int
    col: int

    def __repr__(self):
        return f"{self.type}({self.value!r})@{self.line}:{self.col}"


class Lexer:
    def __init__(self, source, filename="<sicpfuf>", line_offset=0):
        # Normalise Windows line endings and make sure the text ends in "\n".
        self.src = source.replace("\r\n", "\n")
        if not self.src.endswith("\n"):
            self.src += "\n"
        self.filename = filename
        self.pos = 0
        self.line = 1 + line_offset
        self.col = 1
        self.tokens = []
        self.indent_stack = [0]   # <- THE STACK. Bottom is always column 0.
        self.depth = 0            # how many ( [ { are open; newlines inside are ignored
        self.at_line_start = True

    # ---------------- small helpers ----------------
    def peek(self, k=0):
        i = self.pos + k
        return self.src[i] if i < len(self.src) else ""

    def advance(self):
        ch = self.src[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def error(self, msg, line=None):
        raise SicpSyntaxError(msg, self.filename, line or self.line, self.col)

    def add(self, type_, value, line, col):
        self.tokens.append(Token(type_, value, line, col))

    # ---------------- main loop ----------------
    def tokenize(self):
        while self.pos < len(self.src):
            if self.at_line_start and self.depth == 0:
                self.handle_indentation()
                if self.at_line_start:      # it was a blank/comment line: measure the NEXT line
                    continue
            ch = self.peek()

            if ch == "\n":
                line, col = self.line, self.col
                self.advance()
                # Inside brackets a newline is just whitespace (lets you split long lists).
                if self.depth == 0:
                    self.add(NEWLINE, "\\n", line, col)
                    self.at_line_start = True
            elif ch in " \t":
                self.advance()
            elif ch == "#":                       # comment: skip to end of line
                while self.peek() not in ("\n", ""):
                    self.advance()
            elif ch == "\\" and self.peek(1) == "\n":   # explicit line continuation
                self.advance(); self.advance()
            elif ch.isdigit() or (ch == "." and self.peek(1).isdigit()):
                self.read_number()
            elif ch.isalpha() or ch == "_":
                self.read_name_or_string_prefix()
            elif ch in "'\"":
                self.read_string(prefix="")
            else:
                self.read_operator()

        # End of file: close the last line, then pop every open indentation level.
        if self.tokens and self.tokens[-1].type not in (NEWLINE, INDENT, DEDENT):
            self.add(NEWLINE, "\\n", self.line, self.col)
        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            self.add(DEDENT, "", self.line, 1)
        self.add(EOF, "", self.line, 1)
        return self.tokens

    # ---------------- indentation: the stack lesson ----------------
    def handle_indentation(self):
        """Called at the start of every physical line (outside brackets).

        Measure how far the line is indented, then compare with the TOP of the stack:
            deeper   → push it, emit INDENT
            same     → nothing
            shallower→ pop until equal, emit one DEDENT per pop
                       (if we never hit an equal level → IndentationError)
        """
        width = 0
        while True:
            ch = self.peek()
            if ch == " ":
                width += 1
            elif ch == "\t":
                width = (width // 8 + 1) * 8   # tabs jump to the next multiple of 8, like Python
            else:
                break
            self.advance()

        ch = self.peek()
        if ch in ("\n", "#", ""):      # blank or comment-only line: indentation doesn't matter
            if ch == "#":
                while self.peek() not in ("\n", ""):
                    self.advance()
            if ch == "\n":
                self.advance()
            return                     # still at_line_start for the next line

        self.at_line_start = False
        top = self.indent_stack[-1]
        if width > top:
            self.indent_stack.append(width)
            self.add(INDENT, width, self.line, 1)
        elif width < top:
            while width < self.indent_stack[-1]:
                self.indent_stack.pop()
                self.add(DEDENT, width, self.line, 1)
            if width != self.indent_stack[-1]:
                raise SicpSyntaxError("unindent does not match any outer indentation level",
                                      self.filename, self.line, 1, kind="IndentationError")

    # ---------------- numbers ----------------
    def read_number(self):
        line, col, start = self.line, self.col, self.pos
        if self.peek() == "0" and self.peek(1) in "xXbBoO" and self.peek(1):
            base = {"x": 16, "b": 2, "o": 8}[self.peek(1).lower()]
            self.advance(); self.advance()
            while self.peek().isalnum() or self.peek() == "_":
                self.advance()
            text = self.src[start:self.pos].replace("_", "")
            try:
                self.add(NUMBER, int(text, base), line, col)
            except ValueError:
                self.error(f"invalid number literal {text!r}")
            return
        is_float = False
        while self.peek().isdigit() or self.peek() == "_":
            self.advance()
        if self.peek() == "." and (self.peek(1).isdigit() or not self.peek(1).isalpha()):
            is_float = True
            self.advance()
            while self.peek().isdigit() or self.peek() == "_":
                self.advance()
        if self.peek() in ("e", "E") and (self.peek(1).isdigit() or
                                         (self.peek(1) in "+-" and self.peek(2).isdigit())):
            is_float = True
            self.advance()
            if self.peek() in "+-":
                self.advance()
            while self.peek().isdigit():
                self.advance()
        text = self.src[start:self.pos].replace("_", "")
        if self.peek() in ("j", "J"):          # 2j, 1.5j → an imaginary (complex) number
            self.advance()
            self.add(NUMBER, complex(0, float(text)), line, col)
            return
        self.add(NUMBER, float(text) if is_float else int(text), line, col)

    # ---------------- names, keywords, prefixed strings ----------------
    def read_name_or_string_prefix(self):
        line, col, start = self.line, self.col, self.pos
        while self.peek().isalnum() or self.peek() == "_":
            self.advance()
        word = self.src[start:self.pos]
        # f"...", r'...', b'...', rf"...", rb'...'  → string with a prefix
        if self.peek() in "'\"" and word.lower() in ("f", "r", "rf", "fr", "b", "rb", "br"):
            self.read_string(prefix=word.lower(), line=line, col=col)
            return
        self.add(KEYWORD if word in KEYWORDS else NAME, word, line, col)

    # ---------------- strings ----------------
    def read_string(self, prefix, line=None, col=None):
        line = line or self.line
        col = col or self.col
        quote = self.peek()
        triple = self.peek(1) == quote and self.peek(2) == quote
        delim = quote * 3 if triple else quote
        for _ in delim:
            self.advance()
        raw = "r" in prefix
        chars = []
        while True:
            if self.pos >= len(self.src):
                self.error("unterminated string literal", line)
            if self.src.startswith(delim, self.pos):
                for _ in delim:
                    self.advance()
                break
            ch = self.peek()
            if ch == "\n" and not triple:
                self.error("unterminated string literal (strings can't span lines; use \"\"\" for that)", line)
            if ch == "\\" and not raw:
                self.advance()
                esc = self.advance()
                if esc in ESCAPES:
                    chars.append(ESCAPES[esc])
                elif esc == "x":
                    chars.append(chr(int(self.advance() + self.advance(), 16)))
                elif esc == "u":
                    chars.append(chr(int("".join(self.advance() for _ in range(4)), 16)))
                else:                          # unknown escape: keep the backslash (Python does too)
                    chars.append("\\" + esc)
            elif ch == "\\" and raw:
                chars.append(self.advance())
                if self.peek():
                    chars.append(self.advance())
            else:
                chars.append(self.advance())
        text = "".join(chars)
        if "b" in prefix:                      # bytes literal: b"abc" → the bytes 97 98 99
            try:
                self.add(STRING, text.encode("latin-1"), line, col)
            except UnicodeEncodeError:
                self.error("bytes can only contain ASCII literal characters", line)
            return
        # f-strings keep their raw text; the PARSER splits out the {expressions}.
        self.add(FSTRING if "f" in prefix else STRING, text, line, col)

    # ---------------- operators & brackets ----------------
    def read_operator(self):
        line, col = self.line, self.col
        for op in OPERATORS:
            if self.src.startswith(op, self.pos):
                for _ in op:
                    self.advance()
                if op in OPENERS:
                    self.depth += 1
                elif op in CLOSERS:
                    self.depth = max(0, self.depth - 1)
                self.add(OP, op, line, col)
                return
        self.error(f"invalid character {self.peek()!r}")


def tokenize(source, filename="<sicpfuf>", line_offset=0):
    return Lexer(source, filename, line_offset).tokenize()


def format_tokens(tokens):
    """Pretty table used by `python3 -m sicpfuf --tokens file.py`."""
    out, indent_level = [], 0
    for t in tokens:
        if t.type == DEDENT:
            indent_level -= 1
        shown = "" if t.type in (NEWLINE, INDENT, DEDENT, EOF) else repr(t.value)
        out.append(f"{t.line:>4}:{t.col:<4} {'  ' * indent_level}{t.type:<8} {shown}")
        if t.type == INDENT:
            indent_level += 1
    return "\n".join(out)
