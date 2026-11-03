# Iteration7: towards application-specific gameplay coding

This continues [iteration6](custom-codec-prototype-v6-2026-11-03.md) with three
actual Python experiments and a Luna-led independent evidence audit. The result
is a clearer codec direction: immutable-reference transform residuals plus
explicit application priorities. The combination is the **next prototype**,
not an implemented or hardware-qualified format. The detailed next steps are
in the [application-specific codec plan](gamebub-application-specific-codec-plan.md).

## Faster compatible decoder

The [word-reader study](../experiments/python-word-decode-study/README.md)
replaces per-bit reads with a bounded≤64-bit reservoir and unary lookahead,
plus combined AC tag reads. The frozen CP02 syntax, CRC, coefficient limits,
canonical escapes, padding and Q14 reconstruction remain unchanged. There are
72 exact same-packet receive pairs,216 coefficient-plane pairs,80 valid families,
all64 zigzag positions and2,000 valid-CRC malformed-payload differential checks.

| Actual paired Python receive mean | Frozen | Word reader | Reduction |
| --- | ---: | ---: | ---: |
| Combat |23.99 ms|22.02 ms|8.2%|
| Second clip |31.49 ms|27.60 ms|12.3%|

Key-only means improve62.93→49.27 ms and41.74→35.30 ms, but tails remain over
33.33 ms. The same mandatory inverse/color/reference work remains. Timings use
uncontrolled host load, repeated twelve-frame cohorts and alternating pair order;
they exclude acquisition/encoder/transport/display. They are not native or FPGA
services and do not change packet size or compression ratio.

Four actual-codec service replays perform212 preparations/hash-checked commits
and drain resources. Assumed8 ms decode gives28/30 diagnostic IDs/s; measured
Python receive gives26/24. The30 count occurs only in `[500,1500)` ms and still
has56/60 strict and58/60 eventual frames. Actual timing is endogenous and case
histories differ, so an assumed-decoder count cannot be credited to decoder
speed. There is no sustained30 fps or physical performance pass.

## A real application-priority quality map

The [RG01 prototype](../experiments/python-game-roi-study/README.md) encodes a
2-bit scale8/16/32 map per16×16 luma /8×8 chroma macroblock and three CP02 planes.
At720×480 the map costs338 bytes, outer header/CRC34 bytes; all nested payload
metadata is included. Relative to uniform FT02, the net packet increase at the
same uniform quantization is318 bytes. Uniform maps reproduce frozen pixels.
This is a new independent-frame format requiring a matching decoder.

Two fixed rectangles declare the priority regions. They are **not detected or
verified HUD coordinates** on the real footage. Eight predeclared native frames
from each4-second Mass Effect window and two seeded HUD fixtures are tested.
Six fixed profiles plus one bounded-search selection give126 profile records
and252 actual encode/decode candidate evaluations.

The selected map retains ROI8 and mixes background16/32 under each current
frame's uniform16 **reference-size budget**. It really encodes at most eight
midpoint candidates plus two charged endpoints; it does not use future source
frames or quality metrics to select the map. Policy causality is a source-review
observation, not a formal proof; metadata-only audit flags missing explicit
oracle/future declarations. Candidate search is not proven monotonic or optimal.

| Pooled comparison at nearly uniform16 bytes | Priority-region PSNR | Background PSNR | Active PSNR |
| --- | ---: | ---: | ---: |
| Combat8 |+2.51 dB|−0.46 dB|−0.08 dB|
| Second clip8 |+1.47 dB|−0.93 dB|−0.60 dB|
| Synthetic HUD2 |+2.75 dB|−0.06 dB|−0.04 dB|

All18 selections fit their same-frame reference size; two synthetic packets
still exceed48 KiB, largest91,513 bytes. A reference-size fit is not a receiver
capacity or network-admission pass. The actual encode work including the
reference/candidates averages254/238/395 ms by group, excluding additional
candidate decode/metrics/acquisition work. It is an **offline RD prototype**.
A live implementation must reuse transforms and prove a much smaller candidate
budget; it cannot substitute one selected encode time for all search work.

This is the first concrete application-specific gain: more fidelity where the
profile says it matters, paid for elsewhere. Lower edge-gradient error and
synthetic threshold errors do not establish text recognition, visual acceptance
or better gameplay. Real HUD profiles, temporal stability and a quality floor
remain required. Temporal residual savings and ROI gains cannot be multiplied
until the new combined profile is actually encoded/decoded.

## Exact dirty tiles: reject as the gameplay base

The [DT01 study](../experiments/python-dirty-tile-study/README.md) reuses an ACKed
reconstructed32×32 tile only if its current source RGB exactly matches the
ACKed original. Changed tiles are independent FT02; the complete dirty map,
per-tile headers, lengths and CRCs are charged. It has one outstanding frame,
atomic receiver publication and forced independent refresh on geometry/quality
change. No future or approximate-change threshold is used.

|12 inputs | Dirty-tile mean bytes | Whole intra | Immutable anchor | Dirty over48 KiB |
| --- | ---: | ---: | ---: | ---: |
| Combat |21,507|39,155|9,709|3 /12|
| Second clip |53,465|25,764|15,635|7 /12|
| Static synthetic HUD |7,456|21,483|7,135|1 /12|
| Scrolling synthetic HUD |74,078|32,043|31,646|12 /12|

The static tail averages only1,210 bytes per update, but its initial key is
oversized; that is not a bootstrappable48 KiB stream. Combat's82.8% tile-skip
rate partly reflects repeated native images. Scrolling and independent tile
metadata/context loss make this a poor default. All oversized packets are
kept and decoded for comparison; they are cap failures, not admitted frames.
Different tile/chroma boundaries produce different pixels and possible seams.

Logical skip-copy reads and output writes are counted, but this is immediate
in-process ACK eligibility, not a finite feedback model or physical memory
proof. Retained original/reconstructed host RGB and decoder outputs are
additional storage. Reusing pixels still consumes copy/scanout bandwidth in a
back-buffer design. Keep this only as a possible static UI/patch mode; the
immutable-anchor residual control is the better general candidate here.

## Evidence and remaining work

Twenty-six new tests pass: seven word-reader, seven ROI, six dirty-tile and six
audit tests. New formats have parser/CRC/range/padding checks and independent
reconstruction or frozen comparisons. The [independent audit](../experiments/python-app-audit-v7-study/README.md)
reconciles actual map/header costs, area-weighted active/ROI/background MSE,
source IDs/hashes, complete packet demand, cap failures and diagnostic/strict/
eventual counts. The [snapshot](prototype-v7-provenance.json) binds the sources,
inputs, result JSON and logs. Source media stays outside Git.

These are short, related, already-compressed sources at25/29.88 native fps;
repeated content and synthetic fixtures are labeled. None is native30-distinct
capture proof, broad game generalization, target memory/fit qualification or
physical display testing. The v6 handoff branches remain unchanged.

Next build one new temporal-ROI Python profile with the faster parser, exact
reconstructed references, explicit map and bounded rate controller. Compare it
against uniform temporal/JPEG controls with a declared priority-quality floor,
paid source/transform/search costs and exact matched IDs. Then freeze golden
vectors and integrate the standalone sender, firmware transport and FPGA
parser/dequantizer/reference path. Preserve JPEG for hardware testing throughout.
