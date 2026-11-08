# V107 registered tuple validation flags

Focused actual RTL PASS on the first strict attempt. Production, runner and verification sources are frozen after qualification. No native run is authorized for this candidate yet. The measured TABLES route and static/live classification are pinned in [metadata-control-next.md](metadata-control-next.md).

Three isolated production files under `fpga/experiments/cu66-v107-meta-flags/` derive from frozen stage `28de630d…`, inverse `c93bec92…` and top `d9441f5a…`. The exact recipe preserves the entire original 130-bit payload assignment, unpacking, ready/valid and fence process. Two unreset token-owned bits share precisely its acceptance edge. Static geometry/qcell failure is bit one; static signed-value/scale failure is bit zero. Existing occupancy masks unowned contents. Holding, replacement and cancellation cover the whole 132-bit record without another stage or public cycle.

The inverse consumes registered flags but keeps index comparison, full 108-bit FILL-owner equality, token exhaustion, done/partial-tile detection, immediate kill/ready and arithmetic faults in their original places. Input priority remains done4, index1, static-or-live metadata2, domain3, token7. The original coefficient-bank write guards and main math-case source ordering remain exact, including a coefficient write coincident with a later arithmetic fault. Public debug outputs, including invalid/unowned inverse views and raw top coefficient outputs, remain unchanged.

All original SystemVerilog assertions remain. New assertions compare consumed flags to the original pure expressions, and hold both sideband bits under backpressure. They qualify owned input handshakes and ignore unowned data after flush. The exact qualified geometry helper is copied to the stage; its inverse copy remains solely for simulation invariants, so synthesis does not retain a parallel tuple-to-WE geometry qualifier.

`scripts/cu66-v107/meta_flags.py` prepares no source edits during execution. It checks the literal recipe, freezes all sources and then runs these two strict actual RTL proofs sequentially:

- Stage: the original independent queue/fence/conservation driver, extended with independent integer Cartesian geometry and signed-domain checks for the two bits. Actual helper outputs cover all 32,768 binary plane/tile inputs, static metadata covers all 67,108,864 plane/tile/qcell combinations, and scale/value covers all 262,144 combinations. The finite exhaustive phase emits aggregate counts while the randomized phase retains token traces, avoiding a multi-gigabyte exhaustive transcript. Both random seeds retain held/replacement/reset/start/cancel, offered-final-word and done-fence cases. The original five-million-edge random watchdog is retained separately from the exactly bounded exhaustive phase.
- Inverse: complete old/new modules against actual `c93bec92…`, preserving every inherited public/store/priority and independent historical math check. It adds equality of inverse control, owner arrays and arithmetic interfaces, plus 51 prepared input-versus-arithmetic fault cases across dequant wait, IDCT wait and emission. Those explicitly cover error priorities and same-edge payload writes; prepared states are labeled and do not claim packet reachability. Both sides instantiate the actual selected IDCT-area baseline `1ed49416…` and dequant baseline `1ce06c26…`. An independent C++ oracle supplies tuple flags and checks fault/store behavior. No public or invalid debug output is masked.

Frozen production SHA-256 values are stage `ea53b408aab5e522dfb2c4ffc2eefee41d58af37032cedc409e74815ab35dab9`, inverse `afc0ebb4f8ea72e5a07b4606f0d2f5fa4f6ab8ec858e4a35203a625f34541738`, top `582e6cf1f56d678c0356822b6e2b4e8371bd43827870b7a8fb947b1fb4e61e86`. Independent read-only review reconstructed and reversed all three source recipes and found no functional issue. This is source review, not execution signoff.

Two source-preparation anchor mistakes are retained under `experiments/python-gamebub-v107/meta-flags/preparation/001` and `002`; neither launched compilation or RTL execution. The eventual focused selected pointer is `experiments/python-gamebub-v107/meta-flags/results.json`, with `status`, `actual_RTL_run` and pinned `source_sha256`. Parent canonical and fresh comparisons, followed by any separately authorized fixed-10-ns native run, remain required. The upstream geometry-to-flag-D path, downstream live owner/WE cone, routing and fanout can still fail timing; no frequency gain is claimed.

## Focused results

The [selected receipt](../../experiments/python-gamebub-v107/meta-flags/attempts/20261108T061004970792Z/results.json), SHA-256 `cc5bb5aa21a2c820a4c7e04b2e8b171e45312ee0d8921cb8b776633f4861690b`, records strict zero-Verilator-warning compilation and both seeds 108001/108002. No assertion or checker was disabled, downgraded or bypassed. Execution completed in 33.1 seconds, with the stage and inverse proofs sequential in one granted heavy lane.

| Actual RTL result | Count |
| --- | ---: |
| Stage clock edges | 67,715,579 |
| Complete helper plane/tile cases | 32,768 |
| Full plane/tile/qcell tuples | 67,108,864 |
| Full scale/value tuples | 262,144 |
| Random/adversarial seeds | 2 |
| Stage flush discards | 28 |
| Paired inverse clock edges | 41,697 |
| Added concurrent input/arithmetic fault cases | 102 |
| Preserved original late arithmetic/write cases | 4 |
| Historical boundary cases | 96 |
| Independently expected residual samples | 5,376 |

All four combinations of metadata/domain flags were explicitly held while a different offered tuple stalled, then replaced and consumed. Independent UP/DOWN/DISCARD conservation passed. Both inverse seeds preserved every inherited public/store/golden/priority check; all added owner/control/intermediate interface comparisons also passed. Prepared cases exercise all input errors 1/2/3/4/7 and their priority against dequant 5 and IDCT 6, while actual interface-driven tests retain all fifteen historical ownership/reset/abort/retry checks per seed.

[audit.json](../../experiments/python-gamebub-v107/meta-flags/audit.json) rechecks all 25 source hashes, 51 artifacts, the selected receipt hash and strict compile/assertion settings. The production source bytes remain the reviewed hashes above. The focused result is not a new complete canonical/fresh pipeline execution or routed timing result. Full integration must retain exact public cycles, events, counters and canonical goldens; future native selection must be separately authorized.
