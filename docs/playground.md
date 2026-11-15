---
hide:
  - toc
  - navigation
---

# Visual stepper

Choose an example or edit the code. Step through **environments** or **substitution**,
inspect bindings, and zoom the diagram. Python §4 **Typed** checks annotations before running.
Unreachable frames and functions stay visible in grey. A returned frame retained by a live
closure stays reachable. The E-stepper shows a **before** and **after** state for each reduction.
Choose **Program** to follow the remaining code, or **Diagram** to inspect frames, functions and
shared lists. Matching object numbers refer to the same object, including cycles.

<iframe class="stepper-frame" src="../assets/stepper/index.html" title="sicpfuf visual stepper" loading="eager"></iframe>

<a class="stepper-fullscreen" href="../assets/stepper/index.html" target="_blank" rel="noopener">Open the stepper in a full tab ↗</a>

Examples are ready immediately. Running edited code downloads Python on first use and executes
in your browser; **Stop** cancels a run. Supply one line per `input()` call under **Program input**.
Traces stop at 400 states or 15,000 interpreter operations. Custom runs have a 10-second execution
limit; the first Python download can take longer. Substitution supports Python §1–§2.

For the same interface offline, use the [built-in UI](reference/xray.md) from your installation.
The [compatibility review](reference/compatibility.md) records the reference checks and known differences.
