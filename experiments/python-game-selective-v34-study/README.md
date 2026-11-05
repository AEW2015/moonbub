# Selective parent32 to child16 refinement

This fixed-reference probe reduces sampled motion-search work, but neither
selective preset admits a packet against the actual accepted control. It is
not a causal-stream rate/quality improvement. All losing trials are retained.

`model.analyze16(module, adaptive, parentPrepared32, reference, *, budget=25)`
returns a new `Prepared` owned by the supplied frozen GM27 runtime. `budget`
must be the integer 25 or 50. The parent must be an owned block-size-32
preparation and the reference must match its tag. Key frames produce an owned
key child without a motion map. No imported module is patched or mutated.

`model.refine(adaptive, source, reference, parent_vectors, *, budget=25,
mask=None)` returns `(child_vectors, work)`. An optional boolean parent-grid
mask replaces automatic selection for controlled tests; it does not alter the
budget-preset validation. The returned field is private to the call.

The automatic screen measures current-source weighted absolute residual at
stride 4 under the exact inherited parent prediction. Each parent's score is
its weighted mean residual plus the range of its child16 mean residuals. This
prioritizes residual error and spatial dispersion; exact UI/background scores
zero. Scores have no future-frame, candidate-encode, decoded-quality, or
retained admission-metric input. Groups rank by descending score, then
row-major index. The fixed quota is `ceil(parent_groups * budget / 100)`,
including partial edges. The 720×480 grid selects 87/345 or 173/345 groups.
Selected groups whose sampled weighted mean residual is at most 2 remain
quiet and retain their parents. Every unselected group also retains its exact
replicated parent field, including nonzero quiet parents.

Each selected active group searches all four existing child16 blocks with
25 offsets in ±2 half-luma units around its own parent. The parent candidate
runs first; strict improvement wins ties. Vectors stay bounded to ±18
half-luma units. Fine scoring uses stride 2 and exact frozen bilinear rounding
and edge clamping. Search cannot choose zero unless zero lies in that local
candidate set. The full-refinement v33 baseline separately retains its original
zero-first policy, which can return a quiet child to zero. This semantic
difference is explicit: the selective path preserves parent inheritance for
hierarchical map coding, which is not part of this study.

The 24 inputs are IDs 0–11 from each of the two frozen v33 split-study source
windows. Every trial uses the actual prior accepted v32 `band_control`
reference (the same control parity lineage retained by v33). Candidates never
update history. Each input pays parent32 search, prediction, transform, map
packing and strict-band base encoding; full v33 refinement and both incumbent16
and strict-band16 encodes; both selective analyses and both encodes for each;
current-source hybrid RGB scoring and actual CP27 binding. The experiment
constructs and retains **168 real GM27/CP27 probe packets**, plus copies of the
24 actual accepted controls. All probe packets fit the 49,152-byte cap and pass
the frozen CP27 parser. The same retained exact HU25 HUD and 60-byte binding
apply to all comparisons. Admission requires strictly fewer complete bytes,
no higher active current-source RGB SSE, and cap fit against the actual
accepted control, with a separately labelled parent32-band comparison.

| 24-frame result | Full v33 | Selective 25% | Selective 50% |
| --- | ---: | ---: | ---: |
| Qualified incumbent/band trials | 10 | 0 | 0 |
| Frames admitted against control | 5 | 0 | 0 |
| Admitted complete bytes | 506,909 | 508,720 | 508,720 |
| Admitted active RGB SSE | 426,515,821 | 426,975,565 | 426,975,565 |
| Raw strict-band complete bytes | 508,776 | 514,794 | 514,670 |
| Raw strict-band active RGB SSE | 426,825,737 | 428,037,625 | 427,816,213 |
| Raw strict-band motion bytes | 13,945 | 13,289 | 13,474 |
| Raw strict-band residual bytes | 218,608 | 225,282 | 224,973 |
| Screen + fine SAD sample operations | 19,466,400 | 11,186,400 | 13,130,400 |
| Screen + fine reference sample fetches | 69,312,000 | 44,745,600 | 52,521,600 |
| Raw strict-band decoder reference reads | 14,734,336 | 15,832,448 | 15,933,824 |
| Mean child analysis time | 70.94 ms | 62.56 ms | 64.84 ms |
| Mean additional child + two-encode probe | 207.96 ms | 201.22 ms | 203.43 ms |

The accepted control totals 508,720 complete bytes and 426,975,565 active RGB
SSE. The selective 25% preset reduces sampled screen/refinement SAD operations
by 42.53% versus full v33; 50% reduces them by 32.55%. The raw selective paths
increase complete bytes and source error and increase decoder reference reads.
Their lower motion bytes do not offset their larger residuals. The 25% preset
selects 1,914 groups across 22 P frames and searches 1,091 active groups; 50%
selects 3,806 groups and searches 1,295. Selection is fixed independently of
these outcomes. No preset was selected by retained acceptance results.

All motion bytes above are **actual ordinary uniform-grid GM27 maps**. There
is no HM34 dependency or prospective hierarchy saving in these totals. The
full-v33 48 incumbent/band packets and all 24 parent32-band packets match the
frozen retained split-v33 bytes exactly.

`work` records sampled screen and fine operations separately, conservative
four-tap reference fetches for compact half-sample scoring, scored source
reads, distinct source-gather reads, exact prediction reference fetches, full
source/prediction transform sample reads, map work, retained arrays, and paid
screen/search/map/transform/wall times. Gather reads and scored reads describe
different stages and are labelled separately. Parent search is paid once per
source and is not folded into the child-only table. The combined seven-attempt
probe averages 776.32 ms per input in this one local timing sample. It excludes
fixture I/O/conversion, retained HU25 generation, offline retained-control
quality extraction, debug decoder verification, archive compression, transport
and display. It establishes no physical 30 fps, hardware fit, causal-stream,
combined-gain, or endpoint result.

Run from the repository root:

```sh
PY=/home/lori/gamebub-streaming-prototype/.venv/bin/python
$PY -m unittest discover -s experiments/python-game-selective-v34-study -p test_model.py -v
$PY experiments/python-game-selective-v34-study/benchmark.py
$PY experiments/python-game-selective-v34-study/verify.py
```

Six tests cover mapping/partial edges, fixed quotas and row-major ties, quiet
nonzero-parent inheritance, a known fractional shift, unselected exact-parent
inheritance and bounds, invalid budget/mask/ownership/reference, read-only
owned analysis, and actual partial-edge key/P decoding with both encoders.
The independent verifier checks all 1,028 source pins and source-pixel hashes,
actual accepted references and controls, CP27 components/caps, every decoded
output/quality metric, admission decisions, and decoder reads. Its default
mode re-encodes all 168 probe packets exactly and independently recomputes the
screen from source and full parent-prediction pixels, then checks masks and
exact inheritance. `--archives-only` explicitly disables re-encoding and
independent screen recomputation. `sourcepins.json`, `results.json`,
`objects/`, `tests.log`, `benchmark.log`, and `verify.log` retain evidence.
All files from v33 and earlier remain frozen.
