# CU66 V78 — actual decoder to continuous direct display

V78 removes the portrait RGB framebuffer composition/copy stage and integrates
the compressed-frame FPGA receiver with the bounded V77 YUV cache, RGB565
converter and native LCD line buffers. The canonical frame is decoded and
validated by RTL into actual modeled SDRAM before it becomes a presentation
descriptor. Source changes and repeated display refreshes share one continuous
run, with three-bank ownership and no per-source reset.

The fixed-arrival campaign delivers **30/30 distinct sources** as complete
correct rasters, checks **25,353,488 native pixels** including repeats and a
partial final raster, and reports zero underruns/black lines. Modeled validated
latency is **14.09–29.11 ms**; all 30 serial processor-ACK budgets pass.
Finite first-to-last display cadence is **29.49 source-fps**, so sustained
30-fps and strict max-under-10-ms goals remain open.

The goals remain **30 distinct source-fps**, then **strict maximum validated
FPGA decode below 10 ms**, at the established resolution. Functional simulation,
a serial service budget and physical qualification have separate verdicts.

- [Results, reproduction and hardware handoff](hardware-handoff.md)
- [Integration and bank ownership contract](interface-contract.md)
- [Receiver and fault/control regression](receiver.md)
- [Continuous scanout, repeat and source-switch tests](scanout.md)
- [Evidence audit](evidence-audit.md)
- [Iteration plan](plan.md)

Only V78 directories are added. Earlier source, results and manifests stay
frozen; this is a simulation candidate, not a routed Game Bub bitstream.
