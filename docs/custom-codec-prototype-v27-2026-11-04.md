# Iteration27: one application-specific codec profile

GM27 now combines compact fractional prediction, exact RDO bit counting and
EC26 block-major coefficient coding in one direct encoder/decoder. Actual
CP27 packets bind that base to the same pixel-exact HU25 sidecar; JA27 ACKs bind
the complete pair and both reconstructed output tags. This replaces v26's
independent codec experiments with a real combined wire profile.

The native Sunshine/ESP32/FPGA path is not installed. This remains a Python
prototype at720×480 coded /720×405 active resolution, with21,120 exact RGB565
HUD words per accepted frame and a49,152-byte complete-frame cap.

## Actual combined results

Body rates project actual complete packet bytes to30 source IDs/s. The same
96 retained precompressed29.88fps source images are reused across the controls.
No measured physical frame rate is implied.

| Window | V26 fractional body | V27 fixed-history control | V27 causal controller |
| --- | ---: | ---: | ---: |
|2600 |2.904850Mb/s |2.620690Mb/s |2.620080Mb/s |
|7200 |6.445595Mb/s |5.993735Mb/s |5.978380Mb/s |

The fixed-history control preserves every v26 coefficient, reconstructed
reference, displayed RGB565 hash and active MSE14.04092 /26.42170 while saving
**9.78% /7.01%** complete bytes. It reuses the old mode/quantizer-choice trace;
it isolates exact entropy gain rather than claiming a new online selector.

The causal controller instead builds zero and half32 candidates from its actual
currently accepted reference. It chooses the smaller complete packet only when
its current source SSE is no worse than that same-reference zero candidate.
All competing searches, transforms, legacy entropy trials and EC26 construction
are paid; references advance only after actual decode/publication/ACK validation.

| Window | Causal byte saving vs v26 fractional | V26 MSE | V27 causal MSE |
| --- | ---: | ---: | ---: |
|2600 |9.80% |14.04092 |14.05861 |
|7200 |7.25% |26.42170 |26.17453 |

Primary mean error rises about0.13%; complex mean error falls about0.94%.
A current-source guard against zero prediction does not guarantee a better
whole-window MSE than a different controller with a different reference history.
Neither policy reduces resolution or exact HUD coverage.

The causal path selects half32 on45/48 and46/48 frames. Entropy savings allow
the complex frame24 fine key to fit, so it needs no coarse-key fallback there.
Both policies retain actual capacity checks; the causal largest complete packet
is45,405bytes. All192 accepted pairs across the four cohorts fit the cap.
The experiment retains284 actual candidate encodes, including losing candidates.

## Comparison with the native software controls

The native HEVC/AV1 access units from v24 are charged the same actual current
HU25 packets and60-byte binding budget. At sampled quality thresholds, their
body projections remain approximately1.751/1.669Mb/s on2600 and3.838/3.812Mb/s
on7200. Those settings have lower MSE than the compared custom points.
The new causal profile still needs about **1.5–1.6×** their complete-body bytes.
These are sampled operating points, not matched-quality BD-rate or a decoder-fit
comparison. HEVC/AV1 parity remains open.

## Direct coding and a coherent decoder contract

The encoder quantizes once per candidate, applies the exact counted RDO rule,
and executes the frozen legacy original/pruned comparison before fixing the
coefficients. It then constructs EC26 layout0 for those actual chosen
coefficients and keeps the smaller complete plane. All alternatives and subset
CP02 constructions are counted and timed. It does not serialize a GM26 packet
and silently omit that cost from a later repack phase.

This preserves the previous coefficient decision on a matched predictor/map;
the new entropy syntax changes rate rather than pixels. The online selector can
still choose a different predictor or key map because the actual complete cost
changes, which explains its altered reference history and quality.

The [static profile descriptor](../experiments/python-game-unified-v27-study/profile.json)
and [wire schema](../experiments/python-game-unified-v27-study/SCHEMA.md) state
geometry, motion units/ranges, coefficient dispatch, caps and publication rules.
GM27/CP27/JA27 are distinct from GM26/CP2F and GE26/CP26. This descriptor is
handoff metadata; capability negotiation/reset integration is not implemented.

## Receiver work that belongs on the receiver

