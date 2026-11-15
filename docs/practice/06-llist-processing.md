# Drills: llist processing

<p class="chapter-goal">Ten problems on map, filter and reduce one-liners, recursive functions over llists, the argument order of reduce, and the cost of append.</p>

Keep these three in front of you (all from the §2 library):

- `map(f, xs)`: the llist of `f(x)` for each `x`, in order.
- `filter(pred, xs)`: the llist of the `x` with `pred(x)` true, in order.
- `reduce(f, initial, xs)` folds **from the right**: `reduce(f, init, llist(1, 2, 3))` is `f(1, f(2, f(3, init)))`. So `f` gets (current element, result for the rest).

All programs run as Python §2.

## 1. One-liners ★

**Skill:** combine map, filter and reduce into one expression.

With `xs = enum_llist(1, 8)`, write one expression for each:

(a) the llist of the cubes of the odd numbers in `xs`;
(b) the sum of the squares of the multiples of 3 in `xs`;
(c) the llist of pairs `pair(x, 9 - x)` for each `x` in `xs` with `x < 9 - x`.

??? success "Answer"
    ```python title="§2"
    xs = enum_llist(1, 8)
    print_llist(map(lambda x: x ** 3, filter(lambda x: x % 2 == 1, xs)))
    print(reduce(lambda x, acc: x + acc, 0, map(lambda x: x * x, filter(lambda x: x % 3 == 0, xs))))
    print_llist(map(lambda x: pair(x, 9 - x), filter(lambda x: x < 9 - x, xs)))
    ```
    ```text
    llist(1, 27, 125, 343)
    45
    llist([1, 8], [2, 7], [3, 6], [4, 5])
    ```

    Read each from the inside out: filter first, then map, then reduce. (b) is 3² + 6² = 9 + 36. In (c) the elements are pairs that are not llists, so `print_llist` shows them in box notation.

## 2. Which way does reduce fold? ★

**Skill:** reduce's argument order.

```python title="§2"
print(reduce(lambda x, y: x - y, 0, llist(1, 2, 3)))
print(reduce(lambda x, y: y - x, 0, llist(1, 2, 3)))
print(reduce(lambda x, acc: str(x) + acc, "", llist(1, 2, 3)))
print(reduce(lambda x, acc: acc + str(x), "", llist(1, 2, 3)))
```

??? success "Answer"
    ```text
    2
    -6
    123
    321
    ```

    Write the fold out. Line 1: `1 - (2 - (3 - 0))` = 1 − (−1) = 2. Line 2 swaps the operands of every step: `((0 - 3) - 2) - 1` = −6. Line 3 puts each element in front of the result for the rest: "123". Line 4 puts it behind: the rest of the llist comes first, so the string comes out reversed. The first parameter is always the **element**, the second the **result so far** (which comes from the right).

## 3. reduce that builds llists ★★

**Skill:** predict llist-building folds.

```python title="§2"
xs = llist(1, 2, 3)
print_llist(reduce(lambda x, acc: pair(x, acc), None, xs))
print_llist(reduce(lambda x, acc: append(acc, llist(x)), None, xs))
print_llist(reduce(lambda x, acc: pair(x * 10, acc) if x != 2 else acc, None, xs))
print_llist(reduce(lambda x, acc: pair(x, pair(x, acc)), None, xs))
```

??? success "Answer"
    ```text
    llist(1, 2, 3)
    llist(3, 2, 1)
    llist(10, 30)
    llist(1, 1, 2, 2, 3, 3)
    ```

    `pair` with `None` as the initial value rebuilds the same llist (a copy with new pairs). Appending each element **after** the result for the rest reverses. Line 3 is a map and a filter in one fold: the lambda's body is the whole conditional expression. Line 4 puts each element in twice.

## 4. Write it with reduce ★★

**Skill:** choose the initial value and the combining function.

Write one-liners with `reduce`: `count_if(pred, xs)` (how many elements satisfy `pred`) and `llist_max(xs)` for a non-empty llist.

