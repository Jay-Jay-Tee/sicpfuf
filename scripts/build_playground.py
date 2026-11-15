"""MkDocs hook: ship the interpreter and instant, offline example traces."""

import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def on_post_build(config, **kwargs):
    # MkDocs restores sys.path after importing hook modules.
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from sicpfuf.xray.playground import trace

    assets = Path(config["site_dir"]) / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(assets / "sicpfuf.zip", "w", zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted((ROOT / "sicpfuf").rglob("*.py")):
            bundle.write(path, path.relative_to(ROOT).as_posix())
    examples = json.loads((ROOT / "docs/assets/playground-examples.json").read_text())
    for example in examples:
        example["trace"] = trace(example["source"], example["chapter"], example.get("mode", "environment"))
        if example["trace"]["error"]:
            raise ValueError(example["title"] + ": " + example["trace"]["error"])
    (assets / "playground-traces.json").write_text(json.dumps(examples))


if __name__ == "__main__":
    on_post_build({"site_dir": sys.argv[1] if len(sys.argv) > 1 else ROOT / "site"})
