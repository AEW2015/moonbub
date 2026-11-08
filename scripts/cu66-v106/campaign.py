"""V106 adaptive experiment policy; frozen initial RTL runners stay unchanged."""
from regress import BASELINE, BASELINE_OVERRIDES, LANES as INITIAL_LANES, OVERRIDES as INITIAL_OVERRIDES

SCRATCH = 'fpga/experiments/cu66-v91g2/packed_scratch_v91g2.sv'
PLAN = 'fpga/experiments/cu66-v106-plan/packed_scratch_v91g2.sv'
FOLLOWUP_OVERRIDES = {
    'lut-plan': {**INITIAL_OVERRIDES['lut'], SCRATCH: PLAN},
    'lut-storage-plan': {**INITIAL_OVERRIDES['lut-storage'], SCRATCH: PLAN},
}
FOLLOWUP_OVERRIDES['lut-storage-plan-context'] = {
    **FOLLOWUP_OVERRIDES['lut-storage-plan'],
    'fpga/experiments/cu66-v91b/br88_context.sv': 'fpga/experiments/cu66-v106-context/br88_context.sv',
}
FOLLOWUP_OVERRIDES['closure'] = {
    **FOLLOWUP_OVERRIDES['lut-storage-plan-context'],
    'fpga/experiments/cu66-v91/br88_rice_elastic.sv': 'fpga/experiments/cu66-v106-rice/br88_rice_elastic.sv',
}
FINAL_OVERRIDES = {'closure-prefix-telemetry': {
    **FOLLOWUP_OVERRIDES['closure'],
    'fpga/experiments/cu66-v91/br88_rice_elastic.sv': 'fpga/experiments/cu66-v106-prefix/br88_rice_elastic.sv',
    'fpga/experiments/cu66-v91h/br88_pipeline_v91h.sv': 'fpga/experiments/cu66-v106-telemetry/br88_pipeline_v91h.sv',
}}
PIPELINE_OVERRIDES = {'guarded-suffix-idct-cache': {
    **FINAL_OVERRIDES['closure-prefix-telemetry'],
    'fpga/experiments/cu66-v91/br88_rice_elastic.sv': 'fpga/experiments/cu66-v106-suffix/br88_rice_elastic.sv',
    'fpga/experiments/cu66-v69/inverse/cu66_idct8x8.sv': 'fpga/experiments/cu66-v106-idct/cu66_idct8x8.sv',
    'fpga/experiments/cu66-v91k/cs88_coefficients_v91k.sv': 'fpga/experiments/cu66-v106-producer-cache/cs88_coefficients_v91k.sv',
    'fpga/experiments/cu66-v91i2b/cs88_pipeline_v91i2b.sv': 'fpga/experiments/cu66-v106-producer-cache/cs88_pipeline_v91i2b.sv',
}}
LOCALITY_OVERRIDES = {'local-guards-scratch-area': {
    **PIPELINE_OVERRIDES['guarded-suffix-idct-cache'],
    'fpga/experiments/cu66-v91/br88_rice_elastic.sv': 'fpga/experiments/cu66-v106-suffix24/br88_rice_elastic.sv',
    'fpga/experiments/cu66-v69/inverse/cu66_idct8x8.sv': 'fpga/experiments/cu66-v106-idct-area/cu66_idct8x8.sv',
    'fpga/experiments/cu66-v91h/br88_packet_ingress_sync_v91h.sv': 'fpga/experiments/cu66-v106-ingress/br88_packet_ingress_sync_v91h.sv',
    'fpga/experiments/cu66-v91g2/packed_scratch_v91g2.sv': 'fpga/experiments/cu66-v106-scratch/packed_scratch_v91g2.sv',
}}
OVERRIDES = {**INITIAL_OVERRIDES, **FOLLOWUP_OVERRIDES, **FINAL_OVERRIDES, **PIPELINE_OVERRIDES, **LOCALITY_OVERRIDES}
FOLLOWUP_LANES = [(name, mode) for name in FOLLOWUP_OVERRIDES for mode in ('fresh', 'canonical')]
LANES = [*INITIAL_LANES, *FOLLOWUP_LANES,
         *[(name, mode) for name in [*FINAL_OVERRIDES, *LOCALITY_OVERRIDES] for mode in ('fresh', 'canonical')]]
NATIVE_PHASES = {name: False for name in ('lut', 'lut-storage-plan', 'closure', 'closure-prefix-telemetry', 'guarded-suffix-idct-cache', 'local-guards-scratch-area')}
REJECTED_FUNCTIONAL = {
    'guarded-suffix-idct-cache': {
        'fresh': 'FAIL_STRICT_PRODUCTION_LINT',
        'fresh_receipt': 'experiments/python-gamebub-v106/regression/guarded-suffix-idct-cache/fresh/attempts/20261108T023622841266Z-22231e3b/results.json',
        'canonical': 'NOT_RUN_REJECTED_CANDIDATE',
        'reason': 'Placement failed area/packing; strict full-production lint also rejects unused suffix_extracted[63:24]. Keep both failures; do not suppress warning or treat focused wrapper exports as production lint qualification. Replace with separately proved private24-bit projection and area-qualified IDCT in the sixth candidate.',
    },
}
DEFERRED_NATIVE = ['narrow', 'storage', 'lut-storage', 'lut-storage-memory', 'memory',
                   'lut-plan', 'lut-storage-plan-context']
