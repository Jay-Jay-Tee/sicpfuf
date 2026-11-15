# Applied patterns: from a topic to an unfamiliar problem

<p class="chapter-goal">Combine the core chapters into the kinds of reasoning needed in studios, reflections and longer exam questions.</p>

These are original worked examples, not solutions copied from course sheets. Use the
[course map](course-map.md) to connect them to the material you are revising.

## A condition can force an argument

Normal order delays an argument until it is needed; it does not promise that the argument
will never run. Compare these two function bodies:

```python
def choose_left(a, b):
    return a

def inspect_then_choose(a, b):
    return 0 if b == 0 else a
```

For `choose_left(1, 1 // 0)`, applicative order fails while evaluating the second argument.
Normal order substitutes expressions and returns 1 without evaluating that division.
For `inspect_then_choose(1, 1 // 0)`, **both orders fail**: the predicate needs `b`.

Here is an explicit delay in the actual, applicative-order language:

```python title="§1"
def choose_left(a, delayed_b):
    return a

print(choose_left(1, lambda: 1 // 0))
```
```text title="Output"
1
```

The lambda is a value. Its body runs only when called. Keep this distinction separate from
memoization: a plain delayed function repeats its work every time it is called.

## Streams as coefficients of a power series

A stream can represent data other than a sequence to print. Interpret its elements as
coefficients `a0, a1, a2, ...` of `a0 + a1*x + a2*x*x + ...`. Taking the first `n` terms gives
a finite approximation even when the stream is infinite.

Horner's rule rewrites that prefix as `a0 + x*(a1 + x*(a2 + ...))`. The function below also
handles a finite stream: it stops when it reaches `None`.

```python title="§3"
def series_value(coefficients, x, n):
    if n == 0 or is_none(coefficients):
        return 0
    elif n == 1:
        return head(coefficients)
    else:
        return head(coefficients) + x * series_value(stream_tail(coefficients), x, n - 1)

print(series_value(integers_from(1), 2, 3))
print(series_value(stream(3, 4), 2, 10))
print(series_value(None, 2, 10))
```
```text title="Output"
17
11
0
```

The first call uses `1 + 2*2 + 3*2*2`. When n terms are available and each tail costs Θ(1), it takes Θ(n) time
and Θ(n) deferred-operation space. The `n == 1` case avoids forcing a tail we will not use.

## Removing nodes without allocating new pairs

A destructive filter reconnects existing nodes. It has two jobs: find the first survivor,
then splice rejected nodes out of the remaining chain. The returned head matters: a variable
that referred to a removed first node is not automatically rebound.

```python title="§3"
def keep_existing(keep, xs):
    while not is_none(xs) and not keep(head(xs)):
        xs = tail(xs)
    if is_none(xs):
        return None
    previous = xs
    current = tail(xs)
    while not is_none(current):
        if keep(head(current)):
            previous = current
        else:
            set_tail(previous, tail(current))
        current = tail(current)
    return xs

original = llist(1, 2, 3, 4, 5)
kept = keep_existing(lambda x: x % 2 == 0, original)
print_llist(kept)
print_llist(original)
print(kept is tail(original))
print(keep_existing(lambda x: False, llist(7, 9)))
```
```text title="Output"
llist(2, 4)
llist(1, 2, 4)
True
None
```

No call to `pair` or `llist` occurs inside `keep_existing`. It uses Θ(n) time and Θ(1)
auxiliary space when `keep` costs Θ(1). It mutates its argument; use it only when mutation
is permitted. Compare this with ordinary `filter`, which builds a new llist.

## Binary search can return a boundary

Searching is not limited to finding an equal value. In an ascending Python list, the first
index whose value is at least `target` is also the insertion position that puts a duplicate
before existing equal values. Maintain a half-open interval `[low, high)`.

```python title="§3"
def insertion_position(values, target):
    low = 0
    high = len(values)
    while low < high:
        middle = (low + high) // 2
        if values[middle] < target:
            low = middle + 1
        else:
            high = middle
    return low

print(insertion_position([2, 5, 5, 9], 5))
print(insertion_position([2, 5, 5, 9], 7))
print(insertion_position([2, 5, 5, 9], 20))
print(insertion_position([], 3))
```
```text title="Output"
1
3
4
0
```

