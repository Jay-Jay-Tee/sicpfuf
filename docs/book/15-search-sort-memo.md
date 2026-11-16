# Searching, sorting and memoization

<p class="chapter-goal">Search and sort Python lists in place, know their orders of growth, and make slow recursion fast by remembering results.</p>

!!! abstract "The big idea, in plain words"
    Finding a name in a shuffled pile of cards means checking them one by one. Finding it in a phone
    book is much faster: open in the middle, throw away the half it cannot be in, repeat. Lists make the
    phone-book trick possible, because you can jump straight to the middle in Θ(1).

    The second idea is a notebook: write each answer down the first time, look it up after that. That is
    **memoization**, and it can turn an exponential program into a linear one.

## Linear search

Look at every element in turn. The list need not be sorted.

```python title="§3"
def index_of(xs, value):
    i = 0
    while i < len(xs) and xs[i] != value:
        i = i + 1
    return i if i < len(xs) else -1

shelf = ["maths", "art", "chem", "bio"]
print(index_of(shelf, "chem"), index_of(shelf, "music"))
```
```text title="Output"
2 -1
```

The order of the test matters: `i < len(xs)` comes first, so `xs[i]` is never read out of range
(`and` skips its right operand when the left one is `False`). Time: **best case** Θ(1) (the first
element), **worst case** Θ(n) (absent, or last).

## Binary search

On a list **sorted** in ascending order, compare with the middle element and keep only the half where
the value can be. `low` and `high` mark the part still in play.

```python title="§3"
def binary_search(xs, value):
    low = 0
    high = len(xs) - 1
    while low <= high:
        mid = (low + high) // 2
        print("look at index", mid)
        if xs[mid] == value:
            return mid
        elif xs[mid] < value:
            low = mid + 1
        else:
            high = mid - 1
    return -1

years = [1990, 1995, 2001, 2004, 2010, 2013, 2019, 2022, 2026]
print(binary_search(years, 2019))
print(binary_search(years, 2000))
```
```text title="Output"
look at index 4
look at index 6
6
look at index 4
look at index 1
look at index 2
-1
```

Each look halves the part in play: about log₂ n looks, Θ(log n) (20 looks for a million elements). It
needs Θ(1) indexing; on a llist, reaching the middle alone costs Θ(n).

## Swapping two elements

Sorting in place keeps swapping elements. `bad_swap` below **does not work**; `swap` does:

```python title="§3"
def bad_swap(x, y):
    temp = x
    x = y
    y = temp

def swap(xs, i, j):
    temp = xs[i]
    xs[i] = xs[j]
    xs[j] = temp

nums = [1, 2]
bad_swap(nums[0], nums[1])
print(nums)
swap(nums, 0, 1)
print(nums)
```
```text title="Output"
[1, 2]
[2, 1]
```

`bad_swap` reassigns its own parameters, which are bindings in its own frame: the list never sees
anything. `swap` gets the **list** and the **indices**, and assigns to the list's elements.

## Selection sort

Grow a sorted part on the left. In each pass, find the **smallest** element of the unsorted part and
swap it to the front of that part.

```python title="§3"
def swap(xs, i, j):
    temp = xs[i]
    xs[i] = xs[j]
    xs[j] = temp

def selection_sort(xs):
    n = len(xs)
    for i in range(n - 1):
        smallest = i
        for j in range(i + 1, n):
            if xs[j] < xs[smallest]:
                smallest = j
        swap(xs, i, smallest)
        print(xs)

selection_sort([40, 10, 30, 20])
```
```text title="Output"
[10, 40, 30, 20]
[10, 20, 30, 40]
[10, 20, 30, 40]
```

The inner loop runs n−1, n−2, …, 1 times, whatever the input: about n²/2 comparisons, Θ(n²) time,
Θ(1) extra space.

## Insertion sort

Also grow a sorted part on the left, but take the **next** element and slide it left into its place.
Larger elements shift one step right to make a gap.

```python title="§3"
def insertion_sort(xs):
    for i in range(1, len(xs)):
        item = xs[i]
        j = i - 1
        while j >= 0 and xs[j] > item:
            xs[j + 1] = xs[j]
            j = j - 1
        xs[j + 1] = item
        print(xs)

insertion_sort([40, 10, 30, 20])
```
```text title="Output"
[10, 40, 30, 20]
[10, 30, 40, 20]
[10, 20, 30, 40]
```

