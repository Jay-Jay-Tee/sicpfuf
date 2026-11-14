# Substitution model & processes

<p class="chapter-goal">One page: evaluate §1/§2 programs by hand, lay out a trace, and say whether the process is recursive or iterative.</p>

## The rules (applicative order)

The substitution model explains every program WITHOUT reassignment or mutation (Python §1 and §2).
Python uses **applicative order reduction**: arguments first, then the body.

1. **Primitive expression** (numeral, string, `True`, a primitive name): take its value.
2. **Operator combination**: evaluate the operands, left to right, then apply the operator.
3. **Declaration assignment** `x = e`: evaluate `e`, then replace `x` by that value in the rest of the program.
4. **Conditional expression** `c if p else a`: evaluate `p` FIRST. If `True`, the whole thing becomes `c`, else `a`. The other branch is never evaluated.
5. **Function application** `f(e1, e2)`: evaluate `f` and the arguments. Primitive `f`: apply it. Compound `f`: replace the application by the **return expression** of the body, with every parameter replaced by its argument value.
6. `a and b` is `b if a else False`; `a or b` is `True if a else b`. So the right operand may never run.

Micro-example of rules 2 and 5. Watch the arguments become values BEFORE `sq` is opened up:

```python title="§1 · --subst"
def sq(x):
    return x * x

def area_sum(a):
    return sq(a + 1) + sq(a * 2)

area_sum(3)
```
```text title="Output"
area_sum(3)
-> sq(3 + 1) + sq(3 * 2)
-> sq(4) + sq(3 * 2)
-> 4 * 4 + sq(3 * 2)
-> 16 + sq(3 * 2)
-> 16 + sq(6)
-> 16 + 6 * 6
-> 16 + 36
-> 52
```

## How to lay out a trace in the exam

1. Write the starting expression on the first line.
2. One rewrite per line, each line prefixed by `->`. Rewrite ONE eligible subexpression: the leftmost one whose operands are already values.
3. Copy the rest of the line unchanged. Keep the brackets of operations that are still waiting.
4. Stop at a single value. Examiners mostly care that the *shape* is right; skipping trivial lines (like `3 - 1` to `2`) is usually fine if the question does not forbid it.

## Recursive or iterative?

A **deferred operation** is an operation that must wait for a recursive call to come back before it can run.

- **Recursive process**: deferred operations pile up. The trace grows wide, then shrinks.
- **Iterative process**: no deferred operations. Every line has the same width: the state lives in the arguments.

A *function* is recursive when it calls itself. A *process* is recursive or iterative. A recursive function can give an iterative process.

The test: look at the recursive call. If something is done with its result (`n * f(...)`, `pair(x, f(...))`, `1 + f(...)`), that something is deferred. If the call's result is returned as it is (`return f(...)`), nothing is deferred.

```python title="§1 · --subst"
def power(b, e):
    return 1 if e == 0 else b * power(b, e - 1)

power(2, 3)
```
```text title="Output"
power(2, 3)
-> 1 if 3 == 0 else 2 * power(2, 3 - 1)
-> 1 if False else 2 * power(2, 3 - 1)
-> 2 * power(2, 3 - 1)
-> 2 * power(2, 2)
-> 2 * (1 if 2 == 0 else 2 * power(2, 2 - 1))
-> 2 * (1 if False else 2 * power(2, 2 - 1))
-> 2 * (2 * power(2, 2 - 1))
-> 2 * (2 * power(2, 1))
-> 2 * (2 * (1 if 1 == 0 else 2 * power(2, 1 - 1)))
-> 2 * (2 * (1 if False else 2 * power(2, 1 - 1)))
-> 2 * (2 * (2 * power(2, 1 - 1)))
-> 2 * (2 * (2 * power(2, 0)))
-> 2 * (2 * (2 * (1 if 0 == 0 else 2 * power(2, 0 - 1))))
-> 2 * (2 * (2 * (1 if True else 2 * power(2, 0 - 1))))
-> 2 * (2 * (2 * 1))
-> 2 * (2 * 2)
-> 2 * 4
-> 8
```

The `2 * (2 * (...))` growing to the right is the pile of deferred multiplications. Now the same answer with an accumulator:

```python title="§1 · --subst"
def power_iter(b, e, acc):
    return acc if e == 0 else power_iter(b, e - 1, acc * b)

power_iter(2, 3, 1)
```
```text title="Output"
power_iter(2, 3, 1)
-> 1 if 3 == 0 else power_iter(2, 3 - 1, 1 * 2)
-> 1 if False else power_iter(2, 3 - 1, 1 * 2)
-> power_iter(2, 3 - 1, 1 * 2)
-> power_iter(2, 2, 1 * 2)
-> power_iter(2, 2, 2)
-> 2 if 2 == 0 else power_iter(2, 2 - 1, 2 * 2)
-> 2 if False else power_iter(2, 2 - 1, 2 * 2)
-> power_iter(2, 2 - 1, 2 * 2)
-> power_iter(2, 1, 2 * 2)
-> power_iter(2, 1, 4)
-> 4 if 1 == 0 else power_iter(2, 1 - 1, 4 * 2)
-> 4 if False else power_iter(2, 1 - 1, 4 * 2)
-> power_iter(2, 1 - 1, 4 * 2)
-> power_iter(2, 0, 4 * 2)
-> power_iter(2, 0, 8)
-> 8 if 0 == 0 else power_iter(2, 0 - 1, 8 * 2)
-> 8 if True else power_iter(2, 0 - 1, 8 * 2)
-> 8
```

Every line has the same shape. Iterative process.

!!! tip "Turning a recursive process into an iterative one"
    Add a parameter (the **accumulator**) that holds "the answer so far". Do the work on the accumulator BEFORE the recursive call, and return the accumulator in the base case. Check the order: building a llist with an accumulator reverses it.

## Time and space from a trace

- **Time** = number of steps (lines of the trace). `power(b, e)`: Θ(e).
- **Space** = the most deferred operations waiting at once (the widest line). `power`: Θ(e). `power_iter`: Θ(1).

## Normal order vs applicative order

**Normal order reduction** substitutes the argument EXPRESSIONS unevaluated, and evaluates them only when a primitive operator needs their value. Python does NOT do this, but exam questions ask you to compare.

Both orders give the same value when both finish. They differ when an argument is never needed and its evaluation fails or never ends:

```python title="§1"
def pick_first(a, b):
    return a

print(pick_first(5, 1 // 0))
```
```text
ZeroDivisionError: division by zero
```

In applicative order `1 // 0` runs before `pick_first` is opened, so it crashes. In normal order the trace would be:

```python
pick_first(5, 1 // 0)
-> 5          # b is never used, so 1 // 0 is never evaluated
```

Normal order can also do MORE work: in `sq(2 + 3)` it gives `(2 + 3) * (2 + 3)` and evaluates `2 + 3` twice.

| | applicative order | normal order |
|---|---|---|
| arguments evaluated | once, before the body | each time a primitive needs them |
| unused argument that crashes | crash | fine |
| used by | Python, in every chapter | the lazy evaluator of §4 (with memoized thunks) |

## The tools

- `--subst` prints the trace for any §1/§2 program, exactly as above. Add `--max-steps 40` for long ones.
- `trace(f, args...)` draws the call tree. A `→` line is a call the caller waits for (deferred work); `↻` is a tail call that replaces the caller (iterative).

```python title="§1"
def power(b, e):
    return 1 if e == 0 else b * power(b, e - 1)

def power_iter(b, e, acc):
    return acc if e == 0 else power_iter(b, e - 1, acc * b)

trace(power, 2, 2)
trace(power_iter, 2, 2, 1)
```
```text title="Output"
→ power(2, 2)
│  → power(2, 1)
│  │  → power(2, 0)
│  │  ← 1
│  ← 2
← 4
→ power_iter(2, 2, 1)
↻ power_iter(2, 1, 2)
↻ power_iter(2, 0, 4)
← 4
```

## How to answer this in the exam

1. **"Trace `f(3)`"**: rules 1 to 6, one rewrite per line, `->` in front. Do not open a function before its arguments are values.
2. **"Recursive or iterative process?"**: point at the recursive call and say what is (or is not) waiting for its result. Name the deferred operation.
3. **"Rewrite to give an iterative process"**: add an accumulator; the recursive call must be the whole return expression.
4. **"Normal vs applicative"**: find an argument that is unused (or used twice). Say which order evaluates it and how often.

## Top traps

- Calling `return f(n - 1) + 0` a tail call. It is not: the `+ 0` is deferred.
- Saying "recursive function, so recursive process". Look for deferred operations instead.
- Evaluating both branches of a conditional expression. Only the predicate, then ONE branch.
- Forgetting that `and`/`or` may skip their right operand.
- Using the substitution model after reassignment (§3): it breaks. Use the [environment model](environment-model.md).

*In the course: L2A, L1B, L3B · SICPy 1.1.3, 1.1.5, 1.2.1.*
