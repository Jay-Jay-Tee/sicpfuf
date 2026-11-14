# Orders of growth

<p class="chapter-goal">One page: state Θ for time and space quickly, tightly and with a reason.</p>

## The three symbols, in plain words

Let r(n) be the resource (time or space) used on a problem of size n.

| Symbol | Plain words | Picture |
|---|---|---|
| r(n) is **Θ(g(n))** | for large n, r(n) stays between two constant multiples of g(n) | "grows like g" |
| r(n) is **O(g(n))** | for large n, r(n) is at most a constant times g(n) | upper bound |
| r(n) is **Ω(g(n))** | for large n, r(n) is at least a constant times g(n) | lower bound |

Θ means O and Ω at the same time. Constants and smaller terms do not matter: 3n² + 100n + 7 is Θ(n²).
The course default is Θ, and it wants the **tightest** bound. "fib is O(2ⁿ)" is true but loose; "fib is Θ(φⁿ)" is tight. "factorial is O(n³)" is true and earns nothing.

Ladder, slowest growth first: 1, log n, n, n log n, n², n³, 2ⁿ (and φⁿ, n! ...).

## The recipe

1. **Say what n is.** "n is the length of `xs`", "n is the value of the argument". With two inputs, you may need two letters (`append(xs, ys)` depends only on the length of `xs`).
2. **Time = count the steps.** How many calls (or loop iterations) happen, times the work in ONE call that does not count the recursion. Draw the call tree if there are two or more recursive calls.
3. **Space = the most that must be remembered at one moment**:
    - deferred operations waiting (the depth of the pending calls),
    - pairs, lists and function values that must still be kept (the result llist counts!).
4. **Check best and worst case.** If the work depends on the data (early exit, sorted input), say which case you give, or give both.
5. **Simplify**: drop constants and smaller terms. Write the answer as Θ(...) with n defined.

Micro-example: `def f(n): return 0 if n == 0 else n + f(n - 1)`. Calls: n + 1, each Θ(1) work, so time Θ(n). Up to n additions wait at once, so space Θ(n).

## Where the shapes come from

| You see | You get |
|---|---|
| one recursive call on n − 1, Θ(1) work each | Θ(n) |
| one recursive call on n // 2 (halving) | Θ(log n) |
| two recursive calls on n − 1 | Θ(2ⁿ) |
| two calls on n − 1 and n − 2 (fib) | Θ(φⁿ), φ ≈ 1.618 |
| loop of n iterations, each doing Θ(n) | Θ(n²) |
| `append(result_so_far, ...)` once per element | Θ(n²) |
| two calls on n/2, Θ(n) work to combine (merge sort) | Θ(n log n) |

Halving in action. Making n a thousand times bigger adds only 10 calls:

```python title="§1"
def halvings(n):
    return 0 if n <= 1 else 1 + halvings(n // 2)

measure(halvings, 1000)
measure(halvings, 1000000)
```
```text title="Output"
[measure] halvings(1000): 10 calls, 114 steps, at most 10 waiting at once
[measure] halvings(1000000): 20 calls, 234 steps, at most 20 waiting at once
```

## Standard results (learn this table)

n is the argument value, or the length of the (first) llist/list.

