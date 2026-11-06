# CU 66 V80 — integrated reference prefetch and snapshot overlap

V80 connects the tagged two-slot reference window to the actual decoder,
SDRAM controller/model, canonical/HUD fences and continuous native display.
It measures an exact legacy control, conservative prefetch, and a controlled
variant that permits candidate writes while a saved read snapshot drains.

The goals remain sustained 30 distinct source-fps, then strict maximum
ingress-complete → validated FPGA decode below 10 ms, without changing the
established coded/native resolution or the encoded fixture packets.

The selected overlap replay passed **457/457** canonical and full-raster checks.
It improved validated latency on 273 sources and regressed on 184. Pooled median
is 28.52827 ms and maximum is 71.49397 ms; **326/457** meet the separate 33.333-ms
ACK budget and **0/457** validate under 10 ms. The sustained and hardware gates
remain open. See the handoff for per-history results and measurement limits.

- [Results and hardware-development handoff](hardware-handoff.md)
- [Integration, authentication and drain contracts](integration.md)
- [Monitors, attempts and command/tile traces](monitor.md)
- [Actual-system reject/abort/retry tests](faults.md)
- [Actual trace analysis and its limits](trace-analysis.md)
- [Iteration plan](plan.md)
- [Evidence audit](evidence-audit.md)

V79 and earlier sources/evidence stay immutable. These are simulator results;
no new bitstream, target timing/CDC signoff or physical streaming proof is
claimed. The standalone V79 cache result is not substituted for the integrated
V80 system's canonical and full-raster checks.

The next architectural experiment is a tagged 128-bit reference-fill interface
that consumes the SDRAM bridge's existing snapshot without serializing it into
eight x16 transfers. It must keep generation, bank, plane, tile and block identity,
backpressure, abort/drain and reference-bank leases intact. Its latency benefit
remains unmeasured; compare it against the same mode-2 histories before deciding
to adopt it. Details and the missing trace events are in the trace-analysis report.
