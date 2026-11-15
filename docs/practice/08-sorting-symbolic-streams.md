# Drills: Sorting, symbolic data & streams I

<p class="chapter-goal">Eleven problems on sorting llists (with best and worst cases), binary search trees, evaluators for tagged llists, and streams written by hand.</p>

All programs run as Python §2. The stream library only arrives in §3, so the streams here are built by hand, as in the lectures: a stream is `None` or a pair whose tail is a nullary function (a function of no arguments) that returns a stream.

The sorting problems use these two functions:

```python title="§2"
def insert(x, xs):
    return (llist(x) if is_none(xs)
            else pair(x, xs) if x <= head(xs)
            else pair(head(xs), insert(x, tail(xs))))

def insertion_sort(xs):
    return None if is_none(xs) else insert(head(xs), insertion_sort(tail(xs)))

print_llist(insertion_sort(llist(3, 1, 2)))
```
```text title="Output"
llist(1, 2, 3)
```

## 1. Trace an insert ★

**Skill:** follow one insertion step by step.

How many calls of `insert` does `insert(5, llist(1, 4, 6, 9))` make, and which pairs are new?

??? success "Answer"
    Three calls.

    ```python title="§2"
    def insert(x, xs):
        return (llist(x) if is_none(xs)
                else pair(x, xs) if x <= head(xs)
                else pair(head(xs), insert(x, tail(xs))))

    print(trace(insert, 5, llist(1, 4, 6, 9)))
    ```
    ```text
    → insert(5, [1, [4, [6, [9, None]]]])
    │  → insert(5, [4, [6, [9, None]]])
    │  │  → insert(5, [6, [9, None]])
    │  │  ← [5, [6, [9, None]]]
    │  ← [4, [5, [6, [9, None]]]]
    ← [1, [4, [5, [6, [9, None]]]]]
    [1, [4, [5, [6, [9, None]]]]]
    ```

    `insert` walks past every element smaller than 5 and stops at the first one that is ≥ 5. The three new pairs hold 1, 4 and 5; the pairs holding 6 and 9 are the old ones, shared with the input. Each call that walks past an element leaves a `pair(head(xs), ...)` waiting: a recursive process.

## 2. Best and worst case of insertion sort ★★

**Skill:** find the inputs that make a sort fast or slow, and give Θ for each.

For this `insertion_sort`, which input order of n numbers is the best case, which the worst? Give Θ of time for each.

??? success "Answer"
    Best case: already sorted (ascending), Θ(n). Worst case: sorted the other way (descending), Θ(n²). Space is Θ(n) in both.

    ```python title="§2"
    def insert(x, xs):
        return (llist(x) if is_none(xs)
                else pair(x, xs) if x <= head(xs)
                else pair(head(xs), insert(x, tail(xs))))

    def insertion_sort(xs):
        return None if is_none(xs) else insert(head(xs), insertion_sort(tail(xs)))

    measure(insertion_sort, enum_llist(1, 100))
    measure(insertion_sort, enum_llist(1, 200))
    measure(insertion_sort, reverse(enum_llist(1, 100)))
    measure(insertion_sort, reverse(enum_llist(1, 200)))
    ```
    ```text
    [measure] insertion_sort([1, [2, [3, [4, [...): 201 calls, 2,999 steps, at most 101 waiting at once
    [measure] insertion_sort([1, [2, [3, [4, [...): 401 calls, 5,999 steps, at most 201 waiting at once
    [measure] insertion_sort([100, [99, [98, [...): 5,151 calls, 111,206 steps, at most 101 waiting at once
    [measure] insertion_sort([200, [199, [198,...): 20,301 calls, 442,406 steps, at most 201 waiting at once
    ```

    The head is inserted into the **sorted tail**. If the input is ascending, the head is smaller than everything in the tail and `insert` stops at once: one step per element. If it is descending, the head is the biggest and must walk to the end of the sorted tail: 1 + 2 + ... + (n − 1) steps. Doubling n doubles the steps in the first case and multiplies them by 4 in the second.

## 3. Merge ★★

**Skill:** predict `merge` and count its comparisons.

