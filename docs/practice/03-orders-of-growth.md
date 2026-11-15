# Drills: Orders of growth

<p class="chapter-goal">Ten problems on stating the tightest Θ for time and space, with sicpfuf's <code>measure</code> as evidence for every answer.</p>

The recipe for every problem on this page:

1. Say what n is (the number, the length, ...).
2. **Time**: how many calls happen, and how much work each call does outside its recursive calls.
3. **Space**: the largest number of deferred operations waiting at once (for a recursive process, the depth of the calls).
4. Drop constants and smaller terms; give the tightest bound.

`measure(f, args...)` reports calls, steps (time) and "at most k waiting at once" (space). Double n and watch: steps that double mean Θ(n), steps that grow by a fixed amount mean Θ(log n), steps that grow four times mean Θ(n²). Measured numbers are evidence; the counting argument is the answer the exam wants.

## 1. Put them in order ★

**Skill:** know the common growth functions.

Put these in order from slowest-growing to fastest-growing: n², log n, 2ⁿ, n, 1, n log n, √n, n³.

??? success "Answer"
    1, log n, √n, n, n log n, n², n³, 2ⁿ. The numbers for n = 16 and n = 1024 make the gaps visible:

    ```python title="§1"
    def row(n):
        print(n, math_log2(n), math_sqrt(n), n * math_log2(n), n * n, n * n * n)

    row(16)
    row(1024)
    print(2 ** 16)
    print(len(str(2 ** 1024)), "digits in 2 to the power 1024")
    ```
    ```text
    16 4.0 4.0 64.0 256 4096
    1024 10.0 32.0 10240.0 1048576 1073741824
    65536
    309 digits in 2 to the power 1024
    ```

    Going from 16 to 1024, log n only goes from 4 to 10, while 2ⁿ goes from 65536 to a number with 309 digits.

## 2. Tightest, true, false ★

**Skill:** Θ, O and Ω and the word "tightest".

A function takes r(n) = 3n² + 100n + 7 steps. True or false?

(a) r(n) is Θ(n²). (b) r(n) is O(n³). (c) r(n) is Ω(n³). (d) r(n) is Ω(n). (e) r(n) is Θ(n² + n).

??? success "Answer"
    (a) True: the n² term wins for large n, and constants do not matter. (b) True, but loose: O is only an upper bound, and n³ is above. (c) False: Ω is a lower bound, and r(n) does not grow as fast as n³. (d) True, but loose. (e) True, but nobody writes it: smaller terms are dropped, so it is the same as Θ(n²).

    In the exam "give the order of growth" means the tightest Θ: here Θ(n²).

## 3. The two sums ★

**Skill:** time and space of a recursive and an iterative process.

Give Θ of time and space for `sum_to(n)` and for `sum_iter(n, 0)`.

```python
def sum_to(n):
    return 0 if n == 0 else n + sum_to(n - 1)

def sum_iter(n, total):
    return total if n == 0 else sum_iter(n - 1, total + n)
```

??? success "Answer"
    `sum_to`: Θ(n) time, Θ(n) space. `sum_iter`: Θ(n) time, Θ(1) space.

    ```python title="§1"
    def sum_to(n):
        return 0 if n == 0 else n + sum_to(n - 1)

    def sum_iter(n, total):
        return total if n == 0 else sum_iter(n - 1, total + n)

    measure(sum_to, 200)
    measure(sum_to, 400)
    measure(sum_iter, 200, 0)
    measure(sum_iter, 400, 0)
    ```
    ```text
    [measure] sum_to(200): 201 calls, 2,406 steps, at most 201 waiting at once
    [measure] sum_to(400): 401 calls, 4,806 steps, at most 401 waiting at once
    [measure] sum_iter(200, 0): 201 calls, 2,606 steps, at most 1 waiting at once
    [measure] sum_iter(400, 0): 401 calls, 5,206 steps, at most 1 waiting at once
    ```

    Both make n + 1 calls with a constant amount of work each, so steps double when n doubles. `sum_to` leaves an `n + ...` waiting in every call; `sum_iter` leaves nothing waiting.

## 4. Halving ★★

**Skill:** recognise Θ(log n).

```python
def halvings(n):
    return 0 if n <= 1 else 1 + halvings(n // 2)
```

