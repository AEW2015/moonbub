# Reconstructed-reference transform and global motion prototype

MT02 adds temporal prediction to the frozen FT01 arithmetic and CP02 coefficient
coder. It is a Python research format, not an installed Sunshine mode, ESP32
implementation or FPGA decoder. The benchmark measures actual encoded packets,
independent parsing and reference reconstruction; it does not measure FPS.

## Format and reference contract

`Encoder.prepare(rgb, frame_id, quant_scale=16, mode='global')` produces one
packet and holds its reconstructed YUV420 planes pending. `Receiver.receive`
validates all lengths, CRCs, coefficients, epoch/frame/reference IDs, geometry
and vectors before committing the reconstructed reference. Its returned RGB
must exactly match `Encoder.prepared_rgb()`. Only `ack(frame_id, epoch=...)`
advances the host reference. ACKs from another epoch, stale IDs and extra work
while a transaction is outstanding are rejected. Timeout/abort discards the
host reference and forces an independent next frame, including after a lost
ACK when the receiver already committed. Session allocation, timers and a wire
ACK/control protocol remain external; CRCs do not authenticate messages.

The frame header `<4sBIIIBHHhhI>` declares magic/version, epoch, frame ID,
reference ID, quantizer, width/height, signed vector and payload length.
`0xffffffff` denotes no reference and is reserved for epochs/frame IDs. The
payload is three length-prefixed CP02 coefficient packets plus a frame CRC.
Dimension-derived RAW bounds are checked before CRC/decompression. IDs cannot
wrap; a caller must allocate a fresh epoch/session. A key frame predicts128
and exactly matches the frozen independent transform reconstruction.

P frames predict from the **ACKed reconstructed planes**, never original host
pixels. The bounded host-only translation search uses sampled luma SAD and
even vectors within ±16 pixels. Prediction samples reference[y+dy,x+dx] with
replicated borders; chroma uses half the vector. Residuals are transformed
without a128 level offset, quantized, decoded and added to the prediction with
clipping. Residual sample bounds ±255 give fixed-Q14 coefficients within the
±2048 CP02 bound. This is global translation, not per-block motion estimation.

One outstanding transaction is intentional for this correctness prototype.
It serializes feedback and may limit rate. A hardware implementation needs
bounded in-flight reference lifetimes, control delay, drain/commit semantics
and reference recovery; it must not silently replace this with guessed refs.

## Run