??? success "Answer"
    ```python title="§2"
    def count_if(pred, xs):
        return reduce(lambda x, n: n + 1 if pred(x) else n, 0, xs)

    def llist_max(xs):
        return reduce(lambda x, best: max(x, best), head(xs), tail(xs))

    print(count_if(lambda x: x > 2, llist(5, 1, 3, 2)))
    print(count_if(lambda x: x > 2, None))
    print(llist_max(llist(4, 9, 2)), llist_max(llist(-7)), llist_max(llist(-3, -8)))
    ```
    ```text
    2
    0
    9 -7 -3
    ```

    For counting, the result for the empty llist is 0. For the maximum there is no good value for the empty llist (0 would be wrong for `llist(-3, -8)`), so start from `head(xs)` and fold over the tail.

## 5. Write it: zip_with ★★

**Skill:** recursion over two llists at once.

Write `zip_with(f, xs, ys)`: the llist of `f(x, y)` for elements at the same position. Stop when either llist runs out.

??? success "Answer"
    ```python title="§2"
    def zip_with(f, xs, ys):
        return (None if is_none(xs) or is_none(ys)
                else pair(f(head(xs), head(ys)), zip_with(f, tail(xs), tail(ys))))

    print_llist(zip_with(lambda a, b: a + b, llist(1, 2, 3), llist(10, 20, 30)))
    print_llist(zip_with(lambda a, b: pair(a, b), llist("a", "b", "c"), llist(1, 2)))
    print_llist(zip_with(max, None, llist(1)))
    ```
    ```text
    llist(11, 22, 33)
    llist(['a', 1], ['b', 2])
    llist()
    ```

    Both llists move one step at a time. The base case checks both, because `head(None)` would fail on the shorter one. Brackets let a long conditional expression span two lines. Strings inside a pair print with single quotes.

## 6. Write it: positions ★★

**Skill:** carry an index along with a recursion.

Write `positions(v, xs)`: the llist of the 0-based positions at which `v` occurs in `xs`.

??? success "Answer"
    ```python title="§2"
    def positions(v, xs):
        def go(ys, i):
            return (None if is_none(ys)
                    else pair(i, go(tail(ys), i + 1)) if head(ys) == v
                    else go(tail(ys), i + 1))
        return go(xs, 0)

    print_llist(positions(7, llist(7, 1, 7, 7, 2)))
    print_llist(positions("x", llist("a", "b")))
    ```
    ```text
    llist(0, 2, 3)
    llist()
    ```

    The llist itself does not know positions, so the helper `go` takes the position of `head(ys)` as an extra parameter. An empty result is `None`, which `print_llist` shows as `llist()`.

## 7. Write it: interleave ★★

**Skill:** swap the roles of two arguments in the recursive call.

Write `interleave(xs, ys)`: first of `xs`, first of `ys`, second of `xs`, ...; when one llist runs out, the rest of the other follows.

??? success "Answer"
    ```python title="§2"
    def interleave(xs, ys):
        return ys if is_none(xs) else pair(head(xs), interleave(ys, tail(xs)))

    print_llist(interleave(llist(1, 2, 3), llist("a", "b")))
    print_llist(interleave(None, llist(5, 6)))
    ```
    ```text
    llist(1, 'a', 2, 'b', 3)
    llist(5, 6)
    ```

    After taking the head of `xs`, it is the other llist's turn, so the recursive call passes `ys` first and the rest of `xs` second. This handles every case with one base case: whichever llist is empty first, the other is returned whole.

## 8. The cost of append ★★

**Skill:** Θ of `append(xs, ys)` depends on xs only.

Give Θ of time for `append(a, b)` where `a` has n elements. Which is faster: `append(long, short)` or `append(short, long)`? How many new pairs does each make?

