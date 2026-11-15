# 5. Higher-order functions and scope

<p class="chapter-goal">Use local names and conditional statements, pass functions around like numbers, and know which declaration every name refers to.</p>

!!! abstract "The big idea, in plain words"
    A recipe card that says "add 2 spoons of sugar" is useful. A card that says "add 2 spoons of *the
    sweetener of your choice*" is more useful, because one card now covers many dishes. Passing a
    **function** as an argument does the same for programs: one definition, many uses. And when two
    people in the same house are both called Alex, "Alex" means the one in *this* room first. Names in
    programs work the same way: a name means the **closest surrounding declaration**.

## Local names and conditional statements

A function body can be more than one return statement. **Nested declaration assignments** give names
to intermediate values inside the function:

```python title="§1"
def trip_cost(km, people):
    fuel = km * 0.15
    toll = 4 if km > 100 else 0
    total = fuel + toll
    return total / people

print(trip_cost(200, 4))
```
```text title="Output"
8.5
```

`fuel`, `toll` and `total` are **local** to `trip_cost`: outside its body they do not exist.

A **conditional statement** chooses between whole blocks of statements. Each branch can have its own
local names and its own `return`. `elif` is short for "else, if":

```python title="§1"
def grade(score):
    if score >= 80:
        return "A"
    elif score >= 65:
        bonus = 5
        return "B" if score + bonus >= 75 else "C"
    else:
        return "D"

print(grade(90), grade(72), grade(66), grade(10))
```
```text title="Output"
A B C D
```

A `return` ends the function at once. If a run of the function reaches its end without any
`return`, the function returns `None`.

!!! warning "Trap: a local name computed too early"
    A declaration assignment runs *every time* the body runs, even when the answer does not need it.
    Here the recursive application happens before the base case is checked, so it never stops:

    ```python title="§1"
    def halvings(n):
        rest = halvings(n // 2)
        return 0 if n <= 1 else 1 + rest

    print(halvings(8))
    ```
    ```text
    RecursionError: maximum recursion depth exceeded
    ```

    Fix: compute `rest` only in the branch that needs it.

    ```python title="§1"
    def halvings(n):
        if n <= 1:
            return 0
        else:
            rest = halvings(n // 2)
            return 1 + rest

    print(halvings(8), halvings(1000))
    ```
    ```text
    3 9
    ```

## Solving a problem in 5 steps

The course recommends the same five steps for every problem. Here they are on a fresh one.

**The problem.** The post office sells stamps of 2, 5 and 10 cents, as many as you like. In how many
ways can you pay exactly `amount` cents? The order of the stamps does not matter.

1. **Read the problem carefully.** Order does not matter, so 5 + 2 + 2 + 2 and 2 + 5 + 2 + 2 are the
   same way. Every stamp kind can be used any number of times.
2. **Play with examples.** 10 cents: one 10; two 5s; five 2s. So 3 ways. 4 cents: only 2 + 2. 3 cents:
   no way.
3. **Think.** Split all ways into two groups: those that use **at least one** of the biggest stamp,
   and those that use **none** of it. The first group is "pay `amount - 10` with all kinds"; the
   second is "pay `amount` with the smaller kinds only". Wishful thinking does the rest. Base cases:
   amount 0 has exactly 1 way (no stamps); a negative amount, or no kinds left, has 0.
4. **Program.**

    ```python title="§1"
    def stamp_value(kinds):
        return 2 if kinds == 1 else 5 if kinds == 2 else 10

    def ways(amount, kinds):
        if amount == 0:
            return 1
        elif amount < 0:
            return 0
        elif kinds == 0:
            return 0
        else:
            return ways(amount - stamp_value(kinds), kinds) + ways(amount, kinds - 1)

    print(ways(10, 3), ways(4, 3), ways(3, 3), ways(100, 3))
    ```
    ```text title="Output"
    3 1 0 66
    ```

5. **Test.** The small answers match step 2. Also try edge cases: `ways(0, 3)` should be 1.

`ways` applies itself twice: tree recursion, like `fib`. The time grows very fast with the amount,
and the space grows linearly (the deepest path keeps taking off the smallest stamp).

