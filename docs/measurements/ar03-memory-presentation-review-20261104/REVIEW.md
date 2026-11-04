# Private KEY to memory and presentation: read-only architecture review

Date: 2026-11-04. No RTL/source edits, builds, simulations or hardware actions.
The only executed program was `collect.py`: it read local/pinned Git files,
verified selected build50 sources against their native build bindings, and wrote
`bindings-and-arithmetic.json`. Arithmetic below is not measured memory service.

Frozen semantics remain MoonBub kit
`27a4dde6a7e2ea4fab09d892551ef542f05c8965` and Sunshine native oracle/plan
`c9c0bf4bcbe5c95f38b50bf6e190b84822886d53`. The JSON binds exact Git objects,
paths, SHA-256s, selected local sources/reports and the collector itself. Existing
local repositories were inspected, not assumed to exist on another computer.

## Reusable baseline

Use `fpga/candidates/v21-audio/rtl`, selected build50/USR_ACCESS `0x4D424F50`,
manifest SHA-256
`ab274599ef9372addb19bd2a9c15a1e74458d0e66fe55c818695ebb54b099270`.
The selected native source-binding file SHA-256 is
`e10b84d0de58984180d56dc32b9ac1ab5d669b4000200f615ea4e2d551c0ded1`.
Do not substitute the older `fpga/rtl/moonshine_memory.sv` single-write path.

- `moonshine_memory_burst`: 16-bit pixel valid/ready, 24-bit **word** address,
  `force_flush`, `discard`, and `idle`. A single aligned masked BL8 packer feeds
  `moonshine_sdram_burst`. Scanout reads take priority between bursts.
- `moonshine_sdram_burst`: 100 MHz, 16-bit SDR, aligned eight-word requests,
  128-bit write payload, 16 byte-mask bits; four tracked open rows, refresh and
  a separate 279-degree read clock. It has no multi-client read tags.
- `moonshine_lcd_720p`: two 480-word dual-clock line banks with request/done
  toggles, held payload and frame epochs. It fetches 480 words per portrait
  line. The landscape coded canvas is stored at `base + x*480 + y`, not normal
  `y*720+x`. Existing RGB bases are 0 and `0x080000` **words**.
- `moonshine_core_overlap`: useful examples of front/back ownership, write
  drain, `force_flush`, abort barrier and presentation on `frame_boundary`.
  Reuse those responsibilities through a new controller; do not graft AR03
  semantics onto the JPEG CSR/status identity.
- Existing JPEG tile coalescing drains a 16x16 tile column-major to make these
  portrait framebuffer writes contiguous. A raster-order RGB renderer connected
  directly to the one-group packer would flush on almost every address-group
  change. Preserve a bounded transpose/coalescing stage.

AKD1 currently removes the memory controller and keeps SDRAM inactive. Its LCD
bars are independent of decoded KEY samples. Re-enabling memory requires the
actual live read clock, I/O/CDC constraints, reset/initialization and board gates;
the diagnostic's inactive-interface assertions cannot simply be removed.

## Compact YUV and a jointly backpressured raster tee

`ar03_key_tagged` already emits canonical plane/raster-order uint8 samples with
owner/epoch/frame/plane/x/y/last. Its raster transfer and SHA input are joined to
`sample_ready`; an external memory sink can therefore backpressure the same
accepted sample. This is a useful seam: one accepted sample must advance both
the hash path and private storage, never one independently of the other.

Pack two adjacent YUV bytes into each 16-bit word and aligned BL8 groups for
sequential storage. Do not expand physical banks to int16 merely because the
canonical SHA format hashes each sample as low byte followed by zero. A complete
720x480 YUV420 uint8 image is 518,400 bytes (Y345,600/Cb86,400/Cr86,400).

This tee does **not** solve display rendering: the stream emits all Y before Cb
and Cr. The pinned `body_decoder.h::render565` needs bilinear co-sited chroma,
including right/below neighbors and edge replication, followed by exact integer
full-range RGB and RGB565 truncation. Nearest-neighbor chroma or generic JPEG
color conversion would not match this oracle. Its signed floor/rounding rules
must be preserved, including negative chroma products.

The simplest first renderer reads a private compact YUV image using bounded
chroma/tile caches, transposes RGB output for the existing portrait framebuffer,
then writes the back framebuffer. It needs a real additional memory read client:
the current adapter exposes only fixed 480-word LCD reads, not arbitrary YUV
reads. Add explicit response ownership/arbitration at the burst-controller seam;
do not misuse LCD completion tokens or assume reads are instantaneous.

## Integrity, HUD and separate publications

The envelope currently validates outer/nested bounds and records patch offsets;
it does not implement the HP01/HR01 display patch decoder. For a complete AR03
display, implement exact patch CRC/header/length/mode/palette/token/padding and
geometry validation, reject overlapping patches, and honor all mandatory
rectangles. The pinned native renderer applies patches only after base RGB565.
Patches never enter predictor samples or the canonical tag. Mandatory regions
contain 21,120 RGB565 words per frame. Preserving the existing menu overlay is
separate from implementing these encoded game HUD patches.

Keep these ownership/publication events distinct:

1. Provisional YUV samples and display writes may exist privately before final
   validation. They are not a new reference or visible frame.
2. Reference publication requires complete validated input/patch syntax, exact
   canonical tag, valid destination ownership and actual storage drain. The
   frozen native decoder leaves prior state and samples unchanged on rejection.
   Thus do not overwrite an existing logical bank in place before a tag/patch
   failure is impossible. Use unpublished physical backing and atomic logical
   remapping (or another explicitly proved preservation scheme). Two published
   logical banks plus a provisional destination generally need a third physical
   compact YUV region. For the very first KEY, an initially empty unpublished
   destination can be sufficient; that does not implement general P recovery.
3. AF03 confirms the exact stored reference identity/tag. A normal no-store P
   (`destination=255`) does not create a reference. An AF03 may be independent of
   panel presentation only with explicit distinct state/counters and held leases.
4. Visible presentation requires every required RGB/HUD write drained, a ready
   back framebuffer and a frame-boundary swap. Count the unique frame ID at that
   swap. Source completion or an ingress ACK is not this event.
5. Packet permits, FINISHED and frame RELEASE retain their own ingress/read/
   decode drain requirements. Neither AF03 nor presentation manufactures a
   packet credit or proves another owner's buffers reusable.

On abort/error, discarding a packer's unissued group does not undo an SDRAM burst
already accepted. Retain the affected region/job until accepted writes and reads
are drained. Prevent old-epoch completions or an old LCD request from publishing
or releasing new ownership. Reset/rekey remains the agreed unresolved production
contract; this review adds no UDP port, capability or wire fields.

## Resource and bandwidth arithmetic

The current routed AKD1 LCD-prune report uses 106/135 RAMB36 tiles, leaving 29;
its private compute uses41, fixture ROM16, audio4, bridge1 and overlay44. Build50
uses120.5/135 equivalent tiles. A whole compact YUV image would require112.5
RAMB36 tile-equivalents before mapping overhead, so full YUV banks cannot be
added to the remaining BRAM. Store full images externally and budget bounded
tile/line caches. Removing the fixture ROM in a later real ingress design is a
separate source/resource change, not available free memory in this candidate.

Preset0 has a 29.361979 MHz pixel clock and 541x834 total geometry: approximately
65.07617 panel refreshes/s. Do not silently assume60 Hz.

| Useful payload operation | Arithmetic MB/s (decimal) |
| --- | ---: |
| Repeated 720x480 RGB565 scanout at preset0 |44.981|
| RGB565 back writes at30 unique frames/s |20.736|
| Compact YUV stores at30 frames/s |15.552|
| Ideal one-read compact YUV render input at30/s |15.552|
| KEY store + render read + RGB write + scanout lower bound |96.821|
| Above plus one compact predictor read per P frame |112.373|

The nominal SDR bus ceiling is200 MB/s, but this is not useful service. BL8
request/turnaround cycles, refresh, row activation/precharge, write masks and
nonideal chroma reuse reduce it. Separate patch overwrites would add up to1.2672
MB/s for the mandatory words; a renderer that merges patches before its single
RGB store avoids that particular extra pass. Measure arbitration under real
scanout deadlines rather than accepting a sum below200 MB/s as a pass.

The retained `sdram_model_burst` has only1,048,576 words (2 MiB). Two existing RGB
apertures already occupy that address range. Add an explicit bounded enlarged
model for new YUV regions, check every accessed range for bounds and aliasing,
and confirm the actual board part/address capacity before a physical layout.
The controller's 24-bit word address is an interface width, not proof of installed
capacity. Do not silently truncate addresses into the existing model.

## Smallest next simulation seams

First implement **KEY raster storage and drain**, without P or a live transport:
use the real tagged KEY fixture, join its canonical raster/SHA transfer to a
bounded byte-to-word sink, then the actual burst packer/controller and bounded
BL8 SDRAM model. Preserve a competing read workload using the real LCD request
shape or an existing held front framebuffer. Compare all518,400 YUV bytes in
the model with the pinned oracle and validate nonalias regions. Prove final
flush/idle, no early publication, held-ready behavior and abort after partial/
accepted bursts. A direct scoreboard readback proves storage only; it does not
stand in for the later RTL renderer's read port.

Second implement **one complete KEY display**: bounded YUV read arbitration,
exact bilinear/RGB565 renderer, HP01/HR01 patch decoder, tile transpose and the
actual back-framebuffer write/LCD line path. Compare all345,600 displayed RGB565
words against a pinned complete mandatory-HUD native fixture. Check orientation,
both edges and existing margin/porch settings. Assert zero old/new frame mixing,
drain-before-swap, unique frame identity and no publication after any malformed
CRC/tag/patch or mid-burst reset. Use natural unrelated clocks and real line
buffers, not a fake callback that equates decoder completion with presentation.

Only afterward add exact-reference P reads, logical bank remapping/promotion,
read leases, no-store frames and AF03 atomicity/recovery transcripts. The full
pipeline must then measure sustainable initiation interval, scanline service and
unique presentation intervals. The private fixture's roughly30 ms compute
simulation leaves little unmeasured budget and is not a demonstrated30 fps
display pipeline. No source/transport or physical30 fps readiness is established
by this architecture review.