??? success "Answer"
    Θ(log n) time and Θ(log n) space.

    ```python title="§1"
    def halvings(n):
        return 0 if n <= 1 else 1 + halvings(n // 2)

    measure(halvings, 1000)
    measure(halvings, 2000)
    measure(halvings, 1000000)
    ```
    ```text
    [measure] halvings(1000): 10 calls, 114 steps, at most 10 waiting at once
    [measure] halvings(2000): 11 calls, 126 steps, at most 11 waiting at once
    [measure] halvings(1000000): 20 calls, 234 steps, at most 20 waiting at once
    ```

    Each call halves n, so after k calls n is about n / 2ᵏ, which reaches 1 when k = log₂ n. Doubling n adds **one** call; multiplying n by 1000 only doubles the calls. The process is recursive (`1 + ...` waits), so space is the same log₂ n.

## 5. Two calls where one would do ★★

**Skill:** tree recursion with identical calls; fixing it with a name.

Give Θ of time and space of `t(n)`. Then rewrite it so that it is linear.

```python
def t(n):
    return 1 if n == 0 else t(n - 1) + t(n - 1)
```

??? success "Answer"
    `t`: Θ(2ⁿ) time, Θ(n) space. Every call makes two calls, so the call tree has 1 + 2 + 4 + ... + 2ⁿ = 2ⁿ⁺¹ − 1 nodes, but only one path of the tree (n + 1 calls deep) is waiting at any moment.

    ```python title="§1"
    def t(n):
        return 1 if n == 0 else t(n - 1) + t(n - 1)

    def t2(n):
        if n == 0:
            return 1
        else:
            half = t2(n - 1)
            return half + half

    print(t(10), t2(10))
    measure(t, 10)
    measure(t, 11)
    measure(t2, 10)
    measure(t2, 11)
    ```
    ```text
    1024 1024
    [measure] t(10): 2,047 calls, 22,512 steps, at most 11 waiting at once
    [measure] t(11): 4,095 calls, 45,040 steps, at most 12 waiting at once
    [measure] t2(10): 11 calls, 146 steps, at most 11 waiting at once
    [measure] t2(11): 12 calls, 160 steps, at most 12 waiting at once
    ```

    For `t`, adding 1 to n doubles the steps: exponential. `t2` asks for the answer once and uses it twice: Θ(n) time and space. The conditional statement matters: with `half = t2(n - 1)` above a conditional expression, the call would happen even when n is 0, and the recursion would never stop.

## 6. Two calls on half ★★

**Skill:** do not say "two recursive calls, so exponential" without counting.

```python
def u(n):
    return 1 if n <= 1 else u(n // 2) + u(n // 2)
```

??? success "Answer"
    Θ(n) time, Θ(log n) space.

    ```python title="§1"
    def u(n):
        return 1 if n <= 1 else u(n // 2) + u(n // 2)

    measure(u, 64)
    measure(u, 128)
    measure(u, 256)
    ```
    ```text
    [measure] u(64): 127 calls, 1,392 steps, at most 7 waiting at once
    [measure] u(128): 255 calls, 2,800 steps, at most 8 waiting at once
    [measure] u(256): 511 calls, 5,616 steps, at most 9 waiting at once
    ```

    The call tree doubles in width at each level, but there are only log₂ n levels, so the bottom level has about n calls and the whole tree about 2n. Steps double when n doubles: Θ(n). The depth of the tree is log₂ n + 1, and that is the space.

## 7. A loop inside a loop ★★

**Skill:** time = (number of calls) × (work per call), when the work per call is not constant.

`tri(n)` adds `line_sum(n) + line_sum(n - 1) + ... + line_sum(1)`.

```python
def line_sum(n):
    return 0 if n == 0 else n + line_sum(n - 1)

def tri(n):
    return 0 if n == 0 else line_sum(n) + tri(n - 1)
```

??? success "Answer"
    Θ(n²) time, Θ(n) space.

    ```python title="§1"
    def line_sum(n):
        return 0 if n == 0 else n + line_sum(n - 1)

    def tri(n):
        return 0 if n == 0 else line_sum(n) + tri(n - 1)

    measure(tri, 50)
    measure(tri, 100)
    measure(tri, 200)
    ```
    ```text
    [measure] tri(50): 1,376 calls, 16,306 steps, at most 52 waiting at once
    [measure] tri(100): 5,251 calls, 62,606 steps, at most 102 waiting at once
    [measure] tri(200): 20,501 calls, 245,206 steps, at most 202 waiting at once
    ```

    `tri` makes n calls, and the k-th of them runs `line_sum` on a number up to n: n + (n − 1) + ... + 1 = n(n + 1)/2 steps of `line_sum`. Doubling n multiplies the steps by about 4: quadratic. Space: n calls of `tri` wait, and on top of them at most n calls of `line_sum`, about 2n in all, so Θ(n).

