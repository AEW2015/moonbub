# V118: owned residual pipeline and spatial control

Baseline is published V117 `7aad458`. Primary goal is routed125MHz (8ns), with separately measured100MHz control. V117 final C failed125MHz WNS−1.679ns and100MHz−0.317ns. No hardware30fps or validated under10ms milestone is closed.

1. Capture complete residual tuple and expected owner, validate in a register stage, commit locally atII1. Keep separate accepted/committed frontiers, stop after64 accepts, arm math after final validated commit. Earlier fault revokes younger tuples.
2. Copy sole engine result into inactive canonical owner in four128-bit beats. No extra full tile buffer; engine holds result until fourth beat; READY follows complete copy. Cover reset/cancel/fault at every beat and held older owner.
3. Spatial scratch decisions compare per-band local counters/head state before narrow selection. Preserve range, epoch, error priority and physical debt. Seek existing-edge preparation; declare any changed schedule.
4. Run strict focused tests, complete original component canonical/transport goldens, peer-kill/retry and guarded finite-memory LIVE parent metrics. Original V117 exact-cycle checker stays frozen. New V118 comparator excludes timestamps/interleaving for successful accepted events, keeps every value/owner tuple; original error/debt/held assertions remain active.
5. Fresh RTL synth/place/route at8ns and10ns using fixed V117 method. At most two actual source compositions, four initial source/clock trials and two positive fresh repeats (one perclock). No negative reroute or strategy search. Any positive requires identical-source/tool/recipe fresh repeat before qualification.

Root alone grants at most two heavy slots, each2CPU/8GiB and no additional swap. AvailableRAM/PSI are primary gates; combinedRAM/swap secondary. Native tools use existing legitimate readonly license. MCP currently returns Transport closed, so established native CLI is recorded. No hardware contact or bitstream generation.

Results will distinguish exact measured clocks/cycles from conditional milliseconds; no synthesized-clock estimate or single fixture becomes sustained hardware30fps evidence. See machine-readable [policy](../../experiments/python-gamebub-v118/study-policy.json).

Outcome: selected focused, full/transport, peer, reachable-response and guarded-parent suites passed. Two fresh identical-source 100 MHz component routes passed with +0.061 ns WNS. The 125 MHz route failed at −1.499 ns. No second source composition was selected; [next coordinated work](native-mapping-next.md) addresses the actual independent failing families. Hardware 30 fps and validated under-10-ms decoding remain open. See [results](README.md) and the [handoff](handoff.md).
