# V129 proposal from the routed V128 result

V128 passes the complete functional comparison but **does not meet 125 MHz**.
Its fresh 8 ns component route has **−1.320 ns WNS, −3,146.811 ns TNS and
10,006 failing setup endpoints**. The equivalent V127 result was −1.193 ns,
−1,762.554 ns and 6,980 endpoints: V128 is worse by 0.127 ns WNS, 1,384.257 ns
TNS and 3,026 endpoints. The candidate is useful evidence, not a promotion.
Its separate independent [terminal audit](../../experiments/python-gamebub-v128/audit/native-independent.json)
passes evidence integrity while reporting `design_timing_pass=false`.

The next candidate must address **both** the Rice parser's bit-consumption
control and the separate dense owner/ready return. Scratch phase/write control is
another independently negative family. Fixing one local path cannot qualify the
clock while these other paths remain. Prototype the cuts independently, then
integrate only source-bound candidates that pass their appropriate semantic and
ownership tests. The original V128 cycle-preserving results remain the control;
a useful registered boundary may declare additional cycles and use an explicitly
reviewed latency-aware contract.

## What the route actually shows

The [fresh routed path report](../../experiments/python-gamebub-v128/native/20261110T215644882105Z/reports/route-setup-paths.rpt)
contains these separate examples. The named intermediate cells identify the
physical path; their exact optimized Boolean functions need further mapped
fanin analysis before attributing them to one source statement.

| Launch → destination | Slack | Data delay | Physical detail |
| --- | ---: | ---: | --- |
| Rice `cached_remaining[31]` → `out_consumed[23]/D` | −1.320 ns | 9.311 ns | 14 levels, including six CARRY4; 2.816 ns logic and 6.495 ns routing. A net named `state_reg[0]_1` has fanout 80 and 1.299 ns delay; that net name alone does not prove it is a state FF. |
| Producer `current_child_epoch[17]` → scratch `state[2]/D` | −1.306 ns | 9.206 ns | 11 levels, including two CARRY4; 2.520 ns logic and 6.686 ns routing. The epoch launch net has fanout 5 and 1.510 ns delay. |
| Scratch `phase[0]` → `write_address[13]/CE` | −1.273 ns | See retained report | A separate phase/write-control family remains negative. |
| Scratch `phase[0]` → `transfer_data[12]/CE` | −1.217 ns | 8.928 ns | 10 levels, including three CARRY4; launch fanout 62 / 1.278 ns and a final CE net fanout 128 / 1.589 ns. An intermediate `error1` net contributes 1.539 ns. |

The second path passes named `tile_owner_match_inferred` logic, then
`coefficient_valid` and `dense_ready0`, before the scratch state endpoint. This
is consistent with the source's full owner-comparison/ready return. The exact
mapped carry function is not independently proven by its cell name. The third
path crosses logic named for `assembly_bytes` and `error1`; its complete mapped
fanin must be traced before assigning each carry to a source expression.

V128 reduced the targeted ingress-mode family but moved and exposed other
failures. The [matched 152-family query](../../experiments/python-gamebub-v128/pipeline-observations.json)
reports family minima, which may end at different physical replicas:

| Family | V127 | V128 |
| --- | ---: | ---: |
| Ingress RAW mode → scratch state | −1.193 ns | +1.118 ns |
| Scratch RAW mode → all endpoints | +0.127 ns | −0.325 ns |
| Emit bank → scratch state | −0.367 ns | −1.085 ns |
| Scalar epoch → scratch state | −0.671 ns | −1.207 ns |
| Producer tile cursor → cell cache | −0.489 ns | +0.445 ns |
| Producer state → prepared successor tile | +0.150 ns | −0.405 ns |

The separate padding query measured header FF → all endpoints at −1.165 ns
in V127 and −0.630 ns in V128; those are different endpoint instances. On V128,
the named new cache D has +2.369 ns minimum and its Q → all-endpoint family
has +0.494 ns minimum. The Q has two direct loads and 402 transitive endpoint
objects; its printed endpoint list is capped at 256. Inputs → cache CE and
cache/header → tile R returned `NO_TIMED_PATHS`, which is a query gap, not proof
that a path was eliminated or that all header-control paths pass. See the
[baseline](../../experiments/python-gamebub-v128/padding-inspection/baseline-v127-20261110T215424460066Z/receipt.json)
and [candidate](../../experiments/python-gamebub-v128/padding-inspection/candidate-20261110T222722130673Z/receipt.json)
read-only receipts and their gap tables.