Worst case Θ(n²) (descending order: every item slides all the way). On a nearly sorted list each
`while` stops almost at once, so insertion sort is much faster there.

## Merge sort

Split the part `low … high−1` in two halves, sort each half (wishful thinking), then **merge** the two
sorted halves through a temporary list `buffer`.

```python title="§3"
def merge(xs, low, mid, high):
    buffer = [None] * (high - low)
    left = low
    right = mid
    for k in range(high - low):
        if right >= high or (left < mid and xs[left] <= xs[right]):
            buffer[k] = xs[left]
            left = left + 1
        else:
            buffer[k] = xs[right]
            right = right + 1
    for k in range(high - low):
        xs[low + k] = buffer[k]

def merge_sort(xs):
    def sort(low, high):
        if high - low >= 2:
            mid = (low + high) // 2
            sort(low, mid)
            sort(mid, high)
            merge(xs, low, mid, high)
    sort(0, len(xs))

marks = [7, 3, 9, 1, 8, 2]
merge_sort(marks)
print(marks)
```
```text title="Output"
[1, 2, 3, 7, 8, 9]
```

Each level of splitting does Θ(n) work in `merge`, and there are about log₂ n levels: Θ(n log n) time.
The buffers need Θ(n) extra space.

| Algorithm | Time | Extra space |
|---|---|---|
| linear search | Θ(n) worst, Θ(1) best | Θ(1) |
| binary search (sorted list) | Θ(log n) worst, Θ(1) best | Θ(1) |
| selection sort | Θ(n²) always | Θ(1) |
| insertion sort | Θ(n²) worst, Θ(n) on a sorted list | Θ(1) |
| merge sort | Θ(n log n) | Θ(n) |

## Merge sort by rewiring existing nodes

The previous merge sort sorts a **list** using a buffer. For a **llist**, a different
representation permits a different operation: change tails to join already existing nodes.
Do not copy a value into a new node and call that node reuse. Check identity with `is`.

This version uses bottom-up passes over runs of width 1, 2, 4, … . Its comparison function
`before(a, b)` is strict: it says that a must precede b. Equal keys are taken from the left
run first, preserving their original order. Inputs must be proper, acyclic llists; the two
runs supplied to a merge must be disjoint.

```python title="§3"
def cut_run(first, width):
    if is_none(first):
        return None
    last = first
    used = 1
    while used < width and not is_none(tail(last)):
        last = tail(last)
        used = used + 1
    remainder = tail(last)
    set_tail(last, None)
    return remainder

def join_sorted_nodes(left, right, before):
    if is_none(left):
        return right
    if is_none(right):
        return left
    if before(head(right), head(left)):
        result = right
        right = tail(right)
    else:
        result = left
        left = tail(left)
    last = result
    while not is_none(left) and not is_none(right):
        if before(head(right), head(left)):
            set_tail(last, right)
            right = tail(right)
        else:
            set_tail(last, left)
            left = tail(left)
        last = tail(last)
    set_tail(last, right if is_none(left) else left)
    return result

def reorder_nodes(xs, before):
    size = length(xs)
    width = 1
    while width < size:
        rest = xs
        result = None
        last = None
        while not is_none(rest):
            left = rest
            right = cut_run(left, width)
            rest = cut_run(right, width)
            merged = join_sorted_nodes(left, right, before)
            if is_none(result):
                result = merged
            else:
                set_tail(last, merged)
            last = merged
            while not is_none(tail(last)):
                last = tail(last)
        xs = result
        width = 2 * width
    return xs

jobs = llist(pair(2, "a"), pair(4, "b"), pair(2, "c"), pair(1, "d"))
old_first = jobs
old_third = tail(tail(jobs))
ordered = reorder_nodes(jobs, lambda a, b: head(a) > head(b))
print_llist(ordered)
print(tail(ordered) is old_first, tail(tail(ordered)) is old_third)
print(reorder_nodes(None, lambda a, b: a < b))
print_llist(reorder_nodes(llist(3, 1, 3, 2, 0), lambda a, b: a < b))
single = llist("only")
print(reorder_nodes(single, lambda a, b: a < b) is single)
```
```text title="Output"
llist([4, 'b'], [2, 'a'], [2, 'c'], [1, 'd'])
True True
None
llist(0, 1, 2, 3, 3)
True
```

