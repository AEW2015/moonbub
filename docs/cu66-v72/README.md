# CU66 v72 — masked write bursts

The matched P-frame transaction falls from 260.19 ms to 148.51 ms in the command
model, with exact output and zero LCD underruns. Four chronological frames also
pass. This is simulation-qualified experimental source, not a 30-fps release or
a target-implementation result.

- [Results, limits and hardware-development handoff](hardware-handoff.md)
- [Plan](plan.md) and [milestone checklist](milestone-checklist.md)
- [Reviewed write API](api-review.md)
- [Controller evidence](controller.md)
- [Adapters, masks and cache evidence](memory.md)
- [Generic frontend and strip-memory implementation gate](elaboration.md)

Machine-readable results, commands and source/log hashes are in
`fpga/experiments/cu66-v72/`. Run the read-only checks under `scripts/cu66-v72/`
before using the branch as an integration baseline. All v69/v70/v71 bundles
remain unchanged.
