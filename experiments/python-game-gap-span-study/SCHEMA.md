# `gamebub-gap-span-v22`

`source_sha256` maps repository-relative files to SHA256, including retained v21
input result/objects, all imported frozen codec dependencies and this component's
helpers, tests and documentation. `cases` keeps all five132-update sequences with
per-frame/per-patch costs. `hc21_bytes` is the exact frozen existing sidecar size;
`proposed_same_overhead_bytes` is83 plus the new selected patch sizes, a new-profile
projection rather than an existing HC21 packet.

Per-patch records retain full/HD21/HD22 candidate sizes and modes, selected formats,
span counts, merged zero words, actual source-vs-confirmed changed words, measured
old/new encode and selected decode times and the HD22 packet SHA256. Case summaries
separate pure candidate-byte reductions from final full-fallback reductions. Timings
pay actual codec calls but exclude fixture acquisition/conversion/oracle/export.

`goldens` bind selected actual HD22 bytes and original/reference `<u2` words to a
case/frame/patch/shape. Blob descriptors provide bounded safe relative paths,
stored/raw SHA256 and exact raw lengths. The wire header is `<4sBBHHI16s16s` plus
finalCRC32. RAW=0,COPY=1,SPAN_XOR=2. A SPAN_XOR payload begins with a little-endian
u16 record count and has ordered `<HHH` row/start/word-count records followed by
that many little-endian XOR words. Interior zeros are permitted only in gaps of
one or two words; endpoints must be nonzero and records separated by at least
three zero positions. Geometry/content tags match the HD21 convention.
