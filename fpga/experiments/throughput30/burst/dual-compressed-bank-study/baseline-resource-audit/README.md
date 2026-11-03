# Routed baseline resource and provenance audit

This is a **read-only audit of retained reports**, not a new synthesis or proof that an experimental design fits. The saved `fpga/build-final/utilization.rpt` identifies Vivado 2025.2 win64, routed design `moonshine_top`, target `xc7a100tcsg324-1`:

| Resource | Used / available | Arithmetic unoccupied |
| --- | ---: | ---: |
| Block RAM tiles | 120.5 / 135 | 14.5 tile equivalents |
| DSP48E1 | 32 / 240 | 208 |
| Slice LUTs | 7,362 / 63,400 | 56,038 |
| Slice registers | 5,994 / 126,800 | 120,806 |

The report breaks BRAM out as 113 RAMB36E1 and 15 RAMB18E1, equivalent to 120.5 tiles. The 14.5 is **aggregate tile-equivalent arithmetic**, not a guarantee that every remaining half-tile can be packed or placed as a new 36-Kb block.

The routed timing summary reports setup WNS **+0.031 ns**, hold WHS **+0.014 ns**, pulse-width WPWS +2.000 ns and zero failing endpoints in those categories. The 100 MHz internal clock has +0.040 ns setup and +0.014 ns hold; the 200 MHz clock has +0.031 ns setup and +0.122 ns hold. The route report says 13,535/13,535 routable nets fully routed and zero routing errors; the gate reports zero DRC **errors**. These margins belong only to this specific routed baseline and its assumptions; 31 ps / 14 ps are not timing headroom transferable to a modified design. The DRC report still lists warnings, including pipelining, BRAM asynchronous-control checks and rule-limit warnings. `check_timing.rpt` lists 17 inputs without input delay, two output-delay diagnostics and one partial-input-delay diagnostic. The reviewed constraints and assumed external SDRAM/MCU budgets are described in `docs/timing-review.md`; these reports do not establish physical board I/O margins.

## Source and artifact provenance

`audit.py` recomputes all **43** entries in `fpga/build-final/source-bindings.json`, including the exact v3 routed seed checkpoint, against the current workspace; all match. It independently checks the **31** RTL/vendor entries in the seed's own binding file. The actual retained `fpga/scripts/close_timing.ps1` checks seed RTL hashes before invoking `close_timing.tcl`, snapshots its sources and seed, then checks them again after the run. The Tcl/log show post-route optimization from that seed and the same reported WNS/WHS/DRC gate. The current delivered bitstream SHA-256 is `785f0a2dd813e2e3d8cd001999120e33e9f565eb74c79b5da5fd70c1e9c25786`, matching `fpga/README.md`; report, bitstream, checkpoint and binding-file hashes are retained in `results.json`.

This binding manifest is a source snapshot, **not a cryptographic attestation binding all reports, DCP and bitstream to the exact tool invocation**. The matching manifests, retained log and bitstream hash provide reproducible provenance evidence; they do not replace independently rebuilding or hardware testing. In particular the saved `synthesized.dcp` is not assumed to be the direct input of this post-route closure: `close_timing.tcl` opens the source-bound v3 **routed** checkpoint.

The bound vendor `jpeg_idct_x.v` and `jpeg_idct_y.v` are the original RTL, and neither experimental narrow candidate path is in the final source manifest. `results.json` records the distinct original/candidate hashes. The separate generic Yosys coarse experiments reported X 16→9 and Y 22→14 DSP48E1 cells under their own defaults; they are standalone, unmapped/intermediate counts, not a routed two-stage result. Their original-stage counts add to 38, while this whole routed baseline has 32 DSPs; therefore subtracting their apparent savings from 32 would be unjustified. No candidate DSP, LUT, timing or bitstream result is implied by the baseline report.

## Implications for prospective banks

The default source specifies one `MAX_BYTES=262144` compressed buffer. A conventional 32-bit payload mapping **estimates**, but this audit does not hierarchically verify, 64 RAMB36 for that buffer. A new additional 48 KiB or 64 KiB bank would nominally consume 12 or 16 RAMB36 respectively under that same simplified mapping. If all baseline resources were unchanged, tile arithmetic would suggest 132.5/135 for adding 48 KiB, and 136.5/135 for adding 64 KiB. These are **illustrative arithmetic**, not implementation predictions: packing, parity use, BRAM18 allocation, optimization, control/FIFO additions and routing can change the answer. Replacing the current 256 KiB buffer with two smaller banks is a different redesign; this nonhierarchical report does not establish exactly how many present tiles would be released. It also requires an explicit compressed-size cap—`../capacity-profile/` shows two local frames already exceed 32 KiB. Neither option has a routed resource or timing result.

To reproduce, run `OUTPUT=/tmp/baseline-audit.json ./run.sh` from this directory. It runs a temporary-copy negative test that modifies a bound RTL file and requires provenance failure, then performs the read-only audit and emits the hashes/report values. The saved `results.json` was reproduced byte-for-byte. No new Vivado flow is invoked.
