# Direct compact-YUV scanout alternative

Read-only design study; no new RTL, simulation, build, bank map or hardware
result. Source hashes and calculated values are in
`evidence/coordinated-ar03-20261104/direct-yuv-scanout-review-20261104/analysis.json`.
The exact RGB arithmetic already has separate executed native-oracle evidence
in `fpga/experiments/ar03-rgb565-tag-width-20261104`. That evidence does not cover
the caches, addressing, scanout, publication or service budgets proposed here.

**Recommendation: simulate a static-front, column-major YUV scanout seam before
committing to a full external RGB backbuffer renderer.** It can nearly halve
useful no-HUD KEY traffic, but moves conversion and overlay traffic onto every
panel refresh. Deadline service and ownership remain decisive.

## Actual traversal and refresh

The retained build50 LCD source is
`fpga/candidates/v21-audio/rtl/moonshine_lcd_720p.sv`. For the native 720x480
canvas (`front_720p=0`), its physical portrait active area is 480x800:

- Physical active x, `px=0..479`, corresponds to landscape sample **y**.
- Physical active y minus the applied margin, `source_py=0..719`, corresponds
  to landscape sample **x**.
- Thus one portrait scanline visits a complete landscape **column**, not a
  landscape row. The rest of the 800-line active area is black.
- Margin changes placement only. They do not change the coded YUV coordinates
  used for interpolation or hashing. The 1280x720 scaled-JPEG crop mode is outside
  this native-canvas calculation.

Preset0 is 29,361,979.1667 pixel clocks/s, 541 clocks/line and 834 lines/frame:
65.0761738 refreshes/s, 15.366607 ms/refresh and 18.425188 us/line. This is not a
60 Hz display. A held front still needs to be scanned repeatedly between new
30 fps frame arrivals.

The existing alternating 480-word RGB line banks request landscape column k+2
after column k finishes scanning. The nominal interval from that request point
to k+2's first active pixel is `(2*541-480)/pixel_clock = 20.502705 us`, before
CDC, request capture, response delivery, BRAM-read and completion setup costs.
Average line service is not enough: the next design must meet this real bursty
schedule, prime the first lines and account for blank intervals and margins.

## Compact column backing and exact chroma reuse

Use a descriptor-relative compact layout, not assigned physical addresses:

```text
Y byte offset  = x       * 480 + y
Cb byte offset = floor(x/2) * 240 + floor(y/2)
Cr byte offset = floor(x/2) * 240 + floor(y/2)
```

The planes have independent region descriptors. These expressions describe
layout only; they do not select SDRAM banks or establish installed capacity.
Y columns are 480 bytes and chroma columns 240 bytes, both divisible by the
16-byte BL8 payload. Full columns therefore need no padding in this profile.

For landscape column x, the native renderer needs chroma column `cx=x/2` and,
only on odd x, `min(cx+1,359)`. While y traverses 0..479 it needs rows `cy=y/2`
and, only on odd y, `min(cy+1,239)`. Keep two full adjacent columns of each chroma
plane: `2 columns * 2 planes * 240 bytes = 960 logical bytes`.

Each chroma column can then be fetched once per panel refresh. Across four
portrait lines the reuse pattern is:

```text
x=2k:   use k;       k+1 must be ready for the following odd line
x=2k+1: use k,k+1;   retain both through that line's last consumer
x=2k+2: use k+1;     retire k, fill its slot with k+2
x=2k+3: use k+1,k+2
```

Two slots are sufficient if filling the retired slot completes before that
next odd line. A third column per plane increases logical cache size to 1,440
bytes and permits earlier prefetch/extra arbitration slack; it does not remove
the need to prove deadlines. Prime the initial columns explicitly. At x=719,
right replication uses column359 rather than fetching column360.

Inside each column, rolling current/next-row registers avoid rereading four
neighbors from cache for every pixel. At most four Cb/Cr pairs are held for the
two columns/two rows: eight bytes. After two output y values, shift the row
window and fetch the next row. At y=479 replicate row239, with no row240 read.
Cache port counts, fill/read conflicts, actual BRAM allocation, burst response
staging and any Y FIFO are still implementation choices. The retained two RGB
line banks themselves hold 1,920 logical bytes and can still terminate the
memory-domain renderer; direct YUV need not put arithmetic on the pixel-clock
critical path.

