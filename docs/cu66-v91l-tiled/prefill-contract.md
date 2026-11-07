# Source-derived prefill-order tile8x8 model

This Python-only study adapts the tile8x8 unused-byte retention model to the
actual chroma-prefill and luma consumer order in the frozen V91k converter.
The line-address vector is **DERIVED_FROM_SOURCE**, not captured from physical
address events. The RTL trace records `row_fill` events, not line addresses.

## Derived access order

`canonical_rgb565_cached.sv` is entered at `CHECK_ROWS` for each output pixel.
Before the luma request for a row, it fills missing chroma rows in `cy` then
`bottom_row` order. A row fill requests all 360 Cb bytes, followed by all 360 Cr
bytes. It then enters the luma request state for each pixel in raster order.
The exact row schedule matches `tb_lines.cpp::schedule`: chroma rows 0 and 1
are filled before Y row 0; row 2 is filled before Y row 2; each subsequent row
`r` is filled before Y row `2*(r-1)`; row 239 is the bottom-row alias for output
rows 478 and 479, so no row 240 is requested. The line reader has one independent
16-byte aligned line tag for each of Y, Cb, and Cr. Replaying those tags over
this source-derived byte sequence yields 32,400 unique aligned line misses.

The fixture `experiments/python-gamebub-v91l-tiled/vectors/prefill-lines.hex.gz`
contains one aligned canonical client address per line-reader miss, as five
lowercase hex digits per line. These are source-layout client addresses, not the
tile-mapped physical addresses generated inside the candidate model. Its
decompressed bytes preserve request order. The Python
model also replays both profile-0 canonical frame goldens (`actual_001` and
`actual_006`) through every source-derived byte consumer request and checks exact
byte values.

## Tile8x8 comparison

The independent baseline retains only the current physical 16-byte line tag per
plane. On each scalar consumer byte, it fetches a BL8 when that byte's
tile-mapped line differs from that plane's current tag; it does not retain
unused bytes across later line requests. This is the current-line-tag control
model and a fetch-count comparison, not a claim about a particular new RTL
scratch scheduling implementation. The retention model stores unused bytes from each fetched
BL8 by their future logical address and consumes them in that plane's monotonic
consumer order. Both models use the same 360x240 chroma edge geometry and exact
consumer sequence.

The observed peak pending occupancy, including bytes left over from the current
BL8, is 727 Y bytes, 367 Cb bytes, and 367 Cr bytes, with 1,447 bytes maximum
across all three planes at once. Inserted bytes are checked to belong to the
current or next logical row in their plane. The per-plane peaks are each seven
bytes above the nominal 720+360+360 plane allocations; total peak is 1,447, within
1,440 bytes of retained storage plus the shared 16-byte BL8 scratch. A separate
16-byte output register brings the proposed data budget to 1,472 bytes. This is a storage
accounting proposal only; it is not implemented RTL. Reusing the current
chroma-prefill RAM would need an explicit architecture change and is not claimed
here.

## Provenance and scope

`prefill-results.json` pins the generator, all source files read for the order
and prior retention model, and the canonical input gzip. `--check` regenerates
the expected vector bytes in memory and compares both the compressed fixture
and JSON report with the checked-in files.

The report pins the generator SHA, source hashes, canonical input gzip SHA, and
input report SHA. This is a deterministic Python candidate-memory replay. It provides no hardware
latency, throughput, timing, controller, refresh, or resource-fit result. The
independent baseline is the stated current-line-tag policy; retained mode is a
proposed logical-byte buffer model. Neither represents a measured SDRAM trace.

Run the freshness check from the repository root:

```sh
python3 experiments/python-gamebub-v91l-tiled/prefill_model.py --check
```
