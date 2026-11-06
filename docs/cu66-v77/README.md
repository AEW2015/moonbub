# CU66 V77 — direct-YUV rendering RTL

A streamed 29,184-byte cache and elastic RGB565 pipeline now drive exact native
portrait pixels through the real controller model and existing LCD line buffers.
The bounded variant passes **eight source-condition panels with zero mismatches
or underruns**, and matches every tested original counter/cycle.

Bounded address arithmetic reduces the cache/converter's unplaced mapping from
**29,462 to 2,970 cells**, using **7 DSPs and 17 BRAM 18K equivalents**. These
counts exclude the controller, LCD buffers and compressed-frame decoder.

**Sustained 30 source-fps and validated FPGA decode below 10 ms remain unproven.**
Inputs here are predecoded fixture planes. Seamless source ownership, full
decoder integration, target timing/CDC and physical testing remain next work.

- [Results, recommended sources and next milestones](hardware-handoff.md)
- [Cache, stream and pixel interfaces](interface-contract.md)
- [Cache verification and bounded arithmetic](cache.md)
- [Pixel conversion and native render tests](render.md)
- [Frontend and unplaced mapping comparison](elaboration.md)
- [Iteration plan](plan.md)

Retained evidence is in `fpga/experiments/cu66-v77/`; producers and integrity
checks are in `scripts/cu66-v77/`. All V69–V76 files remain frozen.