Use the [existing pinned environment](../python-codec-study/requirements.txt).
The scripts use the same two local media files as the earlier studies;
`GAMEBUB_MEDIA_DIR` and `GAMEBUB_SUNSHINE_TOOLS` override their directories.
From this directory:

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v
/home/lori/gamebub-streaming-prototype/.venv/bin/python benchmark.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python synthetic_motion.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python feedback_bound.py
```

`tests.log` records20 passing tests: reconstructed rather than original
reference use, exact host/receiver pixels, key equivalence, lost data/ACK and
CRC recovery, replay/wrong epoch, ACK epoch, malformed vectors, private refs,
known encoded pan, perfect-frame metrics and feedback-window checks. The
benchmark snapshots/verifies executed helpers and JPEG-reference hashes.

## Video comparison

The four windows contain30 native decoded frames each, starting at1 s and4 s
from the two precompressed Mass Effect files. Unique-image counts are19/30
and30/30 for primary windows,21/30 and30/30 for held-out windows. These are
short, related clips with native rates25/29.88 fps, not fresh native30 fps game
captures. No input frames are repeated/interpolated to fill a window.

`results.json` has independent, zero-motion temporal and global-motion temporal
profiles at scales8/16/32. Normal profiles include one initial independent
frame followed by29 dependent frames. Host ACKs immediately after the complete
receiver commit; there is no network/capture/ACK-time schedule in this benchmark.
All1,080 normal packets reconstruct exactly to the host model. The separate
four fault campaigns commit28 of30 attempted frames each and recover to ID29.

Rates project measured mean sizes to hypothetical30 fps, including40 application
and28 IPv4/UDP bytes per1,024-byte chunk. RF/link framing, ACK/retry, audio and
input bytes are excluded. PSNR pools active-content RGB565-output MSE against
the common BOX-scaled/letterboxed RGB canvas; it does not establish visual
equivalence or HUD/temporal acceptance.

| Exact30-frame window | MT02 temporal scale8 Mb/s / PSNR | Receiver JPEG q80 Mb/s / PSNR |
| --- | --- | --- |
| Combat primary | 1.697 /35.87 dB | 8.345 /36.19 dB |
| Second clip primary | 2.219 /36.23 dB | 5.419 /36.42 dB |
| Combat held-out | 2.745 /35.89 dB | 7.095 /36.30 dB |
| Second clip held-out | 2.635 /36.11 dB | 5.458 /36.29 dB |

These temporal results use about52–80% fewer projected wire bytes than JPEG
q80 with0.18–0.41 dB lower PSNR. That is promising sample evidence, not an
agreed matched-quality advantage. Repeats/static regions favor prediction;
long native captures, cuts, fast pans and visual inspection remain necessary.
Almost all real-clip vectors are zero; at scale16 only one held-out combat
frame selects a nonzero vector. The gain is predominantly reconstructed-reference
residual coding, not demonstrated global motion benefit on these game clips.

At scale16, primary temporal rates are1.305/1.468 Mb/s versus independent
MT02's7.547/4.308 Mb/s. Error is different across temporal/intra profiles;
they must not be described as identical-pixel savings. All sampled packets
fit48 KiB, but general RAW fallback can exceed device caps. No cap enforcement
or real sender admission occurs in this offline packet benchmark.

The fault campaigns lose data at ID7, lose its ACK after receiver commit at
ID17, and corrupt ID23. The next IDs8/18/24 become independent; no failed
packet mutates the receiver reference. Mean sender bytes increase because
refreshes cost data. Fault quality statistics include committed frames only
and are not matched against full-corpus JPEG quality.

## Motion diagnostic and memory

`synthetic-results.json` separately tests a seeded smooth grayscale texture
panning4 pixels/frame with replicated borders. At720×480, mean dependent
packet size drops from9,743 bytes with zero vectors to4,616 bytes with global
motion; all nine translated frames select(-4,0). Both modes match their own
host reconstruction exactly. This positive diagnostic is synthetic, not a
substitute for the mostly-zero-vector gameplay results.

Logical P-frame payload counters charge518,400 reference-sample read bytes,
518,400 reconstructed-reference write bytes and691,200 RGB565 output bytes at
720×480. An independent60 Hz RGB565 scan adds41.472 MB/s. At29 P +1 I per30
frames, these primary payloads total92.7936 MB/s at30 fps, before compressed
traffic, color-conversion rereads, overfetch, copies, arbitration and refresh.
This is not a physical SDRAM bandwidth proof or complete transaction model.

Python stores reference arrays as int16:1,036,800 bytes per YUV reference,
with old/new prediction/snapshot/output arrays and temporaries coexisting.
The codec is plane-first and full-frame in software. It is **not integrated**
with the separate byte-driven stripe decoder, and cannot claim that decoder's
small sample footprint. Python encode/decode times are reference-program costs,
not real Windows or hypothetical FPGA service measurements.

## Feedback cost remains a gate

`feedback-results.json` tests a serial, store-and-forward stop-and-wait capacity
schedule using cyclic fixed JPEG lengths, assumed2 ms encode/8 ms decode,
8 Mb/s network and160 Mb/s QSPI. With0/10/20 ms extra feedback delay, combat
decode-completion rates are25.18/20.12/16.74 IDs/s; the second trace gives
29.78/22.96/18.66. There is no vblank stage or physical measurement.

Those numbers are **not MT02 FPS**: its dependent packets are smaller, and
dropping an input changes subsequent reconstructed references and residual
sizes. The next gate is a coupled virtual-capture/codec/feedback model that
actually re-encodes after skips, then longer source scenes and real service
measurements. An in-flight window may improve overlap, but needs explicitly
owned references and delayed/duplicated/lost ACK/reset tests before adoption.
