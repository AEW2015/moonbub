# GM01 golden vectors and bounded GF01 laboratory ingress

This is an in-process interoperability harness for the new combined custom
codec. It exports actual GM01 keys/residuals, macroblock maps, decoded RGB565
and parsed coefficients. The fixtures can seed a future C/RTL decoder testbench.
No sockets, installed Sunshine mode, ESP32 firmware or FPGA are changed.
GF01 is an **experimental laboratory container**, not MSV1/JPEG compatibility
or an implemented capability-negotiation protocol.

## Fixtures and exact replay

`export_fixtures.py` creates eight frames and64 binary files: random small key,
small changed region, small pan, non-multiple-of16 edge key/residual,720×480
canvas key/residual, and a new-epoch key. It performs one analysis/three plane
transforms per frame (24 plane transforms total), a real parsed decode, an exact
host RGB hash check and a matching epoch/frame ACK. All data is procedurally
created; no external media or real gameplay is represented by these vectors.

The full fixture set is5,746,416 bytes, with40 actual datagrams and maximum
packet19,803 bytes. Packets carry the new explicit quality map. Golden RGB565 is
the codec's lossy decoded output, not an assertion that it equals original RGB.
Git marks fixture payloads as binary to preserve their bytes across platforms.
Each file's size/hash and each packet's source/output IDs are in
`fixtures/manifest.json`. Source and coefficient arrays are included to make
color, parsing, block ordering and reconstruction independently inspectable.

The exporter reverses each frame's chunks and inserts a duplicate before the
final missing chunk. `replay_fixtures.py` checks all64 file hashes, reassembles
in reverse order, decodes all eight frames and verifies RGB565, coefficient/map
bytes, anchor IDs and final empty ownership. This is functional evidence,
not simultaneous endpoint execution, latency or30 fps qualification.

Data layout:

- `.rgb888`: original RGB888 row-major, dimensions in the manifest.
- `.gm01`: complete actual codec packet, including CRC and map.
- `.gf01`: fixture-onlyu16 big-endian datagram length followed by each datagram;
  the length prefix is not a network field.
- `.rgb565le`: expected decoded RGB565, little-endian row-major words.
- `.scale8`: uncompressed row-major scale values8/16/32 (not packed2-bit codes).
- `.planeN.i16le`: parsed signed16 little-endian coefficients in
  `(block_raster,8,8)` shape, as recorded per plane.

## Bounded ingress and ownership

`chunks.py` accepts canonical1024-byte payload chunks into at most two slots,
each at most49,152 bytes. Out-of-order fragments and identical duplicates are
allowed. Inconsistent metadata, conflicting duplicates, wrong epochs, stale IDs,
invalid counts/lengths and oversized allocation requests are rejected. Full-frame
CRC is verified before a `Complete` is returned. CRC is integrity detection,
not authentication; this laboratory is not a secured network protocol.

**Complete assembly does not release a slot or ACK a codec reference.** The
returned immutable payload remains pinned in its exact owning row until the
caller finishes decoding and calls `commit(complete)` or `reject(complete)`.
A forged/foreign/copied completion cannot release credit. Only partial assembly
expires; duplicate arrivals do not extend its150 ms default timeout. Delivered
readers cannot be reclaimed by that timeout or session reset. A later-frame
commit discards only obsolete partial assemblies, leaving older delivered readers
pinned until explicitly rejected after read completion.

`harness.decode_complete` checks ownership and the outer/inner epoch/frame
binding before invoking GM01. Inner parser/reconstruction must succeed before
ingress decode commit. The sender's reference ACK is a further explicit action;
ingress completion alone never creates an ACKed predictor. Rejected packets free
their drained slot without advancing the codec. This tests a single-threaded
API contract, not physical DMA/QSPI/CDC read drain or a serialized wire ACK.

A unit test fills both full-size partial slots and observes98,304 retained
payload bytes. The fixture run uses one frame at a time and peaks at19,803.
These are logical owned payload sizes. Temporary immutable copies, received
chunks, sets/dictionaries, generated source arrays, decoder workspaces, retained
anchors, output and fixture/oracle buffers are extra host memory. There is no
ESP32 or FPGA allocation/fit claim.

## Reproduce

Use the common pinned Python/NumPy/Pillow/PyAV environment:

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v
/home/lori/gamebub-streaming-prototype/.venv/bin/python export_fixtures.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python replay_fixtures.py
```

Thirteen tests cover reorder/duplicates, two-slot saturation, partial timeout,
conflicting duplicates, complete CRC failure, metadata/size/session bounds,
foreign completion, delivered-reader pins, reset drain, full-frame decode/ACK
separation and inner/outer identity/CRC atomicity. Export/replay are additional
functional checks, not additional unit-test counts. The source-bound fixture
manifest and final iteration snapshot preserve the exact run.

See [PROTOCOL.md](PROTOCOL.md) for byte offsets and the key/ACK distinction.
Next implement explicit capability negotiation, serialized feedback and real
firmware ingress against these vectors before trying this format on hardware.
Keep the existing JPEG control and do not reinterpret GM01/GF01 as MSV1.
