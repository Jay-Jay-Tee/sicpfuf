# Your course in one place

Use this page as the front door: find a lecture, studio or reflection, read the explanation,
then practise the skill and check it with the interpreter. For exams, use the
[past-paper routes](../finals/past-papers.md), [checklist](../finals/checklist.md),
[revision sheets](../finals/sheets/index.md) and [three mock papers](../finals/index.md).

## What this map establishes

Source inventory reviewed on **16 November 2026**.

The source set available for this review contains **20 lecture decks, 11 studio sheets and
12 reflection sheets**, plus the assessment archives and mission/practice export listed below. These links map their
topics to original explanations and exercises. A mapped topic does **not** mean that every
slide diagram has been visually checked or every official question has a worked solution here.

The [applied-patterns workshop](21-applied-patterns.md) fills several gaps between knowing a
chapter and solving a longer question: power series, destructive filtering, binary-search
boundaries, multi-variable state, fair stream interleaving, combinations, comparators and
static name analysis.

The newly supplied mission export adds **19 missions with 68 tasks** and **four distinct PA
practice papers with 38 questions**. Two PA2 solution versions repeat 18 of those questions.
Their presence establishes which tasks were supplied; it does not make the saved editor code
a verified answer key. The mission and practice tables below distinguish topic routes from
material that still needs a dedicated explanation or a browser/hardware check.