Preserve the native **horizontal half-up first, vertical half-up second** order
even though physical traversal advances y first. Averaging vertically first is
not equivalent on ties. Center chroma after interpolation, then use the exact
signed-floor full-range conversion/clamp/RGB565 truncation in the sealed kernel.
Each accepted kernel token carries its complete internal owner identity and
actual x/y/geometry. Reversing traversal never changes those coordinates.

Without reuse, requesting all four Cb/Cr neighbors per pixel offers nine useful
bytes/pixel including Y: about 202.413 MB/s at this panel refresh, before bus
overhead. Even exploiting parity but no sample reuse averages 5.5 bytes/pixel.
A one-pixel/cycle converter alone does not solve those access patterns.

## Keep conversion in the core clock and retain the LCD banks

The simpler direct-YUV seam is a **core100MHz column renderer feeding the
existing 480-word RGB565 LCD banks**. A portrait line request identifies a
landscape column and owner. Fetch its480 Y bytes (240 memory words,30BL8s),
ensure the needed cached chroma columns are ready, run480 exact pixel
conversions, and fill the selected RGB line bank. Publish that bank's completion
toggle only after all480 words and its correct generation are resident. The
pixel-clock side then scans the same synchronous RGB BRAM outputs as before.
No new color arithmetic latency enters the panel or ESP32-overlay pixel path.

One new chroma column is240 bytes per plane:240 memory words total, another
30BL8s, normally once per two portrait columns. The initial two-column prime
is60BL8s; priming/refill scheduling must be explicit. Either stage a complete
Y column or feed a bounded Y FIFO while conversion proceeds. Chroma prefetch,
Y fetch and conversion can overlap only with demonstrated cache ports, queue
capacity, bank ownership and downstream readiness. Sequential costs below are
illustrations, not a promise that overlap exists.

The current owned-read seam reserves one complete128-bit response slot before
issuing a physical BL8. That slot captures all eight nonstallable beats and can
remain held afterward. It is not a multi-request prefetch queue: if a converter
holds its response while waiting for chroma or a cache-port conflict, no next
burst may issue. Avoid a circular wait in which the only occupied Y response
slot prevents the chroma read needed to consume Y. Prime chroma first, or copy
an entire accepted Y response into separately reserved bounded storage before
asking for chroma; prove the reservation and drain rules. Measure issue-to-
response-consumption gaps rather than multiplying raw SDRAM data-pin bandwidth.
Changing to multiple outstanding slots would be a separate owned-read service
design, not an assumed property of this alternative.

## Traffic comparison

All figures below are decimal MB/s of useful payload, for full 720x480 and 30
new frames/s. They exclude command/refresh/turnaround, partial bursts, ownership
metadata and compressed ingress. The original RGB baseline also excludes HUD.

| Operation | RGB backbuffer path | Direct YUV front |
| --- | ---: | ---: |
| New compact YUV writes at30fps |15.552|15.552|
| One YUV read for RGB rendering at30fps |15.552|0|
| New RGB565 backbuffer writes at30fps |20.736|0|
| Repeated panel scan reads |44.981 RGB|33.735 YUV|
| KEY/no-overlay total |**96.821**|**49.287**|
| Plus one complete compact P predictor read per new frame |112.373|64.839|

The direct scan reads 345,600 Y bytes + 172,800 Cb/Cr bytes each refresh:
21,600 Y BL8 bursts +10,800 chroma BL8 bursts =32,400 bursts/refresh. The retained
RGB scan is43,200 bursts/refresh. New YUV writes are another32,400 bursts per new
frame; these counts assume full useful BL8s and no rereads.

Conversion work increases from10.368 million RGB pixels/s at30 rendered frames
to22.490 million pixels/s at65.076 panel refreshes. The isolated elastic kernel
has simulated initiation interval1, but no integrated routed clock, cache ports,
concurrency or line deadline has been qualified.

