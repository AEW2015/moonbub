# CU66 v71 component status

**Overall: INCOMPLETE.** This read-only inventory records component evidence under `fpga/experiments/cu66-v71/{memory,display,system}/evidence`. It does not certify a complete v71 system or hardware release.

## Passing component evidence

- **Memory/controller component:** `memory/evidence/rowburst01` passes the canonical/auxiliary LCD qualified controller test with seed 7001. It exercises copied RTL with a conditional digital model. Canonical four-word rows use masked BL8; auxiliary scalar writes use one masked BL8 each. This is not routed timing, reset/PVT/fit signoff, or a hardware result.
- **Display component:** `display/evidence/regression01` passes asynchronous scanout with a **synthetic functional BL8 memory response**. It reports 8 complete rasters and 3,072,000 compared pixels across nominal and injected starvation/fault/reset conditions. Starvation runs intentionally lose lines. This does not establish actual pin/controller behavior, panel timing, unique source frames, or 30 fps. Source hashes are recorded in the JSON manifest.
- **Local control path:** `system/evidence/local-control03` passes actual local-control + packet-staging + read-arbiter RTL with fake owner/AUX endpoints. The exact current RTL hashes are in `result.json` and in the JSON manifest. Scope excludes the complete CU66 decoder and physical QSPI.
- **Staging:** `system/evidence/staging01` passes maximum-size and failure tests against staging RTL hash `191794ee6e7336a46460a910ab2f040c7c198d705ee1349e4dbadbdfbc794f85`; the 49,152-byte fixture compiles and runs successfully.

## Distinct display/system evidence classes

The synthetic scanout component pass above is not a pin model. `display/evidence/memory-full-raster-fast01` reports `PASS_SELECTED_LINE_INTEGRATION`; this is selected-line memory/scanout integration and does not establish full-system completion or cadence. `display/evidence/memory-scanout-fast02` reports `FAIL_SELECTED_LINE_CADENCE_FUNCTIONAL_DATA_PASS`: retain it as a failed cadence attempt. `system/evidence/full-pin01` is a separate full pin/system attempt: its Verilator build returned 0, but the control run returned 134. It therefore does not pass. These results must not be merged into a single “display pass” or “full CU66 pass.”

## Remaining gates

No passing actual-pin-model integrated system test is established. The evidence set does not establish complete decoder/physical QSPI operation, an audited reproducible release source bundle, Vivado routed timing/DRC/route/resource results, board identity, bitstream hash, programming/DONE confirmation, or measured panel frame rate. **Do not claim 30 fps.** The audit observed active Vivado processes and a long-lived Verilator process; baseline OOC work may still be running, so this inventory does not call it complete or process-free.

See [COMPONENT-STATUS.json](COMPONENT-STATUS.json) for evidence paths, statuses, source bindings and hashes, limits, and pending gates.
