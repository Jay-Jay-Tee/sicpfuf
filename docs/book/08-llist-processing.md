# 8. Llist processing: map, filter, reduce

<p class="chapter-goal">Write length, append and reverse yourself, know what they cost, then let map, filter and reduce do the walking.</p>

!!! abstract "The big idea, in plain words"
    A llist is a train: each carriage (pair) carries one parcel and is coupled to the rest of the train.
    Almost every llist function does the same walk: "if there is no train, answer the easy thing; otherwise
    deal with the first carriage and **trust a recursive call** with the rest". After writing that walk a few
    times you notice three patterns that cover most jobs: change every parcel (**map**), keep some parcels
    (**filter**), combine all parcels into one value (**reduce**).

## 1. The llist recipe

Every function in this chapter has the shape:

1. **Base case**: `is_none(xs)`. What is the answer for the empty llist?
2. **Reduction step**: assume (wishful thinking) the function already works on `tail(xs)`. How do you get
   the answer for `xs` from `head(xs)` and that result?

`length` is the smallest example, as a recursive and as an iterative process:

```python title="§2"
def length_rec(xs):
    return 0 if is_none(xs) else 1 + length_rec(tail(xs))

def length_iter(xs):
    def count(ys, so_far):
        return so_far if is_none(ys) else count(tail(ys), so_far + 1)
    return count(xs, 0)

print(length_rec(llist(5, 6, 7)), length_iter(llist(5, 6, 7)))
measure(length_rec, enum_llist(1, 200))
measure(length_iter, enum_llist(1, 200))
```
```text title="Output"
3 3
[measure] length_rec([1, [2, [3, [4, [...): 201 calls, 2,406 steps, at most 201 waiting at once
[measure] length_iter([1, [2, [3, [4, [...): 202 calls, 2,612 steps, at most 1 waiting at once
```

Both take Θ(n) time for a llist of length n. `length_rec` leaves a deferred `1 + ...` per element: Θ(n)
space. `length_iter` ends in a tail call: Θ(1) space.

## 2. append

`append(xs, ys)` makes a llist of the elements of `xs` followed by those of `ys`. Wishful thinking: if
`append(tail(xs), ys)` already works, put `head(xs)` in front of its result.

```python title="§2 · --subst"
def app(xs, ys):
    return ys if is_none(xs) else pair(head(xs), app(tail(xs), ys))

app(llist(1, 2), llist(3))
```
```text title="Output"
app(llist(1, 2), llist(3))
-> app([1, [2, None]], llist(3))
-> app([1, [2, None]], [3, None])
-> [3, None] if is_none([1, [2, None]]) else pair(head([1, [2, None]]), app(tail([1, [2, None]]), [3, None]))
-> [3, None] if False else pair(head([1, [2, None]]), app(tail([1, [2, None]]), [3, None]))
-> pair(head([1, [2, None]]), app(tail([1, [2, None]]), [3, None]))
-> pair(1, app(tail([1, [2, None]]), [3, None]))
-> pair(1, app([2, None], [3, None]))
-> pair(1, [3, None] if is_none([2, None]) else pair(head([2, None]), app(tail([2, None]), [3, None])))
-> pair(1, [3, None] if False else pair(head([2, None]), app(tail([2, None]), [3, None])))
-> pair(1, pair(head([2, None]), app(tail([2, None]), [3, None])))
-> pair(1, pair(2, app(tail([2, None]), [3, None])))
-> pair(1, pair(2, app(None, [3, None])))
-> pair(1, pair(2, [3, None] if is_none(None) else pair(head(None), app(tail(None), [3, None]))))
-> pair(1, pair(2, [3, None] if True else pair(head(None), app(tail(None), [3, None]))))
-> pair(1, pair(2, [3, None]))
-> pair(1, [2, [3, None]])
-> [1, [2, [3, None]]]
```

Two facts to remember:

- Every pair of `xs` is **copied** (one new `pair` per element), but `ys` is **reused** as it is: the
  last new pair points at the very same `ys`.
- Time Θ(n) where n is the length of the **first** llist. The length of `ys` does not matter.

!!! warning "Trap: append is not pair"
    `pair(xs, ys)` puts the whole llist `xs` into one box: `pair(llist(1, 2), llist(3))` is
    `llist(llist(1, 2), 3)`, a llist of 2 elements, not 3. Only `append` joins two llists.

## 3. reverse, three ways

**Attempt 1** pairs the reversed tail with the head. Wrong shape:

```python title="§2"
def rev_wrong(xs):
    return None if is_none(xs) else pair(rev_wrong(tail(xs)), head(xs))

print(rev_wrong(llist(1, 2, 3)))
```
```text title="Output"
[[[None, 3], 2], 1]
```

