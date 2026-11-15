# Drills: Trees & CPS

<p class="chapter-goal">Ten problems on tree recursion over nested llists, continuation-passing style, the order in which continuations run, and the space a CPS function really uses.</p>

A **tree** (of numbers, say) is a llist whose elements are numbers or trees. Every tree function has the same three cases:

1. the tree is empty (`is_none(tree)`);
2. the first element is a subtree (`is_llist(head(tree))`): recurse into the head **and** the tail;
3. the first element is a data item: deal with it, recurse into the tail.

In **CPS** a function gets an extra argument `c`, the continuation: "what to do with my result". The base case applies `c`; the recursive call passes a new lambda that does the deferred work and then calls the old `c`. The top-level call passes `lambda x: x`.

All programs run as Python §2. Most use this tree:

```python title="§2"
t = llist(1, llist(2, 3), llist(llist(4)), 5)
print_llist(t)
```
```text title="Output"
llist(1, llist(2, 3), llist(llist(4)), 5)
```

## 1. Write it: tree_sum ★

**Skill:** the three-case tree recursion.

Write `tree_sum(tree)`, the sum of all the numbers in a tree of numbers.

??? success "Answer"
    ```python title="§2"
    def tree_sum(tree):
        if is_none(tree):
            return 0
        elif is_llist(head(tree)):
            return tree_sum(head(tree)) + tree_sum(tail(tree))
        else:
            return head(tree) + tree_sum(tail(tree))

    t = llist(1, llist(2, 3), llist(llist(4)), 5)
    print(tree_sum(t))
    print(tree_sum(llist(None, llist())))
    ```
    ```text
    15
    0
    ```

    An empty llist inside a tree is an empty subtree, not a data item, so it adds 0 (the second test). The `elif` must test `is_llist`, not `is_pair`: an empty subtree is `None`, which is a llist but not a pair.

## 2. What does map_tree make? ★

**Skill:** read a higher-order tree function.

```python title="§2"
def map_tree(f, tree):
    return map(lambda sub: map_tree(f, sub) if is_llist(sub) else f(sub), tree)

print_llist(map_tree(lambda x: x * 10, llist(1, llist(2, 3))))
print_llist(map_tree(lambda x: x % 2 == 0, llist(llist(1), 2, llist())))
```

??? success "Answer"
    ```text
    llist(10, llist(20, 30))
    llist(llist(False), True, llist())
    ```

    `map` walks along the top level. Each element that is itself a llist is handled by a recursive `map_tree`, every other element by `f`. The shape of the tree stays exactly the same, including the empty subtree at the end.

## 3. Write it: depth ★★

**Skill:** tree recursion with `reduce` over the elements.

The depth of a data item is 0. The depth of a llist is 1 + the largest depth of its elements (so an empty llist has depth 1). Write `depth(x)`.

??? success "Answer"
    ```python title="§2"
    def depth(x):
        return 0 if not is_llist(x) else 1 + reduce(lambda e, d: max(depth(e), d), 0, x)

    t = llist(1, llist(2, 3), llist(llist(4)), 5)
    print(depth(t), depth(llist(1, 2)), depth(None), depth(7))
    ```
    ```text
    3 1 1 0
    ```

    Here the recursion treats a tree as "a llist of elements", not as head and tail: `reduce` goes along the top level, and `depth(e)` goes down into each element. `4` in `t` sits inside three llists, so `t` has depth 3.

## 4. Stop early ★★

**Skill:** `or` does not evaluate its right operand once the left one is `True`.

Write `tree_contains(v, tree)`. Make sure it stops searching as soon as it finds `v`.

