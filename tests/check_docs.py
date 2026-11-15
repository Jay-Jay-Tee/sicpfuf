#!/usr/bin/env python3
"""
Keeps the site (docs/**/*.md) honest: every program shown is RUN, and what the
page claims it prints must be what sicpfuf really prints.

A code block is run when its title names a chapter:

    ```python title="§2"                     run as Python §2
    ```python title="§1 · --subst"           ... with extra flags after the dot
    ```python title="§1 · figure quilt"      ... saving pictures as docs/assets/figures/quilt-rune-1.svg
    ```python title="§4 · --with examples/mce.py"   ... after loading that file (path from the project root)

What must it print? The NEXT code block, if that block is a `text` block and only
blank lines or one admonition header (??? / !!!) stand between them:

    ```text title="Output"       must equal everything the program prints (errors included)
    ```text                      (an "Answer" inside a toggle) must equal what the program prints,
                                 plus, if it stops with an error, the line  "SomeError: message"

A titled block with no text block after it must simply run without an error.
Blocks without a §-title are illustrations and are not run.

    python3 tests/check_docs.py              check every page
    python3 tests/check_docs.py --fill       (re)write the expected blocks and the figures
    python3 tests/check_docs.py docs/finals  check only some files or folders
    python3 tests/check_docs.py --oracle     also run every plain snippet in Source Academy's own
                                             implementation (py-slang) and compare what it prints
"""
import concurrent.futures
import glob
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIGURES = os.path.join(ROOT, "docs", "assets", "figures")
FENCE = re.compile(r"^(\s*)```(\w*)\s*(.*)$")
TITLE = re.compile(r'title="([^"]*)"')
CHAPTER = re.compile(r"§\s*([1-4])")
BETWEEN = re.compile(r"^\s*((\?\?\?\+?|!!!)\s.*)?$")
ERROR_LINE = re.compile(r"^(\w+Error|Error): ")


def blocks_of(lines):
    """Find the fenced code blocks: (indent, language, info, first line index, last line index)."""
    found, i = [], 0
    while i < len(lines):
        m = FENCE.match(lines[i])
        if m and (m.group(2) or m.group(3)):
            indent = m.group(1)
            j = i + 1
            while j < len(lines) and lines[j].strip() != "```":
                j += 1
            found.append((indent, m.group(2), m.group(3), i, j))
            i = j + 1
        else:
            i += 1
    return found


def body(lines, block):
    indent, _, _, start, end = block
    return "\n".join(l[len(indent):] if l.startswith(indent) else l.lstrip() for l in lines[start + 1:end]) + "\n"


def run_snippet(code, chapter, flags, figure):
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "snippet.py")
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)
        cmd = [sys.executable, "-m", "sicpfuf", path, "-v", str(chapter)] + flags
        out_dir = None
        if figure:
            out_dir = os.path.join(tmp, "figures")
            cmd += ["--out", out_dir, "--stem", figure]
        env = dict(os.environ, PYTHONHASHSEED="0", PYTHONPATH=ROOT)
        try:
            p = subprocess.run(cmd, cwd=tmp, env=env, capture_output=True, text=True, timeout=120)
            code_, out, err = p.returncode, p.stdout, p.stderr
        except subprocess.TimeoutExpired:
            code_, out, err = 124, "", "TIMEOUT: the snippet ran for more than 120 seconds\n"
        made = {}
        if out_dir and os.path.isdir(out_dir):
            for name in sorted(os.listdir(out_dir)):
                with open(os.path.join(out_dir, name), "rb") as f:
                    made[name] = f.read()
        return code_, out, err, made


ORACLE = os.environ.get("SICPFUF_ORACLE", os.path.expanduser("~/.cache/sicpfuf/py-slang/dist/repl.cjs"))
SICPFUF_ONLY = re.compile(r"\b(trace|measure|show_env|draw_data|input)\(|^\s*from\s+(rune|curve|sound|repeat)\s+import"
                          r"|random_random|time_time", re.M)


def run_oracle(code, chapter):
    """What py-slang prints for this program, and the first word of its error (if any)."""
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "snippet.py")
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)
        try:
            p = subprocess.run(["node", ORACLE, path, "-v", str(chapter)], capture_output=True, text=True, timeout=120)
        except subprocess.TimeoutExpired:
            return "", "TIMEOUT"
        return p.stdout, error_kind(p.stderr)


def error_kind(err):
    first = err.strip().split("\n")[0] if err.strip() else ""
    if first.startswith("Feature not supported"):
        return "Feature"
    if first.startswith("Error:"):
        return first
    if first.startswith("'break'") or first.startswith("'continue'"):
        return "SyntaxError"
    m = re.match(r"(\w+)", first)
    return m.group(1) if m else ""


