# Isolated two-bank byte RAM → word reader → JPEG decoder

This single-clock Verilator experiment connects the earlier 48 KiB-per-bank
storage/controller and little-endian word reader directly to the real
`jpeg_core`, using `marker-followup/jpeg_input_followup.v`. It observes decoder
ready and the reader's byte strobes, with `inport_last_i=0` as in the existing
core (the decoder uses JPEG EOI). Its pixel sink is always ready. It resets the
decoder between frames and checks output dimensions, coordinate bounds,
uniqueness, byte/word accounting, CRC-gated bank commits, and alternating bank
identity. A software C-model comparison checks every RGB565 pixel.

In the recorded run, 26,159-byte fixture 0000 uses bank 0; while it decodes,
26,991-byte fixture 0002 is committed to bank 1 after 23,808 pixels of frame 0
have been emitted. Both produce 345,600 unique pixels, each exactly matching
its own related C model. The second distinct image and complete per-pixel
comparison detect stale-bank or stale-decoder output for this pair. Both final
words contain three valid bytes. The simulated vblank is a control pulse, not a
framebuffer or scanout simulation.

Run `run.sh` with `BUILD_DIR` set to an empty scratch directory and `JPEG0` and
`JPEG1` set to compatible baseline 720×480 JPEG fixtures. Requires Verilator
5.x, make, C++ compiler, Python 3 and GNU timeout. The recorded fixtures are
`/home/lori/gamebub-tools/network-rtl-repro-v1/fixtures/{0000,0002}.jpg`; their
hashes and source hashes are in `results/sha256.txt`. The fixture generation
script is `experiments/fixture30/generate.py` in the repo; other arbitrary JPEG
profiles are not supported by this proof. The short tracked output and comparison
JSONs are in `results`; large simulation dumps are left in scratch space.

The wrapper uses the byte RAM and controller model, with synthetic same-clock
byte ingress and no QSPI, CDC, real SDRAM/framebuffer, scanout, radio, ESP32 or
physical FPGA. Decoder output is always accepted; the test exercises normal
input ready handling but does not characterize adverse output stalls. No claim
is made about FPGA fit, target timing, end-to-end 30 fps, or production status.
