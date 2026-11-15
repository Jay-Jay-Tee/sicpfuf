# 3. The substitution model and recursion

<p class="chapter-goal">Evaluate any §1 program by hand, write functions that use themselves, and tell a recursive process from an iterative one.</p>

!!! abstract "The big idea, in plain words"
    Imagine evaluating a program on paper with a pencil and an eraser. Find a function application,
    rub it out, and write the function's body in its place with the arguments filled in. Repeat until
    one value is left. That is the **substitution model**. It also explains recursion: a function
    that uses itself just leaves another application on the paper, which you rewrite in the same way.
    How the paper *looks* while you do this (a long, growing line, or a line that stays short) tells
    you whether the process is **recursive** or **iterative**.

## The substitution model

These four rules are all you need to evaluate a Python §1 program by hand:

1. **Primitive expression** (a number, a string, `True`): its value is itself.
2. **Operator combination**: evaluate the operands, then apply the operator.
3. **Declaration assignment** `name = e`: evaluate `e`, then replace `name` by that value in the rest
   of the program.
4. **Function application** `f(a, b)`: evaluate the function expression and the arguments. If `f` is
   primitive, apply it. If `f` is compound, replace the application by its **return expression**,
   with each parameter replaced by its argument's value.

```python title="§1"
def box_price(weight):
    return 3 + 2 * weight

def order_total(a, b):
    return box_price(a) + box_price(b + 1)

print(order_total(2, 1 + 3))
```
```text title="Output"
20
```

??? example "X-ray: `--subst` rewrites the program one step at a time"
    ```python title="§1 · --subst"
    def box_price(weight):
        return 3 + 2 * weight

    def order_total(a, b):
        return box_price(a) + box_price(b + 1)

    order_total(2, 1 + 3)
    ```
    ```text title="Output"
    order_total(2, 1 + 3)
    -> order_total(2, 4)
    -> box_price(2) + box_price(4 + 1)
    -> 3 + 2 * 2 + box_price(4 + 1)
    -> 3 + 4 + box_price(4 + 1)
    -> 7 + box_price(4 + 1)
    -> 7 + box_price(5)
    -> 7 + (3 + 2 * 5)
    -> 7 + (3 + 10)
    -> 7 + 13
    -> 20
    ```
    The very first step turns `1 + 3` into `4`: arguments are evaluated **before** the body is
    used. Then `order_total(2, 4)` is replaced by its return expression with `a` as `2` and `b` as
    `4`.

!!! note "A model, not a machine"
    The substitution model is a way to *think*. Real interpreters do not rewrite text. It works
    perfectly for §1 and §2, where names never change. From §3 on, names can be reassigned, and you
    will need the **environment model** (chapter 14).

## Applicative order and normal order

Python evaluates the arguments first and then substitutes their values. This is **applicative
order reduction**. The alternative is **normal order reduction**: substitute the argument
*expressions* unevaluated, and only work them out when a primitive operator needs their value.

For `order_total(2, 1 + 3)`, normal order would give:

```text
order_total(2, 1 + 3)
-> box_price(2) + box_price((1 + 3) + 1)
-> (3 + 2 * 2) + (3 + 2 * ((1 + 3) + 1))
-> 7 + (3 + 2 * 5)
-> 20
```

Same answer, different steps. The two orders can disagree when an argument cannot be evaluated:

```python title="§1"
def first(a, b):
    return a

print(first(1, 1 // 0))
```
```text title="Output"
ZeroDivisionError at line 4
    print(first(1, 1 // 0))
ZeroDivisionError: division by zero
sicpfuf hint: check the divisor before dividing, for example with a base case `if n == 0`.
```

Under normal order, `b` is never used, so `1 // 0` would never be computed and the answer would be
`1`. Python is applicative, so it computes `1 // 0` first and stops. (Chapter 18 builds an evaluator
that uses normal order.)

## Recursion by wishful thinking

A function is **recursive** when its body applies the function itself. The recipe, called
**wishful thinking**:

1. Find the **base case**: the smallest problem, whose answer you know straight away.
2. *Wish* that the function already works for a slightly smaller problem.
3. Use that wish to solve the problem in front of you.

Example: count the digits of a positive integer. A number below 10 has 1 digit (base case). For a
bigger number, wish that `count_digits(n // 10)` works: chopping off the last digit leaves one digit
fewer, so add 1.

```python title="§1"
def count_digits(n):
    return 1 if n < 10 else 1 + count_digits(n // 10)

print(count_digits(7), count_digits(507), count_digits(2 ** 64))
```
```text title="Output"
1 3 20
```

??? example "X-ray: `count_digits(507)` under the substitution model"
    ```python title="§1 · --subst"
    def count_digits(n):
        return 1 if n < 10 else 1 + count_digits(n // 10)

    count_digits(507)
    ```
    ```text title="Output"
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
    The conditional expression is what stops the recursion: when `5 < 10` is `True`, the branch with
    the recursive application is thrown away.

!!! warning "Trap: no base case, no end"
    A program must describe *every* step. Without a base case, the function keeps applying itself
    and the machine eventually gives up.

    ```python title="§1"
    def total_down(n):
        return n + total_down(n - 1)

    print(total_down(3))
    ```
    ```text
    RecursionError: maximum recursion depth exceeded
    ```

## Factorial, two ways

The factorial of n is n! = n × (n − 1) × … × 1, and 0! = 1. Straight from that definition:

```python title="§1"
def factorial(n):
    return 1 if n == 0 else n * factorial(n - 1)

