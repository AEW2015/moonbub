# CU66 v73 — banked strip and reference row service

## Objective

Evaluate the CU66 720×480 reference-read path using an eight-bank 720×16 strip
store. Its storage is 8×720×16 bits = 92,160 bits = 11,520 bytes, equal to a
720×128-bit store. The decoder-facing reference response remains one 8×8 tile
(64 bytes), while memory fetches are organized as eight row requests per tile.
Each row request returns the four logical x16 words in the selected half of a
BL8, reducing the request count from 32 scalar-word requests to eight row
requests per tile.

The prototype compares the frozen v72 scalar request shape with a v73 row-wide
shape and a one-entry versus eight-entry round-robin physical BL8 tag cache.
The cache tags are `address >> 3`; an eight-word BL8 is 16 bytes. Writes must
invalidate every matching physical BL8 tag, including partial-byte writes.
The RTL implementation and write invalidation are qualified separately. The
Python trace measures synthetic locality, not RTL behavior or timing.

## Frozen contract

- Keep CU66 dimensions, packet syntax, tile identity, SDRAM controller/model,
  exact output and ownership semantics unchanged. Preserve every v72 file; new
  painter banking, memory interfaces and system integration live in v73 paths.
- Keep the existing canonical map: x16 word base `0x080000`, Y/U/V offsets
  0/172800/216000 words, Y pitch 360 words, and chroma pitch 180 words.
- Iterate the synthetic raster tile set: Y is 90×60 = 5,400 tiles, U and V
  are each 45×30 = 1,350 tiles, for 8,100 total. Tile `i`, row `r` starts at
  `planeBase + (i // width) * 8 * pitch + (i % width) * 4 + r * pitch`.
- The selected row words begin at address low bits 0 or 4, and are the four
  consecutive logical words in that half. This matters for chroma's odd
  180-word pitch, which alternates half placement between rows.
- Compare v72's 32 scalar requests/tile with v73's eight four-word row
  requests/tile. Cache misses fetch one BL8 burst containing eight x16 beats; useful payload is
  still 64 bytes/tile. Overfetch counts physical returned bytes minus useful
  bytes.

## Evidence and limitations

`scripts/cu66-v73/verify_baseline.py` checks that commit
`41d070476c074e8caa1ccabe7ae745ba61707717` is an ancestor of the checkout,
rechecks the exact v69/v70/v71/v72 frozen manifest hashes (4,879/460/122/131
files), and invokes the prior v72 baseline verifier. The v73 script does not
rewrite those bundles.

`scripts/cu66-v73/reference_traffic.py` is a standard-library-only synthetic
all-tiles raster trace with address-bound checks, selected-word checks,
chroma half-placement checks, cache comparisons, and adjacent-tile self-checks.
It is not the observed CU66 P-request set (7,806 tiles), a frame-rate result,
RTL verification, or proof on a live target. The result JSON and its log record
source hashes and assumptions. The v72 full-strip record is the frozen comparison baseline. Native and
translated painter tests, actual-command memory tests and v73 full-system runs
provide the new implementation evidence in [the handoff](hardware-handoff.md).

The first trace covers 8,100 tiles (64,800 row requests and 259,200 useful
x16 words). `word_requests` means API calls: scalar-word calls for v72 and
four-word row calls for v73. Each cache miss causes one BL8 read burst, which
returns eight physical x16 beats (16 wire bytes). The v72 scalar/cache1 shape
records 259,200 API calls, 64,800 read bursts / 518,400 physical beats,
1,036,800 wire bytes, 518,400 useful bytes, and 518,400 overfetch bytes. The
v73 row-wide/cache8 shape records 64,800 API calls, 32,640 read bursts /
261,120 physical beats, 522,240 wire bytes, the same 518,400 useful bytes,
and 3,840 overfetch bytes. These counts are for the stated raster ordering and this
synthetic round-robin tag model; the trace shows a fourfold request-count
reduction and fewer misses, not cycle timing or target throughput. In the
focused adjacent Y tile pair, the row-wide/cache8 model gets 8 misses and 8
hits; scalar/cache1 gets 16 misses across the 64 word requests (and 48 hits
within each fetched BL8).

The Python prototype does not build HDL. Separate RTL/controller/model tests
and unplaced family mapping qualify the stated implementation scopes.

## Evidence audit gate

`scripts/cu66-v73/verify_evidence.py` is a read-only standard-library gate. It
rechecks the v69–v72 frozen baseline, every recorded source and log hash,
expected native painter and memory adapter run counts, translated/generic and
unplaced family-map outputs, the 43-member superseded archive, and the system
frame/cache comparison. System results must retain a complete record for each
source frame, zero LCD underruns, and explicit limits on target timing and
physical cadence. The synthetic traffic report is checked independently and
must remain labeled as a model, not a live-target result.

The gate reports missing producer outputs as pending evidence. Its PASS status
requires the cache-width ablation, four-frame history, and exact-output
comparison artifacts in addition to the current two-frame system trace. A
gate failure during an active producer run therefore identifies the missing or
stale artifact; it does not imply that frozen v69–v72 files were changed.

## Completed iteration and next measured work

The stated prototype and simulation campaign are complete: [results and limits](hardware-handoff.md). Matched P transaction 148.51433→129.16555 ms; four-frame history exact with zero LCD underruns; unplaced strip allocation 48→8 in 18K equivalents. The next priorities are tile-major canonical storage and direct-YUV display caching, with end-to-end memory service measured before choosing either. All original 30-fps and under-10-ms target gates remain open.
