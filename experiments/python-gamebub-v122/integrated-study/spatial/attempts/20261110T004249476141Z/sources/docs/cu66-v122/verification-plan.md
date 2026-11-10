# V122 prepared admission bounds verification

V122 changes only the admission alias `fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv` from the qualified V121 eighteen-source composition. It resolves to `fpga/experiments/cu66-v122-bounds/cs88_admission_v91i2a.sv`. The V121 accepted-request queue remains byte-identical, as do the other sixteen source/include origins, source order, parameters and public interfaces. The frozen V121 functional index is `bafb9950bbf740f0b3182f4d7f5f19875e1fbfa65b85d3c193282ceec748b689`. The public cycle delta is zero.

Prepared full-width admission predicates must represent the original unsigned expressions at the existing consuming edge. Full64 length, full32 cursor, high bits, overflow, remaining-byte underflow, chunk boundaries, error priority and physical replay range checks remain part of the proof. Any coherent predecessor priming in directed fixtures must pass through the real preceding RTL edge; directly assigning the new predicate is insufficient. All predecessor-state assumptions must be recorded by the focused proof. The original checks and assertions remain active.

The focused admission selector is `experiments/python-gamebub-v122/bounds/results.json`. It must pass and bind the exact new source before any integration execution. Focused comparison checks public behavior each edge against the frozen V120 admission implementation already selected by V121, including legal and illegal boundary values, accepted packet data, held values, replay requests/responses, reset/start/abort priority, first-fault priority and physical ownership/drain behavior. The new predicates may change internal implementation only.

The integration adapters are reversible derivatives of frozen V121 runners, recorded in `scripts/cu66-v122/integration/derivation.json`. `contract.py` verifies both directions, the V121 source-map pin, all unchanged bodies, and the new lossless admission compile packaging. `spatial.py` retains independent V113 canonical goldens, the V117 command API and actual V97 transport adapter, all original functional/error/counter/drain checks, seeds107601/107602, and byte-exact stdout/event/canonical comparison to V121. `peer.py` retains the unmodified V118 prepared-fault bench, fourteen fault injections and fourteen canonical retries per seed, six real-parent abort/reset cases, physical debt checks, seeds115501/115502, and exact V121 stdout/event/canonical comparison. `live_guard/qualify.py` retains both byte and row variants, seeds116701/116702, all six terminal dictionaries, accepted bytes, C2 root, HUD SHA, seal,1025 hash jobs, ACK ownership/draining, wrong-token ACK and retry checks, and exact V121 stdout/event/actual/hash comparison.

All independent golden pins remain frozen. Expanded six-row canonical goldens SHA256 is `6d4e956a413d23d3945d30419c19dcb065423bfe486ea37506361cb0d9c73097`; complete-component canonical-actual TSV raw SHA256 is `a9f796047cc725a19e14dfae7bed75a57735e4c6d12def28ade7b98e99f8a861`. The parent fixture C2 root is `d918803829f69e61f9743eb94cfad209c74b203099c995aaa5c24984e3b555b9`, HUD SHA is `3aedb933fbc4fbbe7ca2a2fa6a0ad44582f3d1745b108945da0d2e10b0f2175f`, and seal is `a6a785a850784b3c4a7b145563412df6ff7bfcbb45128cf00daf9f29423f9ee1`. Repeated fixture records do not establish additional distinct gameplay frames.

Root grants at most two heavy jobs globally, each2CPUs/8GiB, with memory/PSI/watchdog gates and compiler job1. Spatial seeds remain sequential without an explicit source-bound two-slot grant. Freeze all proof-pinned scripts and this plan before execution. Never edit frozen V120/V121 sources, benches, scripts, selectors, receipts, the SrcB18 artifact, or unrelated markers. Every stage writes a fresh attempt and retains failures. No older qualification substitutes for new candidate execution.

```bash
python3 scripts/cu66-v122/integration/prepare.py
python3 scripts/cu66-v122/integration/contract.py
python3 scripts/cu66-v122/integration/spatial.py
python3 scripts/cu66-v122/integration/peer.py
python3 scripts/cu66-v122/integration/live_guard/qualify.py
```

After focus passes and Root grants slots:

```bash
python3 scripts/cu66-v122/integration/peer.py --run
python3 scripts/cu66-v122/integration/spatial.py --run
python3 scripts/cu66-v122/integration/live_guard/qualify.py --run --root-grant ROOT_V122_BOUNDS_PARENT
python3 scripts/cu66-v122/integration/collect_final.py
python3 scripts/cu66-v122/audit_functional.py
```

The collector retains the corrected V121 strict compile policy: every Verilator compile uses `--assert -Wall` without warning downgrades; executable builds supply strict host `-CFLAGS`; only the frozen `v97_forward` generated-library build may omit `--exe`/host flags, followed by a separately strict C++17 `-O2 -Wall -Wextra -Werror` adapter build. Source and artifact hashes resolve relative to the actual receipt directory after resolving each selector. The unified index schema is `v122-bounds-functional-composition-v1`, status `PASS_V122_BOUNDS_FULL_FUNCTIONAL`, with all eighteen origins and focused/spatial/peer/parent selector and receipt pins. It declares retained oracles, assertions active, exact public cycles and delta0.

Native qualification independently consumes that index. Hardware SourceB100MHz remains the qualified V120 control; failed V120 B125 and failed V121125 are diagnostic comparisons. The native terminal auditor rehashes source/tooling/recipe/retained/external artifacts, verifies fresh RTL synthesis, the fixed part/tool/8ns clock/default synthesis recipe, and independently parses all twelve timing metrics, twelve coverage checks, routing, worst setup path and fresh methodology details. Optional Python3.14 Zstd EDIF enrichment inventories mapped queue and admission FFs and global carries; Python3.10 can verify core evidence without Zstd. Timing success requires all setup/hold/pulse/coverage/routing gates and a separate fresh same-source repeat. This component qualification does not establish full-parent/board routing, physical service, hardware30fps or validated hardware decode below10ms.
