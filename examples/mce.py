# chapter 4
#
# A METACIRCULAR EVALUATOR: an interpreter for a small Python, written in Python §4.
#
#     python3 -m sicpfuf examples/mce.py
#
# The design and the function names follow the metacircular evaluator of
# "Structure and Interpretation of Computer Programs" (section 4.1), so you can
# hold this file next to the textbook and the lecture slides. The code itself
# was written from scratch for sicpfuf.
#
# THE BIG PICTURE
#
#     program text --parse--> syntax tree --evaluate--> value
#
#     evaluate(component, env)   looks at ONE node of the tree and decides what to do.
#                                For a function application it calls apply.
#     apply(fun, arguments)      runs a function: a built-in one directly, a compound
#                                one by calling evaluate on its body in a NEW frame.
#
# evaluate calls apply, apply calls evaluate: the "evaluate-apply loop".
# Everything else in this file is bookkeeping for those two functions.
#
# WHAT THE EVALUATED LANGUAGE HAS: literals, names, operators, conditional
# expressions and statements, lambda, def, return, assignment, global, nonlocal, pass.
# WHAT IT DOES NOT HAVE (yet): and/or, loops, lists. Adding them is good practice.


# ============================================================ 1. SYNTAX
# parse(text) gives a tree of TAGGED LLISTS: llist(tag, part, part, ...).
# These functions are the only ones that know the positions of the parts.

def is_tagged_llist(component, the_tag):
    return is_pair(component) and head(component) == the_tag

# llist("literal", value)
def is_literal(component):
    return is_tagged_llist(component, "literal")
def literal_value(component):
    return head(tail(component))
def make_literal(value):
    return llist("literal", value)

# llist("name", symbol)
def is_name(component):
    return is_tagged_llist(component, "name")
def symbol_of_name(component):
    return head(tail(component))
def make_name(symbol):
    return llist("name", symbol)

# llist("application", function expression, llist(argument expressions))
def is_application(component):
    return is_tagged_llist(component, "application")
def function_expression(component):
    return llist_ref(component, 1)
def arg_expressions(component):
    return llist_ref(component, 2)
def make_application(fun_expr, arg_exprs):
    return llist("application", fun_expr, arg_exprs)

# llist("unary_operator_combination", operator, operand)
# llist("binary_operator_combination", operator, operand 1, operand 2)
def is_unary_operator_combination(component):
    return is_tagged_llist(component, "unary_operator_combination")
def is_binary_operator_combination(component):
    return is_tagged_llist(component, "binary_operator_combination")
def is_operator_combination(component):
    return (is_unary_operator_combination(component)
            or is_binary_operator_combination(component))
def operator_symbol(component):
    return llist_ref(component, 1)
def first_operand(component):
    return llist_ref(component, 2)
def second_operand(component):
    return llist_ref(component, 3)

# llist("conditional_expression", predicate, consequent, alternative)
# llist("conditional_statement",  predicate, consequent, alternative)
def is_conditional(component):
    return (is_tagged_llist(component, "conditional_expression")
            or is_tagged_llist(component, "conditional_statement"))
def conditional_predicate(component):
    return llist_ref(component, 1)
def conditional_consequent(component):
    return llist_ref(component, 2)
def conditional_alternative(component):
    return llist_ref(component, 3)

# llist("lambda_expression", llist(parameter names), body expression)
def is_lambda_expression(component):
    return is_tagged_llist(component, "lambda_expression")
def lambda_parameter_symbols(component):
    return map(symbol_of_name, llist_ref(component, 1))
def lambda_body(component):
    return llist_ref(component, 2)

# llist("sequence", llist(statements))
def is_sequence(component):
    return is_tagged_llist(component, "sequence")
def sequence_statements(component):
    return head(tail(component))
def first_statement(stmts):
    return head(stmts)
def rest_statements(stmts):
    return tail(stmts)
def is_empty_sequence(stmts):
    return is_none(stmts)
def is_last_statement(stmts):
    return is_none(tail(stmts))

# llist("return_statement", expression)
def is_return_statement(component):
    return is_tagged_llist(component, "return_statement")
def return_expression(component):
    return head(tail(component))
def make_return_statement(expression):
    return llist("return_statement", expression)

# llist("assignment", name, value expression)
def is_assignment(component):
    return is_tagged_llist(component, "assignment")
def assignment_symbol(component):
    return symbol_of_name(llist_ref(component, 1))
def assignment_value_expression(component):
    return llist_ref(component, 2)

