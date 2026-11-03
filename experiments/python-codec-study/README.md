# Python codec and delivery design study

The [follow-up results and next custom-codec steps](../../docs/custom-codec-prototype-progress-2026-11-03.md)
add MED prediction, fixed-point transform/stripe prototypes and finite-buffer
delivery with capture-phase/jitter sweeps. This directory preserves the first
iteration's sources and artifacts.

This implements the software comparison stage of the
[codec plan](../../docs/codec-development-audit-plan.md), paired with the
[memory-service model](../python-memory-study/README.md). Keep JPEG as the
gameplay control. These are executable architecture experiments, not new
Sunshine modes, ESP32 firmware, FPGA decoders or hardware FPS measurements.

## Implemented methods

* `codec.py`: bounded 16×16 RAW, FILL, RLE, palette and channel-wise spatial
  DPCM/Rice tile selection. Little-endian versioned frames, lengths and CRC;
  RAW fallback limits expansion. Channel prediction resets at each tile row.
  Independent decoding checks runs, Rice escapes, channels, padding and bounds.
* `index_codec.py`: code compact quantization-level indices instead of
  dequantized RGB565 values. This removes redundant residual bits and preserves
  **exactly the same reconstructed image**. Power-of-two steps need shifts and
  saturation in a prospective receiver, rather than multipliers.
* `zero_run_codec.py`: bounded zero-residual runs address Rice's minimum one
  bit per channel sample. Compare this extension before adding more elaborate
  predictors. It keeps the existing tile modes and RAW fallback.
* `temporal.py`: send a compact mosaic of changed tiles against the exact
  previous reconstructed image, with an independent frame every 30 frames in
  the benchmark. The stateful receiver owns its reference and rejects stale
  epochs, replay/regression, incomplete packets and wrong predecessors.
* `budget.py`: try at most five receiver-profile JPEG qualities, accepting
  only a complete image that fits both a compressed-memory cap and an ideal
  per-frame wire budget. Default: q80/q65/q50/q35/q20, 48 KiB, 8 Mb/s at 30 fps.
  Otherwise drop the whole frame. A receiver encoder's >256 KiB rejection
  also advances this search; unrelated validation errors propagate.
* `pacing.py`: nonpreemptive ideal network serialization, latest-waiting-frame
  versus FIFO, QSPI and decoder stages, refresh phase and latest-per-vblank
  publication. Temporal dependencies are checked: dropping a predecessor
  invalidates dependents until an independent frame arrives.

All spatial quantization is explicit preprocessing of separate R5/G6/B5
channels: `min(((v + q//2)//q)*q, maximum)`. It is not packed-word DPCM or
closed-loop temporal quantization. Lossless means exact relative to RGB565 at
q1. Other steps are lossy. CRC detects accidental corruption; it provides no
authentication. The reference owner is a Python oracle, not a physical
write-drain or ACK implementation.

## Reproduce

Use Python 3.14 and the versions in `requirements.txt` for the recorded
environment. Other versions need new provenance/results. Clone the paired
Sunshine study branch and set its tools location; do not start its service:

```sh
python3.14 -m venv .venv
.venv/bin/pip install -r experiments/python-codec-study/requirements.txt
export GAMEBUB_SUNSHINE_TOOLS=/path/to/Sunshine/tools/gamebub
cd experiments/python-codec-study
../../.venv/bin/python -m unittest -v
../../.venv/bin/python benchmark.py --frames 60 --media-dir /path/to/media
../../.venv/bin/python benchmark_index.py
cd ../python-memory-study
../../.venv/bin/python codec_sizes.py
```

The actual local interpreter was
`/home/lori/gamebub-streaming-prototype/.venv/bin/python`. Tests of budget and
benchmark imports need the paired Sunshine Python tools and these dependencies.
The memory model alone uses the standard library. Commands regenerate result
files; archive an existing run before replacing it.

