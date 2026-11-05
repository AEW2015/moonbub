# V38 prediction inventory

This inventory reviews the v20–v37 plans/results and the corresponding experiment
READMEs. It is a guide to prior evidence, not a new benchmark. The current
comparison still has a **4.19×–11.57×** video-byte gap to the sampled HEVC/AV1
anchors after removing the identical HUD and modeled bindings. Those are
different-quality sampled points, not a matched-quality rate-distortion result.
No experiment below proves custom-codec superiority.

## Methods already tried

| Method and evidence | What was measured | Scope and finding |
|---|---|---|
| Integer temporal block motion, zero/global/block search, and residual SKIP/pruning ([GM25 study](../experiments/python-game-base-motion-v25-study/README.md), [SR01](../experiments/python-game-skip-residual-study/README.md)) | Actual packets with reconstructed references; block sizes 16/32; bounded integer vectors; exact dense/split zero/DC/full residuals and lossy zero/DC pruning | Causal cohorts and separate synthetic controls. Source-selected motion often loses to zero plus residual RDO. Prune-4 saves bytes but changes error and can worsen source MSE; no general win. |
| Fractional local block refinement ([GM26](../experiments/python-game-prediction-v26-study/README.md), unified in [GM27](../experiments/python-game-unified-v27-study/README.md)) | Half-pixel candidates around coarse integer winners; actual complete candidate bytes and causal decode/reference history | In the 48-frame causal selector, half32 saves 8.087% / 6.107% vs v25 zero and slightly improves aggregate MSE on the two retained windows. This remains the strongest measured motion-related complete-byte result in the current codec lineage; all losing candidates are paid. |
| Sampled search and tap-aware prediction ([v28](../experiments/python-game-search-v28-study/README.md), [taps](../experiments/python-game-taps-v28-study/README.md)) | Lower-cost coarse/refine search; exact-equivalent predictor gather optimization | Six causal cohorts: mixed sample search is 2.29–2.40× faster but spends 3.28–3.30% more complete bytes; a less aggressive option also spends bytes. Tap-aware arithmetic cuts prediction component time 2.462× with identical output, not coding bytes. |
| Quiet-block gating and source-error guards ([v29 docs](custom-codec-prototype-v29-2026-11-04.md), [motion gate](../experiments/python-game-motion-gate-study/README.md)) | Keep quiet blocks at zero; search only active blocks; compare actual complete candidate | Causal primary grows 2.19% in bytes and 1.28% in MSE; complex changes −0.15% bytes / +0.078% MSE. The cheap screen declines motion on all real temporal/held-out inputs; it misses useful choices on synthetic motion. |
| Residual-band deletion/shrink ([v30 docs](custom-codec-prototype-v30-2026-11-04.md), [shrink v32](../experiments/python-game-shrink-v32-study/README.md), [controller v32](../experiments/python-game-controller-v32-study/README.md)) | AC-tail cutoffs with protected low-frequency/ROI coefficients; strict and bounded block error | Small or inconsistent byte changes with substantial extra trial cost. Later causal evidence found negligible/worse totals and no reason to replace the earlier budget policy. A single-block or fixed-reference win is not sufficient. |
| Global/cross/grid predictors ([global v33](../experiments/python-game-global-v33-study/README.md), [wide v32](../experiments/python-game-wide-motion-v32-study/README.md), [wide escapes](../experiments/python-game-wide-escape-v32-study/README.md)) | Shared global translation plus local choices; integer-grid vectors; expanded motion range with actual residual re-encode and side-byte accounting | Causal global alternatives save host/search or logical reads but increase bytes and MSE. Wider search reduces residual bytes 1.04% / 1.47%; paid raw-vector overhead makes complete bodies larger. Sparse wide syntax narrows the penalty but remains a <1% prospective gain from a noncausal fixed-reference probe, not a causal accepted stream. |
| Parent32/child16 motion hierarchy ([split v33](../experiments/python-game-split-v33-study/README.md), [HM34](../experiments/python-game-hierarchy-v34-study/README.md), [selective v34](../experiments/python-game-selective-v34-study/README.md)) | Actual parent-plus-child syntax, sparse corrections/masks, and fixed-quota refinement | The v34 full hierarchy saves 0.40% / 0.95% complete causal bytes but raises complex MSE and costs substantially more host time. Selective fixed-reference search reduced scoring operations but admitted no candidate; raw bytes/error/reference reads regressed. Hierarchy does not reduce measured logical prediction reads. |
| Recent reconstructed-reference promotion ([AR01](../experiments/python-game-recent-reference-study/README.md)) | Explicitly ACKed/promoted past P frame, with bounded bank/lease rules and real packet bytes | On two short windows plus one 180-ID related held-out sequence, recent-8 reference reduces complete bytes 25–29% vs the same immutable-reference envelope, with small PSNR shifts. Promotion reconstruction, tags, bank storage and feedback are paid; it is an older GM01-family format and not a measured gain on current GM27/CN36. |
| Hidden-region source masking and canonical hidden references ([opaque v34](../experiments/python-game-opaque-v34-study/README.md), [aligned v35](../experiments/python-game-aligned-v35-study/README.md), [controller v35](../experiments/python-game-controller-v35-study/README.md), [CN36](custom-codec-prototype-v36-2026-11-04.md), [CS37](custom-codec-prototype-v37-2026-11-04.md)) | Mask only transform/interpolation-support-safe opaque-HUD regions; CN36 normalizes hidden reconstructed samples before reference commit; CS37 omits hidden blocks implicitly | Unnormalized masking saves about 3–4% complete bytes but changes causal references and slightly worsens MSE despite precodec-visible equality. CN36 skip saves 4.10% / 4.19% vs fixed legacy. CS37 adds 1.505% / 0.277% over CN36. The full causal equality evidence is limited to retained short clips; the nonzero-motion extension is a directed six-frame probe. |
| Exact zero-motion implementation ([direct v37](../experiments/python-game-direct-v37-study/README.md), [analysis v37](../experiments/python-game-analysis-v37-study/README.md)) | Remove redundant serialization/reparse/reconstruction; bypass zero-weight four-tap analysis with exact copy prediction | Paired sender service improves, but bytes/pixels do not. The fast analyzer is narrowly fixed-zero; it is not acceleration of searched motion. Means remain above 33.33 ms before receiver or transport. |