# llist("function_definition", name, llist(parameter names), body)
def is_function_definition(component):
    return is_tagged_llist(component, "function_definition")
def function_definition_symbol(component):
    return symbol_of_name(llist_ref(component, 1))
def function_definition_parameter_symbols(component):
    return map(symbol_of_name, llist_ref(component, 2))
def function_definition_body(component):
    return llist_ref(component, 3)

# llist("pass_statement")    llist("global_statement", llist(names))    llist("nonlocal_statement", llist(names))
def is_pass_statement(component):
    return is_tagged_llist(component, "pass_statement")
def is_global_statement(component):
    return is_tagged_llist(component, "global_statement")
def is_nonlocal_statement(component):
    return is_tagged_llist(component, "nonlocal_statement")
def declaration_symbols(component):
    return map(symbol_of_name, head(tail(component)))


# ============================================================ 2. EVALUATE
# One case per kind of component. The ORDER of the cases does not matter
# here, because every component has exactly one tag.

def evaluate(component, env):
    if is_literal(component):
        return literal_value(component)
    elif is_name(component):
        return lookup_symbol_value(symbol_of_name(component), env)
    elif is_application(component):
        return apply(evaluate(function_expression(component), env),
                     llist_of_values(arg_expressions(component), env))
    elif is_operator_combination(component):
        return evaluate(operator_combination_to_application(component), env)
    elif is_conditional(component):
        return eval_conditional(component, env)
    elif is_lambda_expression(component):
        return make_function(lambda_parameter_symbols(component), None, None,
                             make_return_statement(lambda_body(component)), env)
    elif is_sequence(component):
        return eval_sequence(sequence_statements(component), env)
    elif is_return_statement(component):
        return eval_return_statement(component, env)
    elif is_function_definition(component):
        return eval_function_definition(component, env)
    elif (is_pass_statement(component) or is_global_statement(component)
          or is_nonlocal_statement(component)):
        return None
    elif is_assignment(component):
        return eval_assignment(component, env)
    else:
        return error("unknown syntax -- evaluate", component)

# The arguments of an application: each one is evaluated, in the SAME environment.
def llist_of_values(exps, env):
    return map(lambda arg: evaluate(arg, env), exps)

# x + y is treated as the application of a function called "+" to x and y.
# (So the operands are always BOTH evaluated: that is why `and` / `or` need more.)
def operator_combination_to_application(component):
    operator = operator_symbol(component)
    if is_unary_operator_combination(component):
        return make_application(make_name(operator), llist(first_operand(component)))
    else:
        return make_application(make_name(operator),
                                llist(first_operand(component), second_operand(component)))

# "We explain conditionals of the evaluated language with a conditional of OURS."
def eval_conditional(component, env):
    if is_truthy(evaluate(conditional_predicate(component), env)):
        return evaluate(conditional_consequent(component), env)
    else:
        return evaluate(conditional_alternative(component), env)

# Statements run one after the other. As soon as one of them produces a
# RETURN VALUE, the remaining statements are skipped and it is passed upwards.
def eval_sequence(stmts, env):
    if is_empty_sequence(stmts):
        return None
    elif is_last_statement(stmts):
        return evaluate(first_statement(stmts), env)
    else:
        first_value = evaluate(first_statement(stmts), env)
        if is_return_value(first_value):
            return first_value
        else:
            return eval_sequence(rest_statements(stmts), env)

def eval_return_statement(component, env):
    return make_return_value(evaluate(return_expression(component), env))

def eval_assignment(component, env):
    value = evaluate(assignment_value_expression(component), env)
    assign_symbol_value(assignment_symbol(component), value, env)
    return None

# def f(...): ...   makes a function object and assigns it to the name f.
# Which names are LOCAL to the function is decided HERE, once, when the
# definition is evaluated (not when the function is called).
def eval_function_definition(component, env):
    parameters = function_definition_parameter_symbols(component)
    body = function_definition_body(component)
    fun = make_function(parameters, local_variables(parameters, body),
                        global_variables(body), body, env)
    assign_symbol_value(function_definition_symbol(component), fun, env)
    return None


# ============================================================ 3. WHICH NAMES ARE LOCAL?
# A name is local to a function if the body assigns it (name = ... or def name),
# unless it is a parameter or the body says `global name` / `nonlocal name`.
# The scan looks into sequences and into both branches of conditional
# statements, but NOT into the bodies of nested function definitions.

