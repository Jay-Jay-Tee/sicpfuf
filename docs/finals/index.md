# Finals kit

Have the supplied previous-year papers? Use the **[past-paper study routes](past-papers.md)**
to find the chapters and drills for each question group. For lectures, studios and reflections,
start at the **[course map](../book/course-map.md)**.

<p class="chapter-goal">Ten days to the final: what is on it, what to do each day, how to check yourself, and how to spend the two hours.</p>

!!! abstract "The kit in one breath"
    A [topic checklist](checklist.md) of every examinable skill, twelve [one-page sheets](sheets/index.md), the [drills](../practice/index.md), three timed mock papers in [exam mode](exam-mode.md), and the [easy textbook](../book/index.md) for anything that still feels shaky. Follow the plan below and you will have revised everything twice and sat three full papers by Tuesday night.

## What is on the exam

As far as the course has told us:

| | |
|---|---|
| **When** | Wednesday 25 November 2026, 9:00 to 11:00 |
| **How long** | 2 hours, one paper |
| **Scope** | all core material: lectures, paths, reflections, studios and missions, Units 1 to 4 |
| **Library functions** | the declarations of library functions used in the questions are supplied (in an appendix or in the question itself): you must be able to read and use them, not recite them |
| **Marks** | full marks need a solution that is correct, reasonably efficient AND communicates the computational process clearly. "Keep it simple." |
| **Format** | not described in the material. Expect the skills of the reading and programming assessments: predict output, trace, state orders of growth, draw diagrams, write and modify functions |

The skills the course returned to most often, roughly in order: environment diagrams; substitution traces and recursive vs iterative processes; orders of growth in time and space; map/filter/reduce; box-and-pointer diagrams; higher-order functions; scope; streams. They are starred (★) in the [checklist](checklist.md).

## The 10-day plan

Each day has the same shape: **read** the sheets for the day (30 to 45 minutes), **tick** the matching part of the checklist on paper, **drill** what you could not tick, then **check** your answers with sicpfuf. Mock days follow the [exam mode](exam-mode.md) rules: start at 9:00 if you can, so your brain gets used to the real time slot.

| Day | Date | Topic | Sheets | Checklist | Then |
|---|---|---|---|---|---|
| 1 | Sun 15 Nov | Substitution, processes, orders of growth | [substitution](sheets/substitution.md), [growth](sheets/growth.md) | L1A to L2B | drills on substitution and orders of growth |
| 2 | Mon 16 Nov | Scope, higher-order functions; pairs and llists | [scope-hof](sheets/scope-hof.md), [llists](sheets/llists.md) | L3A to L5A | drills on HOF and scope, llists and box-and-pointer |
| 3 | Tue 17 Nov | Trees, CPS, sorting on llists, symbolic data, streams I | [trees-cps](sheets/trees-cps.md), [streams](sheets/streams.md) (first half) | L5B to L7B | redo every Unit 2 line you could not tick |
| 4 | Wed 18 Nov | **[Mock 1](mock-1.md)**, then mark it | [traps](sheets/traps.md) after marking | untick what you lost | log the lost topics; fix the two worst today |
| 5 | Thu 19 Nov | Environment model; mutation, lists and loops | [environment-model](sheets/environment-model.md), [mutation-lists-loops](sheets/mutation-lists-loops.md) | L8A to L9B | draw three environment diagrams, check each with `--env` |
| 6 | Fri 20 Nov | Memoization, searching and sorting; streams II | [memo-search-sort](sheets/memo-search-sort.md), [streams](sheets/streams.md) | L10A, L11A | drills on memoization and streams |
| 7 | Sat 21 Nov | **[Mock 2](mock-2.md)**, then mark it | the sheets of your lost topics | untick what you lost | redo every lost question from scratch |
| 8 | Sun 22 Nov | The metacircular evaluator; types | [mce](sheets/mce.md), [types](sheets/types.md) | L11B to L13B | modify the evaluator twice (a new operator, a changed rule) |
| 9 | Mon 23 Nov | **[Mock 3](mock-3.md)**, then mark it | the sheets of your lost topics | untick what you lost | fix the lost topics |
| 10 | Tue 24 Nov | Light review | [traps](sheets/traps.md), then any two sheets | every unticked ★ line | stop by 21:00, pack, sleep |