Each element lands in a tail and each rest lands in a head: a left-nested structure, not a llist.

**Attempt 2** appends a one-element llist at the end. Correct, but each `append` walks the whole reversed
part again: 1 + 2 + … + n steps, so **Θ(n²)** time.

**Attempt 3** moves elements one at a time onto an accumulator, like moving a stack of plates. **Θ(n)**
time, and an iterative process.

```python title="§2"
def app(xs, ys):
    return ys if is_none(xs) else pair(head(xs), app(tail(xs), ys))

def rev_slow(xs):
    return None if is_none(xs) else app(rev_slow(tail(xs)), llist(head(xs)))

def rev_fast(xs):
    def move(original, done):
        return done if is_none(original) else move(tail(original), pair(head(original), done))
    return move(xs, None)

print(rev_slow(llist(1, 2, 3)), rev_fast(llist(1, 2, 3)))
measure(rev_slow, enum_llist(1, 100))
measure(rev_slow, enum_llist(1, 200))
measure(rev_fast, enum_llist(1, 200))
```
```text title="Output"
[3, [2, [1, None]]] [3, [2, [1, None]]]
[measure] rev_slow([1, [2, [3, [4, [...): 5,151 calls, 81,506 steps, at most 101 waiting at once
[measure] rev_slow([1, [2, [3, [4, [...): 20,301 calls, 323,006 steps, at most 201 waiting at once
[measure] rev_fast([1, [2, [3, [4, [...): 202 calls, 3,212 steps, at most 1 waiting at once
```

Doubling the length makes `rev_slow` about four times slower (quadratic) and `rev_fast` about twice as
slow (linear).

??? example "X-ray: watch the accumulator fill up"
    `--trace move` shows each tail call (`↻`) replacing the previous one. Nothing waits.

    ```python title="§2 · --trace move"
    def rev_fast(xs):
        def move(original, done):
            return done if is_none(original) else move(tail(original), pair(head(original), done))
        return move(xs, None)

    print(rev_fast(llist(1, 2, 3)))
    ```
    ```text title="Output"
    → move([1, [2, [3, None]]], None)
    ↻ move([2, [3, None]], [1, None])
    ↻ move([3, None], [2, [1, None]])
    ↻ move(None, [3, [2, [1, None]]])
    ← [3, [2, [1, None]]]
    [3, [2, [1, None]]]
    ```

## 4. Counting space in Unit 2

In Unit 1, space meant deferred operations. With llists we also count **pairs**:

- Only a call of `pair(...)` (or `llist(...)`) makes a new pair. `head`, `tail` and passing a llist to a
  function copy nothing.
- Count the most pairs (and deferred operations) that must be **remembered at the same moment**, not the
  total ever made. A pair that nothing points to any more can be forgotten.

| Function | Time | Space |
|---|---|---|
| `length_rec(xs)` | Θ(n) | Θ(n) deferred operations |
| `length_iter(xs)` | Θ(n) | Θ(1) |
| `app(xs, ys)`, n = length of `xs` | Θ(n) | Θ(n): n deferred `pair`s, then n new pairs |
| `rev_slow(xs)` | Θ(n²) | Θ(n) |
| `rev_fast(xs)` | Θ(n) | Θ(n): the n new pairs of the result |

`rev_fast` has no deferred operations, but its answer is n new pairs, so its space is still Θ(n).

## 5. map and filter

Doubling every element and squaring every element are the same walk with a different job in the middle.
Pull the job out as a parameter and you get **map**. Keeping only some elements gives **filter**.

```python title="§2"
def my_map(f, xs):
    return None if is_none(xs) else pair(f(head(xs)), my_map(f, tail(xs)))

def my_filter(keep, xs):
    return (None if is_none(xs)
            else pair(head(xs), my_filter(keep, tail(xs))) if keep(head(xs))
            else my_filter(keep, tail(xs)))

prices = llist(120, 45, 300, 80)
print_llist(my_map(lambda p: p // 2, prices))
print_llist(my_filter(lambda p: p < 100, prices))
print_llist(map(lambda p: p // 2, prices))
print_llist(filter(lambda p: p < 100, prices))
```
```text title="Output"
llist(60, 22, 150, 40)
llist(45, 80)
llist(60, 22, 150, 40)
llist(45, 80)
```

The library's `map(f, xs)` and `filter(pred, xs)` do the same: the **function comes first**, the order of
elements is kept, and the result is a **new** llist (the input is untouched).

