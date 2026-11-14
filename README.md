# sicpfuf

**SICP in Python, with x-ray vision.** An unofficial study companion for a first course on
*Structure and Interpretation of Computer Programs* taught in Python (the SICPy textbook and the
sublanguages **Python §1–§4**).

**Website: https://jay-jay-tee.github.io/sicpfuf/**

It has three parts:

- **A finals kit**: a topic checklist, one-page summary sheets, three original two-hour mock papers
  with machine-checked solutions, and an exam mode with a clock.
- **A book and drills** that follow the course in order: 20 chapters and 15 pages of practice problems.
- **An interpreter for Python §1–§4**, written in readable Python, with x-ray tools:

  | | |
  |---|---|
  | `--subst` | the substitution model, step by step (§1–§2) |
  | `--estep` | the environment model, step by step |
  | `show_env()`, `--env` | environment diagrams, as text and as pictures |
  | `draw_data(x)` | box-and-pointer diagrams, as text and as pictures |
  | `trace(f, ...)`, `measure(f, ...)` | call trees, time and space |
  | `--typed` | the type checker of Python §4 Typed |
  | `from rune / curve / sound import ...` | pictures (SVG) and sounds (WAV) |

## Try it

You need Python 3.9 or newer, nothing else.

    git clone https://github.com/Jay-Jay-Tee/sicpfuf.git
    cd sicpfuf
    python3 -m sicpfuf -v 2                          # interactive prompt, Python §2
    python3 -m sicpfuf examples/mce.py               # a metacircular evaluator
    python3 -m sicpfuf my_program.py -v 1 --subst    # watch the substitution model

## How it is checked

- `python3 tests/run_tests.py` runs hundreds of programs and compares what sicpfuf prints, and the
  errors it reports, with Source Academy's own implementation of the languages (py-slang).
- Every program on the website is run by `tests/check_docs.py`: the outputs you see are real.

## Not official

sicpfuf is a student-made companion. It is not affiliated with or endorsed by the authors of SICPy,
Source Academy or any university. All explanations, problems and mock papers are original. MIT licensed.
