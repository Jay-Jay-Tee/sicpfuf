# Compatibility and sources checked

Review date: **16 November 2026**.

sicpfuf is an independent study interpreter. Its reference behaviour is Source Academy's
Python implementation, **py-slang**. Differential tests compare output and errors on concrete
programs; they are evidence about those cases, not proof that every program behaves identically.

The runtime reference is pinned at
[`c0a8dfd9`](https://github.com/source-academy/py-slang/tree/c0a8dfd9d6b1c4f6a59d1778e7e7380fa9b9f918).
The frontend's handling of retained frames was inspected at
[`8e8d2f39`](https://github.com/source-academy/frontend/tree/8e8d2f39cad45f8e89292cb116959e840c5467a3).

## Reproducible checks

| Check | Result |
|---|---|
| Generated operators across §1–§4 | 3964/3964 exact output and error kinds |
| Deterministic builtin probes | 4709/4769 exact; differences recorded below |
| Directed syntax/scope probes | 380/396 exact; 12 require the module host and 4 hit an upstream evaluator failure |
| Environment histories | 59 programs, 1424 states; 58 match every compared field, one active-frame display discrepancy |
| Checked documentation | 753 snippets run; 506 eligible plain snippets also compared live with py-slang, no discrepancies |
| Supplied final-paper probes | 44/44 outputs match the reference and independent predictions |

The [conformance harness](https://github.com/Jay-Jay-Tee/sicpfuf/tree/main/tests/conformance)
keeps the fixtures, reference revision, regeneration commands and every discrepancy.
These sweeps compare exact stdout and normalized error kinds. They do not establish exact
wording and columns for all errors. The main differential suite separately checks error lines
and typed diagnostic messages.

The builtin discrepancies are 20 cases where upstream `str` ignores undocumented extra
arguments, and 40 floating-point output differences in `atan`, `atan2`, `erfc`, `gamma`,
`lgamma`, `log1p`, `sinh` and `tan`. Native math and JavaScript/mathjs need not print identical
last digits; some approximation differences are larger than one unit in the last place.
Those differences remain failures in the raw comparison report. sicpfuf keeps the documented
`str(x)` interface. Four `assert` probes encounter an upstream evaluator crash; twelve imports
cannot be assessed by a headless CSE oracle without its Conductor module host.

A separate zero-base probe also exposes an upstream complex-power quirk: `0j ** 0`
returns `0j` there. sicpfuf keeps the zero-exponent result `(1+0j)`. The generated
operator universe above uses a nonzero complex sample, so its perfect match does
not include this separate discrepancy.
Complex NaN text also differs: sicpfuf prints Python's `(nan+nanj)` where the
reference prints `(NaNNaNj)`. Non-finite complex arithmetic is handled without
leaking a native math exception.

## Official language specifications

This review compared chapter boundaries, syntax restrictions, operator rules and library
interfaces with the official specifications:

| Language | Main addition | Reference |
|---|---|---|
| Python §1 | names, functions, conditionals, lexical scope and applicative order | [2026 specification](https://docs.sourceacademy.org/python/python_1.pdf) |
| Python §2 | pairs and the linked-list library | [2026 specification](https://docs.sourceacademy.org/python/python_2.pdf) |
| Python §3 | state, native lists, loops and streams | [2026 specification](https://docs.sourceacademy.org/python/python_3.pdf) |
| Python §4 | `parse`, `tokenize`, `apply_in_underlying_python` | [2026 specification](https://docs.sourceacademy.org/python/python_4.pdf) |

Regression cases exercise chapter-specific rejection, scope and unassigned names, booleans,
arithmetic, pair/list operations, tail calls, streams and evaluator support. See the
[language](language.md) and [library](library.md) references for the usable interface.
If a published summary and a concrete py-slang result appear to disagree, reproduce the
program in Source Academy and record the discrepancy rather than silently changing the language.

## Steppers

The browser and terminal E-steppers now rewrite the remaining program according to the
[environment-stepper rules](https://github.com/source-academy/py-slang/blob/c0a8dfd9d6b1c4f6a59d1778e7e7380fa9b9f918/docs/specs/python_4_estepper_rules.tex).
Each contraction has a before and after state. **Program** shows that remaining code;
**Diagram** shows frames, functions and lists. Repeated object numbers identify shared objects,
including cycles. Library applications are atomic. Empty call frames are omitted, and tail
calls replace their caller's environment block.

The 59-program oracle check compares the program tree, bindings, lexical parents, object
identity, list contents, output and reachability at every state. It reconstructs the
reference frontend's retained history before comparing garbage. Node IDs, source formatting,
tooltips, explanation wording and pixel layout are outside this comparison.

One reference display discrepancy remains intentional: while reducing the RHS function call
in `a[f(0)] = f(1)`, upstream labels Global as active because its display visits the target first.
sicpfuf labels the function frame that is actually executing. All other state fields in that
history are compared too.

Unreachable frames and objects stay visible in grey, or labelled in the terminal. A returned
frame stays reachable when a live closure retains it. There is no “clear unreachable” control.
The standalone `show_env()` snapshot shows reachable frames only, and still renders pairs/lists
as text inside frames. The compact `--estep` command remains an environment **event log**;
it does not print the UI's complete reduction states.

The substitution recorder uses applicative order in Python §1–§2 and has no normal-order mode.
Eight scope probes match both the reference runtime and its actual substitution
reducer; local binders are renamed when necessary to preserve lexical scope.
It still differs from the official whole-program substitution reducer: it presents expressions
and collapses some declaration/library steps. Its step numbering must not be treated as an
exact reproduction of Source Academy's. The canonical
[substitution specification](https://github.com/source-academy/py-slang/blob/c0a8dfd9d6b1c4f6a59d1778e7e7380fa9b9f918/docs/specs/python_2_stepper_rules.tex)
is available in the checked reference; a failed PDF download does not prevent inspecting it.

## Modules

The [official module documentation](https://source-academy.github.io/modules/documentation/)
includes more browser and hardware functionality than sicpfuf implements. Supporting an import
does not imply support for every function in the corresponding browser module.

| Module | Implemented here | Limits |
|---|---|---|
| [rune](https://source-academy.github.io/modules/documentation/modules/rune.html) | static 2-D primitives, transformations, composition, named/RGB colours, terminal previews and SVG export | simplified geometry; no `colour_with_hue`, downloaded images, animation or full 3-D renderer; `anaglyph`/`hollusion` use the static preview |
| [curve](https://source-academy.github.io/modules/documentation/modules/curve.html) | 2-D points, curve functions, transformations and sampled drawings | no complete 3-D or animated browser renderer |
| [sound](https://source-academy.github.io/modules/documentation/modules/sound.html) | wave construction, composition, envelopes, instruments and WAV export | approximated synthesis; no browser audio playback engine |
| [repeat](https://source-academy.github.io/modules/documentation/modules/repeat.html) | `repeat_apply(f, n, x)`, `repeat(f, n)`, `twice(f)`, `thrice(f)` | intended for valid functions and nonnegative integer repetition counts |

Terminal rune colour is automatic for terminal output. Redirected output stays plain so text
files and regression snapshots contain no escape sequences. `NO_COLOR` or `TERM=dumb` disables
terminal colour. SVG export keeps the actual colours.

`math_fma` uses the reference runtime's compensated multiply-add consistently across supported
Python versions. It returns a float and preserves the extra precision lost by plain `x*y+z`.
Extreme-value behaviour follows py-slang; it can differ from a native hardware fused operation.

## Python §4 Typed

The typed-related test set has 103 cases, including untyped rejection of the extra syntax.
Its oracle runs py-slang's actual checker. This is not a complete reimplementation of Pyright.
Known limits include unchecked imported-module types, unchecked evaluator-support builtins,
no `Callable[..., T]` ellipsis syntax, and some wording differences in difficult generic
inference diagnostics. Columns are not part of the differential comparison.

This comparison uses the canonical
[Python §4 Typed specification](https://github.com/source-academy/py-slang/blob/c0a8dfd9d6b1c4f6a59d1778e7e7380fa9b9f918/docs/specs/python_4_typed.tex)
and its included grammar/type rules, together with py-slang's real checker. The reference
checkout has 48 TeX specification files, including both stepper rule sets. Having those files
available is not a claim that every possible typed program is covered by the tests.

`--typed` selects §4, overriding a file's chapter header. Other explicit chapter flags and
`--subst` are rejected with it. The interactive prompt has no typed mode; the CLI reports this
rather than silently starting an untyped session.

## Local UI and native Python

The UI runs a fresh local subprocess for each trace. Default limits are 400 states, 15,000 interpreter
operations and 10 seconds. Optional program input supplies one line per `input()` call;
browser “Cancel” input is not emulated. `--typed` is supported in the §4 environment UI and
terminal stepper; errors are reported before execution. Other CLI x-ray flags remain separate.
Use `--max-steps 1000` to change the state limit (2–5000), or press + in the terminal to
increase it and retrace. The operation and time limits still apply.
Retained environment history is also bounded to 250,000 frame/heap entries across its snapshots.
Finer reductions produce longer histories than the old event recorder; increase the limit for
longer examples. Large traces can still hit the history or execution-time bound.

The [website stepper](../playground.md) uses the same UI and interpreter inside a browser worker.
Examples have build-checked histories, so opening one needs no Python download. Edited code
loads Pyodide on first use; Stop terminates its worker. This is separate from the local UI's
subprocess backend. The website allows up to 60 seconds to load Python and 10 seconds to trace.

`--tui` is a terminal-text view of the same histories, with reload and keyboard navigation.
Its frames are text rather than the graphical SVG view available in `--ui`.

Native Python differs from the course language in truthiness, available syntax and tail calls;
see [the final chapter](../book/20-big-picture.md). The [course map](../book/course-map.md)
separately records which lecture, sheet and assessment material was available for review.

## Supplied finals and course coverage

All 73 questions in the three supplied finals have a private evidence record: execution probes,
analytic review, or both. The 44 executable probes include exact supplied programs and original
candidate implementations, with separate reasoning for complexity, resources and compiler
chains. No official final-answer PDFs were supplied. Some supplied versions are repaired or
adapted, and one question has equivalent alternatives, so these are independent checks rather
than certification of an official historical key. Paper text, extracted programs and the answer
ledger remain outside the public repository.

The November 16 mission/practice export contains 19 missions (68 tasks), four distinct PA
practice papers (38 questions), and two PA2 solution versions. Its 386 PA practice test programs,
run with the saved editor code and without filling missing assessment helpers, agree between
sicpfuf and the pinned CSE reference on stdout and normalized error kind. This includes 72
programs that stop with errors; 314 produce the exported final-line result. A long stream case
needed a 50-million-step reference budget. No parity of evaluation counts, official scores,
hidden-test results or mission graphics is inferred. Extracted source, raw results and the
comparison ledger remain in the private assessment cache. The saved average program also
fails a separate non-integer-mean probe in both interpreters despite passing its supplied tests.

The textbook's [course map](../book/course-map.md) records the available lectures, studios,
reflections, missions and practice papers, with remaining topic and source gaps. It does not
establish complete coverage of unseen sheets, every slide figure, or full official worked
solutions. Browser DOM/SVG and actual Pyodide histories are tested;
pixel layout has not been verified in a live browser in this environment.
