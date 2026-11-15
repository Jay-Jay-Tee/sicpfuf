"""Small-step environment reduction, independently implementing the published rules.

A contraction changes the remaining program and its store once. The driver can
record the state immediately before and after that change. The ordinary
interpreter supplies primitive operations and atomic library applications.
"""
import copy
from dataclasses import dataclass
import io

from .. import nodes as N
from ..errors import SicpError
from ..interpreter import Interpreter
from ..values import Builtin, Closure, type_name, show_atom
from .envdiagram import frame_name, real_frame


class Value(N.Expr):
    def __init__(self, value, source=None):
        self.value = value
        self.line = source.line if source is not None else 0
        self.builtin_name = None


class Block(N.Expr):
    def __init__(self, env, body, source=None):
        self.env, self.body = env, body
        self.line = source.line if source is not None else 0
        self.globals = sorted(env.scope.global_names) if env.scope is not None else []


class Loop(N.Stmt):
    def __init__(self, body, again, source, condition=None):
        self.body, self.again, self.condition = body, again, condition
        self.line = source.line


class RangeFor(N.Stmt):
    def __init__(self, source, current, stop, step):
        self.source = source
        self.current, self.stop, self.step = current, stop, step
        self.line = source.line


@dataclass
class Contraction:
    node: object
    env: object
    rule: str
    change: object
    explanation: str = ''

    def apply(self):
        try:
            self.explanation = self.change()
        except (TypeError, ValueError, ZeroDivisionError, OverflowError, IndexError) as exc:
            raise SicpError(type(exc).__name__, str(exc), self.node.line) from None


class StoreInterpreter(Interpreter):
    """Runtime primitives, with a registry that never becomes a reachability root."""
    def __init__(self, chapter, typed=False):
        self.objects = {}
        self.created_frames = {}
        self.hidden_frames = {}
        self.operations = 0
        self.atomic = False
        super().__init__(chapter, out=io.StringIO(), max_depth=80, typed=typed)
        self.diagrams = True
        self.created_frames[id(self.program_env)] = self.program_env
        self._eval[Value] = lambda node, env: node.value

    def make_closure(self, node, env, name, is_lambda):
        function = super().make_closure(node, env, name, is_lambda)
        if not function.prelude and not self.atomic:
            self.objects[id(function)] = function
        return function

    def new_frame(self, *args, **kwargs):
        previous_count = self.frame_count
        env = super().new_frame(*args, **kwargs)
        function = args[0]
        if function.is_lambda:
            env.name = 'lambda'
        if self.atomic:
            self.frame_count = previous_count
            env.serial = 0
            if not function.prelude:
                self.hidden_frames[id(env)] = env
        elif not function.prelude and env.serial:
            self.created_frames[id(env)] = env
        return env

    def eval(self, node, env):
        self.operations += 1
        if self.operations > 15000:
            raise SicpError('RuntimeError', 'Execution stopped after 15,000 operations.', node.line)
        return super().eval(node, env)

    def exec(self, node, env):
        self.operations += 1
        if self.operations > 15000:
            raise SicpError('RuntimeError', 'Execution stopped after 15,000 operations.', node.line)
        return super().exec(node, env)

    def write(self, text):
        if self.out.tell() + len(text) > 16000:
            raise SicpError('RuntimeError', 'Output stopped at 16,000 characters.')
        self.out.write(text)


def val(node):
    return isinstance(node, (Value, N.Constant))


def unwrap(node):
    return node.value


def ref(env):
    name = frame_name(env)
    return 'the global environment' if name == 'global env' else name



