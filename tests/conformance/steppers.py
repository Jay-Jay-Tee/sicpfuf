"""Original programs exercising each reduction/store rule, with upstream snapshots."""
import json

PROGRAMS = {
    'arithmetic': 'print(2 + 3 * 4)',
    'lookup': 'x = 2\ny = x + x\nprint(y)',
    'call': 'def f(x):\n    return x + 1\nprint(f(2))',
    'anonymous-call': 'print((lambda x: x)(3))',
    'nested-shadow': 'def add(a,b):\n    def add(c,d):\n        return c+d\n    return add(a,b)\nprint(add(5,6))',
    'closure': 'def make(x):\n    return lambda y: x + y\nf = make(2)\nprint(f(3))',
    'two-closures': 'def make(x):\n    return lambda y: x + y\nf = make(2)\ng = make(10)\nprint(f(3), g(3))',
    'nonlocal': 'def make(x):\n    def f(y):\n        nonlocal x\n        x = x + y\n        return x\n    return f\nf = make(2)\nprint(f(3), f(4))',
    'global': 'x = 2\ndef f(y):\n    global x\n    x = y\nf(4)\nprint(x)',
    'branch': 'x = 2\nif x > 0:\n    print(x)\nelse:\n    print(0)',
    'conditional': 'print(2 if True else 1 / 0)',
    'short-circuit': 'print(False and 1 / 0, True or 1 / 0)',
    'recursion': 'def f(n):\n    return 0 if n == 0 else 1 + f(n-1)\nprint(f(2))',
    'tail-recursion': 'def f(n,a):\n    return a if n == 0 else f(n-1,a+n)\nprint(f(2,0))',
    'empty-frame': 'x = 2\ndef f():\n    return x\nprint(f())',
    'implicit-return': 'def f(x):\n    print(x)\nprint(f(2))',
    'list-sharing': 'a = [1,2]\nb = a\nb[0] = 3\nprint(a, a is b)',
    'list-cycle': 'a = pair(1,None)\nset_tail(a,a)\nprint(head(tail(a)))',
    'list-of-functions': 'a = [lambda x: x + 1]\nprint(a[0](2))',
    'while': 'x = 0\nwhile x < 2:\n    x = x + 1\nprint(x)',
    'for': 'total = 0\nfor i in range(3):\n    total = total + i\nprint(total)',
    'break': 'x = 0\nwhile True:\n    x = x + 1\n    if x == 2:\n        break\nprint(x)',
    'continue': 'for i in range(3):\n    if i == 1:\n        continue\n    print(i)',
    'rest-parameter': 'def f(x,*ys):\n    return pair(x,ys)\nprint(f(1,2,3))',
    'library-call': 'print(length(map(lambda x: x + 1, llist(1,2))))',
    'builtin-shadow': 'p = print\nprint = 0\np(print)',
    'and-chain': 'print(True and True and False and True)',
    'or-chain': 'print(False or True or False or True)',
    'unary-values': 'print(-1, -2.5, +3, not False)',
    'strings': 'x = "abc"\nprint(x[1], "a" + "b")',
    'complex-values': 'print((1+2j) + 2)',
    'empty-list': 'a = []\nprint(a)',
    'nested-lists': 'a = [[1],[2]]\nprint(a[0][0])',
    'spread-arguments': 'def f(x,y):\n    return x-y\na = [5,2]\nprint(f(*a))',
    'list-repetition': 'a = [[1]] * 2\na[0][0] = 3\nprint(a, a[0] is a[1])',
    'subscript-evaluation-order': 'a = [0,0]\ndef f(x):\n    print(x)\n    return x\na[f(0)] = f(1)\nprint(a)',
    'parameter-and-locals': 'def f(x):\n    z = x\n    a = z\n    return a\nprint(f(3))',
    'nested-while': 'i = 0\nwhile i < 2:\n    j = 0\n    while j < 2:\n        j = j + 1\n    i = i + j\nprint(i)',
    'negative-range': 'for i in range(4,0,-2):\n    print(i)',
    'empty-range': 'for i in range(0):\n    print(i)\nprint(9)',
    'return-through-loop': 'def f(x):\n    while True:\n        if x > 0:\n            return x\n        return 0\nprint(f(2))',
    'return-through-conditional': 'def f(x):\n    if x:\n        return 1\n    return 2\nprint(f(False))',
    'nested-loop-break': 'for i in range(2):\n    while True:\n        break\n    print(i)',
    'returned-list': 'def f(x):\n    return [x,x]\nprint(f(2))',
    'discard-value': '2 + 3\nNone\nprint(4)',
    'pass-function': 'def f():\n    pass\nprint(f())',
    'mutual-recursion': 'def even(n):\n    return True if n == 0 else odd(n-1)\ndef odd(n):\n    return False if n == 0 else even(n-1)\nprint(even(2))',
    'logical-right-call': 'def f(x):\n    return x\nprint(True and f(3), False or f(4))',
    'logical-right-none': 'True and None\nprint(False or None)',
    'logical-tail-call': 'def f(x):\n    return x == 0 or f(x-1)\nprint(f(2))',
    'library-returned-closures': 'a = map(lambda x: lambda y: x+y, llist(2,3))\nprint(head(a)(4))',
    'post-library-frame-number': 'def f(x):\n    return x+1\nmap(f,llist(1,2))\nprint(f(3))',
    'bare-return': 'def f(x):\n    return\nprint(f(2))',
    'explicit-none-return': 'def f(x):\n    return None\nprint(f(2))',
    'no-parameter-lambda': 'print((lambda: 3)())',
    'math-constant': 'x = math_pi\nprint(x * 2)',
    'library-value': 'f = length\nprint(f(llist(1,2)))',
    'logical-right-list': 'print(True and [1,2])',
    'range-header-calls': 'def f(x):\n    return x+1\nfor i in range(f(0),f(2)):\n    print(i)',
}


def cases():
    result = [{'id': 'steps/environment/' + name, 'source': source + '\n', 'chapter': 3,
               'stepper': 'environment'} for name, source in PROGRAMS.items()]
    for name in ('arithmetic', 'lookup', 'call', 'anonymous-call', 'nested-shadow', 'closure',
                 'conditional', 'short-circuit', 'recursion', 'tail-recursion', 'library-call'):
        result.append({'id': 'steps/substitution/' + name, 'source': PROGRAMS[name] + '\n',
                       'chapter': 2, 'stepper': 'substitution'})
    return result


if __name__ == '__main__':
    print(json.dumps({'cases': cases()}))
