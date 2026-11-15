# Drills: Higher-order functions & scope

<p class="chapter-goal">Ten problems on functions as arguments and results, lambda expressions, short-circuit <code>and</code>/<code>or</code>, and finding the declaration each name refers to.</p>

The one scope rule to use everywhere: **a name refers to the closest surrounding declaration, looking at where the code is written** (lexical scoping), not at who called it. All programs run as Python §1.

## 1. Which y? ★

**Skill:** lexical scoping: a function sees the names around its definition, not around its caller.

```python title="§1"
x = 10
y = 1

def f(x):
    return x + y

def g(y):
    return f(y * 2) + x

print(g(3))
```

??? success "Answer"
    ```text
    17
    ```

    In `g(3)`, `y` is 3, so `f(6)` is called. Inside `f`, `x` is f's parameter (6), and `y` is **not** g's parameter: `f` is written at top level, so its `y` is the global `y`, 1. So `f(6)` is 7. Back in `g`, `x` is the global 10. 7 + 10 = 17. If you got 19, you looked up `y` in the caller.

## 2. Twice ★

**Skill:** apply a function that returns a function; know how function values print.

```python title="§1"
def twice(f):
    return lambda x: f(f(x))

print(twice(lambda n: n * 3)(2))
print(twice(lambda s: s + "!")("hi"))
print(twice)
print(twice(abs))
print(abs)
```

??? success "Answer"
    ```text
    18
    hi!!
    <function twice>
    <function (anonymous)>
    <built-in function abs>
    ```

    `twice(g)` is a new function that applies `g` two times: 2 → 6 → 18. `twice(abs)` is the lambda expression's value, which has no name, so it prints as `(anonymous)`. Printing a function shows that it is a function, never its code.

## 3. Compose, in which order? ★★

**Skill:** `compose(f, g)` applies `g` first.

```python title="§1"
def compose(f, g):
    return lambda x: f(g(x))

half = lambda x: x / 2
sub3 = lambda x: x - 3

print(compose(sub3, half)(10))
print(compose(half, sub3)(10))
print(compose(half, compose(half, half))(40))
```

??? success "Answer"
    ```text
    2.0
    3.5
    5.0
    ```

    `compose(sub3, half)(10)` is `sub3(half(10))`: 10 / 2 = 5.0, then 2.0. The other order is `half(sub3(10))`: 7 / 2 = 3.5. Read `compose(f, g)` from right to left, like f(g(x)). `/` gives a float, so every result here is a float.

## 4. A function maker ★★

**Skill:** each call of a maker makes a new, independent function that remembers its argument.

```python title="§1"
def make_multiplier(k):
    return lambda n: n * k

double = make_multiplier(2)
times5 = make_multiplier(5)

print(double(times5(3)))
print(make_multiplier(4)(double(1)))
print(make_multiplier(make_multiplier(3)(3))(2))
```

??? success "Answer"
    ```text
    30
    8
    18
    ```

    `times5(3)` is 15 and `double(15)` is 30. `double` keeps its own `k` (2) even after `times5` was made with `k` 5. In the last line, `make_multiplier(3)(3)` is 9, so the outer maker builds "times 9", applied to 2.

## 5. Write it: curry and uncurry ★★

**Skill:** converting between a two-argument function and a function that returns a function.

Write `curry(f)`, which turns a function of two arguments into one that takes them one at a time, so `curry(f)(a)(b)` is `f(a, b)`. Then write `uncurry(g)`, which does the opposite.

??? success "Answer"
    ```python title="§1"
    def curry(f):
        return lambda a: lambda b: f(a, b)

    def uncurry(g):
        return lambda a, b: g(a)(b)

    minus = lambda a, b: a - b
    print(curry(minus)(10)(3))
    take_from_100 = curry(minus)(100)
    print(take_from_100(1), take_from_100(58))
    print(uncurry(curry(minus))(10, 3))
    ```
    ```text
    7
    99 42
    7
    ```

    A lambda expression's body can itself be a lambda expression: `lambda a: lambda b: ...` takes `a`, then returns a function waiting for `b`. Fixing the first argument early (`take_from_100`) is the reason to curry: you get a one-argument function to pass to another function, as curves and `map` need.

## 6. How far does a lambda reach? ★★

**Skill:** lambda precedence: the body of a lambda goes as far right as it can, so a conditional expression after `lambda x:` belongs to the body.

```python title="§1"
f = lambda x: x * 2 if x > 0 else 0
print(f(3), f(-3))

k = lambda x: lambda y: x - y if x > y else y - x
print(k(2)(9))
```

