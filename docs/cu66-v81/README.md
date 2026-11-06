# V81 tagged 128-bit reference fill

This experiment consumes the actual SDRAM bridge snapshot as one authenticated
128-bit block rather than serializing it into eight x16 transfers. Tiles remain
512 bits, with four blocks each and two bounded reference slots. The encoded
packets, coded/native resolution, host encoder and ESP32 wire protocol stay the
same. Keyframes bypass reference prefetch.

The comparison is V81 mode 2 (frozen V80 snapshot-overlap behavior) versus mode 3
(wide fill). Mode 2 must first reproduce V80 on identical inputs, release times,
clocks and reset schedules. Faster accepted cache responses alone do not prove
an end-to-end gain.

The wide-fill system passed **457/457** canonical/full-raster checks. Against
V80 mode 2, 314 sources improve, 134 regress and 9 are equal; median paired
latency change is only −0.00314 ms. **327/457** meet the separate ACK budget,
while **0/457** validate under 10 ms. The separate Python residency prototype
avoids 45.5255% of canonical writes in its modeled round-robin schedule; it is
not integrated into RTL and has no measured speed claim.

- [Results and hardware-development handoff](hardware-handoff.md)
- [Implementation and component contracts](integration.md)
- [System instrumentation and monitors](monitor.md)
- [Measured path dependencies](path-analysis.md)
- [Actual-system faults](faults.md)
- [Exact native tile-reuse screening](tile-reuse.md)
- [Python bank-resident store-elision prototype](residency.md)
- [Measured next bottleneck](next-bottleneck.md)
- [Acceptance plan](plan.md)
- [Baseline and evidence scope](evidence-audit.md)
- [System evidence audit](system-audit.md)

All V80 and earlier artifacts are immutable. New results retain source snapshots,
log and executable hashes, explicit terminal verdicts and failed attempts.
Simulation at a modeled 100 MHz, with zero-time CPU HUD/control, cannot establish
physical timing, fit, CDC, ESP32 transport or a sustained hardware frame rate.
The goals remain 30 distinct source-fps and strict maximum packet-complete-to-
validated latency below 10 ms. Longer 60/600-second qualifications remain open.
