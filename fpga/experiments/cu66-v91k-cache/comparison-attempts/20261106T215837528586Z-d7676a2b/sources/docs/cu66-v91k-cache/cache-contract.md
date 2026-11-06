# V91k two-row chroma cache model contract

This document defines the independent Python schedule and data-parity model for
an exact two-row Cb/Cr cache in the base 720×480 RGB565 converter. It consumes
the retained canonical bytes captured from the V91k reconstruction RTL and
compares the modeled converter output with the independently derived V91k
RGB565 goldens. The model does not modify or qualify the frozen V91k controls.

## Source evidence and inputs

The frozen source is commit `914fe698ba61ac0b266dd45c722fca2b86d995a7` and the
retained RTL replay report is
`fpga/experiments/cu66-v91k/pipeline-results.json`. Its accepted candidate
memories are `canonical_actual.tsv.gz` from the selected V91k pipeline attempt;
the independent RGB words are in `vectors/rgb_goldens.tsv.gz` in that same
attempt. `experiments/python-gamebub-v91k-cache/model-results.json` records the
report SHA-256, frozen source hashes, both vector SHA-256 pins, and results for
all six frame IDs in profiles `0` (FAST) and `1` (SLOW). The Python runner
checks those compressed artifact pins before reading data.

The canonical memory has exactly 518,400 bytes: 345,600 Y bytes followed by
86,400 Cb bytes and 86,400 Cr bytes. All 12 retained profile/frame memories
are consumed. Each generated RGB565 frame is compared byte-for-byte with its
same-ID independent golden. The two service profiles must preserve identical
canonical contents per ID.

## Cached external read schedule

Rows are raster ordered, with absolute addresses `Y = y*720+x`,
`Cb = 345600+cy*360+cx`, and `Cr = 432000+cy*360+cx`.

1. Before output pixel `(0,0)`, fill paired chroma row 0: read all 360 Cb bytes
   in increasing column order, then all 360 Cr bytes in increasing column
   order. Repeat for row 1.
2. For each luma row, before reading its first Y byte, ensure its chroma pair
   `(cy, min(cy+1,239))` is resident. At the first even luma row for each new
   `cy` from 1 through 238, fill only newly needed bottom row `cy+1`, Cb then
   Cr, before that row's first Y request. Odd luma rows reuse the same pair.
3. For each pixel, read its one Y byte. Chroma neighbor requests are local
   registered cache lookups and do not create external byte reads.
4. At `cy=239`, the bottom lookup aliases the top row. No row 240 read occurs.

The two row slots are selected by `row & 1`. In each slot, chroma columns are
split across parity banks: bank `column & 1`, word `column // 2`. Each 16-bit
word pairs the Cb and Cr value at one chroma coordinate. The four row-slot ×
parity banks each hold 180 words × 16 bits, for 1,440 logical bytes total.
Top and bottom use different slots while the chroma pair advances. Horizontal
neighbors use different parity banks; right-edge replication selects the same
column. The fill tag becomes valid only after both full plane rows have been
acknowledged, including the last Cr byte.

There are 240 paired-row fills per frame: two startup fills and one new bottom
row fill for each following chroma row. External read totals are 345,600 Y +
86,400 Cb + 86,400 Cr = 518,400 bytes. The uncached reference schedule reads
one Y and four samples from each chroma plane per pixel, for 3,110,400 reads.
The model hashes every accepted read as its 32-bit little-endian byte address
followed by the returned byte, using 64-bit FNV-1a with offset
`1469598103934665603` and prime `1099511628211`. Per-frame cached and uncached
hashes are recorded in the results JSON.

## Pixel arithmetic and timing boundary

Horizontal interpolation on odd x is `(left+right+1)//2`; vertical
interpolation on odd y is `(top+bottom+1)//2` after horizontal rounding. Even
coordinates select the direct sample, and image edges replicate the final
column or row. The model subtracts 128 from interpolated chroma, uses the frozen
signed floor-shift RGB equations and clipping, then truncates to RGB565. It
checks every modeled word against the independent golden.

The RTL implementation uses a registered local lookup request/response stage;
this Python external-read schedule does not grant zero-cycle BRAM behavior or
claim measured RTL timing. It proves the address/data schedule count, complete
byte coverage, the parity-bank address mapping, and RGB output parity in
software. It does not prove inferred block RAM/DSP/logic counts, routed clock,
physical bandwidth, 30 fps, or complete validated frame latency below 10 ms.
