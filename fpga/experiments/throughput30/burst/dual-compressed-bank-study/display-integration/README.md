# Dual compressed banks through modeled display path

This isolated testbench connects the experimental two-bank byte storage and
word reader directly to the existing JPEG core, tile transpose, burst writer,
functional SDRAM, and LCD controller models. It uses the guarded experimental
`jpeg_input_followup.v`, not an amended production decoder. The JPEG decoder
obeys tile input backpressure. The LCD supplies the modeled frame boundary;
the testbench drives compressed-bank decode/presentation control and flips the
modeled front-buffer select after the accepted boundary.

Two distinct 720×480 synthetic JPEG fixtures (26,159 and 26,991 bytes) load into
banks 0 and 1; the second commits when 7,488 pixels of the first have already
been decoded. Each frame supplies 345,600 unique valid pixels, matching its own
related C model bit-for-bit in RGB565. The functional SDRAM contains those same
345,600 pixels both before and after presentation; each frame has exactly
345,600 writes and 43,200 eight-pixel bursts. No model-detected LCD underrun
occurs after the initial warmup. The two frame IDs and front-buffer selections
alternate correctly. The test does not compare the LCD output pin stream to the
framebuffer; it checks the framebuffer and model underrun counter instead.

For reproduction set `BUILD_DIR` to an empty directory and `JPEG0` and `JPEG1`
to supported baseline 720×480 JPEG files, then execute `run.sh`. Requires
Verilator 5.x, make, a C++ compiler, Python 3 and GNU timeout. Recorded fixtures
are `/home/lori/gamebub-tools/network-rtl-repro-v1/fixtures/{0000,0002}.jpg`;
source/fixture hashes and short results are under `results/`. Source fixture
generator: `experiments/fixture30/generate.py`. Scratch output in the recorded
run is `/home/lori/gamebub-tools/bank-display-v2/`.

This is a bounded functional model. Compressed ingress, ownership, and reader
use one simulation clock; no ESP32, QSPI transport, ingress CDC or physical
board is included. The existing SDRAM and LCD clock crossings and memory model
are exercised functionally, but not verified for metastability or real SDRAM
signal/timing margins. Model clocks and boundary timing are synthetic. No
synthesis, device fit, display signal integrity, end-to-end throughput, or
30 fps hardware claim follows from this test.
