# CU66 v73 — banked strip and wide reference rows

The matched P transaction is 129.17 ms versus v72's 148.51 ms in the command
model. Four chronological frames are exact with zero LCD underruns. The banked
strip maps to eight RAMB18 cells instead of 24 RAMB36 cells in an unplaced
7-series family flow. Target 30 fps and sub-10-ms decoding remain open.

- [Results and hardware-development handoff](hardware-handoff.md)
- [Plan](plan.md)
- [Reference-row and cache API/evidence](memory.md)
- [Native banked painter](display.md)
- [Frontend validation and unplaced family mapping](elaboration.md)

Machine-readable evidence is under `fpga/experiments/cu66-v73/`. Reproduction
and read-only audits are under `scripts/cu66-v73/`. Frozen v69–v72 sources and
evidence remain unchanged.