??? example "X-ray: measuring `ways`"
    ```python title="§1"
    def stamp_value(kinds):
        return 2 if kinds == 1 else 5 if kinds == 2 else 10

    def ways(amount, kinds):
        if amount == 0:
            return 1
        elif amount < 0:
            return 0
        elif kinds == 0:
            return 0
        else:
            return ways(amount - stamp_value(kinds), kinds) + ways(amount, kinds - 1)

    measure(ways, 50, 3)
    measure(ways, 100, 3)
    measure(ways, 200, 3)
    ```
    ```text title="Output"
    [measure] ways(50, 3): 1,066 calls, 16,966 steps, at most 28 waiting at once
    [measure] ways(100, 3): 6,631 calls, 105,826 steps, at most 53 waiting at once
    [measure] ways(200, 3): 46,261 calls, 739,246 steps, at most 103 waiting at once
    ```
    Doubling the amount multiplies the calls by 6 to 7, and roughly doubles the waiting calls.

## Functions as arguments

A **higher-order function** takes a function as an argument or returns one. Look at two sums:

- 1² + 2² + … + 10²
- 1/1² + 1/2² + … + 1/1000²

Only two things change: the **term** to add, and how to get to the **next** value. Make them
parameters:

```python title="§1"
def sum(term, a, next, b):
    return 0 if a > b else term(a) + sum(term, next(a), next, b)

def square(x):
    return x * x

def inverse_square(x):
    return 1 / (x * x)

def plus_one(x):
    return x + 1

print(sum(square, 1, plus_one, 10))
print(sum(inverse_square, 1, plus_one, 1000))
```
```text title="Output"
385
1.6439345666815597
```

`square` is passed **without** parentheses: you pass the function itself. Inside `sum`, `term(a)`
applies it. (The second sum creeps up on π²/6 ≈ 1.6449.)

Helpers that are only needed in one place can be hidden inside the function that uses them:

```python title="§1"
def sum(term, a, next, b):
    return 0 if a > b else term(a) + sum(term, next(a), next, b)

def sum_of_odd_cubes(n):
    def cube(x):
        return x * x * x
    def plus_two(x):
        return x + 2
    return sum(cube, 1, plus_two, n)

print(sum_of_odd_cubes(5))
```
```text title="Output"
153
```

## Lambda expressions

Naming every tiny helper is tiresome. A **lambda expression** `lambda parameters: expression` makes a
function without a name. Its body is one expression, and there is no `return`:

```python title="§1"
def sum(term, a, next, b):
    return 0 if a > b else term(a) + sum(term, next(a), next, b)

print(sum(lambda k: k * k, 1, lambda k: k + 1, 10))
print((lambda x, y: x * 10 + y)(4, 2))
print(lambda x: x)
```
```text title="Output"
385
42
<function (anonymous)>
```

`name = lambda x: ...` and `def name(x): return ...` make the same kind of function. Note the
parentheses in `(lambda x, y: ...)(4, 2)`: without them, the `(4, 2)` would become part of the body.

## Functions as results

A function can also **return** a function. A "maker" takes some settings and returns a function that
remembers them:

```python title="§1"
def make_discount(percent):
    return lambda price: price - price * percent / 100

half_off = make_discount(50)
tenth_off = make_discount(10)
print(half_off(80), tenth_off(80))
print(make_discount(25)(40))
```
```text title="Output"
40.0 72.0
30.0
```

`half_off` and `tenth_off` are two independent functions; each remembers its own `percent`.
`make_discount(25)(40)` applies the maker and immediately applies the result. A classic maker is
`compose(f, g)`, which returns `lambda x: f(g(x))`.

## Scope

Every name occurrence refers to a **declaration**. There are four ways to declare a name:

1. pre-declared names (such as `math_pi`) and names imported from a module;
2. declaration assignments `x = ...`;
3. parameters of a function definition or lambda expression;
4. the function name of a function definition (`def f` declares `f`).

The rule: **a name refers to the closest surrounding declaration.** The **scope** of a declaration
inside a function is that function's whole body; at top level, it is the whole program. This is
called **lexical scoping**: you can find the declaration by reading the program text, from the
inside out.

```python title="§1"
rate = 3

def charge(hours):
    rate = 5
    return hours * rate

def charge_with_tax(hours, rate):
    def with_tax(x):
        return x + x * rate / 100
    return with_tax(hours * 10)

print(charge(2), rate, charge_with_tax(2, 10))
```
```text title="Output"
10 3 22.0
```

- In `charge`, `rate` means the local `rate = 5`. The global `rate` is untouched: it is still 3.
- In `with_tax`, `rate` is not declared, so look one level out: it is the parameter `rate` of
  `charge_with_tax`, which is 10.

