"""Bounded, immutable histories of the environment reduction machine."""
from ..errors import SicpError, SicpSyntaxError, format_syntax_error, format_runtime_error
from ..values import Closure
from .envdiagram import Snapshot, frame_name, fn_name
from .reduction import Machine, ProgramSerializer, StoreSerializer
from . import svg


def program_text(node, indent=0):
    """Render protocol terms as Python, with explicit environment blocks."""
    if node is None:
        return ''
    kind = node['type']
    text = lambda child: program_text(child, indent)
    pad = '    ' * indent
    body = lambda statements: '\n'.join(program_text(statement, indent) for statement in statements)
    suite = lambda block: '\n'.join(program_text(statement, indent + 1)
                                    for statement in block['body']) or '    ' * (indent + 1) + 'pass'
    if kind in ('Program', 'BlockStatement'):
        return body(node['body'])
    if kind in ('Identifier', 'Builtin'):
        return node['name']
    if kind == 'Literal':
        return node['raw']
    if kind == 'Ref':
        return node['objectId']
    if kind in ('BinaryExpression', 'LogicalExpression'):
        return '(' + text(node['left']) + ' ' + node['operator'] + ' ' + text(node['right']) + ')'
    if kind == 'UnaryExpression':
        return '(' + node['operator'] + text(node['argument']) + ')'
    if kind == 'ConditionalExpression':
        return '(' + text(node['consequent']) + ' if ' + text(node['test']) + ' else ' + text(node['alternate']) + ')'
    if kind == 'ArrowFunctionExpression':
        return '(lambda ' + ', '.join(text(param) for param in node['params']) + ': ' + text(node['body']) + ')'
    if kind == 'CallExpression':
        return text(node['callee']) + '(' + ', '.join(text(arg) for arg in node['arguments']) + ')'
    if kind == 'SpreadElement':
        return '*' + text(node['argument'])
    if kind == 'ArrayExpression':
        return '[' + ', '.join(text(arg) for arg in node['elements']) + ']'
    if kind == 'MemberExpression':
        return text(node['object']) + '[' + text(node['property']) + ']'
    if kind == 'EnvBlock':
        return node['envId'] + ' ⟦\n' + suite({'body': node['body']}) + '\n' + pad + '⟧'
    if kind == 'VariableDeclaration':
        return pad + '; '.join(text(declaration['id']) + ' = ' + text(declaration['init'])
                               for declaration in node['declarations'])
    if kind == 'AssignmentStatement':
        return pad + text(node['target']) + ' = ' + text(node['value'])
    if kind == 'FunctionDeclaration':
        return pad + 'def ' + text(node['id']) + '(' + ', '.join(text(param) for param in node['params']) + '):\n' + suite(node['body'])
    if kind == 'ExpressionStatement':
        return pad + text(node['expression'])
    if kind == 'ReturnStatement':
        return pad + 'return' + (' ' + text(node['argument']) if node['argument'] is not None else '')
    if kind == 'IfStatement':
        return pad + 'if ' + text(node['test']) + ':\n' + suite(node['consequent']) + (
            '\n' + pad + 'else:\n' + suite(node['alternate']) if node['alternate'] else '')
    if kind == 'WhileStatement':
        return pad + 'while ' + text(node['test']) + ':\n' + suite(node['body'])
    if kind == 'ForStatement':
        return pad + 'for ' + text(node['target']) + ' in ' + text(node['iter']) + ':\n' + suite(node['body'])
    if kind == 'LoopIteration':
        return body(node['statements'])
    if kind in ('GlobalStatement', 'NonlocalStatement'):
        return pad + ('global ' if kind == 'GlobalStatement' else 'nonlocal ') + node['names']
    if kind == 'ImportDeclaration':
        return pad + 'from ' + node['source'] + ' import ' + ', '.join(
            specifier['imported'] + (' as ' + specifier['local'] if specifier['local'] != specifier['imported'] else '')
            for specifier in node['specifiers'])
    return pad + {'PassStatement': 'pass', 'BreakStatement': 'break', 'ContinueStatement': 'continue'}.get(kind, '<' + kind + '>')


