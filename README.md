# sicpfuf

**SICP in Python, with x-ray vision.** An unofficial study companion for a first course on
*Structure and Interpretation of Computer Programs* taught in Python (the SICPy textbook and the
sublanguages **Python §1–§4**).

**Website: https://jay-jay-tee.github.io/sicpfuf/**

**[Online visual stepper](https://jay-jay-tee.github.io/sicpfuf/playground/)**: edit and run code
in your browser, with environment diagrams, substitution and Python §4 Typed.

The program includes a **terminal stepper**: `python3 -m sicpfuf --tui my_program.py`.
Keep editing in VS Code, then reload and step through the saved file below. An optional local
browser interface is available with `--ui`. Both use installed Python and work offline.

It has three parts:

- **A finals kit**: a topic checklist, one-page summary sheets, three original two-hour mock papers
  with machine-checked solutions, and an exam mode with a clock.
- **A book and drills**: 20 core chapters, an applied-patterns workshop, 15 practice pages,
  a lecture/studio/reflection map and routes through the supplied previous-year finals.
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
    python3 -m sicpfuf --ui my_program.py            # open the built-in visual UI
    python3 -m sicpfuf --ui --subst -v 1             # start with the substitution stepper
    python3 -m sicpfuf --tui my_program.py           # step inside the terminal
    python3 -m sicpfuf --tui my_program.py --typed   # Python §4 Typed in the terminal

`--tui` uses the terminal directly: arrows or n/p step, Space plays, r reloads the saved file,
1–4 changes chapter, Tab switches model, v switches Program/Frames, t toggles Typed in §4, and q quits. Press i to enter
program input; Ctrl-G saves that input and retraces. It needs curses support (included with the
macOS/Linux Python used here). It displays frames and bindings as terminal text, not SVG graphics.

`--ui` opens a local browser tab and prints its URL. Keep the terminal open; Ctrl-C stops it.
Use `--no-browser` to open the printed URL yourself, or `--port 8765` to choose a port.
The browser UI includes syntax colours, a current-frame binding inspector, diagram zoom,
and adjustable playback speed. Arrow keys step and Space plays when the editor is not focused.
In the E-stepper, **Program** shows the remaining code before and after each reduction;
**Diagram** shows frames, function objects and shared/cyclic lists.
Edits in the UI do not overwrite your file. Each run starts fresh and is bounded to 400 steps
(adjust with `--max-steps 1000`, up to 5000; press + in the terminal to increase and retrace),
15,000 interpreter operations, and 10 seconds. Python §4 Typed is available with `--typed` in
either interface, and with the Typed checkbox in the browser. Type errors prevent execution.
Expand **Program input** to supply one line per `input()` call. Rune previews keep colour in
terminals; redirected output stays plain. Set `NO_COLOR=1` to disable terminal colour.

## Read beside your code in VS Code

Open this folder in VS Code. In **Run and Debug**, choose **sicpfuf: Textbook beside code**
and start it. The book opens inside VS Code in a dedicated side editor group, which stays
separate from your code tabs. This uses VS Code's built-in integrated browser; no extension is needed.

Choose **sicpfuf: Visual stepper beside code** to start the local stepper in that pane too.
If you are already serving the docs with MkDocs, **sicpfuf: Local textbook (MkDocs running)**
opens the current local book instead of the published one. Stop the stepper server with
**Tasks: Terminate Task** when you finish.

For the terminal workflow, run **Tasks: Run Task → sicpfuf: Terminal stepper (current file)**
with your Python file active. **sicpfuf: Run current Python file** runs it through the course
interpreter rather than ordinary Python's Run File command.

The included editor declarations also let Pylance recognise sicpfuf's extra built-ins and
module imports. These provide name/signature hints; `sicpfuf --typed` remains the course-language
type checker. If VS Code retains an old “show_env is not defined” warning, reload the window.

## How it is checked

- `python3 tests/run_tests.py` runs hundreds of programs and compares what sicpfuf prints, and the
  errors it reports, with Source Academy's own implementation of the languages (py-slang).
- Every program on the website is run by `tests/check_docs.py`: the outputs you see are real.
- `python3 -m unittest discover -s tests -p 'test_*.py'` checks serialized stepper histories,
  closures, mutation, typed diagnostics, editor hints, errors and execution limits.
- `tests/test_ui.py` checks the local UI's API and CLI integration. `tests/ui.cjs` checks its
  controls and diagrams using jsdom. The UI itself needs no JavaScript packages.
- Website deployment waits for the interpreter and UI CI jobs, including the real Pyodide
  worker checks. To request a manual deployment, run the **tests** workflow on `main`.

## Not official

sicpfuf is a student-made companion. It is not affiliated with or endorsed by the authors of SICPy,
Source Academy or any university. All explanations, problems and mock papers are original. MIT licensed.
