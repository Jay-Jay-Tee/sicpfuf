# Reference conformance checks

These fixtures come from Source Academy's actual implementation, not sicpfuf.
They use original small programs and generated type/operator combinations.
The pinned py-slang revision is `c0a8dfd9d6b1c4f6a59d1778e7e7380fa9b9f918`.
The frontend's retained-history behaviour was inspected at
`8e8d2f39cad45f8e89292cb116959e840c5467a3`.

## Run frozen checks

From the repository root:

```sh
python3 tests/conformance/compare.py tests/conformance/operators.json.gz /tmp/operators-report.json
python3 tests/conformance/compare.py tests/conformance/builtins.json.gz /tmp/builtins-report.json
python3 tests/conformance/compare.py tests/conformance/syntax.json.gz /tmp/syntax-report.json
python3 tests/conformance/steps.py tests/conformance/environment.json.gz
python3 -m unittest discover -s tests -p 'test_reduction.py'
```

The raw comparison commands intentionally return nonzero for discrepancies;
they do not treat a documented mismatch as a match. Reports include every
discrepancy, its source, and both results. Runtime comparisons check exact
stdout and normalized error kinds; they do not compare every diagnostic word
or location. The main differential suite separately checks error lines and
typed diagnostic messages.

Results on Python 3.9.6 on macOS, 16 November 2026:

| Fixture | Evidence | Result |
|---|---|---|
| `operators.json.gz` | All binary/unary/boolean combinations generated from upstream's test type universe, in all four chapters | 3964/3964 exact |
| `builtins.json.gz` | Deterministic stdlib acceptance, output and arity probes; random/time checked by result type | 4709/4769 exact |
| `syntax.json.gz` | 99 directed programs across four chapters | 380/396 exact; 12 need a module host and 4 encounter an upstream evaluator failure |
| `environment.json.gz` | 59 complete histories, 1424 states, including nested calls, empty frames, tails, declarations, loops, library callbacks, shared/cyclic lists and garbage | 58 histories exact; one upstream active-frame display issue |

The 60 builtin discrepancies are 20 undocumented extra-argument acceptances by
upstream `str`, and 40 floating-point output differences in `atan`, `atan2`,
`erfc`, `gamma`, `lgamma`, `log1p`, `sinh` and `tan`. The comparison retains them
even when the numerical difference is small. Other platforms can have different
last digits in native math results.

Separately, upstream returns `0j` for `0j ** 0`; sicpfuf keeps `(1+0j)`.
The generated operator universe's complex literal is nonzero, so that conflict
is outside its 3964 cases. A perfect finite sweep is not a universal equivalence claim.

The syntax failures are `assert` (upstream crashes with `Unknown evaluator
error: Assert`) and three import probes per chapter (the headless runtime lacks
its Conductor module host). They are not evidence of twelve language bugs.

For `a[f(0)] = f(1)`, upstream correctly reduces the RHS first but chooses the
active-frame label by inspecting the target first. During `f(1)`, it labels
Global as active. sicpfuf labels the executing call E1. The regression test
checks this exact known difference and compares every other field and state.

The state comparison checks the whole remaining program, frame bindings,
parent links, heap identity and elements, active frame, cumulative output and
reachability. It reconstructs upstream's delta transport before comparing
retained garbage. It ignores presentation node IDs, tooltips, source formatting
and map display order. It does not establish matching pixel layout, marker
positions or wording of explanations.

The complete documentation check executes 753 snippets. With `--oracle`, its
506 eligible plain snippets also match the reference. Module/graphics examples,
typed flags and sicpfuf-only tools are checked by their respective paths rather
than counted as those 506 comparisons.

## Regenerate using upstream

`PYSLANG` can select a built checkout with its dependencies installed. It
defaults to `~/.cache/sicpfuf/py-slang`. Build the helper without editing that
checkout:

```sh
node tests/conformance/build_oracle.mjs
printf '%s' '{"generate":"operators"}' | node tests/conformance/oracle.mjs > /tmp/operators-oracle.json
printf '%s' '{"generate":"builtins"}' | node tests/conformance/oracle.mjs > /tmp/builtins-oracle.json
python3 tests/conformance/programs.py > /tmp/syntax-request.json
node tests/conformance/oracle.mjs < /tmp/syntax-request.json > /tmp/syntax-oracle.json
python3 tests/conformance/steppers.py > /tmp/steps-request.json
node tests/conformance/oracle.mjs < /tmp/steps-request.json > /tmp/steps-oracle.json
```

The helper also records substitution histories for comparison. sicpfuf's
expression-oriented substitution recorder still differs from upstream's
whole-program substitution reducer; the environment conformance result must
not be presented as a substitution conformance result.

`substitution-scope.json` records eight scope regressions against
both the ordinary reference runtime and its actual substitution reducer. They
exercise a lambda parameter, a local assignment, a local function parameter,
and a local function name, including fresh-name collisions and a function whose
parameter shares its name. These compare answers, not identical step histories.
Function values also retain their original printed names after renaming and aliasing.

## Supplied finals

The three supplied papers and their extracted programs remain outside the
repository. The private assessment cache contains the original probe generators
in `tools/exam_programs.py` and `tools/exam_coverage.py`, plus the question ledger
`conformance-coverage.json`. Run the generators only with those supplied inputs.
Do not commit their extracted question programs or an answer key.

All 44 executable probes match upstream and their independent predictions.
The ledger covers all 73 question numbers with execution evidence or an explicit
analytic review. Complexity arguments, compiler diagrams and candidate solutions
are distinct from running an exact supplied program. There is no official finals
answer key in the supplied archive. Some supplied PDFs are repaired/adapted
versions, and one question has equivalent alternatives. These checks do not
certify a historical official answer key.