`cut_run` saves the remainder **before** cutting the last tail. It returns that remainder;
the caller already remembers the run's first node, so no wrapper pair is needed. Neither
merging nor sorting calls `pair`, `llist` or `set_head`. The record values and llist nodes
were all allocated before sorting began.

After each pass, runs of size at most 2 × width are sorted. A pass visits Θ(n) nodes,
including the walks that find merged tails. There are Θ(log n) passes, giving Θ(n log n)
time for constant-time comparisons and Θ(1) auxiliary storage. This bottom-up version does
not accumulate recursive calls. Replacing it with recursive splitting changes the space
analysis even if neither implementation allocates new result nodes.

## Memoization

Tree-recursive `fib` asks the same questions many times: `fib(5)` computes `fib(3)` twice and `fib(2)`
three times. Remember each answer in a **table**: a list `memo` where `memo[k]` is `fib(k)`, or `None`
if not computed yet.

```python title="§3"
def fast_fib(n):
    memo = [None] * (n + 1)
    def f(k):
        if memo[k] is None:
            memo[k] = k if k <= 1 else f(k - 1) + f(k - 2)
        return memo[k]
    return f(n)

print(fast_fib(10), fast_fib(90))
```
```text title="Output"
55 2880067194370816120
```

Each `f(k)` does real work once; later applications are Θ(1) lookups: Θ(n) time, Θ(n) space.

??? example "X-ray: the call tree with and without the table"
    With a top-level table we can `trace` it. Without memoization the subtree for `fib(2)` is computed
    twice; with it, the second `mfib(2)` is answered at once from the table.

    ```python title="§3"
    def fib(n):
        return n if n <= 1 else fib(n - 1) + fib(n - 2)

    table = [None] * 20

    def mfib(n):
        if table[n] is None:
            table[n] = n if n <= 1 else mfib(n - 1) + mfib(n - 2)
        return table[n]

    trace(fib, 4)
    trace(mfib, 4)
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
    → mfib(4)
    │  → mfib(3)
    │  │  → mfib(2)
    │  │  │  → mfib(1)
    │  │  │  ← 1
    │  │  │  → mfib(0)
    │  │  │  ← 0
    │  │  ← 1
    │  │  → mfib(1)
    │  │  ← 1
    │  ← 2
    │  → mfib(2)
    │  ← 1
    ← 3
    ```

## A general `memoize`, and its trap

We can wrap any one-argument function on small non-negative integers:

```python title="§3"
def memoize(f, size):
    table = [None] * size
    def memo_f(n):
        if table[n] is None:
            table[n] = f(n)
        return table[n]
    return memo_f

def fib(n):
    return n if n <= 1 else fib(n - 1) + fib(n - 2)

wrong = memoize(fib, 50)
right = memoize(lambda n: n if n <= 1 else right(n - 1) + right(n - 2), 50)
measure(wrong, 20)
measure(right, 20)
```
```text title="Output"
[measure] memo_f(20): 21,892 calls, 240,812 steps, at most 21 waiting at once
[measure] memo_f(20): 60 calls, 811 steps, at most 40 waiting at once
```

!!! warning "Trap: the recursive calls must use the memoized function"
    `wrong` remembers only its **own** answers. Inside, `fib` still calls plain `fib`, so the first
    `wrong(20)` is as slow as ever. In `right`, the lambda's recursive calls go through `right` itself,
    so every subproblem is looked up in the table. (The lambda can mention `right` because its body runs
    only later, when `right` already has its value.)

## Two arguments: a 2-D table

