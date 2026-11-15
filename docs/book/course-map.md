# Your course in one place

Use this page as the front door: find a lecture, studio or reflection, read the explanation,
then practise the skill and check it with the interpreter. For exams, use the
[past-paper routes](../finals/past-papers.md), [checklist](../finals/checklist.md),
[revision sheets](../finals/sheets/index.md) and [three mock papers](../finals/index.md).

## What this map establishes

Source inventory reviewed on **15 November 2026**.

The source set available for this review contains **20 lecture decks, 11 studio sheets and
12 reflection sheets**, plus the assessment archives listed below. These links map their
topics to original explanations and exercises. A mapped topic does **not** mean that every
slide diagram has been visually checked or every official question has a worked solution here.

The [applied-patterns workshop](21-applied-patterns.md) fills several gaps between knowing a
chapter and solving a longer question: power series, destructive filtering, binary-search
boundaries, multi-variable state, fair stream interleaving, combinations, comparators and
static name analysis.

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

## Material that is still missing or not fully verified

- The available set has no L8B deck. Do not infer its contents from the numbering alone.
- There is no S4 in-class continuation, no S1 sheet and no R7 sheet in the supplied set.
  Some of these numbering gaps may be intentional; that is not evidence that a file was reviewed.
- Complete Paths, Missions, Quests and Check-Ins were not supplied, so their individual tasks
  are not audited here. Topic overlap with a chapter is not the same as reviewing every task.
- Text extraction loses diagrams and some mathematical layout. Existing explanations and regenerated
  diagrams help, but a complete slide-figure audit has not been performed.
- The three finals have topic routes here, not complete verified worked solutions for all 73 questions.
- Language and module differences are listed in [compatibility](../reference/compatibility.md).

This page is a study map of the evidence available, not a claim that unseen material is covered.
