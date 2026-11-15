# Drill 13 · Streams II

<p class="chapter-goal">Define infinite streams in terms of themselves, predict what they hold, count the work with and without memo_fun.</p>

Easiest first. Try each problem on paper before you open the answer. Every answer was run in Python §3. `add_streams`, `scale_stream` and `memo_fun` are **not** pre-declared, so each program defines the ones it uses.

!!! tip "Reading a self-referential stream"
    Write the stream as a row of boxes and fill them **left to right**. The definition says how to compute box k from boxes that are already filled. Example: `s = pair(1, lambda: scale_stream(2, s))`: box 0 is 1; the rest is `s` doubled, so box 1 is 2 × box 0, box 2 is 2 × box 1, …: 1, 2, 4, 8, …

## 1. Back and forth ★

*Skill: a finite definition that loops back to itself.*

Define `seesaw`, the infinite stream 2, 3, 2, 3, … with no helper function, and show its first 5 elements.

??? success "Answer"
    ```python title="§3"
    seesaw = pair(2, lambda: pair(3, lambda: seesaw))
    print_llist(eval_stream(seesaw, 5))
    print(stream_ref(seesaw, 100))
    ```
    ```text
    llist(2, 3, 2, 3, 2)
    2
    ```
    The tail of the second pair returns `seesaw` itself, the first pair: a loop of two pairs. This works because `seesaw` is only looked up when the lambda is **applied**, by then the assignment has happened. Even indices give 2.

## 2. What is in it? ★

*Skill: predict a stream defined with `scale_stream` over itself.*

```python title="§3"
def scale_stream(c, s):
    return stream_map(lambda x: c * x, s)

s = pair(1, lambda: scale_stream(3, s))
t = pair(1, lambda: scale_stream(-1, t))
print_llist(eval_stream(s, 5))
print_llist(eval_stream(t, 5))
```

??? success "Answer"
    ```text
    llist(1, 3, 9, 27, 81)
    llist(1, -1, 1, -1, 1)
    ```
    Each box of `s` after the first is 3 times the box before it: the powers of 3. `t` flips the sign each time: 1, −1, 1, −1, …

## 3. Adding a stream to itself ★★

*Skill: predict a stream defined with `add_streams`.*

```python title="§3"
def add_streams(s1, s2):
    return (s2 if is_none(s1) else s1 if is_none(s2)
            else pair(head(s1) + head(s2),
                      lambda: add_streams(stream_tail(s1), stream_tail(s2))))

u = pair(0, lambda: add_streams(u, integers_from(1)))
print_llist(eval_stream(u, 6))
```

??? success "Answer"
    ```text
    llist(0, 1, 3, 6, 10, 15)
    ```
    Box k+1 of `u` = box k of `u` + box k of `integers_from(1)`, which is k + 1. So 0, 0+1, 1+2, 3+3, 6+4, 10+5: the **running sums** 1 + 2 + … + k (the triangular numbers).

## 4. Squares without multiplying ★★

*Skill: define a stream from a mathematical pattern.*

The squares 1, 4, 9, 16, … differ by the odd numbers 3, 5, 7, …. Define `squares` using `add_streams` and itself, with no `*`.

??? success "Answer"
    ```python title="§3"
    def add_streams(s1, s2):
        return (s2 if is_none(s1) else s1 if is_none(s2)
                else pair(head(s1) + head(s2),
                          lambda: add_streams(stream_tail(s1), stream_tail(s2))))

    def odds_from(n):
        return pair(n, lambda: odds_from(n + 2))

    squares = pair(1, lambda: add_streams(squares, odds_from(3)))
    print_llist(eval_stream(squares, 7))
    ```
    ```text
    llist(1, 4, 9, 16, 25, 36, 49)
    ```
    Box k+1 = box k + (2k + 3). The same shape as problem 3: "next = this one + a known stream".

## 5. Tick, tick ★★

*Skill: count how often tail functions run, without and with `memo_fun`.*

