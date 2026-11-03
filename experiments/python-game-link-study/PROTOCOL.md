# Experimental GM01/GF01 functional contract

This document describes the implemented Python laboratory, not a deployed wire
protocol. Ordinary JPEG/MSV1 peers do not support these packets. Authentication,
audio/input multiplexing, capability negotiation and serialized decode ACK/NACK
are outside this prototype. No reference ACK is inferred from frame assembly.

## GM01 frame (little endian)

The outer header is46 bytes with no implicit padding:

| Offset | Bytes | Field |
| --- | ---: | --- |
|0|4|`GM01`|
|4|1|Version1|
|5|1|Key flag0 or1|
|6|4|Epoch|
|10|4|Frame/capture ID|
|14|4|Exact immutable anchor ID, or0xffffffff for a key|
|18|2|Width|
|20|2|Height|
|22|2|Signed dx|
|24|2|Signed dy|
|26|2|Macroblock columns|
|28|2|Macroblock rows|
|30|4|Packed map bytes|
|34|4|Y CP02 bytes|
|38|4|Cb CP02 bytes|
|42|4|Cr CP02 bytes|
|46|variable|Packed map, Y payload, Cb payload, Cr payload|
|end−4|4|CRC32 of preceding bytes, zlib convention|

Geometry is even and bounded by the frozen720×480 maximum pixel count, with
individual dimension bounds inherited from FT01. Frame and epoch IDs cannot
use0xffffffff; IDs increase without wrapping in a session. dx/dy are even in
±16 and zero for a key. Residual anchor ID must be lower than frame ID and match
the receiver's retained reconstructed key exactly. A P frame never becomes the
predictor. New epoch/reset requires explicit session coordination.

The map grid is ceil(width/16)×ceil(height/16). Four2-bit codes per byte, MSB first,
map0→scale8,1→16,2→32; code3 and nonzero unused padding are rejected. The same
macroblock selects four luma8×8 blocks and its Cb/Cr8×8 blocks. At720×480 the
map is338 bytes; total outer header/CRC50 bytes. Every plane is separately bounded
and CRC-checked CP02, with original DC row reset, Rice contexts, RAW fallback,
coefficient limits, canonical escapes and exact padding semantics.

Residuals use the exact ACKed reconstructed YUV420 key. The host computes one
RGB/prediction/raw-forward-transform analysis, then may quantize/serialize several
pure candidate previews. Admission alone commits a selected pending packet;
rejected candidates do not consume frame/reference credits. Key commit reconstructs
YUV for future prediction; its matching epoch/frame ACK installs that anchor.
P ACKs release bounded credits, and refresh waits for those credits to drain.
Actual physical old-reader drain and wire feedback still require implementation.

All Q14, quantization, interpolation, color conversion and clipping semantics
are defined by the frozen Python source hashes and golden vectors. A uniform
map matches MA01 decoded pixels; complete packet bytes differ. GM01 is342 bytes
larger than same-scale MA01 at720×480 due to map and envelope accounting.

## GF01 chunk (network byte order)

The laboratory container has a27-byte header:

| Offset | Bytes | Field |
| --- | ---: | --- |
|0|4|`GF01`|
|4|1|Version1|
|5|4|Epoch|
|9|4|Frame ID|
|13|4|Complete frame bytes,1..49152|
|17|2|Chunk index|
|19|2|Chunk count, ceil(total/1024)|
|21|2|Payload bytes|
|23|4|CRC32 of complete GM01 bytes|
|27|variable|Canonical frame slice at index×1024|

All non-final chunks contain1024 payload bytes; the last length is exact.
Maximum datagram payload is1051 bytes (header plus data). Total nominal IPv4/UDP
bytes in the fixture accounting are data+55 bytes per chunk; lower-layer/RF,
feedback and retransmission costs are excluded. This differs from older model
accounting that assumed40 application+28 IP/UDP header bytes per chunk.
Do not mix the two wire budgets or infer physical throughput from either.

Metadata must agree for every chunk. The receiver has two frame slots and
bounded per-slot chunk metadata. Unique out-of-order chunks fill fixed offsets;
identical duplicates do not add progress or extend the timeout. Whole-frame
CRC must pass before the payload is delivered. Delivered payload stays pinned
through decoding. `commit` requires the exact locally owned completion object;
`reject` releases a rejected reader after it is finished. Higher-frame decode
commit can invalidate older partial assemblies but cannot free older delivered
readers. Epoch reset refuses outstanding delivered readers.

The adapter binds GF01 epoch/frame to the GM01 header before codec mutation.
Incomplete, corrupt, missing-reference or mismatched data cannot publish an
anchor or image. Actual decode completion and sender reference ACK remain two
separate steps. The fixtures perform those steps immediately in-process; there
is no real network timing, hardware display, or physical memory qualification.
