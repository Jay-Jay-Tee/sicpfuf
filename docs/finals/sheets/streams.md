# Streams

<p class="chapter-goal">A stream is a llist that computes its rest only when asked. Know the shape, know what runs when, count the prints.</p>

## 1. The shape

A **stream** is either `None` (the empty stream) or a pair whose head is a value and whose tail is a **nullary function** (a function of no arguments) that returns a stream.

1. Build one with `pair(value, lambda: rest)`. The `lambda:` **delays** `rest`: nothing in it runs yet.
2. Take the rest with `stream_tail(s)`, which is `tail(s)()`: it calls the nullary function. That is **forcing**. The first element is plain `head(s)`.

```python title="§3"
s = pair("a", lambda: pair("b", lambda: None))
print(s)
print(head(stream_tail(s)))
print(stream_tail(stream_tail(s)))
```
```text title="Output"
['a', <function (anonymous)>]
b
None
```

## 2. The library (pre-declared from §3)

| Function | Gives | Lazy? |
|---|---|---|
| `stream(1, 2, 3)` | a finite stream | yes |
| `stream_tail(s)` | the rest (forces one tail) | forces once |
| `enum_stream(a, b)` | a, a+1, …, b (inclusive) | yes |
| `integers_from(n)` | n, n+1, n+2, … forever | yes |
| `stream_map(f, s)` | f of each element | `f` runs on the head **now**, the rest later |
| `stream_filter(p, s)` | elements that pass `p` | forces **until the first match** now |
| `stream_ref(s, n)` | element n (0-based) | forces n tails |
| `eval_stream(s, n)` | llist of the first n elements | forces n − 1 tails |
| `stream_to_llist(s)`, `stream_length(s)`, `stream_for_each(f, s)` | walk the WHOLE stream | never stop on an infinite stream |
| `llist_to_stream(xs)`, `build_stream(f, n)`, `stream_append(s, t)` | as for llists | yes |

**Not** pre-declared: `ones`, `integers`, `add_streams`, `scale_stream`, `mul_streams`, `memo_fun`. Write them yourself (section 4).

## 3. What runs when

The rules:

1. `pair(E1, lambda: E2)` evaluates `E1` now and `E2` only when that tail is forced, and **again every time** it is forced.
2. Only `stream_tail` forces (also inside `stream_ref`, `eval_stream`, `stream_filter` …).
3. `stream_map(f, s)` applies `f` to the head at once; element k is mapped when tail k of the *result* is forced.
4. `stream_filter(p, s)` forces tails of `s` right away until an element passes. To see it all, map a function that prints:

```python title="§3"
def loud(x):
    print("map", x)
    return x * 10

s = stream_map(loud, enum_stream(1, 5))
print("defined s")
print(stream_ref(s, 2))
print(stream_ref(s, 2))
```
```text title="Output"
map 1
defined s
map 2
map 3
30
map 2
map 3
30
```

`map 1` appears while defining `s` (rule 3). Each `stream_ref(s, 2)` forces two tails, and without memoization the second walk repeats the prints of 2 and 3 (rule 1).

## 4. Infinite and self-referential streams

A name may appear inside its own `lambda:`: by the time the tail is forced, the name has a value.

```python title="§3"
def add_streams(s1, s2):
    return (s2 if is_none(s1)
            else s1 if is_none(s2)
            else pair(head(s1) + head(s2),
                      lambda: add_streams(stream_tail(s1), stream_tail(s2))))

def mul_streams(s1, s2):
    return (None if is_none(s1) or is_none(s2)
            else pair(head(s1) * head(s2),
                      lambda: mul_streams(stream_tail(s1), stream_tail(s2))))

def scale_stream(c, s):
    return stream_map(lambda x: c * x, s)

ones = pair(1, lambda: ones)
integers = pair(1, lambda: add_streams(ones, integers))
powers_of_3 = pair(1, lambda: scale_stream(3, powers_of_3))
factorials = pair(1, lambda: mul_streams(factorials, stream_tail(integers)))
fibs = pair(0, lambda: pair(1, lambda: add_streams(stream_tail(fibs), fibs)))

print(eval_stream(integers, 5))
print(eval_stream(powers_of_3, 5))
print(eval_stream(factorials, 5))
print(eval_stream(fibs, 8))
```
```text title="Output"
[1, [2, [3, [4, [5, None]]]]]
[1, [3, [9, [27, [81, None]]]]]
[1, [2, [6, [24, [120, None]]]]]
[0, [1, [1, [2, [3, [5, [8, [13, None]]]]]]]]
```

