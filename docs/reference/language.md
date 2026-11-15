# Python §1–§4: the language

<p class="chapter-goal">Exactly what each chapter allows and forbids, and how it differs from the Python you may know.</p>

The course language is not one language but four, each a little bigger than the one before. Every program on this page was run in sicpfuf, and every plain one was also run in py-slang (the implementation the course uses) with the same result.

## The four chapters at a glance

| Feature | §1 | §2 | §3 | §4 |
|---|:-:|:-:|:-:|:-:|
| numbers, strings, `True`/`False`, `None` | ✓ | ✓ | ✓ | ✓ |
| `x = e` (declaration assignment), `def`, `return`, `lambda` | ✓ | ✓ | ✓ | ✓ |
| `if` / `elif` / `else`, conditional expression `a if p else b` | ✓ | ✓ | ✓ | ✓ |
| `and`, `or`, `not`, `+ - * / // % **`, `== != < > <= >=` | ✓ | ✓ | ✓ | ✓ |
| `from rune import ...` (and curve, sound, repeat) | ✓ | ✓ | ✓ | ✓ |
| MISC and MATH libraries (`print`, `math_sqrt`, …) | ✓ | ✓ | ✓ | ✓ |
| `==` on booleans and functions | ✗ | ✗ | ✓ | ✓ |
| pairs and linked lists: `pair`, `head`, `tail`, `llist`, `map` … | ✗ | ✓ | ✓ | ✓ |
| reassignment `x = x + 1`, `global`, `nonlocal` | ✗ | ✗ | ✓ | ✓ |
| `while`, `for i in range(...)`, `break`, `continue`, `pass` | ✗ | ✗ | ✓ | ✓ |
| lists `[1, 2, 3]`, `xs[i]`, `xs[i] = v`, `[0] * n` | ✗ | ✗ | ✓ | ✓ |
| `is`, `is not` | ✗ | ✗ | ✓ | ✓ |
| `*rest` parameters and `f(*xs)` | ✗ | ✗ | ✓ | ✓ |
| `set_head`, `set_tail`, `is_list`, the stream library | ✗ | ✗ | ✓ | ✓ |
| `parse`, `tokenize`, `apply_in_underlying_python` | ✗ | ✗ | ✗ | ✓ |
| `x += 1`, `a < b < c`, f-strings, tuples, dictionaries, classes, slices … | ✗ | ✗ | ✗ | ✗ |

