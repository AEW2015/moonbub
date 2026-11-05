# V32: specialize the Game Bub codec using measured costs

The useful advance is **lossless HUD compression**, plus an explicit model for
overlapping FPGA block stages. The new residual-shrink policy and expensive wider
motion search do not justify deployment. We have **not beaten HEVC or AV1** on
compression, proved a native 30 fps endpoint, or implemented a new full receiver.
This study preserves 720×480 coded / 720×405 active video rather than reducing
resolution. It uses the two retained Mass Effect gameplay windows; these are
short reused fixtures, not independent evidence across games.

## Measured outcomes

| Experiment | Primary window | Complex window | Decision |
| --- | ---: | ---: | --- |
| Exact HUD component bytes | 310,961 → 310,685 | 623,615 → 562,316 | Keep; 0.089% / 9.830% savings, no pixel changes |
| Strict residual shrink, complete causal bytes | 552,619 → 552,584 | 1,229,773 → 1,230,134 | Reject as default; negligible or worse |
| Budgeted residual shrink, complete causal bytes | 552,619 → 552,040 | 1,229,773 → 1,225,574 | Reject as default; prior v30 budget dominates it |
| Wide motion with actual sparse escapes, prospective body bytes | 152,292 → 151,790 | 355,962 → 353,896 | Research only; 0.33% / 0.58%, different 12-frame matched-reference probe |
| Two-bank inverse-stage model, mean ms at assumed 100 MHz | 11.78 → 6.20 | 13.71 → 7.39 | Implement RTL next; conditional projection only |

The 48-frame causal comparisons serialize actual GM27/CP27/JA27 packets with
the existing HU25 HUD and a 49,152-byte cap. The HUD and wide-motion components
are separately serialized experiments. Their prospective totals are not an
integrated CP32 stream. Do not add independent savings or compare the 12-frame
wide-motion totals directly with the 48-frame causal totals.

## HUD: specialize the exact interface layer

[HX32/HS32](../experiments/python-game-hud-v32-study/README.md) codes RGB565
component prediction residuals with bounded canonical Huffman tables. It reuses
the existing motion prefix and tries row or intra-left prediction. Existing HU25
bytes win ties and remain the fallback. All 2,027,520 HUD words across 96 frames
reconstruct exactly; 58 frames select new syntax, containing 148 new patches.

This is a promising application-specific layer because small text and UI patches
have different statistics from the game picture. The implementation adds
67.37 / 80.58 ms per frame of Python encoding work, **excluding** the inherited
HUD encoder and motion search. Python component decode averages 4.03 / 14.82 ms.
These are research timings, not firmware or FPGA service times.

The bounded logical table budget is 1,143 bytes for three tables, plus row state;
an expanded lookup, ports and physical mapping remain unmeasured. Reference and
staging HUD payloads total 84,480 bytes in external memory, not ESP32 SRAM. The
ESP32 should forward bounded opaque payloads rather than decode them. Negotiation,
CRC/reference binding and atomic full-frame publication must precede deployment.

## Residual edits: local improvement can lose across time

[The causal controller](../experiments/python-game-controller-v32-study/README.md)
adds protected small-AC deletion and magnitude shrink against the actual v30
strict winner on each policy's own decoded history. It protects DC, the lowest
six zigzag positions, ROI and chroma halo. Every alternative pays actual entropy
and source-distortion work; the complete winner must save bytes and pass a
current-frame RGB error guard. All losing attempts are retained.

Strict primary MSE changes 14.386886 → 14.385352, but complex MSE changes
26.303889 → 26.309251. Locally valid strict choices can create worse subsequent
references. Budgeted complex MSE rises 0.753% for 0.341% fewer bytes. Both new
budget points have more bytes and higher mean MSE than the older v30 budget.
Host policy work rises from 306 / 410 to roughly 500 / 652 ms per frame, including
all trials. This work excludes capture, source conversion, preencoded HUD creation,
archival I/O, network and presentation. It is far above a 33.33 ms source period.

The [isolated shrink probe](../experiments/python-game-shrink-v32-study/README.md)
likewise finds few genuine magnitude-shrink wins. Retain these negative results;
do not promote the policy because a fixed-reference or single-frame result wins.

## Wider motion: compact syntax is necessary but insufficient

[The wider search](../experiments/python-game-wide-motion-v32-study/README.md)
extends the prediction search beyond the current ±18 half-luma-unit syntax bound.
It reduces actual residual bytes 1.04% / 1.47%, but raw motion-map accounting makes
the complete prospective bodies larger. Only 3.00% / 4.03% of P-frame blocks
exceed the current bound.

[WV32 sparse escapes](../experiments/python-game-wide-escape-v32-study/README.md)
then serialize a bounded narrow base plus sorted exceptions. The 16-byte CRC
header and all escapes are paid: motion bytes fall from the raw budget of 7,601
per window to 1,705 / 2,926. Independent parsing checks all 24 maps and 267
exceptions without calling the encoder. Pixels remain those of the wide probe.

The final prospective gain is still below 1%, while fully paid Python source
work is approximately 262 / 420 ms, including about 8 ms for motion packing.
The probe uses frozen accepted narrow references; its trial reconstructions do
not become later references. A new bounded frame profile and causal qualification
are required. Existing GM27 bounds and compatibility remain unchanged.

## FPGA: overlap work before adding more arithmetic