The fresh routed methodology report has 167 `TIMING-16` large setup-warning
records versus 55 for V127; this is **not** a count of high-fanout nets or
independent root causes. Grouping the V128 records by named endpoint hierarchy
gives 93 scratch, 37 producer, 20 Rice parser, 12 transform and five admission
records. Among the listed launches, scratch phase has 84 records, producer child
epoch 40 and Rice remaining 20; 71 listed destinations are transfer-data CEs.
Repeated endpoint records can share a cone. The separate routed path above
provides actual fanout/delay evidence. Fresh `TIMING-18` has 1,000 reported
missing-I/O-delay warnings, at the reporting cap; the independent check lists
1,101 input and 12,887 output ports without delays. No external timing values
or waivers are supplied for this out-of-context component. `SYNTH-6` remains
28 and `ULMTCS-1` remains one. Control sets fell from 1,253 to 1,233, while
routed LUTs increased 928 to 34,504 and FFs decreased 162 to 43,432; 42 DSPs
and 32 RAMB36 plus 12 RAMB18 remain. These costs and counts do not by themselves
explain the changed WNS.

## 1. Break the Rice bit-count/control dependency

The selected [Rice parser](../../fpga/experiments/cu66-v116-rice/br88_rice_elastic.sv)
uses a 64-bit MSB-aligned reservoir and full32 `cached_remaining`/`consumed`.
Its combinational `window`, `needed` and `take_bits` logic is shared across
PREFIX and SUFFIX. Prefix truncation writes `out_consumed=consumed+take_bits`;
successful SUFFIX also writes that sum; other errors publish the previous
`consumed`. Reset/start clear the public view, while a held response must keep
its value, error and consumed position stable.

There is already an existing-edge `prefix_window` register for nonserial PREFIX,
with an IDLE/request warm-up and an assertion checking freshness. Earlier V110
also removed a redundant parallel-prefix rank clamp. Do not repeat those cuts
or assume a new register is automatically owner-correct. The mapped path still
starts at full `cached_remaining`; a serial-only rewrite may be dead in this
selected child, and a new window register can move the feedback path to its D.

First test a small cycle-preserving variant: form independent PREFIX and SUFFIX
take/consumed candidates from their own data, then select the appropriate
already-computed result at the existing response writer. The exact unsigned
SUFFIX truncation predicate can be decomposed as
`!(|remaining[31:5]) && (remaining[4:0] < suffix_left)` because
`suffix_left` is five bits. This identity retains **all 32 remaining bits**
and all 32 possible suffix widths; prove it independently and compare every
old valid, invalid, held, malformed and counter view. It may trade a shared
adder for duplicate CARRY4 logic, and synthesis may recombine it: inspect both
the new data and enable paths, resources, actual fanout and global route.

If that remains too deep, implement a true registered decision/response stage.
It must bind the reservoir bits, available count, full remaining and consumed
position, serial/parallel mode, Rice parameters, suffix state and output error
class to the same live request. `reset`, `stream_start` and context abort must
invalidate the pending token; a same-epoch restart must not revive an old
token. The parser receives no epoch input itself, so define a context-lifetime
owner or local generation with a proven no-wrap/live-token rule rather than
assuming the current tag is a freshness certificate. Input acceptance changes
the reservoir and has priority over PREFIX/SUFFIX progress. Either forward the
newly accepted word and counters into a correctly owned next snapshot or wait
an explicitly declared cycle; do not use a pre-refill prefix on the next step.
Keep request acceptance, input acceptance, bad-word handling, truncation,
response consumption and reset/start priority explicit.

## 2. Break the dense owner/ready return

The selected [producer](../../fpga/experiments/cu66-v127-owner/cs88_coefficients_v91k.sv)
compares both bank keys and the scalar key against full32 `current_child_epoch`
and full16 `expected_block`, then chooses `child_owner_match`. It gates both
the child-ready return and public valid. Scratch's selected
[dense emitter](../../fpga/experiments/cu66-v128-raw/packed_scratch_v91g2.sv)
advances and releases the active bank on the accepted dense handshake. Merely
registering `child_owner_match` would compare one tuple while potentially
accepting another.

Prototype the separately described [owned two-slot boundary](../cu66-v127/elastic-control-options.md).
Each slot owns the actual child epoch, outer frame epoch, block, index and value;
the source-level estimate is 102 payload bits per slot plus valid/control, not
measured FPGA cost. Upstream ready comes from reserved local capacity, avoiding a
same-cycle downstream-ready/owner-comparison return. Keep separate acquisition
and publication block cursors. Validate an offered foreign owner even while
the public sink is stalled, and never publish it. Mapping metadata belongs to
the public head after its correct MAP_REQ/MAP_WAIT context is installed.

Carry exact queue validity and owner keys across simultaneous push/pop,
block-end index63, bank reuse, child completion, a full-queue stall and retry.
Child completion must not cause a new plane or frame while old entries remain.
Cancellation may discard unpublished local tuples but must preserve physically
accepted memory requests until the matching ACK; queue-empty is not debt-free.
Preserve accepted writes that were already physically visible and the existing
wrong-epoch response/error ordering. The two slots do not automatically prove
one coefficient per cycle: measure the validation, acquisition and publication
initiation intervals, including the full-queue recovery bubble.

