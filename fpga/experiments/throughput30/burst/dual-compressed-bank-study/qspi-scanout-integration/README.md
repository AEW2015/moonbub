# Experimental QSPI + CDC through dual-bank display and scanout

This bounded functional test connects the experimental pin-level QSPI endpoint
and its 64-entry asynchronous credit FIFO (63 usable entries) to the isolated
compressed banks, byte-to-word reader, guarded JPEG decoder, tile transpose,
modeled burst SDRAM and LCD pixel-clock scoreboard. It sends two distinct
720×480 JPEGs and checks full framebuffer, decoded pixel and active LCD canvas
contents against their own related C models.

The bus adapter inside the testbench is explicitly **test-only**, not production
MMIO. It accepts `0x14` frame ID, `0x18` byte count, `0x1c` 720×480 dimensions,
`0x20` CRC32, `0x24` command 1 (begin) or 4 (commit), and `0x100` byte data.
It exposes byte count at `0x28` and accepted-frame count at `0x2c`; these status
reads use the experimental CDC mailbox's drain-before-read behavior as ordering
fences. The endpoint's `0x54` read provides conservative FIFO credit. The
synthetic QSPI master requires at least one credit for each metadata write,
reads the byte-count fence before each data burst, and caps burst length at the
reported 0–63 credits. It fences the final byte count before commit and fences
the accepted-frame count afterward. Controller rejects and FIFO overflow fail
the run. The adapter covers only these commands and is not a full replacement
for the production `moonshine_core` register protocol or recovery machinery.

In the recorded run, 26,159-byte frame 0 and 26,991-byte frame 1 were each
accepted without modeled CDC overflow. Frame 1 committed during frame 0 decode
at 56,512 emitted pixels. Each frame had 345,600 pixels matching its own C
model, 345,600 exact framebuffer pixels before/after presentation, 345,600
writes and 43,200 bursts. The LCD scoreboard verified two complete frame-0
scans and one frame-1 scan, while 280,256 frame-1 pixels decoded during a frame-0
scan. No modeled LCD underrun occurred after warmup. The stimulus deliberately
holds presentation until the previous full scan is checked: this is not a
30 Hz scheduled test.

Set `BUILD_DIR` to an empty scratch directory, set `JPEG0` and `JPEG1` to the
pinned `/home/lori/gamebub-tools/network-rtl-repro-v1/fixtures/{0000,0002}.jpg`
fixtures, and run `run.sh` with Verilator 5.x, make, C++ compiler, Python 3,
coreutils and GNU timeout available. Fixture and `sources.sha256` checks precede
compilation. Short output and comparisons are in `results/`; full recorded
artifacts are in `/home/lori/gamebub-tools/bank-qspi-scanout-v2/`. The source
fixture generator is `experiments/fixture30/generate.py`.

This is simulation of a synthetic bus master, endpoint and functional CDC, not
an ESP32 firmware run or hardware test. Gray-pointer synchronization and SDRAM
are digital models; they do not prove metastability safety, physical timing,
QSPI pin margins, real memory timing or FPGA fit. The scoreboard covers the
active canvas, not electrical LCD timing. No 30 fps or physical throughput claim
is supported.
