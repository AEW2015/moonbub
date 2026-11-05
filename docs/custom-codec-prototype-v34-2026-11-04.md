# V34: real hierarchical frames, atomic composition and opaque-HUD inputs

The main implementation advance is an **actual Python frame/receiver profile**:
hierarchical motion, exact v33 HUD run packets, base/HUD identity binding,
staged validation, ping-pong publication and ACKs now run together. The control
integrates shared encoder evaluation and reproduces all 96 legacy base packets.
The previous same-HUD control budgets are now serialized and accepted CP34
streams in the host model, rather than only component re-accounting.

Compression gains remain modest and have costs. Full hierarchy saves 0.40% /
0.95% complete causal bytes; complex mean error rises slightly. A new opaque-HUD
source mask saves 3.36% / 2.97% at about 1% higher mean error. Fresh HEVC/AV1 runs
on the same processed input still use fewer bytes at better sampled MSE.
**There is no HEVC/AV1 compression victory or native 30 fps proof.**

All studies preserve 720×480 coded / 720×405 active geometry and exact RGB565
HUD. They reuse the two short retained Mass Effect windows. Rates are nominal
bytes at 30 decisions/second, not measured endpoint throughput or evidence of
generalization across games. No native software, bitstream or remote hardware
was changed. JPEG and the v20 hardware handoff remain frozen.

## Actual motion syntax and frame integration

[HM34](../experiments/python-game-hierarchy-v34-study/README.md) serializes a
bounded parent32 field and child16 corrections. It constructs flat, sparse-gap
and parent-mask candidates, pays every header/parameter/mask/delta/padding/CRC
byte and retains the smallest actual component. The independent decoder checks
domains, lengths, geometry, indices, masks and Rice escapes without encoder
search or canonical repacking.

On the retained 24-source split probe, strict-band motion bytes fall
**13,945 → 12,318**, an 11.67% reduction with identical vectors and pixels. The
old accepted-control guard totals 506,909 bytes; replacing the component yields
506,756 prospective bytes and admits six frames instead of five. This 153-byte
increment is a matched-reference component result, not a new causal stream.
Host component encoding costs 44.81 ms per nonkey trial; syntax decode is 2.14 ms.

[GM34/CP34](../experiments/python-game-controller-v34-study/README.md) then tests
actual complete packets and causal histories. GM34 uses the existing frame
header shape with new magic and an HM34 motion section. Qmap, inverse arithmetic
and residual payloads remain the frozen design. GM27 is retained as a fallback;
all legacy and hierarchical child candidates are actually constructed.

The Python receive adapter expands HM34 to the frozen literal raw-vector receive
grammar privately. Tests prohibit motion-encoder calls during decode. Its
compatibility packet and NumPy arrays are host scratch, not wire overhead or a
streaming hardware architecture. Hierarchical vectors require 3,390 logical
parent/child bytes, and component storage is bounded to 2,719 bytes. Physical
ports, placement, DMA, lookup/state logic and native service are unmeasured.

CP34 adds an explicit **21,120-word total HUD bound**, checks inner geometry
before allocating legacy patch data, and binds exact SHA/CRC/length/epoch/frame/
reference/bank identities. Base and HUD decode privately; only after both pass
and the modeled write-drain/vblank gates are true does the receiver publish and
return JA34. Corrupt/missing HUD, wrong references, stale frames, invalid slots
and late output-tag failures leave state unchanged. This is a synchronous host
publication model, not live negotiation or a hardware memory-fence simulation.

## Full causal hierarchy results

Three policies independently update their accepted reconstructions, rotating
execution order. Child admission uses the full strict control winner on that
policy's **own current history**: cap fit, strictly fewer complete bytes and no
higher active source RGB SSE. A standalone control history is a different
comparison. All policies use identical actual HX33 packets and 60-byte binding.

| 48-frame window | Policy | Complete bytes | Active MSE | Paid host policy ms/frame |
| --- | --- | ---: | ---: | ---: |
| Primary | Control | 441,224 | 14.386886 | 227.99 |
| Primary | Full hierarchy | 439,457 | 14.380495 | 410.34 |
| Primary | Select25 hierarchy | 441,224 | 14.386886 | 408.66 |
| Complex | Control | 1,068,678 | 26.303889 | 323.09 |
| Complex | Full hierarchy | 1,058,551 | 26.370030 | 574.79 |
| Complex | Select25 hierarchy | 1,066,019 | 26.382721 | 565.04 |

