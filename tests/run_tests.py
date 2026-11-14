#!/usr/bin/env python3
"""
sicpfuf test runner.

  tests/cases/*.cases    many small programs per file. Each starts with a line
                             #### name (§N)
                         and is run as Python §N. What sicpfuf prints, and the kind
                         and line of the error it stops with, must equal the entry
                         in tests/expected.json. Those entries were recorded from
                         Source Academy's own implementation (py-slang), so this is
                         a DIFFERENTIAL test: two implementations, one answer.

  tests/xray/*.py        programs that use sicpfuf-only tools (first line: # args: ...).
                         Output must match the .expected file next to them.

  examples/*.py          must run without an error (with --oracle: and print what py-slang prints).

  docs/**/*.md           every code block in the book and the finals kit is run
                         (tests/check_docs.py).

    python3 tests/run_tests.py                    check everything
    python3 tests/run_tests.py --oracle           compare live against py-slang (needs node + a build)
    python3 tests/run_tests.py --update           re-record expected.json from py-slang, and the xray files
"""
import difflib
import glob
import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SICPFUF = [sys.executable, "-m", "sicpfuf"]
ORACLE = os.environ.get("SICPFUF_ORACLE", os.path.expanduser("~/.cache/sicpfuf/py-slang/dist/repl.cjs"))
EXPECTED = os.path.join(ROOT, "tests", "expected.json")
HEADER = re.compile(r"^#### (.+?) \(§([1-4])\)( noline)?\s*$")
SYNTAX = ("SyntaxError", "IndentationError", "Unexpected", "ScopeConflictError")


def run(cmd, cwd=ROOT, timeout=120):
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return 124, "", "TIMEOUT"
    return p.returncode, p.stdout, p.stderr


def signature(stderr):
    """Boil an error report down to 'Kind@line' so two implementations can be compared."""
    lines = [l for l in stderr.strip().split("\n") if l.strip()]
    if not lines:
        return ""
    first = lines[0].strip()
    if first.startswith(SYNTAX) or "outside loop" in first or "not properly in loop" in first:
        return "SyntaxError"
    m = re.match(r"Feature not supported in this sublanguage: (.*) \(line (\d+), col \d+\)", first)
    if m:
        return f"Feature: {m.group(1)}@{m.group(2)}"
    m = re.match(r"(\w+) at line (\d+)", first)
    if m:
        return f"{m.group(1)}@{m.group(2)}"
    if first.startswith("Error:"):
        return first
    m = re.match(r"(\w+Error)\b", first)
    if m:
        return m.group(1)
    return first[:60]


def load_cases():
    cases = []
    for path in sorted(glob.glob(os.path.join(ROOT, "tests", "cases", "*.cases"))):
        group = os.path.basename(path)[:-6]
        name, chapter, body, noline = None, None, [], False
        for line in open(path, encoding="utf-8").read().split("\n") + ["#### END (§1)"]:
            m = HEADER.match(line)
            if m:
                if name is not None:
                    cases.append((f"{group}/{name}", chapter, "\n".join(body).strip("\n") + "\n", noline))
                name, chapter, body, noline = m.group(1), int(m.group(2)), [], bool(m.group(3))
            elif name is not None:
                body.append(line)
    return cases


def run_case(cmd_prefix, chapter, code):
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(code)
        path = f.name
    try:
        _, out, err = run(cmd_prefix + [path, "-v", str(chapter)])
    finally:
        os.unlink(path)
    return {"stdout": out, "error": signature(err)}


def same(a, b, noline=False):
    if a["stdout"] != b["stdout"]:
        return False
    ea, eb = a["error"], b["error"]
    if noline:            # (py-slang reports a line of its own library here; sicpfuf reports your line)
        return ea.split("@")[0] == eb.split("@")[0]
    if ea == eb:
        return True
    # a line number is only compared when BOTH sides report one
    return "@" in ea and "@" not in eb and ea.split("@")[0] == eb or \
           "@" in eb and "@" not in ea and eb.split("@")[0] == ea


