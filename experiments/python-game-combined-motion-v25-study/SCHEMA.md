# CP25 / HU25 / JA25 laboratory framing

All integers are little-endian. Every packet ends in uint32 CRC32 over all
preceding bytes. SHA tags mean SHA256 truncated to16 bytes. This is a new
incompatible research protocol; no existing AR03 endpoint accepts these bytes.

## CP25 pair

The56-byte `<4sBBIIBBII16s16s>` header contains magic`CP25`, version1, flags,
epoch, frame ID, source slot, destination slot, exact GM25 length, exact HU25
length, SHA16 of complete GM25 bytes and SHA16 of complete HU25 bytes. The two
inner packets follow in that order; the CRC gives60 fixed bytes. Maximum complete
pair length is49,152. Both inner frame IDs/epochs and canvases must agree.

Flags are0 (display only P),2 (published P),3 (published key). A key requires
source255/destination0 and independent GM25/HU25. A P requires source0/1; its
destination is the opposite slot when published and255 otherwise. The GM25
reference frame/tag must match the actual source bank. No other flags or slots
are accepted. Source-bank bytes are validated again by the frozen GM25 decoder.

## HU25 exact display HUD

The106-byte `<4sBBIIIHH16s16s4I4B16H>` header contains magic`HU25`, version1,
patch count0..4, epoch, frame ID, reference ID, canvas width/height, exact whole
reference HUD tag, exact whole reconstructed HUD tag, four payload lengths,
four type bytes and four `(x,y,width,height)` uint16 rectangles. Active slots are
contiguous from zero; unused lengths/types/rectangle fields are zero. Type1 is
a complete validated HP01/HR01 packet; type2 is a complete HD25 packet. Patch
payloads follow active slot order; a final CRC gives110 fixed bytes.

Reference ID`0xffffffff` requires a zero reference tag. Otherwise the reference
ID precedes this frame and names the actual previous accepted HUD. The whole
HUD tag hashes `<HHB>` canvas width,height,count followed by each `<4H>` rect
and its exact raster RGB565 words as uint16LE, in slot order. Rectangles are
inbounds and disjoint. HP01/HR01 inner rectangles must match their HU25 slot;
HD25 inner dimensions must match it. Every decoded RGB565 output contributes to
the whole output tag. Independent HD25 modes may coexist with referenced modes;
the HU25 reference binding remains mandatory whenever its refID is not sentinel.

## JA25 acknowledgement

The61-byte `<4sBII16s16s16s>` header contains magic`JA25`, version1, epoch,
frame ID, SHA16 of the complete CP25 pair including its CRC, GM25 reconstructed
YUV tag and HU25 reconstructed HUD tag. Its CRC gives65 total bytes. An ACK is
produced only after both outputs validate and modeled write-drain/vblank gates
allow the atomic publication. `validate_ack` checks the exact complete pair and
both embedded output identities; it does not infer acceptance from bare frame ID.
