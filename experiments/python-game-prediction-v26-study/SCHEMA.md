# GM26 predictor component grammar

This is a standalone Python component, not a CP25-compatible base frame. The
little-endian header remains `<4sBBIIIHHBB16s16sIIIII>` (76 bytes): magic `GM26`,
version2, key flag0/1, epoch/frame/reference uint32 IDs, uint16 width/height,
uint8 block size16/32, uint8 vector limit18, 16-byte reference and output tags,
then uint32 exact lengths of quant-map, motion-map, Y/Cb/Cr payloads. Append CRC32
of the full preceding bytes. Identity/tag/plane bounds follow frozen GM25.

Each signed motion component is in **half a luma pixel**, bounded -18..18. Luma
interpolation denominator2; chroma denominator4. For a component q, use Python
floor division `i=q//d`, fractional numerator `f=q%d`, including negative q.
Sample the four taps at `(x+ix+ox,y+iy+oy)`, each coordinate separately clamped
to its plane edges. Weights per axis are `(d-f,f)`. Add `d*d//2` once to the
weighted sum, then floor-divide once by `d*d`. Thus half ties round upward.
Pixels use the vector of their destination macroblock; chroma block size is
half luma size, including cropped right/bottom blocks. There is no cross-block
vector interpolation. The executable evaluates four taps even at zero weight;
all four reference fetches per output sample are charged.

Key prediction is128 with empty motion map and absent reference identity/tag.
P motion map baseline modes are (compact modes4/5/6 follow below):

- 0: exactly one `<bb>` vector, uniform across all macroblocks.
- 1: raster dense `<bb>` vectors, exactly `mw*mh` pairs.
- 2: positive `<Hbb>` run length/vector records spanning exactly all blocks.
- 3: one default `<bb>` vector followed by `<Hbb>` absolute raster index/vector
  exceptions, strictly increasing and different from the default.

Uniform maps use mode0. Otherwise choose shortest bytes with tie priority
mode1,2,3,4,5,6. Sparse default is most frequent pair, lexicographically lowest on a
tie. Decoder repacking must exactly match transmitted bytes. Unknown modes,
nonminimal maps, vectors outside the domain, malformed or incomplete runs,
out-of-range and duplicate indices are errors.

Residual dispatch and arithmetic are **frozen GM25**: plane mode0 CP02 dense,
mode1 SP01 zero/DC/full, mode2 all-zero plane. Other modes reject. Quant-map,
Q14 forward/inverse transform, quantization, clipping, ROI protection and
optional encoder RDO are imported unchanged. The output tag binds the resulting
reconstruction, not the source. An exact supplied reference ID and tag are
required for P decode. This component has no HUD payload, transport, ACK,
publication/bank ownership, native memory allocation, or frame admission policy.

## Compact version2 additions

Current model emits/requires header version2. Version1 is preserved only in
`model_early_probe.py` and the early checkpoint. Version2 adds three map modes:

- 4: each raster vector's x then y component encoded as6 unsigned bits of
  `component+18`, MSB first. Codes37..63 reject. This is12bits/vector.
- 5: per-axis causal left prediction, reset to0 at each row's first vector.
- 6: per-axis median of left, top, top-right. Missing left and first-row top /
  top-right are0; at the right edge top-right equals top.

Modes5/6 start with one byte `kx`, then one byte `ky`, each0..6. The remaining
MSB-first bitstream encodes all raster x deltas followed immediately by all
raster y deltas, with no padding between axes. Delta is actual minus predicted
component. Map signed delta to `z=2*delta` for nonnegative values, otherwise
`z=-2*delta-1`; valid z is0..72. For `q=z>>k <7`, encode q one-bits, a zero-bit,
then k low bits of z. For q>=7, encode seven one-bits followed directly by7bits
of z (no terminating zero or remainder). Escape z with q<7 rejects as
noncanonical. Each reconstructed component must stay -18..18. Each axis uses
only current-row left and previous-row top/top-right vectors; no older history
is consulted. Full output MV storage is distinct from this causal scratch.

The final byte in modes4/5/6 has zero low padding bits. There must be fewer than
8 unused bits; nonzero padding, extra bytes, premature end, invalid k, illegal
escape or vector reconstruction reject. Encoder constructs **all seven k
streams per axis per predictor**, chooses lowest bit length with lowest k tie,
then concatenates those two chosen axis streams. The decoder's canonical
repack check includes that k choice.

Uniform maps still shortcut to mode0. For other maps the actual byte minimum
has tie priority1 dense,2 RLE,3 sparse,4 packed,5 left Rice,6 median Rice. All six
representations and all28 axis/k streams are actually constructed and charged;
work reports the candidate lengths, selected mode, Rice axis/value trial counts
and whole pack wall time. This Python encoder and diagnostic canonical decoder
are executable models; they do not establish native allocations or timing.
