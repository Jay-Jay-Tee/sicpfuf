# Drills: Substitution & processes

<p class="chapter-goal">Ten problems on writing substitution traces, telling recursive processes from iterative ones, converting between them, and applicative versus normal order.</p>

How to write a trace in this course: one expression per line, each line one step on from the last. Evaluate the arguments first (applicative order), then replace the application by the body with the parameters replaced by the argument values. The answers below were made by sicpfuf's `--subst`, so you can compare yours line by line. Your trace may skip some of the small steps (such as `1 if False else ...`); the order of the big steps must match.

## 1. Your first trace ★

**Skill:** substitution model with two compound functions.

Write the substitution trace of the last line.

```python
def double(x):
    return x + x

def tile_cost(side):
    return double(side) * side + 1

tile_cost(2 + 1)
```

??? success "Answer"
    ```python title="§1 · --subst"
    def double(x):
        return x + x

    def tile_cost(side):
        return double(side) * side + 1

    tile_cost(2 + 1)
    ```
    ```text
    tile_cost(2 + 1)
    -> tile_cost(3)
    -> double(3) * 3 + 1
    -> (3 + 3) * 3 + 1
    -> 6 * 3 + 1
    -> 18 + 1
    -> 19
    ```

    The argument `2 + 1` becomes `3` **before** the body of `tile_cost` is used (applicative order). Then every `side` in the body becomes `3`. `double(3)` is replaced by its return expression with `x` replaced by `3`. The brackets around `(3 + 3)` keep the meaning of the original expression.

## 2. Recursive or iterative? ★

**Skill:** spot deferred operations by reading the return statement.

For each function, say whether `f(5)` gives rise to a recursive process or an iterative process.

```python
def a(n):
    return 0 if n == 0 else n + a(n - 1)

def b(n, total):
    return total if n == 0 else b(n - 1, total + n)

def c(n):
    return 0 if n == 0 else c(n - 1)

def d(n):
    return 1 if n == 0 else 2 * d(n - 1)
```

??? success "Answer"
    `a` and `d` give recursive processes; `b` and `c` give iterative processes. `trace` shows it: `→` is a call the caller waits for, `↻` is a tail call that replaces its caller.

    ```python title="§1"
    def a(n):
        return 0 if n == 0 else n + a(n - 1)

    def b(n, total):
        return total if n == 0 else b(n - 1, total + n)

    print(trace(a, 2))
    print(trace(b, 2, 0))
    ```
    ```text
    → a(2)
    │  → a(1)
    │  │  → a(0)
    │  │  ← 0
    │  ← 1
    ← 3
    3
    → b(2, 0)
    ↻ b(1, 2)
    ↻ b(0, 3)
    ← 3
    3
    ```

    In `a` and `d` something is left to do after the recursive call returns (`n + ...`, `2 * ...`): a **deferred operation**. In `b` and `c` the recursive call is the whole return expression, so nothing waits. A recursive *function* can give either kind of *process*.

## 3. Trace a recursive process ★★

**Skill:** write a trace where deferred operations pile up.

```python
def count_digits(n):
    return 1 if n < 10 else 1 + count_digits(n // 10)

count_digits(507)
```

??? success "Answer"
    ```python title="§1 · --subst"
    def count_digits(n):
        return 1 if n < 10 else 1 + count_digits(n // 10)

    count_digits(507)
    ```
    ```text
    count_digits(507)
    -> 1 if 507 < 10 else 1 + count_digits(507 // 10)
    -> 1 if False else 1 + count_digits(507 // 10)
    -> 1 + count_digits(507 // 10)
    -> 1 + count_digits(50)
    -> 1 + (1 if 50 < 10 else 1 + count_digits(50 // 10))
    -> 1 + (1 if False else 1 + count_digits(50 // 10))
    -> 1 + (1 + count_digits(50 // 10))
    -> 1 + (1 + count_digits(5))
    -> 1 + (1 + (1 if 5 < 10 else 1 + count_digits(5 // 10)))
    -> 1 + (1 + (1 if True else 1 + count_digits(5 // 10)))
    -> 1 + (1 + 1)
    -> 1 + 2
    -> 3
    ```

    The lines grow to the right (the `1 + (1 + ...` waiting in front), then shrink: the typical shape of a recursive process. The number of `1 +` waiting at the widest point is the space used.

## 4. Trace an iterative process ★★

**Skill:** write a trace where the lines stay the same length.

