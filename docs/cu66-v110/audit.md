# V110 baseline audit

This read-only audit pins the completed V109 results used as the V110 timing
study baseline. The pinned study branch is
`study/gamebub-v110-timing-closure-20261108`, based on
`ba60d8359b9833ff910d82af791f71a2ba93f0f7`. The machine-readable receipt is
[baseline-audit.json](../../experiments/python-gamebub-v110/audit/baseline-audit.json).

V109's final derived-data audit reports four completed native routes, 96 actual
canonical case-counter rows, and no 100-MHz, full-parent, hardware-30-fps or
under-10-ms qualification. The best route is `v109-fault-initial` at WNS
−1.589 ns; the `v109-fault-fetch` comparison is −1.635 ns. Both used the
10.000-ns component clock on `xc7a100tcsg324-1`, with 18 source snapshots
verified and zero route, hold or pulse failures. Both still fail setup timing.
These are existing V109 receipts, not V110 reruns.

The selected FETCH source closure has 18 files: 17 SystemVerilog sources and
one include header. The final native receipt verified 18 immutable snapshots;
the portable source export checked all 18 source hashes against their current
origins and preserved the exact run recipe. The export check was source-only;
it did not invoke Vivado. Its native timing result is the existing
`v109-fault-fetch` receipt.

The frozen full canonical comparison is 44 case profiles and 42 directed
checks across seeds 107601 and 107602. The V108 actual RTL controls were reused,
not recompiled or rerun, so these counts describe the qualified V109 candidate
comparison and must not be presented as a newly executed baseline.

## Scope and limits

This audit only reads the V109 summary, route receipts, canonical receipts,
source-export record and V110 gate definitions. It does not execute simulations,
Vivado or hardware. Hardware qualification occurs elsewhere; this audit remains
simulation/source-record scope. OOC timing or Verilator evidence cannot establish
complete-parent qualification. Production `moonshine_core` still instantiates
JPEG, and the CS88/CU66 component is not integrated into `moonshine_top`.

See [hardware gates](hardware-gates.md) for the remaining prerequisites and
product acceptance conditions.