def expected_text(out, err, full):
    if full:
        return out + err
    short = [l for l in err.split("\n") if ERROR_LINE.match(l)]
    return out + (short[0] + "\n" if short else "")


def plan(path):
    """What has to be run for one file: a list of jobs."""
    lines = open(path, encoding="utf-8").read().split("\n")
    found = blocks_of(lines)
    jobs = []
    for k, block in enumerate(found):
        indent, lang, info, start, end = block
        title = TITLE.search(info)
        if lang != "python" or not title or not CHAPTER.search(title.group(1)):
            continue
        chapter = int(CHAPTER.search(title.group(1)).group(1))
        extra = title.group(1).split("·", 1)[1].split() if "·" in title.group(1) else []
        figure = None
        if "--with" in extra:                       # a path given from the project root
            at = extra.index("--with")
            extra[at + 1] = os.path.join(ROOT, extra[at + 1])
        if "figure" in extra:
            at = extra.index("figure")
            figure = extra[at + 1]
            del extra[at:at + 2]
        expect = None
        if k + 1 < len(found) and found[k + 1][1] == "text":
            if all(BETWEEN.match(l) for l in lines[end + 1:found[k + 1][3]]):
                expect = found[k + 1]
        jobs.append({"path": path, "line": start + 1, "code": body(lines, block), "chapter": chapter,
                     "flags": extra, "figure": figure, "expect": expect})
    return lines, jobs


def main():
    fill = "--fill" in sys.argv
    oracle = "--oracle" in sys.argv
    targets = [a for a in sys.argv[1:] if not a.startswith("--")] or [os.path.join(ROOT, "docs")]
    files = []
    for t in targets:
        t = os.path.abspath(t)
        files += sorted(glob.glob(os.path.join(t, "**", "*.md"), recursive=True)) if os.path.isdir(t) else [t]
    problems = total = 0
    for path in files:
        lines, jobs = plan(path)
        if not jobs:
            continue
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda j: run_snippet(j["code"], j["chapter"], j["flags"], j["figure"]), jobs))
        changed = False
        for job, (code, out, err, made) in sorted(zip(jobs, results), key=lambda jr: -jr[0]["line"]):
            total += 1
            where = f"{os.path.relpath(path, ROOT)}:{job['line']}"
            for name, data in made.items():
                target = os.path.join(FIGURES, name)
                old = open(target, "rb").read() if os.path.exists(target) else None
                if old != data:
                    if fill:
                        os.makedirs(FIGURES, exist_ok=True)
                        open(target, "wb").write(data)
                    else:
                        problems += 1
                        print(f"--- FIGURE out of date: {name} (from {where}); run with --fill")
            if oracle and not job["flags"] and not job["figure"] and not SICPFUF_ONLY.search(job["code"]):
                want_out, want_err = run_oracle(job["code"], job["chapter"])
                got_err = error_kind(err)
                same_error = want_err == got_err or (want_err in ("SyntaxError", "Unexpected") and
                                                     got_err in ("SyntaxError", "IndentationError", "Feature"))
                if want_out != out or not same_error:
                    problems += 1
                    print(f"--- DIFFERENT FROM PY-SLANG at {where}:\n{job['code']}py-slang prints:\n{want_out}"
                          f"[{want_err}]\nsicpfuf prints:\n{out}[{got_err}]")
            if job["expect"] is None:
                if code != 0:
                    problems += 1
                    print(f"--- FAILED at {where} (no expected output is shown, so it must run cleanly):\n"
                          f"{job['code']}{out}{err}")
                continue
            indent, _, info, start, end = job["expect"]
            full = 'title="Output"' in info
            shown = body(lines, job["expect"])
            got = expected_text(out, err, full)
            got = got.rstrip("\n") + "\n" if got.strip("\n") else ""     # (trailing blank lines don't count)
            shown = shown.rstrip("\n") + "\n" if shown.strip("\n") else ""
            if got != shown:
                if fill:
                    lines[start + 1:end] = [(indent + l) if l else l for l in got.rstrip("\n").split("\n")] \
                        if got.strip("\n") else []
                    changed = True
                else:
                    problems += 1
                    print(f"--- MISMATCH at {where}:\n{job['code']}page shows:\n{shown}sicpfuf prints:\n{got}")
        if fill and changed:
            open(path, "w", encoding="utf-8").write("\n".join(lines))
    print(f"{total} doc snippets checked, {problems} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
