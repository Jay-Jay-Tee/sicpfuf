# Streams II: streams that refer to themselves

<p class="chapter-goal">Define infinite streams in terms of themselves, combine them element by element, and use memo_fun so that no element is computed twice.</p>

!!! abstract "The big idea, in plain words"
    Imagine a conveyor belt that makes each new item out of items that are already on the belt. To start,
    someone puts the first item on by hand; after that the belt feeds itself. That is a
    **self-referential stream**: "the integers are 1, followed by the integers with 1 added to each".

    It works because a stream's tail is a **promise** (a nullary function): the rest is built only when
    someone asks for it, and by then enough of the stream already exists. The catch: unless we
    **memoize**, every time someone walks the belt again, every item is made again.

## A quick reminder

A stream is `None` or a pair whose tail is a nullary function returning a stream:
`pair(value, lambda: rest)`. `stream_tail(s)` applies the tail function. Python §3 pre-declares
`stream_map`, `stream_filter`, `stream_ref`, `integers_from`, `eval_stream` and friends (see
[Streams](11-streams.md)). `add_streams`, `mul_streams`, `scale_stream`, `memo_fun`, `ones` and
`integers` are **not** pre-declared: we define them below.

## A stream defined by its own name

```python title="§3"
ones = pair(1, lambda: ones)
moves = pair("rock", lambda: pair("paper", lambda: pair("scissors", lambda: moves)))

print_llist(eval_stream(ones, 4))
print_llist(eval_stream(moves, 5))
```
```text title="Output"
llist(1, 1, 1, 1)
llist('rock', 'paper', 'scissors', 'rock', 'paper')
```

Why is `lambda: ones` allowed, when `ones` is not assigned yet? Creating the lambda does not evaluate
its body. The body looks up `ones` only when the tail is forced, and by then the assignment has run. In
the [environment model](14-environment-model.md): the lambda's function object points to the global
frame, where `ones` will be bound by the time the body runs.

## Combining streams element by element

```python title="§3"
def add_streams(s1, s2):
    return (s2 if is_none(s1)
            else s1 if is_none(s2)
            else pair(head(s1) + head(s2), lambda: add_streams(stream_tail(s1), stream_tail(s2))))

def mul_streams(s1, s2):
    return (None if is_none(s1) or is_none(s2)
            else pair(head(s1) * head(s2), lambda: mul_streams(stream_tail(s1), stream_tail(s2))))

def scale_stream(c, s):
    return stream_map(lambda x: c * x, s)

tens = scale_stream(10, integers_from(1))
print_llist(eval_stream(add_streams(tens, integers_from(1)), 4))
print_llist(eval_stream(mul_streams(tens, tens), 4))
```
```text title="Output"
llist(11, 22, 33, 44)
llist(100, 400, 900, 1600)
```

All three are lazy: they compute one element now and leave the rest in a lambda. So they work on
infinite streams.

## The classics, defined implicitly

Each definition below says how the stream is built out of **itself**. Read them aloud.

```python title="§3"
def add_streams(s1, s2):
    return (s2 if is_none(s1)
            else s1 if is_none(s2)
            else pair(head(s1) + head(s2), lambda: add_streams(stream_tail(s1), stream_tail(s2))))

def mul_streams(s1, s2):
    return (None if is_none(s1) or is_none(s2)
            else pair(head(s1) * head(s2), lambda: mul_streams(stream_tail(s1), stream_tail(s2))))

def scale_stream(c, s):
    return stream_map(lambda x: c * x, s)

ones = pair(1, lambda: ones)
integers = pair(1, lambda: add_streams(ones, integers))
fibs = pair(0, lambda: pair(1, lambda: add_streams(stream_tail(fibs), fibs)))
powers_of_3 = pair(1, lambda: scale_stream(3, powers_of_3))
factorials = pair(1, lambda: mul_streams(factorials, stream_tail(integers)))

print_llist(eval_stream(integers, 6))
print_llist(eval_stream(fibs, 8))
print_llist(eval_stream(powers_of_3, 6))
print_llist(eval_stream(factorials, 6))
```
```text title="Output"
llist(1, 2, 3, 4, 5, 6)
llist(0, 1, 1, 2, 3, 5, 8, 13)
llist(1, 3, 9, 27, 81, 243)
llist(1, 2, 6, 24, 120, 720)
```