class Machine:
    def __init__(self, source, chapter=3, typed=False):
        self.source = source
        self.interp = StoreInterpreter(chapter, typed)
        self.tree = self.interp.load_source(source, typecheck=typed)
        self.normalize(self.tree)
        self.program = self.tree.body
        self.after_redex = None
        self.object_ids = {}
        self.revision = 0
        self.dead_frame_records = {}
        self.function_sources = {}
        self.frame_views = {}

    def normalize(self, node):
        """Erase type-only declarations and make boolean association explicit."""
        if isinstance(node, list):
            node[:] = [item for item in node if not isinstance(item, N.TypeAlias)]
            for item in node:
                self.normalize(item)
        elif isinstance(node, N.Node):
            for child in list(vars(node).values()):
                if isinstance(child, (list, N.Node)):
                    self.normalize(child)
            if isinstance(node, N.BoolOp) and len(node.values) > 2:
                prefix = N.BoolOp(node.op, node.values[:-1])
                prefix.line, prefix.col = node.line, node.col
                self.normalize(prefix)
                node.values = [prefix, node.values[-1]]

    def object_id(self, value):
        key = id(value)
        if key not in self.object_ids:
            self.object_ids[key] = '#' + str(len(self.object_ids) + 1)
        self.interp.objects[key] = value
        return self.object_ids[key]

    def show(self, value):
        if type(value) is Closure and not value.prelude:
            return self.object_id(value)
        return show_atom(value)

    def lookup_frame(self, env, name, line):
        current = env
        while current is not None:
            if name in current.vars:
                return current
            scope = current.scope
            if scope is not None:
                if name in scope.local_names:
                    env.lookup(name, line)  # raises the proper local/free-variable error
                if name in scope.global_names:
                    current = current.program
                    continue
            current = current.parent
        env.lookup(name, line)

    def action(self, node, env, rule, change):
        def contract():
            self.after_redex = None
            try:
                explanation = change()
            finally:
                # A failing builtin may already have printed a prompt/output.
                self.revision += 1
            if val(self.after_redex) and self.after_redex.value is None:
                self.discard_void(self.program, self.after_redex)
            return explanation
        return Contraction(node, env, rule, contract)

    def discard_void(self, node, result):
        if isinstance(node, list):
            node[:] = [item for item in node if not (isinstance(item, N.ExprStmt) and item.value is result)]
            for item in node:
                self.discard_void(item, result)
        elif isinstance(node, (N.Node, Block)) and not isinstance(node, (Value, N.FunctionDef, N.Lambda)):
            for child in vars(node).values():
                if isinstance(child, (list, N.Node)):
                    self.discard_void(child, result)

    def replace_value(self, replace, value, source):
        replacement = Value(value, source)
        replace(replacement)
        self.after_redex = replacement
        if type(value) is list:
            self.interp.objects[id(value)] = value
        return self.show(value)

    def expression(self, node, env, replace, tail=None):
        if val(node):
            return None
        if isinstance(node, Block):
            return self.block(node, replace)
        if isinstance(node, N.Name):
            found = self.lookup_frame(env, node.id, node.line)
            value = env.lookup(node.id, node.line)
            if found.kind in ('builtins', 'library'):
                replacement = Value(value, node)
                replacement.builtin_name = node.id
                replace(replacement)
                return None
            def lookup():
                self.replace_value(replace, value, node)
                where = 'the global frame' if found.kind == 'program' else 'frame ' + frame_name(found)
                return f'Looked up {node.id} in {where}: {self.show(value)}'
            return self.action(node, env, 'lookup', lookup)
        if isinstance(node, N.Lambda):
            def allocate():
                function = self.interp.make_closure(node, env, '(anonymous)', True)
                self.replace_value(replace, function, node)
                return f'Created a function object {self.object_id(function)} in {ref(env)}'
            return self.action(node, env, 'lambda', allocate)
        if isinstance(node, N.IfExp):
            action = self.child(node, 'test', env)
            if action:
                return action
            def choose():
                condition = unwrap(node.test)
                if type(condition) is not bool:
                    raise self.interp.not_a_bool('conditional expression', condition, node)
                replacement = node.body if condition else node.orelse
                replace(replacement)
                self.after_redex = replacement
                return f'Evaluated conditional expression: condition is {condition}'
            return self.action(node, env, 'conditional', choose)
        if isinstance(node, N.BoolOp):
            action = self.item(node.values, 0, env)
            if action:
                return action
            left = unwrap(node.values[0])
            def logical(value):
                self.replace_value(replace, value, node)
                return f'Evaluated {node.op}: {value}'
            if type(left) is not bool:
                return self.action(node, env, 'logical', lambda: self.boolean_error(node, left))
            if (node.op == 'and' and not left) or (node.op == 'or' and left):
                return self.action(node, env, 'short-circuit', lambda: logical(left))
            def choose_right():
                replacement = node.values[1]
                replace(replacement)
                self.after_redex = replacement
                return f'Evaluated {node.op}: continue with the right operand'
            return self.action(node, env, 'logical', choose_right)
        if isinstance(node, N.Call):
            action = self.child(node, 'func', env)
            if action:
                return action
            for i, argument in enumerate(node.args):
                if isinstance(argument, N.Starred):
                    action = self.child(argument, 'value', env)
                else:
                    action = self.item(node.args, i, env)
                if action:
                    return action
            def application():
                function = unwrap(node.func)
                args = []
                for argument in node.args:
                    if isinstance(argument, N.Starred):
                        values = unwrap(argument.value)
                        if type(values) is not list:
                            raise SicpError('TypeError', 'spread argument must be a list', argument.line)
                        args.extend(values)
                    else:
                        args.append(unwrap(argument))
                if type(function) is Closure and not function.prelude:
                    call_env = self.interp.new_frame(function, args, node)
                    if function.is_lambda:
                        statement = N.Return(copy.deepcopy(function.node.body))
                        statement.line = function.node.line
                        body = [statement]
                    else:
                        body = copy.deepcopy(function.node.body)
                    body, global_names = self.declarations(body)
                    replacement = Block(call_env, body, node)
                    replacement.globals = global_names
                    target = tail[1] if tail else replace
                    target(replacement)
                    self.after_redex = replacement
                    arguments = ', '.join(self.show(value) for value in args)
                    return f'{"Tail call" if tail else "Called"} {function.name}({arguments}): new environment {frame_name(call_env)}, whose enclosing environment is {ref(function.env)}'
                previous_envs = self.interp.envs
                self.interp.envs = [self.interp.program_env, env]
                self.interp.atomic = True
                try:
                    result = self.interp.apply(function, args, node)
                finally:
                    self.interp.atomic = False
                    self.interp.envs = previous_envs
                text = self.replace_value(replace, result, node)
                if type(function) is Builtin and function.name in ('set_head', 'set_tail'):
                    return f'Changed the {"head" if function.name == "set_head" else "tail"} of a pair: {text}'
                return f'Applied {function.name if type(function) in (Builtin, Closure) else "function"}: {text}'
            return self.action(tail[0] if tail and type(unwrap(node.func)) is Closure and not unwrap(node.func).prelude else node,
                               env, 'application', application)
        if isinstance(node, N.ListExpr):
            for i in range(len(node.elts)):
                action = self.item(node.elts, i, env)
                if action:
                    return action
            def allocate_list():
                result = [unwrap(item) for item in node.elts]
                self.replace_value(replace, result, node)
                return 'Created a list'
            return self.action(node, env, 'list', allocate_list)
        if isinstance(node, (N.BinOp, N.UnaryOp, N.Compare, N.Subscript)):
            if isinstance(node, N.BinOp):
                fields = ['left', 'right']
            elif isinstance(node, N.UnaryOp):
                fields = ['operand']
            elif isinstance(node, N.Compare):
                action = self.child(node, 'left', env)
                if action:
                    return action
                fields = []
                for i in range(len(node.comparators)):
                    action = self.item(node.comparators, i, env)
                    if action:
                        return action
            else:
                fields = ['value', 'index']
            for field in fields:
                action = self.child(node, field, env)
                if action:
                    return action
            def primitive():
                value = self.interp.eval(node, env)
                text = self.replace_value(replace, value, node)
                return f'Evaluated {type(node).__name__}: {text}'
            return self.action(node, env, 'primitive', primitive)
        raise SicpError('RuntimeError', f'No reduction rule for {type(node).__name__}', node.line)

    def boolean_error(self, node, value):
        raise self.interp.not_a_bool('logical operand', value, node)

    def child(self, node, field, env):
        return self.expression(getattr(node, field), env, lambda value: setattr(node, field, value))

    def item(self, items, index, env):
        return self.expression(items[index], env, lambda value: items.__setitem__(index, value))

    def declarations(self, body):
        global_names = []
        def strip(statements):
            result = []
            for statement in statements:
                if isinstance(statement, N.Global):
                    global_names.extend(name for name in statement.names if name not in global_names)
                if isinstance(statement, (N.Global, N.Nonlocal)):
                    continue
                if isinstance(statement, (N.If, N.While, N.For)):
                    statement.body = strip(statement.body)
                    statement.orelse = strip(statement.orelse)
                result.append(statement)
            return result
        return strip(body), global_names

    def block(self, block, replace):
        if not block.body:
            def finish():
                self.replace_value(replace, None, block)
                return f'Returned None from {frame_name(block.env)}'
            return self.action(block, block.env, 'return', finish)
        return self.statements(block.body, block.env, function=(block, replace))

    def statements(self, statements, env, function=None, loop=None):
        if not statements:
            return None
        node = statements[0]
        def replace_head(replacement):
            statements[:1] = [] if replacement is None else [replacement]
            self.after_redex = replacement
        def remove():
            del statements[0]
            self.after_redex = None
        if isinstance(node, (N.Global, N.Nonlocal)):
            remove()
            self.revision += 1
            return self.statements(statements, env, function, loop)
        if isinstance(node, (N.Assign, N.AnnAssign)):
            action = self.child(node, 'value', env)
            if action:
                return action
            target = node.targets[0] if isinstance(node, N.Assign) else node.target
            if isinstance(target, N.Subscript):
                action = self.child(target, 'value', env) or self.child(target, 'index', env)
                if action:
                    return action
            def assign():
                if isinstance(target, N.Name):
                    env.assign(target.id, unwrap(node.value))
                    where = frame_name(env.target_env(target.id))
                    text = f'Assigned {target.id} = {self.show(unwrap(node.value))} in {where}'
                else:
                    sequence, index = unwrap(target.value), unwrap(target.index)
                    if type(sequence) is not list:
                        raise SicpError('TypeError', 'only a list supports item assignment', node.line)
                    sequence[self.interp.check_index(sequence, index, node)] = unwrap(node.value)
                    text = 'Changed a list item'
                remove()
                return text
            return self.action(node, env, 'assignment', assign)
        if isinstance(node, N.FunctionDef):
            def define():
                function_value = self.interp.make_closure(node, env, node.name, False)
                env.assign(node.name, function_value)
                remove()
                return f'Defined {node.name}: function object {self.object_id(function_value)} in {ref(env)}'
            return self.action(node, env, 'definition', define)
        if isinstance(node, N.Return):
            action = (self.expression(node.value, env, lambda value: setattr(node, 'value', value), tail=function)
                      if node.value is not None else None)
            if action:
                return action
            def returned():
                value = unwrap(node.value) if node.value is not None else None
                self.replace_value(function[1], value, node)
                return f'Returned {self.show(value)} from {frame_name(env)}'
            return self.action(function[0], env, 'return', returned)
        if isinstance(node, N.ExprStmt):
            action = self.child(node, 'value', env)
            if action:
                return action
            def discard():
                value = self.show(unwrap(node.value))
                remove()
                return f'Finished the expression statement: its value {value} is not used'
            return self.action(node, env, 'expression-statement', discard)
        if isinstance(node, N.If):
            action = self.child(node, 'test', env)
            if action:
                return action
            def branch():
                condition = unwrap(node.test)
                if type(condition) is not bool:
                    raise self.interp.not_a_bool('if condition', condition, node)
                statements[:1] = node.body if condition else node.orelse
                self.after_redex = statements[0] if statements else None
                return f'Evaluated if statement: condition is {condition}'
            return self.action(node, env, 'if', branch)
        if isinstance(node, N.While):
            def unfold():
                replacement = Loop(copy.deepcopy(node.body), copy.deepcopy(node), node,
                                   copy.deepcopy(node.test))
                replace_head(replacement)
                return 'Unfolded the while loop into an if statement whose body ends with the loop'
            return self.action(node, env, 'while-unfold', unfold)
        if isinstance(node, N.For):
            for i in range(len(node.iter.args)):
                action = self.item(node.iter.args, i, env)
                if action:
                    return action
            def evaluate_range():
                args = [unwrap(argument) for argument in node.iter.args]
                for argument in args:
                    if type(argument) is not int:
                        raise SicpError('TypeError', f'range() needs integers, not {type_name(argument)}', node.line)
                values = range(*args)
                replace_head(RangeFor(node, values.start, values.stop, values.step))
                return f'Evaluated range: from {values.start} to {values.stop} in steps of {values.step}'
            return self.action(node, env, 'for-range', evaluate_range)
        if isinstance(node, RangeFor):
            def iterate():
                inside = node.current < node.stop if node.step > 0 else node.current > node.stop
                if not inside:
                    replace_head(None)
                    return f'Evaluated for statement: {node.current} is not in the range, the loop ends'
                assignment = N.Assign([copy.deepcopy(node.source.target)], Value(node.current, node))
                assignment.line = node.line
                again = RangeFor(node.source, node.current + node.step, node.stop, node.step)
                replace_head(Loop([assignment] + copy.deepcopy(node.source.body), again, node))
                return f'Evaluated for statement: run the body with {node.source.target.id} = {node.current}'
            return self.action(node, env, 'for-unfold', iterate)
        if isinstance(node, Loop):
            if node.condition is not None:
                action = self.expression(node.condition, env, lambda value: setattr(node, 'condition', value))
                if action:
                    return action
                def choose_iteration():
                    condition = unwrap(node.condition)
                    if type(condition) is not bool:
                        raise self.interp.not_a_bool('while condition', condition, node)
                    if condition:
                        node.condition = None
                    else:
                        replace_head(None)
                    return f'Evaluated if statement: condition is {condition}, ' + ('run the loop body' if condition else 'the loop ends')
                return self.action(node, env, 'if', choose_iteration)
            if node.body:
                return self.statements(node.body, env, function, (node, replace_head))
            def finish_iteration():
                replace_head(node.again)
                return 'Finished the loop body, back to the loop'
            return self.action(node, env, 'loop-finish', finish_iteration)
        if isinstance(node, (N.Break, N.Continue)):
            def jump():
                replacement = loop[0].again if isinstance(node, N.Continue) else None
                loop[1](replacement)
                return ('Evaluated continue: back to the loop' if isinstance(node, N.Continue)
                        else 'Evaluated break: the loop ends')
            return self.action(node, env, 'continue' if isinstance(node, N.Continue) else 'break', jump)
        if isinstance(node, N.Pass):
            def passed():
                remove()
                return 'Finished pass'
            return self.action(node, env, 'pass', passed)
        if isinstance(node, N.ImportFrom):
            def imported():
                self.interp.exec_ImportFrom(node, env)
                remove()
                return f'Imported from {node.module}'
            return self.action(node, env, 'import', imported)
        raise SicpError('RuntimeError', f'No reduction rule for {type(node).__name__}', node.line)

    def step(self):
        return self.statements(self.program, self.interp.program_env)