| Function | Time | Space |
|---|---|---|
| factorial, recursive process | Θ(n) | Θ(n) |
| factorial, iterative process (accumulator or loop) | Θ(n) | Θ(1) |
| fib, tree recursion | Θ(φⁿ) | Θ(n) (depth of the tree) |
| fib, iterative or memoized | Θ(n) | Θ(1) iterative, Θ(n) memoized |
| fast power by squaring (halve when even) | Θ(log n) | Θ(log n) recursive, Θ(1) iterative |
| Towers of Hanoi with n discs | Θ(2ⁿ) | Θ(n) |
| `length(xs)` written recursively | Θ(n) | Θ(n) |
| `append(xs, ys)` | Θ(length of xs) | Θ(length of xs) new pairs |
| `reverse` via `append` in each step | Θ(n²) | Θ(n) |
| `reverse` with an accumulator | Θ(n) | Θ(n) (the new pairs) |
| `map(f, xs)`, `filter(p, xs)` with Θ(1) `f`, `p` | Θ(n) | Θ(n) |
| `llist_ref(xs, k)` | Θ(k) | Θ(1) |
| `xs[i]`, `xs[i] = v`, `len(xs)` on a list | Θ(1) | Θ(1) |
| `[0] * n` | Θ(n) | Θ(n) |
| linear search | Θ(n) worst, Θ(1) best | Θ(1) with a loop |
| binary search on a sorted list | Θ(log n) | Θ(1) loop, Θ(log n) recursive |
| insertion sort | Θ(n²) worst, Θ(n) best (already sorted) | Θ(1) extra in place |
| selection sort | Θ(n²) in every case | Θ(1) extra in place |
| merge sort | Θ(n log n) | Θ(n) |
| `stream_ref(s, k)` (cheap tails) | Θ(k) | depends on the stream |

## Space: the refined rule

In Unit 1, space = deferred operations. From Unit 2 on, also count the **pairs** (and lists and function objects) that must be remembered at the same moment. Only `pair(...)`, `llist(...)`, `[...]`, `lambda` and `def` create things; `head`, `tail` and passing a value create nothing.

- A function that builds a result llist of length n uses Θ(n) space even if its process is iterative.
- A CPS function has no deferred operations but builds a chain of n continuations: Θ(n) space.

`measure` counts waiting calls, not pairs. Here both reversals keep n new pairs, so both use Θ(n) space, but only the slow one has deferred operations, and its steps grow four times when n doubles:

```python title="§2"
def slow_rev(xs):
    return None if is_none(xs) else append(slow_rev(tail(xs)), llist(head(xs)))

def fast_rev(xs):
    def go(ys, acc):
        return acc if is_none(ys) else go(tail(ys), pair(head(ys), acc))
    return go(xs, None)

measure(slow_rev, enum_llist(1, 100))
measure(slow_rev, enum_llist(1, 200))
measure(fast_rev, enum_llist(1, 100))
measure(fast_rev, enum_llist(1, 200))
```
```text title="Output"
[measure] slow_rev([1, [2, [3, [4, [...): 10,301 calls, 97,256 steps, at most 101 waiting at once
[measure] slow_rev([1, [2, [3, [4, [...): 40,601 calls, 384,506 steps, at most 201 waiting at once
[measure] fast_rev([1, [2, [3, [4, [...): 102 calls, 1,612 steps, at most 1 waiting at once
[measure] fast_rev([1, [2, [3, [4, [...): 202 calls, 3,212 steps, at most 1 waiting at once
```

## How to answer this in the exam

1. Define n in words.
2. Give Θ for time, then for space, each with ONE sentence of reason ("n + 1 calls, Θ(1) each"; "n multiplications deferred at once").
3. For two recursive calls, sketch the call tree: how many levels, how many nodes per level.
4. If asked for O or Ω, give the tightest one you can still justify.
5. For "best/worst case", name the input that causes it ("already sorted", "value not present").

## Top traps

1. **Loose bound.** O(n²) for a Θ(n) function is true, but the question wants the tight one.
2. **Forgetting what n is.** `llist_ref(xs, k)` is Θ(k), not Θ(length of xs).
3. **Hidden loops.** `append`, `length`, `reverse`, `llist_ref`, `member` inside a recursion each cost Θ(n), so the total is Θ(n²).
4. **Ignoring the result.** "Iterative, so Θ(1) space" is wrong when the function builds a llist of n pairs.
5. **Best case with Θ.** "Insertion sort is Θ(n²)" is the worst case; say so.
6. **log base.** Θ(log n) needs no base: log₂ n and log₁₀ n differ by a constant factor.
7. **Measuring tiny n.** Compare n and 2n with `measure`: steps × 2 suggests Θ(n), × 4 suggests Θ(n²), + constant suggests Θ(log n).

*In the course: L2B, L5A, L5B, L10A · SICPy 1.2.2, 1.2.3, 1.2.4.*
