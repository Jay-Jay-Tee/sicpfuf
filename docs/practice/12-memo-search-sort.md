# Drill 12 · Memoization, searching & sorting

<p class="chapter-goal">Memoize with 1-D and 2-D tables, count the calls saved, search and sort lists, give Θ.</p>

Easiest first. Try each problem on paper before you open the answer. Every answer was run in Python §3. `measure(f, args...)` applies `f` and reports how many calls and steps it took; it returns `f`'s result.

!!! tip "Memoization in three lines"
    1. Make a table (a list, or a list of fresh rows) full of `None`, **outside** the function, so it lives between calls.
    2. Before computing `f(k)`: if `mem[k] is not None`, return it.
    3. After computing it: `mem[k] = result`, then return it. The recursive calls must go to the **memoized** function.

## 1. What gets computed? ★

*Skill: trace a memoized function; see which calls hit the table.*

```python title="§3"
mem = [None] * 10

def fib(k):
    if mem[k] is not None:
        return mem[k]
    print("computing", k)
    result = k if k < 2 else fib(k - 1) + fib(k - 2)
    mem[k] = result
    return result

print(fib(4))
print(fib(5))
print(fib(3))
```

??? success "Answer"
    ```text
    computing 4
    computing 3
    computing 2
    computing 1
    computing 0
    3
    computing 5
    5
    2
    ```
    `fib(4)` computes 4, then 3, 2, 1, 0 (following the first recursive call `fib(k - 1)` all the way down). Every later `fib(k - 2)` finds its result in `mem`. `fib(5)` only needs `fib(4)` and `fib(3)`, both in the table: one new "computing" line. `fib(3)` is answered from the table at once. The table is global, so it persists between the top-level calls.

## 2. Memoize the tiles ★★

*Skill: memoize a one-argument function with a 1-D list; compare call counts.*

`tiles(n)` counts the ways to cover a strip of length `n` with tiles of length 1 and 3.

```python title="§3"
def tiles(n):
    return 1 if n < 3 else tiles(n - 1) + tiles(n - 3)

print(measure(tiles, 20))
```
```text title="Output"
[measure] tiles(20): 2,555 calls, 28,100 steps, at most 19 waiting at once
1278
```

Write `fast_tiles(n)` with a table, for `n` up to 100, and measure it on 20.

??? success "Answer"
    ```python title="§3"
    table = [None] * 101

    def fast_tiles(n):
        if table[n] is None:
            table[n] = 1 if n < 3 else fast_tiles(n - 1) + fast_tiles(n - 3)
        return table[n]

    print(measure(fast_tiles, 20))
    print(fast_tiles(100))
    ```
    ```text
    [measure] fast_tiles(20): 37 calls, 718 steps, at most 19 waiting at once
    1278
    24382819596721629
    ```
    Without the table the calls grow exponentially (each call makes two more). With it, each `n` from 0 to 20 is computed once and every other call is a table hit: fewer than 2n calls, Θ(n) time, Θ(n) space for the table and the waiting calls. `fast_tiles(100)` would take longer than the age of the universe without memoization.

## 3. The memoize pitfall ★★

*Skill: spot why memoizing only the outer call does not help, and fix it.*

Why is the first `quick(20)` as slow as plain `tiles(20)`? Fix it, still using `memoize`.

```python title="§3"
def memoize(f, size):
    mem = [None] * size
    def remembered(n):
        if mem[n] is None:
            mem[n] = f(n)
        return mem[n]
    return remembered

def tiles(n):
    return 1 if n < 3 else tiles(n - 1) + tiles(n - 3)

quick = memoize(tiles, 50)
print(measure(quick, 20))
print(measure(quick, 20))
```

??? success "Answer"
    ```text
    [measure] remembered(20): 2,556 calls, 28,116 steps, at most 20 waiting at once
    1278
    [measure] remembered(20): 1 calls, 10 steps, at most 1 waiting at once
    1278
    ```
    `quick` only remembers the result of the **outer** call. Inside, `tiles` calls the plain `tiles`, which knows nothing about the table, so the first call does all the exponential work (the second one is a table hit: 1 call). The recursion must go **through** the memoized function:

    ```python title="§3"
    def memoize(f, size):
        mem = [None] * size
        def remembered(n):
            if mem[n] is None:
                mem[n] = f(n)
            return mem[n]
        return remembered

    tiles = memoize(lambda n: 1 if n < 3 else tiles(n - 1) + tiles(n - 3), 50)
    print(measure(tiles, 20))
    ```
    ```text
    [measure] remembered(20): 58 calls, 781 steps, at most 38 waiting at once
    1278
    ```
    Now the lambda's body looks up the name `tiles` when it runs, and finds the **memoized** function.

