# GM01: combined temporal residual and application-priority map

GM01 is an executable Python combined codec, not a claim that the independent
RG01 quality gain and MA01 rate saving multiply. It uses the exact ACKed
reconstructed immutable YUV key as predictor and an explicit16×16 luma /8×8
chroma quantizer map with scales8/16/32. P output releases credit without
advancing the anchor. Every selected packet is actually parsed and reconstructed.
The format requires a matching receiver; it is neither JPEG, MA01 nor RG01.

## Format and decoder

The46-byte outer header is `<4sBBIIIHHhhHHIIII>`: GM01 magic,version1,key flag,
epoch,frame,anchor ID,width,height,even dx/dy,macroblock width/height,map bytes,
and three CP02 payload lengths. Key flag1 requires anchor0xffffffff and zero
motion; residual frames require a lower exact retained anchor ID. The current
map follows, then three actual CP02 payloads and a4-byte whole-frame CRC32.
Each CP02 payload retains its own bounded syntax and CRC. Geometry, key/reference
identity, vector domain, map codes/padding, nested lengths, coefficient limits
and complete CRC are checked before reference/visible-ID commit.

At720×480 the map is338 bytes, outer header/CRC50 bytes. Relative to uniform
MA01, GM01 at the same map scale adds342 bytes overall (the338-byte map plus
changed envelope accounting), not merely a free control flag. RGB/YUV conversion,
Q14 transform/inverse/rounding and macroblock table choices are frozen. The
bounded word reader is the independent CP02 parser.

Keys predict constant128. P uses the exact reconstructed anchor with bounded
zero/global translation and chroma half-vectors. Per-block mapped quantization
applies to the residual. Reconstruction adds the inverse residual to prediction,
clips and converts to RGB. Failed packets never update the retained anchor or
last visible ID. The parser has no access to sender originals or candidate arrays.

## Analysis, previews and admission

`Encoder.analyze(rgb, frame_id, force_key=False, mode='zero')` converts source,
chooses the current predictor and performs three forward transforms (one per
plane) exactly once. It returns a `Prepared` with read-only owned prediction and
raw transform arrays. It changes observation counters, not references, frame-ID
admission or pending credits.

`encode_candidate(prepared, scale_map)` validates/copies the map, quantizes the
cached transforms and emits a complete `Candidate.packet`. Multiple candidates
can share one analysis. Preview does not admit the capture, reset a reference
or reconstruct a rejected key. `commit(candidate)` reconstructs a selected key,
then creates pending state and returns its packet. P verification is optional
and lazy via `expected_hash(frame_id)` outside production preparation.

Owner identity, emitted-object identity, epoch, generation, monotonic frame ID,
current anchor and current credit eligibility are checked again before commit.
A forged dataclass clone, foreign encoder's candidate or stale preview cannot
be committed. A successful commit invalidates other analyses/candidates from
that generation. Weak registries do not retain discarded candidates forever.
Read-only NumPy flags protect normal callers; trusted Python code can explicitly
change internals, so this is not an isolation/authentication boundary.

`ack(frame_id, epoch=...)` installs only a pending key; P ACK only releases credit.
Wrong epochs raise, duplicate/expired ACKs do not consume another credit. Keys
expire to no anchor and require a fresh independent frame. Key replacement
requires pending P credits drained. The default is two credits, maximum eight.
Logical ACK credit is not hardware/DMA read-drain proof. Wire ACK serialization,
network reset/reorder/retry and physical lifetime/pinning remain implementation
gates; this reference is single-threaded.

`prepare(...)` is a convenience analyze/candidate/commit call. Its default
uniform scale is16. A caller can use `can_prepare`, `expire`, `expected_hash`
and `retained_reference_bytes` with the prior MA01-style scheduling interface.
Candidate-size admission is a caller/controller responsibility: credit bounds
alone do not enforce a48 KiB storage cap.

## Actual packet and quality results

