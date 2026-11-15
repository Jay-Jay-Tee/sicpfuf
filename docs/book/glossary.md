# Glossary

<p class="chapter-goal">Every course word in plain language, with the chapter that explains it.</p>

The words are the course's own. Where full Python or other courses use a different word, the
course's word is the one to use in the exam.

## A

abstraction barrier
:   A line between the code that USES some data and the code that knows how it is represented.
    Users go through constructors, selectors and predicates only. [Chapter 7](07-data-abstraction.md)

accumulator
:   An extra parameter that carries the result built so far, so that the recursive call can be
    the last thing done (an iterative process). [Chapter 3](03-substitution-recursion.md)

`actual_value`
:   In the lazy evaluator: evaluate an expression and force the result, giving a real value, not
    a thunk. [Chapter 18](18-mce-lazy.md)

annotation (type annotation)
:   A type written next to a parameter, a result or an assignment: `x: int`, `-> int`. Checked by
    Python §4 Typed, ignored at run time. [Chapter 19](19-types-objects.md)

applicative order reduction
:   Evaluate the arguments first, then apply the function to their values. Python works this
    way. [Chapter 3](03-substitution-recursion.md), [Chapter 18](18-mce-lazy.md)

`apply`
:   The evaluator function that runs a function object on a llist of argument values: a
    built-in directly, a compound function by evaluating its body in a new frame. [Chapter 18](18-mce-lazy.md)

`apply_in_underlying_python`
:   Python §4 built-in: `apply_in_underlying_python(f, args)` applies the function `f` to the
    elements of the llist `args`. [Chapter 18](18-mce-lazy.md)

argument
:   A value given to a function in a function application. Not the same as a parameter.
    [Chapter 1](01-elements.md)

assignment
:   See declaration assignment and reassignment.

## B

base case
:   The case of a recursive function that is answered without a further recursive call.
    [Chapter 3](03-substitution-recursion.md)

binary search
:   Search a sorted list by halving the range each time: Θ(log n). [Chapter 15](15-search-sort-memo.md)

binding
:   A pair "name and value" in a frame. [Chapter 14](14-environment-model.md)

boolean
:   `True` or `False`. In Python §1 to §4 every condition must be exactly one of them.
    [Chapter 1](01-elements.md)

box notation
:   Writing pairs as nested brackets: `[1, [2, None]]` is `llist(1, 2)`. [Chapter 7](07-data-abstraction.md)

box-and-pointer diagram
:   A drawing of pairs as two-box cells with arrows to their head and tail. [Chapter 7](07-data-abstraction.md)

built-in function (primitive, pre-declared function)
:   A function the language already has, such as `print`, `math_sqrt` or `head`. In the
    evaluator: `llist("built_in", implementation)`. [Chapter 1](01-elements.md), [Chapter 18](18-mce-lazy.md)

built-ins frame
:   The outermost frame of the environment model, holding the pre-declared names. The global
    frame sits on top of it. [Chapter 14](14-environment-model.md)

## C

`Callable[[A, B], R]`
:   The type of functions that take an A and a B and return an R. [Chapter 19](19-types-objects.md)

class
:   In full Python (not §4): a blueprint for objects, listing their attributes and methods.
    [Chapter 19](19-types-objects.md)

closest surrounding declaration
:   The rule of lexical scoping: a name refers to the nearest declaration of it that encloses it
    in the program text. [Chapter 5](05-higher-order-scope.md)

component
:   The textbook's word for a statement or an expression, as seen by the evaluator. [Chapter 17](17-mce.md)

compound function
:   A function defined in the program with `def` or a lambda expression (not a built-in). In the
    evaluator: `llist("compound_function", parameters, locals, globals, body, env)`.
    [Chapter 1](01-elements.md), [Chapter 18](18-mce-lazy.md)

conditional expression
:   `consequent if predicate else alternative`: an expression whose value is the consequent or
    the alternative. [Chapter 1](01-elements.md)

conditional statement
:   `if predicate: ... elif ...: ... else: ...`, choosing which statements run. [Chapter 5](05-higher-order-scope.md)

constructor
:   A function that builds a data object, such as `pair` or `make_rational`. [Chapter 7](07-data-abstraction.md)

continuation
:   A function that receives a result and does "the rest of the work". [Chapter 9](09-trees-cps.md)

continuation-passing style (CPS)
:   Writing functions that pass their result to a continuation instead of returning it to a
    waiting caller. Every call becomes a tail call. [Chapter 9](09-trees-cps.md)

## D

data abstraction
:   Using data only through constructors, selectors and predicates, so the representation can
    change without changing its users. [Chapter 7](07-data-abstraction.md)

declaration assignment
:   The first `name = expression` of a name in its scope: it creates the name. [Chapter 1](01-elements.md)

