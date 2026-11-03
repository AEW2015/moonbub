# BM01 bounded integer block prediction over frozen Q14/ROI/CP02

This new Python codec uses16×16 luma /8×8 chroma block vectors against an immutable
**ACKed reconstructed key**. It changes no frozen GM01 source. BM01 is a separate
experimental format, incompatible with installed JPEG/MSV1, GF02's GM01 adapter,
GH01/HG01 and standard HEVC/AV1 decoders. No firmware, native decoder, RTL or
hardware result is supplied by this study.

## Normative prediction and references

The host searches all even vectors in±4 luma pixels (25 candidates; optional±8
is81). Every actual luma sample contributes integer SAD. Candidates are ordered
by Manhattan magnitude, then dy, then dx; strict improvement retains that tie
order and prefers zero when tied. Partial edge blocks use only actual pixels.
Search reads the current source luma and reconstructed ACKed key luma, never
original key RGB, future frames or verification/error metrics.

Each output luma sample uses `key[clamp(y+dy),clamp(x+dx)]`. Its chroma block uses
half the same even vector, with border replication. Each macroblock has its own
vector; source pixels are never copied directly into a skip result. Residuals
use the frozen integer RGB/YUV420 conversion, Q14 transform, quantizer/map and
CP02 word arithmetic. Keys predict128; P frames predict only the immutable key.
ACKed P frames return credits without replacing that key. There is no recent-P
reference chain or adaptive motion partition size.

The key is reconstructed inside preparation and becomes the encoder reference
only after matching frame/session/body-CRC ACK. Two P credits are allowed. A
key cannot be replaced until all pending credits drain. Key ACK loss blocks P
preparation; expiration requires a new independent key. P loss/expiration keeps
the already-ACKed immutable key. Wrong-session/body-tag ACK cannot install a
reference, and a late ACK for an expired frame is ignored. These in-process
ownership rules are not physical read-drain or serialized wire feedback.

## Actual BM01 bytes and zero-residual mode

The little-endian outer header declares magic/version, key/zero-residual flags,
epoch/frame/reference IDs, even dimensions, search range, vector mode, map grid
and exact map/vector/three-plane lengths. A whole-body CRC follows. Parsers check
identity/reference ordering, bounded geometry/lengths, vectors, map padding,
nested CP02 CRC/coefficients and exact consumption before receiver publication.
No bad frame advances decoder anchor or last-frame state.

The quality map is the same2-bit macroblock map as GM01. P vectors use the
shorter complete representation: dense signed-int8 dx/dy pairs (2bytes/block),
or a MSB-first nonzero bitmap plus signed-int8 pairs for set bits. Dense wins ties.
Sparse zero pairs, nonzero unused bits, odd/out-of-range vectors and nonminimum
vector modes are rejected. All vector/map bytes are included in packet sizes.
GM01 controls have their global dx/dy fields inside their header; BM01 vector
payload sizes are separate, and neither header is treated as free.

Whole-P zero-residual mode is emitted only after **all three actual forward
transforms and quantizations** produce zero coefficients. Its three CP02 payloads
are absent; decoder output is the normative block prediction from reconstructed
YUV planes. The map and vector bytes remain. This is not a source-image equality
shortcut, per-block skip map or uncompressed RGB copy. It does not skip the host's
search/transform work. No per-block zero-residual syntax is implemented yet.

The receiver reconstructs directly from parsed bytes and its own key planes;
it never receives encoder pending arrays. Tests compare it with the encoder's
separate frozen-arithmetic expectation and compare every key against GM01 pixels.
Optional P expected-image reconstruction is verification-only and excluded from
preparation timing, as in the GM01 controls. Actual key reference reconstruction
is paid; every forward transform, motion search, vector search/encoding, map,
quantization and coefficient entropy operation is paid.

## Same-source experiment

