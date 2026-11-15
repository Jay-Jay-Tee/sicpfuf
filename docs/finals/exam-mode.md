# Exam mode

<div id="exam-timer" data-minutes="120"></div>

<p class="chapter-goal">Sit a mock paper like the real thing: a clock, paper and pen, no running code, then mark yourself honestly.</p>

## How the mock papers work

Each mock paper is one page with a clock like the one at the top of this page. The clock is set to 120 minutes, the length of the final.

1. Press **Start 120 min**. From now on every solution on the page is hidden.
2. Work on paper. The page shows only the questions.
3. When the time is up, the clock turns red and counts the minutes you overran. Finish your sentence and stop.
4. Press **Stop and show solutions**. The solutions come back, and you mark your own paper.

The clock keeps running if you reload the page or leave it, so a quick look at another page does not reset it (closing the browser tab does).

Try it on this sample. Start the clock above: the solution below disappears. Stop it: the solution comes back.

**Sample question (2 marks).** What does this program print?

```python
def apply_n(f, n, x):
    return x if n == 0 else apply_n(f, n - 1, f(x))

print(apply_n(lambda y: y * 3, 3, 1))
```

??? solution "Solution"
    ```python title="§1"
    def apply_n(f, n, x):
        return x if n == 0 else apply_n(f, n - 1, f(x))

    print(apply_n(lambda y: y * 3, 3, 1))
    ```
    ```text
    27
    ```
    `f` is applied three times, starting from 1: 3, 9, 27. Full marks only for exactly `27`. (`f` is applied BEFORE the recursive call, so the process is iterative.)

## The papers

| Paper | What it is like |
|---|---|
| [Mock 1](mock-1.md) | A balanced paper over all four units, the best first try. |
| [Mock 2](mock-2.md) | Heavier on state: the environment model, mutation and streams. |
| [Mock 3](mock-3.md) | The hardest: heavier on the metacircular evaluator, CPS and program design. |

Do them in this order, on the days the [revision plan](index.md#the-10-day-plan) gives. Keep at least one day between two papers so you can fix what the first one showed.

## Rules to simulate

The rules below copy what a real sit-in paper feels like. Breaking them makes the score meaningless.

1. **One sitting, 120 minutes.** Phone in another room. No breaks you would not get in the hall.
2. **Closed book**, except the sheets you allow yourself. Choose them BEFORE you open the paper (we suggest at most two of the [one-page sheets](sheets/index.md), printed or handwritten). The material we have does not say what the real final allows; if the course announces a notes rule, copy it exactly.
3. **Paper and pen only.** No sicpfuf, no editor, no browser tabs while the clock runs. Programs are written by hand, diagrams drawn by hand.
4. **Library declarations are given.** The real paper supplies the declarations of library functions it uses in an appendix. Each mock has the same; use only what it lists plus the language itself.
5. **Write for a reader.** Full marks need a solution that is correct, reasonably efficient and clearly communicated. Name things well, keep it simple, and add one line of explanation where the idea is not obvious.

## After the clock: marking yourself

Mark with a different colour pen. Then, and only then, type your answers into sicpfuf and run them: a program that does not run is a program that does not work.

```sh
python3 -m sicpfuf my_answer.py -v 2
python3 -m sicpfuf my_answer.py -v 3 --env      # check your environment diagram
python3 -m sicpfuf my_answer.py -v 2 --subst    # check your trace
```

### What earns partial credit

The real marking scheme is not published. This guide follows the course's stated idea (correct, reasonably efficient, clear) and how written papers in this style are usually marked. Be strict with yourself: when in doubt, take the lower mark.

**"Write a function" questions** (split the marks roughly like this):

| Part | Share | You earn it when |
|---|---|---|
| Approach | about 40% | the plan is right and visible: the right recursion or loop shape, the right library functions, a sensible helper |
| Base cases | about 20% | every base case is there and returns the right value (empty llist, n = 0, one element) |
| Step | about 30% | the recursive or loop step is correct, including the order of arguments and what is returned |
| Quality | about 10% | no needless Θ(n²) (no `append` or `length` inside a loop over the same llist), clear names, no dead code |

A program that "would work in full Python" but breaks a Python §N rule (reassignment in §2, `if xs:`, `xs.append`) loses the step marks for that line. A solution that is right but much slower than needed usually loses the quality share and sometimes more.

**"What does it print?" and tracing questions:** the output must be exact (brackets, `None`, quotes, line breaks). Lines that are right before the first mistake usually still count. A trace earns marks for the right shape (deferred operations visible, one rewrite per line) even if an arithmetic slip creeps in.

**Order of growth questions:** the Θ answer and its one-line reason are usually separate marks. A correct but loose bound (O(n²) for a Θ(n) function) earns little. Forgetting to say what n is can cost the mark.

**Diagrams** (box-and-pointer, environment): give yourself one point per correct element and scale to the marks:

- box-and-pointer: right number of boxes, right values inside, every arrow to the right box, shared boxes drawn once, `None` slashes;
- environment diagram: every frame that should exist at the marked point, correct bindings (including unassigned ones), each frame's enclosing-environment arrow, each function object as two circles with the right environment pointer.

Draw neatly: an arrow that might point at two boxes is marked as wrong.

**Explain questions** ("why is this process iterative?"): one mark for the right claim, one for the reason in the course's words ("no deferred operations: the recursive call is the whole return expression").

### Keep a log

After each paper, write one line per question: marks, and the topic of every lost mark. Find that topic in the [topic checklist](checklist.md), untick it, and redo it with its sheet and the [drills](../practice/index.md) the next day.

| Paper | Date | Score | Lost marks on |
|---|---|---|---|
| Mock 1 | | | |
| Mock 2 | | | |
| Mock 3 | | | |
