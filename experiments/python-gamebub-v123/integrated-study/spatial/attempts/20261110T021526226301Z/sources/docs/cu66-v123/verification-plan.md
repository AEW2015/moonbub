# V123 scratch rank verification

V123 replaces only alias `fpga/experiments/cu66-v91g2/packed_scratch_v91g2.sv` with `fpga/experiments/cu66-v123-rank/packed_scratch_v91g2.sv` relative to the frozen V122 eighteen-source index `c6c12f453375ed1d096960d2325c98e7ef17562229893360785a9455f4bce5a4`. The V122 bounds admission source, its lossless compile packaging, the V121 prepared request queue, and all other source/include origins and ordering remain unchanged. Public cycle delta is zero.

The candidate prepares the six-bit rank relation as a64-bit threshold mask on the existing APPEND edge that updates previous_position. The sparse ordering predicate retains live full32 high/block comparisons, including arbitrary initialized previous-position high bits. Rank thresholds, all64 raster indices, all8 phase encodings, raw/DC/AC behavior, value/band/geometry/epoch checks and first-fault priority remain part of the focused proof. The mask may be consumed only with the matching previous-position/phase/epoch owner; cancellation, accepted physical memory debt and original drain behavior remain unchanged. New directed fixtures must prime metadata through a coherent real APPEND predecessor, preserve all existing assertions/checks, and distinguish fixture priming from natural packet cycles.

The new focused selector is `experiments/python-gamebub-v123/rank/results.json`. It must bind the exact scratch candidate and pass before integration. Old V122 bounds and V121 queue focused proofs remain directly pinned. Frozen V122 stage receipts retain prior focused selector/source pins and serve as immutable exact-cycle controls. No older proof substitutes for newly executed candidate RTL.

`integration/prepare.py` derives full spatial/actual transport, physical-debt peer, guarded byte/row parent and final collection adapters reversibly from frozen V122 scripts. Its derivation records every edit, original/candidate hashes, zero removed checks and zero public cycle delta. `contract.py` verifies forward and reverse reconstruction, all18 origins and the scratch-only change. Default preparation launches no tools.

The full runner retains V113 independent canonical goldens, the V117 command API and actual V97 transport, seeds107601/107602,22 case profiles and21 directed checks per decoder seed,12 successful transport profiles and original command/abort/reset checks. It requires exact V122 stdout, events and canonical artifacts, including every cycle. The peer runner retains the frozen V118 fault bench,14 prepared child fault injections and14 canonical retries per seed115501/115502, six real-parent abort/reset cases, physical ownership/drain checks, and exact V122 stdout/event/canonical artifacts. The guarded parent retains byte/row variants and seeds116701/116702; all six terminal dictionaries, canonical/accepted bytes,1025 hash jobs, C2 root, HUD SHA, seal, ACK accounting, physical ownership/draining, wrong-token ACK/retry checks and raw stdout/event/actual/hash cycles must equal V122.

Expanded six-row canonical goldens SHA256 remains `6d4e956a413d23d3945d30419c19dcb065423bfe486ea37506361cb0d9c73097`; complete-component canonical-actual TSV raw SHA256 remains `a9f796047cc725a19e14dfae7bed75a57735e4c6d12def28ade7b98e99f8a861`. Parent C2 root remains `d918803829f69e61f9743eb94cfad209c74b203099c995aaa5c24984e3b555b9`, HUD SHA `3aedb933fbc4fbbe7ca2a2fa6a0ad44582f3d1745b108945da0d2e10b0f2175f`, seal `a6a785a850784b3c4a7b145563412df6ff7bfcbb45128cf00daf9f29423f9ee1`. Repeated fixture/profile records do not establish additional distinct gameplay frames.

Freeze all proof-pinned source, scripts and this plan before execution. Root grants at most two heavy jobs globally, each2CPUs/8GiB RAM and8GiB RAM-plus-swap, compiler job1. Preserve available-memory/full-PSI/combined-memory gates and all live watchdogs. Spatial seeds stay sequential without an explicit source-bound two-slot grant. Every stage retains fresh attempts and failures. Existing V120/V121/V122 files, SrcB18 and unrelated markers remain untouched.

```bash
python3 scripts/cu66-v123/integration/prepare.py
python3 scripts/cu66-v123/integration/contract.py
python3 scripts/cu66-v123/integration/spatial.py
python3 scripts/cu66-v123/integration/peer.py
python3 scripts/cu66-v123/integration/live_guard/qualify.py
```

After focused PASS and Root slot grants:

```bash
python3 scripts/cu66-v123/integration/peer.py --run
python3 scripts/cu66-v123/integration/spatial.py --run
python3 scripts/cu66-v123/integration/live_guard/qualify.py --run --root-grant ROOT_V123_RANK_PARENT
python3 scripts/cu66-v123/integration/collect_final.py
python3 scripts/cu66-v123/audit_functional.py
```

Every Verilator compile retains `--assert -Wall` without warning downgrades. Executable builds require strict host `-CFLAGS`; only the frozen generated v97_forward library may omit --exe/host flags, followed by its separately strict C++17/-O2/-Wall/-Wextra/-Werror adapter. Resolve selectors to actual receipt directories before checking artifact hashes. The unified index schema is `v123-rank-functional-composition-v1`, status `PASS_V123_RANK_FULL_FUNCTIONAL`, stages focused/spatial/peer/parent with selector and receipt pins, all18 origins, retained oracles, active assertions and exact public cycles/delta0.

The terminal native auditor independently checks the actual V123 scratch-only composition against V122, rehashes source/tooling/recipe/retained/external artifacts and verifies fresh RTL synthesis with the fixed part/tool/8ns recipe. It independently parses timing, coverage, routing, worst setup path and fresh methodology; compares QoR to V122125 (WNS−1.949ns,TNS−4597.575ns,11866 setup failures), retains V121125 and historical B125 diagnostics, and verifies qualified SourceB100 initial/repeat controls. Optional Python3.14 Zstd enrichment counts both scalar and vector FD instances in scratch/admission, the unchanged queue and global carries; Python3.10 verifies core evidence without Zstd. A positive initial route requires an independent fresh same-source repeat; a negative route is not qualified by rerouting unchanged. Component8ns timing, complete-parent/board routing, physical service, hardware30fps and hardware validated decode below10ms remain separate gates.
