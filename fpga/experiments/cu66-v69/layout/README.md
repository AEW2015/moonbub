# CU66 layout and portrait scanout proof

Run the proof in the pinned project environment:

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python fpga/experiments/cu66-v69/layout/prove_layout.py
```

`results.json` pins the RTL, LCD simulation, CU66 receiver, V67 independent filter verifier, and actual native fixture sources. The chosen sample is frame 0 (a key packet) from the archived `mass-effect-10000` case. The script decodes it with frozen `Receiver(profile='CU66')`, checks packet/canonical/HUD/output-tag hashes against the v69 manifest, runs the frozen strong luma filter, performs canonical color conversion and exact HUD overlay, then archives the resulting active raster as two physical RGB565 streams (`identity` and `strong-filter`). The filter is the fixed preset calibrated on the first 24-frame windows in the existing study; this one-frame physical-layout proof does not qualify filter quality on new content. Each stream is row-major physical scan order `y,x`, little-endian u16, dimensions 800×480, including both black bars.

## Coordinate mapping from the RTL

The source's `moonshine_core.sv` maps a decoded coded coordinate `(u=dec_x,v=dec_y)` to RGB565 word address `base + (u + 40) * 480 + v`. `moonshine_lcd.sv` scans 480 pixel positions per line and requests successive portrait rows at 480-word strides; `moonshine_lcd_tb.sv` independently computes `landscape_x = scan_y - 24`, `landscape_y = scan_x - 14` and reads `landscape_x * 480 + landscape_y`. Together these give:

- Physical scan x is coded `v`; physical scan y is coded `u + 40`.
- Inverse mapping inside the image is `u = physical_y - 40`, `v = physical_x`.
- The 720 coded x positions occupy physical y `[40,760)`. Physical y `[0,40)` and `[760,800)` are black bars: 38,400 pixels total.
- Every one of 345,600 coded pixels round-trips; the proof also checks all 384,000 physical raster positions and verifies black bars.

This is the actual RTL's transposed portrait memory mapping; the proof does not add a flip or infer one from panel mounting. Canonical CU66 hashing remains row-major planar Y, Cb, Cr. SRAM/SDRAM placement may be transposed or tiled, but a decoder/hash adapter must present canonical samples in their normative order rather than hashing physical scan traversal.

## Address-trace comparison

The trace model uses one byte address per u8 sample. The write stream follows conventional 8×8 block order (`v` tile, `u` tile, local `v`, local `u`); the read stream follows actual physical scan order (coded `u` outer, coded `v` inner). Each 16-byte burst is aligned and counted independently per noncontiguous increasing run; this deliberately assumes no cache or cross-run coalescing. These are locality estimates only. The existing SDRAM controller performs single writes, so the figures are not observed controller transactions or timing.

| Layout | Transform-block write locality | Physical scan-read locality |
|---|---|---|
| Canonical row-major plane | 8-sample row segments; 50% logical 16-byte occupancy | Strided; one-sample runs; 6.25% occupancy |
| Plane-transposed | Scattered writes; 6.25% occupancy | Fully sequential; 100% occupancy |
| 8×8 tile-major in coded tile order | Fully sequential tile writes; 100% occupancy | Scattered; 6.25% occupancy |
| 8×8 tile-major oriented to physical scan | Scattered for coded block writer; 6.25% occupancy | 8-sample segments; 50% occupancy |

`results.json` contains exact per-plane counts. Luma has 345,600 samples; Cb and Cr have 86,400 each. The tile-major physical orientation is included as a layout option, not claimed as an RTL implementation. Address locality presents a write/read tradeoff; it does not show that any option fits existing BRAM or SDRAM timing.

## Capacity and traffic accounting

The 720×480 YUV420 frame has 345,600 Y samples and 86,400 each of Cb and Cr: **518,400 bytes** at one u8 per sample. A reference read plus replacement-reference write is **1,036,800 logical bytes**. If two samples are packed per x16 SDRAM word, that is 259,200 words per frame and 518,400 word transfers for the read-plus-write pair; actual banking/packing is not implemented by this proof.

The native physical RGB565 stream is 800×480 = 384,000 words (768,000 bytes) including black output bars; the image itself is 345,600 words. These counts do not imply a frame-rate or bus-utilization result. Existing `moonshine_sdram.sv` has a 24-bit word address and selects one SDRAM chip; the Rev4.1 schematic records two 32 MiB chips, but this controller mapping only reaches one 32 MiB device. The displayed artifact is Python data, not a BRAM-fit claim, physical panel capture, or whole-system memory budget.
