# 4. Orders of growth

<p class="chapter-goal">Say how fast a process slows down as its input grows, with Θ, O and Ω, and check your answer by measuring.</p>

!!! abstract "The big idea, in plain words"
    You are cooking for a party. Whether one dish takes you 20 or 25 minutes hardly matters. What
    matters is what happens when twice as many guests come. If you cook one pot per guest, the work
    doubles. If every guest must shake hands with every other guest, the handshakes quadruple. If
    every new guest doubles the work, you are in trouble. An **order of growth** is that rough answer:
    how the cost of a process grows with the size of its input, ignoring the small print.

## Tree recursion: Fibonacci

The Fibonacci numbers are 0, 1, 1, 2, 3, 5, 8, 13, …: each one is the sum of the two before it. The
definition turns straight into a function that applies itself **twice**:

```python title="§1"
def fib(n):
    return n if n <= 1 else fib(n - 1) + fib(n - 2)

print(fib(10), fib(20))
```
```text title="Output"
55 6765
```

Because each application makes two more, the process branches like a tree. This is **tree
recursion**.

??? example "X-ray: the call tree of `fib(4)`"
    ```python title="§1"
    def fib(n):
        return n if n <= 1 else fib(n - 1) + fib(n - 2)

    print(trace(fib, 4))
    ```
    ```text title="Output"
    → fib(4)
    │  → fib(3)
    │  │  → fib(2)
    │  │  │  → fib(1)
    │  │  │  ← 1
    │  │  │  → fib(0)
    │  │  │  ← 0
    │  │  ← 1
    │  │  → fib(1)
    │  │  ← 1
    │  ← 2
    │  → fib(2)
    │  │  → fib(1)
    │  │  ← 1
    │  │  → fib(0)
    │  │  ← 0
    │  ← 1
    ← 3
    3
    ```
    `fib(2)` is worked out twice, `fib(1)` three times. For bigger `n` the repeated work explodes.

The tree for `fib(n)` has about φⁿ nodes, where φ = (1 + √5) / 2 ≈ 1.618 is the golden ratio. So
the **time** grows like φⁿ. The **space** is different: at any moment only one path from the root
down is waiting, and the tree is `n` levels deep, so the space grows like `n`.

An iterative version keeps the last two numbers in parameters and counts down:

```python title="§1"
def fib_iter(a, b, count):
    return b if count == 0 else fib_iter(a + b, a, count - 1)

def fast_fib(n):
    return fib_iter(1, 0, n)

print(fast_fib(10), fast_fib(20), fast_fib(100))
```
```text title="Output"
55 6765 354224848179261915075
```

## Resource functions

To compare programs, ignore the computer and count. Let **n** be the **problem size** (here, the
argument). A **resource function** r(n) says how much of a resource the process needs for size n:

- **time**: the number of steps;
- **space**: how much must be remembered at once (for now, the deferred operations).

`measure(f, args...)` is a sicpfuf builtin that counts both. "Waiting at once" is the space:

```python title="§1"
def fib(n):
    return n if n <= 1 else fib(n - 1) + fib(n - 2)

def fib_iter(a, b, count):
    return b if count == 0 else fib_iter(a + b, a, count - 1)

measure(fib, 5)
measure(fib, 10)
measure(fib, 15)
measure(fib, 20)
measure(fib_iter, 1, 0, 20)
```
```text title="Output"
[measure] fib(5): 15 calls, 160 steps, at most 5 waiting at once
[measure] fib(10): 177 calls, 1,942 steps, at most 10 waiting at once
[measure] fib(15): 1,973 calls, 21,698 steps, at most 15 waiting at once
[measure] fib(20): 21,891 calls, 240,796 steps, at most 20 waiting at once
[measure] fib_iter(1, 0, 20): 21 calls, 286 steps, at most 1 waiting at once
```

Each time `n` grows by 5, the number of calls of `fib` is multiplied by about 11 (that is φ⁵).
`fib_iter` needs 21 calls for `n = 20`, and only one is ever waiting.

## Θ, O and Ω

The exact counts depend on small details: how you count a step, which base case you chose. An order
of growth throws those details away and keeps the shape.

**Θ (Big Theta)**: r(n) has order of growth Θ(g(n)) if there are positive constants k₁, k₂ and n₀
such that k₁·g(n) ≤ r(n) ≤ k₂·g(n) for all n > n₀. In words: for big enough n, r is sandwiched
between two multiples of g.

**O (Big O)**: only the upper half, r(n) ≤ k·g(n). "It grows **at most** like g."

**Ω (Big Omega)**: only the lower half, k·g(n) ≤ r(n). "It grows **at least** like g."

Two consequences you use all the time:

- **Constants do not matter**: 1000n² and n²/2 are both Θ(n²).
- **Smaller terms do not matter**: 3n² + 10n + 17 is Θ(n²), because n² wins for large n.

The course uses Θ by default and wants the **tightest** bound. Tree-recursive `fib` takes Θ(φⁿ)
time. Saying O(2ⁿ) is true (φⁿ ≤ 2ⁿ) but loose; saying Θ(2ⁿ) is wrong.

!!! warning "Trap: O is not \"the answer\""
    In everyday speech people say "big O" when they mean Θ. In this course, O is an upper bound only.
    Everything that is Θ(n) is also O(n²) and O(2ⁿ). If a question asks for the order of growth, give
    the tight Θ.

## The standard growth table

| g(n) | name | n = 10 | n = 100 | n = 1000 | when n doubles |
|---|---|---|---|---|---|
| 1 | constant | 1 | 1 | 1 | no change |
| log n | logarithmic | 3.3 | 6.6 | 10 | adds a constant |
| n | linear | 10 | 100 | 1000 | doubles |
| n log n | | 33 | 664 | about 10 000 | a bit more than doubles |
| n² | quadratic | 100 | 10 000 | 1 000 000 | × 4 |
| n³ | cubic | 1000 | 10⁶ | 10⁹ | × 8 |
| 2ⁿ | exponential | 1024 | about 10³⁰ | about 10³⁰¹ | squares (each +1 doubles) |

(Logs here are base 2. The base of a log does not matter inside Θ: it only changes a constant.)

## A recipe for finding the order of growth

1. Decide what **n** is (the number? the number of digits? the length of a llist?).
2. Pick the **basic step** to count: one application, one multiplication.
3. Try **small values** by hand, or draw the call tree.
4. **Extrapolate**: how many applications in total (time)? How deep does the waiting go (space)?
5. Watch for the **worst case**: is there an input that makes it slower?
6. Give the **tightest** bound, with Θ.

Shortcuts that cover most exam questions:

| Shape of the function | Time | Space |
|---|---|---|
| one self-application on n − 1, with a deferred operation | Θ(n) | Θ(n) |
| one self-application on n − 1, as a tail call | Θ(n) | Θ(1) |
| two self-applications on n − 1 (or n − 1 and n − 2) | exponential | Θ(n) |
| one self-application on n // 2 | Θ(log n) | Θ(log n), or Θ(1) as a tail call |

## Measuring: what doubling does

The quickest sanity check: double n and watch the counts. Here is a plain power function, which
multiplies `b` into the answer `n` times:

```python title="§1"
def power(b, n):
    return 1 if n == 0 else b * power(b, n - 1)

measure(power, 2, 100)
measure(power, 2, 200)
measure(power, 2, 400)
measure(power, 2, 800)
```
```text title="Output"
[measure] power(2, 100): 101 calls, 1,306 steps, at most 101 waiting at once
[measure] power(2, 200): 201 calls, 2,606 steps, at most 201 waiting at once
[measure] power(2, 400): 401 calls, 5,206 steps, at most 401 waiting at once
[measure] power(2, 800): 801 calls, 10,406 steps, at most 801 waiting at once
```

Steps and waiting calls both double when n doubles: Θ(n) time, Θ(n) space.

## Halving: logarithmic growth

To compute b¹⁰⁰ you do not need 100 multiplications. b¹⁰⁰ = (b⁵⁰)², b⁵⁰ = (b²⁵)², and b²⁵ = b · b²⁴.
When n is even, **halve** it and square the result; when n is odd, take one factor off:

```python title="§1"
def square(x):
    return x * x

def is_even(n):
    return n % 2 == 0

def fast_power(b, n):
    return (1 if n == 0
            else square(fast_power(b, n // 2)) if is_even(n)
            else b * fast_power(b, n - 1))

print(fast_power(3, 5), fast_power(2, 100) == 2 ** 100)
```
```text title="Output"
243 True
```

Every two steps at most, n is halved. Halving 1000 down to 1 takes only about 10 halvings, so
the time is Θ(log n). The squarings are deferred, so the space is Θ(log n) too.

??? example "X-ray: doubling n adds a constant"
    ```python title="§1"
    def square(x):
        return x * x

    def is_even(n):
        return n % 2 == 0

    def fast_power(b, n):
        return (1 if n == 0
                else square(fast_power(b, n // 2)) if is_even(n)
                else b * fast_power(b, n - 1))

    measure(fast_power, 2, 100)
    measure(fast_power, 2, 200)
    measure(fast_power, 2, 400)
    measure(fast_power, 2, 800)
    ```
    ```text title="Output"
    [measure] fast_power(2, 100): 25 calls, 237 steps, at most 10 waiting at once
    [measure] fast_power(2, 200): 28 calls, 264 steps, at most 11 waiting at once
    [measure] fast_power(2, 400): 31 calls, 291 steps, at most 12 waiting at once
    [measure] fast_power(2, 800): 34 calls, 318 steps, at most 13 waiting at once
    ```
    Doubling n adds 27 steps and one waiting call each time: that is the fingerprint of Θ(log n).
    (The calls of `square` and `is_even` are counted too.)

