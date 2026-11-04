# `gamebub-ar03-exact-traces-v1`

`results.json` contains relative source hash pins, native media hash/PTS metadata,
cohorts, aggregate counts and explicit model limits. Each ordered cohort starts
from empty banks at epoch18. Requests are `force_key`/`promote` flags. Each row
retains source RGB888/scale map, complete AR03 bytes, ordered GF02 datagrams,
expected AF03, pre/post canonical reference banks, private decoded YUV planes,
final RGB565 output, hashes and a compressed exact trace JSON object.

Objects have relative path, encoding (`raw`/`zlib`), raw byte length, raw SHA-256
and stored SHA-256. Paths may not be absolute or contain `..`. Array descriptors
add C-order shape and canonical dtype (`|u1`,`<u2`,`<i2`) around a blob. Wire bytes
are raw binary; zlib is fixture packaging only. Hash stored bytes before decode,
then verify raw length/hash. Reference tags are independently recomputed from
`<HH width,height>` and concatenated C-order little-endian int16 Y/Cb/Cr arrays.

## `ar03-exact-entropy-trace-v1`

The trace identifies AR03 epoch/frame/dimensions/reference, selected inner format,
full packet size/hash and selected UI pixels. For each plane:

- `packet_payload_offset` is the start of the selected GM CP02 or SR SP01 bytes
  in the complete AR03 packet, including the 61-byte AR03 header and GM/SR header/map.
- `selected_entropy` describes RAW/Rice CP02 layout, or SR dense/split map/DC/full
  layout. All ranges are half-open bytes. Headers/parameters and CRC are separate.
- `stripes` group block-raster coefficient records by one eight-row block row.
  `y`/`rows` crop partial plane edges. Zero/DC/general counts come from independently
  decoded blocks and sum to `block_count`.

For GM CP02, each block's `dc_bits` and `ac_bits` are half-open logical bit cursors
relative to their coded bit streams, excluding Rice parameter bytes. Add the
record's `dc_bit_base` or `ac_bit_base` to obtain CP02-relative bit positions.
`dc_read_range`/`ac_read_range` are newly refilled whole-byte ranges; they may be
empty if earlier bounded lookahead already supplied the needed bits. Add the
plane `packet_payload_offset` for complete-packet byte offsets. RAW blocks use
`raw_range` instead and consume128 bytes per block.

SR dense adds `cp02_base` to CP02-relative ranges. SR split output records contain
one mode-bit pair and newly read mode-byte range, optional signed DC value range,
or `compact_cp02` child plus `compact_cp02_base`. Mode/DC ranges are SP01-relative.
A full block's child cursors refer to the compact CP02 stream; add both the compact
base and plane payload offset to obtain complete-packet positions. Child block ID
is compact-stream order; parent block ID is spatial output order. Do not treat a
compact CP02 row width1 as the original spatial width.

`stripe-demand.json` is a separately result/analyzer-hash-bound untimed aggregate
of selected-payload refill ranges, conserving exact bytes over every plane. It
excludes header/parameter/CRC and separate preflight rescans equally from exact
and uniform comparisons. It is not a physical memory burst schedule.
