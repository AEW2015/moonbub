# V74 tile-aware portrait painter

V74 preserves the V73 bit-exact 720×480 YUV420-to-RGB565 conversion, bilinear chroma rounding, four opaque HUD rectangles, portrait transpose, 40-row black borders, result identity, start validation, and drain-before-abort behavior. It changes canonical input access to tile-major BL8 reads. No predecessor source or result is rewritten.

## Memory contract

Addresses count 16-bit words. Plane starts remain Y=0, Cb=172800, Cr=216000 words relative to the canonical bank. Each 8×8-byte tile occupies 32 contiguous words, low byte first; Y has 90 tiles per row and each chroma plane has 45.

For a plane with byte width `W`, byte coordinate `(x,y)` resides at word offset:

```
((y / 8) * (W / 8) + x / 8) * 32 + (y % 8) * 4 + (x % 8) / 2
```

`aux_req_read_burst=1` requests an aligned eight-word read, returned in `aux_rsp_burst_data[127:0]` with the lowest-address word in bits 15:0. `aux_req_burst` continues to identify writes only; all writes carry 128 bits and mask `ffff`. Scalar `aux_rsp_data` remains in the compatibility interface but is not consumed by V74. One operation may be outstanding. The service holds its response until accepted; accepted commands drain before releasing the painter on abort or memory error.

## Prefetch and cache tradeoff

An eight-row Y stripe is prefetched by tile column, four BL8 reads per tile. Each response is captured in a 128-bit register and unpacked across eight clocks; only one cache word is written each clock. Each of eight explicit Y banks stores 360 words.

Chroma uses eight row banks per plane, each 180 words. Two four-row quads are tagged by global quad index, in slots `quad & 1`. Stripe `S` needs chroma rows `S/2` through `min(S/2+4,239)`. Initially quads 0 and 1 are loaded; subsequent stripes retain the overlapping quad and load one new quad. The final stripe retains quad 59 without fetching an invalid quad 60. Each quad is loaded in 45 tile columns, two BL8 reads per tile; the final chroma row clamps exactly to row 239.

HUD data is fetched only for hitbox pixels. Each aligned eight-word HUD-cache miss uses one BL8 read and serial unpack, preserving all 21,120 opaque words and their order. Eight independent 720-word RGB strip banks retain the V73 portrait write layout.

| Data cache | Bytes |
|---|---:|
| Eight Y rows | 5,760 |
| Eight Cb + eight Cr rows | 5,760 |
| Eight RGB565 strip rows | 11,520 |
| Eight HUD words | 16 |
| Total | 23,056 |

The predecessor data-cache footprint was 13,696 bytes. V74 spends 9,360 additional bytes to avoid tile-major raster reread thrashing. Control state, the two six-bit quad tags, response/write registers and pipeline registers are additional; this table is not an FPGA primitive count.

## Evidence

Reproduce using `python3 scripts/cu66-v74/run_painter.py`. The runner builds the actual SystemVerilog with Verilator 5.020, full `--Wall`, `-j 1`, and bounded subprocess/frame watchdogs. Only the unused compatibility scalar response input has a narrow in-source unused-signal annotation. The independent native decoder/render supplies full-precision RGB565 expectations; input planes are placed into memory by an independent pixel-coordinate tile formula.

The generated `fpga/experiments/cu66-v74/display/results.json` records source and fixture hashes, command/log hashes and case results. Three schedules (0, 7201, 7202) each cover eight real key/P frames from four fixture cohorts, four synthetic patterns, and a recovery raster: **39 complete rasters and 14,976,000 compared RGB words**. Each schedule also rejects the ten preserved invalid-start cases without issuing memory work.

Every complete raster requires:

| Operation | Accepted commands | Logical words |
|---|---:|---:|
| Y reads | 21,600 | 172,800 |
| Cb reads | 5,400 | 43,200 |
| Cr reads | 5,400 | 43,200 |
| HUD reads | 2,640 | 21,120 |
| Total reads | **35,040** | **280,320** |
| Portrait canvas + black-border writes | **48,000** | **384,000** |

The RTL exports read commands through `memory_reads`, input words through new `memory_read_words`, write commands through `memory_writes` and output words through `memory_write_words`. Painted active pixels remain 345,600. Every output word is written exactly once; the bench checks stalled request addresses, qualifiers, masks and all payload words for stability.

The two delayed schedules retain ten original abort/read-error/write-error probes and add six probes across Y-prefetch unpack, HUD unpack and pending HUD-wide response: **16 fault probes**, followed by exact recovery. These checks enforce no result for aborted/errored work and no lease release while a response is outstanding.

| Service schedule | V73 cycles per complete raster | V74 cycles per complete raster |
|---|---:|---:|
| No injected stalls | 1,422,489 | 1,212,249 |
| Seed 7201 | 3,007,114–3,012,733 | 1,612,487–1,614,882 |
| Seed 7202 | 3,006,564–3,012,211 | 1,612,552–1,615,241 |

These are painter cycles under the bench's ideal delayed memory service. Wide reads reduce command count eightfold; they do not reduce logical source words. This evidence does not establish actual SDRAM latency, target clock, exact-device fit, physical 30 fps or sub-10-ms decode. The full controller/system replay and exact target implementation remain separate gates.
