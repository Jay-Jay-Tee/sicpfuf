# Drills

<p class="chapter-goal">Short problem sets, one per topic, with checked answers. Do them on paper, the way the exam asks.</p>

## How to use them

1. **Pick one page** for the topic you are weakest at. Each page has about ten problems, easiest (★) first, hardest (★★★) last.
2. **Answer on paper first.** Write the output, the trace, the Θ or the function before you open the answer. The exam gives you no computer, and reading an answer feels like knowing it when you do not.
3. **Then open `Answer`** and compare. Every program and every output in the answers was run by sicpfuf, so the outputs are exact.
4. **Read the "why"**, even when you were right. It names the rule the problem tests; that rule is what you will need on a different problem.
5. **When you were wrong, run it yourself.** Copy the program into a file and run it with the x-ray tools: `--subst` for the substitution model, `trace(f, ...)` for call trees, `measure(f, ...)` for time and space, `draw_data(x)` for box-and-pointer diagrams. Change one thing and predict again.

Each problem says the **skill** it trains, so you can skip what you already know. A ★ problem should take a minute or two; a ★★★ problem is exam-hard.

## The pages

**Unit 1: Functions** (Python §1)

| Page | What you practise | Lectures |
|---|---|---|
| [Elements & conditionals](01-elements.md) | predict outputs, §1's strict rules, small functions | L1A |
| [Substitution & processes](02-substitution-processes.md) | substitution traces, recursive vs iterative, converting, applicative vs normal order | L2A |
| [Orders of growth](03-orders-of-growth.md) | Θ of time and space, tightest bounds, log n | L2B |
| [Higher-order functions & scope](04-hof-scope.md) | which declaration a name refers to, makers, compose, lambda precedence, `and`/`or` | L3A, L3B |

**Unit 2: Data** (Python §2)

| Page | What you practise | Lectures |
|---|---|---|
| [Pairs, llists & box-and-pointer](05-llists-box-pointer.md) | diagrams, box and llist notation, access paths, ADTs | L4A |
| [llist processing](06-llist-processing.md) | map/filter/reduce, recursion on llists, cost of append | L5A |
| [Trees & CPS](07-trees-cps.md) | tree recursion, CPS, order of continuations, space | L5B |
| [Sorting, symbolic data & streams I](08-sorting-symbolic-streams.md) | sorts on llists, BSTs, tagged-llist evaluators, streams by hand | L6A, L7B |

**Unit 3: State** (Python §3)

| Page | What you practise | Lectures |
|---|---|---|
| [State & mutation](09-state-mutation.md) | reassignment, `set_head`/`set_tail`, sharing | L8A |
| [Lists & loops](10-lists-loops.md) | lists, `while` and `for` loops | L8A, L9B |
| [The environment model](11-environment-model.md) | frames, bindings, function objects, environment diagrams | L9A |
| [Memoization, searching & sorting](12-memo-search-sort.md) | memoized functions, binary search, sorts on lists | L10A |

**Unit 4: Beyond** (Python §3, §4)

| Page | What you practise | Lectures |
|---|---|---|
| [Streams II](13-streams-ii.md) | stream library, infinite streams, memoized streams | L11A |
| [The metacircular evaluator](14-mce.md) | `parse`, `evaluate`, `apply`, changing the evaluator | L11B, L12A |
| [Typed Python §4](15-types.md) | type annotations and the type checker | L13A |

!!! tip "A routine for the last week"
    One page a day is enough. Do the ★★ and ★★★ problems of the units you find hardest, and redo every problem you got wrong two days later, without looking.
