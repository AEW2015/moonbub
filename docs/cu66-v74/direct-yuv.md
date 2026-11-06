# Direct-YUV portrait traffic estimate

`scripts/cu66-v74/direct_yuv.py` models the proposed 8×8 tile-major physical
mapping using standard-library Python. It tests address bounds, tile/row edges,
last chroma clamps, chroma parity counts, BL8 beat/byte accounting, and the four
native HUD rectangle areas. Full output is retained in
`fpga/experiments/cu66-v74/direct-yuv-results.json` with source hashes and
per-strip details.

## Results

The 480×720 physical active image reads the 720×480 coded image over 90 strips,
each eight physical rows wide. For a 16-byte BL8 and 16-byte cache lines, naive
portrait-order point access produces 356,160 misses / 5,698,560 wire bytes per
frame for each tested LRU or round-robin cache size (8, 64, 128, 256 lines;
128–4,096 bytes). Those capacities do not capture the tile-major scan's
working set.

Strip prefetch with rolling LRU was measured at 8, 64, 128, 256, 512, 720, and
1,024 lines (128–16,384 bytes). At 8–256 lines it gives 480–720 YUV BL8 lines
per strip (7,680–11,520 bytes), or 860,160 bytes per display frame. A 512-line
cache lowers this to 805,632 bytes. At 720 lines (11,520 bytes), halo tiles
survive across strips and reads reach the 518,400-byte packed-plane bound:
32,400 BL8 bursts / 259,200 beats. The 1,024-line result is the same. This
corresponds to 33.74 MB/s at 65.0755 Hz. Conservative additive HUD reads are
42,240 bytes per panel, with up to 1,536 bytes in one strip.

With the 720-line cache, the largest strip is 7,680 YUV bytes plus 1,536 HUD
bytes. Raw 200 MB/s transfer time is 46.08 µs, or 31.3% of the 147.403024 µs
deadline. Including HUD as 16-byte BL8 transactions, the assumed controller
service time is 115.2 µs at 20 clocks/burst and 184.32 µs at 32 clocks/burst,
using the current model's 100 MHz clock. The 20-clock case fits only before
unrelated traffic; the 32-clock case misses the deadline. The per-burst costs
are assumptions, not measured service for this path. ACT/PRE estimates are
8,100 ACT and 8,099 PRE commands, all assigned to bank 0 with the requested
address slicing. Refresh, controller row policy, turnaround, and competing
clients are omitted.

The candidate YUV upload contributes 518,400 bytes × 30 fps = 15.552 MB/s.
At panel refresh, the 720-line direct-YUV result reads 518,400 bytes plus HUD
reads per panel. Direct-YUV, HUD, and uploads total an estimated 52.04 MB/s
(26.0% of assumed 200 MB/s raw bandwidth), before reference-reader traffic or
other controller work. The current painter writes 384,000 RGB565 words per
source frame (768,000 bytes), including generated black border rows; at 30 fps
this is 23.04 MB/s. The LCD requests 345,600 active canvas words per panel
(691,200 bytes) at 65.0755 Hz, or 44.98 MB/s. It generates the 80 physical
border rows black without reading RGB memory. Baseline RGB writes plus LCD
reads are about 68.02 MB/s at those separate rates.

## Limits and next gates

This is a deterministic address/cache traffic model, not the exact display
renderer, a cycle-accurate controller model, a physical SDRAM trace, or a proof
of display cadence or 30 fps. It assumes exact bilinear parity behavior (1, 2,
or 4 chroma neighbors per output sample), and counts repeated clamped-edge
neighbors conservatively while merging their physical BL8 addresses. It also
fetches YUV beneath opaque HUD overlays and adds the 21,120 HUD words.

The reference reader and direct display can contend for the same canonical
SDRAM bank; that live interference is not modeled. Front-buffer generation and
lease changes must invalidate any direct-YUV cache before reuse. Exact pixels,
lease safety, controller service under upload/reference/painter/HUD traffic,
scanout underruns, and fixed 30-fps arrivals remain open RTL/integration and
target measurements.
