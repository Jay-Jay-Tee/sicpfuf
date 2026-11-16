"""Start or reuse the local textbook, signalling readiness to VS Code."""
import argparse
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import ProxyHandler, build_opener

ROOT = Path(__file__).resolve().parents[1]
HTTP = build_opener(ProxyHandler({}))


def ready(url):
    try:
        with HTTP.open(url, timeout=0.4) as response:
            return response.status == 200 and b'sicpfuf' in response.read(100000).lower()
    except (OSError, URLError):
        return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error('--port must be between 1 and 65535')
    url = 'http://127.0.0.1:%d/sicpfuf/book/' % args.port
    print('sicpfuf textbook: starting', flush=True)
    if ready(url):
        print('sicpfuf textbook: ready ' + url, flush=True)
        return 0

    candidates = [ROOT / '.venv/bin/mkdocs',
                  Path.home() / '.cache/sicpfuf/venv/bin/mkdocs']
    executable = next((str(path) for path in candidates if path.is_file()), None)
    executable = executable or shutil.which('mkdocs')
    command = [executable] if executable else [sys.executable, '-m', 'mkdocs']
    child = subprocess.Popen(command + ['serve', '--dev-addr', '127.0.0.1:%d' % args.port], cwd=str(ROOT))
    try:
        deadline = time.monotonic() + 40
        while child.poll() is None:
            if ready(url):
                print('sicpfuf textbook: ready ' + url, flush=True)
                return child.wait()
            if time.monotonic() >= deadline:
                print('Textbook server did not become ready. See the MkDocs output above.', file=sys.stderr)
                return 1
            time.sleep(0.15)
        return child.returncode
    except KeyboardInterrupt:
        return 130
    finally:
        if child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=3)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()


if __name__ == '__main__':
    def stop(signum, frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, stop)
    sys.exit(main())
