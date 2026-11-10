# V124 producer owner-lane verification

V124 changes only alias `fpga/experiments/cu66-v91k/cs88_coefficients_v91k.sv` to `fpga/experiments/cu66-v124-owner/cs88_coefficients_v91k.sv` relative to the frozen V123 index `0a665162168f4aaa9bff29546263d57b61abbef50bb65fefc2606de919f15d00`. All 18 source/include origins and ordering are checked. V123 scratch rank source and single-module packaging, V122 admission bounds and its lossless split packaging, V121 queue, parameters and public interfaces remain unchanged. Public cycle delta is zero.

The candidate computes complete owner comparisons for each producer bank before selecting their one-bit results. The two tile_owner_match lanes and child_owner_match remain combinational; no new register, phase or public delay is introduced. Root approved KEEP on exactly the two tile_owner_match result bits to preserve the comparison lanes. No DONT_TOUCH or physical placement attribute is added; terminal auditing independently checks the exact added-attribute scope against V123. Full epoch/block widths, selected versus unselected bank semantics, physical ownership, accepted response debt, reset/start/abort/fault priority, held offers and clean retry behavior must remain exact. Focused fixtures must preserve complete owner tuples and retain all previous assertions/checks; no new selector assumption, response mask or synthetic ownership repair may manufacture PASS.

The new focused selector is `experiments/python-gamebub-v124/owner/results.json`. It must bind the exact candidate and pass before integration. Existing V123 rank, V122 bounds and V121 queue focused proofs remain directly selected. Frozen V123 stage receipts retain every earlier focused selector/source pin. New candidate execution is required for every stage; prior execution is only an immutable comparison control.

`integration/prepare.py` records reversible derivation of all four adapters from frozen V123: spatial/full decoder plus actual V97 transport, physical-debt peer, guarded byte/row parent and final collector. Every original check remains; derivation asserts zero removed checks and zero public cycle delta. `prepare_audits.py` also records uniquely reversible auditor hunks and preserves or increases integrity-check call counts; inherited rank/bounds semantic functions remain intact. `contract.py` verifies both directions, all source hashes, exact source order and the producer-only change. Root plans, analytical models and unrelated documents are not proof inputs.

Spatial retains the frozen V117 command API, V113 independent canonical goldens and actual V97 transport. Seeds 107601/107602 retain 22 decoder profiles and 21 directed checks each, plus all original transport profiles, accepted command tuples and abort/reset/retry checks. Stdout, events and canonical bytes, including every cycle, must exactly match V123. Peer retains the frozen V118 injection contract, all physical-debt/held/error/owner checks, 14 prepared child fault injections and 14 canonical retries per seed 115501/115502, including six real-parent abort/reset cases. Stdout/event/canonical streams must match V123 exactly. Parent retains byte and row variants, seeds 116701/116702, all six terminal dictionaries, accepted bytes, 1025 hash jobs, C2 root, HUD SHA, seal, ACK accounting, physical draining, wrong-token ACK and retry checks. All stdout/events/actual/hash cycles must equal V123.

Expanded six-row canonical goldens SHA256 remains `6d4e956a413d23d3945d30419c19dcb065423bfe486ea37506361cb0d9c73097`; complete-component canonical-actual TSV raw SHA256 remains `a9f796047cc725a19e14dfae7bed75a57735e4c6d12def28ade7b98e99f8a861`. Parent C2 root remains `d918803829f69e61f9743eb94cfad209c74b203099c995aaa5c24984e3b555b9`, HUD SHA `3aedb933fbc4fbbe7ca2a2fa6a0ad44582f3d1745b108945da0d2e10b0f2175f`, and seal `a6a785a850784b3c4a7b145563412df6ff7bfcbb45128cf00daf9f29423f9ee1`. Repeated fixture/profile records are not additional distinct gameplay frames.

Freeze all proof-pinned source, scripts and this plan before execution. Root grants at most two heavy jobs globally, each capped at 2 CPUs, 8 GiB RAM and 8 GiB RAM-plus-swap, compiler job 1. Preserve available-memory/full-PSI/combined-memory gates and live watchdogs. Spatial seeds remain serial without an explicit source-bound pair grant. Retain fresh attempts and failures. Existing V120/V121/V122/V123 files, SrcB18 and unrelated markers remain unchanged.

```bash
python3 scripts/cu66-v124/integration/prepare.py
python3 scripts/cu66-v124/integration/contract.py
python3 scripts/cu66-v124/integration/spatial.py
python3 scripts/cu66-v124/integration/peer.py
python3 scripts/cu66-v124/integration/live_guard/qualify.py
```

After focused PASS and Root slot grants:

```bash
python3 scripts/cu66-v124/integration/peer.py --run
python3 scripts/cu66-v124/integration/spatial.py --run
python3 scripts/cu66-v124/integration/live_guard/qualify.py --run --root-grant ROOT_V124_OWNER_PARENT
python3 scripts/cu66-v124/integration/collect_final.py
python3 scripts/cu66-v124/audit_functional.py
```

Every Verilator compile uses `--assert -Wall` without warning downgrades. Executable builds require strict host `-CFLAGS`; only the frozen generated v97_forward library may omit --exe/host flags, followed by its separately strict C++17/-O2/-Wall/-Wextra/-Werror adapter. Resolve every selector to its actual receipt directory before hashing artifacts. The unified index is schema `v124-owner-functional-composition-v1`, status `PASS_V124_OWNER_FULL_FUNCTIONAL`, with focused/spatial/peer/parent selector and receipt pins, all 18 origins, active assertions, retained oracles and exact public cycles/delta 0. The independent functional audit rehashes source/artifact closure and raw streams, checks the new focused semantics and retains independent V123 rank/V122 bounds checks.

Native qualification independently consumes that index. Its terminal auditor checks the producer-only V123 composition delta, source/tooling/recipe/retained/external hashes, fresh RTL synthesis, fixed part/tool/default synthesis/8 ns recipe, actual timing, coverage, routing, worst setup path and fresh methodology. Primary QoR control is V123125 receipt `20261110T024415819812Z`: WNS −1.086 ns, TNS −1709.649 ns and 6724 setup failures. V122125, V121125 and B125 remain historical diagnostics. Qualified Source B100 initial/repeat controls remain independently checked. Optional Python 3.14 Zstd enrichment inventories scalar/vector producer FFs and named owner-lane cells, unchanged scratch/admission/queue registers and global carries; Python 3.10 verifies core evidence without Zstd. A positive initial route requires a fresh same-source repeat; rerouting a negative source unchanged does not qualify it. Component clock, full-parent/board routing, physical service, hardware 30 fps and hardware validated decode below 10 ms remain separate gates.
