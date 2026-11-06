# COPY-aware execution accounting

The [execution runner](../../scripts/cu66-v82/prototype_execution.py) uses the
frozen V81 transactional residency model with actual 64-byte native tiles. Every
claimed resident store is checked against candidate contents, every accepted
candidate equals the complete canonical frame, and all four leaf granularities
reproduce V81's 6,740,876 hypothetical elidable BL8 stores. Keys still write all
tiles. The content tree and residency state are evaluated together on valid
frames; asynchronous joint RTL commit/abort behavior is not simulated here.

The retained [execution result](../../experiments/python-gamebub-v82/execution/attempt-20261106T052617072164Z-c382bb87/results.json)
contains all 1,828 per-source records, source snapshots and source/input hashes.
The [input verifier](../../scripts/cu66-v82/verify_execution_inputs.py) separately
reassembles every original flat canonical plane SHA from exported bytes and
checks every equality/COPY bit. On this corpus, visible exact equality and
encoded-zero eligibility coincide. That is a dataset observation, not a general
rule: a future nonzero residual could round/clip to unchanged bytes and still
require reference data before its equality is known.

## Reference requests and payload availability

A visible non-COPY delta tile reads its reference for normal reconstruction.
A COPY tile without certified candidate residency reads the reference and stores
the copy. A resident COPY can avoid both operations only if hashing does not need
its bytes. If its group contains another non-COPY tile, recomputing the leaf
forces a hash-only read for that resident COPY. CONST128 needs no reference read.
Decoded/copied data already available to the group hash is not counted twice.

The model retains 2,640 HUD writes and 2,640 HUD readback commands per source.
It also retains original logical decoding and integrity requirements. No payload
is re-encoded for a bitrate comparison, and the protocol test's DATA records
mean already-decoded tile bytes, not a new literal-tile network format.

| Leaf tiles | Canonical reference BL8 reads | Canonical BL8 writes | Data + HUD commands | External-tree scenario commands |
|---:|---:|---:|---:|---:|
| V81 baseline | 14,158,800 | 14,806,800 | 31,378,560 | — |
| 1 | 7,370,884 | 8,065,924 | 17,849,768 | 66,398,978 |
| 4 | 8,325,124 | 8,065,924 | 18,804,008 | 32,675,830 |
| 16 | 9,964,644 | 8,065,924 | 20,443,528 | 24,362,062 |
| 64 | 11,539,632 | 8,065,924 | 22,018,516 | 23,546,814 |

A separate COPY-aware flat-SHA control skips eager hidden-tile reference reads
but still reads every visible delta tile to supply the flat canonical hash.
This separates that simple optimization from the new tree profile's benefits.

## State and hash resources are not free

The model deliberately prices the algorithm's full accepted-to-shadow tree copy
on every delta. A persistent/versioned tree could change that design, but is
not assumed. Digest comparisons, internal child reads, digest writes and root
reads are also counted. For a leaf grouping `g`, tree storage is two arrays of
`(2*next_power_of_two(leaves)-1)` SHA256 digests, plus the V81 maps' 6,075 logical
bytes. Control, hash-lane state, physical memory rounding and existing pipeline
buffers are additional.

The on-chip tree access floor assumes **one independent 32-bit read port and
one independent 32-bit write port usable each clock (1R+1W)**. Maps have a
separate read/write interface. This is a throughput bound for the stated access
policy, not a timed hardware schedule. The external scenario sends aligned
32-byte digest accesses through the frozen BL8 bridge, with maps still on chip;
row misses, refresh and scanout are omitted. Fine-grained trees perform poorly
in that scenario despite reducing image-data traffic.

SHA compression block counts include message padding. The original flat hash
needs 8,101 compression blocks/frame. TREE-2 totals over all 457 sources are
6,499,479 / 3,594,477 / 3,088,675 / 3,269,420 for g=1/4/16/64. Context hashing is
separately priced once per configuration. The isolated hash schedules assume
64 rounds/block, one round/clock and all input data ready at time zero. Work and
dependency lower bounds are retained separately from a deterministic list
schedule. Neither is packet-to-validated latency.

| Delta-frame modeled interval, ms | g=1 | g=4 | g=16 | g=64 |
|---|---:|---:|---:|---:|
| Data-service floor median | 7.294 | 7.858 | 8.513 | 8.836 |
| Data-service floor maximum | 11.702 | 11.702 | 11.702 | 11.702 |
| External-tree service floor median | 26.789 | 13.571 | 10.107 | 9.428 |
| External-tree service floor maximum | 36.157 | 18.042 | 13.329 | 12.294 |
| Isolated one-lane hash median | 9.708 | 5.615 | 4.879 | 4.772 |
| Isolated four-lane hash median | 2.430 | 1.407 | 1.224 | 1.197 |

These intervals overlap other work and must not be added as an end-to-end
prediction. Key hash work is a different worst case: g=1 needs 20.913 ms on the
assumed one-lane engine; g=16 needs 6.168 ms. Real input arrival, ports,
backpressure, decode, scanout, ESP32 transport and target timing remain unpriced.

Forty deltas after keys still lack candidate residency. Even without tree
metadata traffic their conditional frozen-service floor reaches 11.70174 ms,
so a lower median cannot establish strict maximum validation below 10 ms.
Shorter/pipelined memory service or a different cold-store strategy remains
necessary for that later goal.
