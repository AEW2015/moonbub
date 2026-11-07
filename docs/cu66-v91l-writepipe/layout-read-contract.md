# V91l candidate layout and aligned-read workload comparison

This experiment extends the mapping and row-locality study in
`scripts/cu66-v79/layout_study.py` to the canonical Y/Cb/Cr planes, the live
v91l row-write fixture, and 16-byte logical converter reads. Regenerate the
result with:

```sh
python3 experiments/python-gamebub-v91l-writepipe/layout_reads.py
```

The script writes `experiments/python-gamebub-v91l-writepipe/layout-read-results.json`.
Its input paths and SHA-256 digests are retained in that result.

## Compared layouts and address rules

Each layout maps the same active canonical raster bytes. Plane dimensions are
Y 720x480, Cb 360x240 and Cr 360x240. Each plane starts at the previous
plane's allocated end. `raster` stores plane rows contiguously. `tile8x8`
orders complete 8x8 tiles and bytes within each tile in row-major order.
`micro16x8` orders complete 16x8 microtiles and bytes within each microtile in
row-major order. Luma dimensions divide evenly into both tile shapes; the
360-byte chroma rows pad to 368 bytes in the 16x8 layout, adding 3,840
inactive plane bytes total. Plane offsets are recomputed from allocated spans.
The 42,240-byte HUD region starts directly
after the complete canonical allocation, at 518,400 for raster/tile8x8 and
522,240 for micro16x8. The mapping checks prove plane address injectivity,
span containment, and right/bottom chroma edge bounds.

An SDRAM BL8 read is treated as one aligned 16-byte physical burst. For each
logical read request, the model maps every requested byte, aligns its physical
address down to 16 bytes, and issues the minimum distinct burst set. It
removes duplicate bursts only inside that one logical request; it does not
reuse fetched data across later requests. `overfetch_bytes` is physical read
payload minus useful logical bytes. The converter's bounded gather can process
one burst response in a 16-byte scratch register and assemble one 16-byte
logical output buffer, for 32 bytes of payload storage total. A 64-byte
reference-tile output uses the same scratch plus a 64-byte output buffer, for
80 bytes total. Tags and control registers are excluded.

## Workloads and provenance

- Candidate writes are the actual 140,160 packed rows in the qualified v91l
  SDRAM `native-rows.hex.gz` input, streamed in captured order. The script
  decodes each 160-bit row's byte address and logical bank, remaps canonical
  raster addresses through each layout, and rebases HUD addresses after that
  layout's canonical allocation. These are 8-byte writes, each represented as
  four x16 single-word writes. They are reported as write rows/word writes,
  never as BL8 read payload or read overfetch.
- Delta-reference reads are every `reference_request` event for `actual_006`,
  profile 0 in the qualified v91l rows trace. The trace contributes 7,806
  logical 64-byte tile requests (499,584 useful bytes). Every event is kept in
  its original order; there is no whole-frame deduplication. Bursts are
  deduplicated only within one tile request. The script independently scatters
  the prior accepted `actual_001` canonical planes through each mapping and
  proves each gathered reference tile equals its exact 64 source bytes.
- The converter read schedule is derived, rather than claimed as an actual
  address trace: it reads each complete canonical plane once, in plane order,
  as aligned 16-byte logical requests. That gives 21,600 Y lines and 5,400
  lines for each chroma plane, or 32,400 requests per frame. The schedule is
  source-backed by the qualified v91k aligned-line contract and converter
  sources, but the retained event trace records row fills rather than each
  read address. Two full captured canonical inputs, `actual_001` and
  `actual_006`, are used for byte-exact gather verification; corpus coverage
  remains two frames.

For every layout and both captured frames, all 32,400 derived logical reads
are gathered from a byte-addressed physical image constructed by scattering
the source canonical bytes through the candidate mapping. The reconstructed
logical bytes match exactly. Chroma edge containment is checked for both
360-wide planes. Every reference tile request is separately gathered and
compared byte for byte with the prior accepted canonical frame.

## Results

The machine-readable output reports these per-frame converter results:

| Layout | Allocation incl. HUD | Physical BL8 reads | Overfetch | Max bursts per 16-byte request | Gather payload bound |
| --- | ---: | ---: | ---: | ---: | ---: |
| Raster | 560,640 B | 32,400 | 0 B | 1 | 32 B total |
| Tile 8x8 | 560,640 B | 64,800 | 518,400 B | 2 | 32 B total |
| Micro 16x8 | 564,480 B | 37,920 | 88,320 B | 2 | 32 B total |

The reference phase has 7,806 logical tile requests for each layout. Its
physical read totals are 62,448 BL8 / 999,168 bytes for raster, 31,224 BL8 /
499,584 bytes for tile8x8, and 62,448 BL8 / 999,168 bytes for micro16x8.

The output also contains row-transition counts for an explicitly serialized
phase order: the actual two-bank native write fixture, then the one-frame
reference request trace, then one derived full-frame converter schedule.
Converter `logical_requests` stays at 32,400 even when one logical request
expands into multiple physical bursts. `row_activations`, conflicts and hits
count request-level row transitions; they are not controller command counts.
Row state is carried across these phases. A controller row is treated as 1,024
bytes under the v91l SDRAM address mapping. These are address-only transition
counts; they do not price time or concurrency.

## Limits

The phases are combined only to define a reproducible address order for row
transition counts. They do not model a joint arbiter, controller service
latency, refresh, bank overlap, or hardware bandwidth. The result is not an
FPS, deadline, or performance claim. Converter request addresses are a
source-backed full-frame schedule, not a captured 32,400-address trace. The
byte-exact checks cover two canonical corpus frames and the retained reference
tile events only.
