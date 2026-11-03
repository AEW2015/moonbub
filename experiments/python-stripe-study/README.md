# Actual byte-driven coefficient stripes

SS01 turns the earlier decoded-sample layout oracle into an incremental
compressed-byte parser. It reuses the frozen FT01 Q14/color/quantization math
and the new CP02 coefficient helper. This is Python research, not an installed
Sunshine/ESP32 mode, an FPGA implementation, or physical memory/FPS proof.

## Protocol and ownership

`stripe_codec.py` documents the exact versioned header, region fields and CRCs.
Each 16-luma-row stripe transmits its Cb block row, Cr block row, then two Y
block rows. Each coefficient region has its own header/CRC and bounded CP02
payload. Region IDs, plane, global row and geometry must follow the declared
sequence. All lengths are checked against geometry-derived maxima before a
region payload is staged; the frame header also bounds its total payload.

The next stripe's Cb/Cr arrives before its Y. That lets the preceding Y stripe
finish FT01's bilinear chroma lookahead without retaining whole YUV planes.
The last stripe repeats its final chroma row, exactly as the frozen full-plane
kernel does. Partial edge stripes crop padded IDCT blocks correctly.

`Decoder.feed(bytes)` accepts arbitrary chunk boundaries. It retains at most
one logical compressed region, one preceding Y stripe and preceding/current
chroma stripes. It emits `on_stripe(row, rgb)` callbacks and metadata events;
these pixels are **provisional BACK-buffer writes only**. No full RGB output
or input frame is retained internally. It never changes a front framebuffer.

The complete frame CRC produces a `frame_validated` event. Only explicit
`finish()` checks EOF/completeness and marks `committed=True`. Late corruption,
truncation, duplicate/out-of-order regions, malformed coefficient payloads or
extra bytes before finish fail closed and require reset; provisional pixels
must be discarded. `reset()` discards decoder state. The caller remains
responsible for abandoning its provisional buffer and suppressing publication.
No generation/session replay, physical drain, CDC, transport credits or ACK
implementation is implied by this codec parser.

The convenience `decode(packet, chunk_size)` allocates a complete RGB888 BACK
buffer outside the incremental parser and returns it only after commit. This
is useful for correctness tests, not a claim that a full display framebuffer
is avoidable.

## Reproduce

Use the existing pinned NumPy/Pillow/PyAV environment and both adjacent
coefficient/transform study directories. From here:

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v
/home/lori/gamebub-streaming-prototype/.venv/bin/python benchmark.py
```

`tests.log` records seven passing tests. They cover 1-byte/mixed/whole-packet
feeds, 2×2 and non-multiple-of-16 edge geometry, exact callbacks, global CRC
failure after provisional pixels have already emitted, missing EOF/trailer,
region order/duplicate/CRC failures, advertised-size bounds, reset and buffer
residency. Expected error conditions are checked by passing tests.

`benchmark.py` uses the exact first12 source frames from each of the four
existing JPEG windows (48 inputs), q16 only. Every incremental decode equals
the packet-independent frozen FT01 host reconstruction. All48 frames are fed
in137-byte chunks; the first frame of each window is additionally tested in
1-byte,4,096-byte and whole-frame chunks. Inputs, PTS, helpers and outputs are
hashed. These remain short precompressed Mass Effect samples; there is no new
capture, hardware test or native30-fps proof.

## Results

| Exact 12-frame window | SS01 projected wire Mb/s | Active RGB565-output PSNR | Largest packet |
| --- | ---: | ---: | ---: |
| Combat primary | 8.323 | 33.25 dB | 32,574 bytes |
| Second clip primary | 5.153 | 34.74 dB | 20,220 bytes |
| Combat held-out | 8.336 | 33.27 dB | 32,622 bytes |
| Second clip held-out | 5.121 | 34.72 dB | 20,149 bytes |

All48 sampled packets fit48 KiB. Wire rates project measured sizes at30 fps
with40 application+28 IPv4/UDP bytes per1,024-byte chunk; RF/link-layer,
retries, input/audio, capture, queues and physical service are excluded.
Region headers, repeated CP02 contexts and CRCs cost bytes versus the
whole-plane coefficient syntax. This layout improves bounded row availability,
not JPEG's rate/quality: same-frame JPEG q50 remains5.969/3.540 Mb/s on the
primary windows at33.30/34.74 dB. A sample cap result is not a general cap
guarantee; RAW coefficient fallback can make a complete frame much larger.

For720×480, actual retained decoded sample arrays peak at **23,040 bytes**:
one16-row Y stripe plus old/new8-row Cb and Cr stripes. This exceeds the
earlier18,000-byte sample oracle because the real block decoder obtains a
whole next chroma block row, not a freely supplied single lookahead row.
The parser stages at most23,070 coefficient-payload/trailer bytes plus a saved
13-byte region header under RAW fallback; actual sampled staged sizes are
about3.4–3.7 KiB. Bounded Python copies of that region may coexist temporarily.

These are separate allocations, not a total decoder BRAM estimate:

| Component | 720×480 modeled allocation |
| --- | ---: |
| Retained decoded sample arrays | 23,040 bytes peak |
| Returned int16 coefficient region | 23,040 bytes peak |
| IDCT int64 input representation | 92,160 bytes per largest region |
| Largest emitted RGB888 stripe | 34,560 bytes |
| Caller RGB888 provisional BACK framebuffer | 1,036,800 bytes |
| Hypothetical RGB565 BACK framebuffer | 691,200 bytes |

The NumPy IDCT/interpolation implementation also allocates arithmetic arrays,
byte copies and Python objects. `tracemalloc` on the first input of each window
records roughly464 kB (454 KiB) of additional decoder working allocations, excluding
the already-owned input packet and caller BACK allocation. This measured
Python peak is not target hardware RAM. No claim of a23-KiB complete decoder
or physical SRAM/BRAM fit follows from the sample residency number.

The recorded encoder timings are Python reference-program costs. The field
`decoder_plus_host_golden_wall_ms` deliberately includes the separate host
golden calculation and is not a decoder-only or hardware latency measurement.
Real adoption still needs a bounded coefficient/IDCT schedule, byte/credit
flow control, integrity-to-write-drain publication, target fit and measured
concurrent link/memory/display behavior.
