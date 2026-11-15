# Memoization, searching & sorting

<p class="chapter-goal">Remember results in a table; find things in Θ(log n); sort llists and lists, and know what each costs.</p>

## 1. Memoization

**Memoization** = remember the result of a call in a table the first time, look it up every later time.

1. Pick the table: arguments are small non-negative integers → a list `mem = [None] * (n + 1)`; two arguments → a 2-D table with a **fresh row** per row.
2. Before computing: if the entry is not `None`, return it.
3. After computing: store the result, then return it.
4. **The recursive calls must go through the memoized function.** Otherwise only the outermost call is remembered.

```python title="§3"
def memoize(f, size):
    mem = [None] * (size + 1)          # private table, survives between calls
    def memoized(n):
        if mem[n] is None:
            mem[n] = f(n)
        return mem[n]
    return memoized

calls = 0
def slow_fib(n):
    global calls
    calls = calls + 1
    return n if n <= 1 else slow_fib(n - 1) + slow_fib(n - 2)

wrong = memoize(slow_fib, 20)          # recursion bypasses the table
print(wrong(20), calls)

calls = 0
def fib_body(n):
    global calls
    calls = calls + 1
    return n if n <= 1 else fast_fib(n - 1) + fast_fib(n - 2)
fast_fib = memoize(fib_body, 20)       # recursion goes through the table
print(fast_fib(20), calls)
```
```text title="Output"
6765 21891
6765 21
```

**Two arguments**, C(n, k) = C(n−1, k) + C(n−1, k−1):

```python title="§3"
def choose(n, k):
    table = [None] * (n + 1)
    for r in range(n + 1):
        table[r] = [None] * (k + 1)    # fresh row each time
    def c(n, k):
        if k > n:
            return 0
        elif k == 0 or k == n:
            return 1
        elif table[n][k] is not None:
            return table[n][k]
        else:
            result = c(n - 1, k) + c(n - 1, k - 1)
            table[n][k] = result
            return result
    return c(n, k)

print(choose(5, 2), choose(30, 15))
```
```text title="Output"
10 155117520
```

| | time | space |
|---|---|---|
| tree-recursive fib | Θ(φⁿ) | Θ(n) |
| memoized fib | Θ(n) | Θ(n) (table + pending calls) |
| tree-recursive C(n, k) | exponential | Θ(n) |
| memoized C(n, k) | Θ(n·k) | Θ(n·k) table + Θ(n) pending calls |

## 2. Searching

| | needs | time |
|---|---|---|
| linear search (list or llist) | nothing | Θ(n) worst, Θ(1) best |
| binary search (list) | sorted, Θ(1) indexing | Θ(log n) |
| BST search (tree) | a binary search tree | Θ(height): Θ(log n) if balanced, Θ(n) if not |

```python title="§3"
def binary_search(xs, x):
    low = 0
    high = len(xs) - 1
    while low <= high:                 # the part that can still hold x
        mid = (low + high) // 2
        if xs[mid] == x:
            return True
        elif xs[mid] < x:
            low = mid + 1
        else:
            high = mid - 1
    return False

print(binary_search([2, 5, 8, 13, 21], 13), binary_search([2, 5, 8, 13, 21], 6))
```
```text title="Output"
True False
```

**Why llists need trees.** Binary search jumps to the middle in Θ(1). A llist needs Θ(n) steps to reach its middle, so we store the data as a **binary search tree** instead: `None`, or `llist(entry, left, right)` with smaller entries left and larger ones right.

```python title="§2"
def entry(t):
    return head(t)
def left_branch(t):
    return head(tail(t))
def right_branch(t):
    return head(tail(tail(t)))

def bst_member(x, t):
    return (False if is_none(t)
            else True if x == entry(t)
            else bst_member(x, left_branch(t)) if x < entry(t)
            else bst_member(x, right_branch(t)))

def bst_insert(x, t):
    return (llist(x, None, None) if is_none(t)
            else t if x == entry(t)
            else llist(entry(t), bst_insert(x, left_branch(t)), right_branch(t)) if x < entry(t)
            else llist(entry(t), left_branch(t), bst_insert(x, right_branch(t))))

tree = reduce(bst_insert, None, llist(9, 3, 14, 7))   # inserts 7, 14, 3, 9
print(entry(tree), bst_member(3, tree), bst_member(8, tree))
```
```text title="Output"
7 True False
```

## 3. Sorting llists

Pass a comparator `before(x, y)` ("may x come before y?") to choose the order: `lambda x, y: x <= y` ascending, `lambda x, y: x >= y` descending.

