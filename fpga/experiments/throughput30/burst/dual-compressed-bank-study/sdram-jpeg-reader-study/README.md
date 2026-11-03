# Experimental SDRAM-fed JPEG reader

This isolated experiment reads a staged compressed JPEG from modeled SDRAM and
feeds the resulting 32-bit words and byte strobes to the **actual JPEG decoder
RTL**. It is research RTL and a bounded Verilator test: it is not integrated
production firmware or bitstream, target timing/fit, physical SDRAM validation,
or proof of sustained 30 fps.

## Reader behavior

`sdram_jpeg_reader.sv` reads one aligned eight-word (16-byte) SDRAM burst at a
time and buffers it as four little-endian 32-bit decoder words. It issues no
next burst until that buffer drains. `out_valid`, data and byte strobes remain
stable under decoder backpressure. The last word's unused byte lanes are zero
and its strobe marks exactly 1, 2, 3 or 4 real JPEG bytes; padding read from
SDRAM is never marked valid. `frame_done` means the final compressed word was
accepted by the downstream decoder, **not** that the frame was decoded or
displayed.

This candidate uses a fixed word-addressed slot (by default `0x060000` through
`0x080000`, exclusive) with an aligned 256 KiB cap. Start requires ownership,
a nonzero length within that cap and a configuration inside the existing
1,048,576-word *functional model*. The caller is responsible for ensuring the
correct frame is complete, valid and physically drained before start; the
reader implements no CRC or ownership-generation protocol. If ownership is
revoked during a read, it suppresses output and drains the already-issued
eight-beat response before accepting a new start. An unsolicited response
faults it until reset. A missing response has **no timeout**. There is no
response backpressure, asynchronous clock-domain crossing, independent-reset
coordination, physical drain ACK or proof against stale responses. A system
must quiesce/reset the controller and reconcile in-flight requests; the local
single-clock behavior is not a complete abort protocol.

## Unit verification

The self-checking test covers lengths 1, 2, 3, 4, 15, 16, 17, 31, 32, 33,
257, 26,991 and 262,144 bytes, plus a repeated 17-byte post-revocation case.
It checks every data byte, exact tail strobe, ordered BL8 addresses, maximum
slot length, producer/consumer backpressure, held-output stability,
ownership-revocation drain and unsolicited-response fault. Its memory response
is a small deterministic behavioral source, not the SDRAM controller. Three
mutants—incorrect three-byte tail strobe, incorrect burst-address increment and
disabled ownership revocation—each fail their intended assertion. The optional
Yosys `proc; opt; check` result is generic elaboration, not FPGA mapping or
timing.

## Decoder and display integration

The separate bounded integration derives from the pinned two-frame
[`sdram-lcd-decoder-study`](../sdram-lcd-decoder-study/README.md) test. Frame 0
still uses the existing BRAM reader. The testbench then writes the complete
second synthetic JPEG into modeled SDRAM at word address `0x060000`, waits for
the experimental shared memory wrapper to report idle, and directly compares
every staged word against the original fixture before starting frame 1. This
predecode comparison is a **testbench guard**, not an implemented CRC or a
production storage-validity mechanism. The frame's input then comes through
this SDRAM reader while the real LCD RTL scans frame 0. The existing BRAM bank
controller supplies the `owned` signal for this isolated setup; actual SDRAM
bank allocation/generation, write ordering and cross-domain ownership have not
been implemented.

In the recorded run the staged frame contained **26,991** real JPEG bytes,
padded with one zero byte and transferred through **1,687 BL8 reads**
(13,496 16-bit words). The decoder accepted **6,748 32-bit words**, including
the final three-byte strobe, then produced all **345,600** RGB565 pixels. They
matched the related C decoder exactly and had the same dump SHA-256 as the
original BRAM-fed reference:
`af13aa217140470bfd6d1ea3270d826b51d0a50fc9c0532c01d19e1aa19490de`.
The C decoder shares algorithms with the RTL, so it is not an independent JPEG
reference.

All 1,687 SDRAM read requests were granted while frame 1's decoder was active;
2,889 combined staging/read grants occurred during frame 0's scan. Complete
modeled LCD scans of the presented frames matched their framebuffers, the
post-warmup underrun count stayed unchanged through the last scan, and 282,541
frame-1 decoder pixels were produced during frame 0's scan. The model checks
the full staged write/read data and adjacent guard words. These observations
cover two synthetic JPEGs and one simulated clock phase; they do not establish
frame deadlines, average FPS, network pacing or physical display behavior.

A deliberately flipped staging-write bit is caught by the testbench's
predecode comparison at word 400. It does not demonstrate an RTL CRC or
NACK/rollback implementation. The existing functional SDRAM model is not a
vendor timing model, and the actual Game Bub memory size, address aliases,
electrical timings, FPGA fit and hardware behavior are not established here.

## Reproduction

With Verilator 5.x, C++, Python and optionally Yosys, set `BUILD_DIR` to a new
empty scratch directory and run `./run-unit.sh`. For the decoder/LCD case,
provide a different new `BUILD_DIR`, set `JPEG0` and `JPEG1` to the hash-pinned
fixtures from the earlier integration, and run `./run-integration.sh`. It
verifies both sets of pinned sources and fixture hashes, runs pixel comparisons
and then requires the deliberately corrupted staging case to fail at the
predecode guard. Full recorded outputs are
`/home/lori/gamebub-tools/sdram-jpeg-reader-unit-v2/` and
`/home/lori/gamebub-tools/sdram-fed-integration-v2/`; compact logs and source
provenance are under `results/`.

Before production use, add bounded response buffering and timeout, loss/reset
and byte-count recovery, real CRC/length and drain-before-commit, tokenized bank
ownership and stale-response rejection, a real ingress-to-SDRAM writer,
asynchronous CDC verification, line deadline and continuous 60-second trace
tests, target place-and-route and physical board measurement.
