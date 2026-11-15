# Topic checklist

<p class="chapter-goal">Every examinable skill as an "I can ..." line, in course order. Tick it only when you can do it on paper, without notes.</p>

How to use it: go through one unit per revision session. For each line, do the self-test in brackets on paper, then check it with sicpfuf. Tick the line only if you got it right without looking anything up. Every unticked line is tomorrow's work: open the linked sheet, then the [drills](../practice/index.md).

Lines marked ★ are the skills the course comes back to most often (mastery-check topics, studios and reflections). If time runs out, do those first.

## Unit 1: Functions (§1)

### L1A Elements of programming

- [ ] I can evaluate an operator combination by hand, respecting precedence. [(sheet)](sheets/substitution.md) (Self-test: `2 + 3 * 4 ** 2 // 5`.)
- [ ] I can say what `/`, `//`, `%` and `**` give, including for negative numbers. [(sheet)](sheets/traps.md) (Self-test: `-7 // 2`, `-7 % 2`, `6 / 3`.)
- [ ] I can use the course words: primitive expression, operator combination, declaration assignment, function definition, function application, compound function, predicate. [(sheet)](sheets/substitution.md)
- [ ] I can write a function definition with a return statement and a conditional expression. (Self-test: `abs_diff(a, b)` without `abs`.)
- [ ] I can explain why a bare expression statement prints nothing, and that only `print` prints. [(sheet)](sheets/traps.md)

### L1B Runes and functional abstraction

- [ ] I can build a picture from `stack`, `beside` and `quarter_turn_right`, and define `beside` from `stack` and rotations. (Self-test: draw what `beside(heart, stack(heart, heart))` looks like.)
- [ ] I can write a rune transformation as a function from rune to rune, and use `repeat_apply`.
- [ ] I can explain "a function as a black box": what it does, not how.

### L2A Substitution model and recursion

- [ ] ★ I can trace a program with the substitution model in applicative order, one rewrite per line. [(sheet)](sheets/substitution.md) (Self-test: trace `power(2, 3)` from the sheet without looking.)
- [ ] I can explain applicative vs normal order and give a program where they differ. [(sheet)](sheets/substitution.md)
- [ ] I can design a recursive function by wishful thinking: base case first, then "assume n − 1 is solved".
- [ ] ★ I can spot deferred operations and say whether a process is recursive or iterative. [(sheet)](sheets/substitution.md) (Self-test: is `return f(n - 1) + 0` a tail call?)
- [ ] ★ I can rewrite a recursive process as an iterative one with an accumulator. [(sheet)](sheets/substitution.md) (Self-test: iterative `sum_digits(n)`.)
- [ ] I can tell a recursive *function* from a recursive *process*. [(sheet)](sheets/substitution.md)

### L2B Orders of growth

- [ ] I can draw the call tree of a tree recursion such as `fib(5)` and count its nodes. [(sheet)](sheets/growth.md)
- [ ] I can write iterative `fib` with two running values.
- [ ] I can define Θ, O and Ω in plain words and say why constants and lower-order terms do not matter. [(sheet)](sheets/growth.md)
- [ ] ★ I can state time and space in Θ for recursive and iterative factorial and fib, with a reason. [(sheet)](sheets/growth.md) (Self-test: space of tree-recursive `fib(n)`?)
- [ ] I can recognise Θ(log n) from halving and Θ(2ⁿ) from two calls on n − 1. [(sheet)](sheets/growth.md) (Self-test: fast power by squaring.)
- [ ] I can give the tightest bound and know that O(2ⁿ) for fib is correct but loose. [(sheet)](sheets/growth.md)

### L3A Higher-order functions and scope

- [ ] I can use nested declaration assignments and nested function definitions to hide helpers.
- [ ] I can write a conditional statement with `if`/`elif`/`else` where each branch returns. [(sheet)](sheets/traps.md)
- [ ] I can solve a "use it or skip it" counting problem (count change, number of ways) by tree recursion.
- [ ] I can follow the 5-step method: read, play with examples, think, program, test.
- [ ] ★ I can pass functions as arguments and abstract a pattern into a higher-order function such as a general sum. [(sheet)](sheets/scope-hof.md)
- [ ] ★ I can write a lambda expression and know it has one return expression and no statements. [(sheet)](sheets/scope-hof.md)
- [ ] ★ I can return a function from a function (`make_adder`) and apply the result at once (`make_adder(4)(6)`). [(sheet)](sheets/scope-hof.md)
- [ ] ★ I can link every name occurrence to its declaration using "the closest surrounding declaration". [(sheet)](sheets/scope-hof.md) (Self-test: the `k` example on the sheet.)
- [ ] I can list the four forms of declaration. [(sheet)](sheets/scope-hof.md)
- [ ] I can explain "in scope but unassigned" and predict the error for a local read before its assignment. [(sheet)](sheets/traps.md)
- [ ] I can explain why a program with an undeclared name is rejected before it runs. [(sheet)](sheets/traps.md)

