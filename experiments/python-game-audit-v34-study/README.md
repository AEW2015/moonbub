# V34 independent audit

`baseline.json` carries the frozen v33 `band_control` plus the sampled HEVC and
AV1 points that meet its mean active RGB MSE and complete frame cap. All three
points share the exact HX33 HUD accounting and 60-byte binding. These figures
are prospective: there is no integrated HX33 custom endpoint. Native encoders
were not rerun.

The causal campaign now has six cohorts (two scenes × control, full hierarchy,
and selective 25%), 288 ordered accepted frames, 1,864 actual candidate
packets, and 96 exact accepted-base/pixel matches to the previous control. The
new CP34/HX33 receiver model validates components and publishes the exact
accepted base/HUD atomically. Full hierarchy reduces complete bytes by 1,767
in the primary scene with slightly lower MSE, and by 10,127 in the complex
scene while its aggregate MSE rises from 26.3039 to 26.3700. Each selected
child passes a strict current-frame guard against a control encoded on that
policy's own causal reference history; this local guard does not guarantee a
better cohort-wide quality result.

The fixed-reference HM34 and selective 25% studies are reported separately and
their gains are not added to the causal campaign. Standards points are
recomputed with the exact HX33 byte vector and 60-byte binding for every v34
policy. These native points remain prospective budgets, not an integrated
standard endpoint.

The opaque-HUD follow-up retains its important chroma-boundary result: masking
all Y/Cb/Cr samples in all rectangles changed visible RGB565 outside the UI on
all 96 frames. The safe mask preserves each rectangle's first chroma row and
column; its pre-codec picture is exactly equivalent after applying the exact
HUD on all 96 frames. In its own causal cohort, the safe mask saves 14,815 and
31,782 bytes against the corrected CP34/HX33 control, while original-source
MSE rises to 14.5659 and 26.5723. The comparison uses actual masked-input
HEVC/AV1 points with the same HX33 bytes and 60-byte binding. Historical HU25
totals are kept out of the savings calculation. Offline coefficient and mask
cost files are pinned; the two-bank inverse numbers remain a conditional
unclosed-clock model only.

`audit.py` verifies source pins, cohort completeness, packet component sums,
per-frame cap, own-reference causal history, accepted pixel/error evidence,
actual control shadows, every candidate's strict-byte/RGB selection, and paid
work subtotals. It also recomputes shared-HX33 HEVC/AV1 operating points and
keeps fixed-reference component evidence distinct from causal results. The
flat `source_sha256` map includes all study inputs and audit code. `--check`
requires byte-identical output without writing. `test_baseline.py` checks exact
integer SSE/sample MSE, common HUD/cap arithmetic, the primary/complex quality
tradeoff, and the safe-versus-full opaque mask and same-processed native
comparison.

Run the baseline checks with:

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest discover -s experiments/python-game-audit-v34-study -v
/home/lori/gamebub-streaming-prototype/.venv/bin/python experiments/python-game-audit-v34-study/audit.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python experiments/python-game-audit-v34-study/audit.py --check
```