def declared_symbols(component, is_declaration):
    if is_sequence(component):
        return reduce(append, None,
                      map(lambda stmt: declared_symbols(stmt, is_declaration),
                          sequence_statements(component)))
    elif is_conditional(component):
        return append(declared_symbols(conditional_consequent(component), is_declaration),
                      declared_symbols(conditional_alternative(component), is_declaration))
    elif is_declaration(component):
        return target_symbols(component)
    else:
        return None

def target_symbols(component):
    if is_assignment(component):
        return llist(assignment_symbol(component))
    elif is_function_definition(component):
        return llist(function_definition_symbol(component))
    else:
        return declaration_symbols(component)

def assigned_variables(component):
    return declared_symbols(component,
                            lambda c: is_assignment(c) or is_function_definition(c))

def global_variables(component):
    return declared_symbols(component, is_global_statement)

def nonlocal_variables(component):
    return declared_symbols(component, is_nonlocal_statement)

def local_variables(parameters, body):
    excluded = append(parameters, append(global_variables(body), nonlocal_variables(body)))
    return filter(lambda symbol: is_none(member(symbol, excluded)),
                  assigned_variables(body))


# ============================================================ 4. APPLY
# A compound function is called by evaluating its body in a NEW FRAME that
# extends the environment stored in the function object (where it was created).
# The frame binds:   each parameter      to its argument
#                    each local name     to the marker "*unassigned*"
#                    each global name    to the marker "*global*"

def apply(fun, arguments):
    if is_built_in_function(fun):
        return apply_built_in_function(fun, arguments)
    elif is_compound_function(fun):
        locals = function_locals(fun)
        globals = function_globals(fun)
        symbols = append(function_parameters(fun), append(locals, globals))
        values = append(arguments,
                        append(map(lambda symbol: "*unassigned*", locals),
                               map(lambda symbol: "*global*", globals)))
        result = evaluate(function_body(fun),
                          extend_environment(symbols, values, function_environment(fun)))
        return return_value_content(result) if is_return_value(result) else None
    else:
        return error("unknown function type -- apply", fun)


# ============================================================ 5. DATA STRUCTURES OF THE EVALUATOR

# Only True and False may be used as conditions.
def is_truthy(x):
    return x if is_boolean(x) else error("boolean expected, received", x)
def is_falsy(x):
    return not is_truthy(x)

# A function object: the code (parameters, body), the names it treats
# specially, and the environment it was created in.
def make_function(parameters, locals, globals, body, env):
    return llist("compound_function", parameters, locals, globals, body, env)
def is_compound_function(f):
    return is_tagged_llist(f, "compound_function")
def function_parameters(f):
    return llist_ref(f, 1)
def function_locals(f):
    return llist_ref(f, 2)
def function_globals(f):
    return llist_ref(f, 3)
def function_body(f):
    return llist_ref(f, 4)
def function_environment(f):
    return llist_ref(f, 5)

# A return value is wrapped, so that eval_sequence can recognise it.
def make_return_value(content):
    return llist("return_value", content)
def is_return_value(value):
    return is_tagged_llist(value, "return_value")
def return_value_content(value):
    return head(tail(value))

# An ENVIRONMENT is a llist of frames, innermost first.
# A FRAME is a pair: (llist of symbols, llist of their values).
the_empty_environment = None
def first_frame(env):
    return head(env)
def enclosing_environment(env):
    return tail(env)
def make_frame(symbols, values):
    return pair(symbols, values)
def frame_symbols(frame):
    return head(frame)
def frame_values(frame):
    return tail(frame)

def add_binding_to_frame(symbol, val, frame):
    set_head(frame, pair(symbol, frame_symbols(frame)))
    set_tail(frame, pair(val, frame_values(frame)))

def extend_environment(symbols, vals, base_env):
    if length(symbols) == length(vals):
        return pair(make_frame(symbols, vals), base_env)
    elif length(symbols) < length(vals):
        return error("too many arguments supplied", pair(symbols, vals))
    else:
        return error("too few arguments supplied", pair(symbols, vals))

# Look a name up: first frame, then the enclosing ones, outwards.
def lookup_symbol_value(symbol, env):
    def env_loop(env):
        def scan(symbols, vals):
            if is_none(symbols):
                return env_loop(enclosing_environment(env))
            elif symbol == head(symbols):
                if head(vals) == "*global*":
                    return lookup_symbol_value(symbol, the_global_environment)
                else:
                    return head(vals)
            else:
                return scan(tail(symbols), tail(vals))
        if env is the_empty_environment:
            return error("unbound name", symbol)
        else:
            frame = first_frame(env)
            return scan(frame_symbols(frame), frame_values(frame))
    return env_loop(env)

