# V29: application-specific motion effort and exact entropy costing

V29 keeps 720×480 coded / 720×405 active video and GM27/CP27/JA27 syntax.
The useful new operating point is **quiet-block motion-search gating** on the
host encoder. A second prototype supplies an exact EC26 size counter, but its
guarded whole-plane residual selector is a measured negative result.

These are Python design experiments on 96 retained source images from two Mass
Effect windows. They advance a custom host → ESP32 transport → FPGA decoder
pipeline; they do not install native Sunshine code, ESP32 firmware, or RTL.

## Full causal comparison

Four policies each process 48 frames from each window, with separate accepted
decoded reference histories. The policy order rotates each source frame.
Key frames are IDs 0 and 24. The control repeats v28 mixed sampled search and
lazy entropy selection. The new conservative policy screens each block with
stride-4 weighted source-versus-reference MAE; blocks at MAE ≤ 2 retain zero
motion, and active blocks perform the same stride-4/stride-2 bounded search.
The threshold was fixed before inspecting corpus results.

| Window | Policy | Complete body Mb/s at nominal 30 IDs/s | Active MSE | Base-policy service ms/frame |
| --- | --- | ---: | ---: | ---: |
| 2600 | V28 mixed control | 2.706105 | 14.213686 | 277.32 |
| 2600 | Quiet-block gating | 2.765395 | 14.395686 | 148.81 |
| 7200 | V28 mixed control | 6.175390 | 26.318948 | 301.16 |
| 7200 | Quiet-block gating | 6.166030 | 26.339495 | 210.56 |

Measured base-policy work is **1.86× / 1.43× faster**. The first window pays
**2.19% more complete bytes and 1.28% higher MSE**. The harder window uses
**0.15% fewer bytes and 0.078% higher MSE**. These are speed/quality operating
points, not perceptual equivalence or compression parity with HEVC/AV1.

Each accepted frame retains exactly 21,120 RGB565 HUD words. All 384 accepted
complete CP27 packets fit the 49,152-byte bound; maxima are 25,898 and 45,405
bytes in the two windows. All 752 winning/losing candidate encodes remain
recorded. No coarse quantizer fallback was required. The repeated mixed control
reproduces all 96 corresponding v28 CP27 packets, ACKs and metrics exactly.

Base-policy service pays all analysis, attempted encodes, full source RGB565
quality evaluation, and binding checks. It excludes fixture acquisition/color
conversion, preencoded HUD generation, offline debug decoding, archive I/O,
network waits and display presentation. Receiver service is separate. The same
29.88 fps source images are reused across policies; nominal 30-ID byte rates
are projections of actual serialized CP27 bytes, excluding ACKs and transport
framing. They are not measured real-time endpoint rates.

## What the quiet-block optimization actually saves

Every pixel still participates in prediction, transform, coefficient coding
and final reconstruction. Quiet blocks retain zero vectors; they do not omit
residuals or freeze displayed pixels. Screening uses the current source and
that policy's last accepted decoded reference, never future source images or
another policy's reconstruction.

| Window | Quiet / evaluated P blocks | SAD sample differences, control → gated | Logical search reference gathers, control → gated |
| --- | ---: | ---: | ---: |
| 2600 | 14,422 / 15,870 | 269,762,400 → 26,650,848 | 716,882,400 → 68,353,248 |
| 7200 | 9,667 / 15,870 | 269,762,400 → 107,675,136 | 716,882,400 → 283,671,936 |

Those reductions include every screening sample: **90.12% / 60.09% fewer SAD
differences** and **90.47% / 60.43% fewer logical gathers**. Array construction,
source copies, indexing, transform work, validation, hashing and output writes
are additional. These are host search counts, not FPGA external-memory traffic.

The short matched-reference probe initially suggested 0.76% fewer bytes for
the conservative gate. The complete causal primary window instead grows 2.19%.
That difference matters: candidate selection changes the next reconstructed
reference and cannot be qualified from isolated frame comparisons alone.