Two60-native-frame Mass Effect windows start at1s. Profiles are frozen GM01 zero,
frozen GM01 global, and BM01 block±4; each uses the same ROI8/background16 map and
independent key IDs0/30. GM01 global retains its original sampled±16 search, while
BM01 uses full-block SAD±4, so this is a comparison of actual policies rather
than equal-search-work algorithms. Map construction is **inside** the outer
preparation timer. Decoder timing includes parse, prediction, inverse arithmetic
and RGB conversion. File load/BOX scaling, oracle/hashes, RGB565 error metrics,
transport and display are outside service timers.

Two additional30-frame comparisons use direct native RGB BOX to512×288, never
a resized720×480 canvas. Declared rectangles are proportionally scaled/clamped
from the720×480 canvas, changing their area and content alignment. Cross-resolution
PSNR is not a matched-quality point. Forward30/20fps fields are byte-rate arithmetic;
they do not change measured per-call costs or establish a paced frame rate.

Three separate8-source functional/algorithm fixtures cover flat static128,
oppositely moving textured halves and noise followed by a cut. Synthetic samples
are128×96, explicitly separate from the720×480 real-source output. Every selected
packet is decoded, even when it exceeds48KiB; oversize packets are algorithm
results, not admitted streaming frames. There is no rate controller/fallback or
paced network here. Forward59bytes/chunk and52-byte reverse feedback fields are
size calculations only; GF02's existing GM01 delivery adapter cannot decode BM01.

All profiles use immediate in-process ACK after valid decode/hash check, with no
lookahead, queue/deadline simulation or benchmark packet loss. Unit tests cover
key/P drops, ACK loss, expiry, stale epochs and recovery separately. Summaries
keep full bytes, vector bytes, cap failures, complete preparation/receive service
and common-region distortion together. Equal quantizer maps do not guarantee
equal distortion when the prediction changes.

