# Qualified output-control/capacity composite

This separate fresh-RTL variant combines the four capacity bodies and the
`cu66-v108-outtile/cu66_idct8x8.sv` body. It changes five source origins in the
same eighteen-file RTL/header closure. It is distinct from the frozen-source
implementation matrix and its clean repeat.

The [composite preparer](../../scripts/cu66-v108/native_composite.py) requires all
five current actual RTL proofs before creating any native build:

| Proof | Required status |
| --- | --- |
| `capacity/results.json` | `PASS` |
| `capacity-pipeline/results.json` | `PASS_EXACT_CAPACITY_CANONICAL` |
| `outtile/results.json` | `PASS` |
| `outtile-kill-collisions/results.json` | `PASS` |
| `outtile-pipeline/results.json` | `PASS_EXACT_OUTTILE_CAPACITY_CANONICAL` |

Each must report `actual_RTL_run=true`. Production hashes must match the focused
proofs, and the composite full canonical proof must bind exactly the complete
native RTL/header closure. The four-body capacity canonical proof remains a
separate prerequisite.

The additional kill-collision proof must bind the current output-body SHA and
all twelve AC write-boundary cases (four groups × reset, abort and both),
group/guard/matrix masks `15`/`7`/`4095`, and twelve successful unchanged-golden
retries. Independently replayed raw traces must also cover the same twelve-case
matrix. This augments the original focused proof without rewriting it.

All six original matrix rows must have actual terminal receipts and separate
completion records before strategy selection. `--trial mN` must identify the
eligible completed matrix route with the highest measured WNS (then TNS,
failing setup count and trial order for ties). Its actual directives transfer to
the composite. A strategy is never selected from placement estimates, failed
routes or incomplete rows.

Eligibility also requires nonnegative hold/pulse slack with zero failing
endpoints, zero unclocked or internally unconstrained endpoints, zero loops or
latch loops, and no multiple-clock endpoints. Negative setup can identify a
measured frontier; the contract labels it `FAILED_FRONTIER_ONLY`, with no 100 MHz
qualification claim.

The preparer preserves original RTL/include order, fresh RuntimeOptimized
synthesis with the fixed 10 ns clock before synthesis, and the selected
implementation directives. It freezes a distinct `outtile-native-contract.json`,
preflight and tooling snapshot. Root activation and independent audit must bind
the separate [fallback policy](../../experiments/python-gamebub-v108/output-control-fallback-policy.json)
as well as the preflight, contract and initial policy. One composite native run
is allowed; failures remain recorded. All six matrix rows and their evidence
stay unchanged.

Limits remain two CPUs, two Vivado threads, 8 GiB without extra swap and 2,400
seconds, within the global two-heavy-job allocation. No clock relaxation,
exception, guessed board I/O delay, hardware operation or post-route physical
optimization is introduced. Native output lives in
`experiments/python-gamebub-v108/outtile-native/`.

A fresh composite route does not replace the unchanged-source matrix winner's
clean repeat. A component timing result does not prove board integration,
sustained hardware 30 fps or validated complete decoding below 10 ms.
