# Bounded writer → SDRAM → JPEG decoder → LCD experiment

This separate two-frame Verilator experiment connects the experimental
[byte-to-BL8 writer](../sdram-jpeg-writer-study/README.md) and
[SDRAM JPEG reader](../sdram-jpeg-reader-study/README.md) through the staged
memory arbiter, experimental SDRAM controller and functional SDRAM model. The
reader feeds frame 1 to the **actual JPEG decoder RTL**, followed by the real
tile transpose, framebuffer logic and LCD RTL. This is a bounded simulation,
not production integration, a target FPGA implementation, a hardware result or
a sustained 30 fps proof.

Frame 0 remains BRAM-fed. For frame 1, a **testbench byte source**, not the
ESP32 or the QSPI receiver, sends a second copy of the synthetic JPEG to the
new writer. The writer issues aligned BL8 writes at word address `0x060000`,
and its external `write_drain_done` input is driven by the test memory wrapper's
modeled idle signal. After writer `done`, the testbench **directly inspects
every SDRAM word** against the fixture and verifies adjacent guard words before
starting the decoder. This direct inspection is a testbench guard, not an RTL
CRC, physical write-drain guarantee, production commit, or proof of packet
identity. The existing BRAM bank controller supplies the reader's `owned`
signal; actual SDRAM bank ownership/generation and CDC are not implemented.

## Observed two-frame run

* The byte source supplied **26,991** JPEG bytes. The writer packed them into
  **1,687** BL8 write bursts, padding one final byte with zero; the testbench
  observed the modeled drain and checked all **13,496** staged 16-bit words.
* The SDRAM reader issued **1,687** BL8 reads and supplied **6,748** 32-bit
  words to the actual decoder, with exactly three valid bytes in the final
  word. All **345,600** frame-1 RGB565 pixels matched the related C decoder;
  its dump SHA-256 matched the earlier BRAM-fed reference
  `af13aa217140470bfd6d1ea3270d826b51d0a50fc9c0532c01d19e1aa19490de`.
  The C model shares algorithms with the RTL and is not an independent JPEG
  decoder.
* There were **2,892** combined staging/read command grants during the active
  frame-0 modeled scan and **1,687** grants during frame-1 decode. Frame 1
  produced **282,496** pixels during frame 0's scan. Complete modeled LCD
  canvas scans matched their framebuffers; the post-warmup underrun counter
  remained unchanged through the final scan.

A deliberate bit flip between the writer and memory arbiter is detected by
the **testbench's** predecode memory comparison at word 400. This shows that
the test detects that corruption; it does not demonstrate an RTL CRC, a NACK,
rollback or safe production recovery. The functional SDRAM model is not a
vendor device/timing model. No Wi-Fi pacing, bounded real network queue,
physical memory timing, data ownership, async reset, independent clocks or
actual LCD hardware is validated here.

## Reproduction

With Verilator 5.x, C++, Python and Pillow, set `BUILD_DIR` to a new empty
scratch directory, `JPEG0` to fixture `0000.jpg` and `JPEG1` to fixture
`0002.jpg` from the pinned network RTL fixture set, then run `./run.sh`. The
script verifies the component source manifests and fixture hashes, generates
the isolated bench, runs both frame and C-model checks, and requires the
deliberately corrupted staging run to fail at the predecode check. The
recorded full output is `/home/lori/gamebub-tools/sdram-jpeg-full-v1/`; compact
logs, comparisons and source checks are in `results/`.

The next engineering step is to replace the testbench byte source and direct
memory comparison with a bounded real packet/CRC path and tokenized bank commit,
then validate explicit arbiter/controller/CDC drain, tail handling and abort or
reset during active transactions. Exercise longer traces and display phases,
check target FPGA fit/timing and measure the actual board before claiming the
complete system or 30 fps works.
