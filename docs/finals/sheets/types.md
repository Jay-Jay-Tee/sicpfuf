# Typed Python §4

<p class="chapter-goal">Annotations, subtypes, None narrowing, generic llist functions, what the checker rejects, and objects made from function objects.</p>

!!! note "How to read this page"
    **Python §4 Typed** is §4 plus **type annotations**. The program is parsed, then **type-checked**, and runs only if the checker finds no type errors. At run time the annotations are ignored. Typed code below is shown as illustration (not run here); the untyped parts in sections 7–8 are run.

## 1. The syntax

| You write | Meaning |
|---|---|
| `def f(x: int, y: float) -> float:` | every parameter AND the return type must be annotated |
| `count: int = 0` | annotated assignment |
| `int`, `float`, `str`, `bool`, `None` | the basic types |
| `Callable[[int, str], bool]` | a function from an `int` and a `str` to a `bool` |
| `Pair[int, str]` | a pair with an `int` head and a `str` tail |
| `LList[int]` | `None` or `Pair[int, LList[int]]` (pre-declared) |
| `Stream[int]` | `None` or `Pair[int, Callable[[], Stream[int]]]` (pre-declared) |
| `list[float]` | a Python list of floats |
| `int | None` | an `int` or `None` |
| `def f[A](x: A) -> A:` | a **generic** function: works for every type `A` |
| `type Vector = list[float]` | a **type alias**: a new name for a type |

```python
def area(width: float, height: float) -> float:
    return width * height

scale: Callable[[float], float] = lambda x: 2 * x     # a lambda gets its type from the name
type Matrix = list[list[float]]
```

## 2. Subtypes

A type is a set of values. S is a **subtype** of T if every S value is also a T value; then an S may be used where a T is expected, not the other way round.

1. `int` is a subtype of `float`: `area(3, 4)` is fine.
2. `T` is a subtype of `T | None`: an `int` may be returned from a function declared `-> int | None`.
3. `bool` is NOT a number: `True + 1` is rejected.

## 3. `None` and narrowing

A value of type `LList[int]` may be `None`, so `head(xs)` is rejected until the checker knows `xs` is a pair. A test with `is_none` (or `is None`) **narrows** the type: in one branch it is `None`, in the other it is the pair.

```python
def sum_llist(xs: LList[int]) -> int:
    return 0 if is_none(xs) else head(xs) + sum_llist(tail(xs))   # accepted: narrowed

def first(xs: LList[int]) -> int:
    return head(xs)                       # REJECTED: xs may be None

def last(xs: LList[int]) -> int | None:   # absence is part of the type
    if is_none(xs):
        return None
    elif is_none(tail(xs)):
        return head(xs)
    else:
        return last(tail(xs))

def last_or_zero(xs: LList[int]) -> int:
    found = last(xs)
    return 0 if is_none(found) else found  # must deal with None before using it as an int
```

## 4. Generic llist functions

```python
def length[A](xs: LList[A]) -> int:
    return 0 if is_none(xs) else 1 + length(tail(xs))

def map[A, B](f: Callable[[A], B], xs: LList[A]) -> LList[B]:
    return None if is_none(xs) else pair(f(head(xs)), map(f, tail(xs)))

def filter[A](pred: Callable[[A], bool], xs: LList[A]) -> LList[A]:
    return (None if is_none(xs)
            else pair(head(xs), filter(pred, tail(xs))) if pred(head(xs))
            else filter(pred, tail(xs)))

def reduce[A, B](f: Callable[[A, B], B], initial: B, xs: LList[A]) -> B:
    return initial if is_none(xs) else f(head(xs), reduce(f, initial, tail(xs)))
```

How to find the type of a higher-order function:

1. Name the element types with letters (`A`, `B`).
2. Read every use: `f(head(xs))` means `f` takes an `A`; its result goes into the new llist, so it returns the element type `B` of the result.
3. `reduce`'s `f` takes an element and the accumulated value and returns a new accumulated value: `Callable[[A, B], B]`, and `initial` is a `B`.

