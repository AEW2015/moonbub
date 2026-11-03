# Iteration8: executable application-specific temporal codec

The [application-specific plan](gamebub-application-specific-codec-plan.md) now
has an actual combined Python codec, GM01, rather than separate temporal and
intra-ROI experiments. It uses an ACKed reconstructed immutable key, temporal
transform residuals, a transmitted macroblock quality map and CP02 coefficients.
This continues [iteration7](custom-codec-prototype-v7-2026-11-03.md). None of these
new packets is an installed Sunshine/ESP32/FPGA mode or JPEG-compatible stream.

## Combined GM01 reference

The [combined-codec study](../experiments/python-game-codec-study/README.md)
implements a46-byte versioned outer header with key/epoch/frame/reference IDs,
even geometry/vector, map geometry and three bounded plane lengths. The explicit
2-bit map selects scale8/16/32 per16×16 luma /8×8 chroma macroblock. Whole-frame
and nested CP02 CRC, map padding, coefficient limits and exact identity checks
precede receiver state publication. The word coefficient reader and frozen Q14
arithmetic remain the reference.

At720×480 the map costs338 bytes and the outer header/CRC50 bytes. Uniform GM01
is342 bytes larger than same-scale MA01 after envelope differences, not zero-cost
metadata. One immutable YUV420 key needs518,400 logical8-bit sample bytes; actual
Python int16 anchor arrays use1,036,800 bytes per endpoint, excluding workspaces.

`analyze → encode_candidate → commit` separates source/color/prediction/forward
DCT from map quantization and entropy. One analysis performs three plane
transforms. Pure previews do not consume references/credits; only the chosen
admitted candidate commits. Owner/generation checks reject foreign, forged,
stale or already-used candidates. Selected keys reconstruct predictor YUV;
optional verification RGB/hash is lazy. P ACK releases credit without changing
the anchor. Key replacement waits for logical old credits to drain; physical
read-drain and wire feedback remain unimplemented contracts.

Seventy-two actual GM01 packets decode correctly. Twenty-four uniform-map
outputs match frozen MA01 pixels exactly. Variable-map keys match the intra
ROI golden; residuals are also checked against explicit reconstruction. The
same twelve4-second source captures per clip are used by all three profiles:

| Within GM01 | Combat | Second clip |
| --- | ---: | ---: |
| Uniform16 mean bytes |9,895|10,420|
| ROI8/background16 mean bytes |10,313|11,519|
| Extra bytes versus uniform16 |4.2%|10.5%|
| ROI PSNR gain |+2.14 dB|+1.39 dB|
| Active PSNR gain |+0.29 dB|+0.21 dB|

ROI8/background32 reduces mean bytes15.1%/16.8% versus uniform16, while lowering
active PSNR2.32/1.64 dB. Keep that quality tradeoff visible. These are declared
priority rectangles, not detected/verified real HUD locations or a perceptual
floor. All72 packets fit48 KiB in this short cohort; no worst-case admission or
30 fps claim follows. All profiles are now actually encoded together with
prediction, so the ROI and temporal results are not multiplied from separate
experiments.

## A two-candidate controller with shared transforms

The [rate study](../experiments/python-game-rate-study/README.md) uses one normal
ROI8/background16 map and at most one ROI8/background32 fallback. The48 KiB cap
is applied to complete actual packets. Rejected candidates are never committed;
ROI stays at8. The comparison control uses uniform16 then32 and therefore has
a different priority-quality policy. Every candidate and selected key
reconstruction is paid before the optional verification oracle.

Ten immediate-ACK sequences evaluate120 policy/capture cases:96 real evaluations
from four12-frame windows and24 seeded stress evaluations. They admit108 and
reject12 noise inputs, with132 actual candidate encodes and360 plane forward
transforms. The96 real evaluations all fit their first candidate. Each stress
policy rejects six initial noise frames without consuming a reference, then
recovers with an independent key at capture6 and admits six quiet inputs.

Priority preparation means are20.15–24.47 ms across the real windows; all48
priority calls are below33.33 ms in that small run (maximum28.83 ms). Acquisition,
receiver, transport, feedback and presentation are excluded. Noisy rejects still
cost up to106.45 ms: two attempts bound work count, not execution time. These
are actual Python wall calls under uncontrolled load and immediate in-process
ACK, not concurrent endpoint throughput, a deadline guarantee or physical FPS.

A separate same-byte/decision paired experiment uses a declared28 KiB pressure
cap chosen from earlier fixture observations. Twenty-four combat key pairs
exercise two candidates: naive recomputation45.87 ms mean becomes34.78 ms with
shared transforms (24.2% lower, six→three plane transforms). Every shared
fallback still exceeds33.33 ms; p9535.31/max35.53 ms. Twenty-four second-clip
pairs fit normally, so25.62→25.53 ms is no meaningful reuse gain. The pressure
fixture is not independent held-out or nominal48 KiB evidence.

## Golden vectors and bounded laboratory ingress

The [link study](../experiments/python-game-link-study/README.md) exports eight
GM01 key/residual/geometry/epoch cases, including full720×480 canvas frames.
Sixty-four files contain source RGB, actual packets, packed datagrams, maps,
parsed coefficient arrays and decoded RGB565. All file sizes/hashes and byte
layouts are recorded. The fixture set is5,746,416 bytes; packets peak at19,803
bytes. Replay checks all eight decoded outputs, maps, coefficients and anchor
IDs exactly.