```python title="§2"
def merge(xs, ys):
    return (ys if is_none(xs) else xs if is_none(ys)
            else pair(head(xs), merge(tail(xs), ys)) if head(xs) <= head(ys)
            else pair(head(ys), merge(xs, tail(ys))))

print_llist(merge(llist(1, 4, 9), llist(2, 3, 10)))
print_llist(merge(llist(5, 6), llist(1, 2, 3)))
```

??? success "Answer"
    ```text
    llist(1, 2, 3, 4, 9, 10)
    llist(1, 2, 3, 5, 6)
    ```

    Each step compares the two heads and takes the smaller. Merging llists of lengths m and n makes at most m + n − 1 comparisons, so `merge` is Θ(m + n) time. In the second example, after taking 1, 2, 3 the second llist is empty and the rest `llist(5, 6)` is returned whole: only 3 comparisons.

## 4. Write it: merge sort with a different split ★★★

**Skill:** divide and conquer; give Θ with the level argument.

Instead of splitting a llist into its first and second half, split it into the elements at even positions and those at odd positions. Write `split_alt(xs)` (returns a pair of two llists) and `merge_sort(xs)` using it and `merge` from problem 3. Give Θ of time.

??? success "Answer"
    ```python title="§2"
    def merge(xs, ys):
        return (ys if is_none(xs) else xs if is_none(ys)
                else pair(head(xs), merge(tail(xs), ys)) if head(xs) <= head(ys)
                else pair(head(ys), merge(xs, tail(ys))))

    def split_alt(xs):
        if is_none(xs) or is_none(tail(xs)):
            return pair(xs, None)
        else:
            rest = split_alt(tail(tail(xs)))
            return pair(pair(head(xs), head(rest)), pair(head(tail(xs)), tail(rest)))

    def merge_sort(xs):
        if is_none(xs) or is_none(tail(xs)):
            return xs
        else:
            halves = split_alt(xs)
            return merge(merge_sort(head(halves)), merge_sort(tail(halves)))

    print(split_alt(llist(1, 2, 3, 4, 5)))
    print_llist(merge_sort(llist(8, 3, 5, 1, 9, 2)))
    print_llist(merge_sort(None))
    ```
    ```text
    [[1, [3, [5, None]]], [2, [4, None]]]
    llist(1, 2, 3, 5, 8, 9)
    llist()
    ```

    Θ(n log n). Each level of the recursion splits and merges llists whose lengths add up to n, so each level costs Θ(n). Each level halves the lengths, so there are about log₂ n levels. Why use a conditional statement: `rest` and `halves` must be computed only when the llist has two or more elements, otherwise the recursion would never stop.

## 5. Build a BST with reduce ★★

**Skill:** BST insertion, and remembering that `reduce` folds from the right.

A binary search tree is `None` or `llist(entry, left, right)`, with smaller entries on the left. What tree does the last line build? Which number is at the root?

```python title="§2"
def make_bst(entry, left, right):
    return llist(entry, left, right)

def entry(t):
    return head(t)

def left(t):
    return head(tail(t))

def right(t):
    return head(tail(tail(t)))

def bst_insert(t, x):
    return (make_bst(x, None, None) if is_none(t)
            else t if x == entry(t)
            else make_bst(entry(t), bst_insert(left(t), x), right(t)) if x < entry(t)
            else make_bst(entry(t), left(t), bst_insert(right(t), x)))

t = reduce(lambda x, tree: bst_insert(tree, x), None, llist(5, 2, 8, 1))
print_llist(t)
```

??? success "Answer"
    ```text
    llist(1, llist(), llist(8, llist(2, llist(), llist(5, llist(), llist())), llist()))
    ```

    The root is **1**, not 5. `reduce` is `f(5, f(2, f(8, f(1, None))))`, so 1 is inserted first, then 8, then 2, then 5. 1 is the root; 8 goes right of 1; 2 is bigger than 1 and smaller than 8, so it goes left of 8; 5 goes right of 2. The selectors are the only functions that know a tree is a llist of three elements.

## 6. When is a BST slow? ★★

**Skill:** Θ of BST search depends on the shape of the tree.

Give Θ of `bst_contains(t, x)` for a tree of n entries that is balanced, and for one built by inserting entries in sorted order.