deferred operation
:   Work left waiting until a recursive call returns, as the `n *` in `n * fact(n - 1)`. Their
    pile-up is what makes a process recursive. [Chapter 3](03-substitution-recursion.md)

`delay_it`
:   In the lazy evaluator: package an argument expression and its environment as a thunk.
    [Chapter 18](18-mce-lazy.md)

delayed evaluation
:   Not evaluating an expression until its value is needed, for example by wrapping it in
    `lambda: ...` (streams). [Chapter 11](11-streams.md)

derived component
:   A syntactic form that the evaluator handles by rewriting it into other components, like an
    operator combination into an application. [Chapter 18](18-mce-lazy.md)

dispatch function
:   The function that represents an object in message passing: it receives a message string and
    returns the matching operation. [Chapter 19](19-types-objects.md)

## E

dynamic programming
:   Filling a table of results bottom-up with a loop; the "beyond the course" partner of
    memoization. [Chapter 20](20-big-picture.md)

enclosing environment
:   The environment that a frame extends: where the search for a name continues when it is not
    in the frame. [Chapter 14](14-environment-model.md)

environment
:   A sequence of frames, innermost first. In the evaluator: a llist of frames. [Chapter 14](14-environment-model.md),
    [Chapter 17](17-mce.md)

environment model
:   The mental model for programs with state: frames of bindings, enclosing environments and
    function objects. [Chapter 14](14-environment-model.md)

`error`
:   `error(message, value)` stops the program and prints `Error: message value`. [Chapter 10](10-sorting-symbolic.md)

`evaluate`
:   The evaluator function that looks at one component and an environment and decides what to
    do, one clause per kind of component. [Chapter 17](17-mce.md)

evaluate–apply loop
:   `evaluate` calls `apply` for applications; `apply` calls `evaluate` on a compound function's
    body. The heart of the evaluator. [Chapter 18](18-mce-lazy.md)

expression
:   A piece of program that has a value, such as `1 + 2` or `f(x)`. [Chapter 1](01-elements.md)

extending an environment
:   Making a new frame whose enclosing environment is an existing one: what every function
    application does. [Chapter 14](14-environment-model.md)

## F

`filter`
:   `filter(pred, xs)`: the llist of the elements of `xs` for which `pred` is `True`. [Chapter 8](08-llist-processing.md)

five-step method
:   Read, play, think, program, test. [Chapter 20](20-big-picture.md)

`for` loop
:   `for i in range(...):` repeats a body for each number of the range (Python §3 and §4 allow
    nothing but `range`). [Chapter 13](13-lists-loops.md)

`force_it`, forcing
:   Evaluating a delayed thing: calling a stream's tail function, or (in the lazy evaluator)
    evaluating a thunk. [Chapter 11](11-streams.md), [Chapter 18](18-mce-lazy.md)

frame
:   A table of bindings. In the evaluator: a pair of two llists, symbols and values. [Chapter 14](14-environment-model.md),
    [Chapter 17](17-mce.md)

function application
:   Using a function on arguments: `f(1, 2)`. [Chapter 1](01-elements.md)

function definition
:   `def f(params): body`: makes a function object and assigns it to the name `f`. [Chapter 1](01-elements.md)

function object
:   The value of a function: its parameters and body plus the environment it was created in. Drawn
    as two circles. [Chapter 14](14-environment-model.md)

functional programming
:   Programming with functions as values and without reassignment. [Chapter 5](05-higher-order-scope.md),
    [Chapter 20](20-big-picture.md)

## G

generic function
:   A typed function with a type parameter, `def length[A](xs: LList[A]) -> int`, that works for
    every element type. [Chapter 19](19-types-objects.md)

`global`
:   `global x` in a function: assignments to `x` change the global `x` instead of making a local
    one. In the evaluator, marked by `'*global*'`. [Chapter 12](12-state-mutation.md), [Chapter 18](18-mce-lazy.md)

global environment, global frame
:   The frame of the names declared at the top level of the program (on top of the built-ins
    frame). [Chapter 14](14-environment-model.md)

## H

`head`, `tail`
:   The selectors of a pair: its first and second part. [Chapter 7](07-data-abstraction.md)

higher-order function
:   A function that takes a function as an argument or returns one. [Chapter 5](05-higher-order-scope.md)

## I

insertion sort, selection sort
:   Two Θ(n²) sorts: insert each element into a sorted part; or repeatedly pick the smallest.
    [Chapter 10](10-sorting-symbolic.md), [Chapter 15](15-search-sort-memo.md)

`is`
:   Identity: `a is b` is `True` when both are the same object (Python §3 and §4). [Chapter 14](14-environment-model.md)

iterative process
:   A process with no deferred operations: its state is all in the parameters, so it runs in
    Θ(1) space (with proper tail calls). [Chapter 3](03-substitution-recursion.md)

