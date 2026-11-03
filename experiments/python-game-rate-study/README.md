# Bounded two-candidate GM01 admission with transform reuse

This Python controller uses the actual combined
[GM01 temporal/ROI codec](../python-game-codec-study/README.md). It replaces the
previous broad offline ROI rate search with a much simpler admission policy:
one normal map, and at most one fallback if its packet does not fit. The two
policies are different algorithms; the earlier search's near-matched rate/quality
result must not be carried over as a benefit of this simpler controller.
No Sunshine/firmware/FPGA mode is installed by this study.

## Policy and transactional work

The priority policy keeps scale8 in the fixed rectangles
`(16,48,192,80)` and `(160,352,400,80)` on the720×480 canvas. Normal background is
scale16; fallback background is scale32. Those are declared priority rectangles,
not automatically detected or verified real-game HUD coordinates. An explicit
uniform control tries scale16, then scale32 everywhere; it does not share the
priority policy's ROI scale8 constraint. Both use the same48 KiB complete-packet
cap, including map, envelope, coefficients and CRCs.

`Encoder.analyze()` computes source/prediction/three-plane forward DCT once.
Each map candidate reuses those raw transforms, applying only quantization,
entropy and packet assembly. The controller selects the first candidate that
fits, then calls `commit()`. Rejected candidates are never committed: they do
not install a reference, consume a pending credit, or advance the issued frame
ID. A second failure drops the whole capture. Candidate/analysis counters still
advance because real work happened. A later accepted key can recover without
weakening the configured ROI scale.

No decoded-error or future-frame observation participates in selection. Actual
candidate byte lengths, fixed maps/current geometry and configured cap are its
only decision inputs. Previous reconstructed references are those explicitly
ACKed by the encoder. The result declares its causality inputs. Verification
parses the chosen packet outside preparation timing and checks the actual
selected ROI map has min/max scale8, not merely what the host intended to send.
This code-level scale constraint is not a perceptual or text-legibility guarantee.

The caller measures the complete `Controller.prepare()` call, including map
construction, analyze/color/prediction/DCT, every attempted candidate, selection,
selected key reconstruction/commit, return and local array cleanup. An internal
service timer and per-stage timings are retained separately. Source acquisition/
scale, optional RGB/hash oracle, decoder checks, transport/QSPI/feedback and
presentation are excluded. Oversize rejected attempts pay all preparation work.
There is no deadline/drop-age scheduler, concurrent endpoint test or hardware
measurement here.

## Actual nominal-cap sequence results

Four12-native-frame windows (two Mass Effect clips, starts1 s/4 s) are each run
with both policies. A separate12-frame seeded fixture has six high-entropy noise
images followed by six simple recovery images, also under both policies. ACK is
immediate in-process after a real receiver decode and exact host hash check.
Source native PTS/rates, input hashes, versions and executed-source hashes are
recorded. Native rates remain25/29.88 fps and content repeats; these short,
related precompressed samples are not30-distinct-frame/s capture evidence.

Ten policy sequences evaluate120 captures, admit108 and reject12 noise inputs.
They perform132 actual candidate encodes and360 plane forward transforms. All
96 real policy/capture evaluations fit the normal candidate; **no real nominal
sequence exercises fallback**. Both noise policies reject six inputs without
consuming credits or references, then recover with a key at capture6 and admit
the next six. Rejected work and startup losses remain in the result. The six
noise rejects cost94.61 ms mean for the uniform policy and104.13 ms for priority
(maximum106.45 ms); bounded attempts are not a worst-case33.33 ms deadline.

Priority preparation means are24.47/20.77 ms for combat starts1/4 s and22.34/
20.15 ms for the second clip. All48 real priority calls in this small run are
below33.33 ms; this excludes receiver/capture/link work and is not a sustained
30 fps or worst-case deadline pass. External host load is uncontrolled, without
CPU affinity/isolated warmup. Different policy runtimes are not paired speed
comparisons and select different reconstructed anchor histories.

The priority map improves common-admitted-ID ROI PSNR by2.09/2.10 dB for combat
and1.56/1.39 dB for the second clip. Background error is effectively unchanged
because both normally use background16. This costs **6.1%/3.9% and12.9%/10.5%
more packet bytes**, respectively. These are same-cap comparisons, not equal-
bitrate gains. Full metrics separate active/ROI/background areas and compare
only IDs admitted by both policies; different decoded predictors/pixels remain.

## Paired reuse proof under a declared pressure cap

A second benchmark makes each of twelve4-second source captures an independent
key, repeats twice, and alternates naive/shared measurement order. Both variants
try exactly the same maps and must produce identical decisions, candidate
lengths, selected bytes and receiver RGB. The fixed28 KiB cap was chosen using
prior fixture observations to exercise fallback; it is a branch-pressure fixture,
not an independently held-out or nominal48 KiB stream.

| Same packet/decision key pairs | Naive mean | Shared mean | Two-attempt pairs |
| --- | ---: | ---: | ---: |
| Combat24 |45.87 ms|34.78 ms|24 /24|
| Second clip24 |25.62 ms|25.53 ms|0 /24|

For combat fallbacks, reuse reduces service24.2% while cutting raw forward
transforms from six to three per capture. It does **not** halve total encoding
work: quantization/entropy/assembly are still done twice, and selected key
reconstruction remains. Every shared fallback call still exceeds33.33 ms;
p95 is35.31 ms and maximum35.53 ms. The second clip fits its first candidate,
so there is no meaningful reuse gain. No rate or FPS gain is inferred from
preparation time alone.

The core GM01 reference rules still apply. This benchmark immediately ACKs one
admission before the next and does not exercise two in-flight credits, wire
ACK serialization/loss, physical read drain, capture scheduling or stale-frame
rejection. Prepared objects retain prediction/raw-transform arrays temporarily;
pending encoded packets and key YUV, the current candidate coefficient workspace, source/output and oracle arrays are additional host
storage. This is not an ESP32 allocation or physical SDRAM fit/throughput proof.

## Reproduce and checks

From this directory with the common pinned environment/media layout:

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v
/home/lori/gamebub-streaming-prototype/.venv/bin/python benchmark.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python verify.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python analysis.py
```

Five tests cover normal/fallback admission, actual packet-map quality checks,
three-vs-six transform counts with identical bytes, paid double rejection and
reference preservation, foreign/stale candidates, edge macroblocks and immutable
configuration. `verify.py` reconciles source pins, cap decisions, paid stages,
selected map counts, all120 capture outcomes and48 independent key pairs.
`analysis.py` derives the compact `summary.json`; neither helper reruns video
encoding. Candidate output rejection/cap behavior and nominal success remain
separate from any30 fps qualification.