def show_diff(expected, got):
    out = "".join(difflib.unified_diff(expected["stdout"].splitlines(True), got["stdout"].splitlines(True),
                                       "py-slang", "sicpfuf"))
    if expected["error"] != got["error"]:
        out += f"  error: py-slang {expected['error']!r}   sicpfuf {got['error']!r}\n"
    return out


def main():
    update = "--update" in sys.argv
    live = "--oracle" in sys.argv or update
    only = [a for a in sys.argv[1:] if not a.startswith("--")]
    passed = failed = 0
    cases = load_cases()
    expected = json.load(open(EXPECTED, encoding="utf-8")) if os.path.exists(EXPECTED) else {}
    if live and not os.path.exists(ORACLE):
        print(f"no py-slang build at {ORACLE} (set SICPFUF_ORACLE)")
        return 2

    for name, chapter, code, noline in cases:
        if only and not any(o in name for o in only):
            continue
        if live:
            want = run_case(["node", ORACLE], chapter, code)
            if update:
                expected[name] = want
        else:
            want = expected.get(name)
        got = run_case(SICPFUF, chapter, code)
        if want is None:
            failed += 1
            print(f"FAIL  {name}: no expected result recorded (run with --update)")
        elif same(want, got, noline):
            passed += 1
        else:
            failed += 1
            print(f"FAIL  {name} (§{chapter})\n{code.rstrip()}\n{show_diff(want, got)}")
    if update:
        keep = {case[0] for case in cases}
        expected = {k: v for k, v in sorted(expected.items()) if k in keep}
        json.dump(expected, open(EXPECTED, "w", encoding="utf-8"), indent=1, ensure_ascii=False, sort_keys=True)
    print(f"differential cases: {passed} same as py-slang, {failed} different")

    if not only:
        for path in sorted(glob.glob(os.path.join(ROOT, "tests", "xray", "*.py"))):
            name = os.path.relpath(path, ROOT)
            first = open(path, encoding="utf-8").readline()
            extra = first[len("# args:"):].split() if first.startswith("# args:") else []
            _, out, err = run(SICPFUF + [name] + extra)
            got = out + ("--- stderr ---\n" + err if err else "")
            exp_path = path[:-3] + ".expected"
            if update or not os.path.exists(exp_path):
                open(exp_path, "w", encoding="utf-8").write(got)
                print(f"wrote {os.path.relpath(exp_path, ROOT)}")
                continue
            if got == open(exp_path, encoding="utf-8").read():
                passed += 1
            else:
                failed += 1
                print(f"FAIL  {name}")
                print("".join(difflib.unified_diff(open(exp_path, encoding="utf-8").read().splitlines(True),
                                                   got.splitlines(True), "expected", "got")))
        for path in sorted(glob.glob(os.path.join(ROOT, "examples", "*.py"))):
            name = os.path.relpath(path, ROOT)
            code, out, err = run(SICPFUF + [name])          # (each file says `# chapter N` on line 1)
            text = open(path, encoding="utf-8").read()
            if code != 0:
                failed += 1
                print(f"FAIL  {name}\n{err}")
            elif live and "# sicpfuf-only" not in text:
                chapter = re.match(r"#\s*chapter\s*([1-4])", text)
                _, want, _ = run(["node", ORACLE, path, "-v", chapter.group(1) if chapter else "4"])
                if want == out:
                    passed += 1
                else:
                    failed += 1
                    print(f"FAIL  {name}: output differs from py-slang\n"
                          + "".join(difflib.unified_diff(want.splitlines(True), out.splitlines(True),
                                                         "py-slang", "sicpfuf")))
            else:
                passed += 1
        checker = os.path.join(ROOT, "tests", "check_docs.py")
        if os.path.exists(checker):
            code, out, err = run([sys.executable, checker], timeout=1800)
            print(out.strip().split("\n")[-1] if out.strip() else err.strip())
            if code == 0:
                passed += 1
            else:
                failed += 1
                print(out + err)

    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
