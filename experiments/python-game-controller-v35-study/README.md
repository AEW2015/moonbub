# Guarded transform-core masking on separate causal histories

This experiment uses unchanged GM27/CP34/HX33/JA34 syntax and the frozen atomic
receiver. Resolution remains 720×480 coded / 720×405 active; every 21,120-word
HUD is exact. There are two independent accepted histories per scene: original
control and guarded core8. Execution order alternates by frame. Keys are 0/24,
and all complete frames fit 49,152 bytes.

The guarded policy prepares both original and transform-core-masked source
planes against its **own currently accepted reference**. Both source families
pay all zero/half32 incumbent and strict-band evaluations. The original-source
family's complete strict winner is the shadow. Each masked candidate must fit,
save actual complete bytes strictly and have current source RGB SSE no higher
than that shadow. Ties retain original control. No future frames, retained
acceptance metrics or independent control reference enter the decision.

All 96 guarded frames select masked source. The full causal comparison is:

| Window | Policy | Actual complete bytes | Active MSE | Max bytes | Paid policy ms/frame |
| --- | --- | ---: | ---: | ---: | ---: |
| Primary | Control | 441,224 | 14.386886 | 23,321 | 229.49 |
| Primary | Guarded core8 | 422,128 | 14.393638 | 22,484 | 477.87 |
| Complex | Control | 1,068,678 | 26.303889 | 43,106 | 327.70 |
| Complex | Guarded core8 | 1,035,638 | 26.349043 | 41,155 | 667.53 |

Bytes fall **4.3280% / 3.0917%**, but mean MSE rises **0.04694% / 0.17166%**.
Every local guard passes; that does not establish equal quality against the
independent control history after hidden reference pixels have changed.
The own-history original shadows cost 497,449 / 1,187,655 bytes, which are
different baselines from the standalone control. Do not present the much larger
shadow-to-winner savings as improvement against the original stream.

All 96 standalone control packets, ACK content and displayed metrics reproduce
the v34 control. All 192 accepted frames, 1,128 candidate frames and 4,055,040
exact HUD words are retained. A candidate is evaluated against the original
RGB source after exact overlay, never against a masked quality target.

`mask_source(..., policy='core8')` replaces complete 8×8 Y/Cb/Cr blocks only when
their full RGB upsampling support is hidden by the exact HUD. All guarded inputs
pass exact precodec RGB8 equality outside the HUD. Its 4.61 / 4.90 ms mean cost,
including validation, coverage, copies and constant stores, is **included** in
paid policy time. Offline source-equivalence proof, fixture acquisition and
conversion, preencoded HUD generation, archive I/O, receiver, network and
display are excluded or separately recorded. All original and masked analyses,
shared-pair evaluations once each, RGB scores, bindings and selection are paid.
These Python timings do not establish native 30 fps.

Four fresh native runs consume the **exact accepted original/core8 input trace**
from the guarded controller. In this run all decisions are core8, so the native
anchors also reproduce the independent RAW core8 study. Each AU and once-only
extradata includes the same actual HX33 + 60-byte binding cost:

| Scene | Native codec | Parameter | Complete accounted bytes | Active MSE |
| --- | --- | ---: | ---: | ---: |
| Primary | HEVC/libx265 | 32 | 239,507 | 11.356621 |
| Primary | AV1/libsvtav1 | 48 | 222,648 | 12.471908 |
| Complex | HEVC/libx265 | 28 | 608,246 | 21.799157 |
| Complex | AV1/libsvtav1 | 38 | 596,944 | 20.025998 |

All native points have fewer bytes and lower MSE. PTS/DTS are 0..47, keys are
0/24 and encode/decode outputs are immediate with no flush-only frames. Native
binding is accounting, not implemented CP34 standards syntax or a Gamebub
standards hardware decoder. Options, versions, per-call work, AUs, extradata,
input hashes and decoded output hashes are retained. Source trace selection is
applied equally; the native encoders do not share custom reconstructed refs.

Three focused tests exercise integer guards/caps/ties/zero error, complete cohort
matrices, and actual guarded key/P publication with mask work included. Offline
verification re-decodes all candidates and accepted histories, checks source
equivalence and visible metrics, recomputes every guard and paid-work subtotal,
compares exact v34 control packets, and decodes all 192 native AUs against the
same trace. No old source or imported module is patched.

```sh
python -m unittest discover -s experiments/python-game-controller-v35-study -v
python experiments/python-game-controller-v35-study/verify.py
```

The result identifies reference semantics as the remaining quality issue. A
future codec-domain hidden-tile skip experiment should define and test canonical
hidden references in both baseline and skip variants, then prove visible and
future-reference equivalence. That is a proposed new experiment, not implemented
here and not a guarantee of parity with the original unmodified profile.