!!! warning "Trap: a local name used before its assignment"
    If a function assigns a name **anywhere** in its body, that name is local in the **whole** body.
    Using it before the assignment has run is an error. It does **not** fall back to the global name:

    ```python title="§1"
    price = 10

    def with_fee(n):
        total = n * price
        price = 12
        return total

    print(with_fee(3))
    ```
    ```text title="Output"
    UnassignedLocalError at line 4
        total = n * price
    UnassignedLocalError: cannot access local variable 'price' where it is not associated with a value
      in with_fee, called from line 8: print(with_fee(3))
    sicpfuf hint: the function assigns to this name somewhere in its body, so the name lives in the function's own frame for the WHOLE body, even on lines before the assignment. To change a name of an enclosing function use `nonlocal`, and for a global name use `global` (Python §3 and §4).
    ```

!!! warning "Trap: a name assigned in only one branch"
    A declaration inside one branch of an `if` still makes the name local to the whole body. If that
    branch does not run, the name is in scope but has no value:

    ```python title="§1"
    def describe(n):
        if n > 0:
            label = "positive"
        return label

    print(describe(5))
    print(describe(-5))
    ```
    ```text
    positive
    UnassignedLocalError: cannot access local variable 'label' where it is not associated with a value
    ```

!!! note "Python §1 vs real Python"
    In real Python, `sum` is a built-in function, and defining your own `sum` hides it. In Python §1
    `sum` is not pre-declared, so the course's `sum(term, a, next, b)` is a fresh name. Real Python
    calls the local-name error `UnboundLocalError`; sicpfuf calls it `UnassignedLocalError`.

## Takeaways

- Nested declaration assignments name intermediate values; they are local to the function body.
- A conditional statement (`if`/`elif`/`else`) chooses between blocks; put a `return` in every branch.
- A declaration placed before the base case check runs every time: compute it inside the branch.
- **5 steps**: read, play with examples, think (wishful thinking, split into cases), program, test.
- **Higher-order functions** take functions as arguments (`sum(term, a, next, b)`) or return them
  (`make_discount`).
- A **lambda expression** is a function without a name; its body is one expression.
- A name refers to its **closest surrounding declaration** (lexical scoping). A name assigned in a
  function is local to the whole body.

## Check yourself

1. What does this print? Link each `x` to its declaration.

    ```python title="§1"
    x = 1

    def f(x):
        return lambda y: x + y

    def g(y):
        return f(10)(y) + x

    print(g(100))
    ```

    ??? success "Answer"
        ```text
        111
        ```
        Inside the lambda, `x` is the parameter of `f` (10) and `y` is the lambda's parameter (100).
        In `g`, `x` is the global `x` (1). So 10 + 100 + 1.

2. Write `product(term, a, next, b)` like `sum`, and use it to compute 5!.

    ??? success "Answer"
        ```python title="§1"
        def product(term, a, next, b):
            return 1 if a > b else term(a) * product(term, next(a), next, b)

        print(product(lambda k: k, 1, lambda k: k + 1, 5))
        ```
        ```text
        120
        ```
        The base case is 1, not 0: 1 is the "empty product".

3. What is `(lambda f: f(f(2)))(lambda x: x * x)`?

    ??? success "Answer"
        ```python title="§1"
        print((lambda f: f(f(2)))(lambda x: x * x))
        ```
        ```text
        16
        ```
        `f` is the squaring function, so `f(f(2))` is `(2²)²`.

4. Write `make_repeater(f, n)` that returns a function applying `f` n times to its argument.

    ??? success "Answer"
        ```python title="§1"
        def make_repeater(f, n):
            return (lambda x: x) if n == 0 else lambda x: f(make_repeater(f, n - 1)(x))

        add_seven_three_times = make_repeater(lambda x: x + 7, 3)
        print(add_seven_three_times(0))
        ```
        ```text
        21
        ```

5. In how many ways can you pay 30 cents with the 2, 5 and 10 cent stamps? Predict, then check.

    ??? success "Answer"
        ```python title="§1"
        def stamp_value(kinds):
            return 2 if kinds == 1 else 5 if kinds == 2 else 10

        def ways(amount, kinds):
            if amount == 0:
                return 1
            elif amount < 0:
                return 0
            elif kinds == 0:
                return 0
            else:
                return ways(amount - stamp_value(kinds), kinds) + ways(amount, kinds - 1)

        print(ways(30, 3))
        ```
        ```text
        10
        ```

6. Why does this fail when it runs, and how do you fix it?

    ```python title="§1"
    level = 1

    def next_level(n):
        level = level + n
        return level

    print(next_level(2))
    ```

    ??? success "Answer"
        ```text
        UnassignedLocalError: cannot access local variable 'level' where it is not associated with a value
        ```
        `level` is assigned in the body, so it is local in the whole body, and the right-hand side
        reads it before it has a value. Use a different local name: `new_level = level + n`.

*In the course: L3A · SICPy 1.1.8, 1.2.2, 1.3.1–1.3.2.*
