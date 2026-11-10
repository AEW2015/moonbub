#!/usr/bin/env python3
"""Independent V125 native preflight source, recipe, qualification and resource audit."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
FLOW = ROOT / 'fpga/experiments/cu66-v120-flow'
BASE = ROOT / 'experiments/python-gamebub-v120/handoff.json'
PARENT = ROOT / 'experiments/python-gamebub-v124/integration/results.json'
PARENT_SHA = '9514c117b7a3769babb3cb4bc9b1c6b4bf355212203c710695696b7b63fcf33f'
PARENT_RESULTS = ROOT / 'experiments/python-gamebub-v124/results.json'
PARENT_RESULTS_SHA = '7153ee06e4d30f8ebb28842453ea597d76cdf1add90488e3db037d899e72712e'
BASELINE_CONTROLS = {
    'initial_100': 'experiments/python-gamebub-v120/repair-study/native/20261109T205145534717Z/receipt.json',
    'repeat_100': 'experiments/python-gamebub-v120/repair-study/native/20261109T211623143358Z/receipt.json',
    'failed_125': 'experiments/python-gamebub-v120/repair-study/native/20261109T205145239583Z/receipt.json',
}
ALIAS = 'fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv'
CANDIDATE = 'fpga/experiments/cu66-v125-tile/cs88_admission_v91i2a.sv'
IMAGE = 'sha256:dd51b5dd44148c23bb0059b929697243797022172d5efb01ffdd8b8dd7a89742'
NATIVE = ROOT / 'scripts/cu66-v125/native.py'
GIB = 1024 ** 3


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def need(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('preflight', type=Path)
    ap.add_argument('--auditor', required=True)
    args = ap.parse_args()
    preflight_path = args.preflight.resolve()
    p = load(preflight_path)
    baseline = load(BASE)
    build = Path(p['build_external']).resolve()
    need(p['schema'] == 'v125-native-preflight-v1' and p['status'] == 'PREPARED_NOT_RUN',
         'Unexpected preflight schema/status')
    need(p['source_contract']['source_B'] == {
        'path': 'experiments/python-gamebub-v120/handoff.json', 'sha256': sha(BASE)},
         'Frozen Source B qualification pin changed')
    need(baseline['rtl_source_commit'] == '69c0f145d1e3969f5418645a79647634b312214b',
         'Unexpected Source B base commit')

    for meta in baseline['source_origins'].values():
        need(sha(ROOT / meta['path']) == meta['sha256'], 'Original Source B changed')
    need(sha(PARENT) == PARENT_SHA, 'V124 functional parent changed')
    parent = load(PARENT)
    need(parent['status'] == 'PASS_V124_OWNER_FULL_FUNCTIONAL', 'Invalid V124 parent')
    need(p['source_contract']['functional_parent'] == {'path': str(PARENT.relative_to(ROOT)), 'sha256': sha(PARENT)}, 'V124 source contract pin changed')
    base_origins = parent['source_origins']
    origins = p['source_contract']['source_origins']
    need(set(origins) == set(base_origins) and len(origins) == 18, 'Expected all 18 Source B aliases')
    need(p['source_contract']['changed_aliases'] == [ALIAS], 'Expected only admission tile predicates changed')
    need(origins[ALIAS]['path'] == CANDIDATE, 'Unexpected admission candidate path')
    changed = []
    for alias, meta in origins.items():
        path = ROOT / meta['path']
        need(path.is_file() and sha(path) == meta['sha256'], 'Current source hash mismatch: ' + alias)
        snap = build / 'snapshot' / alias
        need(snap.is_file() and sha(snap) == meta['sha256'], 'Prepared snapshot mismatch: ' + alias)
        if alias == ALIAS:
            need(meta['sha256'] != base_origins[alias]['sha256'], 'Admission candidate did not change')
            changed.append(alias)
        else:
            need(meta == base_origins[alias], 'Non-admission V124 source changed: ' + alias)
    need(changed == [ALIAS], 'Composition is not a single admission-source change')
    need(p['source_contract']['source_order'] == baseline['source_order'], 'Source order differs from V120')

    # Verify qualification selector/receipt pins from the supplied contract directly;
    # no checked_proofs helper from the launcher is imported or trusted.
    proof_pins = p['source_contract']['proof_pins']
    need(isinstance(proof_pins, dict) and proof_pins, 'Missing qualification proof pins')
    proof_index_rel = 'experiments/python-gamebub-v125/integration/results.json'
    need(proof_pins.get(proof_index_rel) == sha(ROOT / proof_index_rel),
         'Unified functional proof index is not pinned')
    proof_index = load(ROOT / proof_index_rel)
    need(proof_index.get('schema') == 'v125-tile-functional-composition-v1' and
         proof_index.get('status') == 'PASS_V125_TILE_FULL_FUNCTIONAL',
         'Unified functional proof index status/contract mismatch')
    need(proof_index.get('all_original_oracles_retained') is True and
         proof_index.get('exact_B_public_cycles') is True and
         proof_index.get('assertions_disabled_or_downgraded') is False,
         'Unified functional proof flags mismatch')
    stage_records = proof_index.get('stages', {})
    need(set(stage_records) == {'focused', 'spatial', 'peer', 'parent'},
         'Unified proof index must contain focused/spatial/peer/parent stages')
    selector_receipts = {}
    for stage, meta in stage_records.items():
        selector = ROOT / meta['path']
        need(selector.is_file() and sha(selector) == meta['sha256'], stage + ' selector pin mismatch')
        receipt_meta = meta['receipt']
        receipt = ROOT / receipt_meta['path']
        need(receipt.is_file() and sha(receipt) == receipt_meta['sha256'], stage + ' receipt pin mismatch')
        need(proof_pins.get(meta['path']) == meta['sha256'] and
             proof_pins.get(receipt_meta['path']) == receipt_meta['sha256'],
             stage + ' selector/receipt missing from proof pins')
        selector_receipts[meta['path']] = (stage, receipt_meta['path'], receipt_meta['sha256'])

    audited_receipts = set()
    for rel, digest in proof_pins.items():
        path = ROOT / rel
        need(path.is_file() and sha(path) == digest, 'Qualification pin mismatch: ' + rel)
        if path.suffix == '.json':
            record = load(path)
            audit_path = path
            if rel in selector_receipts:
                stage, receipt_rel, receipt_digest = selector_receipts[rel]
                selected = (record.get('selected_receipt') or record.get('selected_report') or
                            record.get('path'))
                need(selected == receipt_rel, stage + ' selector does not point to its pinned receipt')
                if record.get('selected_report_sha256'):
                    need(record['selected_report_sha256'] == receipt_digest,
                         stage + ' selector receipt digest mismatch')
                audit_path = ROOT / receipt_rel
                if 'selected_receipt' in record and 'source_sha256' in record:
                    need(load(audit_path) == {k: v for k, v in record.items() if k != 'selected_receipt'},
                         stage + ' full selector copy differs from pinned receipt')
            if audit_path == path and ('selected_report' in record or 'selected_receipt' in record or
                                       ('path' in record and 'sha256' in record and
                                        'source_sha256' not in record)):
                selected = record.get('selected_report') or record.get('selected_receipt') or record.get('path')
                if selected:
                    audit_path = ROOT / selected
                    expected = record.get('selected_report_sha256', record.get('sha256'))
                    if expected:
                        need(sha(audit_path) == expected, 'Qualification selector receipt mismatch: ' + rel)
            audit_rel = str(audit_path.relative_to(ROOT))
            if audit_rel in audited_receipts:
                continue
            audited_receipts.add(audit_rel)
            record = load(audit_path)
            for source, source_digest in record.get('source_sha256', {}).items():
                current = ROOT / source
                need(current.is_file() and sha(current) == source_digest,
                     'Qualification source changed: ' + source)
            artifacts = record.get('artifact_sha256', record.get('artifacts_sha256', {}))
            for artifact, artifact_digest in artifacts.items():
                artifact_path = audit_path.parent / artifact
                need(artifact_path.is_file() and sha(artifact_path) == artifact_digest,
                     'Qualification artifact changed: ' + audit_rel + ':' + artifact)
            if record.get('actual_RTL_run') is True:
                need(str(record.get('status', '')).startswith('PASS'),
                     'Executed qualification is not PASS: ' + audit_rel)
                commands = [c if isinstance(c, list) else c.get('argv', [])
                            for c in record.get('commands', [])]
                compiles = [c for c in commands if 'verilator' in c and '--cc' in c]
                need(bool(compiles) and all('--assert' in c and '-Wall' in c and
                     '-Wno-fatal' not in c for c in compiles),
                     'Executed qualification lacks strict Verilator compile: ' + audit_rel)
                executables = [c for c in compiles if '--exe' in c]
                libraries = [c for c in compiles if '--exe' not in c]
                need(bool(executables) and all('-CFLAGS' in c and
                     '-Werror' in c[c.index('-CFLAGS') + 1] for c in executables),
                     'Executed qualification lacks strict executable host flags: ' + audit_rel)
                need(all('--build' in c and '--top-module' in c and
                     c[c.index('--top-module') + 1] == 'v97_forward' for c in libraries),
                     'Unexpected library-only RTL compilation: ' + audit_rel)
                adapters = [c for c in commands if 'g++' in c]
                if libraries:
                    need(bool(adapters), 'Transport library lacks adapter build: ' + audit_rel)
                need(all(all(flag in c for flag in ('-std=c++17', '-Wall', '-Wextra', '-Werror'))
                     for c in adapters), 'Adapter warning flags changed: ' + audit_rel)


    # V120's two 100 MHz runs and failed 125 MHz run are immutable comparison controls.
    controls = {}
    expected_wns = {'initial_100': 0.174, 'repeat_100': 0.174, 'failed_125': -1.517}
    for label, rel in BASELINE_CONTROLS.items():
        path = ROOT / rel
        receipt = load(path)
        need(receipt['status'] == 'COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN', label + ' status changed')
        need(sha(path) == baseline[{
            'initial_100': 'initial_receipt', 'repeat_100': 'repeat_receipt',
            'failed_125': 'failed_B_125_MHz_receipt'}[label]]['sha256'], label + ' receipt pin changed')
        need(receipt['result']['timing']['WNS_ns'] == expected_wns[label], label + ' timing control changed')
        need(receipt['start_mode'] == 'rtl' and receipt['clock_loaded_before_synthesis_in_this_run'],
             label + ' is not a fresh RTL clocked run')
        controls[label] = receipt

    need(sha(PARENT_RESULTS) == PARENT_RESULTS_SHA, 'V124 native results pin changed')
    parent_results = load(PARENT_RESULTS)
    native_pin = parent_results['candidate_native_receipt']
    native_path = ROOT / native_pin['path']
    need(sha(native_path) == native_pin['sha256'], 'V124 native receipt pin changed')
    v124_native = load(native_path)
    need(v124_native['clock_period_ns'] == 8.0 and v124_native['result']['timing']['WNS_ns'] == -1.170, 'V124125 control changed')
    need(v124_native['source_contract']['source_origins'] == parent['source_origins'], 'V124 native/functional composition mismatch')
    controls['V124_125'] = v124_native

    need(p['part'] == 'xc7a100tcsg324-1' and p['top'] == 'cs88_pipeline_v91k', 'Part/top changed')
    need(p['image_id'] == IMAGE, 'Unexpected tool image')
    need(p['cpus'] == 2 and p['max_threads'] == 2 and p['max_heavy_jobs'] == 2,
         'CPU/concurrency limits changed')
    need(p['memory_limit_bytes'] == 8 * GIB and p['memory_swap_limit_bytes'] == 8 * GIB,
         'Memory limits changed')
    need(p['timeout_seconds'] == 3600, 'Job timeout changed')
    need(p['start_mode'] == 'rtl' and p['synth_directive_cli'] == 'omitted', 'Start/synthesis mode changed')
    need(p['core_recipe_reused_unchanged'] is True, 'Core recipe is not declared reused')

    # Compare the prepared Tcl/report against V120's handoff hashes and also against
    # every retained baseline route receipt, including the failed 125 MHz control.
    recipe = p['recipe_sha256']
    for name in ('run.tcl', 'report.tcl'):
        path = build / name
        need(path.is_file() and sha(path) == recipe[name], 'Prepared recipe hash mismatch: ' + name)
        need(recipe[name] == baseline['recipe_sha256'][name], 'V120 recipe hash changed: ' + name)
        for label, receipt in controls.items():
            need(receipt['recipe_sha256'][name] == recipe[name],
                 label + ' retained recipe mismatch: ' + name)
    period = p['clock_period_ns']
    need(period in (8.0, 10.0), 'Unexpected target clock period')
    clock_name = 'clock-125.xdc' if period == 8.0 else 'clock-100.xdc'
    clock = FLOW / clock_name
    component_xdc = build / 'component.xdc'
    need(sha(component_xdc) == sha(clock) == recipe['component.xdc'], 'Clock XDC is not exact V120 clock file')
    need(p['tooling_sha256'].get(str(clock.relative_to(ROOT))) == sha(clock), 'Clock tool pin mismatch')
    need(p['recipe_sha256']['inputs.tcl'] == sha(build / 'inputs.tcl'), 'Prepared inputs Tcl mismatch')
    run_text = (build / 'run.tcl').read_text()
    need(run_text.index('read_xdc $constraint_file') < run_text.index('synth_design -top'),
         'Clock is not loaded before synthesis')
    forbidden = re.compile(r'\b(set_false_path|set_multicycle_path|set_clock_groups|set_max_delay|set_min_delay|disable_timing|waiver)\b', re.I)
    for path in (build / 'run.tcl', build / 'report.tcl', component_xdc):
        need(not forbidden.search(path.read_text()), 'Timing exception/waiver token in ' + path.name)
    need('create_clock -name component_clk' in component_xdc.read_text(), 'Required single component clock missing')

    # All declared source/recipe/tool pins, including the exact launched runner, must
    # still match the prepared object. inputs.json is the launcher-generated record.
    for rel, digest in p['tooling_sha256'].items():
        path = ROOT / rel
        need(path.is_file() and sha(path) == digest, 'Tooling pin mismatch: ' + rel)
    inputs = build / 'inputs.json'
    need(inputs.is_file() and sha(inputs) == p['inputs_sha256'], 'Prepared inputs.json hash mismatch')
    need(load(inputs) == {k: v for k, v in p.items() if k != 'inputs_sha256'}, 'Preflight differs from prepared inputs')

    result = {
        'schema': 'v125-native-preflight-audit-v1',
        'status': 'PASS_V125_NATIVE_PREFLIGHT_AUDIT',
        'auditor': args.auditor,
        'preflight_sha256': sha(preflight_path),
        'native_source_sha256': sha(NATIVE),
        'audit_source_sha256': sha(Path(__file__)),
        'independent_source_recipe_resource_checks': True,
        'source_snapshot_count': len(origins),
        'changed_aliases': changed,
        'source_B_commit': baseline['rtl_source_commit'],
        'baseline_control_receipts': {k: sha(ROOT / v) for k, v in BASELINE_CONTROLS.items()},
        'recipe_sha256': {k: recipe[k] for k in ('run.tcl', 'report.tcl', 'component.xdc', 'inputs.tcl')},
        'resource_limits': {'cpus': 2, 'max_threads': 2, 'memory_limit_bytes': 8 * GIB,
                            'memory_swap_limit_bytes': 8 * GIB, 'timeout_seconds': 3600},
        'clock_loaded_before_synthesis': True,
        'timing_exceptions_or_waivers': False,
    }
    out = preflight_path.parent / 'audit.json'
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(out)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('V125_PREFLIGHT_AUDIT_FAIL:', exc, file=sys.stderr)
        raise SystemExit(1)