def capture(machine, message, phase, line, graphics):
    ast = ProgramSerializer(machine).program()
    store = StoreSerializer(machine)
    state = store.snapshot()
    interp = machine.interp
    live_frame_names = {frame['id'] for frame in state['frames'] if not frame['isGarbage']}
    live_frames = {key for key, env in store.frames.items()
                   if ('Global' if env.kind == 'program' else frame_name(env)) in live_frame_names}
    live_functions = {item['id'] for item in state['heap'] if item['kind'] == 'function' and not item['isGarbage']}
    active = next(env for env in store.frames.values()
                  if ('Global' if env.kind == 'program' else frame_name(env)) == state['activeFrameId'])
    snapshot = Snapshot(interp, active)
    snapshot.frames = dict(store.frames)
    snapshot.functions = {value.serial: value for value in store.objects.values() if type(value) is Closure}
    snapshot.stack = store.stack
    snapshot.unreachable_frames = set(snapshot.frames) - live_frames
    snapshot.unreachable_functions = {serial for serial, value in snapshot.functions.items()
                                      if machine.object_id(value) not in live_functions}
    frames = []
    for env in sorted(snapshot.frames.values(), key=lambda env: env.serial):
        if id(env) not in live_frames and id(env) in machine.frame_views:
            frames.append(machine.frame_views[id(env)])
            continue
        machine.frame_views.pop(id(env), None)
        names = list(env.vars)
        if env.scope is not None:
            names += sorted(env.scope.local_names - env.vars.keys())
        bindings = []
        for name in names:
            value = env.vars.get(name)
            function = fn_name(value) if type(value) is Closure and not value.prelude else None
            reference = type(value) is list or (type(value) is Closure and not value.prelude)
            text = (snapshot.list_text(value) if type(value) is list else snapshot.value_text(value))
            bindings.append({'name': name, 'value': text if name in env.vars else '(unassigned)',
                             'function': function, 'objectId': machine.object_id(value) if reference else None})
        frames.append({'id': frame_name(env), 'parent': frame_name(env.parent),
                       'call': env.name + '(' + ', '.join(env.args or []) + ')' if env.kind == 'function' else 'Whole program',
                       'current': env is active, 'reachable': id(env) in live_frames,
                       'on_stack': env in store.stack, 'bindings': bindings})
        if id(env) not in live_frames and not any(type(value) is list for value in env.vars.values()):
            machine.frame_views[id(env)] = frames[-1]
    def function_source(function):
        if function.serial not in machine.function_sources:
            machine.function_sources[function.serial] = program_text(ProgramSerializer(machine).node(function.node))
        return machine.function_sources[function.serial]
    functions = [{'id': fn_name(function), 'objectId': machine.object_id(function), 'params': function.params + (['*' + function.vararg] if function.vararg else []),
                  'line': function.node.line, 'source': function_source(function),
                  'env': frame_name(function.env), 'reachable': function.serial not in snapshot.unreachable_functions}
                 for function in sorted(snapshot.functions.values(), key=lambda function: function.serial)]
    calls = {('Global' if frame['id'] == 'global env' else frame['id']): frame['call'] for frame in frames}
    function_info = {machine.object_id(value): next(function for function in functions if function['id'] == fn_name(value))
                     for value in store.objects.values() if type(value) is Closure}
    return {'message': message, 'line': line, 'phase': phase, 'program': program_text(ast) or 'Program finished.',
            'ast': ast, 'store': state, 'frames': frames, 'functions': functions, 'data': [],
            'diagram': svg.reduction_environment(state, calls, function_info) if graphics else None, 'output': state['output']}


def trace(source, chapter=3, typed=False, graphics=True, max_steps=250):
    history, error, machine = [], None, None
    history_objects = 0
    cached, cached_revision = None, None

    def record(message, phase='boundary', line=0):
        nonlocal history_objects, cached, cached_revision
        if len(history) >= max_steps:
            raise Limit(f'Trace stopped at {max_steps} steps. Increase --max-steps to see more.')
        if cached is not None and cached_revision == machine.revision:
            # A before-state has the same program/store as the preceding
            # after-state. Reuse immutable payloads rather than drawing twice.
            state = dict(cached, message=message, phase=phase, line=line)
            state.pop('focus', None)
        else:
            state = capture(machine, message, phase, line, graphics)
            cached, cached_revision = state, machine.revision
        history_objects += len(state['frames']) + len(state['store']['heap'])
        if history_objects > 250000:
            raise Limit('Trace stopped: diagram history is too large. Try a smaller input.')
        history.append(state)

    try:
        machine = Machine(source, chapter, typed)
        record('Ready. Step forward to start the program.')
        while True:
            action = machine.step()
            if action is None:
                break
            record('Before ' + action.rule, 'beforeMarker', action.node.line)
            before = history[-1]
            if len(history) >= max_steps:
                raise Limit(f'Trace stopped at {max_steps} steps. Increase --max-steps to see more.')
            action.apply()
            record(action.explanation, 'afterMarker', action.node.line)
            after = history[-1]
            old, new = before['program'], after['program']
            start = end = 0
            while start < min(len(old), len(new)) and old[start] == new[start]:
                start += 1
            while end < min(len(old), len(new)) - start and old[-end - 1] == new[-end - 1]:
                end += 1
            before['focus'] = [start, len(old) - end]
            after['focus'] = [start, len(new) - end]
        record('Program finished.')
    except (SicpError, SicpSyntaxError) as exc:
        lines = source.splitlines()
        error = (exc.report(lines) if hasattr(exc, 'report') else
                 format_syntax_error(exc, lines) if isinstance(exc, SicpSyntaxError)
                 else format_runtime_error(exc, lines))
        if len(history) < max_steps:
            try:
                if machine is None:
                    machine = Machine('', chapter)
                    record('Program was not run: ' + str(exc), line=exc.line or 0)
                    history[-1]['program'] = 'Program was not run.'
                else:
                    record('Program stopped: ' + str(exc), line=exc.line or 0)
            except (Limit, RecursionError):
                pass  # preserve the original program error when history is full
    except (Limit, RecursionError) as exc:
        error = str(exc)
    return {'steps': history, 'error': error}


class Limit(Exception):
    pass
