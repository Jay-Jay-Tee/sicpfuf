# Compatibility and sources checked

Review date: **15 November 2026**.

sicpfuf is an independent study interpreter. Its reference behaviour is Source Academy's
Python implementation, **py-slang**. Differential tests compare output and errors on concrete
programs; they are evidence about those cases, not proof that every program behaves identically.

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

The [official environment-stepper specification](https://docs.sourceacademy.org/python/python_4_estepper.pdf)
defines individual reductions with frames and shared objects. sicpfuf instead records environment
events: definitions, calls, lookups across frames, assignments, mutations and returns. One event
is not necessarily one expression reduction. Its snapshots omit unreachable frames; they do
not retain grey garbage with a “clear unreachable” control. See the
[official guide](https://docs.sourceacademy.org/python/e-stepper/) when comparing interfaces.

The substitution stepper uses applicative order in Python §1–§2 and has no normal-order mode.
The public Python §2 stepper PDF could not be retrieved during this review, so full rule-by-rule
conformance to it is not established.

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

A separate public Python Typed PDF could not be retrieved. This comparison uses the available
py-slang implementation and course material. The JavaScript **Source §4 Typed** specification
is not a substitute for Python §4 Typed.

## Local UI and native Python

The UI runs a fresh local subprocess for each trace. Default limits are 400 events, 15,000 interpreter
operations and 10 seconds. Optional program input supplies one line per `input()` call;
browser “Cancel” input is not emulated. `--typed` is supported in the §4 environment UI and
terminal stepper; errors are reported before execution. Other CLI x-ray flags remain separate.
Use `--max-steps 1000` to change the event limit (2–5000), or press + in the terminal to
increase it and retrace. The operation and time limits still apply.

`--tui` is a terminal-text view of the same histories, with reload and keyboard navigation.
Its frames are text rather than the graphical SVG view available in `--ui`.

Native Python differs from the course language in truthiness, available syntax and tail calls;
see [the final chapter](../book/20-big-picture.md). The [course map](../book/course-map.md)
separately records which lecture, sheet and assessment material was available for review.