## Greatest common divisor

The greatest common divisor of a and b is the largest number that divides both. Euclid's idea: if
r is the remainder of a divided by b, then gcd(a, b) = gcd(b, r). Stop when the second number is 0.

```python title="§1"
def gcd(a, b):
    return a if b == 0 else gcd(b, a % b)

print(trace(gcd, 1071, 462))
```
```text title="Output"
→ gcd(1071, 462)
↻ gcd(462, 147)
↻ gcd(147, 21)
↻ gcd(21, 0)
← 21
21
```

Every step is a tail call (`↻`), so the process is iterative: Θ(1) space. The numbers shrink fast:
every two steps the first number at least halves, so the time is Θ(log n), where n is the smaller
input. (The pre-declared `math_gcd` does the same job.)

## Takeaways

- **Tree recursion** applies the function more than once per step. `fib` takes Θ(φⁿ) time but only
  Θ(n) space (the depth of the tree).
- A **resource function** r(n) counts time (steps) or space (what is remembered at once) for size n.
- **Θ** is a two-sided bound, **O** an upper bound, **Ω** a lower bound. Use the tightest Θ.
- Drop constant factors and smaller terms: 3n² + 10n + 17 is Θ(n²).
- Doubling n: Θ(n) doubles, Θ(n²) quadruples, Θ(log n) adds a constant, Θ(2ⁿ) explodes.
- **Halving** the problem each step gives Θ(log n): fast exponentiation, gcd.
- Iterative factorial and `fib_iter`: Θ(n) time, Θ(1) space.

## Check yourself

1. Give the order of growth of time and space of `count_digits` from chapter 3, in terms of the
   number n.

    ??? success "Answer"
        ```python title="§1"
        def count_digits(n):
            return 1 if n < 10 else 1 + count_digits(n // 10)

        measure(count_digits, 10 ** 10)
        measure(count_digits, 10 ** 20)
        ```
        ```text
        [measure] count_digits(10000000000): 11 calls, 126 steps, at most 11 waiting at once
        [measure] count_digits(10000000000000000...): 21 calls, 246 steps, at most 21 waiting at once
        ```
        Θ(log n) time and Θ(log n) space: each step divides n by 10, and every `1 +` is deferred.
        Squaring n (from 10¹⁰ to 10²⁰) only doubles the work.

2. What are the time and space of `both(n)`?

    ```python title="§1"
    def both(n):
        return 1 if n == 0 else both(n - 1) + both(n - 1)

    measure(both, 8)
    measure(both, 9)
    measure(both, 10)
    ```

    ??? success "Answer"
        ```text
        [measure] both(8): 511 calls, 5,616 steps, at most 9 waiting at once
        [measure] both(9): 1,023 calls, 11,248 steps, at most 10 waiting at once
        [measure] both(10): 2,047 calls, 22,512 steps, at most 11 waiting at once
        ```
        Two self-applications on n − 1: the call tree doubles at each level, so Θ(2ⁿ) time. Only one
        path is waiting at a time, so Θ(n) space. Each +1 to n doubles the calls.

3. True or false: tree-recursive `fib` is (a) O(2ⁿ), (b) Θ(2ⁿ), (c) Ω(n).

    ??? success "Answer"
        (a) True, φⁿ ≤ 2ⁿ. (b) False: φⁿ / 2ⁿ goes to 0, so no constant k₁ works. (c) True, φⁿ
        grows at least as fast as n. The tight answer is Θ(φⁿ).

4. Simplify: 5n³ + 100n² + 7, then 2ⁿ + n¹⁰, then 3 log₂ n + 7.

    ??? success "Answer"
        Θ(n³), Θ(2ⁿ) (exponential beats any power for large n), Θ(log n).

5. `fast_power` gives a recursive process. What would an iterative version save, and what would
   stay the same?

    ??? success "Answer"
        Space would drop from Θ(log n) to Θ(1), because nothing would be deferred. Time stays
        Θ(log n): it still halves n.

6. Why is the space of `fib(n)` Θ(n) when it makes about φⁿ applications?

    ??? success "Answer"
        Space counts what is remembered **at the same moment**. When one branch returns, its waiting
        work is gone. At any time only one path from the root is waiting, and the longest path is
        `fib(n)`, `fib(n - 1)`, …, `fib(1)`: n applications.

*In the course: L2B · SICPy 1.2.2–1.2.4.*