??? success "Answer"
    Θ(n) time, n = length of the **first** llist. `append` copies the first llist (n new pairs) and shares the second one (no copy).

    ```python title="§2"
    long = enum_llist(1, 200)
    longer = enum_llist(1, 400)
    short = llist(1)
    measure(append, long, short)
    measure(append, longer, short)
    measure(append, short, longer)
    ```
    ```text
    [measure] append([1, [2, [3, [4, [..., [1, None]): 403 calls, 3,815 steps, at most 1 waiting at once
    [measure] append([1, [2, [3, [4, [..., [1, None]): 803 calls, 7,615 steps, at most 1 waiting at once
    [measure] append([1, None], [1, [2, [3, [4, [...): 5 calls, 34 steps, at most 1 waiting at once
    ```

    Doubling the first llist doubles the steps; a 400-element second llist costs almost nothing. Space is Θ(n) too: the n new pairs, and while it runs, n deferred operations. ("At most 1 waiting" because the library's `append` is written in CPS: its deferred operations are kept as functions, which still take Θ(n) space.)

## 9. Adding at the end ★★★

**Skill:** a Θ(n) operation inside a loop of n steps.

Both functions build `llist(1, 2, ..., n)`. Give Θ of time for each.

```python
def build_slow(n):
    def go(k, acc):
        return acc if k > n else go(k + 1, append(acc, llist(k)))
    return go(1, None)

def build_fast(n):
    def go(k, acc):
        return reverse(acc) if k > n else go(k + 1, pair(k, acc))
    return go(1, None)
```

??? success "Answer"
    `build_slow`: Θ(n²). `build_fast`: Θ(n).

    ```python title="§2"
    def build_slow(n):
        def go(k, acc):
            return acc if k > n else go(k + 1, append(acc, llist(k)))
        return go(1, None)

    def build_fast(n):
        def go(k, acc):
            return reverse(acc) if k > n else go(k + 1, pair(k, acc))
        return go(1, None)

    print_llist(build_slow(5))
    print_llist(build_fast(5))
    measure(build_slow, 100)
    measure(build_slow, 200)
    measure(build_fast, 100)
    measure(build_fast, 200)
    ```
    ```text
    llist(1, 2, 3, 4, 5)
    llist(1, 2, 3, 4, 5)
    [measure] build_slow(100): 10,302 calls, 97,162 steps, at most 2 waiting at once
    [measure] build_slow(200): 40,602 calls, 384,312 steps, at most 2 waiting at once
    [measure] build_fast(100): 204 calls, 3,026 steps, at most 1 waiting at once
    [measure] build_fast(200): 404 calls, 6,026 steps, at most 1 waiting at once
    ```

    `build_slow` appends to a llist of length 0, 1, 2, ..., n − 1: 0 + 1 + ... + (n − 1) = n(n − 1)/2 pairs copied, so doubling n multiplies the steps by 4. `build_fast` puts each number in front (Θ(1)), then reverses once at the end (Θ(n)). The same reasoning makes `reverse` written with `append` Θ(n²) and `reverse` with an accumulator Θ(n).

## 10. Write it: prefixes ★★★

**Skill:** wishful thinking that returns a llist of llists.

Write `prefixes(xs)`: the llist of all non-empty beginnings of `xs`, shortest first. `prefixes(llist(1, 2, 3))` is `llist(llist(1), llist(1, 2), llist(1, 2, 3))`.

??? success "Answer"
    ```python title="§2"
    def prefixes(xs):
        return (None if is_none(xs)
                else pair(llist(head(xs)),
                          map(lambda p: pair(head(xs), p), prefixes(tail(xs)))))

    print_llist(prefixes(llist(1, 2, 3)))
    print_llist(prefixes(llist("z")))
    print_llist(prefixes(None))
    ```
    ```text
    llist(llist(1), llist(1, 2), llist(1, 2, 3))
    llist(llist('z'))
    llist()
    ```

    Wishful thinking: suppose `prefixes(tail(xs))` works. For `llist(1, 2, 3)` it gives `llist(llist(2), llist(2, 3))`. Every prefix of the whole llist is either `llist(1)` alone, or 1 put in front of one of those: that is the `map`. The empty llist has no non-empty prefixes, so the base case is `None`.

*In the course: L5A, R5, S6 · SICPy 2.2.1, 2.2.3.*