```python title="§3"
def memo_fun(fun):
    already_run = False
    result = None
    def memoized():
        nonlocal already_run, result
        if not already_run:
            result = fun()
            already_run = True
        return result
    return memoized

def ticking_from(n):
    def rest():
        print("tick", n + 1)
        return ticking_from(n + 1)
    return pair(n, rest)

def memo_ticking_from(n):
    def rest():
        print("tock", n + 1)
        return memo_ticking_from(n + 1)
    return pair(n, memo_fun(rest))

t = ticking_from(1)
print(stream_ref(t, 2))
print(stream_ref(t, 2))
m = memo_ticking_from(1)
print(stream_ref(m, 2))
print(stream_ref(m, 2))
```

??? success "Answer"
    ```text
    tick 2
    tick 3
    3
    tick 2
    tick 3
    3
    tock 2
    tock 3
    3
    3
    ```
    `stream_ref(t, 2)` forces two tails. Without memoization **every** traversal runs them again, so the ticks are printed twice. With `memo_fun`, each tail function runs once and stores its result (the same pair) in its frame. The second `stream_ref(m, 2)` walks over pairs that already exist: no "tock" at all. The values are the same, only the side effects differ.

## 6. The Fibonacci stream is slow ★★★

*Skill: see why a self-referential stream needs memoization.*

How does the number of `add_streams` calls grow with `n`? Fix it with `memo_fun`.

```python title="§3"
calls = 0

def add_streams(s1, s2):
    global calls
    calls = calls + 1
    return pair(head(s1) + head(s2),
                lambda: add_streams(stream_tail(s1), stream_tail(s2)))

fibs = pair(0, lambda: pair(1, lambda: add_streams(fibs, stream_tail(fibs))))

for n in range(5, 21, 5):
    calls = 0
    print(n, stream_ref(fibs, n), calls)
```

??? success "Answer"
    ```text
    5 5 14
    10 55 221
    15 610 2567
    20 6765 28635
    ```
    The count grows like the Fibonacci numbers themselves: exponentially. Every element after the first two is built from **two** elements of `fibs`, and without memoization each of those is recomputed from scratch by forcing its tails again. Memoizing the tails makes each element computed once:

    ```python title="§3"
    def memo_fun(fun):
        already_run = False
        result = None
        def memoized():
            nonlocal already_run, result
            if not already_run:
                result = fun()
                already_run = True
            return result
        return memoized

    calls = 0

    def add_streams(s1, s2):
        global calls
        calls = calls + 1
        return pair(head(s1) + head(s2),
                    memo_fun(lambda: add_streams(stream_tail(s1), stream_tail(s2))))

    fibs = pair(0, memo_fun(lambda: pair(1, memo_fun(lambda: add_streams(fibs, stream_tail(fibs))))))

    print(stream_ref(fibs, 20), calls)
    print(stream_ref(fibs, 30), calls)
    ```
    ```text
    6765 19
    832040 29
    ```
    Now `stream_ref(fibs, n)` needs about n calls of `add_streams` in total (19 for n = 20), and asking again for a later element only does the new work (10 more for n = 30).

## 7. A sieve that starts in the wrong place ★★

*Skill: predict what the sieve really does.*

```python title="§3"
def sieve(s):
    return pair(head(s),
                lambda: sieve(stream_filter(lambda x: x % head(s) != 0,
                                            stream_tail(s))))

print_llist(eval_stream(sieve(integers_from(2)), 6))
print_llist(eval_stream(sieve(integers_from(4)), 6))
```

??? success "Answer"
    ```text
    llist(2, 3, 5, 7, 11, 13)
    llist(4, 5, 6, 7, 9, 11)
    ```
    The sieve keeps the head and removes its multiples from the rest, then repeats. Started at 2, every number that survives has no smaller factor, so it is prime. Started at 4, 2 and 3 are never heads, so their multiples are not removed: 6 stays (it is not a multiple of 4 or 5), 8 is removed by 4, 9 stays, 10 is removed by 5. The sieve only produces primes because it starts at 2.

## 8. Sieve with a twist ★★

*Skill: write a sieve variant.*

Write `odd_primes()`, the stream 3, 5, 7, 11, 13, … , by sieving a stream of **odd** numbers only (no even number should ever be tested).

