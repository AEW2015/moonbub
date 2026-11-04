# EC26 / GE26 / CP26

All fixed integers are little endian. EC26 header `<4sBBIHH4I3I>` stores magic,
version1, flags, block count, blocks-per-row, reserved0, four stream byte lengths
and three AC nonzero counts. CRC32 follows the bodies. Flags0 means block-major
AC,2 frequency-major AC,1 raw int16 raster coefficients (other streams/counts0).
The fixed header+CRC costs46bytes. Raw fallback bounds each packet to128N+46.
Domains retain CP02: int16 coefficients within±2048,1..65536 blocks with integral
rows1..256 wide. The containing GE26 additionally bounds its native geometry.

The DC stream starts with Rice k0..13, then row-reset zigzag-signed differences,
prefix15 escape14bits. Each AC band positions1..5/6..20/21..63 has run k0..19 and
level k0..11. Sparse run is the number of zeros after the previous nonzero (−1
initial index); runs cross block boundaries. Run prefix15 escapes to24bits;
level prefix15 escapes to12bits and encodes signed-zigzag(nonzero)−1. Exactly
the declared nonzero count is read, all remaining coefficients are zero. Values,
runs, counts, exact lengths, zero bit padding and canonical escapes are checked.
Each of the four streams pads separately to bytes.

GE26 uses the GM25 header/maps with magicGE26 and the same80-byte fixed cost.
Frozen plane dispatches0/1/2 retain their exact grammar. Dispatch3 adds a complete
EC26 packet. The actual source/reference IDs, reconstructed reference tag and
output tag remain mandatory. Unknown modes, malformed framing, foreign tags,
CRC failures and output mismatches reject before publication.

CP26 and JA26 follow the frozen CP25/JA25 structures and strict bank/epoch/HUD
identity rules, except their magic. HU25 is retained verbatim. Complete CP26
must fit49,152bytes. These formats have no installed Sunshine/ESP32/FPGA endpoint.
