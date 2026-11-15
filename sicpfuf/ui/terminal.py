"""A small curses front end: edit in VS Code, reload and step in its terminal."""

from pathlib import Path
import sys
import textwrap
import time

from . import DEFAULT_SOURCE, DEFAULT_TYPED_SOURCE, run_trace


def model_lines(step, mode, error=None, view='frames'):
    lines = []
    if step:
        if mode == "substitution":
            lines.extend(["EXPRESSION", step.get("expression") or "Step forward to begin."])
        elif view == 'program':
            lines.extend(['REMAINING PROGRAM', step.get('program') or 'Step forward to begin.'])
        else:
            for frame in sorted(step["frames"], key=lambda frame: (not frame["current"], not frame.get("reachable", True))):
                lines.append(frame["id"] + ("  [current]" if frame["current"] else
                             "  [unreachable]" if not frame.get("reachable", True) else
                             "  [waiting]" if frame.get("on_stack") else ""))
                lines.append("  " + frame["call"])
                lines.append("  enclosing -> " + frame["parent"])
                lines.extend("  " + b["name"] + " = " + (b['objectId'] + ('' if b.get('function') else ' ' + b['value'])
                             if b.get('objectId') else b['value']) for b in frame["bindings"])
                lines.append("")
            if step["functions"]:
                lines.append("FUNCTION OBJECTS")
                for fn in step["functions"]:
                    lines.append(fn.get('objectId', fn['id']) + "(" + ", ".join(fn["params"]) + ") -> " + fn["env"] +
                                 ("  [unreachable]" if not fn.get("reachable", True) else ""))
                    lines.append("  " + fn["source"])
        lines.extend(["", "OUTPUT", step["output"] or "No output yet."])
    if error:
        lines.extend(["", "ERROR", error])
    return "\n".join(lines).splitlines()