GF01 is a separate experimental27-byte laboratory chunk header with canonical
1024-byte payload slices, not a bypass of MSV1's JPEG validation. Its40 fixture
datagrams are replayed in reverse order, including duplicate handling. The
reassembler enforces two slots of at most49,152 bytes, consistent metadata,
whole-frame CRC, partial timeout and epoch/frame rules. Nominal IPv4/UDP cost
is55 bytes per chunk here; older timing models assumed68. The budgets must not
be interchanged, and neither includes RF/feedback/retransmission overhead.

A completed frame remains pinned until the exact owning completion is decoded
or rejected. Partial timeout and later commits cannot free an older delivered
reader. Epoch reset requires those readers to drain. The adapter checks the
outer/inner epoch/frame binding before codec mutation; ingress completion is
not a sender reference ACK. Thirteen unit tests cover these contracts, including
98,304 retained payload bytes in two full partial slots. Fixtures themselves
use one immediate-ACK frame at a time. Extra source/workspace/output/copy memory
is not included in that logical payload bound; there is no DMA/CDC or physical
ESP32/FPGA memory proof.

## Predict size before paying for oversized entropy packets

The [size study](../experiments/python-game-size-study/README.md) computes exact
CP02 encoded length from quantized coefficients, Rice costs, DC reset, AC runs,
EOB/ZRL, padding and RAW fallback without constructing bitstrings. It reuses the
same source analysis and quantized coefficients when a selected candidate is
emitted. Regenerating72 prior GM01 packets reproduces every saved packet SHA;
216 plane lengths match the exact estimate. Selected decisions, bytes and RGB
also match the original controller on32 paired independent-key calls.

Exact preflight reduces eight seeded-noise rejects113.48→43.24 ms mean, with no
entropy serialization. But normal keys regress32.66→34.62 ms and pressure calls
35.96→37.37 ms; even the six fallback-only pressure calls show negligible gain.
Computing exact Rice costs is not a free normal-path optimization. Preserve
this negative outcome instead of enabling full preflight by default.

The separate [cheap-gate experiment](../experiments/python-game-size-study/GATE.md)
uses a conservative lower bound. Each nonzero AC needs at least five token bits
plus one Rice bit; mandatory DC/EOB and parameter/header bytes are included.
Taking the minimum with the RAW length preserves safety under fallback. If
this lower bound already exceeds the frame cap, the candidate cannot fit and
is dropped before Rice selection/entropy construction. A lower bound below the
cap is **not** admission: actual emitted bytes are still checked.

| Same-input paired key call | Original controller mean | Cheap gate mean |
| --- | ---: | ---: |
| Seeded-noise rejects8 |113.68 ms|25.04 ms|
| Ordinary keys12 |33.52 ms|32.93 ms|
| Pressure keys12 |37.07 ms|37.75 ms|

The noise path avoids every entropy serialization, reduces mean service78.0%,
and peaks at28.68 ms in this small sample. All eight frames remain rejected;
visual continuity during dense scenes is still unqualified. Normal-path variation is small;
pressure regresses1.8% and its gate tail reaches51.13 ms. The weak bound misses
all six real oversized first candidates in the pressure group, so18 packets
are still serialized across12 calls. This is a promising high-entropy rejection
guard, not a general encoding speedup or a deadline/30 fps guarantee. Its32
pairs are a separate controlled comparison from exact preflight; do not infer
a cumulative speedup by mixing baselines measured at different times.

Five size tests cover80 coefficient families, all64 zigzag positions, exact
sizes/lower-bound safety and candidate/credit ownership. Paired tests rotate
measurement order and retain complete preparation time, including rejected
work. All timings are Python wall costs under uncontrolled load, excluding
source capture/scale, verification, receiver, transport and presentation.

## What is ready and what comes next

Forty new tests pass: nine codec, five rate controller, five size guards,
thirteen laboratory link and eight independent audit checks. The
[independent audit](../experiments/python-game-audit-v8-study/README.md) recomputes
packet/candidate accounting, ROI floor and common-ID quality, paired timings,
source pins and golden-vector hashes. The [snapshot](prototype-v8-provenance.json)
binds this checkout's executable sources and artifacts. Component READMEs contain
commands and scope; raw video remains outside Git.

The implementation now provides a concrete application-specific codec reference:
PC-side priorities/rate decisions, opaque transport chunks, and a bounded parser/
transform/reference contract for FPGA implementation. The unchanged priority
rectangles are still not verified real-game HUD locations; subjective readability,
quality floors, temporal flicker and per-game profiles need further evaluation.
Samples remain short, related, already-compressed native25/29.88 fps clips with
repeated content, plus separately labeled stress/functional vectors.

The next work is to integrate the selected controller and guards into an actual
capture/deadline/credit schedule, using the combined decoder and measured services.
Include acquisition/scaling, rejection cost, periodic key replacement, serialized
ACK/NACK and actual packet ingress in that model. Extend sources and the existing
1,800-distinct-frame gate before native/RTL and physical10-minute qualification.
Use the GM01 golden vectors to begin decoder implementation and negotiate a
real peer contract; GF01 remains a laboratory container. No custom firmware,
installed Sunshine output mode, FPGA bitstream or physical30 fps result is
claimed. Existing JPEG hardware testing can continue independently. The v7
handoff remains an unchanged snapshot.
