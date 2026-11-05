# V30 local sparse-run context oracle

`model.py` implements a bounded host-side cost oracle for an application-specific
coefficient selector. It preserves EC26 layout 0, DC values, and the current
Rice parameters. It introduces no new wire syntax or decoder requirement.

`BandIndex(sequence, kr, kv)` indexes the existing nonzero positions, run/level
bit lengths, and a prefix sum. `delete_interval(start, stop)` predicts the exact
bit and padded-stream-byte change when that half-open interval is set to zero.
The query removes the affected tokens and, if a later token exists, replaces
its run with the merged run. The last removed token has no fabricated end token.
The operation needs two binary searches, two prefix reads, and at most one
successor-run repair; it reads no source coefficient array during the query.

This local claim is deliberately restricted: it does not reselect Rice
parameters, change coefficient levels, insert coefficients, change layout or
alter DC coding. The benchmark separately executes the full optimized EC26
counter and actual serialization, including raw fallback. Keeping the old Rice
parameters is a valid cost bound, not necessarily the final optimum. Combining
multiple edits requires updating/rebuilding the index or a new combined query;
independent marginal savings cannot simply be added.

## Retained experiment

The first 12 v29 `adaptive_lazy` packets in each of two Mass Effect windows
supply 24 source-frame decisions and all 72 decoded coefficient planes at full
720×480 coded geometry. Deterministic samples select up to six blocks with
nonzero high-band coefficients per plane and up to two adjacent block pairs.
Each recipe clears zigzag positions 21–63 in its block(s); DC is unchanged.
This is a non-causal rate-context experiment, with no source-distortion guard,
accepted-stream, HUD composition, bitrate-improvement or visual-quality claim.

All **322 modified coefficient constructions** match exact fixed-parameter
local bit predictions versus independent full recounts. All optimized lengths
also match actual EC26 serialization; the retained packet/coefficient SHA-256s
are reproduced by the verifier.

| Window | Local query ms | Full same-parameter recount ms | Full optimized EC26 counter ms | Sparse index build ms |
| --- | ---: | ---: | ---: | ---: |
| 2600 | 0.01233 | 0.30240 | 1.76066 | 0.24796 |
| 7200 | 0.01272 | 0.26645 | 1.82539 | 0.27741 |

Local queries are about 24.5× / 20.9× faster than the same-parameter full
recounts after setup. Full parameter optimization does more work and is not an
identical-semantics speed comparison. Timings exclude coefficient-packet parsing,
initial zigzag band extraction, candidate coefficient copies, distortion checks,
packet framing and reconstruction. They are Python host timings, not native
throughput. The index retains up to **113,948 bytes** for this corpus; its sparse
arrays are host memory, not a fitted FPGA/ESP32 memory allocation.

The 172 independent single-block recipes demonstrate why the old isolated CP02
proxy is insufficient: it disagrees with actual EC26 marginal bytes on
**132/172** queries. The diagnostic sum of their independent actual EC26 savings
is 524 bytes versus 356 bytes predicted by isolated CP02. These overlapping
alternative queries are not one encoded stream and must not become a claimed
524-byte frame/stream gain.

Across all 322 queries, 25 reselect Rice parameters. Of 50 adjacent-pair recipes,
11 have nonadditive fixed-parameter bit changes and 24 have nonadditive optimized
byte savings. For example, window2600/frame1/luma blocks4539 and4540 save one
byte each independently but three bytes when edited together. Run context and
byte padding explain why summing isolated block estimates can miss the actual
rate. Such effects must be charged by the final plane counter/serialization.

## How to use the result

Use the local fixed-parameter oracle to screen a bounded candidate menu on the
PC, measure actual decoded block distortion and protect UI/ROI content, then
use a final full optimized counter and actual serialization before admitting
any frame. Rebuild or update context after accepted edits. A useful next model
could maintain run-neighbor and Rice-parameter histograms incrementally, but
this iteration does not claim that implementation or resource fit.

```sh
python -m unittest discover -s experiments/python-game-context-v30-study -v
python experiments/python-game-context-v30-study/verify.py
```

Four tests cover seeded random deletion intervals, first/middle/last/all/empty
edits, run escape boundaries, byte padding and malformed domains. Offline replay
requires Python/NumPy and inherited retained source objects, not the original
video download. It checks source hashes, all exact bit/byte deltas, actual packet
hashes and adjacent-pair nonadditivity. Native ESP32/QSPI/RF, FPGA clock/resources,
physical 30 fps and gameplay quality remain unqualified here.
