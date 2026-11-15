---
hide:
  - toc
  - navigation
---

# Visual steppers

Edit the code, choose a model, and follow execution with **Next**, **Back**, or **Play**.

- **E-stepper:** watch frames, bindings, function objects and enclosing-environment arrows change.
  Click a frame or function to inspect it. Zoom the diagram or jump to any event in the history.
- **Substitution stepper:** watch Python §1–§2 expressions reduce, with the changed expression
  highlighted at each step. Compare the previous expression with the current one.

<div id="environment-lab">
  <p>Loading the steppers… JavaScript is needed for the interactive UI.</p>
</div>

The examples open instantly with recorded traces from sicpfuf's interpreter. **Run code** executes
your edits in your browser using the same interpreter and steppers as the command line. The first custom run downloads
the Python runtime; it needs an internet connection and may take a little while. Code stays in your
browser. Use small programs: traces stop at 250 events or 15,000 operations.

Frames shown here are reachable from the current call stack or saved closures. A finished call
can disappear when nothing keeps its frame alive. Empty call frames are omitted, just as in the book.
Each model keeps its own code and current step when you switch between them. Mutation and state
need the environment model; the substitution stepper supports Python §1 and §2.

Continue with [the environment model](book/14-environment-model.md),
[scope and higher-order functions](book/05-higher-order-scope.md), or
[mutation and sharing](book/12-state-mutation.md).
