# V81 observed reference and write dependencies

The new traces distinguish first-offered lookup valid, accepted lookup, the
accepted logical reference request, captured bridge snapshot, successful core
block commit, actual backend write completion and receiver retirement. All four
bounded regular/combat control/wide traces pass the event identity/order audit.
Raw physical controller command owner generation remains unknown; no owner is
inferred from a trace window. Logical block events carry authenticated tags.

Reproduce with `python3 scripts/cu66-v81/analyze_path.py`. The artifact is
[`path-analysis/results.json`](../../fpga/experiments/cu66-v81/path-analysis/results.json),
including exact integer histograms and source trace/result hashes. Latest
completed attempts are selected by immutable attempt name, never fastest timing.

## Predicted source 1 in each bounded history

All intervals below are measured memory cycles at the assumed 100 MHz. They
include scheduling/arbitration as applicable and overlap other work; they must
not be added or subtracted as a critical-path decomposition.

| History | Mode | First-offer → accepted lookup median | Accepted lookup → response median | Write accept → backend done median | Backend done → receiver done median |
|---|---:|---:|---:|---:|---:|
| 0 | 2 | 126 | 1 | 136 | 2 |
| 0 | 3 | 119 | 1 | 136 | 2 |
| 3 | 2 | 126 | 1 | 136 | 2 |
| 3 | 3 | 119 | 1 | 136 | 2 |

In mode 3, each accepted logical request takes 17–36 cycles to reach a captured
bridge snapshot in these source-1 samples (median 17), and every snapshot
commits to the core exactly one cycle later. Successive blocks of the same tile
have a median 16 cycles from the preceding core commit to the next accepted
logical request. That latter interval includes admission/arbitration and is not
a measured raw controller service time.

The seven-cycle reduction in median offered-lookup wait is real in these
samples, but the complete-frame timings are nearly unchanged or mixed. A
seven-cycles-times-tiles calculation would not be a validated speedup estimate.
Both modes still perform the same number of physical reads and writes. The
actual write transaction and arbitration dependencies therefore remain in the
comparison rather than disappearing with a faster cache-fill handshake.

Mode 2's raw/snapshot/block path is explicitly uninstrumented. Zero events there
are not zero latency. It does have first-offer, accepted lookup, backend and
receiver completion events, which support the matched columns above.

The next experiment should target measured memory work or scheduling, preserve
continuous LCD priority and bank/write coherence, and rerun identical compressed
sources. See the separate bottleneck screening study before choosing that change.