```python
def digits_iter(n, count):
    return count if n < 10 else digits_iter(n // 10, count + 1)

digits_iter(507, 1)
```

??? success "Answer"
    ```python title="§1 · --subst"
    def digits_iter(n, count):
        return count if n < 10 else digits_iter(n // 10, count + 1)

    digits_iter(507, 1)
    ```
    ```text
    digits_iter(507, 1)
    -> 1 if 507 < 10 else digits_iter(507 // 10, 1 + 1)
    -> 1 if False else digits_iter(507 // 10, 1 + 1)
    -> digits_iter(507 // 10, 1 + 1)
    -> digits_iter(50, 1 + 1)
    -> digits_iter(50, 2)
    -> 2 if 50 < 10 else digits_iter(50 // 10, 2 + 1)
    -> 2 if False else digits_iter(50 // 10, 2 + 1)
    -> digits_iter(50 // 10, 2 + 1)
    -> digits_iter(5, 2 + 1)
    -> digits_iter(5, 3)
    -> 3 if 5 < 10 else digits_iter(5 // 10, 3 + 1)
    -> 3 if True else digits_iter(5 // 10, 3 + 1)
    -> 3
    ```

    Every application line is only `digits_iter(n, count)` with new numbers: no operation waits outside the call. The whole state of the computation is in the two arguments.

## 5. Recursive to iterative ★★

**Skill:** add an accumulator parameter.

This function adds the first `n` odd numbers, 1 + 3 + ... + (2n − 1). It gives rise to a recursive process. Write `sum_odds_iter(n)` that gives the same results with an iterative process.

```python
def sum_odds(n):
    return 0 if n == 0 else (2 * n - 1) + sum_odds(n - 1)
```

??? success "Answer"
    ```python title="§1"
    def sum_odds(n):
        return 0 if n == 0 else (2 * n - 1) + sum_odds(n - 1)

    def sum_odds_iter(n):
        def go(k, total):
            return total if k == 0 else go(k - 1, total + (2 * k - 1))
        return go(n, 0)

    print(sum_odds(4), sum_odds_iter(4))
    measure(sum_odds, 500)
    measure(sum_odds_iter, 500)
    ```
    ```text
    16 16
    [measure] sum_odds(500): 501 calls, 8,006 steps, at most 501 waiting at once
    [measure] sum_odds_iter(500): 502 calls, 8,512 steps, at most 1 waiting at once
    ```

    The deferred `(2 * n - 1) + ...` is done **now** and added to `total`, which is passed on. `measure` confirms the space: hundreds of calls waiting for the recursive version, at most two (the outer call and the current `go`) for the iterative one. Addition does not care about order, so adding from the top down gives the same sum.

## 6. Iterative to recursive ★★

**Skill:** remove the accumulator; let the deferred operation do its work.

`bin_iter(n, "")` builds the binary digits of `n` as a string with an iterative process. Write `bin_string(n)` with no accumulator.

```python
def bin_iter(n, acc):
    return str(n) + acc if n < 2 else bin_iter(n // 2, str(n % 2) + acc)
```

??? success "Answer"
    ```python title="§1"
    def bin_iter(n, acc):
        return str(n) + acc if n < 2 else bin_iter(n // 2, str(n % 2) + acc)

    def bin_string(n):
        return str(n) if n < 2 else bin_string(n // 2) + str(n % 2)

    print(bin_iter(6, ""), bin_string(6))
    print(bin_iter(13, ""), bin_string(13))
    ```
    ```text
    110 110
    1101 1101
    ```

    The last digit `str(n % 2)` is found first. The iterative version puts it in front of what it has so far; the recursive version waits until the other digits are built, then puts it at the end. Unlike addition, joining strings depends on order, so check which side each piece goes on.

## 7. The sneaky deferred operation ★★

**Skill:** a single `not` in front of a recursive call is a deferred operation.

Does `is_even(n)` give rise to a recursive or an iterative process? What about `is_even2`?

```python
def is_even(n):
    return True if n == 0 else not is_even(n - 1)

def is_even2(n):
    return True if n == 0 else is_odd2(n - 1)

def is_odd2(n):
    return False if n == 0 else is_even2(n - 1)
```

