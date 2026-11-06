# CU66 V79 — monitored histories and reference-prefetch prototype

V79 strengthens the simulation checks around the unchanged V78 decoder/direct-
display system, extends fixed-arrival testing across the four available gameplay
histories, and prototypes bounded reference prefetch as a separate RTL component.
The goals remain **30 distinct source-fps**, then **strict maximum validated
FPGA decode below 10 ms**, at the established coded/native resolution.

All **457/457 history sources** pass canonical and complete native-raster checks:
**381,694,375 native pixels**, zero display errors, black lines or underruns.
The new prefetch component independently passes all 8,100 reference payloads
and nine ownership/fault test groups.

Performance remains open: modeled ingress-to-validated latency is
**12.41–78.72 ms**, **0/457** meet strict under-10-ms, and **136/457** miss the
serial 33.333…-ms processor-ACK budget. Finite first-to-last display cadence is
**29.83–29.88 source-fps**. These short independent histories do not establish
the 60-second modeled or 600-second physical sustained goal.

- [Results and hardware-development handoff](hardware-handoff.md)
- [Iteration plan and remaining milestone gates](plan.md)
- [Sticky health, raster deadlines, queue monitoring and self-tests](monitor.md)
- [Actual traffic, controller constraints and Python scheduler study](memory-study.md)
- [Physical tile-layout model and row-conflict tradeoffs](layout-study.md)
- [Standalone prefetch contract and simulation](prefetch.md)
- [Evidence and baseline audit](evidence-audit.md)

The full-system campaign keeps the V78 production RTL byte-for-byte. The new
prefetch module is a separate experiment: it does not alter those measured runs
and has no integrated speedup claim. No new bitstream, routed timing, live ESP32
transport or physical performance qualification is claimed.
