# Drill 10 · Lists & loops

<p class="chapter-goal">Trace while and for loops, write in-place and new-list programs, beat the aliasing traps, give Θ.</p>

Easiest first. Try each problem on paper before you open the answer. Every answer was run in Python §3.

!!! tip "Rules you will need"
    - `for i in range(a, b, step)` visits a, a+step, … and stops **before** b. `range` works only in a `for` loop.
    - A list cannot grow. To build a new list you must know its length first: `[None] * n`, then fill it.
    - Lists, like pairs, are objects: `ys = xs` makes no copy.

## 1. Halve or triple ★

*Skill: trace a `while` loop.*

```python title="§3"
n = 6
steps = 0
while n != 1:
    n = n // 2 if n % 2 == 0 else 3 * n + 1
    steps = steps + 1
print(n, steps)
```

??? success "Answer"
    ```text
    1 8
    ```
    The values of `n` at each test: 6, 3, 10, 5, 16, 8, 4, 2, 1. The body ran once for each arrow between them: 8 times. The loop stops when the test `n != 1` is `False`.

## 2. Counting with range ★

*Skill: what `range` visits, and nested loops.*

```python title="§3"
s = ""
for i in range(5, 0, -2):
    s = s + str(i)
print(s)

t = 0
for i in range(4):
    for j in range(i):
        t = t + 1
print(t)
```

??? success "Answer"
    ```text
    531
    6
    ```
    `range(5, 0, -2)` visits 5, 3, 1 and stops before 0. In the nested loops the inner loop runs `i` times: 0 + 1 + 2 + 3 = 6.

## 3. Skip and stop ★

*Skill: `continue` and `break`.*

```python title="§3"
xs = [4, 7, 0, 9, 2]
found = -1
for i in range(len(xs)):
    if xs[i] == 0:
        continue
    if xs[i] > 8:
        found = i
        break
    print(xs[i])
print(found)
```

??? success "Answer"
    ```text
    4
    7
    3
    ```
    4 and 7 are printed. The 0 is skipped by `continue` (nothing after it in the body runs for that `i`). At index 3 the 9 is bigger than 8: `found` becomes 3 and `break` leaves the loop, so the 2 is never visited.

## 4. Rotate in place ★

*Skill: write an in-place loop over indices.*

Write `rotate_left(xs)`: it changes the list so that every element moves one place to the left and the first one goes to the end. It returns nothing. `[1, 2, 3, 4]` becomes `[2, 3, 4, 1]`.

??? success "Answer"
    ```python title="§3"
    def rotate_left(xs):
        n = len(xs)
        if n > 0:
            first = xs[0]
            for i in range(n - 1):
                xs[i] = xs[i + 1]
            xs[n - 1] = first

    ys = [1, 2, 3, 4]
    rotate_left(ys)
    print(ys)
    rotate_left(ys)
    print(ys)
    zs = []
    rotate_left(zs)
    print(zs)
    ```
    ```text
    [2, 3, 4, 1]
    [3, 4, 1, 2]
    []
    ```
    Save `xs[0]` first: the loop overwrites it. Then copy each element from its right neighbour, left to right. Θ(n) time, Θ(1) extra space, and no new list: the caller's list itself changes.

## 5. Where does it occur? ★★

*Skill: make a NEW list when its size is not known yet (two passes).*

Write `positions_of(xs, v)`: a new list of all indices `i` with `xs[i] == v`, in increasing order. Do not change `xs`.

??? success "Answer"
    ```python title="§3"
    def positions_of(xs, v):
        count = 0
        for i in range(len(xs)):
            if xs[i] == v:
                count = count + 1
        result = [None] * count
        k = 0
        for i in range(len(xs)):
            if xs[i] == v:
                result[k] = i
                k = k + 1
        return result

    print(positions_of(["a", "b", "a", "a"], "a"))
    print(positions_of([1, 2, 3], 9))
    ```
    ```text
    [0, 2, 3]
    []
    ```
    A list cannot grow, so pass 1 only **counts**, then we allocate exactly that many slots. In pass 2, `i` walks over `xs` while `k` is the next free slot of `result`; `k` moves only on a match. Θ(n) time.

## 6. The shared row ★★

*Skill: aliasing in 2-D lists.*

```python title="§3"
bad = [[0] * 3] * 2
bad[0][1] = 5
print(bad)

good = [None] * 2
for r in range(2):
    good[r] = [0] * 3
good[0][1] = 5
print(good)

row = [0, 0]
table = [row, row]
table[1] = [1, 1]
table[0][0] = 9
print(table, row)
```

??? success "Answer"
    ```text
    [[0, 5, 0], [0, 5, 0]]
    [[0, 5, 0], [0, 0, 0]]
    [[9, 0], [1, 1]] [9, 0]
    ```
    `[[0] * 3] * 2` evaluates `[0] * 3` **once** and puts that one list in both slots, so `bad[0]` and `bad[1]` are the same row. `good` evaluates `[0] * 3` once per iteration: two different rows. In the last part, `table[1] = [1, 1]` replaces what slot 1 refers to (the shared `row` is not changed), but `table[0]` is still `row`, so `table[0][0] = 9` changes `row`.

## 7. Transpose ★★

*Skill: nested loops over a 2-D list; allocate fresh rows.*

