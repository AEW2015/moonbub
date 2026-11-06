# Exact two-row chroma cache for V91k RGB565

`canonical_rgb565_cached` preserves the frozen V91k RGB565 word contract while
reusing chroma samples locally. The input remains 518,400 bytes of planar raster
YUV420: Y 720×480, Cb 360×240, Cr 360×240. The output remains 345,600 RGB565 words
with frame epoch and raster pixel identity. It is provisional base conversion;
HUD/content validation and atomic publication are later gates.

## Local storage and read timing

Four `180×16` payload arrays hold two chroma row slots, split by column parity.
Each word pairs Cb in bits 7:0 and Cr in bits 15:8. Total chroma payload is exactly
**1,440 bytes**, plus row tags, valid bits, four registered RAM words, arithmetic
registers and control. Payload is not reset or initialized in bulk.

Each bank has one registered read in `always_ff`. State 6 `LOOKUP_REQ` issues the
four reads, state 7 `LOOKUP_WAIT` consumes their registered results, state 8
`CONVERT` registers exact RGB565 arithmetic, and state 9 `EMIT` holds its output
until accepted. The RAM response is not modeled as a zero-cycle combinational
lookup. Opposite horizontal neighbors use opposite parity banks; top/bottom
rows use different row slots. At the right edge the same last sample is
selected twice. At the bottom edge top and bottom select row 239.

This structure is a logical port/banking design. Verilator simulation does not
prove RAM inference, BRAM/LUT/DSP allocation, achieved clock, placement or
routing on the Game Bub FPGA. Exact 7-series mapping remains a later gate.

## External schedule and validity

The row slot is `row & 1`. Before the first luma sample, fill row 0 and row 1;
within each row, read all 360 Cb bytes followed by all 360 Cr bytes. Only the
last acknowledged Cr byte commits the row tag and valid bit. A reused slot is
invalidated before the first byte of its replacement fill.

At each luma row, state 1 checks that top=`y//2` and bottom=`min(y//2+1,239)` are
present under their expected tags. Odd luma rows reuse their existing pair.
As the pair advances, retain the old bottom and fill only the newly needed
bottom. Rows 238/239 serve y 476/477; y 478/479 alias row 239 and require no new
fill. Every chroma byte is fetched once. Each pixel separately reads its Y byte,
then performs the registered local lookup and conversion.

For a successful full frame the required counters are:

| Counter | Value |
|---|---:|
| Accepted/acknowledged external reads | 518,400 |
| Luma reads | 345,600 |
| Chroma reads | 172,800 |
| Completed paired-chroma rows | 240 |
| Local lookups/cache-served pixels | 345,600 |
| Accepted RGB565 output words | 345,600 |

The frozen uncached converter reads 3,110,400 bytes per frame. The cache therefore
targets sixfold fewer external reads; measured cycle and resource results must
be reported separately from that count. Fill checks, registered local reads,
arithmetic, finite external service and held output all contribute cycles.
The initial 1,440-byte chroma preload delays the first RGB word compared with
the uncached control. Report that startup fence separately from complete-frame
service; a full-frame cycle reduction must not hide the initial preload.

## Arithmetic

The two interpolation rounding points are unchanged: horizontal rounded mean
on odd x, then vertical rounded mean on odd y, with edge replication. Chroma
is centered by subtracting 128. Conversion uses the same signed fixed integer
coefficients, arithmetic floor shifts, clamp and RGB565 truncation as V91k.
Luma enters arithmetic as a signed integer to preserve negative-shift context.
Changing local read reuse changes neither quantization nor encoded wire bytes.

## Physical owner and cancellation

The external byte bus has one accepted pending owner, tagged by frame epoch.
Its pending register has FPGA configuration INIT zero. Synchronous `reset`
and `cancel` invalidate row tags and provisional computation, but retain an
accepted physical read until a matching response drains. Replacement is blocked
while draining. No canceled fill can set a row valid or update payload.

An unexpected response epoch fails the active conversion but cannot release
the real owner. Its later matching response still drains. A matching bus-error
response releases the physical request and fails conversion. Error 1 is response
epoch mismatch, 2 is bus error, 3 is zero start epoch, 4 is an internal state/row
ownership inconsistency. Sticky errors clear on an accepted new start.

Output words/metadata and offered request fields remain stable under legal
backpressure. A row may be used only after both component fills complete and
its tag matches the current top/bottom demand. Any prior emitted RGB words on
a later failure remain provisional; `done` is complete accepted output drain,
not validated frame publication.

## Debug contract

State 0=IDLE, 1=CHECK_ROWS, 2=FILL_REQ, 3=FILL_WAIT, 4=LUMA_REQ, 5=LUMA_WAIT,
6=LOOKUP_REQ, 7=LOOKUP_WAIT, 8=CONVERT, 9=EMIT. `row_valid`/`row_tag` expose row
ownership; `fill_row`, `fill_slot`, `fill_plane` and `fill_column` expose the
accepted-fill schedule. `fill_plane=0` is Cb and 1 is Cr. `lookup_launch` and
`lookup_response` expose the registered local read boundary. `dbg_pending`
reports the physical external owner, independent of warm-reset local activity.

No RTL simulation here establishes hardware 30 fps, complete validated decoding
under 10 ms, monolithic shared-memory service, transport or display scanout.
