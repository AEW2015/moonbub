# GM27 / CP27 / JA27 schema

All fixed integers are little endian. This is a distinct experimental profile;
frozen GM26, GE26, CP26 and earlier parsers are unchanged.

## GM27 frame

Header `<4sBBIIIHHBB16s16sIIIII>` is 76 bytes: magic `GM27`, version1, key
flag0/1, epoch/frame/reference uint32 IDs, uint16 width/height, uint8 macroblock
size16/32, uint8 vector limit18, 16-byte reconstructed reference and output
tags, then uint32 exact quant-map, motion-map, Y, Cb and Cr payload lengths.
The declared payloads follow in that order, then CRC32 over all preceding
bytes; fixed header-plus-CRC cost is80 bytes. Geometry, quant-map grammar,
Q14 transform/quantization/inverse arithmetic, clipping and sample domains are
the frozen predictor/ROI rules. Each plane length is1..132N+256 for its padded
8x8 block countN; the complete frame is at most2,000,000 bytes. IDs exclude
`0xffffffff`. Frame references must precede the current frame.

Keys predict128, use reference ID `0xffffffff`, zero reference tag and empty
motion bytes. P frames require a nonzero reference tag, the exact supplied
reconstructed reference ID/content and a bounded map. Output tags are nonzero
and bind the final reconstructed YUV planes. Decoding an independent key
requires no supplied reference.

Each motion component is a signed half-luma-pixel coordinate in−18..18.
The destination macroblock selects its vector, with half-size chroma blocks.
Luma interpolation denominator is2 and chroma denominator is4. For componentq,
use floor division `i=q//d`, `f=q%d`, clamp each of the four source tap addresses
independently, multiply axis weights `(d-f,f)`, add `d*d//2` once, then divide
once by`d*d`. Negative components use the same floor rule. There is no floating
arithmetic or interpolation between neighboring motion vectors.

The motion payload uses the GM26/version2 modes and bit syntax:

- 0: exactly one `<bb>` vector for all blocks.
- 1: exactlyN raster `<bb>` pairs.
- 2: positive `<Hbb>` run-length/vector records covering exactlyN blocks.
- 3: default `<bb>` plus increasing `<Hbb>` index/vector exceptions, each
  different from the default and within the map.
- 4: raster x/y components encoded MSB-first as6-bit `component+18`; codes37..63
  reject.
- 5: causal left prediction, with missing left0.
- 6: median of left/top/top-right; missing first-row top/top-right and first-column
  left are0; right-edge top-right equals top.

Modes5/6 begin with byteskx,ky, each0..6. Encode all raster x deltas followed
immediately by all y deltas. A signed delta maps to nonnegativez as`2*v` for
v>=0 and`-2*v-1` otherwise; z<=72. Withq=z>>k, q<7 usesq one bits, a zero,
thenk remainder bits; q>=7 uses seven one bits then7 absolutez bits. Escapes
that could use the short spelling reject. Every reconstructed component stays
in−18..18. Modes4/5/6 have fewer than8 unused low zero bits; truncation, extra
bytes, nonzero padding, illegal Rice parameters/escapes, invalid runs/indices
or out-of-range vectors reject. Any map is at most1+2N bytes.

GM27 receive accepts syntactically valid bounded map spellings without
re-encoding to enforce the sender's minimum policy. Dense uniform maps,
adjacent equal RLE records, nonmodal sparse defaults and nonoptimal Ricek can
therefore be valid. Sender behavior remains frozen: uniform maps use mode0;
otherwise build modes1..6 and choose shortest bytes with that tie priority.
Sparse default is most frequent, lexicographically lowest on a tie. Both Rice
predictors construct all sevenk streams per axis, selecting shortest bits then
lowestk. This distinction is intentional and specific to GM27.

## Plane dispatch

Dispatch0 is the frozen CP02 complete coefficient packet, dispatch1 a frozen
SP01 dense-or-zero/DC/full packet, dispatch2 exactly one all-zero-plane byte.
Dispatch3 contains one complete EC26 packet. Unknown dispatches reject.
GM27 allows EC26 flags0 (block-major) and1 (raw fallback); flag2 frequency-major
rejects even though the separate EC26 research codec supports it.

EC26 header `<4sBBIHH4I3I>` stores magic`EC26`, version1, flags, block count,
blocks-per-row, reserved0, four stream lengths and three AC nonzero counts.
Its header plus CRC costs46 bytes. Coefficients are signed int16 within±2048;
blocks1..65536 have integral rows1..256 wide. Raw fallback is exactly128N
coefficient bytes, with lengths`[128N,0,0,0]` and all counts0.

For flags0, the DC stream starts with Ricek0..13 followed by signed-zigzag DC
row-reset differences, prefix15 escape14 bits. AC bands zigzag1..5,6..20,21..63
are each flattened in block-major order. Each stream starts with runk0..19 and
levelk0..11, then exactly its declared nonzero pairs. A run counts zeros since
the prior nonzero, with initial index−1 and cross-block runs. Run prefix15
escapes to24 bits. Level prefix15 escapes to12 bits and codes
`signed_zigzag(nonzero)-1`. Remaining coefficients are zero. Each of four
streams has its own exact byte extent and zero bit padding; bounds, canonical
escapes, counts, runs, coefficient domain, packet length and CRC are checked.

Entropy choice is sender policy. Before EC26 construction, the sender performs
the frozen GM26 original/pruned legacy plane comparison; ties retain the RDO
proposal. EC26 layout0 then wins only if dispatch-plus-packet bytes are strictly
smaller than that legacy winner. Neither the EC26 trial nor its byte size can
change the frozen selected coefficients.

## CP27 pair, unchanged HU25 and JA27

Pair header `<4sBBIIBBII16s16s>` is56 bytes: `CP27`, version1, flags, epoch,
frame, source/destination slots, exact base/HUD lengths, and SHA256-first16-byte
digests binding each complete inner packet. CRC32 follows both inners; binding
cost is60 bytes. Flags are0 (P ephemeral),2 (P publish),3 (independent key).
Key uses source255/destination0 and independent base/HUD. P source is0/1;
published destination is the other bank, ephemeral destination255. Canvas,
epoch/frame and key semantics must agree across the two inners. The complete
pair, including both inners and binding, must fit49,152 bytes.

HU25, HD25, exact RGB565 patch syntax, rectangle binding, last-accepted HUD
reference identity and tag remain frozen. At most four disjoint patches are
accepted. Base reference banks and HUD reference history are distinct.

JA27 header `<4sBII16s16s16s>` followed by CRC32 is65 bytes. It stores`JA27`,
version1, epoch/frame, digest of the complete pair, reconstructed base tag and
reconstructed HUD tag. Validation binds all five identities to the exact pair.
There is no unbound status-only ACK.

The receiver owns two reconstructed base banks and one last-accepted exact HUD.
Write-drain and vblank gates must both be true. Pair envelope checks and SHA
binding use base metadata without entropy decoding; this inspection stage does
not authorize publication. Full receive validates motion/quant/entropy syntax,
exact source-bank ID/tag, base output tag, full HUD content/reference tag and
monotonic presentation before constructing ACK and atomically publishing.
Every failure leaves banks, HUD history, frame ID and prior ACK unchanged.
