# V127: compare complete owners before mode selection

This is a bounded, cycle-preserving timing experiment from V126 commit
`0d03abbd5db89cb941286626de136ac023809eac`. The goal is a correctly constrained
125 MHz component followed by complete-parent and physical streaming
qualification. No version number or local path improvement passes those gates.

## Measured cause and selected change

V126 finishes routing at −1.867 ns WNS, −4,427.979 ns TNS and 10,868 setup
failures. Its global path starts at scratch tile-overlap mode, traverses
selected owner metadata and readiness, then reaches scratch state. The
[V126 proposal](../cu66-v126/next-timing.md) records that path and the separate
placed command/start/reset return path. V123 remains a better historical
global comparison at −1.086 ns WNS; it is not a timing pass either.

V127's first trial exposes raw scalar `active_epoch` and `output_block` through
the scratch and child interfaces. The producer compares complete 32-bit epoch
and 16-bit block values in three independent Boolean expressions—bank0, bank1
and scalar—before choosing one match bit using tile mode and bank selection.
Existing bank views and the original two KEEP bits remain. No new synthesis
attribute, register, reset, public top port, wire format or cycle is intended.
The selected source delta is exactly scratch, child pipeline and producer;
the other fifteen origins remain V126 bytes, with the original eighteen-file
core order and twenty-four-file full-parent order.

The scalar fallback currently compares already-selected output tags, allowing
mode selection before wide comparison despite the existing two bank lanes.
Raw scalar views remove that source-level dependency without presuming that
ready or valid certifies an owner. Synthesis may refactor the expression again;
actual mapped topology and timing must decide its physical benefit.

## Function before implementation

Retain every original assertion, require body, accepted read/write debt,
first-error rule, complete owner key, stale/cancel behavior, and canonical
stream oracle. Additional assertion text may extend a block only through an
exact reversible recipe; the original guarded block must be recovered intact.
The selected baseline verification adapter connects both additional child
output views to private wires and checks them against the actual baseline
scratch registers. This verification-only repair retains strict lint and
baseline production bytes; its failed compile and revision-2 input freeze are
preserved in the [focused results](focused-results.md).

Require source-extracted scalar tests and clocked paired-producer checks for
all mode/bank choices, invalid/unready cycles, high bits, full32/full16 wrap,
duplicate/opposite/foreign owners, held results, reset/abort and response
overlaps. Retain V126 producer address/ROM proofs and all preceding ownership,
rank, admission, bounds and queue tests. New payload/owner forces cannot
manufacture a proof. Prepared contexts and primer clocks remain separately
identified from natural caller traffic.

After focused PASS, execute complete decoder and actual V97 transport, peer,
and both byte/row ordinary/stalled parent profiles. Require exact V126 raw
stdout/event/canonical/hash/terminal comparisons: four spatial, two peer and
four parent sets, with zero public-cycle delta. An independent full audit must
bind all eighteen origins, commands, artifacts and raw verdicts before native
implementation is released. A clean compiler exit alone is insufficient.

## Fixed physical experiment

Use Vivado 2026.1/build6511674, xc7a100tcsg324-1 and the byte-identical V120
core `run.tcl`, `report.tcl` and 8 ns clock. Load the clock before fresh RTL
synthesis; no checkpoint starts implementation. Preserve synthesis Default,
opt Default, place ExtraNetDelay_high and route Default, with no separate
phys-opt, timing exceptions, guessed I/O delays or constraint relaxation.
The connector transport is unavailable; retain its error and the established
pinned Docker/CLI implementation and standalone Verilator 5.020 backend.

Run one fresh initial implementation for the selected composition. Do not
reroute an unchanged negative composition to search for a favorable result.
A positive global result requires its separate identical-source/tool/recipe
fresh repeat. Promotion requires nonnegative WNS/WHS/WPWS, zero total/failing
setup/hold/pulse, zero unconstrained internal endpoints and zero routing
errors in both runs. Aim for at least 0.2 ns setup margin. Missing component
I/O constraints stay an explicit board-integration limitation, not an excuse
to invent delays or waive a path.

Apply the same frozen read-only query to V126 and V127 checkpoints. Retain all
129 previous path families and add actual tile mode, scratch raw mode, scalar
epoch/block sources and the scalar owner net. Inspect complete startpoints of
named owner nets with bounded queries; missing, empty, renamed or truncated
objects remain explicit gaps. Compare global timing alongside producer D/CE/Q,
scratch release/state, mode/owner, admission, RAW and refill families. Report
adverse changes, fresh methodology counts, control sets and real mapped
LUT/FF/BRAM/DSP/CARRY inventories, not source declarations alone.

## Resource and evidence policy

At most two heavy study jobs may run, each limited to two CPUs, 8 GiB RAM and
8 GiB combined RAM-plus-swap, compiler `j1`, 2,048 PIDs and finite watchdogs.
Launch only with available RAM ≥8 GiB, full memory PSI avg10 <1 and combined
RAM/swap used fraction <0.85. Stop the study job at available RAM <4 GiB, PSI
≥5 for two consecutive samples or combined fraction ≥0.90. Account for other
host jobs; do not stop unrelated work or change swap.

Freeze selected sources, fixtures, runners, seeds and auditors before a run.
Retain failed attempts and apply narrow source-bound repairs with fresh
affected builds when justified. Protect the original B100 eighteen physical
files, old proof/report bytes and both marker fixtures, including their size
and modification-time metadata. Checkpoints remain external with exact
hashes; sources, scripts, reports, raw streams and manifests belong in Git.

## Product gates remain separate

The retained row fixtures use 1,145,104 / 1,553,197 last-input-to-commit cycles;
at an assumed complete-parent 125 MHz they project to 9.160832 / 12.425576 ms.
The stalled profile needs at least 303,198 fewer cycles for strictly under
10 ms at that boundary. Preserve byte controls and first-input/start timing
boundaries too. These fixtures do not measure physical SDRAM or ESP32 service.

Sustained 720×480, thirty distinct displayed frames/s over ESP32 Wi-Fi and
validated hardware decode under 10 ms still require the later custom endpoint,
complete-parent, calibrated memory/transport and remote hardware campaigns in
the [V126–V130 plan](../gamebub-v126-v130-timing-streaming-plan.md).
The two-slot registered-capacity readiness option is a separate future
latency-changing experiment: it needs an explicit credit/ownership/fence and
cancellation contract, not a delayed ready wire or a disabled cycle oracle.