Everything strictly before `low` is smaller than the target; everything at or after `high`
is at least the target. Each iteration shrinks the candidate interval, including when a match
is found. Finding the position takes Θ(log n) time and Θ(1) auxiliary space; physically
inserting into a contiguous list can still take Θ(n) time.

## A closure can hold a state machine

One private counter is not enough when behaviour also depends on whether a permanent state
has been reached. This access gate resets the failure count after a successful attempt,
but remains locked after three consecutive failures.

```python title="§3"
def make_gate(secret):
    failures = 0
    locked = False
    def attempt(candidate):
        nonlocal failures, locked
        if locked:
            return "locked"
        elif candidate == secret:
            failures = 0
            return "open"
        else:
            failures = failures + 1
            if failures == 3:
                locked = True
            return "locked" if locked else "denied"
    return attempt

gate = make_gate(42)
print(gate(0), gate(0), gate(42))
print(gate(0), gate(0), gate(0), gate(42))
another_gate = make_gate(42)
print(another_gate(42))
```
```text title="Output"
denied denied open
denied denied locked locked
open
```

Draw one maker frame per gate. Each returned function remembers its own frame. The state
is the pair of bindings `(failures, locked)`, and each call is a transition. This is the
same reasoning used for accounts, retry limits, accumulators and memoized functions.

## Fairly interleaving several streams

To give every stream a turn, keep a llist of active streams. Emit from its first stream,
then put that stream's tail at the back of the queue. Skip streams that have ended.

```python title="§3"
def round_robin(streams):
    if is_none(streams):
        return None
    first = head(streams)
    if is_none(first):
        return round_robin(tail(streams))
    return pair(head(first),
                lambda: round_robin(append(tail(streams), llist(stream_tail(first)))))

mixed = round_robin(llist(stream(1, 2), stream(10, 20, 30)))
print_llist(eval_stream(mixed, 10))
print_llist(eval_stream(round_robin(llist(integers_from(1), integers_from(100))), 6))
```
```text title="Output"
TypeError at line 11
    print_llist(eval_stream(mixed, 10))
TypeError: head(xs) expects a pair as argument xs, but encountered None
sicpfuf hint: you took the head or tail of None, the EMPTY linked list. The usual cause is a missing base case: check `is_none(xs)` before `head(xs)` / `tail(xs)`.
```

The delay encloses both forcing the old tail and producing the next output. With `k` active
streams, this simple queue costs O(k) llist work per emitted element because of `append`.
Fairness and constant-time queue operations are separate properties.

## Internal markers need identity

An evaluator that uses a string such as `"*unassigned*"` as a special marker can confuse a
legitimate user string with that marker. A private pair gives the marker its own identity.

```python title="§3"
unassigned_marker = pair(None, None)

def ready(value):
    return value is not unassigned_marker

print(ready("*unassigned*"))
print(ready(pair(None, None)))
print(ready(unassigned_marker))
```
```text title="Output"
True
True
False
```

Use `is`, not `==`, for this marker. In a complete evaluator, create it privately and make
lookup reject that exact value. Do not change the meaning of every user string that happens
to contain the marker's spelling. See [the evaluator chapters](17-mce.md) for the full model.

## Building all combinations instead of counting them

Tree recursion often starts by counting successful choices. To return the choices themselves,
let each branch return a llist of solutions. Taking an item prefixes it to every solution
of the smaller problem; skipping it leaves those solutions alone.

Assume each ticket price is positive and a ticket can be used at most once. Equal prices
at different positions represent different tickets.

```python title="§2"
def ticket_bundles(prices, budget):
    if budget == 0:
        return llist(None)
    elif budget < 0 or is_none(prices):
        return None
    else:
        with_first = map(lambda rest: pair(head(prices), rest),
                         ticket_bundles(tail(prices), budget - head(prices)))
        without_first = ticket_bundles(tail(prices), budget)
        return append(with_first, without_first)

answers = ticket_bundles(llist(2, 3, 5, 3), 5)
for_each(print_llist, answers)
print(length(answers))
```
```text title="Output"
llist(2, 3)
llist(2, 3)
llist(5)
3
```

