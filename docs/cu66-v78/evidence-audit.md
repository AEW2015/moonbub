# V78 evidence audit

Run the retained-artifact audit from the repository root:

```sh
python3 scripts/cu66-v78/verify_evidence.py
```

The auditor fails closed. It requires the receiver and scanout result schemas,
their PASS status, all recorded source files and SHA-256 values, every command's
zero exit status and log hash, and the expected terminal PASS marker in an
execution log. It checks that receiver success cases complete all 8,100 tiles
and commit, while the intentionally malformed and injected-fault cases are
rejected or aborted. Scanout runs must have exact native-pixel comparisons,
multiple source identities/cache epochs, and no underruns or memory errors.

At least one `system/*/results.json` with the actual-decode/direct-display
schema is required. Every discovered result is audited. In addition to source
and log integrity and its terminal `SYSTEM_PASS`, the auditor checks frame and
timing counts, underrun totals, canonical-plane size, zero RGB framebuffer
writes, write-command/bus-beat arithmetic, and zero per-frame underruns. New
system runs are automatically included when their result files are retained.
It matches logged frame, timing, and summary fields to the JSON records; checks
unique `(generation, frame ID)` identities and a complete raster for each;
recomputes validated-cycle and queue arithmetic, tests strict under-10-ms using
validated-ready latency, tests the modeled 30-fps serial budget using
packet-complete-to-processor-ACK latency, and checks fixed-30 source release
spacing when that arrival mode is recorded. Threshold arithmetic uses the
recorded 10,000 ps memory clock.
Presentation may precede processor ACK, so the audit does not impose an order
between those two milestones.

When `system/faults/results.json` is present, it is audited as its separate
`cu78-system-fault-v1` schema. The check matches its case and summary log fields
to JSON and requires the two directed cases: bad-CRC rejection before any
physical write, and partial-write abort after physical writes with processor
abort acknowledgement after at least 64 observed canonical-write words while a
tile is active. It also checks that the old front completes a full
raster in each case, the post-campaign accepted retry reports repeated
processor COMMIT calls, two rejected and two accepted frames, no per-source
reset, and zero underruns/black lines. This is limited evidence for those
directed cases and their subsequent recovery; it is not exhaustive fault
coverage or proof of recovery from fatal cache/scanout failures.

The report presents functional evidence separately from performance threshold
observations. A functional PASS does not imply that validated decode meets the
strict under-10-ms target, nor that the modeled serial cadence proves physical
30 fps. Simulated clocks are not an FPGA frequency, target timing, or physical
latency measurement. The system results currently report serial 30-fps budget
passes and under-10-ms failures; `physical_fps_proven=0`. These failures remain
visible and do not convert into a functional failure or a physical performance
claim.

This is a retained-artifact integrity and arithmetic audit, not an independent
re-execution of Verilator, a proof of every RTL invariant, or a hardware,
CDC, timing-closure, Wi-Fi, and long-duration qualification. Build reproducibility,
source pins, finite functional simulations, and modeled performance remain
distinct evidence categories.
