# Scope & higher-order functions

<p class="chapter-goal">One page: link every name to its declaration, and read or write functions that take and return functions.</p>

## Scoping rules

1. **Declarations are mandatory.** Every name must be declared somewhere in the program, or the program is rejected before it runs (`NameNotFoundError`), even if the line would never run.
2. **Four forms of declaration:**
    1. primitive (pre-declared) names, including names brought in by `from m import a`;
    2. declaration assignments `x = ...`;
    3. parameters of a function definition or a lambda expression;
    4. the function name of a function definition (`def f` declares `f` as if `f = ...`).
3. **Lexical scoping:** a name occurrence refers to the **closest surrounding declaration** of that name. Look in the innermost function body (and its parameters) first, then the next one out, then the program, then the pre-declared names.
4. **Scope of a declaration** = the whole body of the immediately surrounding function (or the whole program at top level). A parameter's scope is its function's body.
5. **In scope but unassigned.** A name assigned anywhere in a function body is local to the WHOLE body, even before the assignment line and even if the assignment is in a branch that does not run. Reading it before it has a value is an error. It does NOT fall back to an outer name.

Rule 3 at work: three declarations of `k`, three different values.

```python title="§1"
k = 100

def outer(k):
    def inner(x):
        return x + k
    return inner(1)

print(outer(10))
print((lambda k: k * 2)(7))
print(k)
```
```text title="Output"
11
14
100
```

In `inner`, `k` is not declared, so look one level out: `outer`'s parameter `k` (10). The global `k` is shadowed there.

Rule 5 at work: `rate` is assigned in the body, so it is local everywhere in the body. The global `rate` is never seen.

```python title="§1"
rate = 2

def price(n):
    total = n * rate
    rate = 3
    return total

print(price(5))
```
```text
UnassignedLocalError: cannot access local variable 'rate' where it is not associated with a value
```

Rule 1 at work: `missing` is declared nowhere, so nothing runs at all, not even line 1.

```python title="§1"
print("hello")

def never_called():
    return missing + 1
```
```text
NameNotFoundError: the name 'missing' is not found in the current or enclosing environment(s)
```

## Lambda expressions

`lambda x, y: x + y` is a function value whose body is ONE return expression (no `return` keyword, no statements).
`f = lambda x: x * x` and `def f(x): return x * x` give the same kind of function.

**Precedence** (strongest first): function application, then operators, then the conditional expression, then lambda. So the body of a lambda extends as far right as possible:

```python title="§1"
f = lambda x: x + 1 if x > 0 else 0
print(f(5), f(-5))
```
```text title="Output"
6 0
```

The body is the whole conditional expression `x + 1 if x > 0 else 0`. To make a conditional choose between two functions, put brackets around the lambdas.

## Functions as arguments and as results

A **higher-order function** takes a function as an argument or returns one.

```python title="§1"
def twice(f):
    return lambda x: f(f(x))

def make_adder(n):
    return lambda x: x + n

add3 = make_adder(3)
print(add3(10))
print(twice(add3)(10))
print(twice(twice)(add3)(0))
```
```text title="Output"
13
16
12
```

Each call of `make_adder` makes a new function that remembers its own `n`. `twice(twice)` applies `f` four times.

**Currying**: turn a function of two arguments into a function that takes one argument and returns a function for the other. `add(2, 5)` becomes `add_c(2)(5)`.

```python title="§1"
def curry(f):
    return lambda a: lambda b: f(a, b)

def compose(f, g):
    return lambda x: f(g(x))

times = curry(lambda a, b: a * b)
double = times(2)
inc = lambda x: x + 1
print(compose(double, inc)(5))
print(compose(inc, double)(5))
```
```text title="Output"
12
11
```

`compose(f, g)` applies `g` FIRST, then `f`. Order matters: (5 + 1) × 2 = 12, but 5 × 2 + 1 = 11.

## The standard HOF patterns

| Pattern | Shape | Example |
|---|---|---|
| general sum | `sum(term, a, next, b)` adds `term(a)`, `term(next(a))` ... up to b | sum of cubes, sum of odd numbers |
| repeat | `repeat(f, n)` returns `f` applied n times | `repeat(lambda x: x * 2, 10)(1)` is 1024 |
| maker | a function returning a lambda that uses its parameter | `make_adder`, a line with slope m |
| compose / twice | combine functions into a new function | `compose(f, g)` |
| transform a function | takes `f`, returns a changed `f` | numerical derivative, curve transformations |
| map / filter / reduce | apply to each llist element | see [llists](llists.md) |

The general sum, written once and reused:

```python title="§1"
def sum_terms(term, a, next, b):
    return 0 if a > b else term(a) + sum_terms(term, next(a), next, b)

print(sum_terms(lambda x: x * x, 1, lambda x: x + 1, 4))
print(sum_terms(lambda x: x, 1, lambda x: x + 2, 9))
```
```text title="Output"
30
25
```

## How to answer this in the exam

1. **"Which declaration does this occurrence refer to?"**: start at the occurrence, go outward box by box (lambda, function body, program). The first box that declares the name wins. A parameter counts as a declaration.
2. **"What does this print?"** with HOFs: name each intermediate function in words ("`twice(add3)` adds 6"), then apply.
3. **"Write `f` such that `f(a)(b)` ..."**: `def f(a): return lambda b: ...`.
4. Check every lambda's body boundary with the precedence rule.
5. Count the arguments: `make_adder(3)` is a function, `make_adder(3)(4)` is a number.

## Top traps

- A local name read before its assignment (rule 5). It does not fall back to the global.
- `compose(f, g)` runs `g` first.
- Forgetting that a function value is not called: `print(add3)` prints `<function (anonymous)>`, not a number.
- `lambda x: return x` is a syntax error: a lambda has no statements.
- A name used only in code that never runs must still be declared.

*In the course: L3A, L3B, L5A · SICPy 1.1.8, 1.3.1, 1.3.2, 1.3.4.*
