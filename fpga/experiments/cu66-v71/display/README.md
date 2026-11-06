# CU71 dedicated BL8 LCD prefetch

This successor preserves the v70 globally committed descriptor queue and
native dual-clock line endpoint. It replaces the scalar 480-word line reader
with 60 aligned BL8 requests. Physical timings, porches, margins and color
expansion are unchanged. `cu71_lcd_lines.sv` differs from the pinned v70 line
RTL only in its module name; `provenance.json` records that source identity.

## Modules and interface

- `cu71_scanout.sv`: frozen initial dedicated-BL8 baseline. One response is
  consumed and serialized completely before the next burst request.
- `cu71_scanout_prefetch.sv`: selected successor with the identical public
  ports. The next single outstanding request overlaps serialization of the
  current burst. The memory response remains held until the local buffer is
  free; a failed prefetched abort is retained rather than losing completion.
- `cu71_lcd_lines.sv`: unchanged line-buffer logic and token CDC, renamed.

Dedicated memory requests use `lcd_req_valid/ready` and `lcd_req_addr[23:0]`.
Addresses are x16 word addresses, aligned to eight. A held request is stable.
Replies use `lcd_rsp_valid/ready`, `lcd_rsp_data[127:0]`, and `lcd_rsp_error`.
Bits`16*i+:16` correspond to address+i. The backend holds the entire response
stable until accepted; it must isolate that held reply from other clients.
Only one burst is outstanding. A line always requests exactly 480 words.

`lcd_busy` participates in the descriptor drain gate. `lcd_abort_i` asserts
only with the shared memory reset; normal descriptor switching never cancels
memory work. `lcd_aborted` is consumed as a failed burst and reported. A full
reset requires memory service and both clock domains to be flushed together;
this module does not implement safe unilateral pixel reset.

Descriptors are already globally committed when accepted. Actual front-slot
changes remain at the qualified frame-boundary+drained condition. The root
owner must retain memory leases until this ACK; raw vblank is insufficient.
An ACK is not a proof of a complete clean raster or unique displayed FPS.

## Executed component evidence

`evidence/regression01` retains the baseline and exact source snapshots:
four asynchronous functional schedules, eight complete rasters, 3,072,000 pixel
comparisons, queued descriptor/stale rejection and safe whole-black-line
behavior during intentional starvation. Normal three schedules have zero
underruns. The starvation case has 1,440 black lines and matching underruns.

`evidence/prefetch-metrics02` is the selected prefetch functional proof:
seven schedules, 14 complete rasters, 5,376,000 pixel comparisons. Added cases
cover read-error replacement, an abort while the previous response is still
serialized, and coordinated both-domain+memory reset with a fresh generation.
Normal/fault/reset schedules have zero underruns; deliberately slow memory
remains an explicit starvation test. Backend error replacement is eight black
words with a counted memory error; it is distinct from whole-line starvation.

With identical seeded synthetic delays, the maximum line fill interval from
the first accepted memory request through final serialization fell from 1,503
to 1,057 memory clocks for seed7101. The ideal schedule fell from 599 to 540 clocks.
These are component simulation costs, not physical latency or sustained FPS.

The updated tool is Verilator 5.053 from the installed WSL OSS-CAD suite. Only
`PROCASSINIT` is waived for the inherited FPGA declaration initializers plus
explicit reset; all other `--Wall` warnings remain fatal. Initial Windows/CRLF
launch failures were retained under their original files, not called PASS.

## Actual backend integration and remaining blocker

`evidence/memory-scanout-fast02` connects the selected prefetch RTL to the exact
qualified SDR2 controller, command-checked 32 MiB model, 100 MHz memory clock,
274.5° read phase and declared fast routed-delay terms. A framebuffer fixture
is initialized in the model; all display reads go through the real bridge,
controller and pin model. Canonical tile writes, HUD writes and refresh run
concurrently. This test does not establish decoder/write reconstruction.

The eight selected canvas lines pass exact-or-whole-black correctness but
**fail normal-load cadence**: eight black lines/eight matching underruns,
maximum line fill 2,230 memory clocks, maximum backend wait 54 clocks. This exceeds
the roughly20.5µs prefetch-to-active opportunity. 31 canonical tiles and 241 HUD
writes completed in the selected workload plus drain. Post-drain global
underruns are reported separately from the scored eight-line window.

The earlier `memory-scanout-fast01` failed a testbench accounting comparison:
background drain advanced the global underrun count beyond the pixel-scored
window. The corrected test snapshots the selected-window counter explicitly
and still retains the genuine cadence failure. No failure was relabeled PASS.

The measured follow-up changes only the memory bridge scheduler: at most two
LCD bursts per waiting background grant, with a bounded four-cycle lookahead
for the next independent LCD request. See the memory agent's separate proof;
no display source, PHY phase, memory clock or I/O budget was relaxed.

`memory-lookahead-fast01` and `memory-lookahead-slow01` both pass the eight
selected canvas lines with zero black lines/underruns and a maximum 1,741-clock
line fill (17.41µs at the modeled 100 MHz). Each includes 21 canonical tile writes,
162 HUD writes and 177 refreshes through the selected window plus drain. The
old bridge's LCD-only control (`memory-scanout-idle-fast01`) passes with a
maximum 1,248-clock line fill and zero underruns, separating contention from
the reader's baseline service cost.

Full480×800 single-raster repetitions at both model corners pass in
`memory-full-raster-fast01`/`memory-full-raster-slow01`. Each checks all 384,000
physical pixels, including 345,600 canvas pixels and all 720 canvas line fills.
Both have zero black lines, memory errors and underruns; the maximum line
fill is 1,771 memory clocks (17.71µs at modeled 100 MHz), backend wait 56 clocks.
The concurrent workload completes 1,856 canonical tile writes, 14,844 HUD writes
and 1,994 refreshes. These are successful single-fixture, actual-command model
tests. They do not include codec parsing/reconstruction/painter traffic and
must not be used as a full-system, physical cadence or 30 fps PASS.

## Reproduction

Run from the checkout root, with unique output directories:

```powershell
python scripts/cu66-v71/display/run_scanout.py --variant prefetch --metrics --output fpga/experiments/cu66-v71/display/evidence/new-component-run
python scripts/cu66-v71/display/run_memory_scanout.py --corner fast --last-line 799 --memory-proof fpga/experiments/cu66-v71/memory/evidence/lookahead-fast01 --output fpga/experiments/cu66-v71/display/evidence/new-integration-run
```

Use `--memory-proof` to select a new frozen memory qualification directory.
Each executed integration retains exact sources, model, commands and logs.
No physical device, target timing closure or 30 fps qualification is established.
