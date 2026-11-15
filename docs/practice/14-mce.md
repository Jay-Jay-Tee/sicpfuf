# Drill 14 · The metacircular evaluator

<p class="chapter-goal">Read syntax trees, trace evaluate and apply, find the function that decides, change the evaluator, think lazily.</p>

Easiest first. Try each problem on paper before you open the answer. The evaluator is sicpfuf's [`examples/mce.py`](https://github.com/Jay-Jay-Tee/sicpfuf/blob/main/examples/mce.py) (same function names as the textbook). Blocks titled `§4 · --with examples/mce.py` load it first, so they can **redefine** its functions and then run a program in the evaluated language with `parse_and_evaluate("""…""")`.

!!! tip "How a modification works here"
    `evaluate` calls `apply`, `eval_sequence` and the others **by name**, through the global frame. So if you save the old function under a new name and define a new one with the same name, every call inside the evaluator goes to the new one:

    ```python
    old_evaluate = evaluate
    def evaluate(component, env):
        if is_tagged_llist(component, "my_new_tag"):
            return ...                       # the new case
        else:
            return old_evaluate(component, env)
    ```

    In an exam you would instead add the new case to `evaluate` itself. The idea is the same.

!!! warning "The evaluated language's `print` takes ONE argument"
    In `mce.py`, `print` is the built-in `lambda x: print(show(x))`. Inside `parse_and_evaluate`, write `print(a)` and `print(b)`, not `print(a, b)`.

## 1. A tree for an expression ★

*Skill: predict `parse` output for operator combinations.*

```python title="§4"
print_llist(parse("x * (y + 1)"))
```

??? success "Answer"
    ```text
    llist('binary_operator_combination', '*', llist('name', 'x'), llist('binary_operator_combination', '+', llist('name', 'y'), llist('literal', 1)))
    ```
    The outermost operator is `*` (the brackets made `y + 1` one operand), so the root is a `"binary_operator_combination"` with the operator string, then the two operand trees. A name becomes `llist('name', 'x')`, a number `llist('literal', 1)`.

## 2. Four more shapes ★

*Skill: know the tags and the positions of the parts.*

Predict each line before you open the answer.

```python title="§4"
print_llist(parse("lambda a: a"))
print_llist(parse("x = 5"))
print_llist(parse("1 if b else 2"))
print_llist(parse("def f(n):\n    return n"))
```

??? success "Answer"
    ```text
    llist('lambda_expression', llist(llist('name', 'a')), llist('name', 'a'))
    llist('assignment', llist('name', 'x'), llist('literal', 5))
    llist('conditional_expression', llist('name', 'b'), llist('literal', 1), llist('literal', 2))
    llist('function_definition', llist('name', 'f'), llist(llist('name', 'n')), llist('return_statement', llist('name', 'n')))
    ```
    - lambda: the parameters as a llist of **name nodes**, then the body **expression** (no return statement: the evaluator adds one).
    - assignment: the name node, then the value expression.
    - conditional expression: predicate **first**, then consequent, then alternative (not the order you read them in!).
    - function definition: name node, llist of parameter name nodes, body (here one return statement).

## 3. One statement or two? ★

*Skill: the `"sequence"` wrapper.*

```python title="§4"
print_llist(parse("x = 1"))
print_llist(parse("x = 1\nprint(x)"))
```

??? success "Answer"
    ```text
    llist('assignment', llist('name', 'x'), llist('literal', 1))
    llist('sequence', llist(llist('assignment', llist('name', 'x'), llist('literal', 1)), llist('application', llist('name', 'print'), llist(llist('name', 'x')))))
    ```
    A one-statement program is that statement itself. Two or more statements are wrapped: `llist('sequence', llist(statement1, statement2, …))`. The application `print(x)` is `llist('application', function expression, llist(argument expressions))`.

## 4. Which function decides? ★

*Skill: know the job of each part of the evaluator.*

Name the function in `mce.py` that decides each of these:

1. That `1 if 0 else 2` is an error.
2. Which names are local to a function, and **when** that is decided.
3. Which environment a function body is evaluated in.
4. That the statements after a `return` are skipped.
5. That `x = 1` at top level creates a new binding.

??? success "Answer"
    1. `is_truthy` (called by `eval_conditional`): only `True` and `False` are accepted.
    2. `local_variables` (with `assigned_variables`, `global_variables`, `nonlocal_variables`), called by `eval_function_definition`: once, when the `def` is **evaluated**, not at each call. `apply` then binds each local to `"*unassigned*"`.
    3. `apply`: it extends `function_environment(fun)`, the environment stored when the function object was made.
    4. `eval_sequence`: when a statement's value `is_return_value`, it returns it at once without evaluating the rest.
    5. `assign_symbol_value`: if no frame has the name and it has reached the global environment, it calls `add_binding_to_frame`.

    ```python title="§4 · --with examples/mce.py"
    parse_and_evaluate("print(1 if 0 else 2)")
    ```
    ```text
    Error: boolean expected, received 0
    ```

## 5. Frames are data ★★

*Skill: the global frame is a pair of two llists, changed by `add_binding_to_frame`.*

```python title="§4 · --with examples/mce.py"
parse_and_evaluate("a = 1\nb = 2")
print_llist(frame_symbols(first_frame(the_global_environment)))
parse_and_evaluate("a = a + 10")
print_llist(frame_values(first_frame(the_global_environment)))
parse_and_evaluate("print(b)")
```

??? success "Answer"
    ```text
    llist('b', 'a')
    llist(2, 11)
    2
    ```
    `add_binding_to_frame` puts each new binding at the **front** of both llists, so `b` comes before `a`. `a = a + 10` finds `a` and changes its value in place (`set_head` on the values llist): no new binding. The global environment survives between `parse_and_evaluate` calls, so the last program still sees `b`.

## 6. Watch evaluate work ★★

*Skill: trace the evaluate-apply loop.*

Predict the tag of every component that `evaluate` is called on, in order, for `(lambda x: x + 1)(2)`.

```python title="§4 · --with examples/mce.py"
old_evaluate = evaluate

def evaluate(component, env):
    print("evaluate " + head(component))
    return old_evaluate(component, env)

parse_and_evaluate("print((lambda x: x + 1)(2))")
```