??? success "Answer"
    Balanced: Θ(log n). Built from sorted input: Θ(n).

    ```python title="§2"
    def make_bst(entry, left, right):
        return llist(entry, left, right)

    def entry(t):
        return head(t)

    def left(t):
        return head(tail(t))

    def right(t):
        return head(tail(tail(t)))

    def bst_insert(t, x):
        return (make_bst(x, None, None) if is_none(t)
                else t if x == entry(t)
                else make_bst(entry(t), bst_insert(left(t), x), right(t)) if x < entry(t)
                else make_bst(entry(t), left(t), bst_insert(right(t), x)))

    def bst_contains(t, x):
        return (False if is_none(t)
                else True if x == entry(t)
                else bst_contains(left(t), x) if x < entry(t)
                else bst_contains(right(t), x))

    def build(xs):
        return reduce(lambda x, tree: bst_insert(tree, x), None, xs)

    chain = build(enum_llist(1, 15))
    bal = build(llist(1, 3, 2, 5, 7, 6, 4, 9, 11, 10, 13, 15, 14, 12, 8))
    print(entry(chain), entry(bal), bst_contains(bal, 6), bst_contains(bal, 16))
    measure(bst_contains, chain, 1)
    measure(bst_contains, bal, 1)
    ```
    ```text
    15 8 True False
    [measure] bst_contains([15, [[14, [[13, ..., 1): 58 calls, 534 steps, at most 2 waiting at once
    [measure] bst_contains([8, [[4, [[2, [[1..., 1): 14 calls, 127 steps, at most 2 waiting at once
    ```

    Each step of the search goes one level down, so the time is the height of the tree. `chain` was built from sorted input: every entry went to the same side, so it is a llist in disguise, 15 levels deep. `bal` has 4 levels (15 = 2⁴ − 1). The calls counted include the selectors, a constant number per level. The search is a chain of tail calls, so space is Θ(1).

## 7. Write it: an evaluator for tagged llists ★★

**Skill:** constructors, predicates, selectors, and an evaluator that dispatches on the tag.

An expression is a number, `llist("max", e1, e2)` or `llist("neg", e)`. Write the constructors `make_max` and `make_neg`, the predicates `is_max` and `is_neg`, selectors, and `evaluate(e)`. An unknown expression is an error.

??? success "Answer"
    ```python title="§2"
    def make_max(a, b):
        return llist("max", a, b)

    def make_neg(e):
        return llist("neg", e)

    def is_tagged(e, tag):
        return is_pair(e) and head(e) == tag

    def is_max(e):
        return is_tagged(e, "max")

    def is_neg(e):
        return is_tagged(e, "neg")

    def first_operand(e):
        return head(tail(e))

    def second_operand(e):
        return head(tail(tail(e)))

    def evaluate(e):
        if is_number(e):
            return e
        elif is_max(e):
            return max(evaluate(first_operand(e)), evaluate(second_operand(e)))
        elif is_neg(e):
            return -evaluate(first_operand(e))
        else:
            return error(e, "unknown expression type")

    e = make_neg(make_max(3, make_neg(7)))
    print_llist(e)
    print(evaluate(e))
    print(evaluate(make_max(make_neg(2), make_neg(5))))
    print(evaluate(llist("min", 1, 2)))
    ```
    ```text
    llist('neg', llist('max', 3, llist('neg', 7)))
    -3
    -2
    Error: ['min', [1, [2, None]]] unknown expression type
    ```

    One branch of `evaluate` per kind of expression, each evaluating its operands recursively. `is_tagged` checks `is_pair` first; `and` then skips `head(e)` for a number, where it would fail. Only the constructors, predicates and selectors know the tag strings and positions.

## 8. Simplify in the constructors ★★★

**Skill:** put simplification rules into the constructors, so every expression built is already simplified.

Now expressions may also contain names (strings) such as `"x"`. Change `make_neg` and `make_max` so that: `make_neg` of a number is that number negated; `make_neg(make_neg(e))` is `e`; `make_max` of two numbers is the larger; `make_max(e, e)` is `e`.

