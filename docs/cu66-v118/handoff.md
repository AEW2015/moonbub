# V118 handoff for hardware development

Use the exact 18-source alias map and read/include order in the [handoff manifest](../../experiments/python-gamebub-v118/handoff.json). It identifies 17 SystemVerilog files plus the ROM include, the selected `cs88_pipeline_v91k` top, the actual part and both positive routed receipts. Multiple experimental files define the same modules, so select this manifest rather than compiling the experiment directories wholesale.

The selected component passes two fresh 100 MHz runs with +0.061 ns WNS. Both use identical RTL, tool image, core recipe and 10 ns constraints; hold, pulse, internal coverage and routing checks pass. The 125 MHz source failed at −1.499 ns and is not qualified at that frequency. The manifest describes default top parameters and the `SYNTHESIS` define used by the measured flow.

Reconstruction accepts immutable residual tuples, validates them and commits at E+2 with separate reservation/commit frontiers. It holds the existing engine result through four actual 128-bit destination writes; only the completed owner becomes READY. Exactly two canonical owners remain. Errors and copy timing deliberately differ from V117; successful values, ownership and per-stage order match the independent controls. Cancellation and physical reference debt retain their complete tests.

For board integration, add the real memory, clock/CDC, interface and I/O requirements to the full parent and rerun its timing and tests. The native OOC XDC is not a complete board constraint set. Preserve accepted-response ownership, all cancellation/first-fault assertions and the canonical/hash goldens. The fast abstract row parent takes 1,145,104 cycles from the last accepted outer byte to validated commit; that is conditionally 11.451 ms at 100 MHz, not a measured board result.

The replay-lease source and Python nonce arithmetic are experimental proposals without selected RTL integration or a clock qualification. The [next timing work](native-mapping-next.md) addresses the actual remaining 125 MHz path families. Sustained distinct-frame hardware 30 fps, validated under-10-ms decoding and the production Sunshine/ESP32 path remain open.

See [reproduction](reproduce.md) for the strict functional, parent and native commands. Raw failures, source snapshots, reports, audits and the fixed run budget are retained. No board was programmed in this study.

Prepare a portable source tree without launching Vivado:

```bash
python3 scripts/cu66-v118/prepare_handoff.py --output /tmp/v118-handoff --mapped-path /work/v118
```

This verifies both positive receipt pins, every selected source, the source order and the measured run/report/clock recipes. It copies only the selected alias tree and emits Tcl plus a preparation manifest. Use the mapped path if mounting that directory at a different location in a container. It neither consumes a native trial nor programs hardware. A new physical run belongs to a separately declared campaign and budget; the published ledgers and selectors stay immutable.
