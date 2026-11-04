# HD21 exact display-patch delta component

This Python prototype encodes exact RGB565 display patches independently of the
lossy YUV prediction banks. It is a candidate for explicitly acknowledged receiver
HUD-cache reuse. It changes no installed AR03/MSV1 peer or FPGA design.

`encode(current, reference=None)` takes a two-dimensional NumPy uint16 patch and
returns immutable bytes; `decode(packet, reference=None)` validates it and returns
a fresh array. `inspect(packet)` validates framing and span grammar, returning
mode/geometry/byte counts and tag hex strings. Only `decode` can check the complete
current-content tag of a delta. `content_tag(array)` returns the exact geometry-bound
SHA256[:16]. The caller must supply only an acknowledged, still-resident reference;
cache identity, epoch, acknowledgment, eviction, reset, loss and publication belong
to a separate protocol layer.

## Bounded grammar and mode choice

The fixed 46-byte little-endian header is `<4sBBHHI16s16s>`: `HD21`, version 1,
mode, width, height, payload byte count, reference tag, current tag. A final CRC32
of every preceding packet byte adds four bytes, making **50 bytes total fixed
overhead**. SHA256 tags cover `<HH>` width/height followed by little-endian RGB565
words, truncated to 16 bytes. They detect wrong content; they are not authentication.

| Mode | Value | Payload |
| --- | ---: | --- |
| RAW | 0 | Raster little-endian uint16, zero reference tag |
| COPY | 1 | Empty, exact reference and current tags must match on decode |
| SPAN_XOR | 2 | uint16 record count, then changed contiguous row-runs |

Each span has `<HHH>` row, starting column, word count followed by that many
little-endian nonzero XOR words. Rows/runs must increase, never overlap or touch,
and stay within geometry. Adjacent runs should have been merged by the encoder.
The decoder rejects unknown modes, impossible counts, malformed/trailing payload,
zero XOR values, wrong length/CRC/reference/reconstructed tags, and invalid geometry.
Malformed packets never mutate caller-owned input/cache arrays.

The encoder picks the actual smallest complete RAW/COPY/SPAN_XOR packet; ties use
RAW. It stops constructing a losing span stream when its byte length would reach
RAW cost. A separate integration layer can compare this entire framed packet with
an existing compressed full patch, including that alternative's wrapper bytes.

Geometry is bounded to width 720, height 480 and **21,120 total words**; maximum
payload 42,240 bytes, maximum complete packet 42,290 bytes. No packet-declared
length can cause an allocation larger than these bounds. Python's arrays, spans,
temporary headers and runtime overhead are not an ESP32 SRAM allocation plan.

## Component results and limits

The unit campaign includes 60 seeded randomized roundtrips plus explicit exact
COPY, sparse row spans, noisy RAW fallback, maximum geometry, endian/strided input,
wrong references, every truncation of a delta packet, malformed span grammar,
content-tag mismatch and CRC corruption. A 160×24 patch costs 7,730 bytes in RAW,
50 bytes in COPY, or 80 bytes for three runs containing five changed words. Such
synthetic sparse gains do not establish savings on actual gameplay; the separate
cache campaign measures real patches and complete framing costs.

Run from this directory:

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v test_model.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python verify.py
```

Six retained synthetic golden packets reconstruct **36,481 exact words** using a
separately written scalar decoder, deterministic NumPy re-encoding and six negative
CRC replays. `results.json` pins six source/documentation files and all compressed
packet/reference/output objects. `benchmark.py` regenerates these synthetic controls;
it is not a timed gameplay benchmark.

No native endpoint, radio throughput, FPGA area/clock, target memory use or sustained
30 fps is established by this component.
