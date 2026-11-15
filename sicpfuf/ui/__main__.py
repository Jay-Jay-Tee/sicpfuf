"""Private subprocess entry point for an isolated trace."""

import json
import io
import sys

from ..xray.playground import trace


def main():
    if sys.argv[1:] != ["--trace"]:
        print("Launch the stepper with python3 -m sicpfuf --ui", file=sys.stderr)
        return 2
    data = json.load(sys.stdin)
    sys.stdin = io.StringIO(data.get("stdin", ""))
    result = trace(data["source"], data["chapter"], data["mode"], typed=data.get("typed", False),
                   graphics=data.get("graphics", True), max_steps=data.get("max_steps", 250))
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