- `integers`: 1, then (1 + 1st integer), (1 + 2nd integer), …
- `powers_of_3`: 1, then every power times 3.
- `factorials`: 1, then the factorials times 2, 3, 4, … (k! × (k + 1) = (k + 1)!).
- `fibs`: 0, 1, then `fibs` added to itself shifted by one. Line the two streams up and add columns:

| | | | | | | | |
|---|---|---|---|---|---|---|---|
| `stream_tail(fibs)` | 1 | 1 | 2 | 3 | 5 | 8 | … |
| `fibs` | 0 | 1 | 1 | 2 | 3 | 5 | … |
| sum = `fibs` from its 3rd element | 1 | 2 | 3 | 5 | 8 | 13 | … |

!!! warning "Trap: the first elements must be given by hand"
    `fibs = add_streams(stream_tail(fibs), fibs)` without the two starting pairs fails at once: the right
    side needs `fibs` **now**, before it has a value. Every self-referential stream starts with
    `pair(first, lambda: …)`, and the self-reference must be **inside** the lambda.

## The sieve of Eratosthenes

To get the primes from 2, 3, 4, …: keep the first number p, remove every multiple of p from the rest,
and sieve what is left.

```python title="§3"
def sieve(s):
    return pair(head(s),
                lambda: sieve(stream_filter(lambda x: x % head(s) != 0, stream_tail(s))))

primes = sieve(integers_from(2))
print_llist(eval_stream(primes, 10))
print(stream_ref(primes, 50))
```
```text title="Output"
llist(2, 3, 5, 7, 11, 13, 17, 19, 23, 29)
233
```

Each prime found adds one more `stream_filter` to the chain, so the 51st prime has to pass 50
filters. (Strictly, this is **trial division** by every earlier prime, not the true sieve of
Eratosthenes, which crosses off multiples without testing each number.)

## A stream of better and better guesses

Newton's method for √x: start with a guess g and repeatedly replace it by the average of g and x / g.
Instead of a loop with a variable, make the **whole sequence of guesses** a stream:

```python title="§3"
def sqrt_stream(x):
    guesses = pair(1.0, lambda: stream_map(lambda g: (g + x / g) / 2, guesses))
    return guesses

print_llist(eval_stream(sqrt_stream(2), 5))
print(stream_ref(sqrt_stream(9), 5))
```
```text title="Output"
llist(1.0, 1.5, 1.4166666666666665, 1.4142156862745097, 1.4142135623746899)
3.000000001396984
```

`guesses` is a local name that refers to itself: the stream of guesses is 1.0 followed by "improve
each guess". The person who uses the stream decides how many to look at; the producer does not have
to know when to stop.

## How often is each element computed?

The stream library's tails are **not memoized**: forcing a tail runs its function again every time.
Let us count the additions `fibs` performs, with a global counter in `add_streams`:

```python title="§3"
additions = 0

def add_streams(s1, s2):
    global additions
    if is_none(s1):
        return s2
    if is_none(s2):
        return s1
    additions = additions + 1
    return pair(head(s1) + head(s2), lambda: add_streams(stream_tail(s1), stream_tail(s2)))

fibs = pair(0, lambda: pair(1, lambda: add_streams(stream_tail(fibs), fibs)))
print(stream_ref(fibs, 10), additions)
additions = 0
print(stream_ref(fibs, 20), additions)
```
```text title="Output"
55 221
6765 28635
```

Element 20 needs 19 additions, but 28,635 were done: exponential, like tree-recursive `fib`. Every
`stream_tail(fibs)` inside `add_streams` builds `fibs` again from the start.