def source_rows(source, active, width, height):
    rows, focus = [], 0
    for number, line in enumerate(source.splitlines(), 1):
        if number == active:
            focus = len(rows)
        chunks = textwrap.wrap(line.expandtabs(4), max(1, width - 4),
                               replace_whitespace=False, drop_whitespace=False) or [""]
        rows.extend((number, (f"{number:>3} " if i == 0 else "    ") + chunk)
                    for i, chunk in enumerate(chunks))
    top = max(0, min(focus - height // 3, len(rows) - height))
    return rows[top:top + height]


def start(source=None, filename=None, chapter=2, mode="environment", typed=False, max_steps=400):
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        print("sicpfuf: --tui needs an interactive terminal; use --ui for the browser interface.", file=sys.stderr)
        return 2
    try:
        import curses
    except ImportError:
        print("sicpfuf: this Python has no curses support; use --ui instead.", file=sys.stderr)
        return 2

    def run(screen):
        nonlocal source, chapter, mode, typed, max_steps
        source = (DEFAULT_TYPED_SOURCE if typed else DEFAULT_SOURCE) if source is None else source
        index, offset, playing, last_tick = 0, 0, False, 0.0
        program_view = False
        program_input = ""
        status = ""
        try:
            curses.curs_set(0)
        except curses.error:
            pass
        screen.timeout(100)
        screen.keypad(True)

        def put(row, col, text, width, style=0):
            try:
                screen.addnstr(row, col, text, max(0, width), style)
            except curses.error:
                pass  # resizing or the bottom-right cell must not close the stepper

        def reload_trace(read_file=False):
            nonlocal source, index, offset, playing, status
            if read_file and filename and not filename.startswith("<"):
                try:
                    source = Path(filename).read_text(encoding="utf-8")
                except OSError as exc:
                    status = "Could not reload: " + str(exc)
                    return None
            playing, index, offset, status = False, 0, 0, ""
            screen.erase()
            put(1, 2, "Tracing locally…", max(1, screen.getmaxyx()[1] - 4))
            screen.refresh()
            result = run_trace(source, chapter, mode, stdin=program_input, typed=typed,
                               graphics=False, max_steps=max_steps)
            if result["error"]:
                index = max(0, len(result["steps"]) - 1)
            return result

        history = reload_trace()
        while True:
            height, width = screen.getmaxyx()
            screen.erase()
            if height < 12 or width < 64:
                put(0, 0, "Enlarge the terminal to at least 64 columns and 12 rows. q quits.", width - 1)
            else:
                steps = history["steps"] if history else []
                step = steps[index] if steps else None
                divider, body_height = max(25, width * 2 // 5), height - 8
                title = f"sicpfuf | {'E-stepper' if mode == 'environment' else 'Substitution'} | Python §{chapter}{' Typed' if typed else ''} | {filename or 'Example'}"
                put(0, 1, title, width - 2, curses.A_BOLD)
                put(2, 1, "CODE", divider - 2, curses.A_BOLD)
                put(2, divider + 2, f"MODEL  {index + 1 if steps else 0}/{len(steps)}", width - divider - 3, curses.A_BOLD)
                active = step["line"] if step else 0
                for row, (line, text) in enumerate(source_rows(source, active, divider - 2, body_height)):
                    put(row + 3, 1, text, divider - 2,
                        curses.A_REVERSE if line == active else 0)
                for row in range(2, height - 4):
                    put(row, divider, "|", 1, curses.A_DIM)
                right_width = max(1, width - divider - 4)
                rows = []
                for text in model_lines(step, mode, history.get("error") if history else None,
                                        view='program' if program_view else 'frames'):
                    rows.extend(textwrap.wrap(text, right_width, replace_whitespace=False) or [""])
                offset = min(offset, max(0, len(rows) - body_height))
                for row, text in enumerate(rows[offset:offset + body_height]):
                    put(row + 3, divider + 2, text, right_width,
                        curses.A_DIM if "[unreachable]" in text else
                        curses.A_BOLD if "[current]" in text or text in ("ERROR", "EXPRESSION", "OUTPUT") else 0)
                error = history.get("error") if history else None
                limit = error and "Trace stopped at" in error
                message = (f"TRACE LIMIT {max_steps}: press + to increase and retrace" if limit else
                           error.splitlines()[0] if error else step["message"] if step else "No steps recorded.")
                put(height - 4, 1, status or message, width - 2, curses.A_BOLD if error else 0)
                put(height - 2, 1, "←/p Back  →/n Next  Space Play  r Reload  ↑↓ Scroll  q Quit", width - 2, curses.A_REVERSE)
                put(height - 1, 1, "1–4 Chapter  Tab Model  v Program/Frames  t Typed  i Input  + More steps  Home/End Jump", width - 2, curses.A_DIM)
            screen.refresh()
            key = screen.getch()
            count = len(history["steps"]) if history else 0
            previous = index
            if key in (ord("q"), 27):
                return 0
            elif key in (curses.KEY_RIGHT, ord("n")) and count:
                playing, index = False, min(count - 1, index + 1)
            elif key in (curses.KEY_LEFT, ord("p")) and count:
                playing, index = False, max(0, index - 1)
            elif key == curses.KEY_HOME:
                playing, index = False, 0
            elif key == curses.KEY_END and count:
                playing, index = False, count - 1
            elif key == ord(" ") and count > 1:
                playing = not playing
                if playing and index == count - 1:
                    index = 0
                last_tick = time.monotonic()
            elif key == curses.KEY_DOWN:
                offset += 1
            elif key == curses.KEY_UP:
                offset = max(0, offset - 1)
            elif key == ord("r"):
                history = reload_trace(read_file=True) or history
            elif key == ord("+"):
                max_steps = min(5000, max_steps * 2)
                history = reload_trace()
            elif key == ord('v'):
                program_view, offset = not program_view, 0
            elif key == ord("i") and height >= 12 and width >= 64:
                from curses.textpad import Textbox
                playing = False
                screen.erase()
                put(1, 2, "Program input: one line per input() call. Ctrl-G saves and retraces.", width - 4)
                screen.refresh()
                entry = curses.newwin(height - 5, width - 4, 3, 2)
                try:
                    entry.addstr(program_input[:(height - 6) * (width - 5)])
                    curses.curs_set(1)
                except curses.error:
                    pass
                text = Textbox(entry).edit()
                program_input = text.rstrip("\n") + "\n" if text.strip() else ""
                try:
                    curses.curs_set(0)
                except curses.error:
                    pass
                history = reload_trace()
            elif key in (ord("1"), ord("2"), ord("3"), ord("4")):
                chapter = int(chr(key))
                typed = typed and chapter == 4
                if chapter > 2:
                    mode = "environment"
                history = reload_trace()
            elif key == ord("\t"):
                if chapter > 2 or typed:
                    status = "Substitution needs Python §1 or §2. Press 1 or 2 first."
                else:
                    mode = "substitution" if mode == "environment" else "environment"
                    history = reload_trace()
            elif key == ord("t"):
                if chapter != 4:
                    status = "Typed checking needs Python §4. Press 4 first."
                else:
                    typed, mode = not typed, "environment"
                    history = reload_trace()
            if playing and count and time.monotonic() - last_tick >= .9:
                index = min(count - 1, index + 1)
                playing = index < count - 1
                last_tick = time.monotonic()
            if previous != index:
                offset, status = 0, ""

    try:
        return curses.wrapper(run)
    except KeyboardInterrupt:
        return 130
    except curses.error as exc:
        print("sicpfuf: could not open the terminal UI: " + str(exc), file=sys.stderr)
        return 2
