# Iteration28: application-specific rate, quality and work budgets

V28 improves implementations and encoder policies while keeping the existing
GM27/CP27/JA27 wire. Exact lazy entropy selection and tap-aware prediction
preserve old packets/pixels. Bounded sampled search offers a separate
rate/quality/CPU trade-off at the same720×480 coded /720×405 active geometry.
Every accepted frame retains21,120 exact RGB565 HUD words and the49,152-byte
complete-packet bound.

## Full causal results

These are six48-frame causal cohorts on96 retained precompressed29.88fps
source images. Encoded bytes are projected to30IDs/s; host time is measured
Python CPU wall time. No physical30fps result is implied.

| Encoder policy | Primary body Mb/s | Complex body Mb/s | Primary base-policy ms | Complex base-policy ms |
| --- | ---: | ---: | ---: | ---: |
| Exhaustive, exact runtime optimizations |2.620080 |5.978380 |662.34 |687.37 |
| Sample2 coarse/refine |2.679505 |6.047600 |394.07 |417.18 |
| Sample4 coarse /sample2 refine |2.706105 |6.175390 |276.42 |300.50 |

Base-policy service includes all analysis, losing/winning encodes, full source
SSE evaluation and binding checks. It excludes retained fixture acquisition/
color conversion, preencoded HU25 generation, debug decoder checks, artifact
storage, network waits and presentation. Receiver/ACK clocks are separate.

The mixed policy is **2.40× /2.29× faster** in measured base-policy work, paying
**3.28% /3.30% more complete bytes**. Sample2 is a less aggressive point: about
1.68× /1.65× faster, with2.27% /1.16% more bytes. These policies change vectors
and later reconstructed references, so quality must be measured too.

| Policy | Primary active MSE | Complex active MSE |
| --- | ---: | ---: |
| Exhaustive |14.058610 |26.174528 |
| Sample2 |14.155874 |26.244321 |
| Mixed sample4/sample2 |14.213686 |26.318948 |

Mixed MSE rises1.10% /0.55% relative to exhaustive; sample2 rises0.69% /0.27%.
These are speed trade-offs, not compression or image-quality wins. A source-side
guard against the current zero candidate does not guarantee the old controller's
whole-window MSE. No visual/perceptual equivalence is inferred from these short
regression windows.

The exhaustive optimized path reproduces **all96 old v27 CP27 packets, JA27
ACKs and displayed hashes exactly**. All288 accepted pairs across the six cohorts
fit the cap; all564 candidate encodes and their work remain recorded, including
losers. There are6,082,560 exact HUD words in these accepted transactions.

## Exact size planning avoids discarded entropy packets

V27 constructs dense CP02 and SP01 alternatives for both original and pruned
planes before trying EC26. V28 instead computes their exact lengths with the
validated CP02 counter and SP01 header/map/DC/subset arithmetic. Original versus
pruned coefficient choices and all tie rules stay identical. SP01dense is
strictly dominated by direct dense coding, so constructing that wrapper is
unnecessary.

The encoder then constructs EC26 for the final chosen coefficients and compares
actual bytes with the exact incumbent size. If a legacy fallback wins, only that
fallback is serialized. A proven55-byte EC26 lower bound skips EC26 construction
when it cannot strictly beat the incumbent. All counters still execute and are
timed; this is not treating losing decisions as free.

| Same-prepared paired leaf encoding | V27 | Lazy v28 |
| --- | ---: | ---: |
| Primary mean |35.786ms |32.190ms |
| Complex mean |50.891ms |42.362ms |

All96 selected source decisions produce byte-identical GM27 packets,
coefficients/references and image hashes. The paired order alternates per source;
shared analysis is outside these leaf clocks. Across this corpus,1,128 discarded
CP02 constructions and1,128 SP01 constructions become zero actual constructions,
with1,128 exact size-counter calls instead. EC26 packets are still actually
encoded. These host measurements imply11–20% faster leaf encoding, not a whole
pipeline speedup of that size or a native target timing result.

## Tap-aware prediction keeps the same pixel arithmetic