Write `transpose(m)` for a matrix with `r` rows and `c` columns (all rows the same length, `r ≥ 1`). It returns a NEW matrix with `c` rows and `r` columns, where entry `[j][i]` is `m[i][j]`. Give its order of growth.

??? success "Answer"
    ```python title="§3"
    def transpose(m):
        rows = len(m)
        cols = len(m[0])
        t = [None] * cols
        for j in range(cols):
            t[j] = [None] * rows
            for i in range(rows):
                t[j][i] = m[i][j]
        return t

    print(transpose([[1, 2, 3], [4, 5, 6]]))
    print(transpose([[7], [8]]))
    ```
    ```text
    [[1, 4], [2, 5], [3, 6]]
    [[7, 8]]
    ```
    One fresh row per value of `j` (problem 6!). The inner assignment runs rows × cols times: Θ(r·c) time, and Θ(r·c) space for the new matrix.

## 8. Lambdas made in a loop ★★

*Skill: a function object remembers its environment, not the values in it.*

```python title="§3"
adders = [None] * 3
for i in range(3):
    adders[i] = lambda x: x + i
print(adders[0](10), adders[2](10))

def make_adder(k):
    return lambda x: x + k

fixed = [None] * 3
for i in range(3):
    fixed[i] = make_adder(i)
print(fixed[0](10), fixed[2](10))
```

??? success "Answer"
    ```text
    12 12
    10 12
    ```
    All three lambdas in `adders` are created in the **global** environment, and `i` is one global variable that the loop reassigns. They look up `i` when they are **applied**, after the loop, when `i` is 2. In `fixed`, each `make_adder(i)` call makes a new frame in which `k` holds that iteration's value, and each lambda remembers its own frame.

## 9. From recursion to a loop ★★

*Skill: turn a recursive process into a loop with an accumulator.*

This works, but gives a recursive process. Rewrite it with a `while` loop and give the space used by both versions.

```python
def llist_max(xs):          # xs is a non-empty llist of numbers
    return (head(xs) if is_none(tail(xs))
            else max(head(xs), llist_max(tail(xs))))
```

??? success "Answer"
    ```python title="§3"
    def llist_max(xs):
        best = head(xs)
        xs = tail(xs)
        while not is_none(xs):
            if head(xs) > best:
                best = head(xs)
            xs = tail(xs)
        return best

    print(llist_max(llist(3, 9, 2, 9, 4)))
    print(llist_max(llist(-5)))
    print(llist_max(enum_llist(1, 5000)))
    ```
    ```text
    9
    -5
    5000
    ```
    The recursive version leaves a deferred `max(head(xs), …)` for every element: Θ(n) space (and it fails for 5000 elements). The loop keeps the "answer so far" in `best` and walks with `xs = tail(xs)`: Θ(n) time, Θ(1) extra space. Reassigning the parameter `xs` is fine: it only changes the local binding.

## 10. How many times? ★★

*Skill: Θ of loop programs.*

Give Θ (in terms of `n`) of the number of times `count = count + 1` runs in each function.

```python title="§3"
def a(n):
    count = 0
    for i in range(n):
        for j in range(i, n):
            count = count + 1
    return count

def b(n):
    count = 0
    i = 1
    while i < n:
        i = i * 2
        count = count + 1
    return count

def c(n):
    count = 0
    for i in range(n):
        for j in range(10):
            count = count + 1
    return count

def d(n):
    count = 0
    for i in range(n):
        j = 1
        while j < n:
            j = j * 2
            count = count + 1
    return count

for k in range(4, 7):
    n = 2 ** k
    print(n, a(n), b(n), c(n), d(n))
```

??? success "Answer"
    ```text
    16 136 4 160 64
    32 528 5 320 160
    64 2080 6 640 384
    ```
    - `a`: n + (n−1) + … + 1 = n(n+1)/2, so **Θ(n²)**. Doubling n roughly quadruples the count.
    - `b`: `i` doubles until it reaches n: about log₂ n times, **Θ(log n)**.
    - `c`: the inner loop has a fixed 10 iterations: 10n, **Θ(n)**.
    - `d`: n outer iterations, each doing log₂ n inner ones: **Θ(n log n)**.

## 11. A triangle of rows ★★★

*Skill: build a jagged 2-D list (rows of different lengths) row by row.*

Write `pascal(n)`: a list of `n` rows, where row `r` has `r + 1` entries; each row starts and ends with 1 and every other entry is the sum of the two entries above it (`row[k] = above[k - 1] + above[k]`). No recursion.

??? success "Answer"
    ```python title="§3"
    def pascal(n):
        rows = [None] * n
        for r in range(n):
            row = [1] * (r + 1)
            for k in range(1, r):
                row[k] = rows[r - 1][k - 1] + rows[r - 1][k]
            rows[r] = row
        return rows

    tri = pascal(5)
    for r in range(len(tri)):
        print(tri[r])
    print(len(pascal(0)))
    ```
    ```text
    [1]
    [1, 1]
    [1, 2, 1]
    [1, 3, 3, 1]
    [1, 4, 6, 4, 1]
    0
    ```
    Each iteration makes a **fresh** row of the right length, already full of 1s, and fills only the inside entries `1 … r−1` from the previous row (for r = 0 and r = 1 the inner loop runs zero times). Θ(n²) time and space: the rows hold 1 + 2 + … + n entries.

*In the course: L8A, L9B.*