# Assign to a name: change the binding in the first frame that has one.
# At the global frame, a name that has no binding yet GETS one.
def assign_symbol_value(symbol, val, env):
    def scan(symbols, vals):
        if is_none(symbols):
            if env is the_global_environment:
                return add_binding_to_frame(symbol, val, first_frame(env))
            else:
                return assign_symbol_value(symbol, val, enclosing_environment(env))
        elif symbol == head(symbols):
            if head(vals) == "*global*":
                return assign_symbol_value(symbol, val, the_global_environment)
            else:
                return set_head(vals, val)
        else:
            return scan(tail(symbols), tail(vals))
    frame = first_frame(env)
    return scan(frame_symbols(frame), frame_values(frame))


# ============================================================ 6. BUILT-INS AND THE GLOBAL ENVIRONMENT
# A built-in function of the evaluated language is a function of OUR language
# in a wrapper: llist("built_in", implementation).

def is_built_in_function(fun):
    return is_tagged_llist(fun, "built_in")
def built_in_implementation(fun):
    return head(tail(fun))
def apply_built_in_function(fun, arg_llist):
    return apply_in_underlying_python(built_in_implementation(fun), arg_llist)

# Printing a compound function would print the whole environment inside it.
def show(value):
    return ("<compound function>" if is_compound_function(value)
            else "<built-in function>" if is_built_in_function(value)
            else value)

# print(a, b, ...) of the evaluated language: show each value, then print them all.
def print_values(*values):
    shown = [None] * len(values)
    for i in range(len(values)):
        shown[i] = show(values[i])
    return print(*shown)

# To add a built-in: add one line here.
built_in_functions = llist(
    llist("head", head),
    llist("tail", tail),
    llist("pair", pair),
    llist("llist", llist),
    llist("is_none", is_none),
    llist("is_pair", is_pair),
    llist("print", print_values),
    llist("error", error),
    llist("abs", abs),
    llist("math_sqrt", math_sqrt),
    llist("+", lambda x, y: x + y),
    llist("-", lambda x, y: x - y),
    llist("*", lambda x, y: x * y),
    llist("/", lambda x, y: x / y),
    llist("//", lambda x, y: x // y),
    llist("%", lambda x, y: x % y),
    llist("**", lambda x, y: x ** y),
    llist("==", lambda x, y: x == y),
    llist("!=", lambda x, y: x != y),
    llist("<", lambda x, y: x < y),
    llist("<=", lambda x, y: x <= y),
    llist(">", lambda x, y: x > y),
    llist(">=", lambda x, y: x >= y),
    llist("is", lambda x, y: x is y),
    llist("is not", lambda x, y: x is not y),
    llist("not", lambda x: not x),
    llist("-unary", lambda x: -x),
    llist("+unary", lambda x: +x))

built_in_function_symbols = map(lambda f: head(f), built_in_functions)
built_in_function_objects = map(lambda f: llist("built_in", head(tail(f))), built_in_functions)

built_in_constants = llist(llist("math_pi", math_pi), llist("math_e", math_e))
built_in_constant_symbols = map(lambda c: head(c), built_in_constants)
built_in_constant_values = map(lambda c: head(tail(c)), built_in_constants)

# Two frames: the built-ins, and on top of them an (empty) global frame.
def setup_environment():
    built_in_environment = extend_environment(
        append(built_in_function_symbols, built_in_constant_symbols),
        append(built_in_function_objects, built_in_constant_values),
        the_empty_environment)
    return extend_environment(None, None, built_in_environment)

the_global_environment = setup_environment()


# ============================================================ 7. RUNNING IT

def parse_and_evaluate(program):
    return evaluate(parse(program), the_global_environment)

# An interactive loop: type programs for the evaluator, an empty line stops it.
# Like a program file, it shows only what the program itself prints.
def driver_loop(env):
    text = input("M-evaluate input: ")
    if text == "":
        print("evaluator terminated")
    else:
        evaluate(parse(text), env)
        return driver_loop(env)

# driver_loop(the_global_environment)      <- remove the "#" to try it


# DEMO  (when this file is loaded with --with, everything below this line is left out)
parse_and_evaluate("""
def factorial(n):
    return 1 if n == 1 else n * factorial(n - 1)

def make_counter():
    count = 0
    def next():
        nonlocal count
        count = count + 1
        return count
    return next

counter = make_counter()
counter()
print(factorial(5))
print(counter())
print((lambda x, y: pair(x, y))(1, llist(2, 3)))
print(factorial)
""")