Twelve consecutive native frames from each existing4-second Mass Effect window
are encoded in three profiles: uniform16, fixed ROI8/background16, and fixed
ROI8/background32. The declared rectangles match the previous ROI study but
are not verified real HUD coordinates. Keys occur at IDs0/6, zero motion is
used, and every capture gets immediate in-process ACK after verification.
There are72 actual GM01 packets and24 uniform MA01 decoded-pixel comparisons.
All uniform-map pixels match MA01 exactly, including P and refresh. No virtual
link or native30fps capture is inferred.

| Source/profile | Mean bytes | Priority PSNR | Active PSNR | Packets >48 KiB |
| --- | ---: | ---: | ---: | ---: |
|Combat uniform16|9,895|33.59 dB|33.68 dB|0 /12|
|Combat ROI8/bg16|10,313|35.72 dB|33.97 dB|0 /12|
|Combat ROI8/bg32|8,404|35.72 dB|31.36 dB|0 /12|
|Second uniform16|10,420|34.65 dB|34.93 dB|0 /12|
|Second ROI8/bg16|11,519|36.04 dB|35.14 dB|0 /12|
|Second ROI8/bg32|8,669|36.03 dB|33.29 dB|0 /12|

ROI8/bg16 gains2.14/1.39 dB priority-region PSNR, paid by4.2%/10.5% more
mean bytes. ROI8/bg32 uses15.1%/16.8% fewer bytes than uniform16 but loses
2.32/1.64 dB whole-active PSNR and coarsens background. These are actual combined
format tradeoffs over the same capture IDs, not matched-size/matched-quality,
perceptual acceptance or broad gameplay results. Different anchor quality can
change later residuals and pixels. Uniform baseline reconstruction is frozen;
its complete envelope cost is included.

Observed Python preparation means are19–23 ms across these profiles; recorded
p95 values reach38.34 ms. Receive means are20–24 ms, with key-related tails
up to39.55 ms p95. Profile order/background host load/warmup are uncontrolled;
these are actual per-call observations, not paired speedup or real-time service
qualification. Preparation includes analysis, candidate serialization and
selected-key reconstruction, excluding optional oracles/metrics, source capture/
scale, transport and presentation. The bytes-per-second estimates use actual
wire-size accounting at hypothetical30 captures/s, not delivered FPS.

## Memory and verification limits

Each720×480 analysis retains518,400 int64 raw transform values (4,147,200 bytes)
and518,400 int16 predictor samples (1,036,800 bytes). Each candidate retains
1,036,800 coefficient-array bytes,1,350 map bytes and its packet. These coexist
with anchors, pending packets, entropy strings and reconstruction temporaries.
The default two credits do not bound arbitrary caller-held previews; the bounded
controller must release them. Pending key/P packet bytes remain host-owned until
ACK/expiry in this reference, independently of physical receiver slots.

Each retained key is1,036,800 Python int16 bytes per endpoint (518,400 logical
8-bit YUV420 bytes). These numbers are not device-fit or bus-service proof.
No FPGA/ESP32/Sunshine mode, memory allocation, target timing, wire ACK/drain,
physical display or sustained30 fps qualification is added by this study.
Source footage is related and already compressed at25/29.88 native fps; content
repeats and native PTS remain explicit.

## Reproduce

Use the existing pinned Python/NumPy/Pillow/PyAV environment and external media:

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v
/home/lori/gamebub-streaming-prototype/.venv/bin/python benchmark.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python verify.py
```

Nine tests cover uniform MA01 and nonuniform RG01/golden reconstruction,
key/P/global/refresh and geometry edges, exact source ownership, multiple pure
previews, stale/foreign/forged candidates, credit/drain, key expiry, ACK epochs,
replay, missing reference and malformed map/header/length/CRC/nested payloads.
`results.json` binds inputs, source versions and executed hashes before/after.
`verify.py` reconciles72 packets, counters, paired uniform-envelope overhead,
source IDs, area-weighted MSE and cap counts. Tests are finite regression evidence,
not formal all-input equivalence or a physical platform test.
