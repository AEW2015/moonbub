# V118 finite-memory LIVE parent results

All four LIVE parent profiles passed with the selected18-source V118 component, original byte/owner/ACK assertions, actual RTL C2/SHA/HUD/seal validation, and clean retry after an injected wrong-token ACK. The [terminal receipt](../../experiments/python-gamebub-v118/integrated-study/live-guard/attempts/20261109T150253620173Z/receipt.json) is source-bound; the [independent expert audit](../../experiments/python-gamebub-v118/audit/live-terminal-expert.json) verifies all source/artifact hashes and recomputes every recorded SHA256 job using Python.

The measured interval starts at the final accepted outer packet byte and ends at validated commit. It includes canonical reconstruction, successful memory ACKs, canonical/HUD hashing and seal validation. Safe presentation follows a separate fence. These are real simulated edges; the milliseconds below assume a clock and are **not achieved hardware timings**.

| Memory profile | V117 cycles | V118 cycles | Change | Conditional125MHz | Conditional100MHz |
|---|---:|---:|---:|---:|---:|
| Byte, fast |3,704,690 |3,704,705 |+15 |29.637640ms |37.047050ms |
| Byte, stalled |9,484,122 |9,484,147 |+25 |75.873176ms |94.841470ms |
|8-byte row, fast |1,126,533 |1,145,104 |+18,571 /+1.65% |9.160832ms |11.451040ms |
|8-byte row, stalled |1,553,878 |1,553,197 |−681 |12.425576ms |15.531970ms |

The fast row fixture retains104,896 cycles below a hypothetical125MHz10ms budget. It exceeds the100MHz10ms budget by145,104 cycles. The stalled row fixture exceeds the125MHz10ms budget. The small negative stalled delta does not establish an architecture speedup: the same bounded service rule and seed can draw a different random sequence because request/traffic timing changed.

The row service model transfers8 bytes over four16-bit data edges, with two fast overhead edges or8–16 stalled overhead edges. Byte service transfers one byte over one data edge with the same overhead rule. Only one physical service lease is allowed. This is a finite abstract memory model, not a physical SDRAM controller, contention model, board measurement or full-parent routed design.

Each profile produced518,400 canonical bytes and42,240 HUD bytes;560,640 accepted bytes and successful ACK bytes matched the independent goldens exactly. Byte mode used560,640 physical requests/ACKs; row mode used70,080. The Python audit independently reconstructed all1,025 hash jobs:508 real leaves,4 empty leaves,511 internal Merkle nodes, one HUD digest and one frame seal. It maps accepted raster-order memory into the validator's8×8 tile stream before hashing, checks every recorded job digest, and reproduces the fixture root, HUD digest and seal.

For every profile, the retained transform/canonical trace has8,100 complete canonical tiles and7,806 records at each assemble, dequant and residual stage. Successful whole-owner/value event semantics match V117 after excluding declared cycle/interleaving changes. The byte/ACK/hash/root/HUD/seal/commit/presentation ordering checks passed.

The raw local replay ledger recorded33,384 actual reads and33,384 matching whole responses per profile, with literal integer0 pending at terminal. Each injected parent fault allowed exactly one bounded private residual acceptance before registered producer cancellation; its complete owner and arithmetic golden were checked. Observation masks did not feed back into internal work or mask physical responses. No private cancel-gap local read or revoked response occurred in these fixtures, so those particular gap cases are not claimed as exercised here. Separate peer tests cover their own response-debt fault scope.

The retained independent C++ testbench checks the candidate ACK bus and physical owner conservation. The archived logs do not contain a complete per-cycle ACK bus trace for a second Python bus replay. This audit rechecks the actual byte artifacts, digest records, semantic traces, terminal ledger counters, original oracle source and source identity without pretending to rerun that bus.

This campaign contains one successful keyframe plus wrong-ACK recovery per profile. It does not establish sustained distinct-frame30fps, a worst-case game-content bound, ESP32 execution or under10ms validated hardware decoding. Software performs HUD semantic decoding; RTL performs its digest and frame commitment validation. Component OOC125/100MHz route results must be reported separately: that component excludes the full parent hash/write/service implementation and cannot establish the parent's physical clock. Full-parent timing, memory/display integration and hardware measurements remain open.
