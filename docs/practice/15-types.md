# Drill 15 · Typed Python §4

<p class="chapter-goal">Predict what the type checker rejects and why, annotate functions (generics, Callable, LList[T], T | None), and build message-passing objects.</p>

Easiest first. Try each problem on paper before you open the answer.

!!! note "How the answers on this page are checked"
    sicpfuf's own checker for Python §4 Typed (`--typed`) was not finished when this page was written, so the **annotated** programs here are illustrations, not run. Their answers follow the checking rules of the lectures (below). Where it helps, the same function **without** annotations is run in plain Python §4, to show where things go wrong when nobody checks first. The message-passing problems at the end are ordinary Python §3 and are run.

!!! tip "The rules you need"
    1. Every parameter and every return type is annotated: `def f(x: int) -> int:`. Annotated assignment: `name: T = value`.
    2. Basic types: `int`, `float`, `str`, `bool`, `None`. `int` is a **subtype** of `float`, and `T` is a subtype of `T | None`: a value of the smaller type may go where the bigger type is expected, never the other way round.
    3. Conditions must be `bool`. A `bool` is not a number.
    4. Function types: `Callable[[A, B], C]`. Llists: `LList[T]` (which is `Pair[T, LList[T]] | None`); lists: `list[T]`; streams: `Stream[T]`.
    5. `LList[T]` may be `None`, so `head(xs)` is rejected until a test such as `is_none(xs)` has **narrowed** `xs` to a pair in that branch.
    6. Generic functions: `def f[A](x: A) -> A:`. Inside, you may only do with an `A` what works for **every** type.
    7. The checker runs **before** the program; annotations do nothing at run time.

## 1. Halving ★

*Skill: `/` always gives a float.*

What does the checker say about this function? Give two different fixes.

```python
def half(n: int) -> int:
    return n / 2
```

??? success "Answer"
    It is **rejected** at the return statement: `n / 2` has type `float` (the `/` operator always gives a float, even for `4 / 2`), and a `float` is not assignable to the declared return type `int` (`int` is a subtype of `float`, not the reverse).

    Fix 1, keep the result whole: `return n // 2`. Fix 2, admit the truth: `def half(n: int) -> float:`.

    Without annotations it runs without any error, and gives a float:

    ```python title="§4"
    def half(n):
        return n / 2

    print(half(4), half(3))
    ```
    ```text
    2.0 1.5
    ```
    The checker rejects a program that "works", because the annotation promised an `int`. That is the trade-off: it guarantees the absence of a kind of error, at the price of rejecting some programs.

## 2. Some or none ★

*Skill: conditions must be `bool`.*

```python
def describe(count: int) -> str:
    return "some" if count > 0 else "none"

def describe2(count: int) -> str:
    return "some" if count else "none"
```

Which one is rejected, and when would the problem show up without a checker?

??? success "Answer"
    `describe2` is rejected: the predicate of the conditional expression has type `int`, but a condition must be `bool`. `describe` is fine: `count > 0` is a `bool`.

    Without a checker the error appears only **while running**, and only when that line is reached:

    ```python title="§4"
    def describe2(count):
        return "some" if count else "none"

    print(describe2(3))
    ```
    ```text
    TypeError: conditional expression condition must be bool, not int
    ```

## 3. Points for passing ★

*Skill: a `bool` is not a number.*

```python
def score(passed: bool) -> int:
    return passed * 10
```

??? success "Answer"
    Rejected: `*` needs numbers, and `passed` is a `bool`. Fix: `return 10 if passed else 0`. Untyped, it fails at run time, again only once someone calls it:

    ```python title="§4"
    def score(passed):
        return passed * 10

    print(score(True))
    ```
    ```text
    TypeError: unsupported operand type(s) for *: bool and int
    ```

## 4. Subtype or not? ★★

*Skill: where a value of one type may be used for another.*

`def area(r: float) -> float` and `def count_up(n: int) -> int` are given. Accepted or rejected?

```python
a: float = area(2)
b: int = count_up(2.5)
c: int | None = 5
d: int = c
e: float | None = count_up(1)
```

??? success "Answer"
    - `a: float = area(2)`: **accepted**. `2` is an `int`, and `int` is a subtype of `float`.
    - `b: int = count_up(2.5)`: **rejected**. `count_up` expects `n` to be `int`, but got `float`.
    - `c: int | None = 5`: **accepted**. `int` is a subtype of `int | None`.
    - `d: int = c`: **rejected**. `c` has the declared type `int | None`, which may be `None`, and that is not assignable to `int`.
    - `e: float | None = count_up(1)`: **accepted**. An `int` is a `float`, which is a `float | None`.

    For `d`, the checker goes by the **declared** type of `c`, not by the value 5 you can see.