## L

lambda expression
:   `lambda params: expression`, a function without a name. [Chapter 5](05-higher-order-scope.md)

lazy evaluation
:   Delaying the evaluation of each argument until its value is needed (normal order), using
    thunks. [Chapter 18](18-mce-lazy.md)

lazy pair
:   A pair built from compound functions in the lazy evaluator; both parts are delayed, so llists
    can be infinite. [Chapter 18](18-mce-lazy.md)

lexical scoping
:   A name's meaning is fixed by where it is written in the program, not by where it is used.
    [Chapter 5](05-higher-order-scope.md)

list
:   A Python list `[1, 2, 3]` (from §3): indexed with `xs[i]` from `-len(xs)` to `len(xs) - 1`,
    fixed length. Not a llist. [Chapter 13](13-lists-loops.md)

literal
:   A value written directly in the program: `42`, `"hi"`, `True`, `None`. [Chapter 1](01-elements.md)

llist (linked list)
:   `None`, or a pair whose tail is a llist. `None` is the empty llist. [Chapter 7](07-data-abstraction.md)

llist notation
:   Writing a llist as `llist(1, 2, 3)`, as `print_llist` does. [Chapter 7](07-data-abstraction.md)

`LList[T]`
:   The type of llists of T: `Pair[T, LList[T]] | None`. [Chapter 19](19-types-objects.md)

local name
:   A name assigned in a function body (and not declared `global` or `nonlocal`): it belongs to
    the function's own frame for the whole body. [Chapter 14](14-environment-model.md), [Chapter 18](18-mce-lazy.md)

## M

`map`
:   `map(f, xs)`: the llist of `f` applied to each element of `xs`. [Chapter 8](08-llist-processing.md)

`memo_fun`
:   A function that wraps a nullary function so its result is computed once and remembered: used
    for memoized streams. [Chapter 11](11-streams.md), [Chapter 16](16-streams-ii.md)

memoization
:   Remembering results in a table so each is computed only once. [Chapter 15](15-search-sort-memo.md)

merge sort
:   Split in half, sort each half, merge: Θ(n log n). [Chapter 10](10-sorting-symbolic.md)

message passing
:   Representing an object as a dispatch function that receives a message (a string) and answers
    with an operation or a value. [Chapter 19](19-types-objects.md)

metacircular evaluator
:   An evaluator written in the language it evaluates. [Chapter 17](17-mce.md)

metalinguistic abstraction
:   Solving problems by designing and implementing a new language. [Chapter 17](17-mce.md)

## N

name
:   A word that stands for a value, such as `size` or `square`. Called a variable once it can be
    reassigned. [Chapter 1](01-elements.md)

narrowing
:   After a test such as `is_none(xs)`, the type checker knows a more precise type in each branch.
    [Chapter 19](19-types-objects.md)

`None`
:   The value meaning "nothing": the empty llist, and the result of a function with no executed
    `return`. [Chapter 7](07-data-abstraction.md)

`nonlocal`
:   `nonlocal x` in an inner function: assignments to `x` change the `x` of the enclosing function.
    [Chapter 12](12-state-mutation.md)

non-strict
:   A function is non-strict in an argument if its body is entered before the argument is
    evaluated. [Chapter 18](18-mce-lazy.md)

normal order reduction
:   Substitute argument expressions unevaluated and evaluate them only when needed.
    [Chapter 3](03-substitution-recursion.md), [Chapter 18](18-mce-lazy.md)

nullary function
:   A function of no arguments, `lambda: e`. Used for the tail of a stream. [Chapter 11](11-streams.md)

## O

object
:   State plus the operations on it. In §3 and §4, built from a maker function and closures over
    its frame. [Chapter 19](19-types-objects.md)

operand
:   An expression an operator works on: in `a + b`, `a` and `b`. [Chapter 1](01-elements.md)

operator combination
:   An operator with its operands, such as `a + b` or `-x`. The evaluator turns it into an
    application of a built-in. [Chapter 1](01-elements.md), [Chapter 18](18-mce-lazy.md)

order of growth
:   How time or space grows with the input size n, written Θ(f(n)) (tight bound), O (upper bound)
    or Ω (lower bound). [Chapter 4](04-orders-of-growth.md)

## P

pair
:   Two values glued together: `pair(1, 2)`, printed `[1, 2]`. In §3 and §4 a pair is a list of
    length two. [Chapter 7](07-data-abstraction.md)

parameter
:   A name in a function definition that receives an argument. [Chapter 1](01-elements.md)

`parse`
:   Python §4 built-in: turns program text into a syntax tree of tagged llists. [Chapter 17](17-mce.md)

