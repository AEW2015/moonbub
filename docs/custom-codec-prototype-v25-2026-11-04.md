# Iteration25: stronger temporal prediction and exact HUD coding

The new Python codec reduces complete video/HUD bytes by **31.3% /33.3%** on
the two retained gameplay windows, at slightly better measured image quality
than the previous custom codec. Resolution stays **720×480 coded /720×405 active**,
and all **21,120 requested RGB565 HUD words** remain exact in every frame.
This is progress toward the HEVC/AV1 target, not compression parity or a
physical30fps result. Python encoding remains too slow for that frame rate.

## Measured operating points

Body rates project actual complete encoded bytes to30 source IDs/s, excluding
network overhead. MSE is expanded-RGB565 channel error over the active area;
lower is better. The same fixed `capped_key_zero_rdo1` base policy and full-motion
HD25 HUD policy are used on both windows.

| Window | Previous CP23 body Mb/s | New CP25 body Mb/s | Byte reduction | Previous /new active MSE |
| --- | ---: | ---: | ---: | ---: |
| mass-effect-2600 |4.599835 |3.160445 |31.29% |14.42898 /14.38366 |
| mass-effect-7200 |10.287175 |6.864830 |33.27% |30.08390 /26.89721 |

The fixed policy improves both byte count and mean MSE on these windows. These
are not matched-quality BD-rate measurements, a perceptual-quality guarantee,
or proof that the same setting wins on unseen games. More recent references,
key quantization, entropy dispatch and lossy RDO alter future reconstruction;
do not attribute the whole gain to motion vectors or lossless entropy alone.

The complex window also has a smaller `zero_rdo4` point at6.729880Mb/s,
MSE27.82690, using coarser keys. It meets the old custom mean-quality threshold,
but choosing it only after seeing the whole clip is an offline operating-point
selection, not an implemented adaptive scene classifier/rate controller.

Lower-rate controls remain visible even when they fail quality: the
`zero_roi16_rdo4` policy reaches2.618865 /5.435385Mb/s, but MSE rises to
26.52350 /44.46382. Those points do not meet the old quality floors and do not
establish HEVC-level compression at the intended image quality.

## Fair HEVC/AV1 comparison

Both standards must receive the same improved exact-HUD layer. Comparing our
new HUD against their old HUD would overstate progress. The retained native
v24 access units and actual decoded images are reused; their output HUD pixels
are replaced by the same original words as before. Each projected standard
hybrid pays the actual new HU25 bytes, key resets and the same60-byte binding
budget. This is prospective integration accounting: CP25 still accepts GM25
only, and no Gamebub standards decoder is implemented.

For each new custom MSE threshold, select the smallest retained native setting
that meets or improves that threshold; quality parameters are encoder-specific.

| Window | New custom | HEVC +same new HUD | AV1 +same new HUD |
| --- | ---: | ---: | ---: |
|2600 |3.160445Mb/s, MSE14.38366 |1.750665Mb/s, q32 |1.669230Mb/s, q48 |
|7200 |6.864830Mb/s, MSE26.89721 |3.838135Mb/s, q28 |3.812410Mb/s, q38 |

Those selected native hybrid MSEs are11.21094 /22.16188 for HEVC and
12.24823 /19.76752 for AV1, each below the compared custom point. Passing the
old custom quality floor is distinct from matching a selected HEVC/AV1 image.

The complete-body gap therefore remains approximately **1.8–1.9×**, rather
than disappearing with the HUD improvement. Standards have their own reliable
reference histories and much richer decoder tools; this is an image/byte
comparison, not a matched transport/latency or FPGA complexity comparison.
The frozen v24 targets2.335/5.378Mb/s for HEVC and2.254/5.280Mb/s for AV1 remain
useful absolute milestones, but have different HUD coding and sampled MSE.
The new custom candidate does not meet those rate/quality pairs.

## What changed

**Exact HUD:** HD25 adds byte-plane zero/repeat/literal coding, bounded
R5/G6/B5 component-delta Rice coding, independent intra/left prediction and
±4-pixel global/tile prediction. Actual encoded bytes select among these tools
and the legacy full patch. No DEFLATE or native image codec is used inside the
HD25 wire syntax; zlib is only a retained-artifact storage container.