!!! tip "If you are behind"
    Never skip a mock: a marked mock tells you more than another evening of reading. Drop the unstarred checklist lines instead, and do the ★ ones.

!!! warning "Do not cram on Day 10"
    The night before is for the traps sheet, your mock log and sleep. A tired brain makes exactly the slips the [traps](sheets/traps.md) list.

## Checking yourself with sicpfuf

After you answer on paper, let sicpfuf check you. Every tool shows the course's own model of the program, so you can compare it with what you wrote line by line.

| You wrote on paper | Check it with |
|---|---|
| a substitution trace | `python3 -m sicpfuf answer.py -v 1 --subst` |
| "recursive or iterative process" | `trace(f, args...)` inside the program: `→` waits (deferred work), `↻` is a tail call |
| an order of growth | `measure(f, n)` and `measure(f, 2 * n)`: steps × 2 is linear, × 4 quadratic |
| a box-and-pointer diagram | `draw_data(x)` |
| an environment diagram at a marked point | put `show_env()` at that point, or run with `--env` (at the end) or `--estep` (every step) |
| an evaluator change | `python3 -m sicpfuf answer.py --with examples/mce.py` |
| "what does it print / which error" | run it as the right chapter with `-v N`: §2 rejects what §3 accepts |

One program, three checks at once: the printed value, the diagram and the cost.

```python title="§2"
def count_down(n):
    return None if n == 0 else pair(n, count_down(n - 1))

xs = count_down(3)
print(xs)
draw_data(xs)
measure(count_down, 100)
```
```text title="Output"
[3, [2, [1, None]]]
[3|•]-->[2|•]-->[1|/]
[measure] count_down(100): 101 calls, 1,306 steps, at most 101 waiting at once
```

Two rules for self-checking:

1. **Paper first, tool second.** If you run the program before you predict, you learn nothing about what you would have written in the hall.
2. **Write down why you were wrong.** "Forgot that `reduce` folds from the right" is a line for your mock log and the next day's work.

## Exam-day tactics

### Before you start writing

1. **Read the whole paper** (about 5 minutes). Mark each question with a budget in minutes.
2. **Read the appendix of library declarations.** Note argument orders (`reduce(f, initial, xs)`, `llist_ref(xs, n)`) and whether a function is defined slightly differently from what you remember. The appendix wins.
3. **Start with the question you are surest of.** Easy marks first calm you down and bank time.

### Time per mark

Your budget is about 110 minutes of writing for the whole paper, keeping 10 minutes for checking. Divide by the total marks: for a 100-mark paper, about **1 minute per mark**, so a 6-mark question gets 6 minutes. When a question runs over its budget by half, write down what you have, leave space, and move on. Come back at the end.

### Partial credit

- **Write something for every part.** A correct base case, the right shape of the recursion or a correct Θ with its reason all earn marks on their own.
- **State the plan in one line** if you cannot finish: "recurse on the tail, keep the head when `pred` holds". The marker can give method marks only for what is on the paper.
- **Name helpers well** and say what they return. Clear code is part of the marks.
- **Do not cross out a half-right answer** until the new one is better.

### Diagrams, neatly

- **Box-and-pointer:** draw the boxes first, in a row, with space between them. Then the values. Then the arrows, each starting at a dot inside a half and ending ON the box it points to. A slash for `None`. Shared boxes once.
- **Environment diagrams:** global frame at the top, each new frame below, labelled (`E1`, `E2`, or the function's name). Write every binding as `name: value`; leave an unassigned local as `name:` with nothing after it. When a value changes, strike the old one with ONE line and write the new one after it. Function objects as two circles outside the frames: one arrow to the parameters and body, one to the frame it was created in. Pairs and lists outside frames, with arrows.
- Use a pencil for diagrams if allowed, and draw a rough sketch in the margin first if the structure is big.

### The last 10 minutes

Check, in this order: every function has a base case and returns (not prints) its result; no §1/§2 reassignment; every condition is a boolean; `reduce` arguments in the right order; `stream_tail` not `tail` on streams; every Θ answer says what n is.

## Where to go next

- [Topic checklist](checklist.md): every skill, in course order.
- [One-page sheets](sheets/index.md): the rules, compressed.
- [Exam mode](exam-mode.md): the timed mocks and how to mark them.
- [Drills](../practice/index.md): practice problems by topic, with checked answers.
- [The book](../book/index.md): the full, easy explanation of each topic.