Fractional vectors already state which interpolation weights are zero. The
new implementation fetches one sample for integer axes, two for one fractional
axis and four for two fractional axes. It preserves floor division, separately
clamped addresses, one final rounding, full geometry and output tags. The
negative-edge scalar cases check the original coordinate+1 before clamping;
clamping first and then adding1 would be wrong.

On92 causal P-frame inputs with five interleaved/rotated calls each, mean
prediction time is **22.562→9.165ms (2.462×)**; p95 is23.439→10.563ms. Logical
reference gathers fall190,771,200→94,971,648, a **50.22% reduction**. Clamped
duplicates are still fetched/count separately. Validation, hashing, map reads
and output writes are additional; this is not total external-memory traffic.

All192 retained v27 accepted packets across fixed-history/causal cohorts decode
to identical planes and tags through the new adapter. The full v28 verifier
also recomputes tap counts on the new sampled-search histories. No wire or
normative decoder change is needed. FPGA tap gating can use the same arithmetic,
but its real ports, line buffers and clock timing remain unqualified.

## Search scoring uses fewer source samples

Both sampled policies retain81 bounded coarse vectors and25 half-pixel
refinements. Coarse integer prediction reads one sample per scored point;
refinement uses the frozen exact bilinear expression on the sampled points.
The selected full-resolution prediction, forward transform, quantization and
decoded output are unchanged in geometry.

For a P frame, exhaustive search scores54.9504million sample differences.
Mixed stride4/stride2 scores5.8644million, and sample2 scores13.7376million.
All attempted maps, full final prediction, motion-map coding and source copies
are charged. The earlier matched-reference24-frame probe suggested nearly equal
pooled mixed MSE; full causal48-frame windows reveal the small regressions above.
That difference is why a matched-reference probe alone cannot select defaults.

## Where these tools belong

- **PC/Sunshine encoder:** exact lazy planning is wire/decision compatible.
  Choose a sampled-search operating point only after accepting its measured
  rate/quality trade-off and qualifying longer source sequences.
- **ESP32 transport:** GM27/CP27 framing and complete capacity remain unchanged.
  The experiments do not measure RF/QSPI contention, packet credits, input or
  native parser service.
- **FPGA decoder:** reuse the fixed Q14 inverse/DSP path and gate interpolation
  taps using transmitted vectors. The Python implementation still allocates
  full planes/masks; named array counts are not fitted BRAM or SDRAM scheduling.

The measured Python base-policy times remain far above33.33ms before HUD,
capture and network waits. Mean receiver times in the full experiment are
approximately25–26ms primary and45ms complex on this host. Separate component
means must not be summed or overlapped to assert a native end-to-end frame rate.
HEVC/AV1 compression parity and physical30fps remain open.

## Next application-specific prototypes

1. Port the exact lazy planner and tap arithmetic using the retained packet/
   plane goldens. These are implementation changes with stable GM27 semantics.
2. Prototype adaptive search effort: use current candidate confidence and
   actual source error/bytes to trigger denser or exhaustive fallback only when
   useful. Regenerate whole causal reference histories and pay every fallback.
3. Investigate EC26-aware residual RDO. The current exact proxy counts CP02
   blocks; sparse-band run/DC context can give a different true marginal cost.
   Add a bounded rate counter before claiming more compression or less work.
4. Integrate native encoder service, negotiated reset/credits and real memory/
   publication fences. Qualify1,800 fresh distinct30fps captures and a later
   10-minute hardware run with presented IDs, frame age, recovery and FIFO/CRC
   counts. Preserve JPEG and the frozen hardware handoff until that passes.

## Verification

All25 current tests pass:4 lazy runtime,4 sampled search,5 tap arithmetic and
12 independent audit tests. Retained replay covers96 paired leaf comparisons,
288 accepted CP27/JA27 pairs,564 causal candidate encodes, the matched-reference
search controls and all old/new tap outputs. Cohorts reuse96 source images.

```sh
python experiments/verify_prototype_v28.py
```

The inventory freezes prior v27 code/results and binds all new source snapshots,
packet archives, tests, work/timing ledgers and audit outputs. Offline replay
needs the inherited Python/NumPy/Pillow environment and no original video
download or hardware connection. This branch installs no native Sunshine,
ESP32 firmware or FPGA bitstream.