!!! warning "Trap: lambda precedence"
    A lambda expression reaches as far right as it can. In `lambda x: x * 2 if x > 0 else 0` the body
    is the whole conditional expression. If you meant "this lambda, or else 0", write
    `(lambda x: x * 2) if ... else 0`; otherwise the `x` in the predicate would be outside the lambda.
    Function application binds tightest, then the conditional expression, then `lambda`.

## 6. reduce: a right fold

`reduce(f, initial, xs)` combines all elements with a two-argument function `f`, starting from `initial`
**at the right end**:

    reduce(f, init, llist(1, 2, 3))   is   f(1, f(2, f(3, init)))

```python title="§2"
def my_reduce(f, initial, xs):
    return initial if is_none(xs) else f(head(xs), my_reduce(f, initial, tail(xs)))

show = lambda x, rest: "(" + str(x) + " + " + rest + ")"
print(my_reduce(show, "0", llist(1, 2, 3)))
print(reduce(show, "0", llist(1, 2, 3)))
print(reduce(lambda x, rest: x + rest, 0, llist(1, 2, 3)))
print(reduce(lambda x, rest: x - rest, 0, llist(1, 2, 3)))
```
```text title="Output"
(1 + (2 + (3 + 0)))
(1 + (2 + (3 + 0)))
6
2
```

The last line is 1 − (2 − (3 − 0)) = 2, not 1 − 2 − 3. The bracket picture tells you the result whenever
`f` is not as forgiving as `+`.

!!! warning "Trap: the argument order of f"
    `f`'s **first** parameter is the current element, the **second** is the already-reduced rest. Write
    `lambda x, acc: ...` in that order. Getting it backwards is the most common reduce bug, and it is
    invisible with `+` and `*` because they do not care about order.

`reduce` can build llists too, because `initial` and the result can be anything:

```python title="§2"
xs = llist(3, 8, 1)
print_llist(reduce(lambda x, acc: pair(x * 10, acc), None, xs))
print(reduce(lambda x, acc: max(x, acc), head(xs), xs))
print(reduce(lambda x, acc: acc + 1, 0, xs))
```
```text title="Output"
llist(30, 80, 10)
8
3
```

## 7. Pipelines of one-liners

`enum_llist(a, b)` makes `llist(a, a + 1, ..., b)` (both ends included). Chain it with the trio and many
problems become one line. Read a pipeline **from the inside out**: enumerate, then filter, then map, then
reduce.

```python title="§2"
# sum of the squares of the multiples of 3 between 1 and 12
print(reduce(lambda x, acc: x + acc, 0,
             map(lambda n: n * n,
                 filter(lambda n: n % 3 == 0, enum_llist(1, 12)))))

# a times-table row as strings
print_llist(map(lambda k: str(k) + "x7=" + str(k * 7), enum_llist(1, 3)))

# all pairs (i, j) with 1 <= i < j <= 3
print_llist(reduce(append, None,
                   map(lambda j: map(lambda i: pair(i, j), enum_llist(1, j - 1)),
                       enum_llist(1, 3))))
```
```text title="Output"
270
llist('1x7=7', '2x7=14', '3x7=21')
llist([1, 2], [1, 3], [2, 3])
```

The last example maps to a llist of llists and then flattens it with `reduce(append, None, ...)`.

## 8. member and remove

```python title="§2"
week = llist("mon", "tue", "wed", "tue")
print_llist(member("wed", week))
print(member("sun", week))
print_llist(remove("tue", week))
print_llist(remove_all("tue", week))
```
```text title="Output"
llist('wed', 'tue')
None
llist('mon', 'wed', 'tue')
llist('mon', 'wed')
```

- `member(v, xs)` returns the **rest of the llist starting at** the first `v`, or `None`. It is not a
  boolean: test it with `is_none(member(v, xs))`.
- `remove(v, xs)` drops only the **first** `v`; `remove_all` drops every one. Both compare with `==`.

!!! note "Aside: the library is iterative inside"
    Your own `my_map` leaves one deferred `pair` per element, so it dies past about 1000 elements. The
    library versions do not, because they are written in Python §2 as iterative processes (or in
    continuation-passing style, [next chapter](09-trees-cps.md)). From the prelude in
    `sicpfuf/lib/linked_list.py`:

    ```python
    def map(f, xs):
        def go(ys, done):
            return reverse(done) if is_none(ys) else go(tail(ys), pair(f(head(ys)), done))
        return go(xs, None)
    ```

    It builds the answer backwards on an accumulator and reverses it once at the end: still Θ(n) time.

    ```python title="§2"
    print(length(map(lambda x: x + 1, enum_llist(1, 5000))))
    ```
    ```text title="Output"
    5000
    ```

