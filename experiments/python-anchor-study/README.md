# Immutable-anchor overlap experiment

MA01 is an actual-packet Python prototype for an alternative to MT02's
stop-and-wait reference chain. It reuses frozen Q14/color/quantization, global
motion/residual and CP02 arithmetic. It is a **separate profile/capability**:
an ordinary MT02 receiver must not be assumed to retain the required anchor.
There is no Sunshine mode, ESP32 firmware, FPGA decoder or physical FPS proof.

## Reference and credit rules

`AnchorEncoder.prepare` encodes each P against one immutable, ACKed key
reconstruction. P ACKs release bounded credits and never change the anchor.
The default window is two; pending P entries retain hashes/metadata, not full
reconstructed images. A lost P therefore does not poison following P frames.
The receiver retains its key anchor separately from the latest displayed
reconstruction. It rejects old/regressing display IDs and old-anchor packets
after a refresh, while later P packets against the current anchor remain valid.

A key requires all previous P credits drained. Preparing it discards the old
host anchor, and P preparation waits for that key's epoch/frame-bound ACK.
A lost key ACK causes timeout and a new independent key, not a guessed anchor.
Unknown/duplicate ACKs cannot release another transaction's credit; another
epoch is rejected. Expiring a P only releases its credit. The receiver checks
the complete outer CRC and all frozen coefficient rules before commit.

MA01 uses the MT02 layout with a distinct magic and the interpretation above;
profile conversion validates the existing CRC before rewriting magic/CRC.
No corrupted packet is accidentally repaired by the adapter. The ACK itself
is a Python call, not a serialized/authenticated/drained hardware message.

## Timed model

`timed.run(frames, manifest, Config(...))` actually prepares each selected RGB
input against the available anchor, gets its real packet length, schedules
it, decodes the bytes and checks the expected RGB hash. Captures replaced in
the latest waiting slot are never encoded. The next selected input is really
re-encoded; this is not replay of old fixed lengths.

Virtual defaults are 30 capture IDs/s, 2 ms serialized preparation, ideal
8 Mb/s network, 160 Mb/s QSPI, 8 ms serialized decode and hypothetical 60 Hz
vblank. One network transfer, QSPI and decoder can overlap as independent
stages. Stage times are **assumed**, not derived from Python wall timing.
Wire costs include 40 application+28 IPv4/UDP bytes per1,024-byte payload;
ACK/link/RF/retry/audio/input bytes are excluded. The model retains at most
two slot-owned packet byte arrays and three logical RGB framebuffer roles:
immutable front, latest pending and decoder back. Completed/rejected packet
arrays are released; history logs contain metadata, not all old packet bytes.

A periodic key is requested after30 capture IDs since the last prepared key;
capture replacement can change its actual ID. New P preparation pauses while
old credits drain, so refresh can cost cadence. Oversized actual packets are
rejected after charging preparation time. In the fixed-q8 baseline a rejected
P releases its credit but retains the anchor; repeated cap rejection is a
recorded failure, not hidden by a retry. Two separately labeled held-out
controls enable `cap_backoff_max=32`: after a cap rejection the next capture
uses quantizer8→16→32 (bounded), and a key is requested after old P credits
drain. This changes distortion and is not an equal-quality rate gain.
Host age admission occurs before encoding. Timeout is200 ms from send by
default. Wire/QSPI/decoder resources keep draining after an expired credit;
late old ACKs cannot change a newer anchor. Network processing is serialized,
not a general reordering/retransmission implementation.

The complete capture window is `[0,N/30)` with a separate1,000 ms drain.
For60-input cases a **predeclared short** steady window `[500,1500)` ms is
also reported. Counts in that one-second window are coarse; they do not
qualify long-term30 fps or justify shifting the failed strict window.
Stage-to-vblank age excludes optical/panel response. Front/back roles are an
ownership oracle, not real SDRAM/CDC implementation or pixel-buffer allocation.

## Inputs and reproduction