## Spatial prediction: what the inventory does and does not cover

Spatial predictors exist in adjacent components. HUD patch coders use
intra-left/row, previous-patch, global/tile prediction and row-delta modes
([HD25/HX32](../experiments/python-game-hud-v32-study/README.md),
[HX33](../experiments/python-game-hud-runs-v33-study/README.md)). The standalone
tile study uses left/above and MED edge predictors ([MP01](../experiments/python-predictor-study/README.md)); its 38–42% reduction vs row-reset DPCM is for the same quantized image and its own still-large rates, not the lossy temporal base codec. ROI maps ([RG01](../experiments/python-game-roi-study/README.md)) change quantization priorities, not prediction.

Within the audited v25–v37 base-video experiments, the tested predictors are
constant key prediction, zero displacement, global translation, bounded
per-block integer/fractional motion, hierarchical child corrections, and
reference promotion. I found no full causal base-video experiment that selects
a spatial intra predictor per transform block and compares its actual packet
against temporal prediction. This is a bounded inventory finding, not a claim
that no earlier prototype anywhere tried it.

## Candidate hypotheses for a bounded next codec experiment

These are proposals only. Start with a small, deterministic mode set and a
bit-exact scalar decoder; serialize every candidate including its mode/partition
overhead and keep the incumbent on ties. Carry the winning decoded reconstruction
into the next frame. Compare whole causal streams against the current v36/v37
control, not source-only or matched-reference probes.

1. **Temporal SKIP/copy plus sparse exceptions.** Reuse the already accepted
   reference for exact copy on blocks with zero residual, and code a bounded
   raster run of changed blocks with existing residual syntax. Existing zero/DC
   plane and block modes show the concept, but a compact, mode-explicit skip-run
   grammar integrated with current exact HUD/reference semantics could avoid
   per-block entropy overhead. Measure actual complete bytes; do not assume a
   zero residual screening pass predicts the transform result.
2. **Spatial intra fallback per block.** Test a tiny menu such as temporal
   predictor, spatial DC/left, and one directional predictor using already
   reconstructed current-frame neighbors. Encode the chosen mode and residual;
   select only by exact complete coded size with quality/cap guards. HUD-side
   intra predictors are precedent for bounded arithmetic, not evidence this
   base-video mode will win. Include raster dependencies, boundary resets and
   decoder state in the cost.
3. **Small reference menu without a costly full search.** Compare current
   accepted reference and one explicitly retained older/promoted reference,
   optionally with a shared global translation before local residual. Recent-8
   reference results motivate testing, while promotion evidence shows that
   copies, tags, banks, drain and ACK costs must be included. Bound the list and
   reference lifetime; score/encode each candidate on actual reconstructed
   history and preserve reset/loss recovery.
4. **Sparse parent motion plus local corrections only where profitable.** HM34
   provides a bounded syntax and proves mode sizes, but causal whole-frame gains
   stayed below 1%. A new test should focus on a rate-aware admission rule that
   avoids child search/metadata unless predicted residual savings exceed actual
   syntax cost, then include all screening/search/encoding work and decoder
   reference traffic.

The aim is to test whether any mode changes residual bytes enough to address the
remaining 4–12× sampled video-byte gap while preserving a bounded FPGA decoder.
Do not combine independently measured percentages. Report matched original
inputs and HUD treatment, complete bytes, active and temporal quality, causal
reference hashes, maxima, sender cost, decoder memory/cycles and fallback cases.
Native ESP32 transport and FPGA cycles remain separate unmeasured deployment
gates; no proposal above implies 30 fps or an HEVC/AV1 win.