??? success "Answer"
    ```python title="§2"
    def tree_contains(v, tree):
        if is_none(tree):
            return False
        elif is_llist(head(tree)):
            return tree_contains(v, head(tree)) or tree_contains(v, tail(tree))
        else:
            return head(tree) == v or tree_contains(v, tail(tree))

    t = llist(1, llist(2, 3), llist(llist(4)), 5)
    print(tree_contains(4, t), tree_contains(6, t))
    print(trace(tree_contains, 1, t))
    ```
    ```text
    True False
    → tree_contains(1, [1, [[2, [3, None]], [[[4, ...)
    ← True
    True
    ```

    The trace shows one call only: `head(tree) == v` is `True` for the first element, so the rest of the tree is never searched. The `or` in the `else` branch is also a tail call: if the left side is `False`, the result is whatever the recursive call returns.

## 5. Convert to CPS ★★

**Skill:** turn a recursive process into CPS.

Convert `sum_rec` to CPS as `sum_cps(xs, c)`.

```python
def sum_rec(xs):
    return 0 if is_none(xs) else head(xs) + sum_rec(tail(xs))
```

??? success "Answer"
    ```python title="§2"
    def sum_cps(xs, c):
        return c(0) if is_none(xs) else sum_cps(tail(xs), lambda r: c(head(xs) + r))

    print(sum_cps(llist(1, 2, 3), lambda x: x))
    print(trace(sum_cps, llist(1, 2, 3), lambda x: x))
    ```
    ```text
    6
    → sum_cps([1, [2, [3, None]]], <function (anonymous)>)
    ↻ sum_cps([2, [3, None]], <function (anonymous)>)
    ↻ sum_cps([3, None], <function (anonymous)>)
    ↻ sum_cps(None, <function (anonymous)>)
    ← 6
    6
    ```

    Three steps: (1) add the parameter `c`; (2) where the old function **returned** a value (`0`), return `c(value)`; (3) where it did work after the recursive call (`head(xs) + ...`), make the recursive call a tail call and put that work in a new continuation: `lambda r: c(head(xs) + r)`, where `r` stands for the result of the rest. The trace shows only tail calls (`↻`).

## 6. In which order do continuations run? ★★

**Skill:** the last continuation made is the first one to run.

```python title="§2"
def say(n, r):
    print("finishing", n)
    return r + n

def down_cps(n, c):
    return c(0) if n == 0 else down_cps(n - 1, lambda r: c(say(n, r)))

print(down_cps(3, lambda x: x))
```

??? success "Answer"
    ```text
    finishing 1
    finishing 2
    finishing 3
    6
    ```

    Nothing is printed on the way down: `down_cps(3, ...)`, `(2, ...)`, `(1, ...)` only **build** continuations, each wrapping the previous one. The continuation made for n = 1 is the outermost wrapper, so the base case `c(0)` runs it first; it calls the one for n = 2, which calls the one for n = 3, which calls the identity. Same order as the deferred operations of the recursive version: innermost first.

## 7. Iterative, yet not constant space ★★

**Skill:** analyse the space of a CPS function.

`sum_cps` is a chain of tail calls. Is its space Θ(1)? Compare with `sum_rec`.

??? success "Answer"
    No. Its space is Θ(n), like `sum_rec`. But it is not limited by pending calls.

    ```python title="§2"
    def sum_rec(xs):
        return 0 if is_none(xs) else head(xs) + sum_rec(tail(xs))

    def sum_cps(xs, c):
        return c(0) if is_none(xs) else sum_cps(tail(xs), lambda r: c(head(xs) + r))

    measure(sum_rec, enum_llist(1, 500))
    measure(sum_cps, enum_llist(1, 500), lambda x: x)
    ```
    ```text
    [measure] sum_rec([1, [2, [3, [4, [...): 501 calls, 7,006 steps, at most 501 waiting at once
    [measure] sum_cps([1, [2, [3, [4, [..., <function (anonym...): 1,002 calls, 9,009 steps, at most 1 waiting at once
    ```

    "At most 1 waiting" counts pending calls only. Before the base case, `sum_cps` has built 500 continuation functions, each remembering its own `xs` and the previous `c`: that is Θ(n) space, only stored as function values instead of deferred operations. The difference shows on a long llist:

    ```python title="§2"
    def sum_rec(xs):
        return 0 if is_none(xs) else head(xs) + sum_rec(tail(xs))

    def sum_cps(xs, c):
        return c(0) if is_none(xs) else sum_cps(tail(xs), lambda r: c(head(xs) + r))

    print(sum_cps(enum_llist(1, 2000), lambda x: x))
    print(sum_rec(enum_llist(1, 2000)))
    ```
    ```text
    2001000
    RecursionError: maximum recursion depth exceeded
    ```