## `memo_fun`: run a tail at most once

`memo_fun(fun)` takes a nullary function and returns a nullary function that does the same thing, but
runs `fun` only the **first** time and remembers the result:

```python title="§3"
def memo_fun(fun):
    already_run = False
    result = None
    def memoized():
        nonlocal already_run, result
        if not already_run:
            result = fun()
            already_run = True
        return result
    return memoized

def roll():
    print("rolling...")
    return 4

once = memo_fun(roll)
print(once(), once(), once())
```
```text title="Output"
rolling...
4 4 4
```

`already_run` and `result` live in the frame of `memo_fun(roll)`, the private state of `once`
(exactly like the piggy bank of the [environment model](14-environment-model.md#worked-example-4-local-state-two-instances)).

A **memoized stream** wraps every tail: `pair(h, memo_fun(lambda: …))`. Here is a memoized
`stream_map`, and a squaring function that tells us when it runs:

```python title="§3"
def memo_fun(fun):
    already_run = False
    result = None
    def memoized():
        nonlocal already_run, result
        if not already_run:
            result = fun()
            already_run = True
        return result
    return memoized

def m_stream_map(f, s):
    return None if is_none(s) else pair(f(head(s)), memo_fun(lambda: m_stream_map(f, stream_tail(s))))

def noisy_square(x):
    print("squaring", x)
    return x * x

plain = stream_map(noisy_square, integers_from(1))
print(stream_ref(plain, 2))
print(stream_ref(plain, 3))
print("--- memoized ---")
memo = m_stream_map(noisy_square, integers_from(1))
print(stream_ref(memo, 2))
print(stream_ref(memo, 3))
```
```text title="Output"
squaring 1
squaring 2
squaring 3
9
squaring 2
squaring 3
squaring 4
16
--- memoized ---
squaring 1
squaring 2
squaring 3
9
squaring 4
16
```

Read it line by line:

1. Making `plain` squares the head 1 at once (`stream_map` computes its head eagerly).
2. `stream_ref(plain, 2)` forces two tails: squaring 2 and 3.
3. `stream_ref(plain, 3)` starts again from `plain`: the head is stored, but every tail runs again,
   so 2, 3 **and** 4 are squared.
4. With `memo`, the second walk finds the tails already forced: only 4 is new.

??? example "X-ray: memoized `fibs` does one addition per element"
    ```python title="§3"
    def memo_fun(fun):
        already_run = False
        result = None
        def memoized():
            nonlocal already_run, result
            if not already_run:
                result = fun()
                already_run = True
            return result
        return memoized

    additions = 0

    def m_add_streams(s1, s2):
        global additions
        if is_none(s1):
            return s2
        if is_none(s2):
            return s1
        additions = additions + 1
        return pair(head(s1) + head(s2), memo_fun(lambda: m_add_streams(stream_tail(s1), stream_tail(s2))))

    m_fibs = pair(0, memo_fun(lambda: pair(1, memo_fun(lambda: m_add_streams(stream_tail(m_fibs), m_fibs)))))
    print(stream_ref(m_fibs, 20), additions)
    print(stream_ref(m_fibs, 20), additions)
    ```
    ```text title="Output"
    6765 19
    6765 19
    ```

    19 additions for element 20, and the second walk adds none. Θ(n) instead of exponential.

!!! warning "Trap: memoization changes side effects"
    For **pure** functions, memoizing never changes any result, only the time. If the tail functions
    print or reassign variables, memoization changes **how often** that happens, so the output changes.
    That is why the library does not memoize for you, and why "what does this print?" questions always
    say whether the stream is memoized.

!!! note "Python §3 vs real Python"
    Real Python has no `pair`/`head`/`tail` and no stream library; it would use generators, which are a
    different idea. A course stream is plain data plus nullary lambdas, so everything in this chapter can
    be explained with the environment model.

## When the head is delayed too

An ordinary stream stores its head as a **value** and its tail as a nullary function. A
fully delayed representation stores **two nullary functions**. `None` still denotes the
empty stream; a head function that returns `None` denotes a present element whose value
is `None`.

| Operation | Ordinary stream | Fully delayed representation used below |
|---|---|---|
| Read one element | `head(s)` | `head(s)()` |
| Advance once | `stream_tail(s)` | `tail(s)()` |

An ordinary library operation must not be silently applied to the fully delayed version.
The following position-labelling transformation delays reading the input head until the
corresponding output head is requested. Its first source head deliberately raises an error.

```python title="§3"
def with_positions(s, position):
    if is_none(s):
        return None
    return pair(lambda: pair(position, head(s)()),
                lambda: with_positions(tail(s)(), position + 1))

source = pair(lambda: error("unneeded first head was forced"),
              lambda: pair(lambda: None, lambda: None))
tagged = with_positions(source, 20)
second = tail(tagged)()
print(head(second)())
print(tail(second)())
```
```text title="Output"
[21, None]
None
```

Constructing the result and advancing to its second node do not need the first element's
value. Putting `head(s)()` in a local assignment **before** constructing its lambda would
force it immediately. A useful laziness test makes an unneeded head raise an error or
increment a counter, then requests only tails.

## A delayed running result needs a delayed predecessor

For a running summary, carrying an already computed accumulator can force earlier heads
too soon. Carry a nullary function that will compute the previous result instead. This
original example produces running maxima, starting from a supplied lower bound.

```python title="§3"
def remember(compute):
    ready = False
    value = None
    def get():
        nonlocal ready, value
        if not ready:
            value = compute()
            ready = True
        return value
    return get

def running_peaks(s, lower_bound):
    def build(previous, rest):
        if is_none(rest):
            return None
        current = remember(lambda: max(previous(), head(rest)()))
        return pair(current, lambda: build(current, tail(rest)()))
    return build(lambda: lower_bound, s)

forced = 0
def observe(value):
    global forced
    forced = forced + 1
    return value

def delayed_values(xs):
    return (None if is_none(xs)
            else pair(lambda: observe(head(xs)),
                      lambda: delayed_values(tail(xs))))

peaks = running_peaks(delayed_values(llist(4, 7, 3)), -math_inf)
third = tail(tail(peaks)())()
print(forced)
print(head(third)(), forced)
print(head(third)(), forced)
```
```text title="Output"
0
7 3
7 3
```

Walking two tails does no head work. Requesting the third result then forces the required
prefix, and requesting that same result again uses its remembered value. The separate
`ready` flag matters: `None`, zero and `False` can all be legitimate computed results.
The tail functions themselves are not memoized here; traversing the same tails again can
create different result nodes. For impure operations, memoization changes side effects,
so its role must be part of the specified behaviour rather than assumed harmless.

## Some transformations must inspect ahead

Repeating a finite stream and selecting every kth element concern **tail traversal**.
Remember the original start when repetition must restart; a restart should happen only
when the current finite traversal reaches `None`. For subsampling, emit the current head
and delay advancing k tails until the next result node is demanded. On an infinite input
there is no end to restart from. Specify empty-input behaviour separately.

Run-length encoding has a different demand: the count of a complete run requires finding
its end. An infinite stream containing only one value never finishes its first maximal
run. No implementation can both return its exact finite run length and remain productive.

A useful alternative contract caps each output chunk. This original encoder emits at most
`limit` equal values per chunk; consecutive chunks may therefore contain the same value.
It uses the **ordinary** stream representation, not the fully delayed one above.

```python title="§3"
def bounded_runs(s, limit):
    if not is_integer(limit) or limit <= 0:
        return error("chunk limit must be a positive integer")
    if is_none(s):
        return None
    value = head(s)
    def gather(cursor, count):
        if count == limit:
            return pair(count, lambda: stream_tail(cursor))
        rest = stream_tail(cursor)
        if is_none(rest) or head(rest) != value:
            return pair(count, lambda: rest)
        return gather(rest, count + 1)
    summary = gather(s, 1)
    return pair(pair(value, head(summary)),
                lambda: bounded_runs(tail(summary)(), limit))

def constant_stream(value):
    return pair(value, lambda: constant_stream(value))

finite = llist_to_stream(llist(5, 5, 1, 1, 1, 1, 5))
print_llist(eval_stream(bounded_runs(finite, 3), 4))
print_llist(eval_stream(bounded_runs(constant_stream(8), 3), 3))
```
```text title="Output"
llist([5, 2], [1, 3], [1, 1], [5, 1])
llist([8, 3], [8, 3], [8, 3])
```

At the cap, the next source tail is left inside a lambda. Before the cap, detecting a run
boundary can inspect the first head of the next run. Thus “returns a stream” does not mean
“does no input work until a tail is forced.” State separately the work needed to construct
a result head, to force a result tail, and to request the same result again.

## Takeaways

- A stream can be defined in terms of **itself** because the self-reference sits inside a lambda that
  runs later. Give the first element(s) by hand.
- `add_streams`, `mul_streams`, `scale_stream` combine streams element by element, lazily.
- `integers`, `fibs`, powers and factorials all have one-line implicit definitions.
- The sieve keeps the first number and filters its multiples out of the rest, forever.
- A stream of approximations replaces a loop: the consumer decides how far to go.
- Unmemoized tails rerun on every walk: implicit `fibs` does exponentially many additions.
- `memo_fun` makes each tail run at most once; it changes how often side effects happen.

## Check yourself

1. What are the first five elements of `odd = pair(1, lambda: add_streams(odd, twos))`, where
   `twos = pair(2, lambda: twos)`?

    ??? success "Answer"
        ```python title="§3"
        def add_streams(s1, s2):
            return (s2 if is_none(s1)
                    else s1 if is_none(s2)
                    else pair(head(s1) + head(s2), lambda: add_streams(stream_tail(s1), stream_tail(s2))))

        twos = pair(2, lambda: twos)
        odd = pair(1, lambda: add_streams(odd, twos))
        print_llist(eval_stream(odd, 5))
        ```
        ```text
        llist(1, 3, 5, 7, 9)
        ```
        Each element is the one before plus 2.

2. Describe the stream `count = pair(0, lambda: add_streams(ones, count))` without running it.

    ??? success "Answer"
        0, 1, 2, 3, …: the first element is 0, and every later element is 1 plus the one before it.

3. Define `squares`, the stream 1, 4, 9, 16, …, using `mul_streams` and `integers_from`.

    ??? success "Answer"
        ```python title="§3"
        def mul_streams(s1, s2):
            return (None if is_none(s1) or is_none(s2)
                    else pair(head(s1) * head(s2), lambda: mul_streams(stream_tail(s1), stream_tail(s2))))

        squares = mul_streams(integers_from(1), integers_from(1))
        print_llist(eval_stream(squares, 5))
        ```
        ```text
        llist(1, 4, 9, 16, 25)
        ```

4. What does this print?

    ```python title="§3"
    def shout(x):
        print("made", x)
        return x

    s = stream_map(shout, enum_stream(1, 3))
    stream_ref(s, 1)
    stream_ref(s, 1)
    ```

    ??? success "Answer"
        ```text
        made 1
        made 2
        made 2
        ```
        Making `s` computes the head (1). Each `stream_ref(s, 1)` forces the unmemoized tail again.

5. Why does `bad = pair(1, add_streams(ones, bad))` fail, while the version with `lambda:` works?

    ??? success "Answer"
        Without the lambda, `add_streams(ones, bad)` is evaluated **before** `bad` has a value, so reading
        `bad` is an error. With the lambda, it is evaluated only when the tail is forced, after the
        assignment.

*In the course: L11A · SICPy 3.5.2, 3.5.3.*