Two inputs are `mass-effect-combat.mp4` and `mass-effect-2600.mp4`, which remain
outside Git. These are already compressed, short Mass Effect samples, not new
Elden Ring captures. Earlier provenance names Noire Blue's
[Mass Effect walkthrough](https://www.youtube.com/watch?v=Z8v7xCIGoQA);
the exact local file hashes, dimensions, cadence, PTS and selected-frame hashes
are authoritative in `results.json`. A fresh download or different extraction
may differ; report a new corpus rather than claiming to reproduce those hashes.

Sixty consecutive native decoded frames are selected starting at one second
from each file; source rates are 25 and 29.88 fps. They are BOX-resampled with
aspect preserved into a 720×480 canvas. The 16:9 content is 720×405 with black
bars. There is no interpolation or frame duplication. A separate 30-frame
synthetic gradient/HUD sequence has a moving white square. It demonstrates
controlled static-region savings, not gameplay. Unique hashes and original
PTS are recorded, including repeated content if a source contains it.

The selected combat window contains **32 unique scaled images in 60 decoded
frames**; the second window has 60/60 unique images and the synthetic sequence
30/30. Repeated source content can favor temporal compression. None of these
counts establishes a native 30-distinct-frame/s source or receiver output.

## Measurement contract

`results.json` contains nine profiles per corpus, full per-frame sizes, output
hashes, quantization/mode or budget decisions, PSNR and schedule projections.
`results-index.json` adds compact-index and zero-run comparisons, with exact
per-frame reconstruction-hash checks against the corresponding q2/q4 baseline.
Hashes bind the inputs, executed sources and related result artifact.

The common quality comparison is RGB565-expanded output against the scaled
RGB source, with both full-canvas and active-content MSE/PSNR. Summary PSNR
comes from pooled MSE, not averaged dB values. JPEG also records quality before
RGB565 conversion. PSNR is pixel error, not visual/HUD/temporal acceptance;
neither SSIM nor a perceptual threshold is established here. The compressed
sources and brief windows limit generalization. Synthetic and video rows are
kept separate.

The parser, quantizer, malformed-packet, replay/reference, budget and timing
boundary regression suite records 45 passing tests in `tests.log`. The separate
memory suite records 12 passing tests. Those counts include expected failure
conditions checked by passing tests, not hidden successful streaming runs.

“Projected wire Mb/s at 30 fps” is mean frame bytes replayed at a hypothetical
30 fps, including 40 application and 28 IPv4/UDP bytes per 1,024-byte chunk.
Custom formats use this hypothetical MSV1-sized envelope, not an implemented
protocol. Native-rate and selected-PTS-rate calculations are separate. RF,
link-layer framing, ACK/retry, audio and input bandwidth are excluded.

Schedule projections assume capture/encoding take zero time, an ideal selected
network rate, 160 Mb/s QSPI, **assumed 8 ms decoding**, and hypothetical 60 Hz
refresh at two capture-start phases relative to a fixed vblank clock. The
actual panel/raster conflict remains open.
Only the transmitter has a bounded waiting slot; receiver-stage queues are
abstract and unbounded. Decoder time is a scenario parameter, not derived from
the Python timings. Models for network and SDRAM are separate experiments,
not a composed system proof. Same-vblank candidates are superseded rather than
double-counted. Strict windows are `[0, N/30)`; eventual completion during
drain never becomes a strict-window pass.

Python timings exclude source decode/scale and initial RGB565 packing. Encode
timings include the selected method's quantization/search. Decode timings end
after the parser/reconstruction returns; JPEG includes RGB image decoding but
its final RGB565 packing is outside that timer. They have no warm-up/isolation
guarantee and are reference-program costs, not estimates of ESP32/FPGA speed.

## Results and decisions

For the two video windows, the default JPEG wire-budget search selects q65 on
all 60 combat frames and q80 on all 60 second-clip frames. Complete images fit
48 KiB and 8 Mb/s's per-frame wire bound without dropping. This is a small
offline policy check; the search is not integrated into Sunshine capture and
can cost several encodes per frame. Noise may exhaust all candidates and must
be dropped. Quality fluctuation needs its own visual evaluation.

| Method | Combat projected Mb/s | Combat active PSNR | Second clip projected Mb/s | Second active PSNR |
| --- | ---: | ---: | ---: | ---: |
| JPEG q65 | 6.812 | 34.67 dB | 4.137 | 35.80 dB |
| JPEG q80 | 8.345 | 36.18 dB | 5.407 | 36.40 dB |
| DPCM q2 | 27.229 | 34.54 dB | 28.095 | 35.55 dB |
| Compact-index DPCM q2 | 24.376 | 34.54 dB | 25.846 | 35.55 dB |
| Compact-index + zero runs q2 | 24.139 | 34.54 dB | 24.914 | 35.55 dB |
| Temporal changed tiles q2 | 7.396 | 34.54 dB | 16.144 | 35.55 dB |

Compact-index coding saves 8.0–23.0% wire bytes over original DPCM across the
two gameplay windows and q2/q4, with identical reconstruction hashes. Adding
zero runs brings savings to 11.3–23.3% over that original baseline. The best
q4 zero-run rates are still 19.011 and 16.817 Mb/s, at just 29.04/29.77 dB.
All 60 frames in every gameplay index/zero-run case exceed 48 KiB. These
candidates therefore fail the selected storage/rate goal and do not justify
a replacement FPGA decoder. Improving their predictor may help, but is not a
measured JPEG advantage.

The synthetic gradient's palette/RLE modes already dominate much of its
coding; compact indices alone slightly increase packet size there. Zero runs
also improve it only slightly. ZR01 has 16 fewer framing bytes than IQ01, so
that small constant must not be attributed to residual-run coding. All saved
bytes, header costs and unfavorable cases remain in the result artifact.

The temporal combat mean is below 8 Mb/s but includes a 110,999-byte maximum
frame. At an ideal 8 Mb/s, latest-slot replacement breaks its reference chain:
only two of 60 frames decode in the modeled sequence. The synthetic temporal
mean is just 0.692 Mb/s, yet its initial independent image delays/drops a
predecessor and has the same recovery problem. Small average size is therefore
insufficient. A bounded recovery protocol, startup policy and refresh/peak
budget must precede a temporal hardware design.

The independent JPEG budget profile transmits all 60 frames in each ideal-link
case, but only **59/60** meet the fixed two-second display window; the last
appears at/after its endpoint. That is an explicit failed strict-window count,
not a 30 physical fps demonstration. A latency-compensated steady-state cadence
test would be a different predeclared experiment.

Preserving unchanged regions by copying the full reference costs 1,382,400
bytes per dependent frame, plus changed-pixel writes. At 30 dependent frames/s
the copy alone is 41.472 MB/s, before scanout and ingress; the benchmark's one
independent frame in 30 reduces its copy average to 40.0896 MB/s. Python's extra immutable snapshot
is separately labeled and is not an FPGA requirement. Tile indirection might
avoid copies, but needs a bounded lifetime/scanout design.

See the normalized-index/zero-run measurements in `results-index.json` and
the linked memory report before choosing the next candidate. A coding gain
over a weak custom baseline does not establish an advantage over JPEG.

Next gates: extend held-out source scenes/native captures; agree quality and
peak/age limits; compare the improved residual syntax at matched quality;
include complete-frame refresh bursts and finite receiver/reference queues;
then choose whether any custom codec earns RTL work. Keep the existing JPEG
receiver and SDRAM path as the control while hardware teams qualify actual
memory, concurrent Wi-Fi/QSPI, target fit and display ownership.

For FPGA compute mapping, these residual/index/run operations mainly need
adders, comparisons, shifts and bounded parsing. Assigning DSP multipliers to
them adds no demonstrated benefit. Transform/IDCT, color conversion and scaling
are the useful multiply-intensive candidates; the existing JPEG decoder is
already a relevant DSP-based control. Any DSP optimization must be measured
with the complete memory/display path and target synthesis/timing, rather than
inferring speed from Python or a nominal multiplier count.
