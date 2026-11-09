# V116 LIVE parent with byte and three-slot row joins

Status: prepared, not yet RTL qualified. The LIVE worker has launched no compile
or simulation. The runner requires a Root heavy-slot grant and completed V116
source and focused receipts before executing.

The parent instantiates the actual selected 18-source V116 producer, the frozen
C2/SHA validator and bank publication logic, and either the frozen V91l byte
write/hash join or the V116 three-slot row join. Wrapper parameter ROW_WRITES
selects the variant. Both expose candidate_req_data[63:0] and
candidate_req_bytes[3:0]; the byte branch zero extends its frozen payload and
reports one byte, while the row branch reports eight. join_state is three bits
to represent the row join's aggregate state, with fill and delivery diagnostics.
The V115 local registered producer fault cancellation, immediate parent masks,
and accepted-response drain connections are unchanged.

The preparer derives the wrapper and C++ bench reversibly from frozen V115 LIVE
sources. Exact frozen copies and the full reversible recipe are retained.
Every original C++ need() check remains present. Byte mode retains its original
physical request/ACK count checks. Row mode adds the declared 70,080 physical
request/ACK expectation while retaining the original 560,640 expanded-byte,
canonical/HUD and hash-delivery oracles. All 1,025 hash jobs, exact root/HUD/seal
commitments, accepted pixels/HUD/qcache, immutable bank checks, wrong-token
physical debt, clean retry without reset, and final publication/drain checks
remain active. No expected packet or hash fixture is rewritten.

The bench independently expands each one- or eight-byte descriptor and compares
every byte against the original canonical/HUD golden. A successful matching ACK
commits those bytes to the abstract bank and marks their owner epoch. Every
hash delivery requires the matching value and a successful ACK mark for the
current frame epoch. Repeated writes within one epoch and requests to immutable
banks fail independently.

The finite candidate-memory service has one pending physical request. Its
16-bit data path charges ceil(request_bytes/2) model clock edges, plus two
overhead edges in the fast profile or 8–16 overhead edges in the stalled
profile. An eight-byte row therefore needs six fast edges or at least twelve
stalled edges. Byte control uses the same width-derived rule. Responses retain
the full epoch/token/bank/address tuple. Wrong ACKs do not retire debt; the
original finite due wait, fault injection and matching drain are retained.
All RTL and service logic advance on every modeled clock edge.

The live_fences record separately timestamps the last of all 518,400 canonical
producer acceptances, successful canonical write ACK bytes, canonical hash
deliveries, reconstruct-done, Merkle root completion, HUD digest completion,
frame seal completion, validated commit and abstract presentation. Canonical
completion is determined by byte counts, never by the largest raster address
in the tiled output order. Handshake/result acceptance uses cycle+1 before the
rising edge; registered completion pulses use the same edge after evaluation.
Hash result records use that accepted-edge convention too. Actual validator
localparams are pinned as LEAF=0, EMPTY_LEAF=1, NODE=2, HUD=3 and SEAL=4; the
actual root result is NODE at node 1. Job-kind totals must be 508/4/511/1/1.
Only causal fence ordering is asserted. In particular there is no constraint
requiring the final physical HUD write ACK to precede the root computation.

The wrapper exposes reporting-only slot occupancy and fill/wait/hash indicators
from the actual frozen owner encodings. Reports include occupancy histograms,
coexisting fill/physical-wait/hash edges, simultaneous producer/hash transfer
while a physical owner exists, and per-phase producer/HUD/request/hash/service
stall counts. Phase attribution uses the declared priority list in the record;
it does not imply that physical activities cannot overlap. These diagnostics
do not change readiness, owner transitions or payloads.

Fast and stalled comparisons use the same bounded service rule and seed.
Different accepted traffic causes different RNG draw counts, so stalled byte
and row variants do not have identical cycle traces. The integrated fault test
covers wrong-token ACK, retained debt, matching drain and retry. Integrated
bus-error injection is outside this parent test; successful ACK byte counts
exclude bus errors, and the independently qualified rowjoin unit proof retains
its separate fault coverage.

Preparation reconstructs the current 18-source contract through
scripts/cu66-v116/spatial.py without requiring the future spatial summary or
guessing its SHA. At execution, the runner requires the completed V116 spatial
selector, validates its selected receipt and every selected source/artifact
hash, and checks that its source origins and lossless admission packaging
exactly match the reconstructed contract. It also validates the Rice, admission
and rowjoin focused selectors, raw receipts, source/artifact hashes, actual run
flags, assertions and strict compiler commands. The selected receipt SHA is
captured at launch. The rowjoin selector is
experiments/python-gamebub-v116/rowjoin/results.json.

Preparation-only check:

```
python3 scripts/cu66-v116/live/qualify.py
```

Root launch after source/proof completion and a heavy-slot grant:

```
python3 scripts/cu66-v116/live/qualify.py --run --root-grant ROOT_GRANTED_LIVE_SLOT
```

Default variant both compiles the byte and row parent separately and runs each
with seeds 116701/116702 and fast/stalled profiles. --variant byte or --variant
row bounds a diagnostic attempt; qualified_variants records exactly what ran.
Attempts preserve exact commands, full source snapshots, lossless admission
compile fragments, binary hashes, resource samples, verdicts, expanded-byte
output, hash records and partial failures. actual_RTL_run is persisted true
before simulation launch, including failing simulations.

The backend is pinned Verilator 5.020 image
sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf.
Builds use --assert -Wall and C++17 -O2 -Wall -Wextra -Werror, -j 1 and no warning
suppression. Host optimization changes simulation speed only. Each command has
container and host watchdogs, two CPUs, 8 GiB RAM, memory+swap fixed to 8 GiB,
and disabled networking. Launch requires available RAM >=8 GiB, PSI full avg10
<1 and combined memory+swap utilization <0.85. Stop thresholds are available
RAM <4 GiB, combined utilization >=0.9, or PSI full avg10 >=5 twice. Root
controls the global maximum two heavy jobs.

This is an abstract finite write-service and publication model with actual
selected RTL and software HUD decoding. It does not qualify physical SDRAM,
ESP32 execution, full RTL HUD decoding, full-parent routed timing, achieved
hardware frame rate, or validated decode under 10 ms.
