# CU66 v71 memory and display iteration

The final model preserves exact output and has zero LCD underruns for the
chronological key/P pair. Memory stress tests fit the tested line deadlines.
Full-frame throughput and sub-10-ms validated target decoding remain open.

- [Results and hardware-development handoff](hardware-handoff.md)
- [Implementation and next steps](plan.md)
- [30-fps / under-10-ms milestone checklist](milestone-checklist.md)
- [Memory interface and stress tests](memory.md)
- [Display interface and tests](display.md)
- [Generic elaboration scope](elaboration.md)

Machine-readable evidence is under `fpga/experiments/cu66-v71/`; the independent
checks are `scripts/cu66-v71/verify_baseline.py`, `verify_evidence.py` and
`bundle_manifest.py`. Older v69/v70 sources and evidence remain unchanged.
