# V106 baseline audit

This read-only audit fixes the V106 task baseline at `eececf35da97c9b14230d464ecde7576cb7840db` and checks V105's selected next-study source against it.

## Selected V105 geometry source

V105 selected `geometry`: the V105 admission-coordinate candidate plus V104's cached reconstruction source. Both selected files match the selection SHA-256 pins and their Git blobs at the V106 baseline. The selection artifact itself records V105's prior baseline commit `afc073e36f813cbcedaec9b21b61cda239453a5b`; this audit independently checks the selected files at V106's baseline commit.

The retained V105 source audit is `PASS_EVIDENCE` with 24/24 checks. The retained V105 native audit is `PASS_EVIDENCE` with 6/6 checks and no pending variants. The frozen workload remains 720×480 with a 49,152-byte complete packet cap.

## Actual routed component evidence

The selected receipt `experiments/python-gamebub-v105/native/20261107T235546839098Z/receipt.json` reports `COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN` for `cs88_pipeline_v91k` on `xc7a100tcsg324-1` at a 10.0 ns comparison clock. The route finished with signoff open.

| Routed resource | Value |
| --- | ---: |
| Total LUTs | 46,115 |
| LUTRAMs | 2,718 |
| FFs | 34,760 |
| RAMB36 | 32 |
| RAMB18 | 0 |
| DSPs | 27 |

Routed setup WNS is **-13.124 ns** and hold WHS is **+0.028 ns**. Route status reports 69,998 of 69,998 routable nets fully routed, with 0 routing errors. The worst reported path is `coefficients/mapped_tile_reg[2]/C` to `transform/coefficients_reg_0_1_124_124/DP/WE` with 22.507 ns data-path delay (8.977 ns logic, 13.530 ns route; 30  (CARRY4=14 LUT2=1 LUT3=4 LUT4=4 LUT5=4 LUT6=3) logic levels). These are actual routed report values; report hashes and source pins are in [baseline-audit.json](../../experiments/python-gamebub-v106/baseline-audit.json).

## Qualification remains open

The route is an out-of-context single-clock component comparison. The selected implementation does not meet the 100 MHz internal timing target: setup WNS is negative. Parent clock/boundary/I/O timing, methodology/DRC/CDC signoff, whole-device memory service, hardware 30 fps and validated complete FPGA decoding below 10 ms remain open. Route completion and zero route errors do not establish those goals. No license contents were read.
