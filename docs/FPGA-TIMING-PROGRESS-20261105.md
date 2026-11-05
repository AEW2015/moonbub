# CP23 timing progress (2026-11-05)

This table summarizes selected, sealed checkpoints in the restricted synthetic KEY CP23 lineage. The resource and timing columns describe whole-composite out-of-context (OOC) synthesized netlists, not a placed or routed whole-board design. Exact source and manifest SHA-256 values and per-check evidence paths are in [`FPGA-TIMING-PROGRESS-20261105.json`](FPGA-TIMING-PROGRESS-20261105.json).

| Selected checkpoint | LUT / FF | RAMB36 / RAMB18 (BRAM tiles) | DSP | Unplaced WNS / hold WHS | Loop status | Executed functional gates | Source / manifest SHA256 prefix |
|---|---:|---:|---:|---:|---|---|---|
| composite_scanout_v006 | 44,912 / 33,525 | 88 / 4 (90) | 47 | -5.843 / +0.164 ns; 3,767 setup endpoints fail | not recorded | 6 PASS; setup FAIL | `02283eaa3e54` / `739a415eee94` |
| yuv_stage_v007 | 45,387 / 33,550 | 88 / 4 (90) | 47 | -4.985 / +0.164 ns; 3,798 setup endpoints fail | not recorded | 1 PASS; setup FAIL | `1050ca953d8f` / `8b3bf67db114` |
| cache_transpose_v006 | 25,638 / 21,939 | 99 / 4 (101) | 48 | -4.829 / +0.164 ns; 3,754 setup endpoints fail | PASS loop-free | 4 PASS; setup FAIL | `02283eaa3e54` / `9815f5d0cb20` |
| timing_pipeline_v007 | 25,543 / 21,957 | 99 / 4 (101) | 48 | -2.699 / +0.164 ns; 3,309 setup endpoints fail | PASS loop-free | 6 PASS; setup FAIL | `1050ca953d8f` / `6c88c261eaf5` |
| boundary_stages_v008_ooc02 | 25,503 / 22,057 | 99 / 4 (101) | 48 | -3.084 / +0.164 ns; 3,743 setup endpoints fail | PASS loop-free | 8 PASS; setup FAIL | `cd3f7001cda7` / `dfe6c229f04e` |
| constant_bounds_v008 | 25,405 / 22,047 | 99 / 4 (101) | 47 | -2.367 / +0.164 ns; 3,037 setup endpoints fail | PASS loop-free | 6 PASS; setup FAIL | `cd3f7001cda7` / `e6d3e8988236` |
| registered-child-cancel combo | 25,604 / 22,064 | 99 / 4 (101) | 47 | -2.267 / +0.164 ns; 488 setup endpoints fail | PASS loop-free | 6 functional PASS; setup FAIL | `cd3f7001cda7` / `a5f23f91e040` |

**Interpretation.** Every sealed checkpoint above still has negative estimated setup WNS; none establishes timing closure. The constant-bounds stage improves the estimate to -2.367 ns. The separately tested registered-child-cancel successor reaches -2.267 ns and reduces failing setup endpoints from3,037 to488; setup still fails. Hold WHS is +0.164 ns with zero failing hold endpoints in these unplaced estimates. BRAM tile totals are derived as `RAMB36 + ceil(RAMB18 / 2)`.

The initial v006/v007 OOC snapshots do not expose a separate loop-free gate in their selected manifests, so their loop status is shown as not recorded Later cache-transpose, timing-pipeline, v008 boundary, and constant-bounds selected records explicitly report no inferred loop exception. The boundary v008 selection is `ooc02`; the earlier v007 `ooc01` Synth8-326 timing-loop false path is a retained failure and is excluded from the selected result.

## Separate transpose leaf route

The independent `ar03-transpose-registered-byte-read` leaf uses 8 RAMB36 and reports routed OOC setup +0.605 ns, hold +0.167 ns, pulse +4.500 ns, with 1,578/1,578 routable nets routed and zero routing errors. Its preceding 16-RAMB36 registered-index leaf is a different OOC result; no routed result for that predecessor is implied. These numbers do not describe the CP23 whole-composite table above or qualify the board.

## Publication and limits

The raw CP23 experiment directories under `fpga/experiments/` are workspace-local records. The current portable packages under `fpga/exports/` are the isolated AR03 transpose package and the CP23 ROM-composite package. Their manifests identify distinct package scopes and source hashes; the CP23 ROM-composite RTL hash differs from the selected v008 core hash. Neither portable package replaces the exact intermediate whole-composite experiment snapshots in this table.

Global CDC, board I/O constraints, routed whole-board timing, and hardware gates remain open. The selected resource reports preserve the baseline pre-synthesis clock constraints and add no false or multicycle exceptions. Synthetic simulation refresh counts and cycles are not unique LCD frames and do not establish displayed FPS.

Root update: the registered-child-cancel row now uses its sealed424-artifact manifest and six completed whole functional gates. Its exact changed leaf is50ac0073..., independently sealed under6fc96b4d... after full control/negative/targeted cancellation tests. The subsequent registered-result-fault hypothesis is still separate unfinished work and is not included. An actual optimized CPL1 board implementation is running on the qualified constant-bound parent, not on this later cancellation successor.
