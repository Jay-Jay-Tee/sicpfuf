# Drills: Elements & conditionals

<p class="chapter-goal">Ten warm-ups on numbers, names, functions and conditional expressions in Python §1, and on the rules that make §1 stricter than real Python.</p>

Cover the answer, write yours on paper, then open the toggle. All programs run as Python §1.

## 1. Four division-like operators ★

**Skill:** predict the value of `/`, `//`, `%` and `**`.

```python title="§1"
print(9 / 3)
print(9 // 4)
print(-9 // 4)
print(-9 % 4)
print(9 % -4)
print(2 ** 2 ** 3)
```

??? success "Answer"
    ```text
    3.0
    2
    -3
    3
    -3
    256
    ```

    `/` always gives a float, even when the division is exact. `//` rounds **down** (towards minus infinity), so `-9 // 4` is `-3`, not `-2`. `%` takes the sign of the divisor: `-9 % 4` is `3` because `-9 == 4 * (-3) + 3`. `**` groups from the right: `2 ** 2 ** 3` is `2 ** 8`.

## 2. What gets printed at all? ★

**Skill:** expression statements versus `print`.

```python title="§1"
price = 12
price * 2
print(price + 1)
"hello"
print("total:", price * 3)
```

??? success "Answer"
    ```text
    13
    total: 36
    ```

    A bare expression statement (lines 2 and 4) is evaluated and its value is thrown away: a program prints only what `print` is given. `print` with two arguments puts one space between them. A string printed at top level shows without quotes.

## 3. A chain of conditional expressions ★

**Skill:** how `a if p else b if q else c` groups.

```python title="§1"
def size_label(n):
    return "S" if n < 10 else "M" if n < 100 else "L"

print(size_label(7))
print(size_label(70))
print(size_label(700))
```

??? success "Answer"
    ```text
    S
    M
    L
    ```

    The alternative of the first conditional expression is the whole second one: `"S" if n < 10 else ("M" if n < 100 else "L")`. The predicates are tried from left to right and only one branch is ever evaluated.

## 4. Precedence puzzles ★★

**Skill:** operator precedence (unary minus, `**`, `not`, `and`, `or`).

```python title="§1"
print(-3 ** 2)
print(10 - 4 - 3)
print(2 * 3 + 4 * 5)
print(not 2 > 3 and 1 == 1)
print(1 > 2 or 3 > 2 and False)
```

??? success "Answer"
    ```text
    -9
    3
    26
    True
    False
    ```

    `**` binds tighter than unary minus: `-(3 ** 2)`. `-` groups from the left: `(10 - 4) - 3`. `not` binds tighter than `and`, which binds tighter than `or`: line 4 is `(not (2 > 3)) and (1 == 1)`, line 5 is `(1 > 2) or ((3 > 2) and False)`.

## 5. Strict or not? ★★

**Skill:** spot what Python §1 refuses although real Python accepts it.

Each program below is fine in real Python. Which ones fail in §1, and with which error?

```python title="§1"
print("ab" * 3)
```

??? success "Answer"
    ```text
    TypeError: unsupported operand type(s) for *: str and int
    ```

    Operators are strict in §1: `*` takes two numbers. Repeat a string with a recursive function instead.

```python title="§1"
n = 5
print("big" if n else "zero")
```

??? success "Answer"
    ```text
    TypeError: conditional expression condition must be bool, not int
    ```

    A predicate must be exactly `True` or `False`. Write `n != 0`.

```python title="§1"
print("score: " + 10)
```

??? success "Answer"
    ```text
    TypeError: unsupported operand type(s) for +: str and int
    ```

    `+` joins two strings or adds two numbers, never one of each. Write `"score: " + str(10)`.

```python title="§1"
def is_small(x):
    return x < 5

print(is_small(3) == True)
```

??? success "Answer"
    ```text
    TypeError: unsupported operand type(s) for ==: bool and bool
    ```

    In §1 and §2, `==` cannot compare booleans. `is_small(3)` is already a boolean: write `print(is_small(3))`.

## 6. The branch that never runs ★★

**Skill:** when a program is rejected before it runs, and when an error is avoided because a branch is never evaluated.

Two programs. Each has a "bad" thing in the branch that is not taken. What does each print?

