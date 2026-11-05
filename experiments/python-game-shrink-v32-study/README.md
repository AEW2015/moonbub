# V32 small-AC deletion and shrink candidates

This Python host-encoder prototype preserves GM27 syntax, the full 720×480
coded / 720×405 active geometry, DC and the lowest six zigzag coefficients,
q=8 ROI blocks and the inherited chroma halo. It introduces no new FPGA decoder
mode or ESP32 implementation.

`encode_with(runtime28_module, prepared, qmap, rdo_lambda=1,
policy='shrink_strict')` accepts the caller's owned Prepared object. The optional
policy `shrink_budget` allows a small explicitly bounded block-error increase.
`encode_prepared` is the adapter using this module's own runtime import.

## Fixed candidate menu

The encoder first reproduces v28 incumbent coefficients. Each unprotected 8×8
block then considers these four proposals, declared before corpus evaluation:

1. Zero AC coefficients with magnitude ≤1 at zigzag positions ≥6.
2. Zero AC coefficients with magnitude ≤2 at positions ≥6.
3. Decrement nonzero AC magnitudes by one at positions ≥21.
4. Decrement nonzero AC magnitudes by one at positions ≥6.

Signs are preserved unless a coefficient becomes zero. For every proposal, the
full trial plane is actually inverse-transformed and clipped against the same
source/prediction. Only blocks whose actual clipped YUV SSE passes the guard
are edited: strict uses no increase; budget allows
`min(incumbent_block_SSE//100,64)` extra squared-error units. Protected blocks
are restored unchanged. The encoder deduplicates resulting planes and executes
exact full-plane legacy/EC26 rate planning, including sparse runs, DC, Rice
selection, padding and raw fallback. The incumbent wins ties. Only the selected
payload is serialized, but every proposal transform and counter remains paid.

The final source error may differ in RGB, so the parent controller needs its
actual RGB565 shadow-quality guard as well. A strict per-block YUV rule alone
does not establish global RGB, temporal or perceptual equivalence.

## Matched-reference probe

The first 12 sources from each retained Mass Effect window use the same actual
accepted v28 exhaustive decoded references, predictor choices and quantizer maps.
Trial outputs never become later references in this component experiment.
Policy timing order rotates by source ID. Complete bytes include the actual
retained exact HU25 payload and 60-byte CP27 binding.

| Window | Policy | Complete bytes / 12 frames | Active MSE | Encode-prepared ms |
| --- | --- | ---: | ---: | ---: |
| 2600 | Baseline | 146,255 | 14.422069 | 33.14 |
| 2600 | Strict shrink menu | 146,001 | 14.421975 | 94.04 |
| 2600 | Budgeted shrink menu | 145,940 | 14.423520 | 94.39 |
| 7200 | Baseline | 349,101 | 26.382324 | 42.55 |
| 7200 | Strict shrink menu | 348,423 | 26.378251 | 116.88 |
| 7200 | Budgeted shrink menu | 348,288 | 26.378639 | 117.17 |

Strict saves **0.174% / 0.194%** complete bytes. Budget saves
**0.215% / 0.233%**. All 72 actual candidate envelopes fit 49,152 bytes and keep
the exact HUD. The strict complex sample changes 758 coefficient values, but
753 are zero deletions: only five are genuine nonzero-to-nonzero shrinks. The
budget complex sample has only two such shrinks. The primary samples select
zero-deletion changes only.

These are small gains at roughly 2.7–2.9× baseline Python encode work. The v30
whole-tail menu saved 270/706 strict and 330/854 budget bytes on this same
probe; this finer menu saves only 254/678 and 315/813 bytes. It is **slightly
weaker**, not a compression breakthrough or a recommended product default.
The result argues for better candidate targeting/context and sharing incumbent
work, rather than claiming any generic benefit from adding shrink operations.

Timing includes incumbent quantization/RDO, all proposal inverse transforms,
source-error scoring, deduplication, exact counters and final construction.
It excludes shared Prepared analysis, source acquisition, HUD generation,
debug decoding, archives, network and presentation. This is not full encoder
service, native endpoint performance, an FPGA clock/resource measurement or
physical 30 fps evidence. The same short precompressed windows are reused.

## Verification

```sh
python -m unittest discover -s experiments/python-game-shrink-v32-study -v
python experiments/python-game-shrink-v32-study/verify.py
```

Five focused tests cover exact reconstruction, actual nonzero shrink eligibility,
block SSE, DC/lowest-six/ROI/halo protection, bounded policy/ownership, decoder
equality and input immutability. The retained verifier repeats all 24 source
preparations and 72 candidate packets; checks all hashes, actual decoded source
RGB metrics, per-block YUV guards, no magnitude/sign growth, protected data,
exact minimum rate choices and whole-packet cap; and reconciles summary totals.
No frozen imported module globals are modified.