??? success "Answer"
    ```text
    evaluate application
    evaluate name
    evaluate application
    evaluate lambda_expression
    evaluate literal
    evaluate return_statement
    evaluate binary_operator_combination
    evaluate application
    evaluate name
    evaluate name
    evaluate literal
    3
    ```
    1. The whole program is an `application` of `print`. `evaluate` first evaluates its **function expression** (`name` print), then the argument, which is itself an `application`.
    2. Its function expression, the `lambda_expression`, gives a function object; its argument, `literal` 2, gives 2.
    3. `apply` evaluates the body, a `return_statement` (the lambda's body was wrapped in one), in a new frame `x: 2`.
    4. `x + 1` is a `binary_operator_combination`; `evaluate` rewrites it into an `application` of the name `"+"`, then evaluates `name` +, `name` x, `literal` 1.
    5. Finally the built-in `print` is applied to 3.

## 7. A new built-in ★

*Skill: add a built-in function to the evaluated language.*

Make `square` a built-in function of the evaluated language. Why does adding a line to `built_in_functions` **now** (after `mce.py` has run) not work?

??? success "Answer"
    ```python title="§4 · --with examples/mce.py"
    built_ins_frame = first_frame(enclosing_environment(the_global_environment))
    add_binding_to_frame("square", llist("built_in", lambda x: x * x), built_ins_frame)

    parse_and_evaluate("print(square(7) + 1)")
    ```
    ```text
    50
    ```
    A built-in is a tagged llist `llist("built_in", implementation)`; `apply_built_in_function` hands the arguments to the implementation with `apply_in_underlying_python`. The table `built_in_functions` is only read **once**, by `setup_environment`, when `the_global_environment` is made, so changing it later changes nothing. We add the binding to the built-ins frame directly. (In `mce.py` itself, you would add `llist("square", lambda x: x * x)` to the table.)

## 8. Count the applications ★★

*Skill: modify `apply`; tell compound from built-in functions.*

Make the evaluator count how many times a **compound** function is applied, and find the count for the tree-recursive `fib(10)`.

??? success "Answer"
    ```python title="§4 · --with examples/mce.py"
    count = 0
    old_apply = apply

    def apply(fun, arguments):
        global count
        if is_compound_function(fun):
            count = count + 1
        return old_apply(fun, arguments)

    parse_and_evaluate("""
    def fib(n):
        return n if n < 2 else fib(n - 1) + fib(n - 2)

    print(fib(10))
    """)
    print(count)
    ```
    ```text
    55
    177
    ```
    Every application in the evaluated program, including `+`, `<` and `print`, goes through `apply`; only those whose function is tagged `"compound_function"` are counted. 177 is the number of calls the tree recursion makes for `fib(10)`.

## 9. Teach it `and` and `or` ★★

*Skill: add a syntax form by rewriting it into one the evaluator knows.*

`parse("a and b")` gives `llist('logical_composition', 'and', a, b)`. `mce.py` has no case for it. Add one, keeping the short-circuit rule: `a and b` means `b if a else False`, and `a or b` means `True if a else b`.

??? success "Answer"
    ```python title="§4 · --with examples/mce.py"
    old_evaluate = evaluate

    def evaluate(component, env):
        if is_tagged_llist(component, "logical_composition"):
            left = llist_ref(component, 2)
            right = llist_ref(component, 3)
            if llist_ref(component, 1) == "and":
                rewritten = llist("conditional_expression", left, right, make_literal(False))
            else:
                rewritten = llist("conditional_expression", left, make_literal(True), right)
            return evaluate(rewritten, env)
        else:
            return old_evaluate(component, env)

    parse_and_evaluate("""
    print(1 == 2 and 1 / 0 == 0)
    print(1 == 1 or no_such_name)
    print(1 < 2 and 2 < 3)
    """)
    ```
    ```text
    False
    True
    True
    ```
    We could not make `and` a built-in function like `+`: `apply` gets **values**, so both operands would already have been evaluated, and `1 / 0` would stop the program. Rewriting into a conditional expression means only the operands that are needed are evaluated (the same trick as `operator_combination_to_application`). The unbound `no_such_name` is never looked up.

## 10. Add while loops ★★★

*Skill: add a statement to `evaluate`, and to the scan for local names.*

`parse` gives `llist('while_loop', predicate, body)`. (a) Add a case to `evaluate`; a `return` inside the loop body must leave the function. (b) Then run this program. Why is the global `sq` changed, and how do you fix it?

```python
sq = 0
def last_square(n):
    i = 0
    while i < n:
        i = i + 1
        sq = i * i
    return sq
print(last_square(4))
print(sq)
```

??? success "Answer"
    ```python title="§4 · --with examples/mce.py"
    def eval_while(component, env):
        predicate = llist_ref(component, 1)
        body = llist_ref(component, 2)
        while is_truthy(evaluate(predicate, env)):
            result = evaluate(body, env)
            if is_return_value(result):
                return result
        return None

    evaluate_without_while = evaluate

    def evaluate(component, env):
        if is_tagged_llist(component, "while_loop"):
            return eval_while(component, env)
        else:
            return evaluate_without_while(component, env)

    parse_and_evaluate("""
    def first_power_above(b, limit):
        p = 1
        while True:
            p = p * b
            if p > limit:
                return p

    print(first_power_above(3, 100))

    sq = 0
    def last_square(n):
        i = 0
        while i < n:
            i = i + 1
            sq = i * i
        return sq

    print(last_square(4))
    print(sq)
    """)
    ```
    ```text
    243
    16
    16
    ```
    (a) We explain the loop of the evaluated language with a loop of our own. If the body produces a **return value**, pass it upwards at once, exactly as `eval_sequence` does; otherwise the loop's value is `None`.

    (b) The global `sq` became 16. `declared_symbols` (used by `local_variables`) looks into sequences and conditionals but **not** into while loops, so `sq` was not made local. Inside `last_square`, `assign_symbol_value` found no `sq` in the call frame, went outward and changed the global one. (`i` is fine: it is also assigned before the loop.) Fix: let the scan look into loop bodies too.

    ```python title="§4 · --with examples/mce.py"
    def eval_while(component, env):
        predicate = llist_ref(component, 1)
        body = llist_ref(component, 2)
        while is_truthy(evaluate(predicate, env)):
            result = evaluate(body, env)
            if is_return_value(result):
                return result
        return None

    evaluate_without_while = evaluate

    def evaluate(component, env):
        if is_tagged_llist(component, "while_loop"):
            return eval_while(component, env)
        else:
            return evaluate_without_while(component, env)

    declared_without_while = declared_symbols

    def declared_symbols(component, is_declaration):
        if is_tagged_llist(component, "while_loop"):
            return declared_symbols(llist_ref(component, 2), is_declaration)
        else:
            return declared_without_while(component, is_declaration)

    parse_and_evaluate("""
    sq = 0
    def last_square(n):
        i = 0
        while i < n:
            i = i + 1
            sq = i * i
        return sq

    print(last_square(4))
    print(sq)
    """)
    ```
    ```text
    16
    0
    ```

## 11. Dynamic scoping ★★★

*Skill: see that ONE line of `apply` is what makes scoping lexical.*

Change the evaluator so that a function body is evaluated in an extension of the **caller's** environment instead of the function object's environment. What does this program print, before and after?

```python
x = "global"
def show_x():
    return x
def caller():
    x = "caller"
    return show_x()
print(caller())
print(show_x())
```

??? success "Answer"
    Before (lexical scoping, the normal evaluator):

    ```python title="§4 · --with examples/mce.py"
    parse_and_evaluate("""
    x = "global"
    def show_x():
        return x
    def caller():
        x = "caller"
        return show_x()
    print(caller())
    print(show_x())
    """)
    ```
    ```text
    global
    global
    ```
    After: `apply` needs the caller's environment, so the application case of `evaluate` passes `env` along, and the new frame extends `env` instead of `function_environment(fun)`:

    ```python title="§4 · --with examples/mce.py"
    def dynamic_apply(fun, arguments, env):
        if is_compound_function(fun):
            locals = function_locals(fun)
            globals = function_globals(fun)
            symbols = append(function_parameters(fun), append(locals, globals))
            values = append(arguments,
                            append(map(lambda symbol: "*unassigned*", locals),
                                   map(lambda symbol: "*global*", globals)))
            result = evaluate(function_body(fun), extend_environment(symbols, values, env))
            return return_value_content(result) if is_return_value(result) else None
        else:
            return apply(fun, arguments)

    lexical_evaluate = evaluate

    def evaluate(component, env):
        if is_application(component):
            return dynamic_apply(evaluate(function_expression(component), env),
                                 llist_of_values(arg_expressions(component), env), env)
        else:
            return lexical_evaluate(component, env)

    parse_and_evaluate("""
    x = "global"
    def show_x():
        return x
    def caller():
        x = "caller"
        return show_x()
    print(caller())
    print(show_x())
    """)
    ```
    ```text
    caller
    global
    ```
    With dynamic scoping, `show_x`'s frame extends `caller`'s frame, so `x` is found there. The environment stored in the function object is no longer used at all. That stored environment **is** lexical scoping, and it is what lets a function returned by a maker remember its frame.

## 12. Strict or not? ★★

*Skill: applicative order vs lazy evaluation; strict vs non-strict.*

1. Why does this stop with an error in Python §4?
2. What would it print in a **lazy** evaluator, and why?
3. In the lazy evaluator, are compound functions strict or non-strict in their arguments? And the built-ins?

```python title="§4"
def try_it(a, b):
    return 1 if a == 0 else b

print(try_it(0, 1 / 0))
```

??? success "Answer"
    ```text title="Output"
    ZeroDivisionError at line 4
        print(try_it(0, 1 / 0))
    ZeroDivisionError: division by zero
    sicpfuf hint: check the divisor before dividing, for example with a base case `if n == 0`.
    ```
    1. Python §4 uses **applicative order**: all argument expressions are evaluated before the body, so `1 / 0` is evaluated even though `b` is never used.
    2. 1. With lazy evaluation the argument expressions are passed **unevaluated**, as thunks (expression plus environment). `b`'s thunk is never forced, because the conditional picks the consequent.
    3. Compound functions are **non-strict** in every argument (the argument is evaluated only when needed). Built-ins such as `+`, `/`, `print` and `pair` stay **strict**: `apply` forces all their arguments before calling the underlying implementation.

## 13. A lazy evaluator ★★★

*Skill: thunks, `delay_it`, `force_it`, `actual_value`; memoizing thunks.*

Make `mce.py` lazy: arguments of compound functions are delayed, arguments of built-ins and conditional predicates are forced. Then count how often `noisy()` runs in `twice(noisy())`, with plain and with memoizing thunks.

??? success "Answer"
    ```python title="§4 · --with examples/mce.py"
    def delay_it(exp, env):
        return llist("thunk", exp, env)

    def is_thunk(v):
        return is_tagged_llist(v, "thunk")

    def force_it(v):
        return actual_value(llist_ref(v, 1), llist_ref(v, 2)) if is_thunk(v) else v

    def actual_value(exp, env):
        return force_it(evaluate(exp, env))

    strict_evaluate = evaluate

    def evaluate(component, env):
        if is_application(component):
            fun = actual_value(function_expression(component), env)
            args = arg_expressions(component)
            if is_built_in_function(fun):
                return apply(fun, map(lambda arg: actual_value(arg, env), args))
            else:
                return apply(fun, map(lambda arg: delay_it(arg, env), args))
        elif is_conditional(component):
            if is_truthy(actual_value(conditional_predicate(component), env)):
                return evaluate(conditional_consequent(component), env)
            else:
                return evaluate(conditional_alternative(component), env)
        else:
            return strict_evaluate(component, env)

    program = """
    def try_it(a, b):
        return 1 if a == 0 else b

    def noisy():
        print("running noisy")
        return 5

    def twice(x):
        return x + x

    print(try_it(0, 1 / 0))
    print(twice(noisy()))
    """
    parse_and_evaluate(program)

    def force_it(v):
        if is_tagged_llist(v, "evaluated_thunk"):
            return head(tail(v))
        elif is_thunk(v):
            value = actual_value(llist_ref(v, 1), llist_ref(v, 2))
            set_head(v, "evaluated_thunk")
            set_head(tail(v), value)
            set_tail(tail(v), None)
            return value
        else:
            return v

    print("--- memoizing thunks")
    parse_and_evaluate(program)
    ```
    ```text
    1
    running noisy
    running noisy
    10
    --- memoizing thunks
    1
    running noisy
    10
    ```
    - A **thunk** is `llist("thunk", expression, environment)`: everything needed to evaluate the argument later, in the caller's environment. `force_it` evaluates it; `actual_value` evaluates an expression and forces the result (a name may be bound to a thunk).
    - `try_it` now gives 1: the thunk for `1 / 0` is never forced.
    - Plain thunks are forced **every time** the parameter is used: `x + x` runs `noisy()` twice. The memoizing `force_it` overwrites the thunk with `llist("evaluated_thunk", value)` (dropping the environment), so the second use finds the value: once.
    - Built-in `pair` is still strict, so a recursive "infinite llist" built with it still never stops in this evaluator; defining `pair`, `head` and `tail` as compound functions in the lazy language would make them lazy too.

*In the course: L11B, L12A · SICPy 4.1, 4.2.*
