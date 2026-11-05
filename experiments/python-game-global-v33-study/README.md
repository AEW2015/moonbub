# Sparse camera translation and bounded local motion choices

This is a new host search operating point within unchanged GM27/CP27/JA27. Full
720×480 coded / 720×405 active geometry, exact HUD, key IDs 0/24 and the 49,152-byte
complete cap are retained. Three policies each maintain their own accepted,
decoded reference history; execution order rotates per frame. All candidates,
including losses, are actually encoded, source-scored, bound and archived.

The control repeats v32 `band_control` exactly in all 96 selected packet/ACK/pixel
comparisons. The alternatives retain the control's zero-motion candidate and
strict source-aware band selection, replacing the adaptive local search only:

- `global_cross`: stride-16 coarse global translation, stride-8 half-unit global
  refinement, then stride-4 per-block scoring of zero and a cross of nearby
  vectors. Coarse vectors span ±16 half-luma units; fine/local values remain
  within the current ±18 bound. A current-source quiet gate fixes quiet blocks
  to zero. Global scoring excludes UI regions, falls back if no usable blocks
  remain, and trims the highest quarter of normalized block errors. This is a
  heuristic, not an optimal motion estimate or distortion guarantee.
- `global_grid`: coarse translation and a small grid of local vectors, all
  divisible by four half-luma units. Every reference prediction is therefore
  integer at both luma and chroma resolution, enabling exact one-tap sampling.

The same strict tier selector compares actual source RGB error and full bytes
on each policy's own history. A local selector guard does not make different
causal histories equal-quality. These are per-block choices from a shared
translation menu, not arbitrary motion residuals or a new exception syntax.

| Window | Policy | Actual complete bytes (HU25) | Active MSE | Paid host policy ms/frame |
| --- | --- | ---: | ---: | ---: |
| Primary | Control | 552,619 | 14.386886 | 311.11 |
| Primary | Global cross | 570,115 | 14.425950 | 293.24 |
| Primary | Global grid | 571,086 | 14.397236 | 284.98 |
| Complex | Control | 1,229,773 | 26.303889 | 411.31 |
| Complex | Global cross | 1,256,403 | 26.628150 | 361.56 |
| Complex | Global grid | 1,266,182 | 26.658162 | 351.12 |

Cross saves 5.74% / 12.10% host policy time but increases bytes 3.17% / 2.17% and
MSE 0.27% / 1.23%. Grid saves 8.40% / 14.63% host policy time, with 3.34% / 2.96%
more bytes and 0.072% / 1.347% higher mean MSE. Keep the current control when
compression/quality are the deciding criteria; these are speed/resource options,
not rate-distortion improvements or new defaults.

| Logical reference-sample reads over 48 frames | Primary | Complex |
| --- | ---: | ---: |
| Control selected decoder predictions | 26,053,120 | 33,489,152 |
| Cross selected decoder predictions | 24,215,040 | 28,228,096 |
| Grid selected decoder predictions | 23,846,400 | 23,846,400 |

Grid reduces selected prediction reads 8.47% / 28.79%; all 46 P frames use exactly
518,400 reads. These are logical sample operations, not measured external-memory
transactions, cache misses, bytes or fitted FPGA bandwidth. Entropy, reference
writes, scanout and all other memory users still need service. Host search
reference gathers fall 94.92% / 96.75% for grid, a different counter from decoder
prediction reads. The actual whole-policy speedup is much smaller because other
encoder work dominates. Do not multiply this speedup by the separate shared-pair
study's speedup: the combined path has not been timed.

Paid policy time includes all analyses, candidate encodes, RGB quality scoring
and CP27 binding. Source acquisition/conversion, preencoded HUD generation,
offline debug decoding, archive I/O, network and display are excluded. Prediction
uses the existing exact tap-aware implementation. Sample counters count actual
scored points and reference gathers; array allocation, normalization, sorting,
loop bookkeeping and packet serialization remain paid in wall time. All Python
policies remain far above 33.33 ms per source; no native 30 fps claim follows.

Six focused tests cover quiet gating, known translation, bounds/UI-mask fallback,
integer-grid/tap domains, paid score-call sums, source-error admission, and
missing/duplicate/reordered replay cohorts. Offline verification re-decodes all
1,128 attempted packets, 288 accepted pairs and 6,082,560 exact HUD words. It
reconstructs separate causal histories, recomputes all source metrics and choices,
repeats all 184 non-key fast motion searches and reconciles paid work and summaries.

```sh
python -m unittest discover -s experiments/python-game-global-v33-study -v
python experiments/python-game-global-v33-study/verify.py
```

Next test shared encoder work on this path, selective confidence-triggered dense
fallback, and smaller motion blocks against actual whole-frame costs. A grid-only
hardware fast path should validate its vector domain and be measured with real
reference-memory arbitration before claiming a decoder resource or latency win.