Not everything can be generic: a sort compares with `<=`, which is not defined for every `A`. Fix the element type (`LList[int]`) or take the comparison as a parameter `before: Callable[[A, A], bool]`.

## 5. What the checker rejects

| Program | Why it is rejected |
|---|---|
| `def f(x: int) -> str: return x + 1` | returns an `int` where `str` is declared |
| `def g(s: str) -> int: return s * 2` | `*` on a `str` and an `int` |
| `def h(n: int) -> int: return 1 if n else 0` | a condition must be `bool`, `n` is `int` |
| `def k(xs: LList[int]) -> int: return head(xs)` | `xs` may be `None` |
| `map(lambda s: s + "!", llist(1, 2))` | the elements are `int`, so `s + "!"` adds a `str` to an `int` |
| `def m(x): return x` | parameter and return type are not annotated |
| `total: int = 0.5` | `float` is not assignable to `int` (the subtype goes the other way) |

The trade-off: the checker finds these on EVERY path before running, even in code that would never run, at the price of rejecting some programs that would have worked. Types rule out certain errors; they do not prove the program correct.

## 6. How to answer this in the exam

1. **"Annotate this function"**: annotate every parameter and the return type. Look at how each parameter is USED (`head(xs)` → a llist or pair; `f(x)` → a `Callable`; `+` with a number → `int`/`float`). Element type unknown or irrelevant → make it generic.
2. **"Will the checker accept it? Where does it complain?"**: go through the body expression by expression and compute each type. Check: operator operand types, conditions are `bool`, return expression matches `->`, arguments match parameter types, `head`/`tail` only on a value that cannot be `None`.
3. **"Fix it"**: the usual fixes are an `is_none` test before using the value, a changed annotation (`int | None`, `float`), or a conversion.

## 7. Objects from function objects

An **object** = state + operations on it. A maker function keeps the state in its frame; a **dispatch function** chooses the operation from a **message** (a string). This is **message passing**. Each maker call makes an independent object.

```python title="§4"
def make_stack():
    items = None                       # the state: a llist, top first
    def push(x):
        nonlocal items
        items = pair(x, items)
        return length(items)
    def pop():
        nonlocal items
        top = head(items)
        items = tail(items)
        return top
    def dispatch(message):
        return (push if message == "push"
                else pop if message == "pop"
                else error("unknown message:", message))
    return dispatch

s = make_stack()
t = make_stack()
s("push")(10)
s("push")(20)
t("push")(99)
print(s("pop")(), s("pop")(), t("pop")())
```
```text title="Output"
20 10 99
```

The environment model explains it: `s` and `t` point to two `dispatch` function objects whose environments are two different maker frames, each with its own `items`.

## 8. Classes (a preview: NOT Python §4)

Full Python and Java package the same idea as a **class**: a blueprint whose **instances** have **attributes** (the state) and **methods** (the operations), reached with dot notation. A class is also a type. Python §4 has no classes, no `self`, no dots.

```python
class Stack:                           # full Python only
    def __init__(self):
        self.items = None
    def push(self, x):
        self.items = pair(x, self.items)
    def pop(self):
        top = head(self.items)
        self.items = tail(self.items)
        return top
```

`s = Stack(); s.push(10)` in full Python corresponds to `s = make_stack(); s("push")(10)` in §4.

## 9. Traps

1. Forgetting the return annotation, or annotating only some parameters: rejected.
2. Using a value of type `T | None` as a `T` without an `is_none` test first.
3. `int` fits where `float` is expected; `float` does NOT fit where `int` is expected.
4. A condition of type `int` or `LList[…]` (`if xs:`) is rejected: write `is_none(xs)` / `n != 0`.
5. A lambda has no annotations of its own: its type comes from the annotated name or parameter it is given to.
6. Generic is not "anything goes": inside `def f[A](x: A)` you cannot do `x + 1`, because `A` may not be a number.

*In the course: L13A.*