??? success "Answer"
    ```python title="§1"
    def is_even(n):
        return True if n == 0 else not is_even(n - 1)

    def is_even2(n):
        return True if n == 0 else is_odd2(n - 1)

    def is_odd2(n):
        return False if n == 0 else is_even2(n - 1)

    measure(is_even, 300)
    measure(is_even2, 300)
    ```
    ```text
    [measure] is_even(300): 301 calls, 3,306 steps, at most 301 waiting at once
    [measure] is_even2(300): 301 calls, 3,006 steps, at most 1 waiting at once
    ```

    `is_even` is a recursive process: the `not` must be applied after the recursive call returns, so 300 `not`s pile up. `is_even2` and `is_odd2` call each other, and each call is the whole return expression: an iterative process, even though two functions take turns.

## 8. Applicative versus normal order ★★

**Skill:** say what each order does, and count the work.

(a) What happens when this runs in Python §1? What would happen under normal order reduction?

```python title="§1"
def pick(flag, a, b):
    return a if flag else b

print(pick(True, 1, 1 // 0))
```

??? success "Answer"
    ```text
    ZeroDivisionError: division by zero
    ```

    Python uses applicative order: all three arguments are evaluated before the body, and `1 // 0` fails. Under normal order, `pick(True, 1, 1 // 0)` becomes `1 if True else 1 // 0`, and the alternative is never evaluated: the result would be `1`. This is also why the conditional expression has to be a special form, not a function.

(b) How many multiplications does `sq(sq(3))` do in each order?

```python
def sq(x):
    return x * x
```

??? success "Answer"
    Applicative order: two.

    ```python title="§1 · --subst"
    def sq(x):
        return x * x

    sq(sq(3))
    ```
    ```text
    sq(sq(3))
    -> sq(3 * 3)
    -> sq(9)
    -> 9 * 9
    -> 81
    ```

    Normal order: three. The argument expression is copied in unevaluated, so `sq(3)` is computed twice:

    ```
    sq(sq(3))
    -> sq(3) * sq(3)
    -> (3 * 3) * sq(3)
    -> 9 * sq(3)
    -> 9 * (3 * 3)
    -> 9 * 9
    -> 81
    ```

    Both orders give the same value here. Normal order can do repeated work, but it can also skip work that is never needed, as in (a).

## 9. Half and half ★★★

**Skill:** a process can be partly recursive; count what waits.

Is the process of `g(10)` recursive or iterative? How many calls are waiting at the widest point?

```python
def g(n):
    return 0 if n == 0 else g(n - 1) if n % 2 == 0 else 1 + g(n - 1)
```

??? success "Answer"
    ```python title="§1"
    def g(n):
        return 0 if n == 0 else g(n - 1) if n % 2 == 0 else 1 + g(n - 1)

    print(trace(g, 4))
    measure(g, 10)
    measure(g, 100)
    ```
    ```text
    → g(4)
    ↻ g(3)
    │  → g(2)
    │  ↻ g(1)
    │  │  → g(0)
    │  │  ← 0
    │  ← 1
    ← 2
    2
    [measure] g(10): 11 calls, 176 steps, at most 6 waiting at once
    [measure] g(100): 101 calls, 1,706 steps, at most 51 waiting at once
    ```

    For even `n` the recursive call is a tail call (`↻`, nothing waits); for odd `n` a `1 +` is deferred. So the process is recursive (space still grows with n), but only every second call leaves a deferred operation: 5 for `g(10)`, plus the very first call, gives 6. Space is about n/2, which is still Θ(n).

## 10. When the order of work matters ★★★

**Skill:** convert to an iterative process when the deferred operation is not "the same each time".

`h(3)` is `123`, `h(5)` is `12345`. Write an iterative version.

```python
def h(n):
    return 0 if n == 0 else 10 * h(n - 1) + n
```

??? success "Answer"
    ```python title="§1"
    def h(n):
        return 0 if n == 0 else 10 * h(n - 1) + n

    def h_iter(n):
        def go(k, acc):
            return acc if k > n else go(k + 1, 10 * acc + k)
        return go(1, 0)

    print(h(5), h_iter(5))
    print(h(0), h_iter(0))
    ```
    ```text
    12345 12345
    0 0
    ```

    In the recursive process the deferred operations run from the inside out: first for `n = 1`, last for `n = 5`. An accumulator must do the same work in the same order, so the counter `k` has to count **up** from 1 to `n`, not down. Counting down (`go(n - 1, 10 * acc + n)`) would give `54321`. Always ask: in which order did the deferred operations happen?

*In the course: L2A, R2, S3 · SICPy 1.1.5, 1.2.1.*