## 4. Paths through a grid ★★

*Skill: memoize a two-argument function with a 2-D table (fresh rows!).*

`paths(r, c)` counts the ways to walk from the top-left corner to the cell `r` rows down and `c` columns right, moving only down or right: 1 if `r` or `c` is 0, otherwise `paths(r - 1, c) + paths(r, c - 1)`. Write a memoized version for `r, c ≤ 20` and give its Θ.

??? success "Answer"
    ```python title="§3"
    def make_table(rows, cols):
        t = [None] * rows
        for i in range(rows):
            t[i] = [None] * cols
        return t

    mem = make_table(21, 21)

    def paths(r, c):
        if r == 0 or c == 0:
            return 1
        elif mem[r][c] is not None:
            return mem[r][c]
        else:
            result = paths(r - 1, c) + paths(r, c - 1)
            mem[r][c] = result
            return result

    print(paths(2, 2), paths(3, 3))
    print(measure(paths, 10, 10))
    ```
    ```text
    6 20
    [measure] paths(10, 10): 183 calls, 5,293 steps, at most 17 waiting at once
    184756
    ```
    Each cell `(r, c)` is computed at most once, and each computation does Θ(1) work besides its two calls: Θ(r·c) time and Θ(r·c) space for the table (plus Θ(r + c) waiting calls). Build the table with a fresh row per `i`: `[[None] * 21] * 21` would make all rows the **same** list, and results would be stored in the wrong cells.

## 5. Find it, or say where it is not ★

*Skill: linear search with a compound `while` condition.*

Write `index_of(A, v)`: the first index of `v` in the list `A`, or `-1`. Give the best and worst case Θ.

??? success "Answer"
    ```python title="§3"
    def index_of(A, v):
        i = 0
        while i < len(A) and A[i] != v:
            i = i + 1
        return i if i < len(A) else -1

    print(index_of([5, 3, 8, 3], 3))
    print(index_of([5, 3, 8, 3], 7))
    print(index_of([], 7))
    ```
    ```text
    1
    -1
    -1
    ```
    The order of the test matters: `i < len(A)` first, so `A[i]` is never read out of range (`and` stops at the first `False`). Best case Θ(1) (found at index 0), worst case Θ(n) (not there). The list need not be sorted.

## 6. The last one ★★

*Skill: a binary search variant.*

`A` is sorted in ascending order and may contain repeats. Write `last_index(A, v)`: the **largest** index `i` with `A[i] == v`, or `-1`. It must be Θ(log n), also when `v` appears many times.

??? success "Answer"
    ```python title="§3"
    def last_index(A, v):
        low = 0
        high = len(A) - 1
        found = -1
        while low <= high:
            mid = (low + high) // 2
            if A[mid] == v:
                found = mid
                low = mid + 1
            elif A[mid] < v:
                low = mid + 1
            else:
                high = mid - 1
        return found

    B = [1, 2, 2, 2, 2, 2, 7, 9]
    print(last_index(B, 2), last_index(B, 9), last_index(B, 1), last_index(B, 5))
    ```
    ```text
    5 7 0 -1
    ```
    On a match, remember `mid` and keep searching the **right** half: a later copy may exist. Each iteration still halves `high - low`, so Θ(log n). Stopping and walking right from the first match you find would be Θ(n) on a list full of 2s.

## 7. Search for the answer ★★

*Skill: binary search over numbers instead of a list.*

Write `ceil_sqrt(n)` for an integer `n ≥ 1`: the smallest integer `k` with `k * k >= n`. Use binary search on `k` between 1 and `n` (no `math_sqrt`).

??? success "Answer"
    ```python title="§3"
    def ceil_sqrt(n):
        low = 1
        high = n
        while low < high:
            mid = (low + high) // 2
            if mid * mid >= n:
                high = mid
            else:
                low = mid + 1
        return low

    print(ceil_sqrt(1), ceil_sqrt(16), ceil_sqrt(17), ceil_sqrt(1000000))
    ```
    ```text
    1 4 5 1000
    ```
    The invariant: the answer is always in `low … high`. If `mid` is big enough, it may be the answer, so keep it (`high = mid`); otherwise the answer is above it (`low = mid + 1`). When `low == high` that is the answer. Θ(log n) iterations: no list at all, binary search only needs a test that is `False … False True … True`.

## 8. Selection sort, pass by pass ★★

*Skill: trace selection sort.*

Predict every line.

```python title="§3"
def swap(A, i, j):
    temp = A[i]
    A[i] = A[j]
    A[j] = temp

def selection_sort(A):
    n = len(A)
    for i in range(n - 1):
        smallest = i
        for j in range(i + 1, n):
            if A[j] < A[smallest]:
                smallest = j
        swap(A, i, smallest)
        print(A)

xs = [4, 1, 3, 5, 2]
selection_sort(xs)
```