print(factorial(5))
```
```text title="Output"
120
```

A second version carries the answer-so-far in an extra parameter, the **accumulator** `product`.
Each step multiplies `n` into `product` and counts `n` down:

```python title="§1"
def fact_iter(n, product):
    return product if n == 0 else fact_iter(n - 1, n * product)

def factorial(n):
    return fact_iter(n, 1)

print(factorial(5))
```
```text title="Output"
120
```

Same answer. Now compare how the two evolve:

=== "Recursive process"

    ```python title="§1 · --subst"
    def factorial(n):
        return 1 if n == 0 else n * factorial(n - 1)

    factorial(3)
    ```
    ```text title="Output"
    factorial(3)
    -> 1 if 3 == 0 else 3 * factorial(3 - 1)
    -> 1 if False else 3 * factorial(3 - 1)
    -> 3 * factorial(3 - 1)
    -> 3 * factorial(2)
    -> 3 * (1 if 2 == 0 else 2 * factorial(2 - 1))
    -> 3 * (1 if False else 2 * factorial(2 - 1))
    -> 3 * (2 * factorial(2 - 1))
    -> 3 * (2 * factorial(1))
    -> 3 * (2 * (1 if 1 == 0 else 1 * factorial(1 - 1)))
    -> 3 * (2 * (1 if False else 1 * factorial(1 - 1)))
    -> 3 * (2 * (1 * factorial(1 - 1)))
    -> 3 * (2 * (1 * factorial(0)))
    -> 3 * (2 * (1 * (1 if 0 == 0 else 0 * factorial(0 - 1))))
    -> 3 * (2 * (1 * (1 if True else 0 * factorial(0 - 1))))
    -> 3 * (2 * (1 * 1))
    -> 3 * (2 * 1)
    -> 3 * 2
    -> 6
    ```

=== "Iterative process"

    ```python title="§1 · --subst"
    def fact_iter(n, product):
        return product if n == 0 else fact_iter(n - 1, n * product)

    fact_iter(3, 1)
    ```
    ```text title="Output"
    fact_iter(3, 1)
    -> 1 if 3 == 0 else fact_iter(3 - 1, 3 * 1)
    -> 1 if False else fact_iter(3 - 1, 3 * 1)
    -> fact_iter(3 - 1, 3 * 1)
    -> fact_iter(2, 3 * 1)
    -> fact_iter(2, 3)
    -> 3 if 2 == 0 else fact_iter(2 - 1, 2 * 3)
    -> 3 if False else fact_iter(2 - 1, 2 * 3)
    -> fact_iter(2 - 1, 2 * 3)
    -> fact_iter(1, 2 * 3)
    -> fact_iter(1, 6)
    -> 6 if 1 == 0 else fact_iter(1 - 1, 1 * 6)
    -> 6 if False else fact_iter(1 - 1, 1 * 6)
    -> fact_iter(1 - 1, 1 * 6)
    -> fact_iter(0, 1 * 6)
    -> fact_iter(0, 6)
    -> 6 if 0 == 0 else fact_iter(0 - 1, 0 * 6)
    -> 6 if True else fact_iter(0 - 1, 0 * 6)
    -> 6
    ```

In the first trace the line grows: `3 * (2 * (1 * ...))`. Those multiplications are **deferred
operations**: they must wait until the inner application returns. Then the line shrinks again. In
the second trace every line is just one `fact_iter(...)` application with different numbers. There
is nothing waiting.

## Recursive and iterative processes

| | **Recursive process** | **Iterative process** |
|---|---|---|
| Shape of the trace | grows, then shrinks | stays the same width |
| Deferred operations | pile up, one per step | none |
| The state lives in | the parameters *and* the pending work | the parameters only |
| Typical code | `n * f(n - 1)` | `f(n - 1, n * acc)` |

The test: after the recursive application returns, is there anything left to do? If the recursive
application is the whole return expression (`return f(...)`), it is a **tail call** and the process
is iterative. If its result is still added, multiplied, wrapped, the process is recursive.

!!! warning "Trap: a recursive *function* can give an iterative *process*"
    `fact_iter` is a recursive function: its body applies `fact_iter`. Yet the process it gives is
    iterative. "Recursive" describes the *code*; "recursive process" and "iterative process" describe
    how the *computation unfolds*. Exam questions are careful about this; be careful too.

??? example "X-ray: `trace` shows the difference at a glance"
    `→` is an application that the caller must wait for. `↻` is a tail call: it *replaces* the
    caller, so nothing piles up.

    ```python title="§1"
    def factorial(n):
        return 1 if n == 0 else n * factorial(n - 1)

    def fact_iter(n, product):
        return product if n == 0 else fact_iter(n - 1, n * product)

    print(trace(factorial, 4))
    print(trace(fact_iter, 4, 1))
    ```
    ```text title="Output"
    → factorial(4)
    │  → factorial(3)
    │  │  → factorial(2)
    │  │  │  → factorial(1)
    │  │  │  │  → factorial(0)
    │  │  │  │  ← 1
    │  │  │  ← 1
    │  │  ← 2
    │  ← 6
    ← 24
    24
    → fact_iter(4, 1)
    ↻ fact_iter(3, 4)
    ↻ fact_iter(2, 12)
    ↻ fact_iter(1, 24)
    ↻ fact_iter(0, 24)
    ← 24
    24
    ```

## Time and space

How much work does a process do? Two measures:

- **Time**: the number of steps (lines in the substitution trace).
- **Space**: how much must be remembered at once. For a recursive process, that is the number of
  deferred operations.

For both factorials, the time grows in proportion to `n`. The space differs: the recursive version
remembers `n` pending multiplications, the iterative one remembers nothing extra. You see it when
`n` gets large. Here is a fresh example: the sum of the first `n` odd numbers (which is always n²):

```python title="§1"
def sum_odds(n):
    return 0 if n == 0 else (2 * n - 1) + sum_odds(n - 1)

