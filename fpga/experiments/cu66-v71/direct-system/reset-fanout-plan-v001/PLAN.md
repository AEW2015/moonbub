# Same-cycle reset FF replication: prospective DY71 experiment

Status: planning and read-only helper only. No ECO, Vivado invocation, DCP edit,
BIT or hardware operation is authorized by these files. Current selections and
the two active board implementations remain untouched. Root must first select a
completed DY71 source/DCP/report set and confirm its actual failing cone.

## Evidence and applicability

CU71 implementation06 reports −1.177ns from `joint_core_reset_reg[3]/C` to
`system_core/receiver/base/held_ref_pixels_reg[510]/R`:11.042ns data delay,
10.586ns route,95.870% route, zero logic levels. The routed net has reported
fanout14549. This is evidence for that older CU71 image, not a measured failure
or a primitive-leaf count for either new DY71 implementation.

The original-root CP23 `postroute-reset-replicas03` experiment independently
audited3959 exact primitive leaves and33868 transitive endpoints across11
same-cycle FDPE copies. Effective-property resolution pinned the installed
UNISIM defaults; the raw property comparison initially failed and was retained.
Its independent post-route audit reports worst upstream-stage→copy-D setup
+5.051ns and hold+0.420ns. PRE recovery/removal were explicitly excluded, not
passed. Neither its counts, grouping, timing margins nor DCP hashes transfer to
DY71. `reference-bindings.json` records the files actually inspected.

## Root selection and observation gate

1. Wait for completed final DY71 routed DCP, final completion marker, immutable
   selection, executed source/header/constraint hashes and all timing/CDC/DRC
   reports. Bind their hashes into a new experiment request; never pick a DCP by
   filename, timestamp or old-profile counts alone.
2. Require the intended source be exactly `joint_core_reset_reg[3]`, FDPE,
   effective INIT1, with explicit effective C/D/PRE inversion properties and
   source C/CE/D/PRE nets/drivers. Pin the installed FDPE library used to resolve
   empty native defaults. A missing or unexpected parameter is a stop condition.
3. Run the read-only snapshot on the immutable parent. Obtain direct consumers
   through `get_nets -segments` and `get_pins -leaf`, not only all_fanout. Record
   each exact pin/primitive/ref/pin-role/LOC/BEL/net segment/driver. Also record
   the sorted all_fanout endpoint set, complete primitive connectivity/properties,
   timing constraints and existing source D/setup/hold/PRE scope.
4. Root reviews the measured reset-critical witnesses, complete sorted leaf and
   endpoint lists/hashes, input drivers and proposed physical partition. Those
   exact counts and hashes become required preconditions, rather than broad
   minimum-fanout tests. Unexpected ports, clock consumers, feedback into the
   source's inputs, multiple drivers, missing placement or unknown leaf classes
   block automatic transformation.

## Prospective transform, only after explicit selection

Derive new same-stage FDPE copies from the selected parent. Every copy connects
to the **same original** C,CE,D,PRE driver nets and identical effective INIT and
inversion parameters. Do not cascade copies from source Q: that adds a cycle.
Do not use a BUFG/BUFH for reset, change clock topology, narrow the reset cone,
drop payload reset, or change reset policy as part of this experiment.

Partition only the measured direct primitive pins. Start with the proven
physical grid idea, but freeze DY-specific groups and exact members after the
snapshot. Do not assume11 groups or indiscriminately merge every non-SLICE sink
into `other`: review BRAM/DSP/I/O and unplaced consumers explicitly. Select empty
legal sites/BELs near each region, reserve them without overwriting placements,
and reject name collisions. Copy ASYNC_REG policy explicitly or record/review
its deliberate delta; never treat it as an irrelevant omitted property.

Move each approved direct leaf exactly once from its recorded original segment
to exactly one copy. Preserve every non-reset connection and all original
primitive identities. Original Q must have no remaining leaf/port consumers.
The new direct-leaf multiset must equal the parent exactly; the unique transitive
endpoint union must match. Transitive endpoint overlap between regional branches
is possible through combinational reconvergence and is not itself a leaf error.

Retain every original timing command exactly. If the existing policy excludes
the final source PRE, extend only that exact PRE endpoint policy to the copies,
with one explicit exception per copy and the exclusion labeled. Add no false
path, multicycle, clock cut or disabled timing on D,CE,Q or sink R/S/CE/data pins.
In particular, upstream-stage→each-copy-D must retain normal single-cycle setup
**and** hold; no compensating hold relaxation or ideal-net shortcut.

Generate a new DCP and reports in a unique experiment directory, preserving the
parent bytes and all source selections. A successful transform or route command
is not a release gate. No script from this planning directory performs this step.

## Independent post-route audit and release gates

Open parent and final candidate independently, not the producer's in-memory
design. Compare exact primitive identities/properties/connectivity globally.
Only the approved FDPE copies and their Q nets may be added; only the approved
source-Q leaf connections and documented physical locations may differ. Reject
renamed, optimized-away, missing/new or multiply owned leaves; do not waive them
as phys_opt side effects. Compare drivers through hierarchical net segments.

For each copy require the same functional FDPE parameters, exact C/CE/D/PRE
drivers, rising-edge behavior and original synchronous-stage identity. Emit
separate max/min upstream-source→copy-D timing reports with one actual path,
finite nonnegative slack and no timing exception. Also report reset-Q→every
affected sink class setup/hold, full setup/hold/pulse, route/DRC/CDC/bus-skew and
check_timing. Explicitly diff exported timing commands: the only permitted
addition is the reviewed PRE-only list, with no removals.

Boolean same-cycle identity is conditional on identical initialization/inputs
and a valid capture. Parallel final synchronizer stages can have different analog
metastability resolution; excluded PRE recovery/removal is not physical safety
proof. Review assertion/deassertion policy, synchronizer attributes and newly
loaded upstream stage separately. Positive ordinary D/setup/hold reports do not
convert excluded recovery/removal into PASS.

Root selects or rejects the measured result after final whole-board evidence.
BIT generation and volatile hardware/rollback testing remain separate gates.
If new DY71 STA points elsewhere, retain this plan and do not apply reset ECO
merely because the older CU71 implementation showed reset fanout delay.
