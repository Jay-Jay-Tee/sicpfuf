# 1. Elements of programming

<p class="chapter-goal">Write expressions, give them names, wrap them in functions, and let a program choose between two answers.</p>

!!! abstract "The big idea, in plain words"
    Think of a pocket calculator that you can teach new words. Numbers and `+ - * /` are what it knows
    out of the box (**primitives**). You can put pieces together into bigger expressions
    (**combination**). And you can give a name to a value or to a whole calculation and use that name
    from then on (**abstraction**). Every programming language has these three things. This chapter
    shows them in Python §1.

## Expressions and operator combinations

A program is a sequence of **statements**. The simplest statement is an **expression**. A numeral such
as `42` is a **primitive expression**: its value is the number it names. An **operator combination**
puts an operator between two **operands**:

```python title="§1"
print(7 + 5 * 2)
print((7 + 5) * 2)
print(17 / 4)
print(17 // 4)
print(17 % 4)
print(2 ** 10)
```
```text title="Output"
17
24
4.25
4
1
1024
```

The usual rules hold: `*`, `/`, `//` and `%` bind tighter than `+` and `-`, and parentheses group.
Some details matter in exams:

| Operator | Meaning | Example | Value |
|---|---|---|---|
| `/` | division, **always** a float | `8 / 2` | `4.0` |
| `//` | division rounded down (floor) | `-7 // 2` | `-4` |
| `%` | remainder, with the sign of the divisor | `-7 % 3` | `2` |
| `**` | power | `2 ** 3` | `8` |

Integers have no size limit: `2 ** 100` is an exact integer with 31 digits.

To work out a combination, replace one innermost combination by its value, again and again, until a
single value is left.

??? example "X-ray: `--subst` evaluates a combination step by step"
    ```python title="§1 · --subst"
    (6 + 4) * 3 - 12 / 4
    ```
    ```text title="Output"
    (6 + 4) * 3 - 12 / 4
    -> 10 * 3 - 12 / 4
    -> 30 - 12 / 4
    -> 30 - 3.0
    -> 27.0
    ```
    Each line replaces one operator combination whose operands are already values. Notice that
    `12 / 4` becomes `3.0`, a float, so the final answer is a float too.

## A bare expression prints nothing

This surprises everyone once. Writing an expression on its own line makes the computer work out its
value, and then **throws the value away**. Only `print(...)` shows something:

```python title="§1"
1000 * 1000
print("only this line shows up")
```
```text title="Output"
only this line shows up
```

`print` can take several arguments; it prints them separated by single spaces.

```python title="§1"
print("minutes in a week:", 7 * 24 * 60)
```
```text title="Output"
minutes in a week: 10080
```

!!! note "Python §1 vs real Python"
    The interactive prompt (`python3 -m sicpfuf -v 1` with no file) does show the value of an
    expression you type. A program file never does. In exam questions that ask "what does this program
    print?", a bare expression contributes nothing.

## Naming: declaration assignment

A **declaration assignment** `name = expression` evaluates the expression and gives the value a
**name**. From then on, the name stands for that value.

```python title="§1"
tile_side = 30
room_width = 360
room_length = 450
tiles_across = room_width // tile_side
tiles_down = room_length // tile_side
print(tiles_across * tiles_down)
```
```text title="Output"
180
```

The rule for working this out by hand: evaluate the right-hand side, then replace the name by its
value everywhere below. Names are the simplest **means of abstraction**: `tiles_across` is easier to
read than `360 // 30`, and if the room changes you edit one line.

Some names are **pre-declared** (also called primitive or built-in). Constants such as `math_pi` and
functions such as `math_sqrt`, `abs`, `max` exist in every program without you declaring them. They
are Python's math module with `math_` in front:

```python title="§1"
radius = 5
print(math_pi * radius * radius)
print(math_sqrt(2))
print(max(3, 9), abs(-4))
```
```text title="Output"
78.53981633974483
1.4142135623730951
9 4
```

## Functions

A **function definition** gives a name to a whole calculation, with holes in it called
**parameters**. Its **body** is indented under the `def` line. For now the body is a single
**return statement**: the keyword `return` followed by the **return expression**.

```python title="§1"
def square(x):
    return x * x

def hypotenuse(a, b):
    return math_sqrt(square(a) + square(b))

print(square(12))
print(hypotenuse(5, 12))
```
```text title="Output"
144
13.0
```

`square(12)` is a **function application**: `square` is the function expression and `12` is the
**argument**. To apply a **compound function** (one you defined), evaluate the arguments, then
evaluate the body with each parameter replaced by its argument. `hypotenuse` uses `square` as a
building block without caring how `square` works inside. That is **functional abstraction**: a
function is a black box with a name.