Use the previous [Python environment](../python-codec-study/requirements.txt).
The benchmark selects60 consecutive native frames from each existing Mass
Effect source, at starts1 s/4 s. It preserves source SHA/PTS/canvas hashes,
native25/29.88 fps and duplicate content. Scheduling those images at30 IDs/s
is explicitly hypothetical; no frame interpolation or native30 capture proof.
The code uses the same local project/media layout as the preceding studies.

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v
/home/lori/gamebub-streaming-prototype/.venv/bin/python benchmark.py
```

`tests.log` records13 passing tests: fixed-reference identity, bounded credits,
out-of-order P rejection without later poisoning, dropped P, refresh drain,
key-ACK loss, stale/duplicate/epoch ACK, corruption/private refs, finite stage
ownership, actual-cap rejection/bounded backoff, overload and invalid configuration.
`results.json` binds executed source/input manifests and contains actual
selected IDs, commit/presentation records, ACK/timeouts, slot allocations,
complete packet sizes, quality and independent Python wall costs.

Quality is RGB565-output active-content MSE for the IDs actually committed or
presented. Anchor and stop-and-wait can choose **different IDs** after drops;
do not compare their quality against an unmatched full JPEG corpus or describe
them as identical-pixel compression. The anchored distortion also differs
from MT02's progressively updated reconstruction.

## Measured model results

All sixteen cases use actual packet encoding/decoding:934 preparations,
902 successful hash-checked commits and901 eventual presentations. There
are28 actual cap rejections, two injected data losses, two injected CRC
rejections and one pending image superseded at vblank. Every case drains
its network/QSPI/decode slots and pending ACK credits; no capture waiting
entry remains. Persistent packet payload peaks at95,296 bytes, within the
two49,152-byte slots. Logical framebuffer/credit assertions run throughout.

The twelve fixed-q8 baseline cases have these short-window results:

| Window | Steady IDs/s at feedback0/10/20 ms | Strict2 s counts | Eventual counts | Cap rejects |
| --- | --- | --- | --- | --- |
| Combat primary | 30 /29 /29 | 59 /58 /57 | 60 /59 /58 | 0 /0 /0 |
| Second clip primary | 30 /30 /29 | 59 /59 /58 | 60 /60 /59 | 0 /0 /0 |
| Combat held-out | 27 /27 /27 | 48 /48 /47 | 48 /48 /47 | 9 /9 /8 |
| Second clip held-out | 30 /30 /29 | 59 /59 /58 | 60 /60 /59 | 0 /0 /0 |

Two additional primary-window fault cases use data loss7, ACK loss25 and
CRC corruption45. They each eventually present57 inputs and end at ID59,
without dependent-reference failures from the lost P frame. These schedules
do not inject a duplicated ACK; duplicate ACK safety is a state-machine test.

The held-out combat demonstrates the main fixed-anchor drawback: the old
reference becomes inefficient and frames exceed48 KiB. Presented-image p95
age reaches116.67 ms over its full capture/drain interval. The optional
next-capture8→16→32 backoff with drained-key refresh reduces cap rejection
to one and eventually presents55/54 inputs at0/10 ms feedback, versus48/48
with fixed q8. Steady counts remain27; this has not repaired the30 fps gate.
It also lowers presented-ID PSNR from36.08 dB to35.74/35.76 dB and changes
which IDs present, so quality is not directly matched.

Fixed held-out combat transmits5.044/5.047 Mb/s worth of bytes per declared
two-second capture window; backoff transmits6.076/5.966 because more inputs
are admitted. Those accounting rates include transmissions during drain and
are not measured sustained RF goodput. Better frame admission can increase
wire bytes even when quantization is coarser. The full packet/ID records keep
that distinction visible.

The actual Python model needs about5.42–7.49 wall seconds for each two-second
capture scenario on this run. It therefore does not itself run in real time.
The virtual2/8 ms preparation/decode assumptions cannot be inferred from
these Python timings, and an optimized native/FPGA implementation is unproven.

## Memory and remaining gates

The persistent anchor contains518,400 logical8-bit YUV420 sample bytes at
720×480. Python stores int16 arrays and therefore retains1,036,800 bytes per
anchor at each endpoint. Old/new arrays and transform/prediction/output
temporaries coexist during actual encoding/decoding. The pending-key buffer
is one retained anchor candidate; it does not add an unbounded anchor pool.
Logical RGB framebuffer ownership requires three691,200-byte RGB565 images;
this does not validate their physical map or resource fit. Compressed staging
and protocol metadata, workspace, array snapshots, color-conversion traffic,
reference fetches and scanout service remain separate costs.

The next gate is longer native input, explicit framebuffer/reference memory
service, physical timing and actual ACK/control cost. Fixed anchors can cost
more bits as they age, and periodic refresh/startup drain can lose otherwise
available capture slots. An overlap rate improvement is not automatically a
quality, latency or memory advantage.

## Slower assumed decoder sensitivity

`extra_cases.py` regenerates `extra-results.json` from the exact primary
cohorts. At10 ms feedback and an assumed20 ms decoder, combat and the second
clip both count29 IDs/s in the declared one-second window, with58/59 eventual
presentations. The matching stop-and-wait sensitivity gives26/24 IDs/s and
51/49 eventual presentations. References, selected IDs and quality differ.
Increasing the anchor decoder assumption to40 ms reduces the second clip to
24 IDs/s and48/60 eventual presentations; p95 age reaches100 ms. More overlap
does not remove a receiver-service bottleneck. An independent metric helper
checks the strict/diagnostic presentation counts in these extra cases.
