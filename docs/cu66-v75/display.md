# V75 tile-aware portrait painter

V75 preserves the V74 tile-major packet/memory contract, bit-exact 720×480 YUV420-to-RGB565 conversion, bilinear chroma rounding, four opaque HUD rectangles, portrait transpose, 40-row black borders, result identity, start validation, and drain-before-abort behavior. It changes the internal input-cache read pipeline to register full 16-bit memory words before selecting a byte. No predecessor source or result is rewritten.

## Memory contract

Addresses count 16-bit words. Plane starts remain Y=0, Cb=172800, Cr=216000 words relative to the canonical bank. Each 8×8-byte tile occupies 32 contiguous words, low byte first; Y has 90 tiles per row and each chroma plane has 45.

For a plane with byte width `W`, byte coordinate `(x,y)` resides at word offset:

```
((y / 8) * (W / 8) + x / 8) * 32 + (y % 8) * 4 + (x % 8) / 2
```

`aux_req_read_burst=1` requests an aligned eight-word read, returned in `aux_rsp_burst_data[127:0]` with the lowest-address word in bits 15:0. `aux_req_burst` continues to identify writes only; all writes carry 128 bits and mask `ffff`. Scalar `aux_rsp_data` remains in the compatibility interface but is not consumed by V75. One operation may be outstanding. The service holds its response until accepted; accepted commands drain before releasing the painter on abort or memory error.

## Prefetch and cache tradeoff

An eight-row Y stripe is prefetched by tile column, four BL8 reads per tile. Each response is captured in a 128-bit register and unpacked across eight clocks; only one cache word is written each clock. Each of eight explicit Y banks stores 360 words.

Chroma uses eight row banks per plane, each 180 words. Two four-row quads are tagged by global quad index, in slots `quad & 1`. Stripe `S` needs chroma rows `S/2` through `min(S/2+4,239)`. Initially quads 0 and 1 are loaded; subsequent stripes retain the overlapping quad and load one new quad. The final stripe retains quad 59 without fetching an invalid quad 60. Each quad is loaded in 45 tile columns, two BL8 reads per tile; the final chroma row clamps exactly to row 239.

HUD data is fetched only for hitbox pixels. Each aligned eight-word HUD-cache miss uses one BL8 read and serial unpack, preserving all 21,120 opaque words and their order. Eight independent 720-word RGB strip banks retain the V74 portrait write layout.

| Data cache | Bytes |
|---|---:|
| Eight Y rows | 5,760 |
| Eight Cb + eight Cr rows | 5,760 |
| Eight RGB565 strip rows | 11,520 |
| Eight HUD words | 16 |
| Total | 23,056 |

The logical data-cache footprint remains the V74 total of 23,056 bytes. The change concerns read-port structure and primitive inference, not reduced stored pixel capacity. Control state, the two six-bit quad tags, response/write registers and pipeline registers are additional; this table is not an FPGA primitive count.

## Clocked full-word read pipeline

Each of the eight Y banks and sixteen Cb/Cr banks now has one synchronous full-word read port and one write port. Memory output registers have no reset; output validity comes from the prefetch and pixel-state schedule. Unpack writes occur only in `UNPACK`, and input reads occur only in the pixel-fetch states. Registering a full 16-bit word keeps the byte selector outside the memory port.

`PIXEL_FETCH` reads the Y word and the left chroma words. `PIXEL_FETCH_RIGHT` samples the Y byte and left chroma bytes from those registered outputs while requesting the right chroma words through the same per-bank read port. `PIXEL_COMPOSE` sees the registered right words, selects their bytes and uses the unchanged conversion/rounding. The bottom-row clamp still selects row 239. This serialization removes the previous second chroma read port and adds one clock per active pixel, including HUD-covered pixels.

The BRAM output registers need not be reset because no sample can be composed before the prefetch and both word-fetch states complete. An abort suppresses cache reads/writes, enters the existing drain state and produces no successful result. Any accepted external operation drains before the painter returns to its idle lease boundary. The next start invalidates all quad/HUD tags and refills the required source data.

## Evidence

Reproduce using `python3 scripts/cu66-v75/run_painter.py`. The runner builds the actual SystemVerilog with Verilator 5.020, full `--Wall`, `-j 1`, and bounded subprocess/frame watchdogs. Only the unused scalar compatibility response input has a narrow in-source unused-signal annotation. The independent native decoder/render supplies RGB565 expectations; input planes are placed by an independent pixel-coordinate tile formula.

The generated `fpga/experiments/cu66-v75/display/results.json` records source, fixture and command-log hashes. Three schedules (0, 7201, 7202) each cover eight real key/P frames from four fixture cohorts, four synthetic patterns and a recovery raster: **39 complete rasters and 14,976,000 compared RGB words**. Each schedule rejects ten invalid-start cases without issuing memory work.

Every complete raster retains the V74 traffic counts:

| Operation | Accepted commands | Logical words |
|---|---:|---:|
| Y reads | 21,600 | 172,800 |
| Cb reads | 5,400 | 43,200 |
| Cr reads | 5,400 | 43,200 |
| HUD reads | 2,640 | 21,120 |
| Total reads | **35,040** | **280,320** |
| Portrait canvas + black-border writes | **48,000** | **384,000** |

Every output word is written exactly once. The bench checks stalled addresses, qualifiers, masks and all payload words for stability. Successful frames retain exact 345,600 active painted pixels and the existing full physical framebuffer check.

The delayed schedules retain the eight V74 fault probes each and add two read-pipeline abort probes each: **20 fault probes total**, followed by an exact recovery raster. The added probes abort after the clocked left-word fetch and before pixel composition, respectively. They target pixel progress 16, outside HUD hitboxes, with no outstanding external memory lease; both require no extra painted pixel and no successful result after abort. Their schedule is defined by the public painted-pixel progress and the fixed fetch pipeline. The existing pending external read/write, prefetch unpack and HUD unpack/response probes continue to test accepted-operation drain behavior.

The no-stall raster is **1,557,849 cycles**, versus V74's 1,212,249: exactly **345,600 additional cycles**, one per active pixel. Random-delay schedule cycle ranges are retained per case in the result JSON; random service scheduling changes with extra clocks, so their differences are not isolated memory-service measurements. Actual SDRAM/LCD contention must be measured in the full-system replay.

`display/before-read-stage-probes/` preserves the initial native 39-raster/16-fault qualification in an eight-member source-and-evidence ZIP with internal member hashes; it is superseded by the current stronger 20-fault regression. The RTL was unchanged when those probes were added. `build-initial-comb-order.log` preserves an initial strict-lint combinational assignment-order diagnostic. That order was corrected before the first passing simulation; the retained diagnostic is not qualification evidence.

[Frontend and mapping results](elaboration.md) show that the input banks infer BRAM in the bounded unplaced XC7 family flow. Neither these finite tests nor family mapping establishes exact-device fit, target clock, routed timing/CDC, physical 30 fps or under-10-ms validated decoding. Full controller/system replay and target implementation remain separate gates.