Pick the chapter with `-v N`, or put `# chapter N` on the first line of the file (see [the x-ray tools](xray.md#choosing-the-chapter)). Without either, sicpfuf runs §4.

The full list of pre-declared names per chapter is in the [library reference](library.md).

## §1: names, functions, conditionals

Python §1 has values (numbers, strings, booleans, `None`), names, operator combinations, function definitions, lambda expressions, conditional statements and conditional expressions. That is all. Repetition is done with recursion.

```python title="§1"
def abs_diff(a, b):
    if a > b:
        return a - b
    else:
        return b - a

square = lambda x: x * x
print(abs_diff(3, 10), square(4), "big" if square(4) > 10 else "small")
```
```text title="Output"
7 16 big
```

**A name gets a value once.** In §1 and §2 there is no reassignment. A parameter counts as already having a value, and assigning the same name in both branches of an `if`/`else` also counts as twice. This is found *before* the program runs, so nothing is printed:

```python title="§1"
def sign(n):
    if n < 0:
        s = -1
    else:
        s = 1
    return s

print(sign(-5))
```
```text
NameReassignmentError: the name 's' already has a value
```

Write `return -1` and `return 1` in the two branches instead, or use a conditional expression: `s = -1 if n < 0 else 1`.

**Not yet in §1 and §2:** loops, lists `[...]`, indexing `xs[i]`, `pass`, `is`, `global`/`nonlocal`, `*rest` parameters. Each is a "Feature not supported" error that names your chapter:

```python title="§1"
def nothing_yet():
    pass
```
```text
FeatureNotSupportedError: Python §1 does not have this: pass statements
```

## §2: pairs and linked lists

§2 is §1 plus the LINKED LISTS library: `pair`, `head`, `tail`, `llist`, `map`, `filter`, `reduce` and friends (all listed in the [library reference](library.md#linked-lists-2)). The rules about names stay the same as in §1.

```python title="§2"
xs = llist(1, 2, 3, 4)
evens = filter(lambda x: x % 2 == 0, xs)
print(evens)
print(reduce(lambda x, acc: x + acc, 0, map(lambda x: x * 10, xs)))
```
```text title="Output"
[2, [4, None]]
100
```

There are still no lists `[...]` and no indexing. To get an item of a linked list, use `head`, `tail` or `llist_ref`:

```python title="§2"
xs = llist("a", "b")
print(xs[0])
```
```text
FeatureNotSupportedError: Python §2 does not have this: subscript expressions
```

## §3: state, loops, lists, streams

§3 adds everything that changes things:

- **reassignment** of names, and `global` / `nonlocal` to reassign a name of the program or of an enclosing function;
- **loops**: `while`, and `for i in range(...)` with 1 to 3 integer arguments; `break`, `continue`, `pass`;
- **lists** `[1, 2, 3]`, indexing `xs[i]` (negative indexes count from the end), `xs[i] = v`, `len(xs)`, `[0] * n`;
- `is` and `is not`; `*rest` parameters and spreading `f(*xs)`;
- `set_head`, `set_tail`, `is_list` and the STREAMS library.

```python title="§3"
def count_up(n):
    total = 0
    for i in range(1, n + 1):
        total = total + i
    return total

squares = [0] * 4
for i in range(4):
    squares[i] = i * i

print(count_up(10), squares, squares[-1])
```
```text title="Output"
55 [0, 1, 4, 9] 9
```

Things to know about §3:

- **`for` only works over `range`.** `for x in xs:` is not allowed: loop over the indexes, `for i in range(len(xs)):`. And `range` cannot be used anywhere else, not even stored in a name.
- **Lists cannot grow or shrink.** There is no `xs.append`, no `[1] + [2]`. Make a list of the right size with `[0] * n` and fill it in.
- **A pair is a list of length two.** `pair(1, 2)` and `[1, 2]` are the same thing:

```python title="§3"
print(pair(1, 2) == [1, 2], is_pair([1, 2]), len(llist(1, 2, 3)))
print(len("hello"), "hello"[1])
```
```text title="Output"
True True 2
5 e
```

`len(llist(1, 2, 3))` is `2` because the llist is the pair `[1, [2, [3, None]]]`, a list of two items. Use `length(xs)` for the number of items in a llist.

```python title="§3"
r = range(5)
```
```text
SyntaxError: 'range' can only be used in a for-loop header, as in 'for i in range(n):'
```

## §4: programs as data

§4 is §3 plus three functions for writing the metacircular evaluator: `parse` (program text to a syntax tree made of tagged llists), `tokenize` (program text to a llist of tokens) and `apply_in_underlying_python` (call a built-in function with a llist of arguments).

```python title="§4"
tree = parse("x * 2")
print(head(tree), head(tail(tree)))
print(apply_in_underlying_python(max, llist(3, 9, 4)))
```
```text title="Output"
binary_operator_combination *
9
```

The tags `parse` uses are listed in the [library reference](library.md#mce-4).

## Printing

Only `print(...)` shows anything. A bare expression on its own line is evaluated and thrown away (the [interactive prompt](xray.md#the-interactive-prompt) is the one exception).

| Value | `print` shows |
|---|---|
| a string on its own | the text, no quotes: `hi` |
| a string inside a pair or list | with single quotes: `['a', 'b']` |
| `pair(1, 2)` | `[1, 2]` |
| `llist(1, 2, 3)` | `[1, [2, [3, None]]]` (box notation) |
| the empty llist | `None` |
| a function you defined | `<function f>` |
| a lambda | `<function (anonymous)>` |
| a built-in such as `print` | `<built-in function print>` |
| a library function written in Python, such as `map` | `<function map>` |
| `4 / 2` | `2.0` (always a float) |

```python title="§2"
def twice(f):
    return lambda x: f(f(x))

print("hi", pair("a", None), llist(1, 2), None, True)
print(twice, twice(abs), print, map)
print_llist(llist(1, llist(2, 3), "a"))
```
```text title="Output"
hi ['a', None] [1, [2, None]] None True
<function twice> <function (anonymous)> <built-in function print> <function map>
llist(1, llist(2, 3), 'a')
```

`print(a, b)` puts one space between the values. `print_llist` shows llist notation instead of box notation. To build a string, use `+` and `str`: `"n is " + str(n)`.

## Equality and identity

| | §1, §2 | §3, §4 |
|---|---|---|
| `==` / `!=` on numbers, strings, `None` | by value | by value |
| `==` on pairs (and lists) | item by item, all the way down | item by item, all the way down |
| `==` on a boolean or a function | **TypeError** | allowed (`True == 1` is `True`) |
| `is` / `is not` | not in the language | the same object? |

```python title="§2"
print(1 == 1.0, "ab" == "a" + "b", None == 0)
print(llist(1, 2) == llist(1, 2), pair(1, "x") != pair(1, "y"))
```
```text title="Output"
True True False
True True
```

In §1 and §2, a boolean on either side of `==` is an error, even deep inside two pairs:

```python title="§1"
done = 3 > 2
if done == True:
    print("yes")
```
```text
TypeError: unsupported operand type(s) for ==: bool and bool
```

Write `if done:` instead. The same holds for functions: `f == g` is a TypeError in §1 and §2.

In §3, `==` asks "do they look the same?" and `is` asks "are they the very same object?". For numbers, strings, booleans and `None`, `is` behaves like `==`.

```python title="§3"
xs = [1, 2]
ys = xs
zs = [1, 2]
print(xs == zs, xs is zs, xs is ys)
set_head(ys, 99)
print(xs, zs)
print(True == 1, 5 is 5, None is None)
```
```text title="Output"
True False True
[99, 2] [1, 2]
True True True
```

## Strict booleans and strict operators

The course language never converts a value behind your back. This is the biggest difference from real Python.

**Conditions must be exactly `True` or `False`.** That holds for `if`, `while`, the predicate of a conditional expression, the operand of `not`, and every operand of `and`/`or` except the last.

```python title="§1"
def is_odd(n):
    return n % 2 == 1

n = 7
if n % 2:
    print("odd")
```
```text
TypeError: if condition must be bool, not int
```

Write `if n % 2 == 1:` (or `if is_odd(n):`).

**`and` and `or` are syntactic forms, not functions.** `a and b` means `b if a else False`; `a or b` means `True if a else b`. The right operand is only evaluated when needed, and it may be any value:

```python title="§1"
print(True and 5, False or "x", False and 1 / 0)
print("" or "x")
```
```text
5 x False
TypeError: left operand of 'or' must be bool, not str
```

**Operators do not mix types.** `+` adds two numbers or joins two strings, nothing else. `True` is not a number. `<`, `>`, `<=`, `>=` compare two numbers or two strings.

| You write | You get |
|---|---|
| `"ab" + "cd"` | `abcd` |
| `"a" + 1`, `1 + "a"` | TypeError |
| `"ab" * 3` | TypeError |
| `True + 1` | TypeError |
| `None + 1` | TypeError |
| `7 / 2`, `4 / 2` | `3.5`, `2.0` (`/` always gives a float) |
| `7 // 2`, `-7 // 2` | `3`, `-4` (`//` rounds down) |
| `-7 % 3`, `7 % -3` | `2`, `-2` (`%` has the sign of the divisor) |
| `2 ** 100` | an exact integer (integers have no size limit) |
| `1 < "a"` | TypeError |

```python title="§1"
print(7 / 2, 4 / 2, 7 // 2, -7 // 2, -7 % 3, 7 % -3)
print(2 ** 100)
print("n is " + str(7))
print("ab" * 3)
```
```text
3.5 2.0 3 -4 2 -2
1267650600228229401496703205376
n is 7
TypeError: unsupported operand type(s) for *: str and int
```

## Names must be declared somewhere

Before the program runs, every name you use must be declared *somewhere* in it: by an assignment, a `def`, a parameter or an import. Otherwise the whole program is rejected, even if the line would never run:

```python title="§1"
def unused():
    return mystery + 1

print("never printed")
```
```text
NameNotFoundError: the name 'mystery' is not found in the current or enclosing environment(s)
```

A name that *is* declared, but whose assignment has not run yet, is a run-time error. At the top level it is a NameError. Inside a function it is an UnassignedLocalError, and the function does **not** fall back to a name of the same name outside:

```python title="§1"
x = 10
def f():
    y = x + 1
    x = 5
    return y

print(f())
```
```text
UnassignedLocalError: cannot access local variable 'x' where it is not associated with a value
```

Because `f` assigns `x` somewhere in its body, `x` belongs to `f`'s own frame for the whole body. (In §1 the fix is a new name; in §3 you could also say `global x`.) More in [Errors explained](errors.md#unassignedlocalerror).

Other rules that come with functions:

- A function that ends without running a `return` returns `None`. An `if` does not need an `else`.
- The number of arguments must match the number of parameters exactly. There are no default values and no keyword arguments.

## Proper tail calls and the 1024 limit

A call is a **tail call** when nothing is left to do after it: `return f(...)`, also through both branches of a conditional expression and the last operand of `and`/`or`. The course language has **proper tail calls**: a tail call does not keep its caller waiting. So an iterative process written with recursion runs in constant space, for as many steps as you like:

```python title="§1"
def count_down(n, steps):
    return steps if n == 0 else count_down(n - 1, steps + 1)

def all_even(n):
    return n == 0 or (n % 2 == 0 and all_even(n - 2))

print(count_down(200000, 0), all_even(100000))
```
```text title="Output"
200000 True
```

A **recursive process** keeps a deferred operation for every call (here the `n *` waiting for the answer). Once more than 1024 calls are waiting at the same time, the program stops:

```python title="§1"
def factorial(n):
    return 1 if n == 0 else n * factorial(n - 1)

print(factorial(1000) > 0)
print(factorial(1100))
```
```text
True
RecursionError: maximum recursion depth exceeded
```

So `factorial(1000)` works and `factorial(1100)` does not. The library functions (`map`, `append`, `reduce`, …) are written so that they never pile up deferred operations, so they cope with llists of 100 000 items. Your own non-tail recursion over a llist of more than about 1000 items will fail. Real Python has no proper tail calls (and stops near 1000 calls for every kind of recursion).

## What real Python has and the course language does not

None of these exist in **any** chapter. Each line was checked; most give "Feature not supported", a few give a SyntaxError.

| Real Python | What you get | Write instead |
|---|---|---|
| `x += 1` | Feature not supported: augmented assignment | `x = x + 1` (§3) |
| `a < b < c` | Feature not supported: chained comparisons | `a < b and b < c` |
| `f"{n}"` | SyntaxError: f-strings | `"n is " + str(n)` |
| `a = b = 1` | SyntaxError: chained assignment | two lines |
| `(1, 2)`, `a, b = b, a` | Feature not supported: tuples / assignment to several names | `pair(a, b)`; a temporary name |
| `{1: 2}`, `{1, 2}` | Feature not supported: dictionaries / set displays | a list or a llist of pairs |
| `[x * x for x in xs]` | Feature not supported: list comprehensions | a loop, or `map` |
| `xs[1:]` | Feature not supported: slices | a loop; `tail` for a llist |
| `def f(x=1)`, `f(x=1)` | Feature not supported: default values / keyword arguments | pass every argument by position |
| `xs.append(3)`, `math.sqrt(2)` | Feature not supported: attribute access | `math_sqrt(2)`; lists cannot grow |
| `class`, `try`/`except`, `raise`, `with`, `del`, `yield` | Feature not supported (or SyntaxError for `yield`) | functions and `error(...)` |
| `assert x > 0` | Feature not supported: assert statements | `if ...: error(...)` |
| `import math` | Feature not supported: import statements | `from rune import heart` |
| `while ... else`, `for ... else` | SyntaxError | an `if` after the loop |
| `x = 1; y = 2` | SyntaxError: `;` | one statement per line |
| `1 in xs` | TypeError (there is no `in`) | `member(1, xs)` for a llist; a loop for a list |
| `&`, `^`, `~`, `<<`, `>>`, `@` (and the bitwise or) | Feature not supported: bitwise operators | `%`, `//`, `**` |
| `for x in xs:` | Feature not supported: for loops must use range() | `for i in range(len(xs)):` |

??? example "The checked demos"

    ```python title="§3"
    x = 1
    x += 1
    ```
    ```text
    FeatureNotSupportedError: Python §1-§4 does not have this: augmented assignment (+=)
    ```

    ```python title="§3"
    n = 5
    print(0 < n < 10)
    ```
    ```text
    FeatureNotSupportedError: Python §1-§4 does not have this: chained comparisons (a < b < c)
    ```

    ```python title="§3"
    n = 5
    print(f"n is {n}")
    ```
    ```text
    SyntaxError: f-strings are not part of Python §1-§4
    ```

    ```python title="§3"
    a = b = 0
    ```
    ```text
    SyntaxError: chained assignment (a = b = ...) is not part of Python §1-§4
    ```

    ```python title="§3"
    a = 1
    b = 2
    a, b = b, a
    ```
    ```text
    FeatureNotSupportedError: Python §1-§4 does not have this: assignment to several names (a, b = ...)
    ```

    ```python title="§3"
    ages = {"ann": 19}
    ```
    ```text
    FeatureNotSupportedError: Python §1-§4 does not have this: dictionaries
    ```

    ```python title="§3"
    xs = [1, 2, 3]
    print([x * x for x in xs])
    ```
    ```text
    FeatureNotSupportedError: Python §1-§4 does not have this: list comprehensions
    ```

    ```python title="§3"
    xs = [1, 2, 3]
    print(xs[1:])
    ```
    ```text
    FeatureNotSupportedError: Python §1-§4 does not have this: slices (a[i:j])
    ```

    ```python title="§3"
    def greet(name="you"):
        return "hi " + name
    ```
    ```text
    FeatureNotSupportedError: Python §1-§4 does not have this: default values of parameters (name=value)
    ```

    ```python title="§3"
    xs = [1, 2]
    xs.append(3)
    ```
    ```text
    FeatureNotSupportedError: Python §1-§4 does not have this: attribute access (a.b)
    ```

    ```python title="§3"
    class Point:
        pass
    ```
    ```text
    FeatureNotSupportedError: Python §1-§4 does not have this: classes
    ```

    ```python title="§3"
    import math
    ```
    ```text
    FeatureNotSupportedError: Python §1-§4 does not have this: import statements (use from ... import ...)
    ```

    ```python title="§3"
    x = 1; y = 2
    ```
    ```text
    SyntaxError: ';' is not part of Python §1-§4: write one statement per line
    ```

    ```python title="§3"
    xs = [1, 2]
    for x in xs:
        print(x)
    ```
    ```text
    FeatureNotSupportedError: a for loop can only go over range(...), as in: for i in range(n):
    ```

    ```python title="§3"
    i = 0
    while i < 3:
        i = i + 1
    else:
        print("done")
    ```
    ```text
    SyntaxError: `while ... else` is not part of Python §1-§4
    ```

!!! note "Python §N vs real Python, in one breath"
    Same syntax, fewer features, stricter values: conditions must be booleans, operators never convert, no reassignment before §3, every name declared somewhere, proper tail calls, at most 1024 waiting calls, and lists that cannot change size.

*In the course: L1A (§1), L4A (§2), L8A (§3), L11B (§4) · SICPy 1.1, 2.1, 3.1, 4.1.*
