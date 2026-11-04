# GM25 laboratory frame grammar

The little-endian76-byte header `<4sBBIIIHHBB16s16sIIIII>` contains:

1. magic`GM25`, version1 and key flag0/1;
2. uint32 epoch, frame ID and reference ID (`0xffffffff` only for key reference);
3. uint16 width/height; uint8 motion-block size16/32 and vector limit8;
4. reference SHA256[:16] (zero for key), reconstructed SHA256[:16];
5. uint32 exact byte lengths for quantizer map, motion map, Y, Cb and Cr payloads.

The quantizer map uses the frozen16×16 ROI2-bit grammar. The motion map is empty
for a key. Otherwise it has one mode byte:0 global with one `(int8 dx,int8 dy)`;
1 dense with exactly one pair per raster macroblock;2 RLE with `<Hbb>` positive
run lengths and vector pairs;3 packed nibbles with one byte per block, high=dx,
low=dy, component=`2*nibble-8`, and codes9..15 invalid;4 sparse default packed
vector byte followed by `<HB>` strictly increasing absolute raster indices and
packed-vector exceptions. Each exception differs from the default; default is
the most frequent value, lowest value on a tie. RLE spans exactly all blocks with
no consecutive equal pairs. The complete motion representation matches minimum
actual byte count, global for uniform maps, otherwise tie order dense/RLE/nibble/
sparse. The complete motion representation must match canonical minimum
packing; vectors are even within−8..+8. Partial edge blocks are cropped normally.

Each residual plane starts with one dispatch byte:0 dense complete CP02,1
complete SP01 zero/DC/full plane,2 entirely zero coefficients with no following
bytes. Plane coefficient counts/block widths derive from geometry, not payload
claims. All subgrammars retain their own bounds and CRCs. The complete frame has
a final uint32 CRC32, giving80 fixed bytes before maps/plane bodies.

Optional encoder-side RDO zeroes selected whole8×8 quantized residual blocks;
this uses the existing zero/DC/full decoder syntax and adds no wire flags. Every
output tag binds the actual coefficients after pruning. It does not permit an
approximate reference, output-tag waiver or untransmitted original sample.

Geometry stays within the frozen720×480 maximum area and even dimensions.
Encoder/decoder prototype functions can test smaller dimensions; a parent
streaming profile must separately require its fixed720×480 canvas. A P frame
must reference a smaller frame ID; reconstruction requires the exact supplied
reference ID and canonical tag. All reconstructed output samples and both
geometry dimensions contribute to the final output tag.

The frame parser is diagnostic-bounded at2,000,000 bytes. The streaming complete
cap remains49,152 bytes and must include parent/HUD framing. This schema supplies
no acknowledgement, capability negotiation, reset or physical-owner protocol.
