#!/usr/bin/env python3
"""Collect completed V125 evidence; does not launch or qualify another run."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = 'experiments/python-gamebub-v125/'


def read(path):
    return json.loads((ROOT / path).read_text())


def pin(path):
    return dict(path=path, sha256=hashlib.sha256((ROOT / path).read_bytes()).hexdigest())


def main():
    nr = OUT + 'native/20261110T065004239267Z/receipt.json'
    br = 'experiments/python-gamebub-v124/native/20261110T044515396884Z/receipt.json'
    ar = OUT + 'audit/native-independent.json'
    fi = OUT + 'integration/results.json'
    native, baseline, audit, functional = map(read, (nr, br, ar, fi))
    assert native['component_route_finished'] and native['source_snapshot_unchanged']
    assert native['recipe_unchanged'] and not native['result']['component_internal_target_pass']
    assert audit['status'] == 'PASS_V125_INDEPENDENT_TERMINAL_EVIDENCE'
    assert not audit['failed_checks'] and not audit['errors']
    assert functional['status'] == 'PASS_V125_TILE_FULL_FUNCTIONAL'
    assert functional['declared_public_cycle_delta'] == 0
    for name in ('tile-observations.json', 'producer-observations.json'):
        assert read(OUT + name)['status'] == 'PASS_OBSERVATION_INTEGRITY'
    sources = functional['source_origins']
    previous = read('experiments/python-gamebub-v124/integration/results.json')['source_origins']
    changed = sorted(k for k in sources if sources[k] != previous[k])
    assert changed == ['fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv']
    refs = {
        'candidate_native_receipt': nr, 'baseline_native_receipt': br,
        'native_independent_audit': ar, 'functional_proof': fi,
        'functional_audit': OUT + 'audit/full-independent-v2.json',
        'retained_initial_audit_failure': OUT + 'audit/full-independent-initial-failure.json',
        'corrected_auditor_derivation': OUT + 'audit/full-independent-v2-derivation.json',
        'corrected_auditor_review': OUT + 'audit/functional-v2-review.json',
        'focus_selector': OUT + 'tile/results.json',
        'focus_independent_audit': OUT + 'audit/full-independent-focused.json',
        'readonly_tile_comparison': OUT + 'tile-observations.json',
        'readonly_producer_comparison': OUT + 'producer-observations.json',
        'readonly_producer_derivation': 'scripts/cu66-v125/producer-inspection-derivation.json',
        'python_tile_model': OUT + 'python-model/tile-model.json',
        'optional_boundary_model': OUT + 'boundary-model/results.json',
        'qualified_control_B100': 'experiments/python-gamebub-v120/handoff.json',
        'baseline_and_protected_file_audit': OUT + 'audit/baseline.json',
        'root_tooling_freeze': OUT + 'orchestration/root-tooling-freeze.json',
        'separate_prelaunch_dispatch_gate': OUT + 'orchestration/native-dispatch.json',
        'report': 'docs/cu66-v125/README.md',
        'timing_report': 'docs/cu66-v125/timing-results.md',
        'next_timing_proposal': 'docs/cu66-v125/next-timing.md',
    }
    timing = native['result']['timing']
    bt = baseline['result']['timing']
    result = dict(
        schema='v125-tile-predicates-component-study-v1',
        status='COMPLETED_BOUNDED_STUDY_125MHZ_SETUP_FAIL',
        base_commit='686805ab7b54441b09487df13d4540b434004a51',
        branch=subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip(),
        candidate_source=pin('fpga/experiments/cu66-v125-tile/cs88_admission_v91i2a.sv'),
        changed_aliases_from_V124=changed,
        candidate_result=native['result'], baseline_result=baseline['result'],
        timing_delta_from_V124={k: round(timing[k] - bt[k], 6) for k in timing},
        independent_native_evidence_checks=len(audit['checks']),
        declared_and_measured_public_cycle_delta=0,
        full_functional_raw_stream_sets=10,
        all_original_oracles_retained=True,
        assertions_disabled_or_downgraded=False,
        corrected_auditor_scope='Original failed order check retained; v2 checks core18 and V124 full stage order18/18/24 with admission substitution only. No RTL rerun.',
        root_prelaunch_gate_scope='Corrected v2 audit/review are separate root gates; frozen native proof pins bind functional index/stages.',
        new_payload_scalar_FFs=3,
        verification_owner_FFs_mapped=False,
        routed_resources=dict(LUT=33431, FF=43319, CARRY4=4223, RAMB36=32, RAMB18=12, DSP=42),
        resource_delta_from_V124=dict(LUT=7, FF=-175, CARRY4=3, RAMB36=0, RAMB18=0, DSP=0),
        admission_physical_FFs=dict(synthesis=6750, route=6751, delta_from_V124=22),
        control_sets=dict(synthesis=1250, route=1252),
        fresh_methodology_counts={'SYNTH-6': 28, 'TIMING-16': 76, 'TIMING-18': 1000, 'ULMTCS-1': 1},
        methodology_waivers_added=False, new_synthesis_attributes=[],
        row_parent=dict(
            post_final_accepted_input_to_validated_commit_cycles=dict(fast=1145104, stalled=1553197),
            assumed_complete_parent_MHz=125,
            projected_ms=dict(fast=9.160832, stalled=12.425576),
            minimum_stalled_cycles_to_save_for_strict_under10ms=303198,
            complete_parent_clock_physically_qualified=False),
        optional_boundary_model_implemented=False,
        candidate_recommended_for_125MHz_promotion=False,
        positive_same_source_repeat_performed=False,
        negative_same_source_rerouted=False,
        qualified_control_original_18_files_unchanged=True,
        broader_V125_board_qualification_milestone_complete=False,
        full_single_timebase_custom_endpoint_harness_complete=False,
        custom_CU66_profile_negotiation_complete=False,
        ESP32_CPU_WiFi_QSPI_physical_service_calibrated=False,
        whole_parent_routed_clock_qualified=False,
        sustained_hardware_30fps_qualified=False,
        validated_hardware_decode_under10ms_qualified=False,
        hardware_contact=False, board_bitstream_generated=False,
        next_timing_proposal_implemented=False,
        collector=pin('scripts/cu66-v125/collect_results.py'),
        **{name: pin(path) for name, path in refs.items()})
    path = ROOT / OUT / 'results.json'
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(result['status'], path.relative_to(ROOT))


if __name__ == '__main__':
    main()
