# `gamebub-inline-generated-reconstruction-v1`

`results.json` contains relative source/object SHA-256 pins, exact generated-tile
frame proofs, five conditional service cases, and scope boundaries. `frames` has
16 decisions; `counts` totals 97,308 blocks, 6,227,712 residual samples, 6,224,472
reconstructed samples, 12,449,008 diagnostic canonical bytes and 253,440 selected UI
words. Twelve native decisions reuse six acquisitions; four flat controls do not
represent gameplay FPS.

A frame binds cohort/id, AR03 SHA-256, dimensions, KEY/publication eligibility,
private/canonical/publication tags, residual/reconstruction/tile counts, plane YUV
and display RGB565 hashes, tagger ndarray allocation, and exact stripe completion
records. It references a content-addressed compressed `IT20` stream with raw byte
count/SHA and stored SHA. No source-plane or completed-output-plane traversal is
used as tag input. `publication_tag_hex` is null for ordinary P decisions.

## IT20 golden stream, little endian

This is a test artifact, not a network wire protocol. Its AR03 epoch/frame/body
binding and expected tag/publication permissions are supplied by the JSON manifest.

Header is Python `struct '<4sBHHII'`, 17 bytes:

| Field | Bytes | Value |
| --- | ---: | --- |
| Magic | 4 | ASCII `IT20` |
| Version | 1 | 1 |
| Coded width | 2 | unsigned little endian |
| Coded height | 2 | unsigned little endian |
| Tile record count | 4 | unsigned little endian |
| Following payload length | 4 | includes each tile prefix and its samples |

Each record prefix is `struct '<BHHBB'`, seven bytes: plane (0 Y, 1 Cb, 2 Cr),
y, x, valid row count and valid column count. Coordinates are plane-local. This is
followed by `rows*columns` uint8 samples in tile raster order. Tiles follow Y/Cb/Cr
plane order, then y stripes at multiples of eight, then x blocks at multiples of
eight. The last tile in a row/plane crops to valid dimensions. Chroma shapes are
(height/2,width/2). Each block contributes one record even when its inverse is zero/DC.
No trailing bytes or extra records are allowed.

The tagger collects one compact stripe and hashes complete rows in raster order.
Canonical tag input is `<HH` coded width,height followed by each valid sample as
**little-endian signed int16 with value 0…255**. Thus sample 255 emits `ff 00`, not
`ff ff`. There is no interplane header, UI patch, padded block data, epoch or frame
ID inside this canonical stream. SHA-256 is truncated to its first 16 digest bytes;
the receiver controller binds that tag to AR03/AF03 identity separately.

## Conditional service records

Each schedule stores frozen v19 `Budget`, inline hash/copy/expansion/state planning
parameters, serial baseline and inline completion, eliminated physical bank rereads,
canonical hashed bytes, SHA-256 padded compression service bytes/finalization,
explicit backpressure and local allocations. Both serial and inline profiles pay
the same final padding service before their digest is ready. Hash/expansion
service rates match across baseline and proposed designs. Stripes retain entropy,
consumer, prediction, inverse, compact-write, hash and joint-release instants.
No coefficient stripe is reused before its prior joint release.

`reference_tag_ready_ms`, `bank_publication_earliest_ms` and `rgb_display_ready_ms`
are separate. The first two are null for ordinary P decisions. The bank instant
also waits compact writes; real ownership/CRC/epoch publication remains a receiver
controller obligation. `analysis.json` binds the result/analyzer hashes and matched
service summaries. These are deterministic planning instants, not RTL/native cycles
or physical scanout timings. Python/fixture/export storage is not a local FPGA fit
proof; SHA/control state bytes are explicit assumptions.
