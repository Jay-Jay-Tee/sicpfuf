# The 25 classic traps

<p class="chapter-goal">One page: the mistakes that cost the most marks, each with a tiny program that falls into it and the fix.</p>

Read the program, guess what happens, then look at the result under it. An error result shows only its last line.

## Unit 1: functions (§1)

### 1. A number used as a condition

**What goes wrong:** full Python treats `0`, `None` and `""` as false. Python §1–§4 do not: a condition must be exactly `True` or `False`. The left operand of `and`/`or` must be a boolean too, so `n or 10` fails the same way.

```python title="§1"
def describe(n):
    if n:
        return "non-zero"
    return "zero"

print(describe(3))
```
```text
TypeError: if condition must be bool, not int
```

**Fix:** write the comparison out: `if n != 0:`, `if not is_none(xs):`.

### 2. Giving a name a second value

**What goes wrong:** in §1 and §2 a name gets its value once per scope. The program is rejected before it runs.

```python title="§1"
total = 10
total = total + 5
print(total)
```
```text
NameReassignmentError: the name 'total' already has a value
```

**Fix:** use a new name (`new_total = total + 5`), or carry the changing value as a parameter of a recursive helper.

### 3. `/` always gives a float

**What goes wrong:** `/` is true division, even when the answer is whole. Midpoints and counts come out as floats.

```python title="§1"
print(7 / 2, 6 / 2)
print(7 // 2, -7 // 2, -7 % 2)
```
```text
3.5 3.0
3 -4 1
```

**Fix:** use `//` (it floors, so `-7 // 2` is −4) or `math_floor(x / 2)` when you need an integer. A float index like `xs[6 / 2]` is a TypeError in §3.

### 4. Chained comparisons

**What goes wrong:** `0 < x < 10` is normal Python, but not part of Python §1–§4.

```python title="§1"
x = 5
print(0 < x < 10)
```
```text
FeatureNotSupportedError: Python §1-§4 does not have this: chained comparisons (a < b < c)
```

**Fix:** `0 < x and x < 10`.

### 5. Mixing strings and numbers

**What goes wrong:** `+` joins two strings or adds two numbers, never one of each. `"ab" * 3` does not exist either.

```python title="§1"
n = 4
print("n is " + n)
```
```text
TypeError: unsupported operand type(s) for +: str and int
```

**Fix:** `"n is " + str(n)`, or `print("n is", n)`. To repeat a string, write a recursive function.

### 6. A stray comma makes a tuple

**What goes wrong:** a comma after a value makes a tuple, and there are no tuples in Python §1–§4.

```python title="§1"
width = 3,
print(width)
```
```text
FeatureNotSupportedError: Python §1-§4 does not have this: tuples
```

**Fix:** delete the comma. For two values use `pair(a, b)` (§2).

### 7. Printing is not returning

**What goes wrong:** `print` shows a value but gives back `None`. A function whose body only prints returns `None` to its caller.

```python title="§1"
def show_double(x):
    print(x * 2)

result = show_double(4)
print(result)
print(show_double(1) + 1)
```
```text
8
None
2
TypeError: unsupported operand type(s) for +: None and int
```

**Fix:** `return x * 2`, and print at the place where the value is used. In the exam, "write a function that computes" means return.

### 8. A branch with no `return`

**What goes wrong:** when a conditional statement ends without a `return` on the path that runs, the function returns `None`.

```python title="§1"
def grade(score):
    if score >= 50:
        return "pass"
    elif score >= 40:
        return "borderline"

print(grade(70), grade(10))
```
```text
pass None
```

**Fix:** make sure every path ends in a `return` (here an `else: return "fail"`).

### 9. The conditional expression takes everything to its left

**What goes wrong:** the conditional expression has lower precedence than `+`, so `10 + 2 if p else 0` means `(10 + 2) if p else 0`.

```python title="§1"
is_member = False
price = 10 + 2 if is_member else 0
print(price)
```
```text
0
```

**Fix:** brackets: `10 + (2 if is_member else 0)` gives 10. The same rule makes a lambda's body run to the end of the line.

### 10. A local name read before its assignment

**What goes wrong:** a name assigned anywhere in a function body is local to the whole body. Reading it earlier is an error, even if a global of the same name exists.

```python title="§1"
rate = 2

def cost(n):
    base = n * rate
    rate = 5
    return base + rate

print(cost(3))
```
```text
UnassignedLocalError: cannot access local variable 'rate' where it is not associated with a value
```