## 3. Address phase/write enable and frame latency

Scratch currently loads `transfer_data` on distinct band-flush, full-APPEND and
FLUSH_LINE paths, and moves `write_address` under different response and slot
conditions. A bounded experiment can prepare a **complete owned line/write
token** or locally registered phase/line-ready decision on an earlier real edge,
so that a deep phase/error decision does not drive the 128-bit transfer-data CE
directly. Retain the existing visible data view, phase/count and full owner; use
small valid/control resets only where a proven owner protocol makes payload
clearing unnecessary. Do not remove a reset or register an enable based solely
on fanout. Check every data/CE/reset successor path after mapping and route,
including local fault, slot availability, accepted writes, cancellation and
outstanding ACK debt.

V128's exact parent tests retain the row last-input → validated-commit counts
**1,145,104 ordinary / 1,553,197 stalled cycles**. At an **assumed qualified
complete-parent 125 MHz** these project to 9.160832 / 12.425576 ms. Strictly
below 10 ms requires at least 303,198 fewer stalled cycles. The two scenario
counts differ by 408,093 cycles; if the ordinary count stayed fixed, the needed
reduction is about 74.3% of that *scenario gap*. The two runs have different
service profiles and seeds, so the whole gap is not proven to be memory-ACK
stall time. The 1,125,000-cycle / 9 ms engineering target requires 20,104 fewer
ordinary and 428,197 fewer stalled cycles. Attribute actual wait and overlap
events before choosing burst, queue or buffering optimizations; charge all
extra pipeline and flush cycles.

## Verification and acceptance

Freeze the source map, declared cycle contract, seeds and independent oracles
for each candidate before running. A latency-changing parser or dense queue
needs separate handshake-aware drivers: compare ordered accepted input words,
requests, decoded values, full32 consumed positions, errors, owner keys,
physical request/ACK retirement, canonical/HUD/hash output and terminal
publication. Compare counters at corresponding transactions; cycle and stall
counters may legitimately change and must be reported, not silently ignored.
Never align streams by deleting an accepted mismatch. Keep the unchanged V128
cycle-exact suite as a separate control.

Cover serial and parallel Rice, 16/32-bit input, bounded-prefix and escape
limits, empty and truncated streams, malformed/late words, output stalls,
request-versus-input priority, reset/start/abort on every occupied stage and
immediate retries. For queues add both banks, RAW/scalar modes, full32 epoch
and full16 block differences, bad owner while the sink is stalled, simultaneous
push/pop, block transitions, child completion with queued data, and accepted
write plus cancel/error/wrong ACK. Verify old visible-write retirement and
separate logical-token versus physical-ACK debt. The full decoder, actual V97
transport, peer-fault and byte/row parent must pass the new declared contract.

Only then run a fresh 8 ns implementation for the actual selected source and
part. Require global setup, hold, pulse, routing and internal clock-coverage
checks, not just a favorable targeted family. A passing source requires a fresh
identical-source/tool/recipe repeat; an unchanged negative source is not
rerouted to seek a better placement. Inspect data, CE, reset, occupancy and
owner/kill paths around every added boundary. Qualify the complete parent and
actual board I/O/CDC separately. The existing [B100 control](../cu66-v120/handoff.md)
remains the independent hardware-integration reference.

Sustained 30 distinct hardware frames/s over ESP32 Wi-Fi and validated
packet-complete → publication decoding strictly below 10 ms remain open. These
component routes and abstract-memory simulation do not measure physical SDRAM,
real ESP32 CPU/Wi-Fi/QSPI service, a complete custom Sunshine/Moonlight session
or board display timing.

## Evidence identities

- [Native receipt](../../experiments/python-gamebub-v128/native/20261110T215644882105Z/receipt.json): SHA-256 `83bbb490ed16e83f0cb68f29bf0d9dc1d7480d1df9da64dbbe4902c131cf286b`.
- [Independent terminal audit](../../experiments/python-gamebub-v128/audit/native-independent.json): SHA-256 `fc2b19e40ed891e770a9ca10cf21d1981f03475d7b408127649bb6c8f45d0cce`.
- [Matched path families](../../experiments/python-gamebub-v128/pipeline-observations.json): SHA-256 `5217b3ab6814ab9b9f6033342c790eb8fde377eea2ea74b7c212fcf82d00fcb8`.
- [V128 functional index](../../experiments/python-gamebub-v128/integration/results.json): SHA-256 `57b48154c3e7beda86cfe347032e505841bcdb2d35e1b9e8e560f9d134848f20`.
- Supplemental padding-query receipts: baseline SHA-256 `d05da80c2e4d005df78a1f0654c789f56765eb6b8683c2f837f11f7df161275b`; candidate SHA-256 `24745a46fb49d397baf3bd2ab0679d34aab7fd1de9129f9d5e1cf933d0b5da7d`.