### L3B Curves, sound and logical operators

- [ ] I can rewrite `a and b` and `a or b` as conditional expressions and say when the right operand is skipped. [(sheet)](sheets/substitution.md) (Self-test: `False and 1 // 0`.)
- [ ] I can write a curve as a function from t in [0, 1] to a point, and a curve maker that returns a curve (currying). [(sheet)](sheets/scope-hof.md)
- [ ] I can write a curve transformation and use `compose(f, g)` (g first). [(sheet)](sheets/scope-hof.md) (Self-test: `compose(inc, double)(5)`.)
- [ ] I can write a sound wave as a function from time to amplitude.

## Unit 2: Data (§2)

### L4A Data abstraction, pairs and llists

- [ ] I can write constructors, selectors and predicates for a data type (rationals, points) and respect the abstraction barrier.
- [ ] I can reduce a rational to lowest terms with `gcd` and `//`.
- [ ] I can build pairs from functions only (functional pairs) and explain why that still counts as data.
- [ ] ★ I can say whether a value is a llist, and turn between box notation, llist notation and `pair` calls. [(sheet)](sheets/llists.md) (Self-test: box notation of `llist(1, pair(2, 3))`.)
- [ ] ★ I can draw a box-and-pointer diagram, with shared pairs drawn once. [(sheet)](sheets/llists.md)
- [ ] ★ I can write the `head`/`tail` access path to any element. [(sheet)](sheets/llists.md) (Self-test: reach 3 in `llist(1, llist(2, 3), 4)`.)
- [ ] I can write `length` recursively and iteratively over a llist.

### L5A Llist processing

- [ ] I can apply the lambda precedence rule (application > conditional expression > lambda). [(sheet)](sheets/scope-hof.md)
- [ ] I can write `append` and say which pairs are new and which are shared. [(sheet)](sheets/llists.md)
- [ ] ★ I can count space as deferred operations plus pairs that must be remembered. [(sheet)](sheets/growth.md)
- [ ] ★ I can write `reverse` three ways and give the order of growth of each. [(sheet)](sheets/growth.md)
- [ ] ★ I can solve llist problems with `map`, `filter` and `reduce`, often as one line. [(sheet)](sheets/llists.md) (Self-test: sum of squares of the odd elements.)
- [ ] ★ I can evaluate `reduce` as a right fold with the operator's arguments (element, rest). [(sheet)](sheets/llists.md) (Self-test: `reduce(lambda x, r: x - r, 0, llist(1, 2, 3))`.)
- [ ] I can use the whole §2 library with the right argument order and return values. [(sheet)](sheets/llists.md)

### L5B Trees and CPS

- [ ] I can say what a tree of numbers is, and why `None` in a tree is an empty subtree. [(sheet)](sheets/trees-cps.md)
- [ ] I can write tree recursion with the three cases in the right order. [(sheet)](sheets/trees-cps.md) (Self-test: `count_leaves`.)
- [ ] I can write `map_tree`, `scale_tree`, `flatten` and an accumulate over trees. [(sheet)](sheets/trees-cps.md)
- [ ] ★ I can convert a recursive function to continuation-passing style. [(sheet)](sheets/trees-cps.md) (Self-test: CPS `length`.)
- [ ] ★ I can explain why CPS gives an iterative process but still Θ(n) space. [(sheet)](sheets/trees-cps.md)
- [ ] I can say in which order the continuations run. [(sheet)](sheets/trees-cps.md)

### L6A Sorting and symbolic processing

- [ ] I can explain binary search by halving and why it needs a total order and Θ(1) access to the middle. [(sheet)](sheets/memo-search-sort.md)
- [ ] I can define a binary search tree and search or insert in one.
- [ ] I can write insertion sort, selection sort and merge sort on llists (with `take`, `drop`, `merge`). [(sheet)](sheets/memo-search-sort.md)
- [ ] I can give best and worst case orders of growth for each sort. [(sheet)](sheets/growth.md) (Self-test: insertion sort on a sorted llist?)
- [ ] I can represent expressions as tagged llists and write an evaluator or differentiator that dispatches on the tag.
- [ ] I can put simplification into constructors (adding 0, multiplying by 1).

### L7B Streams I and language processing