At fixed continuous HUD histories, full HD25 lowers the projected HUD body from
2.139830→1.520095Mb/s and4.906925→3.096090Mb/s, preserving every source word.
The actual HU25 integration costs slightly more because its header is110bytes
and keys0/24 carry independent HUD updates. Its full-motion totals are310,961 /
623,615bytes across48 frames, or1.554805 /3.118075Mb/s. Do not substitute the
smaller standalone projection for actual complete-packet bytes.

The no-motion HUD alternative keeps most savings and costs much less Python
time. Full HUD motion offers another3.8–5.6% saving in the continuous-history
component experiment, while paid Python encoding rises from about20ms to54–56ms
per update. The integrated full-frame source expansion and legacy selection are
also charged. Decoder hardware need not execute the host's81-vector search.

**Base video:** GM25 retains the frozen integer color conversion, Q14 8×8
transform/inverse and ROI quantizers, while adding bounded16/32-pixel block
motion, compact vector maps, zero/DC/full residual dispatch and optional lossy
whole-block SKIP. Vectors are even luma displacements within±8, with integer
half-displacement chroma. There is no fractional-pixel interpolation or loop
filter. Every reference tag binds the actual reconstructed YUV bank.

Actual SAD-selected motion is often inferior to zero motion plus residual RDO
on these clips. The native controls retain the losing results. The selected
profile uses zero displacement, every-frame acknowledged reference publication,
ROI8/background16, fine background16 keys0/24 and P-only RDO lambda1. A causal complete-packet
cap check retries background32 only when necessary, with all losing work paid.
This is an
application-specific result: stronger prediction does not automatically mean
more vectors. Fine keys recover the primary window's quality threshold that
coarser keys missed.

RDO compares actual clipped source-YUV SSE against a paid coefficient-bit proxy;
the latter constructs standalone CP02 probes. It protects ROI8 blocks plus the
chroma halo, builds original/pruned complete planes, and retains the smaller
actual plane. This is not HEVC/AV1 RDO, perceptual optimization or an exact
plane-wide marginal-rate oracle. Final reconstructed bytes define all later
references, including after SKIP.

**Composition:** actual CP25 binds GM25 and HU25 with60 fixed bytes. The receiver
privately validates both components and exact bank identities before modeled
write-drain/vblank publication; a65-byte JA25 ACK binds the pair and both output
tags. Sender ACK validation happens before the next reference is accepted.
Keys reset the two logical base banks and require an independent HUD update.
This profile is a new laboratory grammar, incompatible with AR03/CP23 peers.

## Complete-cap failure and causal recovery

The initial fine-key experiment fails admission on complex frame24:34,052 base
+17,502 HUD +60 binding =51,614bytes, exceeding49,152. Its four affected joint
cohorts remain explicitly rejected; their later fine-key component references
are diagnostics, never accepted CP25 timelines. No larger cap is introduced.

The capped policy prepares once, tries the actual fine key, then uses
background32 when the complete packet does not fit. The accepted frame24 is
25,792 +17,502 +60 =43,354bytes. Subsequent P frames are regenerated from that
actual decoded coarse key after valid ACK publication. The rejected fine
packet and both attempts’ work are retained. Each complex capped policy needs
one fallback, while neither primary policy does. All96 main-candidate frames
fit; the maximum48,686bytes leaves466bytes of complete-body headroom.

## Cost and evidence boundaries

- 96 distinct retained source images, reused across28 full-length base cohorts:
  **1,344 selected GM25 components plus2 paid rejected fine-key candidates**. Another192 component probes use the first
  12 images/window; they are exploratory reused controls, not extra captures.
- **28 actual joint cohorts /1,344 CP25 decisions**, with retained CP25/HU25/JA25
  objects, output tags/hashes and source-word quality checks. All complete
  packets fit49,152bytes; all28,385,280 joint HUD words match. Replays consume
  transmitted packets and reconstructed banks, never encoder search state.
- **51 passing tests:**15 base,13 HUD,10 joint protocol,3 fine-key integration,2 capped-key integration,
  8 independent audit tests. The HUD verifier additionally uses a scalar decoder
  on528 patch decisions /2,787,840 words plus24 translation/scene-change controls.
  Joint replay uses the frozen Python decoder; it is not independent RTL.