??? success "Answer"
    ```text
    [1, 4, 3, 5, 2]
    [1, 2, 3, 5, 4]
    [1, 2, 3, 5, 4]
    [1, 2, 3, 4, 5]
    ```
    Pass `i` finds the smallest element of `A[i …]` and swaps it into position `i`; the part left of `i` is sorted and final. The third pass swaps 3 with itself (nothing changes, but the comparisons are still made). Always n(n−1)/2 comparisons: Θ(n²), whatever the input.

## 9. Insertion sort, pass by pass ★★

*Skill: trace insertion sort (shifting version); count shifts.*

```python title="§3"
def insertion_sort(A):
    shifts = 0
    for i in range(1, len(A)):
        x = A[i]
        j = i - 1
        while j >= 0 and A[j] > x:
            A[j + 1] = A[j]
            shifts = shifts + 1
            j = j - 1
        A[j + 1] = x
        print(A)
    return shifts

print(insertion_sort([3, 5, 1, 4]))
```

??? success "Answer"
    ```text
    [3, 5, 1, 4]
    [1, 3, 5, 4]
    [1, 3, 4, 5]
    3
    ```
    Pass `i` takes `A[i]` out, shifts the bigger elements of the sorted part one place right, and drops it into the gap. 5 needs no shift, 1 needs two (past 5 and 3), 4 needs one (past 5): 3 shifts in total. The number of shifts equals the number of out-of-order pairs, so a sorted list needs none (Θ(n)) and a reversed one n(n−1)/2 (Θ(n²)).

## 10. Find the bug ★★★

*Skill: why a binary search loops forever.*

This binary search sometimes never stops. Find an input where it loops, explain why, and fix it.

```python
def contains(A, v):
    low = 0
    high = len(A) - 1
    while low <= high:
        mid = (low + high) // 2
        if A[mid] == v:
            return True
        elif A[mid] < v:
            low = mid          # (*)
        else:
            high = mid - 1
    return False
```

??? success "Answer"
    `contains([1, 3], 5)`: `low = 0`, `high = 1`, `mid = 0`, `A[0] < 5`, so `low = mid = 0` again: nothing changed, and the loop repeats forever. Every iteration must make the range `low … high` **smaller**. Since `A[mid]` is already known not to be `v`, skip it: `low = mid + 1`.

    ```python title="§3"
    def contains(A, v):
        low = 0
        high = len(A) - 1
        while low <= high:
            mid = (low + high) // 2
            if A[mid] == v:
                return True
            elif A[mid] < v:
                low = mid + 1
            else:
                high = mid - 1
        return False

    print(contains([1, 3], 5), contains([1, 3], 3), contains([1, 3], 0), contains([], 1))
    ```
    ```text
    False True False False
    ```

## 11. Counting change, remembered ★★★

*Skill: memoize a two-argument tree recursion; measure the saving; Θ.*

`cc(amount, k)` counts the ways to pay `amount` cents with the first `k` coin kinds of `coins = [1, 5, 10, 25, 50]`. Memoize it with a 2-D table and compare the calls for `cc(150, 5)`.

??? success "Answer"
    ```python title="§3"
    coins = [1, 5, 10, 25, 50]

    def cc(amount, k):
        if amount == 0:
            return 1
        elif amount < 0 or k == 0:
            return 0
        else:
            return cc(amount, k - 1) + cc(amount - coins[k - 1], k)

    def make_table(rows, cols):
        t = [None] * rows
        for i in range(rows):
            t[i] = [None] * cols
        return t

    mem = make_table(301, 6)

    def mcc(amount, k):
        if amount == 0:
            return 1
        elif amount < 0 or k == 0:
            return 0
        elif mem[amount][k] is not None:
            return mem[amount][k]
        else:
            result = mcc(amount, k - 1) + mcc(amount - coins[k - 1], k)
            mem[amount][k] = result
            return result

    print(measure(cc, 150, 5))
    print(measure(mcc, 150, 5))
    ```
    ```text
    [measure] cc(150, 5): 71,775 calls, 1,571,248 steps, at most 155 waiting at once
    972
    [measure] mcc(150, 5): 435 calls, 13,735 steps, at most 155 waiting at once
    972
    ```
    The table has one cell per pair `(amount, k)`; the base cases are checked **before** the table, so a negative amount is never used as an index (that would silently read from the end of the list!). With n = amount and k kinds, the memoized version computes each cell once: Θ(n·k) time and Θ(n·k) space for the table, plus up to about n waiting calls.

*In the course: L10A.*
