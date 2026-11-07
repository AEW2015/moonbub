# V104 source and functional audit

**Status: `PASS_EVIDENCE`.** This offline audit does not run simulations or vendor tools.

## Verified contract

- Baseline `[1d0a702a7587]` exists and is an ancestor of HEAD.
- The V99 q16 profile and V100 historical RTL inventory match their pinned Git baseline contents.
- The V104 regression uses the selected V102 memory/predicate sources as paired controls; both match baseline blobs.
- Candidate source SHA pins, manifests, original-source ancestry, production module headers and port ledgers are checked independently.
- Required lanes are DSP fresh 24/52, DSP canonical 88/84, control canonical 88/84, and combined canonical 88/84, each at seeds 104401 and 104402.
- Each paired receipt must retain exact same-seed transcripts and events, plus canonical bytes on canonical lanes; missing evidence remains PENDING.

## Results

The four paired lanes total 288 case-profile runs and 304 directed checks. Every same-seed baseline/candidate transcript, event stream, and canonical output matched. The control focused probe independently replays 2,445,067 clock edges and 112,409 retained geometry rows, including all 90 Y columns, 30 row pairs, 214 reset/start/cancel pulses and two frame wraps. The DSP focused probe independently replays 579,794 clock edges across seeds 104401/104402, 24,582 legal-value transactions per seed and 111,320,320 packed element comparisons. These are component behavioral checks; they do not prove mapped hardware speed.

- `PASS` `baseline_exists_and_is_ancestor`
- `PASS` `v99_profile_frozen`
- `PASS` `historical_v100_source_inventory_unchanged`
- `PASS` `regress_baseline_contract`
- `PASS` `selected_v102_sources_match_git_baseline`
- `PASS` `control_source_manifest_and_baseline_pins`
- `PASS` `control_production_header_and_port_ledger_unchanged`
- `PASS` `control_verification_adapters_exact`
- `PASS` `control_exact_recurrence_edits_reconstruct_candidate`
- `PASS` `control_candidate_is_stateful_coordinate_recurrence`
- `PASS` `dsp_source_manifest_and_baseline_pins`
- `PASS` `dsp_production_header_and_port_ledger_unchanged`
- `PASS` `dsp_verification_adapters_exact`
- `PASS` `dsp_candidate_has_registered_prefetch_datapath`
- `PASS` `control_failed_attempts_retained`
- `PASS` `focused_control_clocked_receipt_and_independent_python_replay`
- `PASS` `dsp_failed_attempts_retained`
- `PASS` `focused_dsp_clocked_receipt_and_independent_python_replay`
- `PASS` `paired_lane_dsp_fresh_paired_exact_receipt`
- `PASS` `paired_lane_dsp_canonical_paired_exact_receipt`
- `PASS` `paired_lane_control_canonical_paired_exact_receipt`
- `PASS` `paired_lane_combined_canonical_paired_exact_receipt`

The retained focused attempts include one control host-resource launch gate and two DSP stops (a host-resource gate and a strict GCC `-Werror` testbench-formatting failure). The attempts and hashes remain recorded; warning policy and RTL were not relaxed or changed to bypass them.

PASS_EVIDENCE qualifies only the checked source and component evidence. Public-cycle parity is covered by the paired transcript checks; the audit is not a full formal state-space proof, native timing, physical/product qualification, hardware 30 fps or under-10-ms decode qualification. Detailed pins and receipt metadata are in `experiments/python-gamebub-v104/source-audit.json`.