- Selected base encoding alone costs about252/502ms per source in Python,
  before HUD, pair parsing and ACK validation. CP02 bit-probe construction is a
  major RDO cost. Frame acquisition/color conversion is retained from v24 and
  not timed again. Paid base+HUD encoding is about308/562ms before the separately
  measured pair/ACK handling. Reliable immediate ACKs, write-drain and vblank are model
  inputs; no target CPU, RF, QSPI, DMA, memory-port or frame-clock is calibrated.
- Host prepared arrays occupy6,220,800 named bytes plus map bytes and search/
  packet/reconstruction temporaries. This is not an ESP32 allocation or FPGA
  BRAM estimate. Every-frame publication writes49,766,400 modeled int16 YUV bytes
  per48-frame cohort, versus6,220,800 for six period8 publications. A compact
  native eight-bit bank would differ and has not been implemented here.
  Referencing every preceding ACK also puts feedback/commit delay on the next
  frame's critical path; the immediate-ACK compression experiment does not
  prove that this dependency can sustain30fps over the real link.
- The forward/reverse projections retain the earlier1008-byte fragment and
  token/control arithmetic, replacing the joint ACK with actual65-byte JA25.
  No CP25 transport/controller or native reset/capability integration exists.
  Actual radio retries, input/audio, capture and presentation latency are absent.
- All footage is reused precompressed29.88fps regression footage. Projecting
  byte counts to30 IDs/s is neither a sustained distinct-source30fps proof nor
  evidence that the endpoint/FPGA can implement HEVC or AV1.

## Next steps toward the compression target

1. **Close the base coding gap, rather than just the wrapper gap.** Compare
   causal actual-byte zero/block/global selection; charge every candidate.
   Prototype bounded half-pixel interpolation and small intra predictors at
   unchanged resolution. Add each tool as an ablation with fixed reconstructed
   references, decoded output tags and actual serialized syntax. Keep a cheap
   zero/SKIP path; do not mandate exhaustive search at the receiver.
2. **Improve the coefficient rate/quality decision.** Replace CP02 packet-building
   probes with an exact bounded bit counter and prove byte/image parity first.
   Then compare position/context-aware coefficient coding and small integer
   4×4 versus8×8 transforms, with paid mode maps. Derive any deblocking or
   prediction filter from the transmitted reconstructed path; no source oracle
   may repair the reference bank. Retain a fixed-complexity decoder budget.
3. **Evaluate a standards-derived restricted decoder as a separate branch.**
   Specify the supported syntax/tools before choosing encodes. Existing
   ultrafast/low-delay settings do not prove that bitstreams fit that subset.
   Reject unsupported features, measure native/RTL service and external-memory
   traffic, and compile/place/route the identified FPGA before any fit claim.
   A custom HEVC/AV1-inspired syntax is not standards compatibility.
4. **Make the compression gain usable.** Port selected arithmetic/parser/ACK
   rules to native host/endpoint tests, reuse the current hardware JPEG path as
   fallback, and connect real bounded credits, reset and memory/scanout fences.
   Test at least1,800 fresh distinct30fps captures with loss/jitter/cuts and a
   later10-minute physical campaign. Record presented IDs, frame age and stalls;
   a cap-fitting body alone is not a sustainable-rate controller.

## Reproduce and hand off

```sh
python experiments/verify_prototype_v25.py
```

The provenance inventory covers all retained sources, tests, artifacts and old
v24 codec/results. Only README/plan indexes advance; earlier study branches and
the v20 hardware handoff stay frozen. The aggregate verifier runs retained HUD,
fine-key, joint and independent-audit checks without downloading footage or
rerunning native HEVC/AV1 encoders. Python/NumPy and the inherited project
dependencies are needed; this is a study branch, not an installed product.

Primary artifacts are in
[`python-game-combined-motion-v25-study`](../experiments/python-game-combined-motion-v25-study/),
[`python-game-native-motion-v25-study`](../experiments/python-game-native-motion-v25-study/),
[`python-game-fine-key-v25-study`](../experiments/python-game-fine-key-v25-study/),
[`python-game-capped-key-v25-study`](../experiments/python-game-capped-key-v25-study/) and
[`python-game-hud-motion-v25-study`](../experiments/python-game-hud-motion-v25-study/).
