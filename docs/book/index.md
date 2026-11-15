# The Book: start here

Start with the **[course map](course-map.md)** to connect every supplied lecture, studio and
reflection to a chapter and practice route. The **[applied-patterns workshop](21-applied-patterns.md)**
builds on the core chapters, and the **[past-paper routes](../finals/past-papers.md)** connect
the three supplied finals to the relevant skills. The map also records missing material.

<p class="chapter-goal">An easy textbook for the whole course, one chapter per lecture, where every program really runs.</p>

!!! abstract "The big idea, in plain words"
    The lectures move fast and the textbook (SICPy) is long. This book walks the same road in small steps.
    Each chapter takes one lecture, explains it in plain words, and backs every claim with a program
    you can run. If a chapter says "this prints 6", a machine has checked that it prints 6.

## Who it is for

- You are taking the course and the final is close.
- You followed some lectures but lost the thread somewhere, maybe at orders of growth, maybe at the
  environment model, maybe at the evaluator.
- You learn better from small examples than from long explanations.

You do not need to read in order. Every chapter starts from what the lecture assumes and says at the
bottom where it sits in the course. If you only have a few days, read the chapter for the topic that
scares you most, then do its "Check yourself" questions.

## How a chapter is built

Every chapter has the same parts, so you always know where to look.

| Part | What it gives you |
|---|---|
| **The big idea** | The whole chapter in one everyday picture, at the very top. |
| **Short sections** | One idea each, with a small program and its real output. |
| **X-ray boxes** | The same program seen through a sicpfuf tool: the substitution model step by step, a call tree, a time and space count, an environment diagram. They are folded; open them when you want to see inside. |
| **Traps** | The classic mistakes, each with the error you would really get. |
| **Python §N vs real Python** | Where the course language and the Python on your laptop disagree. |
| **Takeaways** | Five to eight lines to reread the night before the exam. |
| **Check yourself** | Short questions; each answer is folded under a toggle, and every program in an answer is checked. |

Here is what a program and its output look like. The title says which chapter of the language
(Python §1 to §4) runs it:

```python title="§1"
def double(x):
    return 2 * x

print(double(21))
```
```text title="Output"
42
```

And here is an x-ray box, folded the way you will meet them:

??? example "X-ray: `--subst` shows the substitution model"
    ```python title="§1 · --subst"
    def double(x):
        return 2 * x

    double(3 + 4)
    ```
    ```text title="Output"
    double(3 + 4)
    -> double(7)
    -> 2 * 7
    -> 14

    ```

## Run the programs yourself

You need Python 3.9 or newer and a copy of sicpfuf (see [Getting started](../start.md)). Save a
program in a file and run it from the `sicpfuf` folder:

```sh
python3 -m sicpfuf my_program.py -v 1            # run as Python §1
python3 -m sicpfuf my_program.py -v 1 --subst    # the substitution model, step by step
python3 -m sicpfuf my_program.py -v 1 --trace fib  # the call tree of fib
python3 -m sicpfuf my_program.py -v 3 --env      # the environment diagram at the end
python3 -m sicpfuf -v 2                          # an interactive prompt
```

Use the chapter number in the title of a program as the `-v` number. Change the programs, break them
on purpose, and read the error messages: sicpfuf adds a hint to every error.

!!! tip "Three builtins that only sicpfuf has"
    `trace(f, args...)` draws the call tree of one application, `measure(f, args...)` counts time and
    space, and `show_env()` draws the environment diagram at that moment. They work in every chapter.
    The course's own playground does not have them, so do not use them in an exam answer.

## Contents

### Unit 1 · Functions (Python §1)

1. [Elements of programming](01-elements.md)
2. [Functional abstraction with runes](02-runes.md)
3. [The substitution model and recursion](03-substitution-recursion.md)
4. [Orders of growth](04-orders-of-growth.md)
5. [Higher-order functions and scope](05-higher-order-scope.md)
6. [Curves, sounds and logical operators](06-curves-sound.md)

### Unit 2 · Data (Python §2)

7. [Pairs, llists and data abstraction](07-data-abstraction.md)
8. [Processing llists: map, filter, reduce](08-llist-processing.md)
9. [Trees and continuation-passing style](09-trees-cps.md)
10. [Sorting and symbolic processing](10-sorting-symbolic.md)
11. [Streams: delayed evaluation](11-streams.md)

### Unit 3 · State (Python §3)

12. [State and mutable data](12-state-mutation.md)
13. [Lists and loops](13-lists-loops.md)
14. [The environment model](14-environment-model.md)
15. [Searching, sorting and memoization](15-search-sort-memo.md)
16. [Streams II: infinite and memoized](16-streams-ii.md)

### Unit 4 · Beyond (Python §4)

17. [The metacircular evaluator](17-mce.md)
18. [Evaluator II: functions, names and laziness](18-mce-lazy.md)
19. [Types and objects](19-types-objects.md)
20. [The big picture: Python §4 vs real Python](20-big-picture.md)

### Look things up

- [Glossary](glossary.md): every course word, in one line each.

!!! note "This is not the official material"
    This book is written by a student, in its own words, with its own examples. It follows the order
    and the words of the lectures and the textbook (SICPy), but it does not replace them. When the two
    disagree on a name, this book uses the lectures' name, because that is what you will run.