`None` means no solutions. `llist(None)` means one solution, containing no tickets. Confusing
these two base cases destroys the construction. The two equal-looking bundles are different
choices of ticket positions. The number of answers can itself be exponential.

## A comparator describes an ordering

Abstract the ordering rule rather than writing a new sorting algorithm for every problem.
Here `before(a, b)` means that `a` is allowed to appear before `b`. Including equality in
that rule keeps the earlier item before an equal item in this recursive insertion sort.

```python title="§2"
def place_by(x, xs, before):
    if is_none(xs) or before(x, head(xs)):
        return pair(x, xs)
    else:
        return pair(head(xs), place_by(x, tail(xs), before))

def sort_by(xs, before):
    return None if is_none(xs) else place_by(head(xs), sort_by(tail(xs), before), before)

def evens_first(a, b):
    return a % 2 < b % 2 or (a % 2 == b % 2 and a <= b)

print_llist(sort_by(llist(5, 2, 7, 4, 1, 3), evens_first))
print_llist(sort_by(llist(3, 1, 4, 2), lambda a, b: a >= b))
```
```text title="Output"
llist(2, 4, 1, 3, 5, 7)
llist(4, 3, 2, 1)
```

Describe a compound order in priority order: first compare the group, then compare values
inside equal groups. Reversing the comparator and reversing the input are different operations.
The algorithm still has quadratic worst-case time; changing the comparator does not make it
a different sorting algorithm.

## A static pass visits branches that will not run

An evaluator chooses one branch of a conditional. A static name check must also inspect the
branch that evaluation would skip. This small checker handles literal, name, binary-operator
and conditional-expression nodes from `parse`; it returns a llist of undeclared occurrences.

```python title="§4"
def unknown_names(node, known):
    tag = head(node)
    if tag == "literal":
        return None
    elif tag == "name":
        symbol = head(tail(node))
        return llist(symbol) if is_none(member(symbol, known)) else None
    elif tag == "binary_operator_combination":
        return append(unknown_names(llist_ref(node, 2), known),
                      unknown_names(llist_ref(node, 3), known))
    elif tag == "conditional_expression":
        return append(unknown_names(llist_ref(node, 1), known),
                      append(unknown_names(llist_ref(node, 2), known),
                             unknown_names(llist_ref(node, 3), known)))
    else:
        return error("unsupported node", tag)

print_llist(unknown_names(parse("x + 1 if True else hidden"), llist("x")))
print_llist(unknown_names(parse("x + 1 if True else hidden"), llist("x", "hidden")))
```
```text title="Output"
llist('hidden')
llist()
```

This is an expression-only pass. To check statements, track which names assignments declare;
to detect reads before earlier assignments, also track assignment order. Function-local scope
and branch merging need their own rules. Do not confuse an undeclared name with a name whose
binding exists but is still unassigned.

## Count the resource the question defines

An exam can define a resource other than running time or peak memory: comparisons, pair
allocations, writes, or overwrites of existing numeric values. First identify exactly which
operation increases that resource.

```python title="§3"
def scaled_copy(xs):
    result = [None] * len(xs)
    for i in range(len(xs)):
        result[i] = 2 * xs[i]
    return result

def scale_in_place(xs):
    for i in range(len(xs)):
        xs[i] = 2 * xs[i]
    return xs

print(scaled_copy([3, 1, 4]))
print(scale_in_place([3, 1, 4]))
```
```text title="Output"
[6, 2, 8]
[6, 2, 8]
```

Both take Θ(n) time. If the resource counts **overwriting a numeric list entry with another
number**, the first performs zero counted operations: its destinations previously hold
`None`. The second performs n. Zero counted overwrites does not mean zero work, zero memory,
or that an arbitrary computation can be reversed without retaining information.

## How to practise these patterns

For each example: predict the output, draw the relevant model, run it, then change one
boundary case. Try empty input, one item, repeated values, independent closures, or a branch
whose unused expression would fail. A correct answer includes both the result and why the
evaluation rules produce it.