- [ ] I can explain why a conditional cannot be an ordinary function, and delay work with a nullary lambda. [(sheet)](sheets/streams.md)
- [ ] I can write a stream by hand with `pair(v, lambda: ...)`. [(sheet)](sheets/streams.md)
- [ ] I can write `stream_tail`, `stream_ref`, `stream_map`, `stream_filter`, `enum_stream`, `integers_from`, `eval_stream` myself. [(sheet)](sheets/streams.md)
- [ ] I can draw T-diagrams for an interpreter and a compiler, and stack them.

## Unit 3: State (§3)

### L8A Mutable data, lists and loops

- [ ] I can tell reassignment from mutation, and use `global` and `nonlocal` correctly. [(sheet)](sheets/mutation-lists-loops.md)
- [ ] ★ I can write a maker function that returns a function with private state (bank account, counter). [(sheet)](sheets/mutation-lists-loops.md) (Self-test: two independent counters.)
- [ ] I can explain why the substitution model fails once there is reassignment. [(sheet)](sheets/environment-model.md)
- [ ] ★ I can predict the effect of `set_head`/`set_tail` through aliases, and after `append` (shared tail). [(sheet)](sheets/mutation-lists-loops.md)
- [ ] I can make and detect a cycle, and explain why `length` never ends on one.
- [ ] I can write destructive `d_append` and `d_map` and draw before/after diagrams. [(sheet)](sheets/mutation-lists-loops.md)
- [ ] I can use lists: indices (also negative), `len`, `[v] * n`, element assignment; and know lists cannot grow. [(sheet)](sheets/mutation-lists-loops.md)
- [ ] I can write `while` and `for i in range(...)` loops (1, 2 or 3 arguments), with `break` and `continue`. [(sheet)](sheets/mutation-lists-loops.md) (Self-test: what does `range(5, 0, -2)` visit?)
- [ ] I can state a loop invariant for a simple loop.
- [ ] I can build a 2-D table with a fresh row per row, and explain the `[[0] * n] * m` trap. [(sheet)](sheets/traps.md)

### L9A Environment model

- [ ] ★ I can name the parts: environment, frame, binding, enclosing environment, global frame, built-ins frame, function object, unassigned. [(sheet)](sheets/environment-model.md)
- [ ] ★ I can apply the function application rule: new frame, enclosing environment from the function object, parameters bound, locals unassigned. [(sheet)](sheets/environment-model.md)
- [ ] ★ I can draw the environment diagram at a marked point of a program with nested functions. [(sheet)](sheets/environment-model.md) (Self-test: `make_adder(5)(1)` at the moment `x + y` is evaluated.)
- [ ] I can draw a function object as two circles pointing to its code and its environment. [(sheet)](sheets/environment-model.md)
- [ ] I can show how `global` and `nonlocal` change which binding an assignment updates. [(sheet)](sheets/environment-model.md)
- [ ] I can draw pairs and lists outside frames, so that sharing is visible. [(sheet)](sheets/environment-model.md)
- [ ] I can say when `is` and `==` differ. [(sheet)](sheets/traps.md) (Self-test: `pair(1, 2) is pair(1, 2)`.)

### L9B Lists and loops II

- [ ] I can sum, find the maximum and compare lists with loops, and give best and worst cases. [(sheet)](sheets/mutation-lists-loops.md)
- [ ] I can map a list in place and filter a list in two passes. [(sheet)](sheets/mutation-lists-loops.md)
- [ ] I can reverse a list in place with two indices and a temporary variable. [(sheet)](sheets/mutation-lists-loops.md)
- [ ] I can use an early `return` instead of a flag and `break`.

### L10A Searching, sorting II and memoization

- [ ] I can write linear search and binary search (loop and recursive) on a sorted list. [(sheet)](sheets/memo-search-sort.md)
- [ ] I can explain why `swap(x, y)` on parameters does nothing, and write `swap(A, i, j)`. [(sheet)](sheets/memo-search-sort.md)
- [ ] I can write in-place selection, insertion (swap and shift) and merge sort on lists. [(sheet)](sheets/memo-search-sort.md)
- [ ] ★ I can memoize a function with a 1-D table and say its new order of growth. [(sheet)](sheets/memo-search-sort.md) (Self-test: memoized `fib(n)` time and space.)
- [ ] ★ I can explain why the recursive calls must go through the memoized function. [(sheet)](sheets/traps.md)
- [ ] I can memoize a function of two arguments with a 2-D table (n choose k). [(sheet)](sheets/memo-search-sort.md)
- [ ] I can draw a call tree with "found in the table" leaves.

### L11A Streams II

