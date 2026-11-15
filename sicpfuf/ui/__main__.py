"""Private subprocess entry point for an isolated trace."""

import json
import sys

from ..xray.playground import trace


def main():
    if sys.argv[1:] != ["--trace"]:
        print("Launch the stepper with python3 -m sicpfuf --ui", file=sys.stderr)
        return 2
    data = json.load(sys.stdin)
    result = trace(data["source"], data["chapter"], data["mode"])
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
