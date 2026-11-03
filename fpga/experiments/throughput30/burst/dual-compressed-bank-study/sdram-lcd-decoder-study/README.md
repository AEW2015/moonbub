# SDRAM staging contention with JPEG decoder and LCD RTL

This bounded Verilator integration adds the experimental four-client SDRAM
arbiter to the existing two-frame QSPI/JPEG/transpose/LCD test. It uses the
actual project `jpeg_core`, tile transpose and `moonshine_lcd` RTL, the
experimental burst controller, and its functional SDRAM model. It is **not**
a production design, physical SDRAM model, hardware test, sustained-FPS test,
or an SDRAM-backed decoder.

The decoder **still reads its JPEG data from the existing BRAM-backed input**.
The test adds independent SDRAM read and write clients carrying another copy
of the second JPEG as competing traffic; their read result is checked, not fed
to the decoder. JPEG staging is generated directly by the testbench; it is not
driven by ESP32 packets or governed by the real receiver's commit/CRC protocol.
The read source is preinitialized directly in the functional SDRAM model.

`moonshine_memory_staging.sv` retains the original test-only memory wrapper's
480-word LCD line collection and aligned eight-pixel write packing. It routes
those requests plus the two staging clients through the separate
[`staging_arbiter.sv`](../sdram-arbiter-study/staging_arbiter.sv). The arbiter
prioritizes LCD reads and round-robins the other clients, permits one pending
read, requires always-ready read sinks and faults on an unaligned selected
address. Range enforcement, response backpressure, CDC, transaction generation,
abort, actual storage ownership and physical write-drain acknowledgment are not
implemented. A memory operation already started cannot be preempted.

## Two-frame result

The generated bench derives from the pinned
[`qspi-scanout-integration`](../qspi-scanout-integration/README.md) test and
checks two distinct synthetic 720×480 JPEGs. Frame 0's complete modeled LCD
scan overlaps frame 1's BRAM-fed decode. Concurrently, the test writes fixture 1
to SDRAM word address `0x060000` and reads an independently preinitialized copy
at `0x0e0000`. It pads the **26,991 JPEG bytes** to **26,992 bytes** (one zero
byte), using **1,687 BL8 writes and 1,687 BL8 reads**.

The recorded run checked:

* All **3,374 staging command grants** occurred during both the active frame-0
  scan and frame-1 decode. All **13,496** 16-bit staged-read words matched the
  JPEG plus padding, every staged-write word matched after drain, and both
  write-range guard words remained intact. The preinitialized read region was
  also unchanged.
* Each decoder framebuffer contained **345,600 exact RGB565 pixels** against
  the related C decoder, and the generated pixel dumps matched the original
  no-staging integration's SHA-256 hashes. The C decoder shares algorithms
  with the RTL and is not a fully independent JPEG reference.
* Complete modeled LCD canvas scans matched frame data, including a scan of
  each presented frame. The LCD's underrun counter remained unchanged from the
  post-warmup baseline through the final scan. Frame 1 produced 280,448 pixels
  during frame 0's scan. These are real `moonshine_lcd` RTL checks with the
  modeled clock and memory, not physical display measurements.

The two input JPEG SHA-256 values are
`8cc99ea7d50d1d20255e41ff7247b0770b3349e705c27152a41817418ce5c9de` and
`a76055f8d43e1b0affe2810697f0f2f795302751ab2e592c43eb83cd19cfa13e`.
The matching original and new output-dump SHA-256 values are
`c087e502623218aa8be0669aab3e634d9b6d22fff6b59bfceee8f5c8322de3f0`
for frame 0 and
`af13aa217140470bfd6d1ea3270d826b51d0a50fc9c0532c01d19e1aa19490de`
for frame 1. They establish identity for these two simulated fixtures only.

An expected-failure run flips one bit in staged write burst 50; the final
storage comparison detects the altered word at index 400. This tests the
checker, not an FPGA CRC or recovery protocol. Neither this negative case nor
the normal run injects real radio loss, async reset, SDRAM timing violation,
backpressure, stale commands or address aliasing.

## Reproduce and next work

With Verilator 5.x, C++, Python and Pillow, set `BUILD_DIR` to a new empty
scratch directory and `JPEG0` / `JPEG1` to the two hash-pinned fixtures, then
run `./run.sh`. The wrapper checks the baseline and integration source hashes,
generates the isolated bench, runs both frames and C comparisons, then reruns
with the deliberate staging bit flip and requires its specific failure. The
full recorded output is `/home/lori/gamebub-tools/sdram-lcd-decoder-v2/`; small
logs, source provenance and comparisons are retained under `results/`.

The functional SDRAM model has only a 1,048,576-word array; actual board memory
geometry, bitstream timing, aliasing, scanout and bandwidth remain unverified.
Before moving the decoder input from BRAM to SDRAM, implement bounded burst
packing and a decoder reader with exact tail strobes, CRC/ownership and
drain-before-reuse semantics, address-range checks, response buffering and safe
reset/abort. Then run a real staged-byte-to-decoder end-to-end workload under
varied line phase, refresh and loss, followed by target fit and hardware tests.