Full hierarchy saves 0.4005% / 0.9476% complete bytes. Primary MSE improves
0.0444%, while complex MSE rises 0.2514%. Select25 saves nothing on primary and
0.2488% on complex, with complex MSE rising 0.2997%. Local strict guards do not
guarantee globally equal quality after references diverge. At their added host
cost, these are research operating points, not recommended defaults.

There are 47 selected child frames, including 38 actual GM34 frames. All 1,864
candidate frames, 748 shared-pair calls, 288 accepted CP34 frames and 6,082,560
exact HUD words are retained. HM34 is prepared once per source and shared across
child incumbent/band variants; pair work is likewise charged once. All losing
frames are encoded, wrapped, source-scored and bound. Source conversion, fixture
reads, preencoded HUD creation, offline debug decode, archive I/O, receiver,
network and display are excluded or separately timed. These clocks remain far
above a 33.33 ms source period.

Control decoder prediction reads are 26,053,120 / 33,489,152 logical samples;
full hierarchy reads 26,137,984 / 33,626,368. The byte gain therefore does not
establish lower reference-memory traffic. Neither counts nor receiver host
timings establish physical bandwidth, FPGA fit or latency.

## Selective search: keep the negative evidence

[The separate 24-source selective probe](../experiments/python-game-selective-v34-study/README.md)
ranks current-source parent error/dispersion, then refines fixed 25% or 50%
quotas. Unselected children inherit their parent exactly. It has no future-frame
or acceptance-metric oracle. SAD work falls 42.53% / 32.55%, but neither preset
admits a packet against accepted control in those short uniform-map probes.
Raw bytes, RGB error and decoder reference reads all regress. All 168 actual
packets and the full-refinement control are retained and independently re-encoded.

The predeclared 25% preset still runs in the full causal hierarchy campaign;
later complex frames can qualify once hierarchical metadata is available. That
does not contradict the earlier fixed-reference result or justify picking a
preset from its training winners. The causal table above supplies the actual
rate/error/work trade-off.

## Application-specific source formation: do not encode hidden detail twice

[The opaque-HUD study](../experiments/python-game-opaque-v34-study/README.md)
tests a host-side change: replace hidden base detail with neutral samples while
the exact opaque HUD reconstructs those pixels. The first implementation sets
Y/Cb/Cr throughout each rectangle. It **fails on all 96 inputs**: bilinear chroma
upsampling changes 546–934 visible RGB565 words outside the HUD per frame.
Even 2×2 alignment is insufficient.

The safe variant preserves the first chroma row and column of each rectangle,
masking only its interior chroma and all its luma. All 96 inputs then preserve
**exact visible RGB8 outside the HUD** and exact RGB565 after overlay before
coding. No external plane sample changes. A decoder format change is unnecessary;
the existing CP34 exact-HUD/atomic-commit contract prevents holes from publishing
without valid HUD data.

| Same-HX33 causal comparison | Original complete bytes | Masked complete bytes | Original MSE | Masked MSE |
| --- | ---: | ---: | ---: | ---: |
| Primary | 441,224 | 426,409 | 14.386886 | 14.565884 |
| Complex | 1,068,678 | 1,036,896 | 26.303889 | 26.572316 |

The true complete savings are **3.3577% / 2.9740%**, with MSE increases of
**1.2442% / 1.0205%**. Both sides use the same actual HX33 HUD and binding;
historical HU25 budgets cannot be credited as masking savings. Precodec visible
equivalence does not imply equal quality after lossy block coding and changed
reference histories. All 96 coded frames have higher MSE in this comparison;
the largest per-frame MSE increases are 0.2562 / 0.6455. Primary peak packet bytes
also rise 23,321→24,502 despite lower aggregate bytes. Aligning future masks to
transform/upsampling support and adding visible-error and peak-byte guards is
a concrete next experiment. The fixed mask is not a quality-neutral default.

Mask formation copies 1,036,800 Python int16 array bytes and writes 30,712
constants per source. Its separately measured postcampaign mean is 0.13346 ms;
it is excluded from policy clocks, not silently included in an end-to-end claim.
Masking adds no decoder format/state, but all covered pixels still participate
in reference reconstruction and display. Actual custom policy means are about
227.37 / 320.59 ms, excluding source preparation and the documented other stages.

