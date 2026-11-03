# Dual compressed-bank integration with pixel-clock scanout scoreboard

This isolated functional simulation extends `../display-integration`: two
CRC-checked, distinct JPEG frames enter separate experimental compressed banks;
the word reader feeds the real guarded JPEG decoder, tile transpose, burst
writer, functional SDRAM and LCD controller. A pixel-clock scoreboard checks
every active 480×720 canvas pixel for exact order, completeness, frame
identity and RGB565 value against the corresponding immutable decoded frame.
The decoded frames are separately compared in full against the related C model,
and framebuffer data are checked before and after modeled presentation.

The recorded run checked two complete scans of frame 0 and one of frame 1,
345,600 pixels each. During the first frame's scan, frame 1 decoding emitted
280,256 pixels. Frame 1's compressed ingress had already overlapped frame 0
decoding, committing at pixel 7,488. The bench delays the next presentation
until the first full scan is verified, then waits for a full second-frame scan;
this is controlled stimulus, not a 30 Hz schedule. No model-detected LCD
underrun occurred after warmup. The scoreboard raises an error on changed frame
identity or any out-of-order or mismatched canvas pixel; missing scan completion
hits the bounded simulation watchdog.

Run `run.sh` with `BUILD_DIR` set to an empty scratch directory and `JPEG0` and
`JPEG1` pointing to the pinned fixture JPEGs. Requires Verilator 5.x, make,
C++ compiler, Python 3, coreutils and GNU timeout. The recorded fixtures are
`/home/lori/gamebub-tools/network-rtl-repro-v1/fixtures/{0000,0002}.jpg`, derived
from `experiments/fixture30/generate.py`. The script verifies fixture hashes
and `sources.sha256` before compilation; source changes require a deliberate
manifest update. Recorded short logs and C-model comparisons are in `results/`;
the full run is `/home/lori/gamebub-tools/bank-scanout-v3/`.

Compressed ingress and bank ownership use a synthetic single-clock model;
there is no ESP32, QSPI transport, ingress CDC, physical FPGA or panel. The
modeled LCD/memory clock crossings and functional SDRAM do not establish
metastability safety, physical timing, signal integrity, or hardware throughput.
Only the canvas is scored, not porch/sync electrical behavior. This is not an
end-to-end 30 fps proof.