## 8. Shrinking work, but watch the space ★★★

**Skill:** a geometric sum of work; space set by the helper, not by the main function.

```python
def line_sum(n):
    return 0 if n == 0 else n + line_sum(n - 1)

def half_work(n):
    return 0 if n == 0 else line_sum(n) + half_work(n // 2)
```

??? success "Answer"
    Θ(n) time, Θ(n) space.

    ```python title="§1"
    def line_sum(n):
        return 0 if n == 0 else n + line_sum(n - 1)

    def half_work(n):
        return 0 if n == 0 else line_sum(n) + half_work(n // 2)

    measure(half_work, 128)
    measure(half_work, 256)
    measure(half_work, 512)
    ```
    ```text
    [measure] half_work(128): 272 calls, 3,226 steps, at most 130 waiting at once
    [measure] half_work(256): 530 calls, 6,318 steps, at most 258 waiting at once
    [measure] half_work(512): 1,044 calls, 12,482 steps, at most 514 waiting at once
    ```

    Time: the `line_sum` work is n + n/2 + n/4 + ... < 2n, and there are only log n calls of `half_work`, so Θ(n) (not Θ(n log n)). Space: `half_work` alone would only need Θ(log n), but the very first `line_sum(n)` keeps n deferred additions waiting. The biggest pile wins: Θ(n).

## 9. Best case, worst case ★★★

**Skill:** when the answer depends on the input, give both.

Give Θ of time and space of `smallest_divisor(n)` in the best case and in the worst case.

```python
def smallest_divisor(n):
    def try_from(d):
        return n if d * d > n else d if n % d == 0 else try_from(d + 1)
    return try_from(2)
```

??? success "Answer"
    Best case (n even): Θ(1) time. Worst case (n prime): Θ(√n) time. Space Θ(1) in every case.

    ```python title="§1"
    def smallest_divisor(n):
        def try_from(d):
            return n if d * d > n else d if n % d == 0 else try_from(d + 1)
        return try_from(2)

    print(smallest_divisor(91), smallest_divisor(97))
    measure(smallest_divisor, 1000000)
    measure(smallest_divisor, 10007)
    measure(smallest_divisor, 40009)
    measure(smallest_divisor, 160001)
    ```
    ```text
    7 97
    [measure] smallest_divisor(1000000): 2 calls, 19 steps, at most 1 waiting at once
    [measure] smallest_divisor(10007): 101 calls, 1,795 steps, at most 1 waiting at once
    [measure] smallest_divisor(40009): 201 calls, 3,595 steps, at most 1 waiting at once
    [measure] smallest_divisor(160001): 401 calls, 7,195 steps, at most 1 waiting at once
    ```

    An even number stops at `d = 2` however big it is. For a prime, `d` runs up to √n before `d * d > n` stops it. The three primes are each about 4 times the last, and the calls only double: that is √n. Every recursive call is a tail call, so space is constant.

## 10. The slowest gcd ★★★

**Skill:** Θ(log n) without halving in plain sight.

Euclid's algorithm is `gcd(a, b) = a if b == 0 else gcd(b, a % b)`. Its worst inputs are two neighbouring Fibonacci numbers. Use `measure` to argue that its time is Θ(log n), where n is the smaller argument.

??? success "Answer"
    ```python title="§1"
    def gcd(a, b):
        return a if b == 0 else gcd(b, a % b)

    measure(gcd, 89, 55)
    measure(gcd, 6765, 4181)
    measure(gcd, 832040, 514229)
    ```
    ```text
    [measure] gcd(89, 55): 10 calls, 105 steps, at most 1 waiting at once
    [measure] gcd(6765, 4181): 19 calls, 204 steps, at most 1 waiting at once
    [measure] gcd(832040, 514229): 29 calls, 314 steps, at most 1 waiting at once
    ```

    Multiplying n by about 76 (55 to 4181) and by 123 again (4181 to 514229) adds about 10 calls each time: the number of calls grows with the number of **digits** of n, which is Θ(log n). Why: two steps of Euclid at least halve the first argument (`a % b` is less than a/2). The process is iterative, so space is Θ(1).

*In the course: L2B, R3 · SICPy 1.2.2, 1.2.3, 1.2.5, 1.2.6.*
