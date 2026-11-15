"""Compare oracle outcomes with the interpreter, retaining every discrepancy."""
import io
import gzip
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from sicpfuf.interpreter import Interpreter
from sicpfuf.errors import SicpError, SicpSyntaxError


def error_kind(text, category=None):
    first = (text or '').strip().split('\n', 1)[0]
    if first.startswith('Feature not supported'):
        return 'FeatureNotSupportedError'
    if first.startswith(("'break' outside loop", "'continue' not properly in loop")):
        return 'SyntaxError'
    if category == 'parse':
        return 'SyntaxError'
    names = re.findall(r'\b((?:[A-Za-z]+)?Error)\b', text or '')
    return names[0] if names else ('Error' if text else None)


def actual(entry):
    output = io.StringIO()
    interp = Interpreter(entry['chapter'], out=output)
    error = None
    try:
        interp.run_source(entry['source'])
    except (SicpError, SicpSyntaxError) as exc:
        error = error_kind(exc.kind) if exc.kind.startswith('Feature not supported') else exc.kind
    except Exception as exc:
        error = 'INTERNAL:' + type(exc).__name__ + ': ' + str(exc)
    return {'output': output.getvalue(), 'error': error}


def main():
    path = Path(sys.argv[1])
    data = json.loads(gzip.decompress(path.read_bytes()) if path.suffix == '.gz' else path.read_text())
    mismatches = []
    prediction_mismatches = []
    for entry in data['cases']:
        wanted = {'output': entry['expected']['output'], 'error': error_kind(entry['expected']['error'], entry['expected'].get('category'))}
        got = actual(entry)
        if entry.get('prediction') is not None and entry['prediction'] != wanted['output']:
            prediction_mismatches.append({'id': entry['id'], 'predicted': entry['prediction'],
                                          'oracle': wanted})
        if wanted != got:
            mismatches.append({'id': entry['id'], 'source': entry['source'], 'chapter': entry['chapter'],
                               'expected': wanted, 'actual': got,
                               'oracle_error': entry['expected']['error']})
    report = {'upstream': data['upstream'], 'checked': len(data['cases']),
              'matched': len(data['cases']) - len(mismatches), 'mismatches': mismatches,
              'prediction_mismatches': prediction_mismatches}
    Path(sys.argv[2]).write_text(json.dumps(report, indent=2))
    print(f"{report['matched']}/{report['checked']} matched; {len(mismatches)} discrepancies")
    for row in mismatches[:15]:
        print(row['id'], row['expected'], row['actual'])
    for row in prediction_mismatches:
        print('PREDICTION', row)
    return bool(mismatches or prediction_mismatches)


if __name__ == '__main__':
    raise SystemExit(main())
