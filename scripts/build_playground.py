"""MkDocs hook: publish the same UI as --ui, with browser Python as its backend."""

import json
from pathlib import Path
import shutil
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def on_post_build(config, **kwargs):
    # MkDocs restores sys.path after importing hook modules.
    sys.path.insert(0, str(ROOT))
    try:
        from sicpfuf.xray.playground import trace
    finally:
        sys.path.pop(0)

    target = Path(config["site_dir"]) / "assets/stepper"
    target.mkdir(parents=True, exist_ok=True)
    ui = ROOT / "sicpfuf/ui"
    page = (ui / "index.html").read_text()
    page = page.replace('href="/ui.css"', 'href="ui.css"')
    page = page.replace('<script src="/ui.js" defer></script>',
                        '<script src="website.js" defer></script>\n  <script src="ui.js" defer></script>')
    page = page.replace("Local session", "Browser session")
    page = page.replace('<div class="configuration">',
                        '<div class="configuration"><select id="example" aria-label="Example program"></select>')
    page = page.replace('<button id="run"', '<button id="stop" type="button" disabled>Stop</button><button id="run"')
    page = page.replace("Edits stay in this session. Your file is unchanged.",
                        "Code runs in your browser. First custom run downloads Python.")
    (target / "index.html").write_text(page)
    for filename in ("ui.css", "ui.js"):
        shutil.copyfile(ui / filename, target / filename)
    for filename in ("website.js", "worker.js"):
        shutil.copyfile(ROOT / "scripts/stepper" / filename, target / filename)

    with zipfile.ZipFile(target / "sicpfuf.zip", "w", zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted((ROOT / "sicpfuf").rglob("*.py")):
            bundle.write(path, path.relative_to(ROOT).as_posix())

    examples = json.loads((ui / "examples.json").read_text())
    examples.insert(0, {"id": "shadowing", "title": "Nested functions with the same name", "chapter": 2,
                        "source": "def add(a, b):\n    def add(c, d):\n        return c + d\n    return add(a, b)\n\nprint(add(5, 6))\n"})
    examples.append({"id": "typed", "title": "Python §4 Typed", "chapter": 4, "typed": True,
                     "source": "def square(x: int) -> int:\n    return x * x\n\nprint(square(3))\n"})
    for example in examples:
        example["trace"] = trace(example["source"], example["chapter"], example.get("mode", "environment"),
                                 typed=example.get("typed", False), max_steps=400)
        if example["trace"]["error"]:
            raise ValueError(example["title"] + ": " + example["trace"]["error"])
    (target / "examples.json").write_text(json.dumps(examples))


if __name__ == "__main__":
    on_post_build({"site_dir": sys.argv[1] if len(sys.argv) > 1 else ROOT / "site"})