## Reproduce and scope

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v
/home/lori/gamebub-streaming-prototype/.venv/bin/python benchmark.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python verify.py
```

Ten tests cover deterministic/scalar SAD equivalence, tie ordering, partial edges,
luma/chroma border prediction, dense/sparse bytes and malformed syntax, exact
zero-residual semantics, key agreement, independent decoder reconstruction,
atomic parser failure, two-credit ownership, source/reference separation, scene
cuts/noise, losses/expiry/session identity and independent-key recovery.
`results.json` binds all executed sources, media/frame/packet/output hashes and
runtime versions. The verifier checks stored bytes/regions/identities and source
pins without rerunning timed encoding.

The clips are related, already compressed native25/29.88fps, with repeated
content. Python runs have fixed profile order and uncontrolled host load. Their
component rates are not native30-distinct-frame capture or hardware throughput.
Full source, prediction, coefficients, oracle/output arrays and reconstructed
keys are extra host memory. A bounded±4 search suggests a possible tiled FPGA
reference cache, but this study implements no physical cache, DSP schedule,
BRAM/SDRAM bandwidth, DMA/CDC ownership, timing or resource fit. Next compare
byte savings against search/memory cost, then add bounded per-block skip or
rate-aware vector selection only with a normative reconstruction contract.

## Recorded results (2026-11-03)

All612 actual packets decode to the encoder's independently reconstructed RGB
expectation; key output matches the frozen GM01 decoder. Thirteen executed-source
pins and both external media hashes verify. Ten tests pass. `results.json`,
`summary.json`, `run.log`, `tests.log` and `verify.log` retain the evidence.
The four real-source windows have byte-identical GM01 zero/global controls,
meaning that frozen global search selects zero throughout these particular windows.
The controls differ on the artificial moving/noise fixtures.

| Canvas / real sources | GM01 mean complete bytes | BM01 mean complete bytes | Change vs GM01 | BM01 vector payload mean | Active RGB565 PSNR change |
| --- | ---: | ---: | ---: | ---: | ---: |
|720×480 combat /60|8,802.4|9,137.0|+3.8%|367.5 B|−0.008 dB|
|720×480 second /60|12,025.5|11,771.6|−2.1%|1,488.2 B|−0.108 dB|
|512×288 combat /30|5,270.7|5,447.4|+3.4%|172.9 B|−0.015 dB|
|512×288 second /30|6,943.4|6,475.1|−6.7%|711.2 B|−0.127 dB|

The mean residual-byte savings must pay for actual vectors/map/header bytes.
Full-block SAD is not entropy/rate-distortion selection: combat gets slightly
larger, and second-clip savings come with a small distortion change. Thus BM01
should not replace GM01 universally. The regional quantizer map remains8/16,
but changed prediction still changes reconstructed error. None of the real
packets uses whole-frame zero-residual mode.

| Canvas / real sources | GM01-zero preparation / receive | BM01 preparation / receive | BM01 mean SAD+prediction |
| --- | ---: | ---: | ---: |
|720×480 combat|22.15 /22.44 ms|55.09 /30.33 ms|33.59 ms|
|720×480 second|19.61 /23.96 ms|50.68 /29.47 ms|32.25 ms|
|512×288 combat|8.85 /10.63 ms|22.18 /13.55 ms|13.76 ms|
|512×288 second|9.47 /12.14 ms|22.69 /13.73 ms|13.85 ms|

These are complete measured Python calls under the stated service boundaries,
not target/native costs. Lower-resolution calls have more component headroom,
but preparation/receive are separate endpoint services, acquisition is omitted
and transport/presentation are not paced here. Means cannot establish30fps or
a worst-case deadline. At720×480 each P search evaluates8,640,000 actual luma SAD
samples; at512×288 it evaluates3,686,400. Abs/add search work is principally a
memory/adder concern; no DSP speedup or physical tiled cache is measured.

|512×288 actual-byte arithmetic|GM01 forward at30 /20 fps|BM01 forward at30 /20 fps|
|---|---:|---:|
|Combat|1.340 /0.893 Mb/s|1.393 /0.929 Mb/s|
|Second clip|1.766 /1.178 Mb/s|1.652 /1.101 Mb/s|

These include59 nominal forward bytes per1024-byte chunk and omit lower-layer
framing/retries; reverse ACK is a separate52-byte/frame assumption.20/30fps are
rate multipliers, not executed schedules. The512×288 inputs are direct-native
BOX resamples with a changed canvas/ROI; cross-resolution PSNR is not a matched
quality comparison. Combat contains32 unique RGB images among60 larger-canvas
inputs and19 among30 smaller-canvas inputs; the second clip has60/60 and30/30.

Artificial128×96 static128 exercises seven legitimate zero-residual P packets:
mean complete BM01 size94 B versus260 B GM01, with the same RGB565 output quality.
BM01 preparation is2.29 ms versus1.39 ms GM01-zero: search/transform work still
runs, so this byte shortcut is not a free host skip. On opposite-moving halves,
BM01 averages2,565.5 B versus6,574.4 GM01-zero /5,936.1 GM01-global, saving61.0% /
56.8%; active PSNR changes by+0.093 /+0.116 dB. This contrived motion field favors
independent blocks and is not representative gameplay evidence. Noise/cut BM01
averages9,845.1 B versus9,758.9 /9,321.5, and does not solve high-entropy scenes.
All recorded packets fit48KiB, but the synthetic noise canvas is128×96; that
is not a full720×480 noise-admission guarantee.

The next useful experiment is bounded actual-rate selection between zero and
block prediction, including complete vector bytes and every attempted search/
transform cost. Then add a per-block residual-zero/skip map only with exact YUV
reconstruction and full side-byte accounting. Test changed/repeated-content
policies against an ACKed state without treating raw source equality as a decoder
copy command. Keep the immutable-key recovery profile separate from any future
recent-ACK reference chain, and integrate the selected format into finite
ownership/service before native/RTL or physical frame-rate qualification.

## Portable stored checks

`python check_stored_results.py` repeats stored source/byte/quality checks
without rewriting the pinned summary, and lists absent external media separately.
`--write-summary` deliberately regenerates its summary. The original benchmark-
pinned `verify.py` is unchanged and expects the recorded media paths. Neither
command reruns timed encoding or establishes native/target performance.