??? example "X-ray: what `hypotenuse(5, 12)` does"
    ```python title="§1 · --subst"
    def square(x):
        return x * x

    def hypotenuse(a, b):
        return math_sqrt(square(a) + square(b))

    hypotenuse(5, 12)
    ```
    ```text title="Output"
    hypotenuse(5, 12)
    -> math_sqrt(square(5) + square(12))
    -> math_sqrt(5 * 5 + square(12))
    -> math_sqrt(25 + square(12))
    -> math_sqrt(25 + 12 * 12)
    -> math_sqrt(25 + 144)
    -> math_sqrt(169)
    -> 13.0
    ```

!!! warning "Trap: forgetting `return`"
    Without `return`, the body works out a value and throws it away, exactly like a bare expression.
    The function then returns `None`.

    ```python title="§1"
    def triple(x):
        x * 3

    print(triple(5))
    ```
    ```text title="Output"
    None
    ```

!!! warning "Trap: the body must be indented"
    The lines of a body must start further right than their `def`. Python uses indentation, not
    brackets, to see where a body ends.

    ```python title="§1"
    def half(x):
    return x / 2
    ```
    ```text title="Output"
    IndentationError at line 2
        return x / 2
        ^
    IndentationError: expected an indented block
    sicpfuf hint: Python uses indentation to group statements. Every line of a block must start at exactly the same column. Use 4 spaces, and never mix tabs and spaces.
    ```

## Booleans and predicates

There are two **boolean** values, `True` and `False`. Comparison operators `<`, `>`, `<=`, `>=`, `==`
and `!=` produce them. A **predicate** is an expression or a function that gives a boolean. By
convention, names of predicate functions start with `is_`:

```python title="§1"
def is_even(n):
    return n % 2 == 0

def is_leap_year(year):
    return year % 4 == 0

print(is_even(10), is_even(7))
print(3 < 2)
print("apple" < "banana")
```
```text title="Output"
True False
False
True
```

(`is_leap_year` ignores the century rule on purpose: you will fix it in "Check yourself".)

## Conditional expressions

A **conditional expression** `consequent if predicate else alternative` chooses between two values.
The predicate is evaluated first. If it is `True`, only the consequent is evaluated; if `False`, only
the alternative. The other part is never touched.

```python title="§1"
def bus_fare(age):
    return 0 if age < 7 else 1 if age < 18 else 2

print(bus_fare(4), bus_fare(12), bus_fare(40))
```
```text title="Output"
0 1 2
```

Chained conditional expressions group to the right, so `bus_fare` reads as "0 if under 7, else (1 if
under 18, else 2)". The conditional expression binds more loosely than any operator, so put it in
parentheses when it is an operand: `10 + (1 if rainy else 0)`.

??? example "X-ray: only one branch is ever evaluated"
    ```python title="§1 · --subst"
    def bus_fare(age):
        return 0 if age < 7 else 1 if age < 18 else 2

    bus_fare(12)
    ```
    ```text title="Output"
    bus_fare(12)
    -> 0 if 12 < 7 else 1 if 12 < 18 else 2
    -> 0 if False else 1 if 12 < 18 else 2
    -> 1 if 12 < 18 else 2
    -> 1 if True else 2
    -> 1
    ```
    After `12 < 7` becomes `False`, the whole consequent `0` disappears and only the alternative is
    kept. This is why a conditional expression can stop a recursion (chapter 3).

## Strings

A **string** is text in quotes, `"like this"` or `'like this'`. `+` joins two strings, and `str(n)`
turns a number into a string. `print` shows a string without its quotes.

```python title="§1"
def greeting(name, hour):
    return ("Good morning, " if hour < 12 else "Good afternoon, ") + name

print(greeting("Mei", 9))
print("Room " + str(101))
```
```text title="Output"
Good morning, Mei
Room 101
```

## Python §1 is strict

Python §1 is a small part of real Python, and it is stricter than real Python in three ways. All three
make programs easier to reason about.

**1. Conditions must be exactly `True` or `False`.** Real Python treats `0`, `""` and `None` as false.
Python §1 does not.

```python title="§1"
items = 3
print("some" if items else "none")
```
```text title="Output"
TypeError at line 2
    print("some" if items else "none")
TypeError: conditional expression condition must be bool, not int
sicpfuf hint: Python §1-§4 are stricter than full Python: a condition must be exactly True or False. Write the comparison out, for example `if n != 0:` or `if not is_none(xs):`.
```

