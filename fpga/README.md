# Moonshine FPGA prototype

This is an isolated native Rev4.1 prototype, targeting XC7A100T-CSG324-1.
It receives complete baseline JPEGs through the established GameBub QSPI
framing, decodes in FPGA, writes transposed RGB565 into external SDRAM, and
switches completed buffers at a native LCD frame boundary. The input canvas is
720x480; inspected Rev4 panel timing is480x800 portrait /800x480 mounted.
The canvas is centered40 landscape pixels from either side. LCD refresh is
independent of incoming frames. With no complete frame it shows diagnostic
bars; gaps repeat the last complete frame. A late scan line is entirely black
and increments underruns, preventing a partially updated line.

The existing native application's RGB1555 Slint overlay is retained, including
its stock360x2402x placement at landscapeX12. Existing buttons/IRQ/framework
registers are preserved by the snapshotted QSPI endpoint. This standalone top
implements the required native-app subset, not every stock framework peripheral.
It has no dock/HDMI signal outputs, audio, motor, cartridge, CSC table processing
or persistent flash updater. No existing working image or source was changed.

## Rebuild and tests

From the `moonbub` workspace, on Windows:

```powershell
./fpga/scripts/test.ps1             # Full720x480 realJPEG, CRC/truncation/overflow
./scripts/test_qspi.ps1             # Actual40MHz write/16MHz read pin protocol + CDC
./fpga/scripts/test_sdram.ps1       # Init/BL8/CAS3/writes/refresh pin model
./fpga/scripts/test_memory.ps1      # Concurrent decoder writes + scanout priority
./fpga/scripts/test_pipeline.ps1    # RealJPEG→SDRAM command pins→readback and watchdog
./fpga/scripts/test_pipeline64.ps1  # Larger JPEGs fill decoder queues/backpressure
./scripts/test_transport_overflow.ps1 # Exact accepted/lost word accounting + recovery
./scripts/test_lcd.ps1              # Native scanout/CDC/line ownership
./fpga/scripts/build.ps1           # Vivado2025.2, frozen source hashes, final route
./fpga/scripts/close_timing.ps1    # Delivered v3 seed: post-route physical closure
python host/compare_decoder.py --require-fixed-exact
```

Icarus Verilog and its runtime DLLs are resolved from`C:/msys64/ucrt64/bin`.
Vivado is`C:/Xilinx/2025.2/Vivado/bin/vivado.bat`. The build uses four threads,
captures source/constraint SHA256 bindings before launching, and rejects source
changes while running. The final build directory is`fpga/build-final`.
The delivered image is`moonshine-rev4.1.bit`(2,218,250bytes), SHA256
`785f0a2dd813e2e3d8cd001999120e33e9f565eb74c79b5da5fd70c1e9c25786`.
Its final routed setup slack is+0.031ns and hold slack+0.014ns, with zero
failing setup/hold endpoints, zero DRC errors and13535/13535fully routed nets.
The independent final I/O audit reports SDRAM input setup+0.395ns and
hold+0.219ns, with12.750ns setup and2.750ns hold edge relationships.
Utilization is7362LUTs,5994registers,120.5/135BRAM tiles and32DSPs.
The first exploratory build used an overly broad CDC exception and was stopped;
its logs/checkpoint remain under`fpga/evidence`and`fpga/build`. It does not qualify
any delivery. A subsequent attempt exposed asynchronous LCD read inference and
DSP absorption across the held line-request payload, and the original JPEG
color path exceeded100MHz timing. Those sources were repaired with synchronous
LCD reads, an explicit captured line payload, an elastic address pipeline and
the local JPEG color pipeline. Its evidence remains in`attempts/v1`.
The repaired synthesis then hit a Vivado`set_bus_skew`object-type error: clock
objects are accepted by`set_max_delay`but not`set_bus_skew`. The correction uses
source-clock register collections scoped to exact first-stage destinations;
the failed transcript/checkpoint is retained in`attempts/v2`.
`scripts/resume_impl.ps1`verifies that checkpoint's RTL hashes and resumes with
corrected constraints, writing`evidence/vivado-final-resume.log`. The clean
rebuild command remains`build.ps1`; both paths use`scripts/timing-reviewed.tcl`.
The final v3 route then missed timing by64ps. Its complete failed reports and
checkpoint remain in`attempts/v3-routed`. The executed`close_timing.ps1`checks
that seed's RTL hashes and applies post-route AggressiveExplore physical
optimization plus Explore/TNS cleanup, without changing RTL or constraints.
This closes timing and writes the delivered image; its final execution log is
`evidence/vivado-close-timing.log`. The seed is deliberately tied to this source
snapshot. Modified RTL requires a fresh routed seed and matching source bindings
before applying the same closure procedure. The final read-only I/O audit is
`evidence/audit-final-io.log`and uses the delivered routed checkpoint.