!!! note "Python §2 vs real Python"
    Real Python's `map` and `filter` take a function and a Python list (or any iterable) and return an
    iterator, not a llist. Real Python's `reduce` lives in `functools`, takes `(f, items, initial)` and folds
    from the **left**, calling `f(acc, x)`. Do not mix the two up in the exam: the course's `reduce` is
    `reduce(f, initial, xs)`, a right fold calling `f(x, acc)`.

## Takeaways

- Llist recursion: base case `is_none(xs)`, reduction step on `tail(xs)`, trust the recursive call.
- `append(xs, ys)`: Θ(length of `xs`) time; copies `xs`, shares `ys`.
- `reverse` with an accumulator is Θ(n); with `append` it is Θ(n²); pairing the wrong way is not a llist.
- Space in Unit 2 = deferred operations **plus** pairs that must be remembered at once. Only `pair` and
  `llist` make pairs.
- `map(f, xs)`, `filter(pred, xs)`: function first, order kept, new llist.
- `reduce(f, init, xs)` is `f(x1, f(x2, ... f(xn, init)))`; `f(element, rest_result)`.
- Pipelines read inside out: `reduce(..., map(..., filter(..., enum_llist(a, b))))`.
- `member` returns a sub-llist or `None`; `remove` removes the first match only.

## Check yourself

1. What does `reduce(lambda x, acc: acc * 10 + x, 0, llist(1, 2, 3))` give? Work it out before running it.

    ??? success "Answer"
        Inside out: `f(3, 0)` = 3, `f(2, 3)` = 32, `f(1, 32)` = 321. The digits come out reversed because
        the fold starts at the right.

        ```python title="§2"
        print(reduce(lambda x, acc: acc * 10 + x, 0, llist(1, 2, 3)))
        ```
        ```text
        321
        ```

2. State the order of growth in time and space of `app(xs, ys)` where `xs` has length n and `ys` has length m.

    ??? success "Answer"
        Time Θ(n): one step per element of `xs`, `ys` is never walked. Space Θ(n): up to n deferred `pair`
        operations, then n new pairs in the result (`ys` is shared, not copied).

3. Write `count_if(pred, xs)`, the number of elements satisfying `pred`, as a one-liner with the library.

    ??? success "Answer"

        ```python title="§2"
        def count_if(pred, xs):
            return length(filter(pred, xs))

        print(count_if(lambda n: n % 2 == 0, enum_llist(1, 9)))
        print(count_if(lambda s: s == "a", llist("a", "b", "a")))
        ```
        ```text
        4
        2
        ```

4. Why does `rev_wrong(llist(1, 2))` not print as a llist? Give its box notation.

    ??? success "Answer"
        Each element is placed in the **tail** of a pair whose head is the rest, so the last tail is a number,
        not `None`.

        ```python title="§2"
        def rev_wrong(xs):
            return None if is_none(xs) else pair(rev_wrong(tail(xs)), head(xs))

        print(rev_wrong(llist(1, 2)))
        print(is_llist(rev_wrong(llist(1, 2))))
        ```
        ```text
        [[None, 2], 1]
        False
        ```

5. Predict both lines.

    ```python
    xs = llist(4, 9, 4, 1)
    print_llist(remove(4, map(lambda x: x + 0, xs)))
    print_llist(member(4, tail(xs)))
    ```

    ??? success "Answer"
        `remove` drops the first 4 only; `member` searches `llist(9, 4, 1)` and returns the rest from the 4.

        ```python title="§2"
        xs = llist(4, 9, 4, 1)
        print_llist(remove(4, map(lambda x: x + 0, xs)))
        print_llist(member(4, tail(xs)))
        ```
        ```text
        llist(9, 4, 1)
        llist(4, 1)
        ```

6. Write `flatten_once(xss)`, which turns a llist of llists into one llist, using `reduce`.

    ??? success "Answer"
        Append each inner llist in front of the flattened rest.

        ```python title="§2"
        def flatten_once(xss):
            return reduce(append, None, xss)

        print_llist(flatten_once(llist(llist(1, 2), None, llist(3))))
        ```
        ```text
        llist(1, 2, 3)
        ```

7. A student writes `reduce(lambda acc, x: acc - x, 0, llist(5, 3))` hoping for 0 − 5 − 3 = −8. What do
   they get, and why?

    ??? success "Answer"
        The first parameter is the element and the second the reduced rest, whatever the names say:
        `f(5, f(3, 0))` = `5 - (3 - 0)` = 2.

        ```python title="§2"
        print(reduce(lambda acc, x: acc - x, 0, llist(5, 3)))
        ```
        ```text
        2
        ```

*In the course: L5A · SICPy 2.2.1, 2.2.3.*
