# V121: prepare the owned refill request address

Continue the [spatial architecture roadmap](../gamebub-v121-v125-spatial-literature-review.md)
with one causal RTL experiment. Preserve qualified V120 Source B and its remote
hardware handoff. No existing decoder source, assertion, timing constraint or
reference oracle is replaced.

## Question and candidate

The B125 route fails at −1.517 ns WNS. Its worst path launches from refill
`issued`, computes `offset + issued`, crosses admission bounds/readiness and
ends at a RAM enable. Prepare the full32 next request address on existing
start/accepted-request edges so it can drive that interface without the
combinational offset addition.

Only the refill queue's source alias changes. A new cursor starts at the
accepted `start_offset`, advances modulo 2^32 exactly once per accepted request,
and holds on stalls and response-only edges. Existing issue/credit logic,
owner epoch, pending address/last binding, reset/cancel/start priority,
first-fault behavior and overflow assertions remain authoritative.

The declared public-cycle delta is **zero**. This candidate does not introduce
the optional elastic stage discussed in the broader roadmap. Keep that as a
future versioned alternative if a same-cycle cut does not close the request
path. Preparing an address relocates arithmetic; it does not eliminate all
carry logic or guarantee physical timing.

## Gates and execution order

1. Recompute all 18 Source B hashes against the manifest and pinned commit;
   record actual baseline reports and protected unrelated file identities.
2. Run a fresh strict focused reference/candidate RTL pair with an independent
   transaction model, stalls, simultaneous operations, cancellation/replacement,
   address boundaries and preserved assertion failures on illegal accepted wrap.
3. Run a fresh complete-component/actual V97 transport regression, physical
   debt/peer retry checks, and guarded byte/row parent. Retain independent
   canonical/HUD/root/seal checks and exact Source B events/cycles. Do not promote
   on an isolated queue test alone.
4. Independently audit the source/proof/recipe-bound native preflight. Start
   from fresh RTL at **8.000 ns before synthesis**, with the unchanged V120
   tool image and core recipe. No timing exceptions, directive sweep, inferred
   board I/O delays or clock relaxation.
5. Retain actual route/setup/hold/pulse/coverage/routing and methodology reports.
   Compare the old request path and other critical families, mapping and route
   delays. A failed route is a measured negative result, not qualification.
6. A positive component result requires a separate fresh same-source/tool/core
   recipe repeat. Keep complete board timing and physical product gates open.

All heavy work uses at most two jobs, each two CPUs and 8 GiB RAM with an 8 GiB
RAM-plus-swap cap. Gate launches on available RAM, full-memory PSI and combined
RAM/swap utilization; monitor pressure and stop bounded jobs on the retained
thresholds. The occupied swap percentage alone does not block a build.

## Performance interpretation

An exact-cycle candidate retains the row fixtures' 1,145,104/1,553,197 cycles
from final accepted outer byte to validated commit. At an assumed complete-parent
125 MHz these are 9.160832/12.425576 ms. Timing repair alone does not save the
303,198 cycles required for the stalled profile to be strictly under 10 ms.
The complete parent is not routed or calibrated physical memory service.

This is V121's timing/control experiment. V122–V123 address service/compute
cycle reductions. V124–V125 require real endpoints, complete-board qualification,
sustained distinct 30 fps and every validated decode below 10 ms. No local
hardware access or bitstream programming is part of this experiment.