How to read a self-referential definition: write the stream in a row, write what it is built from in rows under it, and fill in column by column.

| | 0 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|
| `fibs` | 0 | 1 | 1 | 2 | 3 |
| `stream_tail(fibs)` | 1 | 1 | 2 | 3 | 5 |
| their sum = `fibs` from index 2 | 1 | 2 | 3 | 5 | 8 |

**The sieve** keeps the head and removes its multiples from the rest (this is trial division, not the real sieve of Eratosthenes):

```python title="§3"
def sieve(s):
    return pair(head(s),
                lambda: sieve(stream_filter(lambda x: x % head(s) != 0,
                                            stream_tail(s))))

primes = sieve(integers_from(2))
print(eval_stream(primes, 8))
print(stream_ref(stream_filter(lambda p: p % 10 == 3, primes), 3))
```
```text title="Output"
[2, [3, [5, [7, [11, [13, [17, [19, None]]]]]]]]
43
```

## 5. Memoization with `memo_fun`

`memo_fun(f)` returns a nullary function that runs `f` the first time and then hands back the stored result.

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
    return (None if is_none(s)
            else pair(f(head(s)), memo_fun(lambda: m_stream_map(f, stream_tail(s)))))

def loud(x):
    print("map", x)
    return x * 10

s = m_stream_map(loud, enum_stream(1, 5))
print(stream_ref(s, 2))
print(stream_ref(s, 3))

plain_adds = 0
memo_adds = 0
def add_plain(s1, s2):
    global plain_adds
    plain_adds = plain_adds + 1
    return pair(head(s1) + head(s2), lambda: add_plain(stream_tail(s1), stream_tail(s2)))
def add_memo(s1, s2):
    global memo_adds
    memo_adds = memo_adds + 1
    return pair(head(s1) + head(s2), memo_fun(lambda: add_memo(stream_tail(s1), stream_tail(s2))))

fibs = pair(0, lambda: pair(1, lambda: add_plain(stream_tail(fibs), fibs)))
m_fibs = pair(0, memo_fun(lambda: pair(1, memo_fun(lambda: add_memo(stream_tail(m_fibs), m_fibs)))))
print(stream_ref(fibs, 15), plain_adds)
print(stream_ref(m_fibs, 15), memo_adds)
```
```text title="Output"
map 1
map 2
map 3
30
map 4
40
610 2567
610 14
```

The first walk maps 1, 2, 3; the second walk prints only the NEW element 4: each tail runs at most once. The two counters show the cost. Without memoization every `stream_tail(fibs)` inside `add_plain` rebuilds `fibs` from the start, so the work grows exponentially. With it, element n costs one new addition.

**Why not memoize everything?** For pure functions memoization changes only the speed. When forcing has a **side effect** (a print, a reassignment), it changes how often the effect happens. Questions test exactly that.

## 6. How to answer stream questions in the exam

**"Write a stream function"**

1. Base case: `None` if the input stream is empty (skip it for streams that are known to be infinite).
2. Return `pair(head part, lambda: recursive call on stream_tail(...))`.
3. Never call `stream_tail` outside the `lambda:` unless you really need the next element now.
4. Test on a finite stream AND on `integers_from(1)` with `eval_stream(…, 5)`.

**"What is printed / how many times is f applied?"**

1. Write the stream as a row of boxes; mark which heads already exist.
2. For each statement, count the tails it forces (`stream_ref(s, n)`: n; `eval_stream(s, n)`: n − 1; `stream_filter`: until the first match).
3. Without memo: every walk starts at the stream's start and reruns every tail it passes. With memo: only tails never forced before run.
4. `stream_map` maps the head immediately: one print at definition time.

## 7. Traps

1. **Forcing too early.** `pair(x, stream_tail(s))` forces now and its tail is not a function. Write `pair(x, lambda: stream_tail(s))`.
2. **The head of `stream_map` runs at once.** `stream_map(print, s)` prints the first element on the spot.
3. **Walking an infinite stream.** `stream_length`, `stream_to_llist`, `stream_for_each` never return on `integers_from(1)`. Use `eval_stream(s, n)`.
4. **A filter with no match** never returns: `stream_filter(lambda x: x < 0, integers_from(1))`.
5. **The library is not memoized.** Only tails you wrap in `memo_fun` are. `stream_map` and `stream_filter` rerun every time.
6. **`ones = pair(1, ones)`** without the `lambda:` is a NameError: `ones` has no value yet when the pair is built.

*In the course: L7B, L11A · SICPy 3.5.1–3.5.2.*
