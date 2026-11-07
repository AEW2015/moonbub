# V95 read-only contract and resource audit

## Scope and status

This is a read-only contract/resource audit of the V91–V110 roadmap's V95 row,
E5 in the 2026-11-06 experiment plan, and the V82 native tile loader. It records
constraints for a bounded V95 implementation; it does not establish that the
codec, host search, decoder, RTL, or hardware path has been implemented or
qualified. V95 remains an optional research lane. V99 promotion requires a
qualified end-to-end winner and a supported fallback.

V82 defines canonical tiles as 64-byte 8×8 tiles in Y/U/V plane order, with
5,400 Y, 1,350 U, and 1,350 V tiles. Its masks distinguish same-reference
tiles, zero-coefficient tiles, hidden tiles, and visible zero-coefficient
copy-reference tiles. Preserve that distinction: hidden tiles are CONST128;
visible COPY/reference behavior is unchanged. Palette lookup applies only to
eligible canonical pixel tiles and must not redefine these masks or reference
history.

## Exactness boundary

The new codec maps exact 2-, 4-, or 8-entry palettes over canonical 8×8 Y, U, or
V **pixel** tiles. It does not palette DCT coefficients. An active mode-2 palette
tile supplies reconstructed pixels directly, so that tile bypasses IDCT and
reference reads. This can avoid transforms and reads while preserving exact
canonical pixels, content-root/HUD parity, and downstream RGB565 output, subject
to full-frame validation. It does not establish original-coefficient parity for
palette tiles. Coefficient fallback tiles remain exact to the existing decoded
coefficients and path.

Do not alter COPY or hidden-tile semantics. Palette tiles are not a new reference
alias mechanism, and palette state must never carry across planes or frames.

## Record grammar and bounded decoder obligations

Record kind assignments are:

| Kind | Meaning | Contract |
|---|---|---|
| 0 | Packed indices | Own palette; indices use the fixed-width index representation. |
| 1 | Top/left literal run | Own palette; run positions are literal palette indices. |
| 2 | Indexed escapes | Own palette; escaped pixel values are explicit literals. |
| 3 | RAW | 64 literal pixel bytes; clears previous-palette state. |
| 4 | Reuse previous palette | No palette entries; subkind selects packed, top/left-run, or indexed-escape coding and references palette ID 0. |

An own-palette record carries its kind and a count from 1 through 8, followed
by sorted, unique entries. For `count` entries, each palette index is `ceil(log2(count))` bits. In indexed
escape mode the escape index is `count`, so the index width is
`ceil(log2(count + 1))`; when that index occurs, it is followed by an 8-bit
literal pixel value. Thus an 8-entry palette uses a 4-bit index field and an
8-bit literal for an escaped pixel.

The prediction/run instruction uses its top two bits as the operation and its
low six bits as `length - 1`; exactly 64 output pixels must be produced.
Operation 0 copies the pixel eight positions above and is legal only at positions
at least 8. Operation 1 copies the pixel to the left and cannot cross a row
boundary. Operation 2 supplies literal indices, with unused padding bits zeroed
for the run. Operation 3 is rejected. Reject early termination, overproduction,
invalid palette indices, nonzero padding, invalid escapes, and malformed
subkinds.

A RAW record is a zero count followed by exactly 64 pixel bytes and clears the
previous-palette state. A reuse record has the reuse header, subkind 0/1/2 and
palette ID 0; it has no own palette. Reject reuse when there is no previous
palette. Keep history plane-local and frame-local. Encoder records skipped by
the decoder must not teach or change the cache. Reset history at each plane and
frame boundary.

The worst record is 138 bytes: a 2-byte kind/count header, 8 palette entries,
and 64 one-pixel literal runs. Each run costs a 1-byte instruction and a
1-byte packed index, for `2 + 8 + 64 × 2 = 138` bytes. Keep record-length
accounting consistent with the selected instruction form. There is no
per-record CRC: the outer CS95 CRC and semantic content root cover integrity.
Do not add an unpriced checksum.

## Plane framing and complete byte accounting

The big-endian plane wire layout includes, in order, `pal_count` (u32),
ascending palette entries `(tilepos u16, len u16, record)`,
`residual_blocks` (u32), `entropy_len` (u32), and the EC92 fallback stream. The
fallback stream must be re-encoded for the actual remaining coefficient blocks;
its cost cannot be estimated by subtracting the palette-covered blocks from a
previous stream. Charge all plane and frame metadata, directories, records,
residuals, entropy bytes, and outer framing/CRC in every comparison.

With no palette, the directory remains 12 bytes, matching the existing 12-byte
baseline. Palette entries add directory bytes and each selected record adds its
full serialized length. Select a profile using actual complete serialized cost,
including the 4-byte directory fields and the actual residual re-encoding cost.

The bounded host profiles are: no palette; P2 threshold 16; P4 threshold 24;
P8 threshold 40; E8 threshold 40; W8 threshold 64. Keep these names/thresholds
fixed for the comparison, and report the selected profile and full byte delta.

## Resource and evidence limits

The candidate canonical planes already exist as the baseline. The native
candidate writer should write palette pixels directly into the candidate image;
do not allocate an additional full-frame palette map. The narrow incremental
allowance is one 64-byte tile plus an 8-byte palette decoder/state allowance. It
excludes the bounded 138-byte packet-record buffer, the selected-position
bitmap, and the already-existing candidate planes. Report these as partial
increments against the actual candidate baseline, not a total storage/resource
bound or a demonstrated BRAM mapping. No RTL port, primitive inference, timing,
placement, routing, or fit claim follows from this audit.

Use the 457 retained sources for the initial bounded comparison, including
synthetic text, noise, and scene-pattern fixtures. This is one precompressed
walkthrough family plus synthetic patterns, not independent raw game captures.
Canonical target generation is predecoded, and transform/IDCT cost is
unmeasured. Record the maximum transforms avoided and the complete-byte delta;
work-score evidence is a proxy only. Gate reported gains with the stated byte
allowance under 5% or 15%, and report selected-palette frequency and worst-frame
change. Do not convert saved-transform counts or work score into an FPS,
30-fps, full-host-throughput, or hardware claim.

A V95 result can establish exact pixel/root/HUD parity for the tested canonical
inputs and a bounded software cost comparison. It cannot establish coefficient
parity on palette tiles, raw-capture quality, generalization beyond this corpus,
full host 30-fps operation, an RTL implementation, 7-series resource/port fit,
routed timing, hardware 30-fps throughput, or the complete under-10-ms decode
gate. Keep quality-changing palette clustering separate, negotiated, and
matched-quality as required by E5.

## Source basis

- `docs/gamebub-v91-v110-development-plan.md`: V95 stages and V99 promotion /
  fallback gates.
- `docs/literature-review-2026-11-06/experiments.md`: E5 exact-lane, corpus,
  full-cost, and separate clustering requirements.
- `experiments/python-gamebub-v82/native/data.py`: canonical 8×8 tile layout,
  plane counts, and reference/hidden mask semantics.