## 8. Read CPS backwards ★★

**Skill:** work out what a CPS function computes.

What do these print?

```python title="§2"
def mystery(xs, c):
    return c(None) if is_none(xs) else mystery(tail(xs), lambda r: c(pair(head(xs) * 2, r)))

def mystery2(xs, c):
    return c(None) if is_none(xs) else mystery2(tail(xs), lambda r: c(append(r, llist(head(xs)))))

print_llist(mystery(llist(1, 2, 3), lambda x: x))
print_llist(mystery2(llist(1, 2, 3), lambda x: x))
print(mystery(llist(1, 2), length))
```

??? success "Answer"
    ```text
    llist(2, 4, 6)
    llist(3, 2, 1)
    2
    ```

    Undo the conversion: "the result for `xs` is `pair(head(xs) * 2, result for the tail)`", which is `map(lambda x: x * 2, xs)`. `mystery2` is "append the head after the result for the tail": reverse (the slow Θ(n²) one). The first continuation is applied to the **final** result, so passing `length` instead of the identity gives the length of the doubled llist.

## 9. CPS with two recursive calls ★★★

**Skill:** a continuation that makes the second recursive call.

Convert `tree_sum` (problem 1) to CPS as `tree_sum_cps(tree, c)`. Every recursive call must be a tail call.

??? success "Answer"
    ```python title="§2"
    def tree_sum_cps(tree, c):
        if is_none(tree):
            return c(0)
        elif is_llist(head(tree)):
            return tree_sum_cps(head(tree),
                                lambda a: tree_sum_cps(tail(tree), lambda b: c(a + b)))
        else:
            return tree_sum_cps(tail(tree), lambda b: c(head(tree) + b))

    t = llist(1, llist(2, 3), llist(llist(4)), 5)
    print(tree_sum_cps(t, lambda x: x))
    print(tree_sum_cps(t, lambda x: x * 100))
    ```
    ```text
    15
    1500
    ```

    In the subtree case the old code did two calls and then `+`. In CPS, do the first call (the head) now; its continuation receives the head's sum `a` and then does the second call (the tail); that one's continuation receives `b` and finally passes `a + b` on to `c`. The second continuation can use `a` because it is written inside the first one.

## 10. Write it: count_at_depth ★★★

**Skill:** tree recursion with an extra parameter that changes only when going down.

Top-level data items of a tree are at depth 1; items inside one more llist are at depth 2, and so on. Write `count_at_depth(tree, d)`: how many data items are at depth exactly `d`.

??? success "Answer"
    ```python title="§2"
    def count_at_depth(tree, d):
        if is_none(tree):
            return 0
        elif is_llist(head(tree)):
            return count_at_depth(head(tree), d - 1) + count_at_depth(tail(tree), d)
        else:
            return (1 if d == 1 else 0) + count_at_depth(tail(tree), d)

    t = llist(1, llist(2, 3), llist(llist(4)), 5)
    print(count_at_depth(t, 1), count_at_depth(t, 2), count_at_depth(t, 3), count_at_depth(t, 4))
    ```
    ```text
    2 2 1 0
    ```

    Going into a subtree (the head) brings the target one level closer, so `d - 1`. Going along the same llist (the tail) stays at the same level, so `d` is unchanged. Only data items found while `d` is 1 count. In `t`: 1 and 5 at depth 1, 2 and 3 at depth 2, 4 at depth 3.

*In the course: L5B, S7 · SICPy 2.2.2.*
