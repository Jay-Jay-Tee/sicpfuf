# One-page sheets

<p class="chapter-goal">Twelve dense pages, one per big topic: the rules, a worked micro-example per rule, an exam recipe and the top traps.</p>

Use them in the last ten days: read one, close it, then do the matching [drills](../../practice/index.md). The [revision plan](../index.md#the-10-day-plan) says which sheet goes with which day.

## Unit 1: functions

| Sheet | What it covers |
|---|---|
| [Substitution model & processes](substitution.md) | the applicative-order rules, how to lay out a trace, deferred operations, recursive vs iterative process, normal order |
| [Orders of growth](growth.md) | Θ, O and Ω in plain words, the recipe for time and space, the table of standard results, `measure` |
| [Scope & higher-order functions](scope-hof.md) | the scoping rules, lambda precedence, functions as arguments and results, currying, `compose` |

## Unit 2: data

| Sheet | What it covers |
|---|---|
| [Pairs, llists & box-and-pointer](llists.md) | box notation, llist notation and diagrams, access paths, the whole §2 library, llist recursion patterns |
| [Trees & CPS](trees-cps.md) | the three-case tree template, count/map/flatten/accumulate, continuations and why CPS is iterative but not Θ(1) space |

## Unit 3: state

| Sheet | What it covers |
|---|---|
| [Streams](streams.md) | stream discipline, the stream library, self-referential streams, `memo_fun`, what gets forced when |
| [The environment model](environment-model.md) | frames, bindings, function objects, the application rule, how to draw a diagram at a marked point |
| [Mutation, lists & loops](mutation-lists-loops.md) | `set_head`/`set_tail`, sharing and aliasing, lists and indices, `while`/`for`, in-place algorithms |
| [Memoization, searching & sorting](memo-search-sort.md) | memo tables (1-D and 2-D), linear and binary search, insertion, selection and merge sort |

## Unit 4: beyond

| Sheet | What it covers |
|---|---|
| [The metacircular evaluator](mce.md) | `parse` shapes, `evaluate` and `apply`, environments as data, return values, how to modify the evaluator |
| [Typed Python §4](types.md) | annotations, function types, `LList[T]`, narrowing with `is_none`, reading checker errors |

## Across all units

| Sheet | What it covers |
|---|---|
| [The 25 classic traps](traps.md) | the mistakes that cost the most marks, each with a tiny program and the fix |

!!! tip "Which sheets to take into a mock paper"
    The real exam's rules on notes were not announced in the material we have. For a mock, allow yourself at most two sheets, chosen BEFORE you see the paper. See [exam mode](../exam-mode.md).