REDIRECTION = {
    'reason': 'First LUT synthesis exposed serial scratch-plan sums; first LUT routing exposed full32 context division and Rice remaining-bit paths. Prioritize those measured violations to meet the fixed target.',
    'evidence': 'experiments/python-gamebub-v106/native/20261108T005012241750Z/reports/synth-setup-paths.rpt',
    'evidence_sha256': '6c732f65f791f71c6ef395609d3c4c5452cc2c8c21b224292da4a2c68f4985f8',
    'synthesis_WNS_ns': -5.303,
    'route_evidence': 'experiments/python-gamebub-v106/native/20261108T005012241750Z/reports/route-setup-paths.rpt',
    'route_evidence_sha256': '915b2331b769ee3a06d269482ce707bfecaa410d0056d9978392f35beb90873b',
    'route_WNS_ns': -7.130,
    'Rice_route_WNS_ns': -6.531,
    'closure_route_evidence': 'experiments/python-gamebub-v106/native/20261108T013032873883Z/reports/route-setup-paths.rpt',
    'closure_route_evidence_sha256': '4da106d91e7cb99b7ba84d83252621f3489fb7e1fd9663d2fd20bb234b4953bd',
    'closure_route_WNS_ns': -4.034,
    'final_trial_reason': 'Actual closure routing exposes Rice prefix and indexed telemetry counters. Compare exact parallel rank/static counters; retain separately measured IDCT operand selection, scratch and scale cones as open obligations. The IDCT path is not the V104 dequantizer product-prefetch block.',
    'prefix_telemetry_route_evidence': 'experiments/python-gamebub-v106/native/20261108T015540764948Z/reports/route-setup-paths.rpt',
    'prefix_telemetry_route_evidence_sha256': '83be4d6b68d4eb3f700499ad6dab938c4fb698af31d71b7fe3b674a8c4676d15',
    'prefix_telemetry_route_WNS_ns': -4.700,
    'prefix_telemetry_synth_evidence': 'experiments/python-gamebub-v106/native/20261108T015540764948Z/reports/synth-setup-paths.rpt',
    'prefix_telemetry_synth_evidence_sha256': 'c5ddc85de4180035ae2f25a8329be05f0640c070ee91692795bfa88fb803e001',
    'prefix_telemetry_synthesis_WNS_ns': -3.897,
    'pipeline_trial_reason': 'Parallel prefix factoring alone did not close the shared parser output path. Specialize SUFFIX extraction independently; prefetch actual IDCT operands within existing slots; cache the producer lookup coordinate at every original plane/tile transition. Preserve all public cycles and independently test before routing. No claim that prior path names remain final limiters.',
    'rejected_pipeline_receipt': 'experiments/python-gamebub-v106/native/20261108T021556317071Z/receipt.json',
    'rejected_pipeline_receipt_sha256': 'aa7d1db0875b5a5fe4312bb894eff2018453e79f70a7b6fb44929db0d26041f3',
    'rejected_pipeline_log': 'experiments/python-gamebub-v106/native/20261108T021556317071Z/vivado.log',
    'rejected_pipeline_log_sha256': 'c756c12a137e1f31d50725293cd5068ea41a948d3426e631a212694e98c19fe7',
    'rejected_functional_receipt_sha256': '748c8274bd9daca2d5229157391c2254c6b0718b87fc4fb9cb0ceade0b405a7d',
    'area_preflight_comparison': 'experiments/python-gamebub-v106/idct-area/unit-synthesis-comparison.json',
    'area_preflight_comparison_sha256': '037e606e21f05edfd8d79840b8db3f89c0f66dd6be1706dc689711bd09ccdd9e',
    'last_trial_reason': 'Reject the over-packed fifth full-flow attempt and its strict-production-lint failure. Retain every failure; canonical tests of that rejected candidate are not run. The sixth candidate uses the separately clocked-tested shared-selector IDCT, matched unit-area preflight, exact24-bit suffix temporary projection, live ingress replay-count cache and all-offset scratch/head position predecode. Require strict fresh pipeline PASS before launching the last full flow; keep actual parent input-capture timing open.',
    'scope': 'Deferred variants remain functionally tested, not natively measured. Initial runner declarations describe potential trials; this policy records the actual adaptive native campaign. All native runs keep full routing and 10ns constraints.',
}
