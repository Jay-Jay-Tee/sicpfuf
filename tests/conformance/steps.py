"""Compare remaining programs and retained stores at every reference reduction.

Presentation-only node IDs and tooltips are omitted. Bindings are maps, so their
display order is immaterial. Source strings are presentation, while graph
identity, parent links, bindings, heap values and reachability are compared.
"""
import gzip
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from sicpfuf.xray.reduction import Machine, ProgramSerializer, StoreSerializer


def semantic(value):
    if isinstance(value, dict):
        result = {key: semantic(item) for key, item in value.items()
                  if key not in ('nodeId', 'hoverText')
                  and not (key == 'source' and value.get('kind') == 'function')}
        if 'bindings' in result:
            result['bindings'].sort(key=lambda binding: binding['name'])
        if 'frames' in result:
            result['frames'].sort(key=lambda frame: frame['id'])
        if 'heap' in result:
            result['heap'].sort(key=lambda item: int(item['id'][1:]))
        return result
    if isinstance(value, list):
        return [semantic(item) for item in value]
    return value


def difference(left, right, path='state'):
    if type(left) is not type(right):
        return f'{path}: {left!r} != {right!r}'[:500]
    if isinstance(left, dict):
        if left.keys() != right.keys():
            return f'{path}: different keys {set(left) ^ set(right)}'
        for key in left:
            result = difference(left[key], right[key], path + '.' + key)
            if result:
                return result
    elif isinstance(left, list):
        if len(left) != len(right):
            return f'{path}: lengths {len(left)} != {len(right)}'
        for index, (a, b) in enumerate(zip(left, right)):
            result = difference(a, b, f'{path}[{index}]')
            if result:
                return result
    elif left != right:
        return f'{path}: {left!r} != {right!r}'[:500]


def states(entry):
    machine = Machine(entry['source'], entry['chapter'])
    serializer = ProgramSerializer(machine)
    def state(phase):
        program = serializer.program()
        return dict(StoreSerializer(machine).snapshot(), ast=program, phase=phase)
    result = [state('boundary')]
    while True:
        action = machine.step()
        if action is None:
            break
        if len(result) >= 999:
            raise RuntimeError('conformance program exceeded 1000 states')
        result.append(state('beforeMarker'))
        action.apply()
        result.append(state('afterMarker'))
    result.append(state('boundary'))
    return result


def check(entry, ignore_active_frame=False):
    try:
        actual = states(entry)
    except Exception as exc:
        return f'{type(exc).__name__}: {exc}'
    # The upstream transport sends a dead object once; its frontend carries it
    # forward. Reconstruct that history before comparing retained diagrams.
    expected, frames, heap = [], {}, {}
    for step in entry['expected']['steps']:
        frames.update((frame['id'], frame) for frame in step.get('frames', []))
        heap.update((item['id'], item) for item in step.get('heap', []))
        snapshot = {key: value for key, value in step.items() if key not in ('explanation', 'lookups')}
        snapshot.update(frames=list(frames.values()), heap=list(heap.values()))
        expected.append(snapshot)
    if ignore_active_frame:
        for snapshot in actual + expected:
            snapshot.pop('activeFrameId', None)
    return difference(semantic(actual), semantic(expected))


if __name__ == '__main__':
    path = Path(sys.argv[1])
    data = json.loads(gzip.decompress(path.read_bytes()) if path.suffix == '.gz' else path.read_text())
    entries = [entry for entry in data['cases'] if entry.get('stepper') == 'environment' and not entry['expected']['error']]
    problems = [(entry['id'], check(entry)) for entry in entries]
    problems = [(name, message) for name, message in problems if message]
    for name, message in problems:
        print(name, message)
    print(f'{len(entries) - len(problems)}/{len(entries)} environment histories match every program and retained store')
    raise SystemExit(bool(problems))
