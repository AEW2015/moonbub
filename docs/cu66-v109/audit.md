# V108 baseline audit for V109

Audited frozen V108 at repository HEAD `388208dcb73800d93e8c26bfb0c678485a7de133`.

- Composite receipt: [`v108-baseline-audit.json`](../../experiments/python-gamebub-v109/audit/v108-baseline-audit.json), source receipt `experiments/python-gamebub-v108/outtile-native/20261108T101802940240Z/receipt.json`, SHA-256 `e6f76901d9817dbeabedbf916370985cf5e99fc83f8243f20d82e88fb9241cfb`; source manifest SHA-256 `d159ea2b13ff8720d67b6ae8b5655d6625dc0346e8f648c8a3ef517c89e73a46`.
- Identity: `cs88_pipeline_v91k`, `xc7a100tcsg324-1`, 10.0 ns. All 18/18 source origins and 69/69 retained artifacts match receipt hashes.
- Routed result: WNS −2.020 ns, TNS −11717.641 ns, 16,953 setup failures; hold WHS +0.098 ns/0 failures; pulse WPWS +3.750 ns/0 failures. Routing errors 0, no-clock 0, unconstrained internal endpoints 0, combinational loops 0, latch loops 0. This is a routed component result and it **fails 100 MHz setup timing**.
- Functional evidence: the five V108 proof receipts referenced by `experiments/python-gamebub-v108/results.json` are actual RTL runs; each file hash and receipt status matches its declaration (3 focused PASS and 2 canonical PASS statuses). They establish only their stated component/canonical properties.
- No full custom top, board I/O timing, hardware 30 fps, or validated-decode-under-10-ms qualification is claimed. The V109 parent integration inventory is in [integration-gaps.md](integration-gaps.md).

## V109 terminal component routes and fetch proof

Independent raw-report and immutable-source audits are recorded in
[`native-initial-final.json`](../../experiments/python-gamebub-v109/audit/native-initial-final.json)
and [`fetch-focused-final.json`](../../experiments/python-gamebub-v109/audit/fetch-focused-final.json).
Both 10 ns Artix-7 component routes completed and parsed exactly against their
retained reports. Fault variant WNS/TNS is −1.589/−8342.999 ns; combined is
−1.737/−5988.869 ns. Both still fail setup, despite passing hold and pulse
checks, zero route errors, and zero no-clock/internal-unconstrained/loop findings.
All 18 origin and immutable snapshot hashes, four recipe hashes, two tool pins,
and 69 retained artifact hashes match for each receipt. Neither result qualifies
the complete parent or hardware.

The focused fetch ingress proof is actual RTL PASS for candidate SHA-256
`4d6a16d0b89aa067fe3e7acc01351ea0bacac694cc63fb681a1471ee4683d044`. It retains
the frozen V108 ingress oracle and active assertions: two 607-capture runs each,
plus two whole-ingress runs with 76 packets and 754,644 golden coefficients each.
Six negative owner-contract commands total (three indices × two modes) reject on the original assertion. The per-seed capture verdict repeats an expected-count field of six; that metadata is not an additional six commands for each seed. This focused proof is not a native timing or hardware qualification.

## Fetch plus fault canonical proof

[`fetch-canonical-final.json`](../../experiments/python-gamebub-v109/audit/fetch-canonical-final.json)
records an independent audit of the 18-source fetch/fault composition. Its five
candidate replacements are the fetch ingress synchronizer plus four fault
control sources. The actual RTL run passes 44 profiles and 42 directed checks
across the two frozen seeds. Per-seed stdout, event streams, and raw canonical
pixel output hashes match the retained V108 RTL reference exactly; the baseline
was reused and not rerun. The Verilator compile retained `--assert`, did not use
`-DNDEBUG`, and emitted no warnings. This is component canonical evidence only;
it does not claim native timing, complete-parent closure, or hardware operation.

## Request preparation focused proof

[`request-focused-final.json`](../../experiments/python-gamebub-v109/audit/request-focused-final.json)
records the actual RTL PASS for the request preparation candidate
`ac7260e749ace036495a162882fdb30fdb129d2c7ddde8df67bc2a8957f8f4b1`. The
frozen V108 ingress control (`6514a5f2…83c6`) remains the original side of the
public-interface oracle, with the fetch-stage candidate (`4d6a16d0…d044`) as
its request-preparation baseline. Both capture seeds and both whole-ingress
seeds pass; each capture run includes 1,728 prepared cases. Across the proof, six
negative assertion commands run total (three indices × two modes); the per-seed
verdict count of six is shared-suite metadata. Whole-ingress runs each cover 76 packets
and 754,644 golden coefficients. Verilator assertions and `-Werror` were enabled,
with no warning output. This is focused component evidence only.


## Request plus fault canonical proof

