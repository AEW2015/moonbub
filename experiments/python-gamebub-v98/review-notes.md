# Independent V98 comparison review

Reviewed `scripts/cu66-v98/compare.py`, `metrics.py`, `source_prepare.py`, the
source manifest and `standard_controls.py`. This review did not run the full
benchmark or modify its executed code. The root agent owns the sequential
benchmark and final source/stream audit.

The pooled region MSE/PSNR, RGB565 expansion, worst-frame PSNR and temporal
error arithmetic are correct. The temporal measure is the change in RGB
reconstruction error between adjacent selected frames, not motion-compensated
quality or a time-normalized cross-clip metric. The frontier correctly compares
actual coded bytes, active MSE and ROI MSE within each source; it does not
interpolate three sampled quality settings or infer hardware cost. Codec
quality parameters are different units and should only be compared through
their measured rate/distortion points.

Concrete findings and handling:

- Initial encode/decode timing distributions had unequal scopes: GM01 includes
  canonical color conversion, while native call timing separates it. The root
  added frontend/backend sums and explicit timing scope before freezing the
  run. Opening, flushing, verification and artifact work remain separately
  identified. Native elapsed fences describe unpaced processing of preloaded
  frames, not capture-to-display latency or FPGA cycles. Individual timing
  samples from one ordered host run do not establish stable performance ranks.
- The initially inspected manifest was stale, had three sources and full-canvas
  game ROIs, which would leave an empty background mask. The source agent
  regenerated the four-source corpus before the root froze benchmark inputs.
  Final audit should require the manifest preparation script hash to match its
  retained source snapshot and verify every frame and NPZ hash.
- Native timestamp differences in the original two sources are exactly
  `25/747` seconds (29.88 fps) and `1/25` seconds (25 fps). The new source's
  every-second-frame selection implements 60-to-30 fps decimation without
  interpolation or duplicate scheduling. The final independent audit should
  require every selected timestamp difference to equal the reciprocal of the
  recorded selected rate. The rate metric uses that selected cadence; its
  separately labeled hypothetical 30 fps conversion is arithmetic, not
  measured target delivery. Different selected cadences also mean different
  temporal spans and must not be pooled as one source.
- Synthetic panel ROI rectangles exclude the right/bottom one-pixel boundary
  of Pillow's inclusive drawing endpoints. The root will describe these as
  interior panel probes. They are not exact full-panel masks or OCR/readability
  measurements. The game rectangles have no verified HUD semantics.
- Native header inspection records FFmpeg's return code but does not make a
  nonzero return code fail `standard.run` or the comparison. Final audit must
  require successful inspection and relevant emitted syntax before drawing
  header/filter/reference conclusions. A failed inspection does not invalidate
  a separately verified actual byte and decoded-quality ledger, but it leaves
  those syntax conclusions unsupported.

Packet accounting includes actual emitted elementary bytes plus separately
retained encoder extradata. GM01 counts complete packets including outer and
nested headers/CRCs; its stream offsets delimit the exact concatenation. The
native record key flag is named `is_keyframe`, whereas GM01 uses `is_key`;
audits must handle both. No mux, network, feedback, FEC or retry bytes are
included. A 49,152-byte exceedance count is diagnostic; it does not mean that
the benchmark silently caps, drops or adapts those packets. PTS association,
complete decoded outputs, flush output, frame-emission lag and final source
hashes are retained or checked. For low-delay conclusions, inspect decoder
output availability as well as encoder packet emission; these are distinct.

An honest V98 promotion is the reproducible common-input research comparison
and its measured per-source frontier, with explicit standard syntax and host
runtime evidence. It is not a new custom wire or physical decoder promotion.
GM01 is an older executable fresh-RGB control. Its immutable key, quantization,
motion and reference policies do not establish current CU66 behavior. The
current CU66 fresh-input encoder gap remains open: an executable actual current
encoder must accept the same fresh RGB, emit its full bounded packets and
verify current receiver reconstruction before any current-custom rate/quality
gap, standard-equivalent cost, or FPGA throughput claim is promoted. Frozen
CU66 decoded vectors and later packet repacking cannot fill that gap.