The number of ways to choose k things out of n: C(n, k) = C(n−1, k) + C(n−1, k−1) (leave the last thing
out, or take it), with C(n, 0) = C(n, n) = 1 and C(n, k) = 0 when k > n. With two arguments, the table
is a list of rows, `table[n][k]`, each row its own list ([row-aliasing trap](13-lists-loops.md#lists-of-lists)).

```python title="§3"
def make_table(rows, cols):
    table = [None] * rows
    for r in range(rows):
        table[r] = [None] * cols
    return table

def choose(n, k):
    return 0 if k > n else 1 if k == 0 or k == n else choose(n - 1, k) + choose(n - 1, k - 1)

def fast_choose(n, k):
    table = make_table(n + 1, k + 1)
    def c(n, k):
        if k > n:
            return 0
        if k == 0 or k == n:
            return 1
        if table[n][k] is None:
            table[n][k] = c(n - 1, k) + c(n - 1, k - 1)
        return table[n][k]
    return c(n, k)

print(choose(16, 8), fast_choose(16, 8))
measure(choose, 16, 8)
measure(fast_choose, 16, 8)
```
```text title="Output"
12870 12870
[measure] choose(16, 8): 25,739 calls, 521,207 steps, at most 16 waiting at once
[measure] fast_choose(16, 8): 131 calls, 4,578 steps, at most 16 waiting at once
```

The table has (n+1)(k+1) entries, and each is filled once with Θ(1) work: Θ(n·k) time and Θ(n·k) space.

!!! tip "Beyond the course: filling the table bottom-up"
    Memoization is **top-down**: start from the question, recurse, remember. You can also fill the table
    **bottom-up** with loops, smallest questions first, with no recursion at all:

    ```python title="§3"
    def choose_up(n, k):
        table = [None] * (n + 1)
        for i in range(n + 1):
            table[i] = [0] * (k + 1)
            for j in range(k + 1):
                table[i][j] = 1 if j == 0 else 0 if i == 0 else table[i - 1][j] + table[i - 1][j - 1]
        return table[n][k]

    print(choose_up(16, 8), choose_up(5, 2))
    ```
    ```text title="Output"
    12870 10
    ```

!!! note "Python §3 vs real Python"
    Real Python offers `xs.sort()`, `sorted`, `in` and dictionaries for tables; none of them exist in §3.
    A list of `None`s indexed by the argument is the course's table; `is None` tests "not computed yet".

## Takeaways

- Linear search: Θ(n), any list. Binary search: Θ(log n), sorted list, needs Θ(1) indexing.
- To change a list in a function, assign to its **elements**; reassigning parameters changes nothing outside.
- Selection sort Θ(n²) always; insertion sort Θ(n²) worst but fast on nearly sorted input; merge sort
  Θ(n log n) with Θ(n) extra space.
- Memoization: look in the table first; compute and store only if missing. Memoized fib: Θ(n) time and space.
- The recursive calls must go through the memoized function, or nothing is gained.
- Two arguments need a 2-D table with a fresh row list per row.

## Check yourself

1. Find the bug.

    ```python
    def binary_search(xs, value):
        low = 0
        high = len(xs) - 1
        while low < high:
            mid = (low + high) // 2
            if xs[mid] == value:
                return mid
            elif xs[mid] < value:
                low = mid + 1
            else:
                high = mid - 1
        return -1
    ```

    ??? success "Answer"
        `while low < high` stops when one element is left without looking at it, so a value at that
        position is reported missing (for example, searching for `5` in `[5]` gives `-1`). Use `<=`.

2. Why must the list be sorted? What does `binary_search([5, 1, 3], 5)` return?

    ??? success "Answer"
        `-1`, although 5 is there. It looks at index 1, sees 1 < 5 and throws away the left half, which
        is where 5 is. Throwing away a half is only safe when the list is sorted.

3. Memoize `stairs(n)`: the number of ways to climb n steps taking 1 or 2 steps at a time, where
   `stairs(0)` and `stairs(1)` are 1. Test it on n = 50.

    ??? success "Answer"
        ```python title="§3"
        def stairs(n):
            memo = [None] * (n + 1)
            def s(k):
                if memo[k] is None:
                    memo[k] = 1 if k <= 1 else s(k - 1) + s(k - 2)
                return memo[k]
            return s(n)

        print(stairs(4), stairs(50))
        ```
        ```text
        5 20365011074
        ```
        Θ(n) time and space. Without the table it would be Θ(φⁿ), like `fib`.

4. In `fast_choose(16, 8)`, why is the table `make_table(17, 9)` and not `[[None] * 9] * 17`?

    ??? success "Answer"
        `[[None] * 9] * 17` puts the **same** row in all 17 slots, so storing `table[5][2]` would also
        "store" `table[6][2]`, `table[7][2]` …, and wrong answers would be found in the table.

5. Merge sort on 8 elements: how many levels of splitting are there, and how many elements are merged
   in total on each level?

    ??? success "Answer"
        3 levels (8 → 4 → 2 → 1), and each level merges all 8 elements: n · log₂ n, so Θ(n log n).

*In the course: L10A.*