[`request-canonical-final.json`](../../experiments/python-gamebub-v109/audit/request-canonical-final.json)
records an independent audit of the 18-source request/fault composition. Its
five replacements are the request ingress synchronizer and four fault-control
sources. Actual RTL passes 44 profiles and 42 directed checks over both frozen
seeds. Stdout, event streams, and raw canonical outputs match the retained V108
reference hashes exactly; the unchanged V108 baseline was reused. Focused fault,
fetch, and request proof receipts all match their pins and PASS status. The
compile retained `--assert`, omitted `-DNDEBUG`, and emitted no warnings. These
results do not claim native timing or hardware qualification.

## FETCH native component route

[`fetch-native-final.json`](../../experiments/python-gamebub-v109/audit/fetch-native-final.json)
records an independent parse and pin check for the terminal FETCH route. The
10 ns component route completed with WNS −1.635 ns, TNS −8267.052 ns, and 13,122
setup failures. Hold is +0.044 ns with zero failures; pulse width is +3.750 ns
with zero failures; routing errors, no-clock, unconstrained internal endpoints,
multiple clocks, and loop checks are all zero. The measured worst path is from
`coefficients/child/scratch/state_reg[0]/C` to
`transform/coefficient_banks[1].words[49].value_reg[2]/CE`, with 10 logic levels
and 11.346 ns data delay. All 18 source snapshots/origins, recipe/tool pins, and
69 retained artifact hashes match. This component result fails 100 MHz setup and
does not qualify the production parent or hardware.

## Documentation link and reproduction audit

On 2026-11-08, all 75 relative Markdown file links across the 13 `docs/cu66-v109/*.md` files resolved; external URLs and anchor-only fragments were excluded. The five executable paths shown in `reproduce.md` (four canonical runners and the replay exporter) exist at the documented repository paths. Its additional `summarize.py` and `cycle_budget.py` references also exist. The reproduction text correctly distinguishes the 10 ns component target from board timing and states that neither OOC routes nor regression workloads establish hardware 30 fps or validated decoding below 10 ms.

The root `README.md` is awaiting the planned final results refresh: its physical table and fetch narrative stop at the first three native rows and describe the fetch native route as running, so they omit later completed fetch/request evidence. The focused `fetch.md` and `request.md` receipt paragraphs likewise still say canonical/native qualification remains separate even though those later stages have since run; consult the terminal receipts and final audit JSONs for status. These are stale-status statements, not hardware qualification claims. The six negative subprocesses in each focused ingress proof are six actual commands total across the suite, not six commands per positive seed.

## REQUEST native terminal receipt audit

Independently reparsed the terminal REQUEST native route reports and matched the retained parser result. Receipt SHA-256 is `d61f6b6ecf24ffb26c658313be5fa918c8f57e15ec54a53c1e829e4f708ed0e6`. The run is a fresh RTL component route for `cs88_pipeline_v91k` on `xc7a100tcsg324-1` with the 10 ns clock loaded before synthesis. All 18 immutable source snapshots and all 95 retained artifact files matched their recorded SHA-256 values; the four recipe snapshots matched their recipe pins. Focused fault/fetch/request proofs and the request canonical actual RTL result passed their recorded source pins.

The routed result fails 100 MHz setup: WNS −2.275 ns, TNS −10,280.347 ns, 15,277 setup failures of 89,114. Hold WHS is +0.105 ns with zero failures; pulse WPWS is +3.750 ns with zero failures. All 66,188 routable nets were fully routed with zero routing errors. The worst setup path is `transform/fault_o_reg/C` to `producer_cell_cache_reg[0]_i_86/ENARDEN`, 14 logic levels and 11.748 ns data delay (2.192 ns logic, 9.556 ns routing). No board, full-parent, hardware 30 fps or validated-under-10-ms qualification follows from this component route. Detailed pins and raw report hashes are in `request-native-final.json`.

## Final derived summary audit

Independently checked the regenerated summary and CSV against all four terminal native receipts, recomputed the V108 delta fields, and validated all nine proof receipt hashes and statuses. The summary has four completed rows, no running rows, and selects fault-only as the highest WNS (−1.589 ns); all four routes fail the 100 MHz component setup gate. Hardware FPS, validated decode latency and integrated parent qualification remain explicitly false.

Rebuilt the row facts from the four pinned canonical actual-RTL result files and their candidate simulation transcripts. All 96 successful case counters match exactly (24 per composition), as do the published per-profile statistics; all four canonical input hashes and transcript artifact hashes match. These are testbench counters under a 1,000,000-cycle assumed budget, not calibrated publication latency. Current summary-script SHA-256: `dbdbddbe07b451a9956a5fd15e583cbb664cd5a608f35d22f20294c95f20e590`; cycle-budget script SHA-256: `8172d0b750de934f62156ef547fb5ed102ae775ff2c2be70cb3de8600da0fb57`. Full derived pins are in `summary-final.json`.