## 5. The first element ★★

*Skill: `None` narrowing on `LList[T]`.*

```python
def first(xs: LList[int]) -> int:
    return head(xs)
```

Why is it rejected? Fix it so that it is accepted and says honestly what happens for the empty llist.

??? success "Answer"
    `LList[int]` is `Pair[int, LList[int]] | None`. `head` needs a pair, and `xs` may be `None` (the checker suggests testing with `is_none` first). After the test, the checker knows `xs` is a pair in the `else` branch:

    ```python
    def first(xs: LList[int]) -> int | None:
        if is_none(xs):
            return None
        else:
            return head(xs)
    ```

    The return type must now be `int | None`, and every **caller** has to deal with `None` before using the result as a number. Without a checker, the mistake shows up only when somebody passes the empty llist:

    ```python title="§4"
    def first(xs):
        return head(xs)

    print(first(llist(4, 5)))
    print(first(None))
    ```
    ```text
    4
    TypeError: head(xs) expects a pair as argument xs, but encountered None
    ```

## 6. Annotate compose ★★

*Skill: generic function types with `Callable`.*

Give the most general annotation for:

```python
def compose(f, g):
    return lambda x: f(g(x))
```

??? success "Answer"
    ```python
    def compose[A, B, C](f: Callable[[B], C], g: Callable[[A], B]) -> Callable[[A], C]:
        return lambda x: f(g(x))
    ```

    Read it from the inside out: `x` is an `A`; `g` turns an `A` into a `B`; `f` turns that `B` into a `C`; so the result is a function from `A` to `C`. The lambda itself carries no annotations: its type comes from the declared return type. Example: with `def double(n: int) -> int` and `def label(n: int) -> str`, `compose(label, double)` has type `Callable[[int], str]`, while `compose(double, label)` is rejected: `label` returns a `str`, but `double` expects an `int`.

## 7. Generic llist functions ★★

*Skill: annotate llist functions with type parameters.*

Annotate both, as generally as possible, and write the bodies so that the checker accepts them.

1. `last(xs)`: the last element of `xs`, or `None` if it is empty.
2. `count_if(pred, xs)`: how many elements of `xs` satisfy `pred`.

??? success "Answer"
    ```python
    def last[T](xs: LList[T]) -> T | None:
        if is_none(xs):
            return None
        elif is_none(tail(xs)):
            return head(xs)
        else:
            return last(tail(xs))

    def count_if[T](pred: Callable[[T], bool], xs: LList[T]) -> int:
        if is_none(xs):
            return 0
        else:
            return (1 if pred(head(xs)) else 0) + count_if(pred, tail(xs))
    ```

    `head(xs)` and `tail(xs)` are allowed only in branches where `is_none(xs)` was `False`. `pred` must return `bool`, because its result is used as a condition. The same code, untyped, runs:

    ```python title="§4"
    def last(xs):
        if is_none(xs):
            return None
        elif is_none(tail(xs)):
            return head(xs)
        else:
            return last(tail(xs))

    def count_if(pred, xs):
        if is_none(xs):
            return 0
        else:
            return (1 if pred(head(xs)) else 0) + count_if(pred, tail(xs))

    print(last(llist("a", "b", "c")), last(None))
    print(count_if(lambda n: n % 2 == 0, llist(1, 2, 4, 7)))
    ```
    ```text
    c None
    2
    ```

## 8. Not everything can be generic ★★★

*Skill: why `<=` breaks a generic sort, and two ways out.*

```python
def insert[T](x: T, xs: LList[T]) -> LList[T]:
    return (pair(x, xs) if is_none(xs) or x <= head(xs)
            else pair(head(xs), insert(x, tail(xs))))
```

Why is this rejected? Give two fixes.

