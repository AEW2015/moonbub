# HD25 laboratory grammar

Header `<4sBBHHI16s16s>`: magicHD25, version1, mode, width/height, payload length,
reference SHA256[:16], current SHA256[:16]. Tags hash `<HH>` geometry followed by
raster little-endian uint16 words. CRC32 covers header+payload. At most21,120
words, dimensions≤720×480, packet≤42,290 bytes and payload≤42,240 bytes.

Modes0/1/2 retain RAW/COPY/HD22-span semantics. Mode3 byte-plane RLE XORs the exact
reference. Modes6/7 code direct words or horizontal word-XOR without a reference.
Mode8 codes signed R5/G6/B5 deltas from the exact reference; mode9 independently
codes each component's left-neighbor differences, resetting the predictor at rows.
Independent modes0/6/7/9 use zero reference tag; temporal modes require exact hash.

Byte-plane streams have two uint32 lengths then low/high byte token streams.
Tokens0..127 carry1..128 literal bytes;128..191 mean1..64 zero bytes;192..255 mean
1..64 repeats of one following nonzero byte. Each plane must produce exactlyN
bytes without overflow or trailing encoded data.

Rice has header `<BBBIII>`: kR/kG/kB (0..5) and three exact bit counts, then byte-
padded MSB-first streams. ZigZag maps signed deltas; a code is q zero bits, one,
then k remainder bits. Decoder bounds values to the component delta range and
validates every reconstructed component instead of clipping. Padding must be zero.

Mode4 has int8 global dx/dy then residual grammar. Mode5 has `<BBBBH>` fixed16/8/
radius4/vector-field-mode/tilecount, uint32 vector-field length, vectors and residual.
Vector fields are two signed bytes per tile or `<Hbb>` canonical runs covering
every raster tile exactly once. Residual prefix0 selects HD22 spans (zero count
allowed),1 byte planes,2 component Rice. Motion is bounded to±4 and clamped to
same-patch edges. Residual Rice adds deltas to motion-predicted component values.

`results.json` retains source/dependency pins, actual candidate bytes/costs and
same-history old/no-motion/full selections. Portable golden objects are zlib
with raw/stored SHA256, exact length and shape. Synthetic translations/scene cuts
are separate from the132 reused native/control updates. Future83-byte cache
framing is counted but no new whole-video dispatch is claimed by this component.
