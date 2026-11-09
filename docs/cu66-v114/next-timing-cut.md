# Next timing and integration cut after V114

The source-bound [100 MHz control result](../../experiments/python-gamebub-v114/native/20261108T232847380696Z/receipt.json)
fails setup at −1.670 ns despite a clean route and zero hold/pulse failures. Its
worst path runs from `base_kill_owner_reg[3]` through live tag qualification and
producer control to `coefficients/child/scratch/transfer_data_reg[34]/CE`:
15 logic levels and 11.380 ns data delay. The matched 125 MHz/prepared-prefetch
results must be read separately; no speculative Fmax follows from this slack.

## Control pipeline to prototype next

1. Register the result of matching a kill request to its retained owner before
   driving producer cancel/enables. Separate the full tag comparison from the
   wide downstream control cone. Keep the owner reserved until the authorized
   kill and all accepted physical replies have retired.
2. Retain immediate public revocation of both sides of every request/data
   handshake. Keep scratch/reference response ports available for real accepted
   debt. Extra private kill latency must not reopen admission or silently drop
   a response. Declare a new latency contract and test exact before/with/after
   reply positions around each added edge.
3. Test stale and current tags, pending commands, cache preload, first-fault
   priority, terminal-mask persistence, cancel counters, queued synchronous replay,
   physical read/write/reference drain and clean full-canonical retry. Use the
   complete actual child fail-task poststate for prepared-state injections.
4. Requalify the exact new composition with all original value/order/held-transfer
   oracles. Route fresh RTL at 100 MHz, then 125 MHz using the same method and
   constraints. Require zero setup/hold/pulse failures and a positive fresh repeat;
   separately qualify full-parent I/O, clocks, CDC and memory before adoption.

A formal or bounded invariant may eventually prove a live comparator redundant,
but deleting owner qualification without that proof is not this proposal.
Blind fanout attributes, relaxed timing constraints or another DSP lane do not
by themselves remove the measured comparator-to-enable path. Preserve the old
negative routes as controls; do not rerun unchanged sources hoping for closure.

The terminal audit attributes 48 of the 50 worst reported paths to that kill
owner register. The other two are fetch-byte/header continuation and fetch-index
to prepared-bounds control paths at −1.659 and −1.617 ns. They also need an
independent registered cut; fixing the worst path alone is not timing closure.
This is a sample of 50 paths, not a classification of all 8,299 failing endpoints.

Physical packing is a separate limit: this OOC component uses 42/240 DSPs,
38/135 BRAM tiles and 36,426/63,400 LUTs, but occupies 14,331/15,850 slices
(90.42%). Inspect control-set compatibility and local data/control placement
before adding parallel lanes. Candidate reset reductions must distinguish
payload from valid/owner/debt state, prove that stale payload cannot escape, and
preserve abort and recovery semantics. The reported scratch clear has fanout
7,146 yet positive 0.022-ns slack; scratch reset has fanout 2,355 and −0.959-ns
slack. Prioritize measured negative paths rather than fanout counts alone. These
OOC resources do not establish full-parent capacity alongside JPEG and display.

## Service cycles and spatial work

Timing closure does not close the [latency gap](performance.md). The unstalled
worst case takes 1,383,951 cycles before full-parent validation, exceeding the
strict 1,250,000-cycle budget at 125 MHz. Profile actual inverse, entropy, copy/
reference and reconstruction service before selecting another parallel stage.

Use the [SR14 fixtures](syntax.md) to prototype bounded independent entropy
contexts and ordered chunk retirement. Measure real cycle counts, memory ports,
reorder occupancy and primitive cost. Packed residual-block order is not image
row order; map through the actual operation directory and preserve generation,
reference and C2/HUD ownership. The 128-block compact format's 89-byte worst-fixture
headroom requires a real frame-cap fallback, not a general fit claim. Keep JPEG
fallback and the frozen CS88 format until a negotiated new format is implemented.

## Complete system gate

Follow the [V111–V115 roadmap](../gamebub-v111-v115-simulation-spatial-plan.md)
and [integration inventory](inventory.md): one native Sunshine encoder shared by
capture/replay, explicit firmware codec negotiation, bounded ESP32 service and
production QSPI/CDC adaptation, actual memory arbitration, C2/HUD seal and display
publication. Run 300 distinct frames over ten modeled seconds under declared
service, negative recovery cases and full-parent timing. Then measure physical
30-fps delivery and validated under-10-ms decode. V114 component tests cannot
substitute for those gates.