??? success "Answer"
    Inside a generic function, `T` could be **any** type, including functions or llists, and `<=` only works on two numbers or two strings. The checker cannot know that the `T` used later will be comparable, so `x <= head(xs)` is rejected. (The `is_none(xs) or …` part is fine: on the right of `or`, `xs` is known not to be `None`.)

    Fix 1: give up generality and fix the element type, e.g. `def insert(x: int, xs: LList[int]) -> LList[int]:`.

    Fix 2: keep it generic and let the caller say how to compare:

    ```python
    def insert[T](x: T, xs: LList[T], before: Callable[[T, T], bool]) -> LList[T]:
        return (pair(x, xs) if is_none(xs) or before(x, head(xs))
                else pair(head(xs), insert(x, tail(xs), before)))
    ```

    ```python title="§4"
    def insert(x, xs, before):
        return (pair(x, xs) if is_none(xs) or before(x, head(xs))
                else pair(head(xs), insert(x, tail(xs), before)))

    print_llist(insert(3, llist(1, 2, 5), lambda a, b: a <= b))
    print_llist(insert("kiwi", llist("apple", "fig"), lambda a, b: len(a) >= len(b)))
    ```
    ```text
    llist(1, 2, 3, 5)
    llist('apple', 'kiwi', 'fig')
    ```
    The second call keeps a llist ordered longest first: the same `insert`, a different `before`.

## 9. A lamp object ★★

*Skill: predict a message-passing object.*

An **object** is state plus operations. A maker creates the state in its frame and returns a **dispatch** function that picks an operation by a string message.

```python title="§3"
def make_lamp(name):
    is_on = False
    uses = 0
    def switch():
        nonlocal is_on, uses
        is_on = not is_on
        uses = uses + 1 if is_on else uses
        return name + (" on" if is_on else " off")
    def dispatch(message):
        if message == "switch":
            return switch
        elif message == "uses":
            return uses
        else:
            return error("unknown message", message)
    return dispatch

desk = make_lamp("desk")
hall = make_lamp("hall")
print(desk("switch")())
print(desk("switch")())
print(hall("switch")())
print(desk("switch")())
print(desk("uses"), hall("uses"))
print(desk("dim"))
```

??? success "Answer"
    ```text
    desk on
    desk off
    hall on
    desk on
    2 1
    Error: unknown message dim
    ```
    `desk("switch")` returns the `switch` function of **desk's** frame; the extra `()` applies it. `"uses"` returns a value directly, not a function, so it has no `()`. `desk` and `hall` were made by two calls of `make_lamp`, so they have separate `is_on` and `uses`. `uses` counts only switching **on**: desk was switched on twice. An unknown message reaches `error`.

## 10. A queue object ★★★

*Skill: write a message-passing object with private llist state.*

Write `make_queue()`. It returns a dispatch function for the messages `"add"` (returns a function of one argument that puts it at the back), `"remove"` (returns a function of no arguments that takes the front element away and returns it, or returns `None` if the queue is empty) and `"size"` (returns the number of elements). Adding must be Θ(1): keep a pointer to the last pair and use `set_tail`.

??? success "Answer"
    ```python title="§3"
    def make_queue():
        front = None
        rear = None
        size = 0
        def add(x):
            nonlocal front, rear, size
            new_pair = pair(x, None)
            if is_none(front):
                front = new_pair
            else:
                set_tail(rear, new_pair)
            rear = new_pair
            size = size + 1
        def remove():
            nonlocal front, rear, size
            if is_none(front):
                return None
            else:
                x = head(front)
                front = tail(front)
                if is_none(front):
                    rear = None
                size = size - 1
                return x
        def dispatch(message):
            return (add if message == "add"
                    else remove if message == "remove"
                    else size if message == "size"
                    else error("unknown message", message))
        return dispatch

    q = make_queue()
    q("add")("a")
    q("add")("b")
    print(q("remove")(), q("size"))
    q("add")("c")
    print(q("remove")(), q("remove")(), q("remove")(), q("size"))
    ```
    ```text
    a 1
    b c None 0
    ```
    Three pieces of private state live in the frame of `make_queue()`, all declared `nonlocal` where they are reassigned. `add` **mutates** the old last pair (`set_tail`) so the front of the llist sees the new element, then moves `rear`. When the last element is removed, `rear` is reset too. Note that `"size"` must be asked **each time**: dispatch returns the current value of `size` at that moment.

## 11. Can the lamp be typed? ★★★

*Skill: understand what a dispatch function's type would have to be.*

Try to annotate `dispatch` from problem 9: `def dispatch(message: str) -> ???`. What goes wrong, and what does the course offer instead?

??? success "Answer"
    For `"switch"` it returns a function, `Callable[[], str]`; for `"uses"` it returns an `int`. One return type has to cover both, so the best you can write is `Callable[[], str] | int`, and then every caller must find out which one it got before using it: `desk("uses") + 1` would be rejected, because the value might be a function. Message passing with strings hides the operations from the checker.

    The way out is a **class**: a blueprint whose attributes and methods each have their own type, and a class is itself a type usable in annotations. Python §4 has no classes; full Python and Java do.

*In the course: L13A.*