class ProgramSerializer:
    """The program-term vocabulary used by the reference stepper protocol.

    Node IDs are presentation identities, not program semantics; clients may
    assign them while rendering. Heap references and environment IDs are stable.
    """
    def __init__(self, machine):
        self.machine = machine

    def frame(self, env):
        return 'Global' if frame_name(env) == 'global env' else frame_name(env)

    def literal(self, value):
        label = {int: 'int', float: 'float', complex: 'complex', bool: 'bool', str: 'str', type(None): 'None'}.get(type(value), type_name(value))
        raw = show_atom(value)
        if type(value) in (int, float) and raw.startswith('-'):
            return {'type': 'UnaryExpression', 'operator': '-',
                    'argument': {'type': 'Literal', 'value': None, 'raw': raw[1:], 'label': label}}
        return {'type': 'Literal', 'value': None, 'raw': raw, 'label': label}

    def value(self, node):
        value = node.value
        if isinstance(node, Value) and node.builtin_name is not None:
            return self.ident(node.builtin_name)
        if type(value) is list or (type(value) is Closure and not value.prelude):
            return {'type': 'Ref', 'objectId': self.machine.object_id(value)}
        if type(value) in (Builtin, Closure):
            name = value.name
            return {'type': 'Builtin', 'name': name}
        return self.literal(value)

    def ident(self, name):
        return {'type': 'Identifier', 'name': name}

    def params(self, node):
        names = [param.name for param in node.params.args]
        if node.params.vararg:
            names.append('*' + node.params.vararg)
        return [self.ident(name) for name in names]

    def block(self, body):
        return {'type': 'BlockStatement', 'body': [self.node(item) for item in body]}

    def for_node(self, source, arguments):
        return {'type': 'ForStatement', 'target': self.node(source.target),
                'iter': {'type': 'CallExpression', 'callee': {'type': 'Builtin', 'name': 'range'},
                         'arguments': arguments}, 'body': self.block(source.body)}

    def program(self):
        return {'type': 'Program', 'body': [self.node(statement) for statement in self.machine.program]}

    def node(self, node):
        if val(node):
            return self.value(node)
        if isinstance(node, N.Name):
            return self.ident(node.id)
        if isinstance(node, N.BinOp):
            return {'type': 'BinaryExpression', 'operator': node.op,
                    'left': self.node(node.left), 'right': self.node(node.right)}
        if isinstance(node, N.Compare):
            return {'type': 'BinaryExpression', 'operator': node.ops[0],
                    'left': self.node(node.left), 'right': self.node(node.comparators[0])}
        if isinstance(node, N.UnaryOp):
            return {'type': 'UnaryExpression', 'operator': 'not ' if node.op == 'not' else node.op,
                    'argument': self.node(node.operand)}
        if isinstance(node, N.BoolOp):
            result = self.node(node.values[0])
            for operand in node.values[1:]:
                result = {'type': 'LogicalExpression', 'operator': node.op,
                          'left': result, 'right': self.node(operand)}
            return result
        if isinstance(node, N.IfExp):
            return {'type': 'ConditionalExpression', 'test': self.node(node.test),
                    'consequent': self.node(node.body), 'alternate': self.node(node.orelse)}
        if isinstance(node, N.Lambda):
            return {'type': 'ArrowFunctionExpression', 'params': self.params(node), 'body': self.node(node.body)}
        if isinstance(node, N.Call):
            return {'type': 'CallExpression', 'callee': self.node(node.func),
                    'arguments': [self.node(argument) for argument in node.args]}
        if isinstance(node, N.Starred):
            return {'type': 'SpreadElement', 'argument': self.node(node.value)}
        if isinstance(node, N.ListExpr):
            return {'type': 'ArrayExpression', 'elements': [self.node(element) for element in node.elts]}
        if isinstance(node, N.Subscript):
            return {'type': 'MemberExpression', 'object': self.node(node.value), 'property': self.node(node.index)}
        if isinstance(node, Block):
            body = [self.node(statement) for statement in node.body]
            if node.globals:
                body.insert(0, {'type': 'GlobalStatement', 'names': ', '.join(node.globals)})
            return {'type': 'EnvBlock', 'envId': self.frame(node.env), 'body': body}
        if isinstance(node, (N.Assign, N.AnnAssign)):
            target = node.targets[0] if isinstance(node, N.Assign) else node.target
            if isinstance(target, N.Name):
                return {'type': 'VariableDeclaration', 'kind': '',
                        'declarations': [{'type': 'VariableDeclarator', 'id': self.node(target), 'init': self.node(node.value)}]}
            return {'type': 'AssignmentStatement', 'target': self.node(target), 'value': self.node(node.value)}
        if isinstance(node, N.FunctionDef):
            return {'type': 'FunctionDeclaration', 'id': self.ident(node.name),
                    'params': self.params(node), 'body': self.block(node.body)}
        if isinstance(node, N.ExprStmt):
            return {'type': 'ExpressionStatement', 'expression': self.node(node.value)}
        if isinstance(node, N.Return):
            return {'type': 'ReturnStatement', 'argument': self.node(node.value) if node.value is not None else None}
        if isinstance(node, N.If):
            return {'type': 'IfStatement', 'test': self.node(node.test),
                    'consequent': self.block(node.body), 'alternate': self.block(node.orelse) if node.orelse else None}
        if isinstance(node, N.While):
            return {'type': 'WhileStatement', 'test': self.node(node.test), 'body': self.block(node.body)}
        if isinstance(node, N.For):
            return self.for_node(node, [self.node(argument) for argument in node.iter.args])
        if isinstance(node, RangeFor):
            return self.for_node(node.source, [self.literal(value) for value in (node.current, node.stop, node.step)])
        if isinstance(node, Loop):
            iteration = {'type': 'LoopIteration', 'statements': [self.node(statement) for statement in node.body] + [self.node(node.again)]}
            if node.condition is None:
                return iteration
            return {'type': 'IfStatement', 'test': self.node(node.condition),
                    'consequent': {'type': 'BlockStatement', 'body': [iteration]}, 'alternate': None}
        for cls, label in ((N.Pass, 'PassStatement'), (N.Break, 'BreakStatement'), (N.Continue, 'ContinueStatement')):
            if isinstance(node, cls):
                return {'type': label}
        if isinstance(node, (N.Global, N.Nonlocal)):
            return {'type': 'GlobalStatement' if isinstance(node, N.Global) else 'NonlocalStatement', 'names': ', '.join(node.names)}
        if isinstance(node, N.ImportFrom):
            return {'type': 'ImportDeclaration', 'source': node.module,
                    'specifiers': [{'imported': alias.name, 'local': alias.asname or alias.name} for alias in node.names]}
        return {'type': type(node).__name__}