```python title="§1"
def safe_ratio(a, b):
    return 0 if b == 0 else a // b

print(safe_ratio(7, 0))
print(safe_ratio(7, 2))
```

??? success "Answer"
    ```text
    0
    3
    ```

    For `safe_ratio(7, 0)` the predicate is `True`, so `a // b` is never evaluated and there is no division by zero.

```python title="§1"
def careful(b):
    return 0 if b == 0 else undefined_helper(b)

print("start")
print(careful(0))
```

??? success "Answer"
    ```text
    NameNotFoundError: the name 'undefined_helper' is not declared anywhere
    ```

    Not even `start` is printed. Every name must be declared somewhere in the program, and this is checked **before** the program runs, so it does not matter that the branch would never be evaluated.

## 7. One value per name ★★

**Skill:** no reassignment in §1, including parameters.

```python title="§1"
def next_odd(n):
    n = n + 1 if n % 2 == 0 else n + 2
    return n

print(next_odd(4))
```

??? success "Answer"
    ```text
    NameReassignmentError: the name 'n' already has a value
    ```

    A parameter already has a value, so `n = ...` in the body is a reassignment, which §1 does not allow. The program is rejected before it runs. Fix: `return n + 1 if n % 2 == 0 else n + 2`, or pick a new name such as `result`.

## 8. Write it: minutes to a clock string ★★

**Skill:** `//`, `%`, `str` and a conditional expression in one small function.

Write `clock(minutes)` that turns a number of minutes since midnight (0 to 1439) into a string `"h:mm"`. The minutes always have two digits.

??? success "Answer"
    ```python title="§1"
    def clock(minutes):
        h = minutes // 60
        m = minutes % 60
        return str(h) + ":" + ("0" if m < 10 else "") + str(m)

    print(clock(0))
    print(clock(65))
    print(clock(605))
    print(clock(1439))
    ```
    ```text
    0:00
    1:05
    10:05
    23:59
    ```

    `minutes // 60` counts the whole hours and `minutes % 60` is what is left over. A minute value below 10 needs a `"0"` in front. The brackets around the conditional expression matter: without them the whole sum `str(h) + ":" + "0"` would become the consequent.

## 9. Write it: the middle of three ★★

**Skill:** combining built-ins (`max`, `min`) instead of a big conditional.

Write `middle(a, b, c)` that returns the value that is neither the largest nor the smallest (if two are equal, any correct middle value will do). Use no conditional expression.

??? success "Answer"
    ```python title="§1"
    def middle(a, b, c):
        return max(min(a, b), min(max(a, b), c))

    print(middle(1, 2, 3))
    print(middle(9, 4, 6))
    print(middle(5, 8, 2))
    print(middle(7, 7, 1))
    ```
    ```text
    2
    6
    5
    7
    ```

    `min(a, b)` and `max(a, b)` put the first two in order. Now check the three places `c` can be:

    - `c` above both: `min(max(a, b), c)` is `max(a, b)`, and that is the middle.
    - `c` below both: `min(max(a, b), c)` is `c`, so the outer `max` picks `min(a, b)`, the middle.
    - `c` between them: `min(max(a, b), c)` is `c`, and the outer `max` keeps `c`.

    Going through every case like this is how you convince yourself a formula is right.

## 10. Write it: a predicate with a twist ★★★

**Skill:** writing a predicate as one boolean expression; `and`/`or` with booleans only.

A year is a leap year if it is divisible by 4, except years divisible by 100, which are leap years only if they are also divisible by 400. Write `is_leap(year)` with one return statement and no conditional expression.

??? success "Answer"
    ```python title="§1"
    def is_leap(year):
        return year % 400 == 0 or (year % 4 == 0 and year % 100 != 0)

    print(is_leap(2024))
    print(is_leap(2026))
    print(is_leap(1900))
    print(is_leap(2000))
    ```
    ```text
    True
    False
    False
    True
    ```

    Every operand of `or` and `and` here is a comparison, so it is a boolean, as §1 requires. The order is a choice: the rare case (`% 400`) first, then the usual rule. Test the four kinds of year: ordinary, leap, century, and a multiple of 400.

*In the course: L1A, L1B, L3B (logical operators) · SICPy 1.1.1–1.1.6.*
