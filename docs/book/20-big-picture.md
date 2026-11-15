# The big picture

<p class="chapter-goal">The course's big ideas on one page, how Python §4 differs from real Python, and where to go from here.</p>

!!! abstract "The big idea, in plain words"
    After a long hike, you look back from the top and see the whole path at once: which hill led
    to which valley. This chapter is that view. The course motto is "programming is communicating
    computational processes", to the computer AND to the people who read your code. Every idea
    below serves that.

## The big ideas, one by one

### Scope of names

Python uses **lexical scoping**: a name refers to the **closest surrounding declaration** in the
program text, not to whatever happens to be around when the function runs. `global` and
`nonlocal` stop an assignment from making a new local name.

```python title="§1"
x = "global"
def outer():
    x = "outer"
    def inner():
        return x
    return inner
show = outer()
print(show(), x)
```
```text title="Output"
outer global
```

`inner` sees the `x` of `outer`, where it was WRITTEN, even when applied at the top level.
(Chapters [5](05-higher-order-scope.md) and [14](14-environment-model.md).)

### Functional programming

Functions are values: passed as arguments, returned as results, stored in pairs. `map`, `filter`
and `reduce` capture whole patterns of llist processing. Streams are llists whose tail is
delayed, and lazy evaluation is the evaluator-level version of the same idea (normal order).
(Chapters [5](05-higher-order-scope.md), [8](08-llist-processing.md), [11](11-streams.md),
[18](18-mce-lazy.md).)

### Recursive and iterative processes

A function is recursive; a PROCESS is recursive (deferred operations pile up) or iterative (none).
Time is counted in steps, space in deferred operations plus the pairs and lists that must be
remembered; both are stated as an **order of growth** with Θ, O or Ω.

??? example "X-ray: same answer, different space"
    ```python title="§1"
    def fact(n):
        return 1 if n == 0 else n * fact(n - 1)
    def fact_iter(n, acc):
        return acc if n == 0 else fact_iter(n - 1, n * acc)
    measure(fact, 20)
    measure(fact_iter, 20, 1)
    ```
    ```text title="Output"
    [measure] fact(20): 21 calls, 246 steps, at most 21 waiting at once
    [measure] fact_iter(20, 1): 21 calls, 266 steps, at most 1 waiting at once
    ```

    Both take Θ(n) time. The recursive process keeps Θ(n) calls waiting; the iterative one Θ(1).

CPS makes every call a tail call, so the process is iterative, but the growing continuation
still takes space. (Chapters [3](03-substitution-recursion.md), [4](04-orders-of-growth.md),
[9](09-trees-cps.md).)

### The environment model

Once names can be reassigned, "replace the name by its value" stops working: the value depends
on WHEN you look. The environment model replaces it: frames of bindings, each with an enclosing
environment, and function objects that remember the environment they were created in.
(Chapters [12](12-state-mutation.md), [14](14-environment-model.md).)

### Three mental models

| Model | Good for | Breaks down when |
|---|---|---|
| substitution model | §1, §2: pure functions | names are reassigned |
| environment model | §3: state, `nonlocal`, closures | (does not break, but is slow by hand) |
| metacircular evaluator | §4: the model written as a program | (it IS the definition) |

### Data

Pairs are the glue. **Llists** are built from pairs (`None` or a pair whose tail is a llist), and
so are trees. **Lists** (from §3) map indices to values, from `-len(xs)` to `len(xs) - 1`, and
cannot grow. Data abstraction (constructors, selectors, predicates, an abstraction barrier) lets
you change a representation without changing its users. (Chapters [7](07-data-abstraction.md),
[13](13-lists-loops.md).)

### Memoization

Remember results in a table, so that each one is computed once. Top-down memoization keeps the
recursive shape; building the table bottom-up with a loop is the "beyond the course" version
(dynamic programming).

```python title="§3"
def fib(n):
    return n if n <= 1 else fib(n - 1) + fib(n - 2)

table = [None] * 31
def memo_fib(n):
    if table[n] is None:
        table[n] = n if n <= 1 else memo_fib(n - 1) + memo_fib(n - 2)
    return table[n]

measure(fib, 20)
measure(memo_fib, 20)
```
```text title="Output"
[measure] fib(20): 21,891 calls, 240,796 steps, at most 20 waiting at once
[measure] memo_fib(20): 39 calls, 748 steps, at most 20 waiting at once
```

Θ(φⁿ) calls become Θ(n). (Chapter [15](15-search-sort-memo.md).)

### Types

A type is a set of values. A static checker (Python §4 Typed) finds type mistakes on every path
before running, at the price of rejecting a few correct programs. (Chapter [19](19-types-objects.md).)

### The five-step method

1. **Read** the question twice. Underline the input, the output and the constraints.
2. **Play**: work two or three small examples by hand, including the smallest (0, `None`).
3. **Think**: which pattern? Wishful thinking ("suppose the function already works for the tail"),
   a higher-order function, an accumulator?
4. **Program**: write it, with names that say what things mean.
5. **Test**: run your hand examples, then the edge cases.

In the exam, a full-marks answer is correct, reasonably efficient AND easy to read. Keep it simple.

## Python §4 vs real Python

Python §4 is a SUBSET of Python: a §4 program almost always means the same in real Python. The
four differences that matter are below. Going the other way, real Python has much more.

### 1. Truthiness

In real Python any value can be a condition: `False`, `None`, `0`, `""` and empty collections
count as false ("falsy"), everything else as true. In Python §4 a condition must be exactly
`True` or `False`:

```python title="§4"
xs = llist(1, 2)
if xs:
    print("not empty")
```
```text
TypeError: if condition must be bool, not pair
```