The v26 Python motion parser re-encoded all map alternatives to demand the
encoder's smallest representation. GM27 instead checks bounded syntax, vector
range, lengths, coverage, sparse indexes, bit padding and canonical Rice escapes.
It does not repeat the encoder's representation/parameter search.

This intentionally expands the accepted representation language for GM27.
Deployed GM26 rules remain frozen. Seven decoder tests and retained controls
include31 malformed cases and six valid nonminimal forms, alongside525 canonical
frame parses /492 motion maps that match version-correct frozen parsers exactly.

| Matched v26 full-attempt controls, median Python time | Frozen | Syntax-only |
| --- | ---: | ---: |
| Motion map parse |4.656ms |0.268ms |
| Full frame parse |14.680ms |10.491ms |

The main16-block probe controls show24.368→1.681ms per map. These are paired,
rotated host trials on retained packets, not DSP/FPGA clocks or whole-stream
speedups. The main corpus avoids6,272 Rice-axis trials /4,640,160 Rice-value trial
encodes per pass. Fixed total map bounds also constrain which structurally
nonminimal representations can fit; dropping an optimality check is not an
unbounded acceptance policy.

CP27 also separates metadata validation from full payload decoding. Binding and
ACK validation check header/CRC/identity/geometry/declared lengths and payload
digests without decoding coefficients. The receiver still validates every map,
entropy payload, actual reference and reconstructed output tag before atomic
publication. A CRC-valid malformed entropy body can pass metadata validation
and must fail full receive without changing published banks; tests cover that
distinction.

## Processing and memory limits

The causal Python source build costs about658/694ms per frame with both
predictors, all searches and every entropy alternative paid. Receiver means in
this run are about34/52ms. Bind and ACK checks are sub-millisecond, but these
figures are component clocks from one host run, not a native sustained schedule.
The protocol's write-drain/vblank gates and immediate reliable ACKs are model
inputs. No native30fps claim follows.

Fractional P prediction still executes four-tap reference fetches; search stays
on the host. EC26 block-major's separate iterator proves coefficient order using
four compressed-stream cursors and one128-byte output block. The frame model
still allocates full coefficient and reconstructed planes. Real memory ports,
DMA/scanout arbitration, finite credits, reset, compiled resources and timing
require native/RTL qualification.

## Next steps toward the application codec

1. Retain GM27 as the unified arithmetic/wire golden. Port its block-major
   coefficient readers, compact MV parser and frozen inverse transform together,
   with explicit bounded buffers and output-tag/publication tests.
2. Reduce host search and legacy candidate construction using exact counters,
   native/GPU work or bounded search policies. Measure rate/quality after each
   change; a faster proxy cannot be assumed to preserve the selected mode.
3. Extend quality control beyond per-frame zero prediction: assess temporal
   stability, tails, cuts, particles and UI on fresh footage. The0.13% primary
   MSE regression remains visible until the product policy chooses that tradeoff.
4. Bind a negotiated profile to real reset, packet credits and memory fences.
   Then run at least1,800 distinct30fps captures and a10-minute physical test,
   counting presented IDs, stalls, frame age, CRC/FIFO errors and recovery.
   Keep JPEG and the frozen v20 hardware handoff available until that passes.

## Reproduce

All29 current unit tests pass:12 unified codec/protocol,7 decoder-policy and
10 audit tests. Retained verification covers192 accepted CP27 pairs,284 actual
candidate encodes,4,055,040 exact HUD words,96 frozen-history coefficient/vector
parity controls and576 completely drained EC26 streams /1,555,200 blocks.
The decoder study separately checks525 frozen frames /492 maps,31 malformed
controls and six expanded-language controls. These reuse96 source images.

```sh
python experiments/verify_prototype_v27.py
```

The retained verifier decodes every accepted and losing candidate from bytes
and reconstructed state, recomputes source RGB565 errors, checks exact HUD,
replays selection/admission/ACKs and compares EC26 block streaming. The separate
audit independently reconciles object hashes, actual sizes, source lineage,
rate/MSE sums, policy guards and same-HUD native controls. No original footage
download or hardware is needed for these offline checks. Prior v26 code/results
stay frozen; only README/plan indexes advance on this study branch.