The stride-4 screen can miss small or alternating features. The controller's
full-source RGB error guard compares against the current zero candidate, not
the prior mixed controller or a perceptual threshold. It therefore does not
promise the control's quality. Dense fallback, camera cuts and fine-detail
regions need a broader corpus before selecting this as a product default.

## Exact EC26 size counter: useful foundation, rejected selector

The counter mirrors the actual codec: row-reset DC deltas, zigzag sparse-band
runs, Rice parameter minimization and escape costs, per-stream byte padding,
raw fallback, header and CRC. It supports both layouts for counter verification;
the emitted GM27 profile remains block-major layout 0. It computes lengths
without allocating bit strings or serializing a trial packet.

On 24 matched-reference frames, all **144** selected-plane/layout size checks
match actual serialization. Mean counter versus serialization time is
**0.914 vs 1.608 ms** and **1.089 vs 3.373 ms**. This compares a length-only call
to construction of the same coefficient packet, not whole-encoder speed.

The selection prototype first reproduces v28 coefficients, then considers each
unique original/pruned plane. Exact combined legacy/EC26 cost chooses among
candidates whose clipped source YUV SSE is no greater than the incumbent.
Every alternative reconstruction and counter is paid. The integrated controller
also retains its actual current-source RGB guard.

**No alternative planes won**, either in the probe or all four full causal
EC-control cohorts. Complete packets and output pixels remain identical to
their corresponding non-EC policies. Nevertheless, full base-policy service
grows from 277.32 to 345.69 ms and 301.16 to 373.73 ms on mixed search, and
from 148.81 to 217.39 ms and 210.56 to 283.94 ms with quiet gating. The causal
campaign pays 2,232 EC26 size-counter calls. Keep this selector as a negative
control; **do not deploy it as the default optimization**.

A correct rate oracle cannot create better candidates. The next compression
experiment should change bounded block/band decisions and their run/DC context,
then measure actual rate and displayed error over causal histories.

## Next steps toward an application-specific codec

1. Generate a small declared menu of block/band residual candidates. Protect
   the exact HUD and important UI regions; allow controlled high-band reduction
   in moving backgrounds. Use the exact EC26 oracle and actual decoded RGB565
   quality, not CP02 proxy bytes alone. Pay every candidate and any fallback.
2. Test adaptive search confidence beyond a single quiet threshold. Sample
   phases, high-frequency/source error, scene changes and actual residual cost
   should trigger a bounded denser fallback. Compare full causal rate/quality
   frontiers; reject policies that merely hide work or quality loss.
3. Extend to fresh long gameplay, camera pans, fine UI text and scene cuts.
   Report frame-error tails, temporal flicker and actual packet-size tails;
   these two short reused windows cannot establish gameplay experience.
4. Port the selected host policy to native code using the retained GM27 packet
   goldens. Keep search on the PC. The ESP32 should transport bounded packets
   with negotiated credits/reset, rather than run these NumPy transforms.
5. Implement and qualify bounded FPGA coefficient reconstruction and exact
   tap arithmetic against goldens. Measure DSP/BRAM/SDRAM arbitration, frame
   publication fences, RF/QSPI service and presented frame age under contention.
   A Python array/operation count is not synthesis or a memory timing proof.

The new Python service times remain roughly 4.5× / 6.3× the 33.33 ms frame
budget before capture, HUD and transport. Native implementation and hardware
qualification remain necessary. Preserve the JPEG path and frozen v20 hardware
handoff while this experimental custom codec develops.

## Reproduction and audit

```sh
python experiments/verify_prototype_v29.py
```

The package binds inherited source snapshots and all new sources, actual
candidate/accepted packets, logs, integer source metrics and replay outputs.
All 17 focused tests pass: four adaptive-search, five entropy-counter/selection,
four controller-admission and four independent-audit tests.
The controller verifier decodes every candidate and accepted reference chain,
recomputes full source metrics and all exact HUD words, checks policy/admission,
reconciles every measured service total, and independently derives quiet masks
and scored sample counts. Component verifiers repeat counter/selection and
fixed-reference probes. A separate Luna audit checks retained framing, lineage,
selection and accounting. This is offline Python evidence; no native or physical
30 fps result, resource fit, or HEVC/AV1 parity is asserted.