## Fresh same-processed HEVC/AV1 comparison

Twelve actual low-delay native runs use the frozen v24 CPU encoder settings:
original and masked anchors, plus masked quality brackets. All 576 access units
decode with immediate ordered PTS/DTS, keys 0/24 and no flush-only frames. Actual
AU bytes and once-only extradata receive the same actual HX33 sizes + 60-byte
binding as custom. These native bindings are accounting, not native CP34 streams.

| Masked input, nominal complete Mbps at30 | Custom | HEVC | AV1 |
| --- | ---: | ---: | ---: |
| Primary | 2.132045 | 1.199710 | 1.112610 |
| Primary active MSE | 14.565884 | 11.526840 | 12.487713 |
| Complex | 5.184480 | 3.031685 | 2.964145 |
| Complex active MSE | 26.572316 | 22.048210 | 20.222133 |

The selected HEVC q32/q28 and AV1 q48/q38 points meet or beat custom mean MSE
and fit each complete frame cap. Weaker complex bracket points fail the quality
threshold and remain recorded. Native masking is not uniformly helpful: primary
anchor bytes increase slightly; complex AV1 improves. This is sampled low-delay
rate/error evidence, not matched-quality BD-rate, perceptual equivalence, optimal
standards encoding, or fitted Gamebub standard-decoder performance.

Standards remain ahead on compression and measured mean error. Combining separate
masking/hierarchy gains or claiming superiority from simpler hardware would be
unsupported. A measured latency/resource advantage is a separate target requiring
native implementation evidence.

## DSP and memory opportunity, with measured boundaries

Offline selected-packet coefficient analysis, outside encoder clocks, shows:

| 48-frame cohort | Zero blocks | DC-only | General |
| --- | ---: | ---: | ---: |
| Primary original | 319,767 | 18,217 | 50,816 |
| Primary masked | 327,084 | 16,734 | 44,982 |
| Complex original | 246,345 | 21,397 | 121,058 |
| Complex masked | 257,017 | 20,332 | 111,451 |

Every frame still has 8,100 blocks. Fewer general blocks create a real input
opportunity for the existing zero/DC shortcuts. Replaying the frozen two-bank
dependency model projects 6.20048→6.08656 ms / 7.39291→7.23460 ms **if an unclosed
100 MHz clock is assumed**. This excludes entropy, reference fetches, color/HUD,
CRC, transport and display. It is not new RTL, a fitted DSP result or physical FPS.

## Next gates

1. Prioritize **visible-error-aware source formation**: mask only safe transform
   interiors, preserve interpolation support and quantify boundary/temporal error.
   Compare actual serialized bytes at matched quality; give identical processing
   and HUD credit to HEVC/AV1. Add longer unseen gameplay before choosing a mode.
2. Reduce host HM34 packing overhead through shared exact planning. Preserve
   byte/pixel decisions before adding more searches. The current hierarchy gain
   is small relative to its extra 180–250 ms/source of Python work.
3. Qualify cheap confidence-triggered refinement with full causal histories and
   visible-quality gates. Do not promote quota heuristics merely for fewer SADs.
4. Port the bounded CP34/HM34/HX33 reference and malformed goldens to native
   sender/receiver code. Implement explicit profile negotiation, ACK retry/reset,
   memory drains and publication fences before device use. Keep JPEG fallback.
5. Implement the prior two-bank inverse schedule plus bounded entropy/dequant,
   prediction and HUD stages. Measure cycles, routed clock, DSP/LUT/BRAM/ports,
   full memory arbitration and ESP32 SRAM/DMA/Wi-Fi/QSPI contention. Only a full
   pipeline measurement can establish the intended physical 30 fps operating point.

## Reproduction

```sh
python experiments/verify_prototype_v34.py
```

The manifest freezes v33 sources, new producer/replay code, actual packets/native
access units, test logs and provenance. Component verifiers re-decode packets and
source metrics; independent audit reconciles matrices, caps, cost groups, shadows,
causal histories, masked-source equivalence and fair native points. The prior
hardware handoff is unchanged; this is a Python research and integration branch.

There are **26 focused passing tests**, 384 accepted causal CP34 frames, 2,240
causal candidate frames and 576 native AU decodes. Fixed-reference hierarchy and
selective probes are counted separately and do not become extra causal results.