```python title="§4"
print(not 0)
```
```text
TypeError: operand of 'not' must be bool, not int
```

Write the test out: `if not is_none(xs):`, `n == 0`.

### 2. No guaranteed tail calls

Python §4 runs a tail call without keeping the caller waiting, so an iterative process runs in
constant space however long it runs:

```python title="§4"
def count_down(n):
    return n if n == 0 else count_down(n - 1)
print(count_down(100000))
```
```text title="Output"
0
```

Real Python keeps every call waiting and stops at about 1000 of them with a `RecursionError`.
Outside the course, write long iterations as loops.

### 3. Lists can grow

Python §4 lists have a fixed length, and there are no methods:

```python title="§4"
xs = [1, 2]
xs[2] = 3
```
```text
IndexError: list index out of range: index 2, but the list has 2 items
```

```python title="§4"
xs = [1, 2, 3]
print([0] + xs)
```
```text
TypeError: unsupported operand type(s) for +: list and list
```

In real Python, `xs.append(3)`, `xs.extend(ys)`, `xs.insert(0, v)` and `[0] + xs` all work.

### 4. `for` over anything

In Python §4, `for` only counts over `range(...)`. Real Python loops over any collection, for
example `for ch in "abc":`, and allows a `for ... else`.

```python title="§4"
for ch in "abc":
    print(ch)
```
```text
FeatureNotSupportedError: for loops must use range() — e.g. for i in range(n) is not part of Python §1-§4
```

### Conveniences that §1 to §4 leave out

Each of these is refused by sicpfuf before the program runs, with a hint about the §4 way:

| Real Python | Name of the feature | Python §4 way |
|---|---|---|
| `x += 1` | augmented assignment | `x = x + 1` |
| `a, b = b, a` | multiple assignment (tuples) | one assignment per line, with a temporary name |
| `def f(x, y=1):` | default (and keyword) parameters | pass every argument |
| `f"n is {n}"` | f-strings | `"n is " + str(n)` |
| `xs[1:]` | slices | copy in a loop |
| `{"a": 1}` | dictionaries | a llist of pairs |
| `[x * x for x in xs]` | list comprehensions | a loop, or `map` on a llist |
| `xs.append(3)`, `math.sqrt(2)` | methods and attribute access | `math_sqrt(2)`; lists do not grow |
| `1 < x < 9` | chained comparisons | `1 < x and x < 9` |

Also missing: tuples, sets, classes, exceptions (`try`/`except`), generators, `import m` of whole
modules and packages. Check one of the rows yourself:

```python title="§4"
count = 0
count += 1
```
```text
FeatureNotSupportedError: augmented assignment (+=) is not part of Python §1-§4
```

## Running course programs outside the course tools

Inside the course you use the course's web tools; here you also have sicpfuf
(`python3 -m sicpfuf program.py -v 3`). To run a course program in ordinary Python, the
lectures suggest installing the `sourceacademy-sicp` package and starting the program with
`from sicp import *`, which supplies `pair`, `head`, `tail`, `llist` and friends. Remember the
differences above: an iterative process of 100000 steps written as a tail call will fail in real
Python.

## Where to go next

- **More SICP.** The rest of chapter 4 of the textbook: nondeterministic computing (`amb`, automatic
  search with backtracking) and logic programming (queries, rules, unification). Chapter 5 turns
  the evaluator into a register machine and a compiler.
- **Object-oriented programming.** Classes, instances, methods, and languages such as Java that are
  built around them: the message passing of [chapter 19](19-types-objects.md) grown up.
- **Algorithms and data structures.** More sorting and searching, trees, graphs, and how to prove
  orders of growth.
- **Types and languages.** Type checkers, type inference, and how interpreters and compilers are
  built: the evaluator of chapters [17](17-mce.md) and [18](18-mce-lazy.md) is the first step.

## Takeaways

- Lexical scoping: a name means its closest surrounding declaration in the text.
- Functions are values; higher-order functions, streams and lazy evaluation all build on that.
- A process is recursive or iterative; measure time and space with orders of growth.
- Three mental models: substitution (no state), environment (state), metacircular evaluator
  (the model as a program).
- Memoization trades space for time by remembering results in a table.
- Python §4 is a subset of Python: same meaning, but strict booleans, guaranteed tail calls,
  fixed-length lists and `for` over `range` only.
- Five steps: read, play, think, program, test.

## Check yourself

1. Which mental model would you use to explain `make_jar` from chapter 19, and why not the
   substitution model?

    ??? success "Answer"
        The environment model. `make_jar` reassigns `cookies` with `nonlocal`, so a name's value
        depends on when you look, and substitution cannot express that.

2. This program prints a number in Python §4. What happens in real Python?

    ```python title="§4"
    def sum_to(n, acc):
        return acc if n == 0 else sum_to(n - 1, acc + n)
    print(sum_to(50000, 0))
    ```

    ??? success "Answer"
        ```text
        1250025000
        ```

        In real Python it stops with a `RecursionError`: tail calls still keep the caller
        waiting there, and 50000 waiting calls is far over the limit of about 1000.

3. Rewrite `if name:` (meaning "if the string is not empty") for Python §4.

    ??? success "Answer"
        `if name != "":` or `if len(name) > 0:`. The condition must be a boolean.

4. A student writes `total += price` inside a loop. What does sicpfuf say, and what is the fix?

    ??? success "Answer"
        `FeatureNotSupportedError: augmented assignment (+=) is not part of Python §1-§4`. Write
        `total = total + price`.

5. Name the five steps of the method, and say which one catches "forgot the empty llist".

    ??? success "Answer"
        Read, play, think, program, test. PLAY catches it when you try the smallest example
        (`None`) by hand; TEST catches it if you missed it then.

*In the course: L13B.*
