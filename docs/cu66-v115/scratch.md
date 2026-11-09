# V115 scratch descriptor preparation

The scratch candidate breaks the V114 descriptor-to-storage control cone into
three private preparation edges. It also prepares line/address comparisons on
the existing read-fetch edges. These changes target the routed V114 context
count-to-storage enables and read-address-to-state paths. They do not introduce
new read-service bubbles or change coefficient values, memory order or held
transfers.

## Ownership and latency contract IV115.S1

On accepted begin edge E, scratch captures all 19 descriptor fields and exposes
the proposed `active_epoch` as a **reserved owner**. E+1 validates and prepares
base quantities; E+2 registers dependent wide plans; E+3 commits admission.
Private anti-replay history advances only at a successful commit. Invalid or
cancelled proposals do not burn an epoch. During preparation, scratch accepts no
coefficient, seal or band-end transfer and emits no memory request or dense
output. All descriptor inputs may change after E.

The reserved tag matters to the actual parent: it uses scratch's active epoch
for abort delivery. An initial source-only review found that keeping the old
public epoch until commit would drop a real pending-parent abort. That draft is
retained under `scratch/design-history`; it was corrected before execution.
The selected source publishes the reserved owner at E, accepts its matching
abort, ignores stale tags, and retains committed-history protection.

The original state IDs remain unchanged; two new preparation states are added.
Private payload registers need no reset because visibility is gated by complete
capture and warmup. Public reset and physical outstanding-response drain rules
remain checked. Comparison results prepared for DC, RAW and AC reads include
same-edge response forwarding; boundary probes check the exact consumption
edges instead of assuming cache tags have already updated.

## Executed checks

[Selected paired proof](../../experiments/python-gamebub-v115/scratch/results.json)
binds the production source and strict Verilator build to seeds 115401/115402.
Each seed retains 72 full transactions, 128 corrupt-response cases, four read
owner cases and 48 DC line-boundary transactions. A reversible adapter pauses
the reference clock for exactly three checked candidate-only preparation edges
after each accepted descriptor. Original value, raw-view, memory and ownership
checks resume at paired edges. This is logical-cycle pairing, **not** public
cycle equivalence with V114.

Each seed additionally checks 12 pending abort/reset cases, 12 stale pending
tags and 24 full retries, including reuse of uncommitted tags. All 269 paired
descriptor tuples are poisoned after capture; all 807 extra edges are checked
for forbidden work. Independent candidate goldens cover the new pending-owner
semantics. No original assertions are removed or downgraded. The retained first
attempt failed on a C++ test-harness macro redefinition, not an RTL verdict; the
selected subsequent strict build passed.

[Supplemental metadata proof](../../experiments/python-gamebub-v115/scratch-extra/results.json)
separately executes the actual production scratch with seeds 115451/115452.
Per seed it covers 12 invalid geometry/capacity/RAW/count/overflow descriptors,
their legal same-tag retries, three valid boundaries and four replay-priority
combinations. All 34 accepted descriptors are poisoned after capture and no
physical request is permitted. This supplements the full memory tests rather
than replacing them.

[Actual-composition peer proof](../../experiments/python-gamebub-v115/control-peer/results.json)
checks the complete 18-source decoder, including aborts delivered through the
real parent on every pending phase, and canonical full-frame retries. Native
timing is measured separately. None of these component proofs establish the
full display parent, sustained hardware 30 fps or validated full decoding below
10 ms.