```python title="§2"
def insert(x, xs, before):
    return (llist(x) if is_none(xs)
            else pair(x, xs) if before(x, head(xs))
            else pair(head(xs), insert(x, tail(xs), before)))

def insertion_sort(xs, before):
    return None if is_none(xs) else insert(head(xs), insertion_sort(tail(xs), before), before)

def merge(xs, ys):
    return (ys if is_none(xs) else xs if is_none(ys)
            else pair(head(xs), merge(tail(xs), ys)) if head(xs) <= head(ys)
            else pair(head(ys), merge(xs, tail(ys))))

def take(xs, n):
    return None if n == 0 else pair(head(xs), take(tail(xs), n - 1))
def drop(xs, n):
    return xs if n == 0 else drop(tail(xs), n - 1)

def merge_sort(xs):
    if is_none(xs) or is_none(tail(xs)):
        return xs
    else:
        half = length(xs) // 2
        return merge(merge_sort(take(xs, half)), merge_sort(drop(xs, half)))

def quicksort(xs):      # idea: split around a pivot, sort both parts
    return (None if is_none(xs)
            else append(quicksort(filter(lambda x: x < head(xs), tail(xs))),
                        pair(head(xs), quicksort(filter(lambda x: x >= head(xs), tail(xs))))))

data = llist(5, 1, 4, 2, 3)
print_llist(insertion_sort(data, lambda x, y: x >= y))
print_llist(merge_sort(data))
print_llist(quicksort(data))
```
```text title="Output"
llist(5, 4, 3, 2, 1)
llist(1, 2, 3, 4, 5)
llist(1, 2, 3, 4, 5)
```

**Selection sort on a llist:** find the smallest (Θ(n)), `remove` it, sort the rest, put the smallest in front.

## 4. Sorting lists (in place)

```python title="§3"
def swap(xs, i, j):
    temp = xs[i]
    xs[i] = xs[j]
    xs[j] = temp

def selection_sort(xs):
    for i in range(len(xs) - 1):
        smallest = i                   # position of the minimum of xs[i..]
        for j in range(i + 1, len(xs)):
            if xs[j] < xs[smallest]:
                smallest = j
        swap(xs, i, smallest)

def insertion_sort_list(xs):
    for i in range(1, len(xs)):
        j = i                          # move xs[i] left while it is too small
        while j > 0 and xs[j - 1] > xs[j]:
            swap(xs, j - 1, j)
            j = j - 1

a = [6, 2, 9, 1]
b = [6, 2, 9, 1]
selection_sort(a)
insertion_sort_list(b)
print(a, b)
```
```text title="Output"
[1, 2, 6, 9] [1, 2, 6, 9]
```

**Merge sort on a list:** sort `xs[low..mid]` and `xs[mid+1..high]` recursively, then merge them into a temporary list `[None] * n` and copy back. Θ(n log n) time, Θ(n) extra space for the buffer.

## 5. Orders of growth

| Sort | best | worst | best input | worst input | extra space |
|---|---|---|---|---|---|
| insertion | Θ(n) | Θ(n²) | already sorted (for the code above) | reverse sorted | lists Θ(1) |
| selection | Θ(n²) | Θ(n²) | any (always scans the rest) | any | lists Θ(1) |
| merge | Θ(n log n) | Θ(n log n) | any | any | Θ(n) |
| quicksort | Θ(n log n) | Θ(n²) | pivot splits evenly | already sorted (first element as pivot) | Θ(n) |

## 6. How to answer this in the exam

1. **"Memoize this"**: identify the arguments that vary → table shape; check the table first; store before returning; make every recursive call go through the table.
2. **"Draw the call tree of the memoized version"**: a call whose answer is already in the table is a **leaf**; mark it "found".
3. **"Order of growth"**: memoized = (number of distinct argument combinations) × (work per call without recursion). Sorts: count comparisons in the inner loop for the best and worst input, and NAME those inputs.
4. **"Write a search"**: binary search needs a sorted list; keep `low`/`high` as "the part that may still contain x"; stop when `low > high`.

## 7. Traps

1. Memoizing only the outer call (`memoize(slow_fib, n)`) is still exponential.
2. `[[None] * k] * n` as a 2-D table: all rows are the same row, and wrong answers come back.
3. Checking the table but forgetting to **store** the result: no speed-up at all.
4. Binary search on an unsorted list gives wrong answers, not an error.
5. Selection sort is Θ(n²) even on sorted input; insertion sort is not.

*In the course: L6A, L10A · SICPy 2.3.3.*
