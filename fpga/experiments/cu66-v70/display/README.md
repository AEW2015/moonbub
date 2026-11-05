# V70 presentation and asynchronous scanout components

`cu70_painter.sv` is a correctness-first, identity-filter presentation engine.
It reads canonical 720×480 packed-u8 YUV420 and the four fixed HUD rectangles,
uses the native decoder's exact rounded chroma interpolation/color arithmetic,
overlays HUD words last, and writes a complete 480×800 RGB565 portrait buffer.
The address is `rgb_base + (coded_x+40)*480 + coded_y`; all 38,400 border words
are explicitly written black. Canonical samples and references are unchanged.

The scalar `aux_req_*` / `aux_rsp_*` interface matches the v70 memory system:
one request outstanding, stable held request under backpressure, a held reply
for every read/write, and write replies only after visibility/recovery. Bases
are x16 word addresses, canonical samples are low-byte-first. Start snapshots
generation/frame ID and all five bases. Result is held until accepted and is
bound to the same generation/frame. An abort drains an accepted operation
before restart; **do not simultaneously suppress that reply using another
adapter's independent abort** without a coordinated flush acknowledgment.
Reset assumes the external adapter is flushed.

Logical cached data is 2,176 bytes: one 720-byte Y row, two 360-byte chroma
rows per chroma plane, and a 16-byte HUD cache. The painter reads each canonical
sample once, plus each HUD word once: 259,200 canonical x16 reads, 21,120 HUD
reads and 384,000 RGB writes (1,328,640 logical bytes/frame). External BL8
read-cache overfetch, commands, turnaround, refresh and contention are extra.
The cache declaration/port style has not been mapped to target BRAM resources.

`cu70_scanout.sv` wraps a copy of the existing LCD line-buffer implementation.
`cu70_lcd_lines.sv` is derived from frozen `fpga/rtl/moonshine_lcd.sv`, changing
only the module name and adding an explicit idle observation for queued,
in-flight and synchronized request tokens. Original production RTL is intact.
The wrapper serializes 480-word LCD line reads through the scalar aux port.

The descriptor queue accepts **already globally committed** generation/frame/
RGB-slot descriptors. It switches only on the LCD's memory-domain frame pulse
and when line requests/readers have drained, then pulses `presented` and exposes
the actual front generation/ID/slot. The root bank owner must release the old
RGB slot based on this actual presentation ACK, not a separate raw vblank.
The wrapper's pending descriptor is not a second decoder commit authority.
RGB slots are spaced 0x80000 words from parameter `RGB_BASE` (default0xc00000).

## Retained baseline results

Run `python3 fpga/experiments/cu66-v70/display/run_regression.py` in the normal
checkout/container arrangement. `results.json` pins commands, source/packet
fixtures and logs. All simulation contracts have watchdogs and explicit PASS.

- Three painter schedules (ideal0, seeds7001/7002): eight actual key/P packets
  from four frozen source histories, four generated edge/ramp/extreme fixtures
  and a recovery per schedule. All **39 complete physical rasters**, or
  **14,976,000 RGB565 words**, match independent native rendering exactly.
  Ten seeded fault probes cover accepted read/write abort drains, partial
  painting abort, and read/write completion errors. Every valid frame checks
  all logical read/write and pixel counts plus full memory readback.
- Four asynchronous scanout schedules: **eight complete rasters**, or
  **3,072,000 pixels**, at independent 10ns memory /36ns pixel periods. The
  tests check safe queued-descriptor replacement, exact front IDs, stable
  requests, a rejected stale descriptor and full border/canvas RGB output.
- Three schedules have no underruns. The deliberately slow scalar-memory
  schedule produces **1,340 black lines**, matching **1,340 underrun counts**;
  every such line is checked black throughout. This is a successful test of
  specified underrun behavior, not a clean-picture result for that schedule.
- Both Icarus12 and Verilator5.020 independently check 19,200 border writes,
  720 first-row pixels, the portrait mapping, invalid-generation rejection and
  abort drain. Verilator's BLKSEQ style warning is waived only for procedural
  clock/oracle temporaries in that SV testbench. Design RTL otherwise compiles
  under fatal `--Wall`. Icarus's constant-select sensitivity notices remain in
  its compile log. No functional assertion is suppressed.

The original painter failure exposed unsigned expression propagation into the
signed color shifts; it was fixed with explicit signed Y operands. The initial
scanout failure exposed inadequate scalar-memory service for the line deadline;
it was retained and made a separate explicit starvation test. Failed build
and development transcripts are retained independently of final PASS logs.

## Performance scope and remaining integration

The ideal scalar painter takes 2,084,889 modeled clocks/frame. Seeded service
with request stalls and1–8 extra response waits takes approximately5.30million
clocks/frame. The scalar benches do not implement SDRAM commands and do not
prove 30fps. Direct portrait writes stride480words as coded x advances, so
actual ACT/PRE traffic can be substantially worse than logical byte counts.

The separate strip candidate and its comparison artifacts, when present, are
not part of this frozen baseline qualification. Its purpose is to improve
portrait write locality without changing color/HUD/reference semantics.

These component tests do not prove full packet/HUD/bank integration, physical
memory performance, FPGA DSP/BRAM fit, Fmax, formal CDC signoff or hardware
display behavior. The tested dual-clock token discipline is reused from the
existing implementation; it still requires full-design CDC/timing analysis.
