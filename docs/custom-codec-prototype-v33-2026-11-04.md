# V33: exact run coding, shared encoder work and motion hierarchy

This Python iteration makes two useful advances at unchanged **720×480 coded /
720×405 active resolution**: exact HUD run coding saves 35.77% / 17.75% versus
the v32 HUD, and shared encoder evaluation reproduces actual packets with 32.97%
less measured pair work. Sparse camera-motion search trades extra bytes/error for
lower host and decoder prediction work. Smaller motion blocks are evaluated
separately against the accepted control, including their metadata cost.

These are offline results on the same two short retained Mass Effect windows.
They do not establish native 30 fps, FPGA fit, generalization across games, or
compression superiority over HEVC/AV1. All rates below are nominal bytes at 30
decisions/second, not measured endpoint frame rates.

## Application-specific exact HUD coding

[HX33/HS33](../experiments/python-game-hud-runs-v33-study/README.md) extends the
bounded component-residual approach with zero-gap and repeated-symbol runs.
Each channel selects actual serialized canonical-Huffman and Rice alternatives;
the old HU25/HX32 packet wins ties and is the fallback. The new independent bit
parser checks bounds, padding, coverage, identity, references, CRCs and pixel tags.
All 96 frames select the new envelope, with 371 new run-coded patches.

| 48-frame window | v32 HUD bytes | v33 HUD bytes | Reduction | Exact words |
| --- | ---: | ---: | ---: | ---: |
| Primary | 310,685 | 199,566 | 35.77% | 1,013,760 |
| Complex | 562,316 | 462,520 | 17.75% | 1,013,760 |

Runs exploit correlation that a per-symbol Huffman coder misses, including the
long sequences of zero residuals in UI patches. Full RGB565 pixels remain exact.
This is a useful custom streaming layer, but its gain is equally available to a
standard picture codec with the same exact-HUD layer.

Extra Python encoder work averages **110.65 / 170.10 ms per frame**; decode is
6.02 / 11.81 ms. The timer includes both inherited packet validations, every new
recipe and size trial, actual bit construction and sealing. It excludes prior
HU25/HX32 generation and motion search; an integrated sender must pay or share
those decisions. There are 14,112 channel-scheme and 141,120 Rice-parameter trials.
These costs prohibit calling this a complete 30 fps source encoder.

The serial HS33 state projection is 1,345 logical bytes, or 1,508 bytes including
shared legacy palette fallback scratch. It assumes a seekable packet and serial
color passes with external staging. The measured fixed HUD requires 84,480 bytes
for reference/stage banks plus up to 49,152 packet bytes. Supporting the whole
unchanged generic legacy patch domain requires 1,382,400 bank bytes instead.
**The small bank budget therefore needs an explicit fixed-HUD profile bound.**
These are logical layouts; ports, FIFOs, lookup expansion, DMA, physical memory
and cycle service remain unimplemented. The ESP32 stays an opaque bounded
transport gateway and is not assigned HUD decoding or image banks.

Current CP27/native receivers do not accept HX33. A negotiated new full profile
must bind its components and publish only complete verified frames. The retained
new HUD packets are actual; combined base/HX33 totals remain prospective.

## Exact shared encoder evaluation

[`encode_pair`](../experiments/python-game-shared-v33-study/README.md) computes
the existing incumbent and strict-band outputs together. It shares quantization,
RDO, legacy fallback decisions, incumbent entropy planning/reconstruction and
unchanged plane payloads. Temporary state is private to one call; there is no
persistent cache, global mutation, new wire syntax or changed winner.

All 92 packet outputs across 46 pairs / 24 source frames match the frozen v32
attempt bytes, individual payloads and reconstructed pixels. Tests also cover
72 key/P, quantizer and lambda combinations, plus a real legacy revert case.

| Paid pair work | Separate calls | Shared pair |
| --- | ---: | ---: |
| Mean host time | 127.052 ms | 85.170 ms |
| Quantization / RDO calls | 92 / 92 | 46 / 46 |
| Legacy size-counter calls | 1,668 | 852 |
| Inverse-plane calls, including RDO | 1,092 | 634 |

