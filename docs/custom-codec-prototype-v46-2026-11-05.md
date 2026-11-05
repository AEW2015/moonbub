# V43–V46 checkpoint: direct receive, coefficient delivery and bounded rate work

This checkpoint combines four completed host studies on previously qualified
CS38/AB38 streams. V43 removes proof-adapter work from receiving; V44 streams
coefficients as one-block tiles; V45 checks a symmetry-based inverse-transform
operation model; V46 searches a bounded Rice-parameter neighborhood and measures
actual complete-packet choices. Together, these studies preserve the existing
compressed coefficients and quality. They do not establish FPGA/ESP32 fit,
physical frame rate or end-to-end streaming performance.

## V43 direct CS38 receive path

The direct receiver removes the proof adapter's entropy re-encoding, converted
CS37 packet construction and repeat parse. It reuses 577 already-encoded frames
across eight v38/v39/v40 causal histories; no source re-encoding is included. The
mean of per-frame three-sample paired medians
fell from 145.341108 ms to 89.006410 ms, a 38.7603% reduction in measured receive
service time. Both paths validate and decode, predict, inverse-transform,
normalize and validate HUD; the baseline includes the proof adapter's extra
work. State forks and display checks remain outside both clocks.

Independent replay passes all 577 causal receives across eight histories,
covering 553 unique packet digests (the 24 V38 prefix packets recur in the later
V39 full histories), with 1,298 source pins. It confirms 1,731 arithmetic planes,
4,504,062 visible
coefficient blocks, exact coefficient/qmap/vector/YUV/HUD/reference outputs, and
that entropy re-encoding is disabled. Four producer tests and ten independent
tests pass. Across V43–V46, 28 focused producer and independent test cases pass
(14 + 6 + 5 + 3). Full coefficient and YUV arrays are still retained: each full set is
1,036,800 bytes, plus 42,240 bytes for four RGB565 HUD patches. These are array
sizes, not total process peak memory or a target allocation fit. The result is
host receiver-service improvement over a proof adapter; it does not show
physical 30 fps, whole-pipeline latency or compression superiority.

## V44 one-block coefficient delivery

The iterator replays 3,462 AB38 plane payloads—1,731 full and 1,731 compact—and
9,177,762 coefficient tiles exactly. Its 128-byte staging figure is only the
8×8 int16 output tile. The retained compressed input reached 23,937 bytes, with
additional arithmetic state, probability state, pending events and larger
Python heap use. The iterator does not stage a full coefficient plane, but
reconstructed output still needs staging until the entire packet validates.

All real archived payloads use arithmetic syntax; raw fallback is covered by
directed tests. Six focused tests pass, including a malformed raw case where
tiles are returned before a late range error poisons the iterator. Returned tiles
are provisional: an integrated receiver must withhold frame and reference
publication until complete success. The measured 15.50 ms full-array decode
versus 19.21 ms tile decode plus digest is asymmetric and is not a speedup claim.

## V45 symmetric inverse transform

On 1,731 full-grid planes, the mirrored Q14 inverse matches the frozen matrix
inverse on 4,673,700 actual dequantized blocks; 5,193 actual tiles also exercise
scalar sparse/shortcut paths. Five focused tests cover signed extremes,
rounding boundaries, invalid domains and zero/DC cases.

With equal zero/DC shortcuts charged to both sides, the logical sparse multiply
model falls from 275,542,196 to 138,052,328, a 49.8979% reduction. The NumPy
implementation still performs dense matrix operations; these are logical
multiply counts for a proposed implementation, not measured DSP work. The
proof retains the normative input domain ±2048×255 = ±522,240, which requires
20 signed bits. The observed coefficient magnitude 1,792 does not justify
narrowing. Conservative accumulator/intermediate bounds require 36/22/37 signed
bits. No DSP mapping, resource fit, cycles or routed timing is measured.

## V46 bounded Rice search and complete-packet choices

The component search covers 144 AB38 plane payloads (72 full/compact pairs),
with 2,917 stream candidate encodes independently decoded to exact coefficients.
Across both representations, stored component bytes fall from 451,605 to
449,785, a 1,820-byte reduction. This total includes both full and compact
alternatives, including losing options. The search tests a bounded ±1
neighborhood around existing Rice parameters; it is not a global optimization.
Three focused tests pass.

The actual complete-frame selection on 24 frames is smaller: 395,448 to
394,546 bytes, saving 902 bytes or 0.2281%. Of 72 plane choices, the searched
full representation wins 11 times and compact wins 30 times. The previous
payload wins the other 31 choices; each is a byte tie, and the old-first tie
rule retains it. Independent causal replay confirms exact coefficients,
references, HUD and quality. The existing CS38 source encodes were already
paid; the proof adapter reserializes existing entropy components and is not a
new native receiver. These are short prefixes, not a full-history or held-out
rate campaign.

## Combined limits

The four efforts address separate receive and rate-building components. V44
still needs atomic publication around late errors; V45 needs actual hardware
mapping and scheduling; V46's byte change is small on the measured complete
frames. Source encoding cost, network/display work and a fitted bounded pipeline
are not measured here. No result establishes a 30-fps endpoint, DSP fit, memory
fit or HEVC/AV1 bitrate victory.

Supporting audits: [V44/V45 evidence](v44-v45-evidence-audit.md) and
[V46 rate-search evidence](v46-rate-search-audit.md). V43 study details and
reproduction are in [the direct receiver README](../experiments/python-game-direct-rx-v43-study/README.md).