predicate
:   A function or expression that gives `True` or `False`; the condition part of a conditional.
    Names start with `is_`. [Chapter 1](01-elements.md), [Chapter 7](07-data-abstraction.md)

proper tail call
:   A `return f(...)` with nothing left to do afterwards; Python §1 to §4 run it without keeping
    the caller waiting. Real Python does not guarantee this. [Chapter 3](03-substitution-recursion.md),
    [Chapter 20](20-big-picture.md)

Python §1, §2, §3, §4
:   The four growing sublanguages of Python the course uses; §4 Typed adds type annotations.
    [Chapter 20](20-big-picture.md), [Chapter 19](19-types-objects.md)

## R

reassignment
:   Giving an existing name a new value with `=` (Python §3 and §4). [Chapter 12](12-state-mutation.md)

recursive process
:   A process in which deferred operations pile up, so space grows with the input. [Chapter 3](03-substitution-recursion.md)

`reduce`
:   `reduce(f, initial, xs)`: a right fold, `f(x1, f(x2, ... f(xn, initial)))`. [Chapter 8](08-llist-processing.md)

return statement, return expression
:   `return e`: ends the function and gives the value of the return expression `e`.
    [Chapter 1](01-elements.md)

return value (in the evaluator)
:   The wrapper `llist("return_value", v)` made by evaluating a return statement; `apply` unwraps
    it. [Chapter 18](18-mce-lazy.md)

rune
:   A picture value of the rune library, combined with `stack`, `beside` and friends. [Chapter 2](02-runes.md)

## S

scope
:   The part of the program where a declaration of a name is valid. [Chapter 5](05-higher-order-scope.md)

selector
:   A function that takes a part out of a data object, such as `head`, `tail` or `literal_value`.
    [Chapter 7](07-data-abstraction.md)

sequence (in the evaluator)
:   `llist("sequence", llist(statements))`: several statements in a row. [Chapter 17](17-mce.md)

`set_head`, `set_tail`
:   Change the head or tail of an existing pair (Python §3 and §4). [Chapter 12](12-state-mutation.md)

statement
:   A piece of program that does something, such as an assignment or a `def`. [Chapter 1](01-elements.md)

stream
:   `None`, or a pair whose tail is a nullary function giving the rest of the stream. Can be
    infinite. [Chapter 11](11-streams.md), [Chapter 16](16-streams-ii.md)

strict
:   A function is strict in an argument if the argument is evaluated before the body is entered.
    [Chapter 18](18-mce-lazy.md)

substitution model
:   The mental model for §1 and §2: apply a function by replacing its parameters with the
    arguments in the body. [Chapter 3](03-substitution-recursion.md)

subtype
:   S is a subtype of T if every S value is a T value (`int` of `float`). [Chapter 19](19-types-objects.md)

symbol
:   The string by which the evaluator represents a name, such as `"x"`. [Chapter 17](17-mce.md)

symbolic data
:   Data made of strings that stand for things, such as expressions to differentiate. [Chapter 10](10-sorting-symbolic.md)

syntax predicate
:   A function that tests what kind a component is, such as `is_literal`. [Chapter 17](17-mce.md)

syntax tree
:   The tree that `parse` returns: each component a tagged llist. [Chapter 17](17-mce.md)

## T

tagged llist
:   A llist whose head is a string saying what kind of data it is: `llist("literal", 5)`.
    [Chapter 10](10-sorting-symbolic.md), [Chapter 17](17-mce.md)

thunk
:   In the lazy evaluator: an argument expression packed with its environment,
    `llist("thunk", exp, env)`, to be evaluated when needed. [Chapter 18](18-mce-lazy.md)

tree
:   A llist whose elements may themselves be trees. [Chapter 9](09-trees-cps.md)

tree recursion
:   A function that calls itself more than once per call, like `fib`. [Chapter 4](04-orders-of-growth.md)

truthy, falsy
:   Counting as true or false in a condition. Real Python treats `0`, `""`, `None` and empty
    collections as falsy; Python §1 to §4 accept only `True` and `False`. [Chapter 20](20-big-picture.md)

type
:   A set of values; it decides which operations make sense. [Chapter 19](19-types-objects.md)

type alias
:   `type Vector = list[float]`: a new name for a type. [Chapter 19](19-types-objects.md)

## U

unassigned
:   The state of a local name before its assignment has run. The environment model draws it as
    unassigned; the evaluator binds it to `'*unassigned*'`. [Chapter 14](14-environment-model.md),
    [Chapter 18](18-mce-lazy.md)

## W

`while` loop
:   `while predicate: body` repeats the body as long as the predicate is `True`. [Chapter 13](13-lists-loops.md)

wishful thinking
:   Writing a recursive function by assuming it already works for a smaller input. [Chapter 3](03-substitution-recursion.md)