The pair is **1.492× faster**, with three rotated paired timing samples and fresh
setup paid on every call. This excludes analysis/search, HUD, RGB scoring, debug
decoding, archives, network and display. It is not a 1.492× whole-sender speedup.
Traced transient memory in two key-pair samples falls from about 16.43 to 15.39
MB; these are not all-frame RSS bounds or ESP32 allocations. The shared work
counter appears in both return triples and must be charged once, not twice.

## Causal sparse camera-motion policies

[The global-motion campaign](../experiments/python-game-global-v33-study/README.md)
maintains three separate accepted histories and the existing strict selector.
Sparse global translation excludes UI for estimation, then each block selects
zero or a nearby vector. `global_grid` keeps vectors divisible by four half-luma
units, permitting exact integer sampling in both luma and chroma. Geometry,
quantizers, key cadence, packet cap and exact HUD remain unchanged.

| Window | Policy | Actual complete HU25 bytes | Active MSE | Paid host policy ms/frame |
| --- | --- | ---: | ---: | ---: |
| Primary | Control | 552,619 | 14.386886 | 311.11 |
| Primary | Cross | 570,115 | 14.425950 | 293.24 |
| Primary | Grid | 571,086 | 14.397236 | 284.98 |
| Complex | Control | 1,229,773 | 26.303889 | 411.31 |
| Complex | Cross | 1,256,403 | 26.628150 | 361.56 |
| Complex | Grid | 1,266,182 | 26.658162 | 351.12 |

Cross reduces whole-policy host work 5.74% / 12.10%; grid reduces it 8.40% /
14.63%. Both increase complete bytes and mean MSE versus the control. Retain them
as speed/resource operating points, not compression/quality wins or new defaults.
The shared-pair and search improvements have not been combined and timed; do not
multiply their speedups.

Grid's selected decoder predictions read **23,846,400 logical samples** per
window, versus control 26,053,120 / 33,489,152: reductions of **8.47% / 28.79%**.
Each P frame reads exactly 518,400 samples. These are logical operations, not
measured memory transactions or fitted FPGA service. A hardware integer fast
path still needs domain validation, arbitration and throughput measurement.

All 288 accepted pairs and 1,128 actual candidate encodes are retained. Replay
checks 6,082,560 exact HUD words and 96 exact v32 control packet/ACK/pixel matches,
reconstructs each history, repeats the 184 fast P-frame searches and recomputes
selection, decoded metrics, tap counts and paid work. Host policy time pays all
analyses, encodes, RGB checks and binding, but excludes capture/conversion,
preencoded HUD generation, archive I/O, offline debug decode, network and display.

## Hierarchical 32-to-16 motion probe

[The split probe](../experiments/python-game-split-v33-study/README.md) seeds a
45×30 grid of 16-pixel motion blocks from the 23×15 parent field, then searches
small local half-unit offsets. Actual GM27 block-size-16 packets and their CP27
bindings decode through unchanged parsers; 72 new packets cover 24 source inputs.
All trials pay parent search/encoding, child refinement, both child encodes,
source RGB scoring and binding. Geometry and exact HUD remain unchanged.

The primary guard compares against the **actual accepted v32 control packet**,
not merely the separately encoded half-motion parent candidate. Five frames
qualify, all in the complex window (IDs 5, 7, 8, 10 and 11):

| Fixed-reference, combined 24-source comparison | Complete bytes | Active RGB SSE |
| --- | ---: | ---: |
| Actual accepted control | 508,720 | 426,975,565 |
| Raw strict-band16 on every input | 508,776 | 426,825,737 |
| Guarded actual-control fallback | 506,909 | 426,515,821 |

The guarded gain is **0.356% fewer bytes and 0.108% lower aggregate SSE**. Each
chosen frame individually saves bytes with no higher source RGB error. Raw
unconditional block16 is not a compression win: versus accepted control, motion
bytes rise 2,616 → 13,945 while residual bytes fall 229,881 → 218,608. Metadata
consumes the residual improvement, leaving 56 extra bytes overall.

This identifies a specific next hypothesis: serialize the parent field plus
sparse child refinements, with exact actual-byte competition against the existing
uniform map. Test the syntax overhead and decoding bounds before claiming a gain.
The current study changes only the encoder's uniform block size, not the wire.