- [ ] ★ I can define self-referential streams: ones, integers, Fibonacci, factorials, powers. [(sheet)](sheets/streams.md) (Self-test: first 5 elements of `s = pair(1, lambda: scale_stream(2, s))`.)
- [ ] ★ I can write `add_streams`, `mul_streams` and `scale_stream`. [(sheet)](sheets/streams.md)
- [ ] ★ I can say what gets computed when a stream element is asked for, and how often. [(sheet)](sheets/streams.md)
- [ ] I can write `memo_fun` with `nonlocal` and count the prints with and without it. [(sheet)](sheets/streams.md)
- [ ] I can write the sieve and a stream of improving square-root guesses. [(sheet)](sheets/streams.md)

## Unit 4: Beyond (§4)

### L11B Metacircular evaluator I

- [ ] I can read the tagged-llist syntax tree that `parse` returns for small programs. [(sheet)](sheets/mce.md) (Self-test: `print_llist(parse("x = 1 + 2"))`.)
- [ ] I can follow `evaluate(component, env)` dispatching on the tag, and `llist_of_values`. [(sheet)](sheets/mce.md)
- [ ] I can explain how conditionals are evaluated with a host conditional and `is_truthy`. [(sheet)](sheets/mce.md)
- [ ] I can describe frames and environments as data, and how lookup and assignment walk them. [(sheet)](sheets/mce.md)
- [ ] I can add a new operator or statement kind to the evaluator. [(sheet)](sheets/mce.md)

### L12A Metacircular evaluator II

- [ ] I can explain the evaluate–apply loop, built-in vs compound functions, and `apply_in_underlying_python`. [(sheet)](sheets/mce.md)
- [ ] I can explain how return values are wrapped and unwrapped. [(sheet)](sheets/mce.md)
- [ ] I can explain how locals are found at definition time and marked `'*unassigned*'` in the new frame. [(sheet)](sheets/mce.md)
- [ ] I can change an evaluator rule (argument order, truthiness, a static check) and predict the effect. [(sheet)](sheets/mce.md)
- [ ] I can explain lazy evaluation: thunks, `delay_it`, `force_it`, memoized thunks, strict built-ins. [(sheet)](sheets/mce.md)

### L13A Types and objects

- [ ] I can annotate parameters and return types, including `Callable[[...], R]`, `LList[T]` and `T | None`. [(sheet)](sheets/types.md)
- [ ] I can predict a checker rejection and fix it by narrowing with `is_none`. [(sheet)](sheets/types.md)
- [ ] I can write a generic function such as `length[A]`. [(sheet)](sheets/types.md)
- [ ] I can build an object from closures with message passing (`acc("withdraw")(50)`). [(sheet)](sheets/mutation-lists-loops.md)

### L13B Across the course

- [ ] I can name the three mental models and when each one applies.
- [ ] I can list what Python §1–§4 forbid that full Python allows. [(sheet)](sheets/traps.md)
- [ ] ★ I can avoid all 25 classic traps. [(sheet)](sheets/traps.md)

## Three micro self-tests to check right now

Answer on paper first, then open the answer.

**1.** What does this print?

```python
xs = llist(4, 5, 6)
print(reduce(lambda x, rest: pair(rest, x), None, xs))
```

??? success "Answer"
    ```python title="§2"
    xs = llist(4, 5, 6)
    print(reduce(lambda x, rest: pair(rest, x), None, xs))
    ```
    ```text
    [[[None, 6], 5], 4]
    ```
    `reduce` starts at the right: `f(6, None)` is `[None, 6]`, then 5 and 4 are each put on the right of the previous result. The result is not a llist.

**2.** What does this print?

```python
x = 1
def f(x):
    g = lambda y: x + y
    return g(10)
print(f(5), x)
```

??? success "Answer"
    ```python title="§1"
    x = 1
    def f(x):
        g = lambda y: x + y
        return g(10)
    print(f(5), x)
    ```
    ```text
    15 1
    ```
    `x` in the lambda refers to the closest surrounding declaration: `f`'s parameter, which is 5. The global `x` is untouched.

**3.** What does this print?

```python
def make():
    n = 0
    def bump():
        nonlocal n
        n = n + 1
        return n
    return bump
a = make()
b = make()
print(a(), a(), b())
```

??? success "Answer"
    ```python title="§3"
    def make():
        n = 0
        def bump():
            nonlocal n
            n = n + 1
            return n
        return bump
    a = make()
    b = make()
    print(a(), a(), b())
    ```
    ```text
    1 2 1
    ```
    Each call of `make` creates a new frame with its own `n`, so `a` and `b` count separately.
