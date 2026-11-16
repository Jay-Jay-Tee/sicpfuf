"""Editor diagnostics using the selected chapter, without executing user code."""
import io

from ..errors import SicpSyntaxError, format_syntax_error
from ..interpreter import Interpreter


def check_source(source, chapter=2, typed=False):
    if type(chapter) is not int or chapter not in (1, 2, 3, 4):
        raise ValueError('Choose Python §1, §2, §3 or §4.')
    if type(typed) is not bool or (typed and chapter != 4):
        raise ValueError('Typed checking requires Python §4.')
    interp = Interpreter(chapter, out=io.StringIO())
    interp.typed = typed
    try:
        interp.load_source(source, '<editor>', typecheck=typed)
    except SicpSyntaxError as exc:
        error = exc.report(source.splitlines()) if hasattr(exc, 'report') else format_syntax_error(exc, source.splitlines())
        diagnostics = ([{'line': item.line, 'column': item.col + 1, 'message': item.message}
                        for item in exc.diagnostics] if hasattr(exc, 'diagnostics') else
                       [{'line': exc.line, 'column': exc.col, 'message': exc.msg}])
        return {'ok': False, 'error': error, 'diagnostics': diagnostics}
    return {'ok': True, 'error': None, 'diagnostics': []}