def sum_odds_iter(n, total):
    return total if n == 0 else sum_odds_iter(n - 1, total + 2 * n - 1)

print(sum_odds(1000))
print(sum_odds_iter(100000, 0))
print(sum_odds(1100))
```
```text
1000000
10000000000
RecursionError: maximum recursion depth exceeded
```

The iterative version runs 100 000 steps without trouble. The recursive one fails just above 1000,
because more than 1024 applications are waiting at once. Chapter 4 makes "grows in proportion to"
precise.

!!! note "Python §1 vs real Python"
    The course language (and sicpfuf) runs a tail call without keeping the caller waiting, so an
    iterative process needs no extra space however long it runs. Real Python does not do this: in
    CPython, `sum_odds_iter(100000, 0)` also crashes with a RecursionError. The course's reasoning
    about iterative processes is about the course language.

## Takeaways

- **Substitution model**: replace an application by the function's return expression with the
  parameters replaced by the argument values. Repeat.
- Python uses **applicative order**: arguments first. **Normal order** substitutes unevaluated
  argument expressions.
- **Wishful thinking**: base case, then assume the smaller problem is solved and use it.
- Every recursion needs a base case, chosen by a conditional expression.
- **Recursive process**: deferred operations pile up, the trace grows then shrinks.
- **Iterative process**: the recursive application is a tail call; the state is all in the
  parameters (often an **accumulator**).
- A recursive *function* can give either kind of *process*.

## Check yourself

1. Is the process of `mystery` recursive or iterative? What does it print?

    ```python title="§1"
    def mystery(n, acc):
        return acc if n == 0 else mystery(n - 1, acc + n * n)

    print(mystery(3, 0))
    ```

    ??? success "Answer"
        ```text
        14
        ```
        Iterative: `mystery(...)` is the whole return expression, so nothing is deferred. It adds
        3² + 2² + 1² into `acc`.

2. Same question for `twice_n`:

    ```python title="§1"
    def twice_n(n):
        return 0 if n == 0 else twice_n(n - 1) + 2

    print(twice_n(4))
    ```

    ??? success "Answer"
        ```text
        8
        ```
        Recursive: the `+ 2` must wait for `twice_n(n - 1)`. It does not matter that the recursive
        application is written *first*; what matters is that work remains after it returns.

3. Write `power_of_two(n)` (2ⁿ for n ≥ 0) once with a recursive process and once with an iterative
   process. Do not use `**`.

    ??? success "Answer"
        ```python title="§1"
        def power_of_two(n):
            return 1 if n == 0 else 2 * power_of_two(n - 1)

        def power_of_two_iter(n, result):
            return result if n == 0 else power_of_two_iter(n - 1, 2 * result)

        print(power_of_two(10), power_of_two_iter(10, 1))
        ```
        ```text
        1024 1024
        ```

4. Write `repeat_apply(f, n, x)`, which applies `f` to `x` n times, in both styles.

    ??? success "Answer"
        ```python title="§1"
        def add3(x):
            return x + 3

        def repeat_rec(f, n, x):
            return x if n == 0 else f(repeat_rec(f, n - 1, x))

        def repeat_iter(f, n, x):
            return x if n == 0 else repeat_iter(f, n - 1, f(x))

        print(repeat_rec(add3, 4, 0), repeat_iter(add3, 4, 0))
        ```
        ```text
        12 12
        ```
        In `repeat_rec` the outer `f(...)` is deferred. In `repeat_iter`, `f(x)` is applied *before*
        the recursive application (applicative order), so nothing waits.

5. How many deferred multiplications are waiting at the deepest point of `factorial(5)` (the
   recursive version with base case `n == 0`)?

    ??? success "Answer"
        Five: `5 * (4 * (3 * (2 * (1 * factorial(0)))))`. In general `n` of them, so the space grows
        in proportion to `n`.

*In the course: L2A · SICPy 1.1.5, 1.2.1.*