**Fix:** use a different local name (`new_rate = 5`). In §3, write `global rate` if you really mean the global.

### 11. An undeclared name in code that never runs

**What goes wrong:** every name must be declared somewhere. The check happens before running, so not even the first line runs.

```python title="§1"
print("start")

def helper(x):
    return x + offset
```
```text
NameNotFoundError: the name 'offset' is not found in the current or enclosing environment(s)
```

**Fix:** declare it (`offset = 1`) or pass it as a parameter. Watch for typos in rarely used branches.

### 12. A base case that is never reached

**What goes wrong:** stepping by 2 from an odd number jumps over `n == 0`, so the recursion never stops. The pending additions pile up until the limit of 1024 waiting calls.

```python title="§1"
def sum_every_other(n):
    return 0 if n == 0 else n + sum_every_other(n - 2)

print(sum_every_other(4))
print(sum_every_other(5))
```
```text
6
RecursionError: maximum recursion depth exceeded
```

**Fix:** a base case that catches every way down: `0 if n <= 0 else ...`. The same error hits a correct non-tail recursion on inputs much bigger than 1000: use an accumulator for those.

## Unit 2: data (§2)

### 13. Comparing a boolean with `== True`

**What goes wrong:** in §1 and §2, `==` and `!=` do not accept booleans or functions.

```python title="§2"
xs = llist(1, 2)
if is_pair(xs) == True:
    print("pair")
```
```text
TypeError: unsupported operand type(s) for ==: bool and bool
```

**Fix:** use the boolean itself: `if is_pair(xs):`, and `not p` instead of `p == False`.

### 14. `head(None)`: the forgotten base case

**What goes wrong:** the recursion walks off the end of the llist and takes the head of the empty llist.

```python title="§2"
def largest(xs):
    return head(xs) if head(xs) > largest(tail(xs)) else largest(tail(xs))

print(largest(llist(3, 9, 4)))
```
```text
TypeError: head(xs) expects a pair as argument xs, but encountered None
```

**Fix:** test `is_none(...)` first. Here the base case is a one-element llist: `if is_none(tail(xs)): return head(xs)`. Also name the recursive result once instead of computing it twice (that doubles the time at every level).

### 15. `reduce` folds from the RIGHT

**What goes wrong:** `reduce(f, init, llist(a, b, c))` is `f(a, f(b, f(c, init)))`. The function gets (element, result for the rest), and the LAST element is combined first. Code written for a left fold gives the wrong answer.

```python title="§2"
digits = llist(1, 2, 3)
print(reduce(lambda acc, d: acc * 10 + d, 0, digits))
print(reduce(lambda d, rest: rest * 10 + d, 0, reverse(digits)))
```
```text
60
123
```

**Fix:** name the parameters `(x, rest)` so you remember the order, and trace the inner `f(c, init)` first. For a left-to-right accumulation, reverse first or write a helper with an accumulator.

### 16. `pair(xs, x)` does not add at the end

**What goes wrong:** `pair` always adds at the FRONT. `pair(xs, x)` makes a pair whose head is the whole llist.

```python title="§2"
xs = llist(1, 2, 3)
print_llist(pair(xs, 4))
print_llist(append(xs, llist(4)))
```
```text
[llist(1, 2, 3), 4]
llist(1, 2, 3, 4)
```

**Fix:** `append(xs, llist(x))`, at Θ(length of xs). Doing that once per element costs Θ(n²): build at the front and reverse once instead.

### 17. Tree recursion with the tests in the wrong order

**What goes wrong:** `None` is also "not a pair". Testing for a leaf first counts every `None` as a data item.

```python title="§2"
def count_items(x):
    return (1 if not is_pair(x)
            else 0 if is_none(x)
            else count_items(head(x)) + count_items(tail(x)))

print(count_items(llist(1, llist(2, 3))))
```
```text
5
```

**Fix:** `is_none(x)` first, then `not is_pair(x)`, then recurse on head and tail. The right answer is 3.

## Unit 3: state (§3)

### 18. `tail` of a stream is a function

**What goes wrong:** the tail of a stream is a nullary function, not a stream. `tail(s)` gives that function; `stream_tail(s)` calls it.