??? success "Answer"
    ```python title="§2"
    def make_neg(e):
        return (-e if is_number(e)
                else head(tail(e)) if is_pair(e) and head(e) == "neg"
                else llist("neg", e))

    def make_max(a, b):
        return (max(a, b) if is_number(a) and is_number(b)
                else a if a == b
                else llist("max", a, b))

    print(make_neg(make_neg("x")))
    print(make_neg(make_max(3, make_neg(7))))
    print_llist(make_max("y", make_neg("x")))
    print_llist(make_max(make_neg("x"), make_neg("x")))
    ```
    ```text
    x
    -3
    llist('max', 'y', llist('neg', 'x'))
    llist('neg', 'x')
    ```

    Applicative order makes this work: the inner constructors run first and return simplified pieces, so the outer constructor only has to look one level deep. `make_max(3, make_neg(7))` becomes `make_max(3, -7)`, which is the number 3. `a == b` compares two expressions structurally, which `==` does for pairs in §2.

## 9. Streams by hand: what is forced? ★

**Skill:** a stream's tail is a function; applying it gives the rest.

```python title="§2"
s = pair(1, lambda: pair(2, lambda: None))
print(head(s))
print(tail(s))
print(head(tail(s)()))
print(tail(tail(s)())())
```

??? success "Answer"
    ```text
    1
    <function (anonymous)>
    2
    None
    ```

    `tail(s)` is the nullary function itself, not the rest of the stream. Applying it, `tail(s)()`, gives the stream `pair(2, ...)`. Forcing that one's tail gives `None`, the end of the stream. (`stream_tail(s)` in §3 is exactly `tail(s)()`.)

## 10. Write it: an infinite stream by hand ★★

**Skill:** a stream function that never reaches a base case, and a function that takes a finite part of it.

Write `powers_from(b, p)`, the infinite stream p, p·b, p·b², ..., and `first_n(s, n)`, the llist of the first n elements of a stream.

??? success "Answer"
    ```python title="§2"
    def powers_from(b, p):
        return pair(p, lambda: powers_from(b, p * b))

    def first_n(s, n):
        return None if n == 0 or is_none(s) else pair(head(s), first_n(tail(s)(), n - 1))

    print_llist(first_n(powers_from(3, 1), 5))
    print_llist(first_n(powers_from(2, 5), 4))
    print_llist(first_n(pair(7, lambda: None), 3))
    ```
    ```text
    llist(1, 3, 9, 27, 81)
    llist(5, 10, 20, 40)
    llist(7)
    ```

    `powers_from` has no base case, and that is fine: the recursive call is inside a lambda, so it only runs when someone forces the tail. `first_n` forces at most n tails and stops. It also stops early at the end of a finite stream.

## 11. Count the forcings ★★★

**Skill:** laziness traces: exactly which tails get forced, and when.

`loud_from(n)` is the stream n, n + 1, ... that prints a line every time a tail is forced. What does this program print?

```python title="§2"
def next_loud(n):
    print("forcing", n)
    return loud_from(n)

def loud_from(n):
    return pair(n, lambda: next_loud(n + 1))

def first_n(s, n):
    return None if n == 0 or is_none(s) else pair(head(s), first_n(tail(s)(), n - 1))

def s_filter(p, s):
    return (None if is_none(s)
            else pair(head(s), lambda: s_filter(p, tail(s)())) if p(head(s))
            else s_filter(p, tail(s)()))

print_llist(first_n(loud_from(0), 3))
threes = s_filter(lambda x: x % 3 == 0, loud_from(1))
print("made it")
print(head(tail(threes)()))
print(head(tail(threes)()))
```

??? success "Answer"
    ```text
    forcing 1
    forcing 2
    forcing 3
    llist(0, 1, 2)
    forcing 2
    forcing 3
    made it
    forcing 4
    forcing 5
    forcing 6
    6
    forcing 4
    forcing 5
    forcing 6
    6
    ```

    - `first_n(..., 3)` forces **three** tails for three elements: it forces the tail after 2 before it checks that n is now 0. (Change the recursive call to `None if n == 1 else first_n(...)` to save that one.)
    - `s_filter` forces tails right away until it finds a head that passes: 1 and 2 fail, 3 passes, so building `threes` already prints twice, before "made it".
    - Forcing the tail of `threes` searches on from 3 to 6.
    - These streams are not memoized: forcing the same tail again does all the work again, so the last line prints the three lines once more. (Memoization comes in L11A.)

*In the course: L6A, L7B, R6, S7, S8 · SICPy 2.3.2, 2.3.3, 2.4.*