??? success "Answer"
    ```text
    6 0
    7
    ```

    `lambda x: x * 2 if x > 0 else 0` means `lambda x: (x * 2 if x > 0 else 0)`. Function application binds tightest, then the conditional expression, then lambda. Likewise the inner lambda in `k` has the whole conditional as its body: `k(2)(9)` is `9 - 2`.

Now someone adds brackets "to be safe". What happens?

```python title="§1"
g = (lambda x: x * 2) if x > 0 else 0
print(g(3))
```

??? success "Answer"
    ```text
    NameNotFoundError: the name 'x' is not found in the current or enclosing environment(s)
    ```

    The brackets end the lambda after `x * 2`. The predicate `x > 0` is now outside the lambda, where no `x` is declared, so the program is rejected before it runs.

## 7. Short-circuit ★★

**Skill:** `and`/`or` are syntactic forms: `a and b` is `b if a else False`, `a or b` is `True if a else b`.

```python title="§1"
def boom():
    return 1 // 0

print(False and boom())
print(True or boom())
print(True and 5)
print(False or "x")
print(3 > 2 and boom() > 0)
```

??? success "Answer"
    ```text
    False
    True
    5
    x
    ZeroDivisionError: division by zero
    ```

    The right operand is evaluated only when needed: `False and ...` is already `False`, `True or ...` is already `True`, so `boom()` never runs. When it is needed, its value is the result, whatever it is: `True and 5` is `5`. In the last line `3 > 2` is `True`, so `boom() > 0` must be evaluated, and it crashes.

And this one?

```python title="§1"
print(5 and True)
```

??? success "Answer"
    ```text
    TypeError: left operand of 'and' must be bool, not int
    ```

    Only the **last** operand of `and`/`or` may be anything. The left operand plays the role of the predicate, so it must be a boolean.

## 8. Declared, but no value yet ★★

**Skill:** a name assigned anywhere in a function body belongs to the function for the whole body.

What do these two programs print?

```python title="§1"
rate = 2

def cost(n):
    total = n * rate
    rate = 3
    return total

print(cost(5))
```

??? success "Answer"
    ```text
    UnassignedLocalError: cannot access local variable 'rate' where it is not associated with a value
    ```

    `rate = 3` in the body makes `rate` a name of `cost`, from the first line of the body to the last. So the `rate` in `n * rate` is the local one, which has no value yet. It does **not** fall back to the global `rate`.

```python title="§1"
def sign_of(n):
    if n > 0:
        s = "+"
    else:
        t = "-"
    return s

print(sign_of(5))
print(sign_of(-5))
```

??? success "Answer"
    ```text
    +
    UnassignedLocalError: cannot access local variable 's' where it is not associated with a value
    ```

    `s` is in scope in the whole body, but it gets a value only if the first branch runs. For `-5` the other branch runs, and `return s` reads a name that has no value. The scope of a name and whether it has a value yet are two different questions.

## 9. Write it: count_if ★★

**Skill:** a higher-order function with a predicate parameter, as an iterative process.

Write `count_if(pred, a, b)`: how many integers k with a ≤ k ≤ b make `pred(k)` true. Use it to count the multiples of 3 from 1 to 20 and the perfect squares from 1 to 50.

??? success "Answer"
    ```python title="§1"
    def count_if(pred, a, b):
        def go(k, count):
            return count if k > b else go(k + 1, count + 1 if pred(k) else count)
        return go(a, 0)

    print(count_if(lambda k: k % 3 == 0, 1, 20))
    print(count_if(lambda k: math_floor(math_sqrt(k)) ** 2 == k, 1, 50))
    print(count_if(lambda k: True, 5, 4))
    ```
    ```text
    6
    7
    0
    ```

    `pred` is a parameter like any other; applying it is `pred(k)`. `go` sees `pred` and `b` from the surrounding function, so it needs only the changing values as parameters. The recursive call is the whole alternative, so the process is iterative. An empty range (a > b) gives 0.

## 10. Three x's ★★★

**Skill:** link every occurrence of a name to its declaration when parameters shadow each other.

```python title="§1"
x = 1

def f(x):
    def g(y):
        return x + y
    return lambda x: g(x * 10)

print(f(2)(3))
print(f(x)(x))
```

??? success "Answer"
    ```text
    32
    11
    ```

    There are three declarations of `x`: the global one, f's parameter, and the lambda's parameter. The `x` in `g`'s body is written inside `f` but outside the lambda, so it is **f's** parameter. The `x` in `x * 10` is the lambda's. `f(2)(3)`: `g(30)` with f's `x` = 2, so 32. `f(x)(x)` at top level uses the global 1 twice: `g(10)` with f's `x` = 1, so 11.

*In the course: L3A, L3B, L5A (lambda precedence), R3 · SICPy 1.1.6, 1.1.8, 1.3.1, 1.3.2, 1.3.4.*