[The bank schedule](../experiments/python-game-schedule-v32-study/README.md)
uses v31's measured no-stall stage costs: load 64 cycles, compute 0/4/132 for
zero/DC/general blocks, output 64. One bank exactly reproduces all four retained
RTL component-frame controls. Two or three banks allow ordered independent stages
to overlap while keeping a bank reserved until its final output.

| Band-control window | One bank mean / worst ms | Two banks mean / worst ms | Three banks mean / worst ms |
| --- | ---: | ---: | ---: |
| Primary | 11.78 / 14.81 | 6.20 / 7.94 | 5.83 / 7.24 |
| Complex | 13.71 / 16.70 | 7.39 / 8.87 | 6.76 / 8.22 |

Every time above assumes an **unclosed 100 MHz clock**. There is no new RTL in
this experiment. Two / three banks need 1,216 / 1,824 bytes of logical block
payload, excluding flags, DSP registers, port replication and physical mapping.
All 864 schedules from 2,332,800 decoded blocks enforce stage and bank exclusion.
Independent ports, unchanged stage service and no external stalls are assumptions.
Entropy, dequantization, fractional prediction/reference fetches, color/HUD,
CRC/commit, RF/QSPI and display service are outside this component model.

## Fair comparison with HEVC and AV1

All candidates receive the **same actual new HUD size per frame and 60-byte
binding budget**. The sampled standard point must meet or beat custom mean MSE
and fit the per-frame cap. Key cadence, source conversion and active geometry
are inherited from the retained low-delay v24 standard campaign. These are
prospective complete budgets, including native access units and once-only codec
extradata, not an implemented standard-plus-HX32 endpoint.

| Window | Custom v30 strict base + new HUD | HEVC + same HUD | AV1 + same HUD |
| --- | ---: | ---: | ---: |
| Primary Mbps at 30 fps | 2.761715 | 1.749285 | 1.667850 |
| Primary active MSE | 14.386886 | 11.210939 | 12.248229 |
| Complex Mbps at 30 fps | 5.842370 | 3.531640 | 3.505915 |
| Complex active MSE | 26.303889 | 22.161878 | 19.767521 |

HEVC and AV1 still use approximately 37–40% fewer complete bytes at these sampled
points while delivering better mean MSE. This is not matched-quality BD-rate,
perceptual equivalence, a full rate-distortion curve, or a comparison of fitted
FPGA decoders. The new HUD savings benefit the standards equally. No compression
superiority claim follows from simpler custom hardware or a projected clock.
The [independent audit](../experiments/python-game-audit-v32-study/README.md)
retains the exact accounting and operating-point selection.

## Next experiments and promotion gates

1. **Reduce host trial work without changing winners.** Integrate the v30 exact
   context counter with shared immutable motion/transform analysis. Update run/DC
   contexts after each edit; compare every final packet, winner, pixel and paid
   work against exhaustive selection. First target exact equivalence, then screen
   candidate blocks using prediction confidence rather than searching everywhere.
2. **Exploit game structure with bounded decoder operations.** Prototype shared
   camera-motion predictors and sparse local exceptions, explicit SKIP runs, and
   bounded screen-copy/palette modes for HUD-like blocks. Give HEVC/AV1 the same
   HUD and geometry. Accept modes only when actual serialized whole-body bytes,
   causal visual error and decoder reference traffic improve together. Wider
   search and smaller residuals alone did not deliver a large gain here.
3. **Validate temporal quality and generalization.** Add longer unseen gameplay,
   camera pans, effects, scene cuts and UI transitions. Report error tails and
   temporal variation, not only mean MSE. Test reference loss, reset and bounded
   recovery. Keep lossless UI and resolution as explicit product constraints.
4. **Implement the two-bank RTL path and bounded entropy reader.** Reuse v31
   integer and handshake goldens, then add randomized backpressure/reset and
   memory arbitration. Measure actual cycles, DSP/LUT/BRAM/ports, post-route clock
   and complete entropy-to-pixel service before choosing three banks or more DSPs.
5. **Integrate the useful HUD mode only through a negotiated new profile.** Bound
   tables and lengths, bind references, retain fallback, and publish only verified
   frames. Run native Sunshine encoder and FPGA decoder against Python goldens;
   validate ESP32 SRAM/DMA/credit behavior under concurrent Wi-Fi and QSPI traffic.

The application-specific opportunity is a better **quality/latency/resource**
operating point on this host–ESP32–FPGA system. Beating HEVC/AV1 rate at equal
quality is an additional goal requiring evidence, not an assumption. Preserve the
working JPEG pipeline and frozen v20 hardware handoff while pursuing it.

## Reproduction and retained proof

```sh
python experiments/verify_prototype_v32.py
```

Use the study environment with NumPy. Component READMEs give individual test and
benchmark commands. The manifest freezes prior v31 inputs, new source/packet
archives, test logs, source pins and deterministic replay helpers. There are
**41 focused passing tests**, 288 accepted causal packets, 1,504 attempted
encodes and 6,082,560 exact causal HUD words. The controller replay checks
7,614,000 block guards and 96 exact v30 control packet/ACK/pixel matches.
Component replay separately verifies 96 lossless HUD frames, 24 wider motion
maps and their actual WV32 packets. Native ESP32 execution, full FPGA fit, RF/QSPI
contention, physical 30 fps and HEVC/AV1 parity remain unproved.