```python title="§3"
s = integers_from(1)
print(head(stream_tail(s)))
print(head(tail(s)))
```
```text
2
TypeError: head(xs) expects a pair as argument xs, but encountered <function (anonymous)>
```

**Fix:** always `stream_tail(s)` (or `tail(s)()`). When you build a stream, the tail must be `lambda: ...`.

### 19. A lambda in a loop sees the variable, not its value

**What goes wrong:** every lambda made in the loop refers to the SAME loop variable `i`. When they run, `i` holds its last value.

```python title="§3"
makers = [None] * 3
for i in range(3):
    makers[i] = lambda: i * 10
print(makers[0](), makers[1](), makers[2]())
```
```text
20 20 20
```

**Fix:** make each function in a call of its own, so each has its own frame: `def make(k): return lambda: k * 10`, then `makers[i] = make(i)`. That prints `0 10 20`.

### 20. `[[0] * n] * m` shares one row

**What goes wrong:** `*` repeats the ELEMENTS. The outer `* 2` puts the same row list in both places, so changing one row changes "both".

```python title="§3"
grid = [[0] * 3] * 2
grid[0][0] = 7
print(grid)
print(grid[0] is grid[1])
```
```text
[[7, 0, 0], [7, 0, 0]]
True
```

**Fix:** a fresh row per iteration: `grid = [None] * 2`, then `for r in range(2): grid[r] = [0] * 3`.

### 21. Changing an enclosing function's variable without `nonlocal`

**What goes wrong:** `count = count + 1` assigns, so `count` becomes local to the inner function, and its right side reads that local before it has a value.

```python title="§3"
def make_counter():
    count = 0
    def step():
        count = count + 1
        return count
    return step

c = make_counter()
print(c())
```
```text
UnassignedLocalError: cannot access local variable 'count' where it is not associated with a value
```

**Fix:** put `nonlocal count` as the first line of `step`. For a top-level variable, `global count`.

### 22. `is` versus `==`

**What goes wrong:** `==` compares structure; `is` asks "the same object?". Every `pair(...)`, list expression and lambda makes a NEW object.

```python title="§3"
a = pair(1, 2)
b = pair(1, 2)
c = a
print(a == b, a is b, a is c)
set_head(c, 9)
print(a)
```
```text
True False True
[9, 2]
```

**Fix:** use `==` for "same contents" and `is` only to detect sharing (aliases). `c = a` copies nothing: mutating `c` mutates `a`.

### 23. A memo table the recursive calls never see

**What goes wrong:** memoizing the outer call is not enough. Inside `fib`, the recursive calls go to plain `fib`, so the table is consulted once and the time stays exponential.

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

slow = memoize(fib, 30)
fast = memoize(lambda n: n if n <= 1 else fast(n - 1) + fast(n - 2), 30)
measure(slow, 18)
measure(fast, 18)
```
```text title="Output"
[measure] memo_f(18): 8,362 calls, 91,982 steps, at most 19 waiting at once
[measure] memo_f(18): 54 calls, 729 steps, at most 36 waiting at once
```

**Fix:** the recursive calls must go through the memoized name, as in `fast`. Θ(φⁿ) becomes Θ(n).

### 24. Methods and growing lists

**What goes wrong:** there are no methods (`x.y`) in Python §1–§4, and lists cannot grow. `xs.append(4)` is rejected; `xs[3] = 4` on a list of length 3 is an IndexError.

```python title="§3"
xs = [1, 2, 3]
xs.append(4)
```
```text
FeatureNotSupportedError: Python §1-§4 does not have this: attribute access (a.b)
```

**Fix:** allocate the size you need first (`[None] * n`), then fill by index. Count first if you do not know the size (two-pass filter).

## Unit 4: beyond (§4)

### 25. A one-statement program has no `"sequence"`

**What goes wrong:** `parse` wraps several statements in a `"sequence"` node, but a program of ONE statement is that statement itself. An evaluator that expects a sequence breaks on short programs.

```python title="§4"
print(head(parse("x = 1")))
print(head(parse("x = 1\ny = 2")))
print_llist(parse("x = 1"))
```
```text
assignment
sequence
llist('assignment', llist('name', 'x'), llist('literal', 1))
```

**Fix:** dispatch on the tag (`is_tagged_llist(component, "sequence")` and so on), never assume the outer shape. Look at the real shape with `print_llist(parse(...))` first.

*In the course: all units · see the other [sheets](index.md) for the rules behind each trap.*
