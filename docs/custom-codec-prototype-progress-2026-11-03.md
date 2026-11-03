# Custom streaming codec: Python prototype progress

This continues the [codec plan](codec-development-audit-plan.md), rather than
ending the custom-codec track when JPEG wins an experiment. Work remains on
the paired study branches. The new evidence is software correctness and
conditional architecture modeling; no new firmware or bitstream is installed.

## Steps now exercised

| Plan step | New evidence | Decision |
| --- | --- | --- |
| Stronger spatial prediction | [MED and above predictors](../experiments/python-predictor-study/README.md), exact quantized reconstruction, four primary/held-out windows | MED improves DPCM substantially; JPEG still wins rate/quality |
| DSP-oriented transform | [FT01 fixed-Q14 DCT/IDCT](../experiments/python-transform-study/README.md), bounded coefficient syntax, exact host reconstruction | Fits the sample size cap, but its simple entropy format loses to JPEG |
| Bounded display pipeline | [Finite delivery model](../experiments/python-delivery-study/README.md), compressed-slot/front/back/reference roles, loss/overload tests | Two slots help overlap; modeled rate/age depend on service, jitter and phase |
| Streaming memory layout | FT01 [decoded-sample stripe oracle](../experiments/python-transform-study/stripe_model.py), exact full-plane interpolation comparison | Small sample footprint is possible under a row-availability contract; compressed syntax/scheduling are still missing |
| Temporal/motion codec | Earlier changed-tile parser plus new finite predecessor-loss tests | Motion compensation is still to implement; reference recovery must precede adoption |
| Target RTL and hardware | No new implementation evidence | Selection, target fit, real memory/link service and board tests remain open |

The new suites contain **31 passing tests**: six predictor, twelve finite
delivery and thirteen transform/layout tests. They include negative cases;
passing an error-rejection test is not a successful video-streaming run.
The earlier 57-test codec/memory evidence remains separately archived.

## Quantitative results

For complete 60-frame primary windows, q2 MED projects to16.852/16.182 Mb/s
at34.54/35.55 dB active RGB565-output PSNR. Original q2 DPCM was27.229/28.095
Mb/s with identical reconstructed pixels: roughly38–42% fewer wire bytes.
JPEG q65 on the same windows is6.812/4.137 Mb/s at34.67/35.80 dB. Predictor
work therefore earns a custom-baseline improvement, not a JPEG replacement.
The separate held-out windows reproduce that ordering. The combat samples
contain repeated source images, all explicitly counted in the manifests.

The transform comparison uses **12 exact matching frames per window**, rather
than mixing those subsets with the full predictor aggregates:

| Window | FT01 scale16 Mb/s / PSNR | Receiver JPEG q50 Mb/s / PSNR |
| --- | --- | --- |
| Combat primary | 9.754 /33.25 dB | 5.969 /33.30 dB |
| Second clip primary | 7.599 /34.74 dB | 3.540 /34.74 dB |
| Combat held-out | 9.772 /33.27 dB | 5.989 /33.32 dB |
| Second clip held-out | 7.566 /34.72 dB | 3.524 /34.73 dB |

All144 transform packets (three scales ×48 inputs) fit48 KiB; maximum48,649
bytes leaves little storage margin. Raw coefficient fallback can exceed the
existing256 KiB limit, so sample success is not a general cap guarantee.
These are precompressed clips, not native game capture or perceptual acceptance.
Projected30 fps wire rates exclude RF/link-layer, retries, audio and input.

At720×480 YUV420, the naive separable receiver IDCT costs8,294,400 MACs/frame,
or248.832 million MACs/s at30 fps. Accepted coefficient extremes require up
to37 signed accumulator bits. This identifies useful DSP arithmetic and safe
range bounds; it does not establish inferred DSP count, clock, fit or latency.

The sample-layout oracle retains at most18,000 bytes for16 luma rows and
nine chroma rows per plane at720 pixels, including bilinear lookahead, versus
518,400 bytes for whole decoded YUV420 planes. It matches the full-plane RGB
kernel exactly over boundary/random tests. This count excludes coefficient/
IDCT workspace, output buffers, FIFOs/control and Python temporaries. It
assumes the required predecoded rows are available; FT01's plane-first wire
order cannot provide them without a changed schedule/syntax or retained data.

The finite delivery baseline repeats each60-frame JPEG **size trace** for
1,800 scheduled IDs. With assumed2 ms preparation, ideal8 Mb/s network,
160 Mb/s QSPI,8 ms decode and two slots, it achieves30.0 simulated IDs/s in
the predeclared5–55 s window. The strict60 s count is1,799/1,800. One slot
reduces combat to26.5 fps;40 ms decode limits output to25 fps. Those results
do not execute the decoder or establish hardware FPS.

The128-case phase/jitter sweep has no dropped IDs, but one steady-count
failure (1,499/1,500), p95 age up to59.33 ms even at assumed8 ms decode,
and50 ms presentation gaps. With20 ms decode, p95 age reaches72 ms. Preserve
these failures when discussing the otherwise successful baseline schedule.

## Next custom-codec work, in order

1. **Improve coefficient syntax while freezing pixels.** Separate DC from AC,
   test row-reset DC prediction, band/block-local Rice parameters and bounded
   zero/EOB contexts. Compare exact same quantized coefficient arrays and
   reconstructed hashes against FT01 and receiver JPEG. Include all headers,
   context resets, escape/RAW tails and parser state costs. These are familiar
   codec tools, not claims of a novel compression algorithm.
2. **Define an MCU/stripe transport order.** Prototype luma/chroma/IDCT row
   availability, bilinear lookahead and bounded coefficient/sample FIFOs.
   Turn the sample-layout oracle into an actual byte-driven decoder before
   counting its small footprint as a system benefit. Freeze region lengths,
   CRC, reset points, truncation/abort and complete-frame publication rules.
3. **Then test host motion estimation with one reconstructed reference.**
   Start with bounded integer translation/block COPY and coded residuals,
   with explicit vector ranges and out-of-frame rules. Charge SDRAM reads,
   overfetch and unchanged-region construction. Name committed references,
   model lost data/ACK/reset and bounded independent refresh; no guessed
   reference or front-buffer mutation is acceptable. Synthetic dependency
   tests currently show17 losses causing313 extra rejections.
4. **Measure a closed-loop quality/age policy.** Use genuine native30 fps
   captures when available, more held-out games, a defined wire/peak budget
   and finite feedback delay. Keep host encoding, ESP32 forwarding, decode,
   memory and presentation observations separate. Compare JPEG, the selected
   custom candidate and pinned low-delay standard-codec software baselines
   at matched quality/rate, with HUD/temporal inspection as well as PSNR.
5. **Select before RTL.** The current candidates have not earned the plan's
   advantage over JPEG. Require measured benefit plus a bounded streaming
   memory/parser schedule, then synthesize/place/route the actual target and
   test physical service/latency. Continue existing JPEG integration alongside
   this research; do not destabilize its firmware/service to test a new format.

The [provenance snapshot](prototype-v2-provenance.json), result manifests,
scripts and test logs make this iteration reviewable. Source captures are
outside Git; their exact file hashes/PTS/canvas hashes remain in the artifacts.
