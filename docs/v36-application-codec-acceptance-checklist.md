# V36 application-specific codec acceptance checklist

Use this checklist before describing an application-specific profile as a codec
win. A smaller packet at worse reconstruction quality is a rate/quality trade,
not a compression victory. The v35 figures below are context, not acceptance
thresholds: guarded core8 reduced complete bytes 4.3280% / 3.0917% while active
MSE increased 0.04694% / 0.17166%; sampled HEVC and AV1 on that same trace used
fewer bytes at lower MSE.

## Canonical hidden-reference experiment

- [ ] Define a new negotiated profile/tag and freeze its normalization rule.
- [ ] For each input, run canonical-control and hidden-residual-skip variants
  from identical initial state. Both normalize every fully hidden,
  support-safe reference tile identically after reconstruction.
- [ ] Over every causal frame, compare complete normalized reference planes,
  visible decoded pixels, and next-frame predictor inputs byte-for-byte. Any
  mismatch fails the exact-equivalence claim; compare full state hashes and
  retain per-frame hashes for replay.
- [ ] Confirm visible coefficients, predictor decisions, HUD composition and
  all non-hidden reconstruction are identical. Validate tile eligibility with
  boundary, clamping, odd-rectangle, overlap and chroma-support cases.
- [ ] Retain every frame, packet, rejection and losing candidate, plus an
  independent decoder/replay verifier. Report peak and temporal error as well
  as means; extend beyond the two retained short windows to held-out gameplay.
- [ ] Report quality of the canonical profile separately against the original
  profile and original source. Equality between the two new variants does not
  establish unchanged quality versus old reference semantics.

## Fair codec comparison

- [ ] Feed custom, HEVC and AV1 the same timestamped processed source frames,
  including any precodec mask or other source transform. Publish source hashes
  and transform configuration; credit identical processing to every codec.
- [ ] Hold active/coded geometry, frame cadence, exact 21,120-word RGB565 HUD,
  color conversion, crop, and display composition constant. Decode all outputs
  and measure quality against the same original RGB source after the same HUD
  overlay.
- [ ] Count complete transmitted bytes per frame: codec payload, packet/frame
  headers, binding, once-only sequence extradata, HUD and required padding or
  integrity fields. Show both total bytes and component accounting; verify
  measured totals equal the serialized packet sizes.
- [ ] Match quality before claiming bitrate/compression advantage. Sweep useful
  operating points and compare rate at the same quality constraint (including
  visible and temporal error limits); preserve all points that miss quality or
  frame caps. If no matched-quality point exists, state that compression
  superiority is unproved.
- [ ] Record per-frame and aggregate active-region MSE/PSNR plus peak, tail and
  temporal error. Do not let a good mean conceal a bad frame or scene cut.
- [ ] Verify standard-codec AUs decode with expected PTS/DTS, keyframe behavior,
  and immediate low-delay output. Disclose encoder settings and that sampled
  points do not establish an optimal standards encode.

## Timing and deployment evidence

- [ ] Label every timing scope: preprocessing/source analysis, candidate search,
  encode, serialization, HUD, queueing, packetization, and end-to-end service.
  Include setup and all paid losing work in the scope claimed; distinguish
  already-paid cached maps from a complete sender path.
- [ ] State machine, host, repetitions, load and percentile for each timing.
  A host component speedup cannot be multiplied into a sender or 30 fps claim.
- [ ] Measure ESP32 transport separately: actual target CPU/heap, DMA and copy,
  Wi-Fi contention/retries, QSPI/display traffic, credits and backpressure.
  Transport measurements alone do not establish codec decode performance.
- [ ] Keep FPGA implementation unproved until the complete decoder is measured
  with fitted resource use, routed clock, external-memory arbitration, reset,
  commit/publication fences and sustained frame cadence on the target design.
- [ ] Claim physical 30 fps only after sustained end-to-end capture-to-display
  runs meet the frame deadline and quality gates on target hardware.

## Advantage hypotheses to test

Application-specific gains may come from predictable HUD/occlusion structure,
bounded game-motion search, reusable exact motion maps, compact coefficient
syntax, or avoiding work on hidden samples. Measure each contribution inside a
single complete sender/decoder budget and against equally processed HEVC/AV1.
The v35 13.22× cached-map result is a component result with maps already paid;
it motivates native whole-sender measurement but is not itself a compression or
throughput advantage. Preserve negative results and leave JPEG/v20 unchanged
until the new profile passes these gates.