The probe costs 366.30 ms/source in paid host work, including 204.99 ms additional
child work. Neither trial output becomes the next reference; all probes consume
the accepted v32 history. Thus the selected byte/error improvement is a
**matched-reference result, not a new causal stream** or a gain that can be added
to the global/HUD studies. Longer causal integration and cheaper selective
refinement remain necessary before adoption.

## Equal treatment of HEVC and AV1

The comparison uses the same **actual per-frame HX33 HUD sizes + 60-byte binding**
for custom and native candidates. Native bytes include retained low-delay access
units and once-only extradata. The selected sampled standard point must meet or
beat the custom mean MSE and fit each complete frame under the same cap. Source
conversion, geometry and cadence remain the retained v24 conditions.

| 30 Hz complete budget | Custom control + HX33 | HEVC + HX33 | AV1 + HX33 |
| --- | ---: | ---: | ---: |
| Primary Mbps | 2.206120 | 1.193690 | 1.112255 |
| Primary active MSE | 14.386886 | 11.210939 | 12.248229 |
| Complex Mbps | 5.343390 | 3.032660 | 3.006935 |
| Complex active MSE | 26.303889 | 22.161878 | 19.767521 |

New HUD coding reduces the custom control's prospective total 20.12% / 8.54%
versus the v32 common-HUD budget, with identical pixels. The same absolute
0.555595 / 0.498980 Mbps savings accrue to HEVC and AV1, so the picture-coding gap
does not close. Standards still use about 43–50% fewer complete bytes at these
sampled better-MSE points. This is not matched-quality BD-rate or perceptual
equivalence, and no native standard/HX33 endpoint has been implemented.

For perspective, custom picture bytes alone project to 1.193890 / 3.016390 Mbps,
versus HEVC 0.181460 / 0.705660 and AV1 0.100025 / 0.679935 at the sampled points.
Beating those picture rates requires a larger improvement than the tested local
heuristics. Better fitted latency/resource cost is another product goal that
needs its own implementation evidence; simpler syntax alone does not prove it.

## Next experiments and deployment gates

1. Integrate `encode_pair` into the complete causal selector and reproduce every
   old winner while paying the combined source work. Profile the remaining RDO,
   entropy planning and reconstruction before adding more candidate searches.
2. Serialize a bounded parent32 + sparse child16 motion component against the
   retained actual 16-pixel fields. Pay all masks, lengths, escapes and CRCs; demand
   identical vectors/pixels. Only then integrate a negotiated profile and test
   confidence-triggered refinement/fallback with full causal histories. The raw
   motion-map cost is the demonstrated obstacle, not a missing residual saving.
3. Add bounded copy/palette/SKIP modes only when their actual metadata plus
   residual bytes win. Context-aware rate costs must be rebuilt after edits;
   independent local savings cannot be summed. Qualify longer unseen gameplay,
   temporal error, cuts, effects and UI changes before selecting a new mode.
4. Build a fixed-HUD, negotiated run-decoder profile with explicit bank, packet,
   table and expansion bounds. Generate HDL/native goldens from the independent
   decoder and add reset, truncation, replay and atomic publication checks.
5. Implement the prior two-bank inverse schedule, bounded entropy/dequantization
   and integer prediction fast path. Measure actual cycles, memory arbitration,
   DSP/LUT/BRAM/ports and routed clock. Then qualify ESP32 SRAM/DMA/credit behavior
   under concurrent Wi-Fi/QSPI, native host service and whole-system 30 fps.

Preserve JPEG and the v20 hardware handoff. The research target is a measured
application/hardware advantage in quality, latency and resource use. HEVC/AV1
compression parity remains an unachieved target; no native software, bitstream
or hardware on another system was changed by this iteration.

## Reproduction

```sh
python experiments/verify_prototype_v33.py
```

The manifest pins the frozen v32 inventory, new sources, actual packets, test
logs and offline verifiers. Component READMEs document individual tests, source
dependencies, paid timing scope and retained artifacts. The independent audit
reconciles rate/error/cap arithmetic, common-HUD standard comparisons, separate
causal histories and component result provenance. Twenty focused tests pass,
including 72 shared-encoder parameter combinations and malformed run streams.
No physical 30 fps claim follows.
