# FPGA-only private KEY/hash diagnostic preflight

This new isolated experiment prepares a **compute/hash diagnostic**, not custom
network streaming or video presentation. No hardware is touched. The selected
build50 sources remain unchanged. This is not a deployable FPGA candidate.

The sealed near-cap native `native-2-0` packet is 48,203 bytes, SHA-256
`5a39857f436fc50daaa46fc518ab13f9c168fbdadabbe95ef8bf6eeff02c0518`.
Its 720x480 private pre-HUD reconstruction is 518,400 Y/Cb/Cr samples, opaque
stored tag bytes `c6c97dee75f2be10adddff19f0985885`.
`parent-bindings.json` binds fixture, oracle, quantizers and all copied RTL.
The inverse alone selects the separately verified faster implementation.

## Actual board baseline and integration risk

The existing board is `fpga/candidates/v21-audio`, top
`rtl/moonshine_top_dual_burst.sv`, built by `scripts/build.tcl` for
`xc7a100tcsg324-1`. Its native constraints are `evidence/lcd_pins_rev4.xdc`,
`evidence/sdram_pins_rev4.xdc`, `scripts/buttons.xdc`, `scripts/platform.xdc`
and post-synthesis `scripts/timing-reviewed.tcl`.
`board-baseline-bindings.json` hashes those exact inputs and retained routed
checkpoint/bitstream/reports. These are artifact identities, not device readback.

The baseline uses **120.5/135 BRAM tiles**, 11,510 LUTs, 10,237 FFs and32 DSPs.
Its saved routed setup/hold slack is only **+0.029/+0.014 ns**. The CP02 component
alone uses20 BRAM36 at its full defaults, before outer packet RAM, two raster
stripes and this fixture ROM. Retaining both full JPEG and custom decoders cannot
be presumed to fit. Combined synthesis is required; no full route is launched.
A decoder-exclusive diagnostic variant or a separately verified shared-storage
architecture must be reviewed before producing a board image. Removing the JPEG
decoder is a deliberate variant choice, not a transparent firmware regression.

Preserve 50 MHz reference, 200 MHz QSPI, 100 MHz core, 100 MHz/279-degree SDRAM
capture, and existing panel MMCM (~29.362 MHz), clock forwarding, dynamic margins,
porches, overlay, audio, native button/IRQ path and reset chains. The common audio
reset is registered in the reference domain; do not replace it with ORed domain
resets. Provisional external electrical timing budgets remain provisional.

## Proposed local diagnostic CSR interface

The existing endpoint decodes E-region core accesses; its CDC drains earlier
writes before a read snapshot. The current video registers occupy up to0x21c,
audio0x300..0x380, and margin/timing0x084..0x0a8. Static inspection found no
0x400..0x44c handlers. This proposed window is **not integrated into the board
top**, nor a published network contract. A future isolated top would extend only
the CSR read mux and attach this diagnostic on `clk100`; it must preserve all
existing handlers. No new pin, clock, network port or runtime capability exists.

| Offset | Meaning |
| --- | --- |
| 0x400 / 0x404 | Opaque `AKD1` magic / schema0x00010000 |
| 0x408 | Exact command1 start,2 abort,4 clear terminal state; other commands reject |
| 0x40c | State[2:0], busy bit3, done bit4, failure bit5, aborted bit6 |
| 0x410 / 0x414 / 0x418 | Accepted-start-to-result cycles / samples / ingress bytes |
| 0x41c | Held error stage[11:8], code[7:0]; stage15 local diagnostic faults |
| 0x420 / 0x424 | Run owner64 low/high; never reused before reset |
| 0x428 / 0x42c | Completed epoch / frame |
| 0x430..0x43c | Tag128 low word first; tag byte0 is bits[7:0] |
| 0x440 / 0x444 | Rejected commands / terminal result sequence |
| 0x448 / 0x44c | Fixture length / watchdog cycle limit |

One synchronous ROM byte is fetched and retained until the pipeline accepts it;
the current simple feeder transfers at most one byte per two clocks. Timing
therefore differs from the previous inverse-only A/B stimulus. Sample observer
is always ready; hashing provides its own backpressure. Start while busy cannot
replace the owner. Explicit abort cancels children before allowing another run;
failed children remain aborted until restart. Admission and execution watchdogs
are separate phases using the same finite cycle limit. Owner exhaustion refuses
further starts. Reset reinitializes this diagnostic ownership generation.

Read multiword results after observing a terminal state and ensure no other
operator restarts the diagnostic while reading. RUN fields are live, not an
atomic snapshot. A completed KEY/tag certifies only private pre-HUD samples;
there are no HUD semantics, P frames, reference banks, AF03 or scanout writes.

## Verification and next gates

The complete native fixture run passed all518,400 exact sample comparisons and
all16 stored tag bytes. The controller recorded **2,997,214 actual clocks** from
accepted start to accepted private result, independently checked against the
testbench clock counter. It accepted all48,203 ingress bytes, rejected one busy
START, and recovered from an earlier ingress abort using a fresh owner2. This
includes the diagnostic's two-clock ROM feeder and is not the inverse-only A/B
stimulus. At a nominal10 ns simulation period the interval is29.97214 ms; the
failed implementation timing below prevents treating that as physical service.

Standalone full-default OOC mapping completed:15,428 total LUTs including2,202
LUTRAM,13,503 FFs,53 RAMB36 and33 DSPs. The compute child alone uses37 RAMB36;
the fixture ROM uses16. The raster child maps to3,437 LUTs (2,202 LUTRAM),374 FFs,
**zero BRAM**. Its common selected-output register prevented the intended small
stripe memories from mapping as block RAM in this run. A separate inference
variant needs functional equivalence testing before replacing this baseline.

The100 MHz **synthesized, unrouted** setup gate fails: WNS-2.961 ns,2,634 failing
endpoints, TNS-6410.758 ns. Hold slack is+0.186 ns with zero failing internal
endpoints. The worst setup path is GM01 `width_reg[5]` to `error_code_reg[0]/CE`,
13 logic levels including7 CARRY4 and a DSP. This makes staged GM01 validation a
specific next timing task. No input/output delay budget was supplied to this OOC
run; it also warns that HD.CLK_SRC is unset. The report is not board timing.

`python run.py` verifies copied parent hashes and executes exact sample/tag and
cycle-accounting checks, busy-start rejection, explicit abort and a new-owner
full-fixture recovery. The testbench observes sample output solely to compare
its data; it is not a hardware API. Logs/execution metadata retain actual results.
`python run.py --controls` passed20 CSR/control checks covering invalid commands,
admission/execution watchdogs, injected downstream failure and stale completion,
clear/abort and reset. Injected events test the controller, not codec correctness.
`synth_ooc.tcl` maps the standalone diagnostic at full codec defaults, clocks its
core at100 MHz and reports utilization/timing. It is not route or board timing.

Before a first hardware compute test: finish diagnostic error/watchdog/CSR tests,
choose a fit-capable board variant, integrate its narrow bus interface, simulate
the actual QSPI endpoint/CDC and resets, and close full routed setup/hold,
route/DRC/CDC against preserved board constraints. Package exact source and
bitstream hashes. Root coordinates any later programming and host/receiver test
window. No physical throughput, custom streaming readiness or30fps result is
established by this experiment.