Mission techniques are now taught within their subject chapters: [picture decomposition
and 3-D coordinates](02-runes.md#decompose-a-picture-before-writing-recursion),
[curve refinement](06-curves-sound.md#endpoints-transformation-order-and-repeated-refinement),
[rhythm expansion and scheduling](06-curves-sound.md#expand-a-rhythm-tree-then-schedule-its-events),
[image filters and sensor state machines](13-lists-loops.md#images-coordinates-channels-and-separate-buffers),
[node-reusing merge sort](15-search-sort-memo.md#merge-sort-by-rewiring-existing-nodes),
[stream demand](16-streams-ii.md#when-the-head-is-delayed-too) and
[evaluator instrumentation](18-mce-lazy.md#instrument-allocation-where-it-happens).
These are original explanations and worked examples, not copied mission solutions.

## Lectures

| Lecture | Read | Practise |
|---|---|---|
| L1A · elements | [1 · Elements](01-elements.md) | [Elements](../practice/01-elements.md) |
| L1B · runes | [2 · Runes](02-runes.md) | [Substitution](../practice/02-substitution-processes.md) |
| L2A · substitution and recursion | [3 · Substitution](03-substitution-recursion.md) | [Processes](../practice/02-substitution-processes.md) |
| L2B · growth | [4 · Growth](04-orders-of-growth.md) | [Growth](../practice/03-orders-of-growth.md) |
| L3A · higher-order functions and scope | [5 · Functions and scope](05-higher-order-scope.md) | [Functions and scope](../practice/04-hof-scope.md) |
| L3B · curves, sound and logic | [6 · Curves and sound](06-curves-sound.md) | [Elements](../practice/01-elements.md), [scope](../practice/04-hof-scope.md) |
| L4A · data abstraction | [7 · Data](07-data-abstraction.md) | [Pairs and diagrams](../practice/05-llists-box-pointer.md) |
| L5A · llist processing | [8 · Llists](08-llist-processing.md) | [Llist processing](../practice/06-llist-processing.md) |
| L5B · trees and CPS | [9 · Trees and CPS](09-trees-cps.md) | [Trees and CPS](../practice/07-trees-cps.md) |
| L6A · sorting and symbolic data | [10 · Sorting and symbolic data](10-sorting-symbolic.md) | [Sorting and streams](../practice/08-sorting-symbolic-streams.md) |
| L7B · streams and language processing | [11 · Streams](11-streams.md) | [Streams I](../practice/08-sorting-symbolic-streams.md) |
| L8A · state and mutable data | [12 · Mutation](12-state-mutation.md), [13 · Lists and loops](13-lists-loops.md) | [Mutation](../practice/09-state-mutation.md) |
| L9A · environment model | [14 · Environments](14-environment-model.md) | [Environments](../practice/11-environment-model.md) |
| L9B · lists and loops | [13 · Lists and loops](13-lists-loops.md) | [Lists and loops](../practice/10-lists-loops.md) |
| L10A · searching, sorting, memoization | [15 · Search and memoization](15-search-sort-memo.md) | [Search and memoization](../practice/12-memo-search-sort.md) |
| L11A · streams II | [16 · Streams II](16-streams-ii.md) | [Streams II](../practice/13-streams-ii.md) |
| L11B · evaluator I | [17 · Evaluator I](17-mce.md) | [Evaluator](../practice/14-mce.md) |
| L12A · evaluator II and laziness | [18 · Evaluator II](18-mce-lazy.md) | [Evaluator](../practice/14-mce.md) |
| L13A · types and objects | [19 · Types and objects](19-types-objects.md) | [Types](../practice/15-types.md) |
| L13B · synthesis | [20 · The big picture](20-big-picture.md) | [Checklist](../finals/checklist.md) |

## Studios

| Sheet | Main skills | Route |
|---|---|---|
| S2 | arithmetic, small functions, decimal encodings | [Elements](01-elements.md), [element drills](../practice/01-elements.md) |
| S3 | pictorial substitution, recursive versus iterative processes | [Runes](02-runes.md), [substitution](03-substitution-recursion.md) |
| S4 | tree recursion, call trees, composition | [Growth](04-orders-of-growth.md), [higher-order functions](05-higher-order-scope.md) |
| S5 | pairs, three notations, access paths | [Data](07-data-abstraction.md), [diagram drills](../practice/05-llists-box-pointer.md) |
| S6 | map/filter/reduce, returning combinations | [Llists](08-llist-processing.md), [combination construction](21-applied-patterns.md#building-all-combinations-instead-of-counting-them) |
| S7 | accumulator and CPS conversions, tagged expressions | [Trees and CPS](09-trees-cps.md), [symbolic data](10-sorting-symbolic.md) |
| S8 | recursive streams and power series | [Streams II](16-streams-ii.md), [coefficient streams](21-applied-patterns.md#streams-as-coefficients-of-a-power-series) |
| S9 | destructive filtering and aliasing | [Mutation](12-state-mutation.md), [filtering existing nodes](21-applied-patterns.md#removing-nodes-without-allocating-new-pairs) |
| S10 | stateful closures, CPS frames, loop captures | [Environment model](14-environment-model.md), [environment drills](../practice/11-environment-model.md) |
| S11 | binary-search boundaries, best/worst sorting costs | [Searching and sorting](15-search-sort-memo.md), [insertion boundaries](21-applied-patterns.md#binary-search-can-return-a-boundary) |
| S12 | changing an evaluator, static checks, truthiness | [Evaluator I](17-mce.md), [evaluator drills](../practice/14-mce.md), [static traversal](21-applied-patterns.md#a-static-pass-visits-branches-that-will-not-run) |

## Reflections

| Sheet | Main skills | Route |
|---|---|---|
| R1 | expressions, predicates, declared names | [Elements](01-elements.md), [substitution](03-substitution-recursion.md) |
| R2 | operation counts and deferred work | [Substitution](03-substitution-recursion.md), [growth](04-orders-of-growth.md) |
| R3 | scope, general sums, higher-order functions | [Functions and scope](05-higher-order-scope.md), [scope drills](../practice/04-hof-scope.md) |
| R4 | constructing and traversing pairs | [Data](07-data-abstraction.md), [diagram drills](../practice/05-llists-box-pointer.md) |
| R5 | map/filter/reduce and flattening | [Llists](08-llist-processing.md), [llist drills](../practice/06-llist-processing.md) |
| R6 | comparator design and sort analysis | [Sorting](10-sorting-symbolic.md), [compound comparators](21-applied-patterns.md#a-comparator-describes-an-ordering) |
| R8 | private state, lock-out, list folds | [Mutation](12-state-mutation.md), [state machines](21-applied-patterns.md#a-closure-can-hold-a-state-machine), [loops](13-lists-loops.md) |
| R9 | rebinding, lexical scope, retained CPS frames | [Environments](14-environment-model.md), [CPS](09-trees-cps.md) |
| R10 | repeated search, tabulation and memoized trees | [Search and memoization](15-search-sort-memo.md), [memo drills](../practice/12-memo-search-sort.md) |
| R11 | forcing order, memoized tails, interleaving | [Streams II](16-streams-ii.md), [fair interleaving](21-applied-patterns.md#fairly-interleaving-several-streams) |
| R12 | evaluator markers, argument order, self-interpretation | [Evaluator II](18-mce-lazy.md), [marker identity](21-applied-patterns.md#internal-markers-need-identity), [evaluator drills](../practice/14-mce.md) |
| R13 | narrowing, generic annotations, optional results | [Types](19-types-objects.md), [typed drills](../practice/15-types.md) |

## Missions supplied in the November export

The IDs and titles help you find the matching item in your own course workspace. The routes
lead to original explanations; course question text and saved submissions are not reproduced.
All 68 task entries were inventoried, including the optional final task in mission 1864.
No claim is made here that every saved mission program has been run or corrected.

| Mission | Tasks | Read first | What still needs attention |
|---|---:|---|---|
| 1652 · Rune Trials | 4 | [Functional abstraction with runes](02-runes.md), [picture decomposition](02-runes.md#decompose-a-picture-before-writing-recursion), [functions as arguments](05-higher-order-scope.md) | Reference images are absent from the export, so exact target drawings remain unverified. |
| 1676 · Rune Reading | 3 | [Recursive processes](03-substitution-recursion.md), [nested-panel worked example](02-runes.md#decompose-a-picture-before-writing-recursion) | Apply the decomposition method to each target; missing images prevent a complete visual comparison. |
| 1679 · Beyond the Second Dimension | 2 | [3-D coordinate model](02-runes.md#extending-the-geometry-to-three-dimensions), [module limits](../reference/compatibility.md#modules) | Coordinates, footprint scaling and height are explained; full 3-D rendering and occlusion remain unsupported. |
| 1703 · Curve Introduction | 3 | [Curves are functions](06-curves-sound.md#curves-are-functions), [endpoint checks](06-curves-sound.md#endpoints-transformation-order-and-repeated-refinement) | Exact mission drawings are not certified by these original examples. |
| 1714 · Curve Manipulation | 2 | [Curve transformations](06-curves-sound.md#makers-and-transformations), [order and endpoint contracts](06-curves-sound.md#endpoints-transformation-order-and-repeated-refinement) | Compare each requested transformation with its specified endpoints and geometry. |
| 1726 · Beyond the First Dimension | 3 | [Self-similar segment replacement](06-curves-sound.md#build-a-self-similar-path-from-oriented-segments), [growth](04-orders-of-growth.md) | The original zigzag example teaches the construction method; it is not a worked solution to each named course fractal. |
| 1737 · Premorseal Communications | 5 | [Sounds as functions of time](06-curves-sound.md#sounds-are-functions-of-time), [time windows and mixing](06-curves-sound.md#time-windows-delays-and-overlapping-sounds) | Timing boundaries are tested numerically; browser playback remains outside this check. |
| 1764 · POTS and Pans | 4 | [Pairs and abstraction](07-data-abstraction.md), [time windows and mixing](06-curves-sound.md#time-windows-delays-and-overlapping-sounds), [llist pipelines](08-llist-processing.md) | The method is explained; verify the question's frequency table and delimiters separately. |
| 1789 · Musical Diversions | 5 | [Rhythm-tree expansion and scheduling](06-curves-sound.md#expand-a-rhythm-tree-then-schedule-its-events), [nested trees](09-trees-cps.md) | Worked examples distinguish event spacing, silence and overlapping duration; they do not certify instrument playback. |
| 1798 · Search and Rescue | 3 | [Binary search trees](10-sorting-symbolic.md#4-binary-search-trees-as-llists), [data abstraction](07-data-abstraction.md) | Respect the supplied tree selectors and constructors when checking a solution. |
| 1809 · Sorting Things Out | 5 | [Quicksort](10-sorting-symbolic.md#quicksort-the-idea), [growth](04-orders-of-growth.md) | Partition correctness and best/worst-case analysis are separate obligations. |
| 1814 · Robotic Trials | 4 | [Functions](01-elements.md#functions), [sensor decisions and non-blocking commands](13-lists-loops.md#sensor-driven-programs-are-state-machines) | EV3 motor/speech APIs and physical calibration require the hardware environment. |
| 1825 · Moving about on Planet Y | 3 | [Sensor-driven state machine](13-lists-loops.md#sensor-driven-programs-are-state-machines), [loops](13-lists-loops.md) | Decision logic is tested on recorded values; sensor units and movement still need robot testing. |
| 1826 · Finding ELDRIC | 3 | [Predicates](01-elements.md#booleans-and-predicates), [hysteresis and retained state](13-lists-loops.md#sensor-driven-programs-are-state-machines) | Line recovery and thresholds still need physical calibration and testing. |
| 1832 · Know Your Environment | 3 | [Environments](14-environment-model.md), [sharing and mutation](12-state-mutation.md) | Retain every required frame and distinguish lexical parents from callers; these particular diagrams are not certified here. |
| 1844 · Corrective Sky Surgery | 4 | [Image coordinates and buffers](13-lists-loops.md#images-coordinates-channels-and-separate-buffers), [inverse mapping](13-lists-loops.md#work-backwards-from-a-destination-pixel), [filter composition](13-lists-loops.md#compose-filters-without-corrupting-their-inputs) | Image arithmetic is taught with a checked mirror/warming filter; live-camera APIs are unsupported. |
| 1846 · Reuse Your Pairs | 3 | [Mutation and identity](12-state-mutation.md), [bottom-up merge sort using existing nodes](15-search-sort-memo.md#merge-sort-by-rewiring-existing-nodes) | The worked example explains stability and allocation limits and checks node identity; mission-specific submitted programs remain unaudited. |
| 1864 · Streaming the Anomaly | 5 | [Streams](11-streams.md), [repetition, subsampling and lookahead](16-streams-ii.md#some-transformations-must-inspect-ahead), [image buffers](13-lists-loops.md#images-coordinates-channels-and-separate-buffers) | Stream demand and image handling are explained separately; the footage and video APIs remain unavailable. |
| 1885 · The Essence of Python | 4 | [Allocation instrumentation](18-mce-lazy.md#instrument-allocation-where-it-happens), [value-based operator extensions](18-mce-lazy.md#extend-an-operator-without-evaluating-its-operands-twice) | Counters and an original operator extension run in the book's evaluator. Its frame metric is stated explicitly; the programmable browser REPL is not implemented. |

The export refers to pictures but contains **no embedded images or image links**. It also
contains templates and unfinished submissions. For example, a section labelled “Solution”
has an incomplete assignment; the label alone is not evidence of a complete staff solution.

## PA practice papers supplied in the export

These are **practice papers**, separate from the PA1/PA2 assessment summary supplied in chat.
PA1 Practice A and B each have 10 questions; PA2 Practice A and B each have nine. The PA2
solution versions repeat the corresponding questions and test cases, with different saved code.

| Paper and questions | Skills | Route and remaining gaps |
|---|---|---|
| PA1 A · Q1–4 | Numeric folds, digit reduction, stable partition, repeated function application | [Llist processing](08-llist-processing.md), [iteration and recursion](03-substitution-recursion.md), [higher-order functions](05-higher-order-scope.md). Test non-integer results as well as the supplied examples. |
| PA1 A · Q5–6 | Searching a supplied word collection and using access functions | [Searching](15-search-sort-memo.md), [data abstraction](07-data-abstraction.md). The external word collection and helper environment are not fully captured. |
| PA1 A · Q7–8 | Sparse polynomial evaluation and combination | [Symbolic data](10-sorting-symbolic.md), [folds](08-llist-processing.md), [coefficient representations](21-applied-patterns.md#streams-as-coefficients-of-a-power-series). Sparse-term merging still needs its own worked example. |
| PA1 A · Q9–10 | Prefix recognition and non-mutating sequence replacement | [Llist recursion](08-llist-processing.md), [sharing](12-state-mutation.md#hidden-sharing-append). Overlapping matches and the replacement contract need dedicated practice. |
| PA1 B · Q1–5 | Counting, maximum, recursive numeric processes, sortedness | [Llists](08-llist-processing.md), [recursive processes](03-substitution-recursion.md), [sorting](10-sorting-symbolic.md). |
| PA1 B · Q6–8 | Order-preserving interleavings and non-mutating sequence edits | [Tree recursion](03-substitution-recursion.md), [llists](08-llist-processing.md). Ambiguous equal elements require branching rather than a greedy choice. |
| PA1 B · Q9–10 | Recursive tree rearrangement and traversal | [Trees](09-trees-cps.md), [binary tree abstraction](10-sorting-symbolic.md#4-binary-search-trees-as-llists). Stable rearrangement at every nested level needs further practice. |
| PA2 A · Q1–3 | Adjacent-element processing and reversible encodings | [Llist recursion and accumulators](08-llist-processing.md). Encoding/decoding laws need a dedicated worked example. |
| PA2 A · Q4–6 | Matrix indexing, postfix evaluation, shortest paths | [Nested lists and loops](13-lists-loops.md), [expression trees](10-sorting-symbolic.md). Postfix stacks and grid shortest-path search are not fully taught here. |
| PA2 A · Q7–9 | Constant-time stream construction, self-generated streams, destructive merge | [Streams](11-streams.md), [forcing and lookahead](16-streams-ii.md#some-transformations-must-inspect-ahead), [node-reusing merge](15-search-sort-memo.md#merge-sort-by-rewiring-existing-nodes). Particular submitted implementations still need their own cost checks. |
| PA2 B · Q1–3 | Matrix geometry, pixel quantization, image serialization | [Lists of lists](13-lists-loops.md#lists-of-lists), [pixel mapping and quantization](13-lists-loops.md#work-backwards-from-a-destination-pixel). The exact practice output format still needs dedicated practice. |
| PA2 B · Q4–5 | Expression traversal and grid-path counting | [Expression trees](10-sorting-symbolic.md), [memoization](15-search-sort-memo.md). Postfix conversion and grid recurrences need dedicated practice. |
| PA2 B · Q6–7 | Run-length streams and mutable queues | [Bounded runs and lookahead](16-streams-ii.md#some-transformations-must-inspect-ahead), [front/rear queue invariants](12-state-mutation.md#a-queue-needs-a-front-and-a-rear-invariant). The bounded-run example deliberately uses a different contract from complete maximal runs. |
| PA2 B · Q8–9 | Bounding geometry and in-place three-way partition | [Folds](08-llist-processing.md), [three-region partition](13-lists-loops.md#partition-with-three-regions). Bounding-box geometry still needs a dedicated worked example. |

### What was actually executed

The export contains **442 fenced test programs**, counting repeated tests in the two PA2
solution versions. The **386 PA practice tests** were run with their saved editor code,
without inventing missing assessment helpers. Output and normalized error kind agreed with
the pinned reference interpreter in **386/386** cases. One long stream probe needed a higher
reference evaluation budget; evaluator-step counts are not compared.

Of those local runs, **314 produced the listed final output line** and **72 stopped with an
error**, including unfinished programs and missing helper names. Agreement between interpreters
includes agreement on those errors; it is not a score or proof that the supplied answers are
correct. The test harness compares the final printed line with the export label separately
from the full-output comparison between interpreters. Mission programs, visual results, hidden
tests and actual deployed assessment grading are outside this execution check.

A separate counterexample confirms that passing the supplied examples is insufficient: the
saved average calculation uses integer division, so a non-integer mean is truncated in both
interpreters. Raw programs, test cases and results remain in a private assessment cache,
outside this public repository. See [compatibility](../reference/compatibility.md) for the
reference revision and the limits of the comparison.

## Assessment material available locally

The filenames below identify the archives supplied for this review. The PDFs themselves are
not bundled into this repository. The [past-paper routes](../finals/past-papers.md) identify
question groups and the chapters to revise; they are not an official answer key.

| Archive | Material found |
|---|---|
| `Final_export.zip` | Three final papers: AY23/24, AY24/25, AY25/26; no answer PDFs |
| `Assessments_export.zip` | Four midterms with answer PDFs: AY23/24 through AY26/27 |
| `Reading_Assessment_1_export.zip` | RA1 papers and answers for AY23/24–25/26; four AY26/27 answer variants |
| `Reading_Assessment___export (1).zip` | RA2 papers and answers for AY23/24–25/26; two AY26/27 answer variants |
| `cs1101s-missions-and-pa-practice.md` | November 16 export: 19 missions, four distinct PA practice papers and two PA2 solution versions; editor code, some test cases, no embedded figures |

## Material that is still missing or not fully verified

- The available set has no L8B deck. Do not infer its contents from the numbering alone.
- There is no S4 in-class continuation, no S1 sheet and no R7 sheet in the supplied set.
  Some of these numbering gaps may be intentional; that is not evidence that a file was reviewed.
- The supplied export inventories 19 missions, but completeness against the live mission list
  has not been verified. Paths, Quests and Check-Ins remain unsupplied. Topic routes are not
  task-by-task worked explanations, and saved mission programs have not all been executed.
- Text extraction loses diagrams and some mathematical layout. Existing explanations and regenerated
  diagrams help, but a complete slide-figure audit has not been performed.
- The three finals have topic routes here, not complete verified worked solutions for all 73 questions.
- Language and module differences are listed in [compatibility](../reference/compatibility.md).

This page is a study map of the evidence available, not a claim that unseen material is covered.
