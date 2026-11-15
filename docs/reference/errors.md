# Errors explained

<p class="chapter-goal">Every error sicpfuf can report: a tiny program that causes it, what it means, and how to fix it.</p>

## How to read an error report

Every report has the same shape. Here is one from a program that divides by zero two calls deep:

```python title="§1"
def average(total, count):
    return total / count

def mean_of_none(total):
    return average(total, 0) + 0

print(average(10, 4))
print(mean_of_none(10))
```
```text title="Output"
2.5
ZeroDivisionError at line 2
    return total / count
ZeroDivisionError: division by zero
  in average, called from line 5: return average(total, 0) + 0
  in mean_of_none, called from line 8: print(mean_of_none(10))
sicpfuf hint: check the divisor before dividing, for example with a base case `if n == 0`.
```

Read it from the top:

1. **`ZeroDivisionError at line 2`**: the kind of error and the line where it happened. This first line is the same as the one py-slang (the course's own implementation) prints.
2. **The line itself**, so you do not have to look it up.
3. **`ZeroDivisionError: division by zero`**: what went wrong.
4. **The `in ..., called from line ...` lines**: the calls that were waiting when the error happened, the **innermost first**. Here: the error is in `average`, which was called from line 5 (inside `mean_of_none`), which was called from line 8. Follow them downwards to get from the crash back to your top-level code.
5. **`sicpfuf hint:`**: the usual cause, in plain words. This line is sicpfuf's own.

Two more things about "called from" lines:

- A run of identical calls (a recursion) is folded into one line with a count, like `(x3)`.
- Calls made *inside* library functions such as `map` are left out. An error inside the library is reported at the line of **your** call into it.

```python title="§2"
def down(n):
    return 1 / n if n == 0 else down(n - 1) + 1

print(down(3))
```
```text title="Output"
ZeroDivisionError at line 2
    return 1 / n if n == 0 else down(n - 1) + 1
ZeroDivisionError: division by zero
  in down, called from line 2: return 1 / n if n == 0 else down(n - 1) + 1  (x3)
  in down, called from line 4: print(down(3))
sicpfuf hint: check the divisor before dividing, for example with a base case `if n == 0`.
```

Here `down(3)` was called from line 4, and then three more calls of `down` were made from line 2 before the division by zero.

!!! note "Before running, or while running?"
    Some errors are found **before** the program runs: NameNotFoundError, NameReassignmentError, "Feature not supported", SyntaxError, IndentationError, ModuleNotFoundError, ImportError and (with `--typed`) StaticTypeError. Then **nothing** is printed, not even by the lines above the mistake. All the other errors happen **while** the program runs, so everything printed before them stays on the screen.

## Errors found before the program runs

### NameNotFoundError

**Meaning:** you used a name that is declared nowhere in the program: not by an assignment, a `def`, a parameter or an import. It does not matter whether the line would ever run.

```python title="§1"
def area(r):
    return math_pi * radius * radius

print("start")
```
```text title="Output"
NameNotFoundError at line 2
    return math_pi * radius * radius
                     ^
NameNotFoundError: the name 'radius' is not found in the current or enclosing environment(s)
sicpfuf hint: every name must be declared somewhere: by `name = ...`, by `def name(...)`, as a parameter, or by `from module import name`.
```

**Fix:** check the spelling (sicpfuf suggests a close name when it finds one), or declare the name. If the name is from a later chapter, such as `pair` in §1, the hint says so:

```python title="§1"
p = pair(1, 2)
```
```text
NameNotFoundError: the name 'pair' is not found in the current or enclosing environment(s)
```

### NameReassignmentError

**Meaning:** in §1 and §2 a name may get a value only **once** in each scope. Parameters already have a value. Assigning the same name in the two branches of an `if`/`else` also counts as twice.

```python title="§2"
def count_items(xs):
    xs = tail(xs)
    return length(xs) + 1
```
```text title="Output"
NameReassignmentError at line 2
    xs = tail(xs)
    ^
NameReassignmentError: the name 'xs' already has a value
sicpfuf hint: in Python §1 and §2 a name gets its value ONCE and keeps it. That is what lets you replace a name by its value (the substitution model). Pick a new name instead. (A parameter counts as already having a value, and so does a name assigned in the other branch of an if/else.)
```

**Fix:** pick a new name (`rest = tail(xs)`), or return directly from each branch. Reassignment only exists from §3 on.

### Feature not supported

**Meaning:** the program uses a piece of Python that your chapter (or every chapter) does not have. The first line names the feature and the place.

```python title="§2"
def count(n):
    total = 0
    while n > 0:
        n = n - 1
    return total
```
```text title="Output"
Feature not supported in this sublanguage: while loops (line 3, col 5)
    while n > 0:
    ^
FeatureNotSupportedError: Python §2 does not have this: while loops
sicpfuf hint: loops arrive in Python §3. In §1 and §2, repeat things with recursion.
```

**Fix:** the hint tells you what to write instead. Loops, lists and `pass` come in §3; things like `x += 1`, tuples, dictionaries and slices are in no chapter. The full table is in [the language reference](language.md#what-real-python-has-and-the-course-language-does-not).

```python title="§3"
x = 1
x += 1
```
```text title="Output"
Feature not supported in this sublanguage: augmented assignment (+=) (line 2, col 1)
    x += 1
    ^
FeatureNotSupportedError: Python §1-§4 does not have this: augmented assignment (+=)
sicpfuf hint: write it out in full: x = x + ...
```

### SyntaxError

**Meaning:** the text is not a well-formed program. The `^` points at the place where the parser gave up; the real mistake is often just before it.

A missing colon:

```python title="§1"
def double(x)
    return 2 * x
```
```text title="Output"
SyntaxError at line 1
    def double(x)
                 ^
SyntaxError: expected ':'
sicpfuf hint: if / elif / else / while / for / def lines must end with a colon ':'
```

`=` where `==` was meant:

```python title="§1"
x = 3
if x = 3:
    print("three")
```
```text title="Output"
SyntaxError at line 2
    if x = 3:
         ^
SyntaxError: invalid syntax. Maybe you meant '==' instead of '='?
sicpfuf hint: to COMPARE use '==' ; a single '=' means 'give this name a value'.
```

**The rules for `range`** (§3 and §4). `range` may only appear as the header of a `for` loop, with 1 to 3 integer arguments. Anything else is rejected before running:

```python title="§3"
numbers = range(10)
```
```text title="Output"
SyntaxError at line 1
    numbers = range(10)
              ^
SyntaxError: 'range' can only be used in a for-loop header, as in 'for i in range(n):'
sicpfuf hint: write `for i in range(n):`. In Python §3 and §4 range is not a function you can call or store anywhere else.
```

```python title="§3"
range = 5
```
```text
SyntaxError: 'range' is reserved and cannot be redefined
```

**`break` and `continue`** must be inside a loop of the **same** function. A `def` inside a loop starts a new function, so a `break` in its body is outside any loop:

```python
for i in range(3):
    def stop():
        break           # SyntaxError: 'break' outside loop
```

sicpfuf reports `SyntaxError: 'break' outside loop` (and `SyntaxError: 'continue' not properly in loop` for `continue`), before the program runs. Fix: put the `break` directly in the loop's body, or let the inner function `return` a value that the loop tests.

**`nonlocal`** only reaches names of an **enclosing function**, never names of the program:

```python title="§3"
count = 0
def bump():
    nonlocal count
    count = count + 1
```
```text title="Output"
SyntaxError at line 3
    nonlocal count
    ^
SyntaxError: no binding for nonlocal 'count' found
sicpfuf hint: nonlocal only reaches names of an ENCLOSING FUNCTION. For a name of the whole program, use `global`.
```

Other SyntaxErrors: f-strings, `a = b = 1`, `;` between statements, `while ... else`. See [the language reference](language.md#what-real-python-has-and-the-course-language-does-not).

### IndentationError

**Meaning:** the lines of a block do not start at the same column, or a block (after `def ...:`, `if ...:`) is empty.

```python title="§1"
def is_big(n):
return n > 100
```
```text title="Output"
IndentationError at line 2
    return n > 100
    ^
IndentationError: expected an indented block
sicpfuf hint: Python uses indentation to group statements. Every line of a block must start at exactly the same column. Use 4 spaces, and never mix tabs and spaces.
```

```python title="§1"
def describe(n):
    if n > 0:
        print("positive")
      print("done")
```
```text title="Output"
IndentationError at line 4
    print("done")
    ^
IndentationError: unindent does not match any outer indentation level
sicpfuf hint: Python uses indentation to group statements. Every line of a block must start at exactly the same column. Use 4 spaces, and never mix tabs and spaces.
```

**Fix:** indent every block by 4 spaces more than the line that opens it, and never mix tabs with spaces.

### ModuleNotFoundError and ImportError

**Meaning:** `from M import x` names a module that does not exist (ModuleNotFoundError), or a name the module does not have (ImportError). sicpfuf has the modules `rune`, `curve`, `sound` and `repeat`.

```python title="§1"
from rune import heart
from runes import show
```
```text title="Output"
ModuleNotFoundError at line 2
    from runes import show
    ^
ModuleNotFoundError: there is no module named 'runes'
sicpfuf hint: sicpfuf has these modules: rune, curve, sound, repeat.
```

```python title="§1"
from rune import show, hart
```
```text title="Output"
ImportError at line 1
    from rune import show, hart
    ^
ImportError: module 'rune' has no name 'hart'
sicpfuf hint: did you mean 'heart'?
```

**Fix:** check the spelling. The names of each module are listed in the [library reference](library.md#modules).

### StaticTypeError (only with `--typed`)

**Meaning:** in Python §4 Typed, the type checker found a line whose types do not fit, for example a `str` passed where the function declares `int`, or `head` of a `LList` that may be `None`. All type errors are listed, and the program is not run. See [the x-ray tools](xray.md#python-4-typed-typed) for examples.

**Fix:** make the argument fit the declared type, or test `is_none(xs)` before taking `head(xs)` or `tail(xs)`.

## Errors while the program runs

### NameError

**Meaning:** the name is declared in the program, but at the top level the line that gives it its value has not run yet. Statements run from top to bottom.

```python title="§1"
print(rate * 2)
rate = 5
```
```text title="Output"
NameError at line 1
    print(rate * 2)
NameError: name 'rate' is not defined
sicpfuf hint: the name is declared in your program, but the line that gives it a value has not run yet. Statements run from top to bottom.
```

**Fix:** move the assignment above its first use. (Inside a function body this is fine: the body only runs when the function is called.)

### UnassignedLocalError

**Meaning:** a function assigns to a name *somewhere* in its body, so that name belongs to the function's own frame for the **whole** body. Reading it before the assignment has run is an error. The function does **not** use a name of the same name from outside.

```python title="§3"
balance = 100

def withdraw(amount):
    balance = balance - amount
    return balance

print(withdraw(30))
```
```text title="Output"
UnassignedLocalError at line 4
    balance = balance - amount
UnassignedLocalError: cannot access local variable 'balance' where it is not associated with a value
  in withdraw, called from line 7: print(withdraw(30))
sicpfuf hint: the function assigns to this name somewhere in its body, so the name lives in the function's own frame for the WHOLE body, even on lines before the assignment. To change a name of an enclosing function use `nonlocal`, and for a global name use `global` (Python §3 and §4).
```

In the environment model: calling `withdraw` makes a new frame that already has a slot for `balance`, still unassigned. The lookup finds that slot first, so it never reaches the global `balance`.

**Fix (§3 and §4):** say `global balance` (or `nonlocal balance` for a name of an enclosing function) at the start of the body. In §1 and §2, use a different name for the local value.

### TypeError

A value of the wrong type was used. The message names the types involved. These are the main variants.

**A condition that is not a boolean.** Conditions of `if`, `while` and conditional expressions, the operand of `not`, and every operand of `and`/`or` except the last must be exactly `True` or `False`:

```python title="§1"
def is_empty_name(name):
    return not len(name)

print(is_empty_name(""))
```
```text title="Output"
TypeError at line 2
    return not len(name)
TypeError: operand of 'not' must be bool, not int
  in is_empty_name, called from line 4: print(is_empty_name(""))
sicpfuf hint: Python §1-§4 are stricter than full Python: a condition must be exactly True or False. Write the comparison out, for example `if n != 0:` or `if not is_none(xs):`.
```

Fix: write the comparison out, `len(name) == 0`.

**Operand types that do not fit.** Numbers and strings do not mix, booleans are not numbers, and `None` is not anything:

```python title="§1"
def label(n):
    return "item " + n

print(label(3))
```
```text title="Output"
TypeError at line 2
    return "item " + n
TypeError: unsupported operand type(s) for +: str and int
  in label, called from line 4: print(label(3))
sicpfuf hint: numbers and strings don't mix in §1-§4. Convert with str(n) first, and there is no "ab" * 3.
```

Fix: `"item " + str(n)`. A `None` in the message usually means a function forgot to `return`, or a recursion ran past the end of a llist.

**Calling something that is not a function:**

```python title="§1"
width = 5
print(width(2))
```
```text title="Output"
TypeError at line 2
    print(width(2))
TypeError: 'int' object is not callable
sicpfuf hint: you put () after something that isn't a function. Did a name get a non-function value?
```

**The wrong number of arguments.** There are no default values, so the numbers must match exactly:

```python title="§1"
def area(w, h):
    return w * h

print(area(3))
```
```text title="Output"
TypeError at line 4
    print(area(3))
TypeError: area() takes exactly 2 arguments (1 given)
  in area, called from line 4: print(area(3))
sicpfuf hint: count the arguments in the call and the parameters in the `def`: they must match exactly.
```

**`head` or `tail` of something that is not a pair.** Most often it is `None`, because a base case is missing:

```python title="§2"
def last(xs):
    return head(xs) if is_none(tail(xs)) else last(tail(xs))

print(last(llist(1, 2, 3)))
print(last(None))
```
```text title="Output"
3
TypeError at line 2
    return head(xs) if is_none(tail(xs)) else last(tail(xs))
TypeError: tail(xs) expects a pair as argument xs, but encountered None
  in last, called from line 5: print(last(None))
sicpfuf hint: you took the head or tail of None, the EMPTY linked list. The usual cause is a missing base case: check `is_none(xs)` before `head(xs)` / `tail(xs)`.
```

Fix: decide what the function should do for the empty llist, and test `is_none(xs)` first.

**`==` or `!=` on a boolean or a function, in §1 and §2:**

```python title="§2"
def is_short(xs):
    return length(xs) < 3

print(is_short(llist(1)) == True)
```
```text title="Output"
TypeError at line 4
    print(is_short(llist(1)) == True)
TypeError: unsupported operand type(s) for ==: bool and bool
sicpfuf hint: in Python §1 and §2, == and != don't accept booleans or functions. Use the boolean itself (`if done:` instead of `if done == True:`), or `not done`.
```

Fix: use the boolean itself: `is_short(xs)`, or `not is_short(xs)`. From §3 on, `==` accepts any two values.

**Indexing with a non-integer, or indexing something that is not a list or string** (§3 and §4):

```python title="§3"
scores = [10, 20, 30]
print(scores[3 / 3])
```
```text title="Output"
TypeError at line 2
    print(scores[3 / 3])
TypeError: list indices must be integers, not float
```

```python title="§3"
n = 2026
print(n[0])
```
```text
TypeError: an int can't be indexed with [ ] (only lists and strings)
```

Fix: `/` always gives a float, so use `//` for an index. To get the digits of a number, use `%` and `//`.

### ZeroDivisionError

**Meaning:** `/`, `//` or `%` with 0 on the right.

```python title="§1"
def percent(part, whole):
    return part / whole * 100

print(percent(1, 4))
print(percent(1, 0))
```
```text title="Output"
25.0
ZeroDivisionError at line 2
    return part / whole * 100
ZeroDivisionError: division by zero
  in percent, called from line 5: print(percent(1, 0))
sicpfuf hint: check the divisor before dividing, for example with a base case `if n == 0`.
```

**Fix:** handle the zero case first, for example `0 if whole == 0 else part / whole * 100`.

### IndexError

**Meaning:** a list (or string) with *n* items has indexes 0 to *n* − 1, and −1 to −*n* from the end. Anything else is out of range. Lists never grow, so you cannot assign past the end either.

```python title="§3"
xs = [0] * 3
for i in range(1, 4):
    xs[i] = i * i
```
```text title="Output"
IndexError at line 3
    xs[i] = i * i
IndexError: list index out of range: index 3, but the list has 3 items
sicpfuf hint: a list with n items has indexes 0 .. n-1 (and -1 .. -n counting from the end).
```

**Fix:** loop over `range(len(xs))`, or make the list big enough first with `[0] * n`.

### RecursionError

**Meaning:** more than 1024 function calls were **waiting** for an answer at the same time. Either the base case is never reached, or the function gives a deep recursive process (it has deferred operations).

```python title="§1"
def countdown_sum(n):
    return 0 if n == 0 else n + countdown_sum(n - 1)

print(countdown_sum(1000))
print(countdown_sum(-1))
```
```text title="Output"
500500
RecursionError at line 2
    return 0 if n == 0 else n + countdown_sum(n - 1)
RecursionError: maximum recursion depth exceeded
  in countdown_sum, called from line 2: return 0 if n == 0 else n + countdown_sum(n - 1)  (x1023)
  in countdown_sum, called from line 5: print(countdown_sum(-1))
sicpfuf hint: more than 1024 calls were waiting for an answer at the same time. Either the BASE CASE is never reached, or the function is a deep RECURSIVE PROCESS (it has deferred operations). A tail call (`return f(...)` with nothing left to do afterwards) does not pile up: rewrite it as an ITERATIVE process with an accumulator.
```

`countdown_sum(1000)` works: 1001 waiting calls is under the limit. `countdown_sum(-1)` never reaches 0. The "called from" line `(x1023)` means 1023 calls from line 2 were waiting, plus the first call from line 5: 1024 in all.

**Fix:** check the base case first. If the base case is right and the input is just big, rewrite the function as an **iterative process**: carry the answer in an extra parameter so that the recursive call is a tail call (`return f(...)` with nothing left to do). Tail calls do not pile up; see [proper tail calls](language.md#proper-tail-calls-and-the-1024-limit).

### ValueError

**Meaning:** the type is right but the value is not allowed. For example a math function outside its domain, or a `range` with step 0.

```python title="§1"
print(math_log(0))
```
```text title="Output"
ValueError at line 1
    print(math_log(0))
ValueError: math domain error: math_log can't take 0
```

```python title="§3"
for i in range(0, 10, 0):
    print(i)
```
```text
ValueError: range() arg 3 must not be zero
```

### Error: (from `error(...)`)

**Meaning:** the program called `error(...)` itself, on purpose. The message is the arguments, separated by spaces. sicpfuf adds the line where `error` was called.

```python title="§1"
def safe_sqrt(x):
    return error("safe_sqrt: negative input", x) if x < 0 else math_sqrt(x)

print(safe_sqrt(9))
print(safe_sqrt(-9))
```
```text title="Output"
3.0
Error: safe_sqrt: negative input -9
  (error(...) was called at line 2)
```

Library functions use `error` too. For example `llist_ref` past the end of the llist:

```python title="§2"
print(llist_ref(llist("a", "b"), 5))
```
```text title="Output"
Error: llist_ref: index out of bounds
  (error(...) was called at line 1)
```

**Fix:** find the call that broke the function's rules (the line in brackets is where `error` was called; for a library function it is your call into it).

## Quick index

| First line starts with | Found | Usual cause |
|---|---|---|
| `NameNotFoundError` | before running | typo, or a name from a later chapter |
| `NameReassignmentError` | before running | `x = ...` twice in §1/§2, or assigning to a parameter |
| `Feature not supported` | before running | a piece of Python your chapter lacks |
| `SyntaxError` | before running | missing `:`, `=` for `==`, `range` outside a `for`, `break` outside a loop |
| `IndentationError` | before running | block lines not lined up |
| `ModuleNotFoundError`, `ImportError` | before running | misspelt module or name |
| `StaticTypeError` | before running, with `--typed` | an argument of the wrong type; `head` of a llist that may be `None` |
| `NameError` | while running | used at the top level before its assignment ran |
| `UnassignedLocalError` | while running | local name read before its assignment; missing `global`/`nonlocal` |
| `TypeError` | while running | non-boolean condition, mixed types, wrong argument count, `head(None)` |
| `ZeroDivisionError` | while running | divisor 0 |
| `IndexError` | while running | index ≥ length, or < −length |
| `RecursionError` | while running | missing base case, or a recursive process over 1024 deep |
| `ValueError` | while running | math domain, `range` step 0 |
| `Error:` | while running | `error(...)` was called |

*In the course: every lecture; NameNotFoundError is named in L5A, UnassignedLocalError in L9A.*