As a strictly conditional service illustration, the retained model's ideal
15-core-cycle row-hit BL8 read cost gives450 cycles for one Y column. Fetching
one new Cb/Cr column pair costs another450 cycles every two portrait lines;
the average is675 read cycles/line. Adding480 sequential converter cycles gives
1,155 cycles/line; a line carrying that entire chroma refill is1,380 cycles.
At nominal100MHz those are11.55/13.80us, but they exclude row changes, refresh,
turnaround, writer/reference contention, response/control overhead and CDC.
They are arithmetic illustrations, not achieved service or timing bounds.
The existing strict-priority starvation counterexample must not be hidden by
average byte estimates. YUV fetches that now feed the LCD need an explicit
deadline class, rather than inheriting a best-effort background-read priority.

## Separate validated RGB overlay surfaces

HP01/HR01 produce opaque RGB565 rectangles after native validation. Preserve
up to four nonoverlapping rectangle descriptors and separately owned immutable
expanded surfaces. A column's rectangle membership/vertical intervals can be
computed from those descriptors; a full-canvas per-pixel mask is unnecessary.
Do not assume encoded row RLE/palette bytes are efficient random column reads:
decode and validate once into a bounded transposed surface before publication.
Retain unused-palette, token/row, overlap, bounds and CRC checks from native code.

Composite these RGB words **after** base conversion, with no alpha/filtering.
Patches never enter YUV predictor samples or the canonical tag. A frame's YUV
and patch descriptor set must publish together, including an explicitly empty
patch set; stale patches must not survive into another frame.

For A patched pixels per new frame, expanded-surface traffic adds at least:

```text
patch writes:       2*A*30 bytes/s
patch scan reads:   2*A*65.0761738 bytes/s
total:              2*A*(95.0761738) bytes/s
```

At10% canvas coverage this is6.572 MB/s, and at100% it is65.717 MB/s. With base
YUV reads unconditionally retained, the latter raises direct KEY useful traffic
to115.004 MB/s. These are not an apples-to-apples HUD crossover against the
96.821 number: that baseline excludes HUD acquisition/composition traffic too.
An optimized opaque compositor may suppress some covered Y reads, while chroma
needed by neighboring uncovered pixels must remain available. That optimization
requires a separately tested fetch policy; no suppression savings are assumed.

Patch columns also need BL8 alignment accounting. Padding RGB patch-column
stride to eight pixels can add up to seven unused words/column; a one-row-high
rectangle can cost eight times its useful bytes. Unaligned gather/merge can
avoid some padding but creates partial/extra bursts. A bounded patch cache and
exact rectangle geometry, not just total area A, belong in the simulation load.

## Canonical hash tee through a sixteen-row transpose store

The current source already presents Y, then Cb, then Cr in plane-local **row**
order. Canonical SHA hashes `<HH` dimensions then each uint8 sample followed by
zero. The compact backing stores only the uint8 value.

Accept each ordered sample exactly once into both SHA and the private transpose
buffer, with a joint ready/valid event and plane/x/y/owner checks. Neither path
may accept twice or advance independently under backpressure. Once sixteen rows
are available, flush sixteen-byte columns to the column-major destination as
full BL8 payloads. Retain SHA's original order; do not hash transpose drain order
or padding. SHA completion may precede final SDRAM drain, so publication still
joins both fences and all frame/patch validation.

At720x480, one Y transpose stripe is720*16=11,520 bytes; double buffering for
fill/drain overlap is23,040 logical bytes. Chroma stripes are360*16=5,760 bytes
each; reuse the maximum-sized storage sequentially across planes instead of
assuming three independent simultaneous stripe pairs. Current raster stripes
are eight rows deep; sharing/reusing those memories would be a new ownership
and address proof, not automatic free capacity. Logical bytes are not a routed
BRAM allocation or a claim that the integrated design fits.

For other legal native dimensions, H or H/2 may not be a multiple of16.
Descriptor strides, final partial stripes and aligned masked groups need explicit
handling. Padding is outside valid samples and outside the canonical hash. The
34x18 native case is a useful mandatory counterexample to assuming divisibility.