Write the comparison you mean: `"some" if items > 0 else "none"`. The same goes for `==` on booleans:
in Python §1 `done == True` is an error, and plain `done` is what you want.

**2. Operators are strict.** No mixing strings and numbers, no `"ab" * 3`:

```python title="§1"
print("Room " + 101)
```
```text title="Output"
TypeError at line 1
    print("Room " + 101)
TypeError: unsupported operand type(s) for +: str and int
sicpfuf hint: numbers and strings don't mix in §1-§4. Convert with str(n) first, and there is no "ab" * 3.
```

**3. A name gets its value once.** In Python §1 and §2 there is no reassignment. This is what lets you
replace a name by its value when you trace a program.

```python title="§1"
score = 10
score = score + 5
```
```text title="Output"
NameReassignmentError at line 2
    score = score + 5
    ^
NameReassignmentError: the name 'score' already has a value
sicpfuf hint: in Python §1 and §2 a name gets its value ONCE and keeps it. That is what lets you replace a name by its value (the substitution model). Pick a new name instead. (A parameter counts as already having a value, and so does a name assigned in the other branch of an if/else.)
```

!!! warning "Trap: every name must be declared somewhere"
    sicpfuf (and the course's own implementation) checks the whole program before running it. A name
    that is never declared is an error even if the line that uses it would never run:

    ```python title="§1"
    print(1 if True else bonus_points)
    ```
    ```text title="Output"
    NameNotFoundError at line 1
        print(1 if True else bonus_points)
                             ^
    NameNotFoundError: the name 'bonus_points' is not found in the current or enclosing environment(s)
    sicpfuf hint: every name must be declared somewhere: by `name = ...`, by `def name(...)`, as a parameter, or by `from module import name`.
    ```

## Takeaways

- Every language has **primitives**, **means of combination** and **means of abstraction**.
- An operator combination is evaluated by evaluating the operands first, then applying the operator.
  `/` always gives a float, `//` rounds down, `%` takes the sign of the divisor.
- A bare expression statement prints nothing. Only `print` prints.
- `name = expression` is a **declaration assignment**; in §1 a name gets its value once.
- `def f(params): return expression` defines a **compound function**; applying it means evaluating the
  arguments, then the body with the parameters replaced.
- `consequent if predicate else alternative` evaluates the predicate and then exactly one branch.
- Conditions must be booleans, and operators do not mix types.

## Check yourself

1. What does this program print?

    ```python title="§1"
    a = 7
    b = a // 2
    a * b
    print(a % b, a / b)
    ```

    ??? success "Answer"
        ```text
        1 2.3333333333333335
        ```
        `b` is `3`. The line `a * b` prints nothing. `7 % 3` is `1` and `/` always gives a float.

2. Write `is_divisible(n, d)`, a predicate that is `True` when `d` divides `n` exactly.

    ??? success "Answer"
        ```python title="§1"
        def is_divisible(n, d):
            return n % d == 0

        print(is_divisible(12, 4), is_divisible(12, 5))
        ```
        ```text
        True False
        ```

3. Fix `is_leap_year`: a year divisible by 100 is a leap year only if it is also divisible by 400.

    ??? success "Answer"
        ```python title="§1"
        def is_leap_year(year):
            return (year % 400 == 0 if year % 100 == 0
                    else year % 4 == 0)

        print(is_leap_year(2024), is_leap_year(1900), is_leap_year(2000))
        ```
        ```text
        True False True
        ```
        A conditional expression may return a boolean in each branch. (Chapter 6 shows another way,
        with `and` and `or`.)

4. Why is this program rejected? Give two ways to fix it.

    ```python title="§1"
    lives = 3
    lives = lives - 1
    print(lives)
    ```

    ??? success "Answer"
        ```text
        NameReassignmentError: the name 'lives' already has a value
        ```
        In §1 a name gets its value once. Use a new name (`lives_left = lives - 1`), or write a
        function `def lose_life(lives): return lives - 1` and apply it.

5. Without running it: what is the value of `10 - 2 * 3 + 8 // 3`?

    ??? success "Answer"
        ```python title="§1 · --subst"
        10 - 2 * 3 + 8 // 3
        ```
        ```text
        10 - 2 * 3 + 8 // 3
        -> 10 - 6 + 8 // 3
        -> 4 + 8 // 3
        -> 4 + 2
        -> 6
        ```
        `*` and `//` first, then `-` and `+` from left to right.

*In the course: L1A · SICPy 1.1.1–1.1.6.*
