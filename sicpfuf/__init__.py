"""sicpfuf: Python §1-§4 (the language of SICPy) with x-ray vision.

A small interpreter, written in readable Python, for the four sublanguages of
Python used with "Structure and Interpretation of Computer Programs" (SICPy).
Read the files in this order:

    lexer.py → parser.py (+ nodes.py, scopes.py) → chapters.py → env.py →
    values.py → interpreter.py → lib/ → xray/ → modules/
"""

__version__ = "1.0.0"


def run(source, chapter=4, filename="<sicpfuf>"):
    """Run a program from Python:  import sicpfuf; sicpfuf.run('print(1 + 1)', chapter=1)"""
    from .interpreter import Interpreter
    return Interpreter(chapter).run_source(source, filename)