The SDRAM model is functional and bounded, with CAS latency, representative4ns
forwarded-clock pad flight and2/7ns data-valid corner tests. It is not the
manufacturer's complete timing model. External
delay budgets remain the existing application's conservative part/PCB assumptions
(output2.0/-1.3ns,input7.0/2.0ns); board flight time and hardware calibration have
not been measured. Positive routed timing alone does not certify those budgets.

## Architecture and bounds

-200MHz existing-style QSPI endpoint;64-entry async44bit write queue and
 request/response read mailbox cross into the100MHz core domain.
-One256KiB compressed-frame BRAM buffer. CRC32, exact byte count, dimensions,
 SOI/EOI, and overflow state are checked before decoding.
-Pinned Apache2`core_jpeg`baseline decoder with standard Huffman tables.
 420 and444 supported; no422, restart markers, progressive or optimized tables.
 The sender chooses420, standard tables and dimensions divisible16.
-The decoder emits8x8 block order with explicit x/y. Each pixel's external
 word address is`back_base+(x+40)*480+y`, preserving orientation without
 incorrectly treating block output as a linear raster.
-Two external framebuffer slots at word bases0 and0x080000. The pending back
 slot cannot be overwritten, and it becomes front only at the LCD boundary.
 No full decoded image resides in ESP32 memory or FPGA BRAM.
-100MHz SDR SDRAM controller: BL8/CAS3 reads, single writes, tracked open
 rows, precharge/activate recovery,200us initialization and7.5us refresh target.
 Scanout wins at burst boundaries; the decoder obeys ready/backpressure.
-Two480-word dual-clock line banks use request/completion tokens and tags.
 A line fetch is60eight-word bursts. Native timing remains541x834 at
29.361979MHz; sync/RGB/pixel coordinates remain aligned through the overlay.

The selected decoder's`inport_last_i`ends its byte iterator immediately.
Using AXI-style last-word semantics dropped EOI on a partial final word in the
first test. The wrapper therefore relies on JPEG EOI and strobes padded lanes,
and the final regression checks all345600 output coordinates.

## Verification limits and remaining work

See[PROTOCOL.md](PROTOCOL.md), execution logs and the root evidence manifest.
The full720x480 JPEG output is compared independently with the upstream C
decoder and a separate C oracle using the RTL's fixed-point color conversion.
The original upstream floating-point color comparison is retained as well.

The64-entry CDC queue counts every lost write-queue bus word in its200MHz
domain. A Gray counter crosses into100MHz, where register0x50 exposes the
total. Any count change invalidates the receive/decode/pending transaction,
preserving the current front buffer; ABORT and a new START recover after the
link stabilizes. Register0x40 separately counts compressed-RAM ingress overruns.

The decoder has no native detailed fault port. The wrapper detects dimension
and coordinate violations and bounds incomplete/malformed decode by a watchdog,
preserving the displayed frame. This is recovery protection, not a complete
independent JPEG syntax validator. More unsupported-feature fixtures, actual
Wi-Fi→QSPI concurrency, physical SDRAM timing and extended gameplay are required.
No30/60fps hardware result or visible-panel confirmation is implied by simulation.
The initial controller's single-pixel writes also incur frequent row changes
because decoded8x8 blocks are mapped into portrait storage. This is a known
write-bandwidth bottleneck. Native30fps remains a performance gate; a future
tile transpose/write coalescer and burst writes should be evaluated against
this functional control before claiming the target rate.

## Source attribution and recovery

The read-only donor is the separately modified GameBub workspace at
`C:/Users/lavat/codex/gamebub/gamebub-source`. Snapshots retain local work:
`esp32_overlay.sv`was copied verbatim from native-app QSPI timingv2;
`moonshine_qspi_endpoint.sv`extends that app's endpoint only with the core window;
LCD/pin maps derive from the existing native Rev4 sources. GameBub FPGA source
is CERN-OHL-S-2.0, with license text in`licenses/`. The JPEG vendor base is
Apache2, pinned to`bb03cce45d0b7459d395486e9e1db3de1b416bd2`, with an explicit
local`jpeg_output.v`patch replacing the long combinational color conversion
with a five-stage elastic pipeline. Arithmetic coefficients, expression widths,
rounding, coordinates and clamp behavior are retained; the fixed-point C oracle
checks full-frame pixel identity. The original is available at the pinned upstream revision; the local change is
also recorded in `patches/jpeg-output-elastic.patch`. The published snapshot
does not embed the upstream Git repository.

No hardware programming is performed by these scripts. Keep the existing boot
core and recovery UF2/bitstream. The resulting prototype bitstream has stock
Rev4 USERID`B0100004`and USR_ACCESS`4D425631`. Loading it remains a separate
coordinated hardware step; a native bitstream filename or successful build does
not prove the current board/panel/SDRAM state.
