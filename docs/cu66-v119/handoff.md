# V119 experimental hardware-development handoff

V119’s exact Source A component is qualified internally at 100 MHz by two separate fresh synthesis/place/route runs. Both have setup WNS +0.024 ns, hold WHS +0.028 ns, pulse margin +3.750 ns, zero setup/hold/pulse failures, zero unconstrained internal endpoints and zero routing errors. The fixed 125 MHz run fails setup at −2.105 ns. No source B was selected.

This is a measured development candidate. Keep V118 as the stable control: its qualified 100 MHz margin is +0.061 ns and its failing 125 MHz margin is −1.499 ns, both better than V119. No firmware, Sunshine host, ESP32 or board boot image was changed or deployed by this campaign.

The machine manifest is [handoff.json](../../experiments/python-gamebub-v119/handoff.json). It binds the exact 18 source files, source order, part/top, image, recipe, functional proofs and both positive native receipts. The source set has four changed RTL bodies relative to V118: scratch, producer, admission and reconstruction. The standalone prefix probe is not included in it.

- [Initial 100 MHz receipt](../../experiments/python-gamebub-v119/integrated-study/native/20261109T171312690398Z/receipt.json)
- [Fresh 100 MHz repeat](../../experiments/python-gamebub-v119/integrated-study/native/20261109T174007359715Z/receipt.json)
- [Failed 125 MHz target](../../experiments/python-gamebub-v119/integrated-study/native/20261109T171305710307Z/receipt.json)
- [Final measurements](../../experiments/python-gamebub-v119/results.json)
- [Stable V118 manifest](../../experiments/python-gamebub-v118/handoff.json)

Prepare a self-contained alias tree without invoking tools:

```bash
python3 scripts/cu66-v119/prepare_handoff.py \
  --output /absolute/new/v119-handoff \
  --mapped-path /build/v119-handoff
```

Use a new output directory. Omit `--mapped-path` when the prepared flow will use the output’s actual absolute host path. The builder rejects unsupported periods, duplicate initial/repeat receipts, nonpositive or nonterminal native receipts, and changed source/recipe/tool lineage before export. It copies all 18 files, the fixed 10 ns constraint and the original native core recipe; it does not contact hardware or consume a new implementation trial. The campaign’s successful preparation and fail-closed checks are in [handoff-preparation.json](../../experiments/python-gamebub-v119/audit/handoff-preparation.json).

Any new synthesis/implementation is a separate declared campaign. Actual board constraints, clock uncertainty, I/O/CDC and complete-parent/memory timing still need their own verification; this component’s external input/output timing is intentionally unspecified. Methodology warnings remain recorded rather than waived.

The functional suite passes exact tested V118 outputs, event order, owners and public cycles, including accepted physical debt through cancellation and retry. Fast/stalled row parent fixtures remain 1,145,104/1,553,197 model cycles. Their 11.451/15.532 ms conversions at 100 MHz are conditional calculations, not hardware timing. One key-frame/recovery fixture does not demonstrate sustained distinct-frame 30 fps. Both hardware milestones remain open.

The next work is the [causal ingress-control study](ingress-control-next.md). The mapped carry equations and standalone prefix RTL are ready to inform that study; neither is integrated into Source A or measured as a faster component.