Column-major is preferable for the first seam because complete scan columns
are contiguous. A16x16 tile-transposed layout can also provide sixteen-byte
column fragments but jumps between tiles along the scan, potentially increasing
row changes. An8-row chroma tile gives only eight bytes/column, coupling pairs
inside a BL8: retaining both fetched columns across a k,k+1 boundary may need
a third full-column cache slot or incur rereads. A full sixteen-landscape-column
YUV strip cache would be11,520 bytes (Y7680+Cb/Cr3840), trading more BRAM for
tile-friendly bursts. Byte totals alone do not choose among these layouts.

## Front/reference ownership and atomic publication

A direct front holds immutable YUV **and** overlay descriptors/surfaces for the
entire refresh, including prefetched data, held burst responses, line banks and
kernel tokens. Full owner/epoch/frame/read-sequence metadata follows each read
and output. Caches are keyed by region/generation plus plane/column; neither a
physical address match nor a reused logical bank number proves identity.

Only a fully validated, physically drained candidate may become pending front.
Apply the descriptor switch at the LCD frame boundary. Drain or explicitly
quarantine all old read/cache/line-bank leases before permitting their backing
to be overwritten. Flush or epoch-check prefetched old lines so they cannot
contaminate the new frame; cache warm-up must meet the first new line deadline.
Old front survives any incomplete candidate, bad tag, invalid patch or timeout.
No timeout or ACK fabricates physical write/read completion.

For stored KEY/promoted P, a display front may share an immutable reference
region under an additional read lease. This can avoid a duplicate backing copy,
but prevents replacing that physical region while display readers remain. It
does not remove the need for private destination backing and atomic logical
reference remapping; two published banks plus a provisional destination can
still require three physical YUV regions.

No-store P (`destination=255`) does not create a reference, but direct scanout
still needs its reconstructed YUV retained in a display-owned region across
repeated refreshes. It cannot overwrite a predictor or be released when decode
or AF03 finishes. A newer no-store P needs a separate unpublished destination
until swap and old-reader retirement. Thus direct scanout changes backing roles;
it does not eliminate display front/back lifetime requirements. No physical
region count/capacity/bank assignment is accepted by this study.

## Smallest useful next simulation seam

First test a **static, initialized compact column-major front** through the real
owned BL8 read service, bounded Y/chroma caches, exact parameterized RGB kernel,
and retained alternating RGB line banks/preset0 schedule. Do not add a full
RGB SDRAM backbuffer, decoder, new bank map or network. Use synthetic, explicitly
bounds-checked region descriptors. Begin without patches; add one then four
separately prevalidated opaque patch surfaces as a second case.

Required observations:

- Compare every canvas pixel and black margin against the actual pinned native
  `render565` plus native patch output, including34x18, all parity/edge/tie cases,
  and a full720x480 moving/front-generation pair. Host snapshots alone are not
  a renderer oracle.
- Count exact physical BL8 reads, rereads, cache occupancy, useful/padded bytes,
  first-line priming, every line's request-to-completion and deadline slack,
  underflows and held-response occupancy. Include actual541x834 timing, margin
  parity and repeated panel refreshes of one held frame.
- Add bounded background writes and one predictor-read load with real refresh,
  row transitions and turnaround. Preserve starvation/deadline counterexamples;
  average service cannot mask a failed line.
- Exercise wrong high owner bits, stale responses, cache generation changes,
  reset/abort during issued nonstallable bursts, and frame-boundary switching
  with old responses/line banks outstanding. No lease reuse before actual drain.

Separately prove the sixteen-row row-order-to-column-store tee against exact
canonical SHA and physical readback, including partial geometry. Only then join
stored frames to the scan seam and measure concurrent initiation interval and
unique presentations. This is a smaller architectural decision test than a full
RGB renderer, while keeping its reference-memory and recovery obligations honest.
Any later board implementation also needs restored SDRAM clock/I/O/CDC/reset
and routed timing qualification. The AKD1 inactive-SDRAM lab establishes none of
those active-memory gates.