??? success "Answer"
    ```python title="§3"
    def sieve(s):
        return pair(head(s),
                    lambda: sieve(stream_filter(lambda x: x % head(s) != 0,
                                                stream_tail(s))))

    def odds_from(n):
        return pair(n, lambda: odds_from(n + 2))

    def odd_primes():
        return sieve(odds_from(3))

    print_llist(eval_stream(odd_primes(), 8))
    print_llist(eval_stream(pair(2, odd_primes), 5))
    ```
    ```text
    llist(3, 5, 7, 11, 13, 17, 19, 23)
    llist(2, 3, 5, 7, 11)
    ```
    Starting from 3 is fine here: the even numbers were never in the stream, so 2 is not needed to remove them. `pair(2, odd_primes)` is a stream too: its tail is a nullary function.

## 9. Guess, improve, repeat ★★

*Skill: a stream of approximations defined with `stream_map` over itself.*

Newton's method for the cube root of `x` improves a guess `g` to `(2 * g + x / (g * g)) / 3`. Define `cube_root_stream(x)`, the stream of guesses starting from 1.0, and show the first 6 guesses for 27.

??? success "Answer"
    ```python title="§3"
    def cube_root_stream(x):
        def improve(g):
            return (2 * g + x / (g * g)) / 3
        guesses = pair(1.0, lambda: stream_map(improve, guesses))
        return guesses

    s = cube_root_stream(27)
    for i in range(6):
        print(stream_ref(s, i))
    ```
    ```text
    1.0
    9.666666666666666
    6.540758356453956
    4.570876778578707
    3.4780192333867963
    3.0626891086275365
    ```
    Box k+1 is `improve` of box k: the same shape as `s = pair(1, lambda: scale_stream(3, s))`, with `improve` instead of "times 3". `guesses` is a local name of `cube_root_stream`; the lambda finds it in that frame when it is applied.

## 10. Close enough ★★★

*Skill: consume an infinite stream until a condition holds.*

Write `stream_limit(s, tolerance)`: walk along the stream and return the first element whose distance to the **next** element is less than `tolerance`. Use it on the cube root stream of problem 9.

??? success "Answer"
    ```python title="§3"
    def cube_root_stream(x):
        def improve(g):
            return (2 * g + x / (g * g)) / 3
        guesses = pair(1.0, lambda: stream_map(improve, guesses))
        return guesses

    def stream_limit(s, tolerance):
        rest = stream_tail(s)
        return (head(rest) if abs(head(s) - head(rest)) < tolerance
                else stream_limit(rest, tolerance))

    print(stream_limit(cube_root_stream(27), 0.001))
    print(stream_limit(cube_root_stream(2), 0.0001))
    ```
    ```text
    3.0000000000000977
    1.2599210500177698
    ```
    Force the tail **once** and keep it in `rest`: calling `stream_tail(s)` twice would compute the next guess twice (these streams are not memoized). The recursive call is a tail call, so this is an iterative process. It returns the later of the two close elements, the better guess. On an infinite stream that never settles, it would never stop: that is the price of infinite streams.

## 11. Running maximum ★★

*Skill: a stream function that carries state in a parameter.*

Write `running_max(s)`: element k is the largest of elements 0 … k of `s`. It must work on finite and infinite streams.

??? success "Answer"
    ```python title="§3"
    def running_max(s):
        def go(s, best):
            if is_none(s):
                return None
            else:
                new_best = max(best, head(s))
                return pair(new_best, lambda: go(stream_tail(s), new_best))
        return None if is_none(s) else go(s, head(s))

    print_llist(eval_stream(running_max(stream(3, 1, 4, 1, 5, 9, 2)), 7))
    wave = stream_map(lambda n: (n * 7) % 10, integers_from(1))
    print_llist(eval_stream(wave, 6))
    print_llist(eval_stream(running_max(wave), 6))
    print(running_max(None))
    ```
    ```text
    llist(3, 3, 4, 4, 5, 9, 9)
    llist(7, 4, 1, 8, 5, 2)
    llist(7, 7, 7, 8, 8, 8)
    None
    ```
    The "best so far" travels along as an argument of `go`, so nothing is mutated. Only the head is computed straight away; the rest waits behind the lambda, which is why it also works on the infinite `wave`.

*In the course: L11A · SICPy 3.5.2, 3.5.3.*