class StoreSerializer:
    """Find roots in the remaining program, then follow frame and heap arrows.

    The history registry keeps objects available for inspection. It is never a
    root: an unreachable closure and its frame cannot keep each other alive.
    """
    def __init__(self, machine):
        self.machine = machine
        self.frames = {}
        self.objects = {}
        self.stack = []

    def frame(self, env):
        env = real_frame(env)
        if env is None or env.kind in ('library', 'builtins') or id(env) in self.frames:
            return
        self.frames[id(env)] = env
        for value in env.vars.values():
            self.value(value)
        self.frame(env.parent)

    def value(self, value):
        if type(value) not in (list, Closure) or (type(value) is Closure and value.prelude):
            return
        if id(value) in self.objects:
            return
        self.objects[id(value)] = value
        if type(value) is list:
            for item in value:
                self.value(item)
        else:
            # Atomic library calls hide their internal applications. A returned
            # closure can nevertheless expose a callback's creation frame.
            env = value.env
            while env is not None and id(env) in self.machine.interp.hidden_frames:
                interp = self.machine.interp
                if not env.serial and (env.vars or env.scope.local_names):
                    interp.frame_count += 1
                    env.serial = interp.frame_count
                    interp.created_frames[id(env)] = env
                env = env.parent
            self.frame(value.env)

    def visit(self, node):
        if isinstance(node, list):
            for item in node:
                self.visit(item)
        elif isinstance(node, Value):
            self.value(node.value)
        elif isinstance(node, Block):
            self.frame(node.env)
            self.stack.append(node.env)
            self.visit(node.body)
        elif isinstance(node, (N.FunctionDef, N.Lambda, N.Constant, N.Name)):
            return
        elif isinstance(node, N.Node):
            for key, child in vars(node).items():
                # A future iteration's body has not been allocated/evaluated.
                if isinstance(node, Loop) and key == 'again':
                    continue
                if isinstance(child, (list, N.Node)):
                    self.visit(child)

    def value_record(self, value):
        if type(value) is list or (type(value) is Closure and not value.prelude):
            return {'kind': 'ref', 'objectId': self.machine.object_id(value)}
        if type(value) in (Closure, Builtin):
            return {'kind': 'builtin', 'name': value.name}
        return {'kind': 'primitive', 'display': show_atom(value),
                'label': {int: 'int', float: 'float', complex: 'complex', bool: 'bool',
                          str: 'str', type(None): 'None'}.get(type(value), type_name(value))}

    def snapshot(self):
        m = self.machine
        self.frame(m.interp.program_env)
        self.visit(m.program)
        live_frames, live_objects = set(self.frames), set(self.objects)
        for env in list(m.interp.created_frames.values()):
            self.frame(env)
        for value in list(m.interp.objects.values()):
            self.value(value)
        frames = []
        for env in sorted(self.frames.values(), key=lambda e: e.serial):
            dead = id(env) not in live_frames
            if dead and id(env) in m.dead_frame_records:
                frames.append(m.dead_frame_records[id(env)])
                continue
            m.dead_frame_records.pop(id(env), None)
            names = list(env.vars)
            if env.scope is not None:
                names += sorted(env.scope.local_names - env.vars.keys())
            record = {'id': 'Global' if env.kind == 'program' else frame_name(env),
                           'name': 'global' if env.kind == 'program' else env.name,
                           'parentId': None if env.kind == 'program' else ProgramSerializer(m).frame(env.parent),
                           'bindings': [{'name': name, 'value': self.value_record(env.vars[name])
                                         if name in env.vars else {'kind': 'unassigned'}} for name in names],
                           'isGarbage': dead}
            frames.append(record)
            if dead:
                m.dead_frame_records[id(env)] = record
        heap = []
        for key, value in self.objects.items():
            record = {'id': m.object_id(value), 'isGarbage': key not in live_objects}
            if type(value) is list:
                record.update(kind='list', elements=[self.value_record(item) for item in value])
            else:
                record.update(kind='function', params=value.params + (['*' + value.vararg] if value.vararg else []),
                              envId=ProgramSerializer(m).frame(value.env))
                if not value.is_lambda:
                    record['name'] = value.name
            heap.append(record)
        heap.sort(key=lambda item: int(item['id'][1:]))
        active = real_frame(self.stack[-1]) if self.stack else m.interp.program_env
        return {'frames': frames, 'heap': heap, 'activeFrameId': ProgramSerializer(m).frame(active),
                'output': m.interp.out.getvalue()}
