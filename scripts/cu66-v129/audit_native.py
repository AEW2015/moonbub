#!/usr/bin/env python3
"""Independent V129 preflight audit; fail closed on proof, source or recipe drift."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'experiments/python-gamebub-v120/handoff.json'
PARENT = ROOT / 'experiments/python-gamebub-v128/integration/results.json'
PROOF = ROOT / 'experiments/python-gamebub-v129/integration/results.json'
INDEPENDENT = ROOT / 'experiments/python-gamebub-v129/audit/full-independent.json'
FLOW = ROOT / 'fpga/experiments/cu66-v120-flow'
NATIVE = ROOT / 'scripts/cu66-v129/native.py'
IMAGE = 'sha256:dd51b5dd44148c23bb0059b929697243797022172d5efb01ffdd8b8dd7a89742'
CHANGES = {
    'fpga/experiments/cu66-v91/br88_rice_elastic.sv': 'fpga/experiments/cu66-v129-parser/br88_rice_elastic.sv',
    'fpga/experiments/cu66-v91g2/packed_scratch_v91g2.sv': 'fpga/experiments/cu66-v129-scratch/packed_scratch_v91g2.sv',
}


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
    path = args.preflight.resolve()
    p = load(path)
    parent = load(PARENT)
    q = load(PROOF)
    independent = load(INDEPENDENT)
    base = load(BASE)
    build = Path(p['build_external']).resolve()
    need(p['schema'] == 'v129-native-preflight-v1' and p['status'] == 'PREPARED_NOT_RUN', 'preflight status')
    need(sha(PARENT) == '57b48154c3e7beda86cfe347032e505841bcdb2d35e1b9e8e560f9d134848f20', 'V128 parent drift')
    need(parent['status'] == 'PASS_V128_RAW_FULL_FUNCTIONAL' and q['status'] == 'PASS_V129_FULL_FUNCTIONAL', 'functional index')
    need(q['all_original_oracles_retained'] is True and q['exact_B_public_cycles'] is True and
         q['declared_public_cycle_delta'] == 0 and q['assertions_disabled_or_downgraded'] is False, 'cycle/assertion contract')
    need(independent['status'] == 'PASS_INDEPENDENT_V129_FULL_FUNCTIONAL_AUDIT' and
         independent['integration_index_sha256'] == sha(PROOF) and independent['exact_comparisons'] == {
             'spatial_stdout_event_and_canonical_streams': 4,
             'peer_stdout_event_and_canonical_streams': 2,
             'parent_stdout_and_terminal_stream_sets': 4}, 'independent audit')
    origins = q['source_origins']
    need(p['source_contract']['source_origins'] == origins and len(origins) == 18 and
         set(origins) == set(parent['source_origins']), 'source composition')
    need({a for a in origins if origins[a] != parent['source_origins'][a]} == set(CHANGES), 'nondeclared changes')
    for alias, meta in origins.items():
        need(sha(ROOT / meta['path']) == meta['sha256'] == sha(build / 'snapshot' / alias), 'source/snapshot drift: ' + alias)
        if alias in CHANGES:
            need(meta['path'] == CHANGES[alias], 'candidate mismatch: ' + alias)
    substitutions = {parent['source_origins'][a]['path']: origins[a]['path'] for a in CHANGES}
    need(q['rtl_source_order'] == [substitutions.get(x, x) for x in parent['rtl_source_order']] and
         p['source_contract']['source_order'] == base['source_order'], 'source order')
    proof_pins = p['source_contract']['proof_pins']
    for source in (BASE, PARENT, PROOF, INDEPENDENT):
        need(proof_pins.get(str(source.relative_to(ROOT))) == sha(source), 'missing proof pin')
    need(set(q['stages']) == {'focused', 'spatial', 'peer', 'parent'}, 'missing stage')
    for stage, meta in q['stages'].items():
        selector, receipt = ROOT / meta['path'], ROOT / meta['receipt']['path']
        need(sha(selector) == meta['sha256'] == proof_pins[meta['path']] and
             sha(receipt) == meta['receipt']['sha256'] == proof_pins[meta['receipt']['path']], stage + ' pin')
        selected = load(selector)
        need((selected.get('selected_report') or selected.get('selected_receipt') or selected.get('path')) == meta['receipt']['path'], stage + ' selector')
        record = load(receipt)
        need(record.get('actual_RTL_run') is True and str(record.get('status','')).startswith('PASS') and
             record.get('assertions_disabled_or_downgraded', False) is False, stage + ' actual pass')
        for alias, candidate in CHANGES.items():
            need(record['source_sha256'].get(candidate) == origins[alias]['sha256'], stage + ' candidate pin')
        for source, digest in record['source_sha256'].items():
            need(sha(ROOT / source) == digest, stage + ' source drift')
        artifacts = record.get('artifact_sha256', record.get('artifacts_sha256', {}))
        need(bool(artifacts), stage + ' missing artifacts')
        for artifact, digest in artifacts.items():
            need(sha(receipt.parent / artifact) == digest, stage + ' artifact drift')
        cmds = [c if isinstance(c, list) else c['argv'] for c in record['commands']]
        compiles = [c for c in cmds if 'verilator' in c and '--cc' in c]
        need(bool(compiles) and all('--assert' in c and '-Wall' in c and '-Wno-fatal' not in c for c in compiles), stage + ' Verilator flags')
        executable = [c for c in compiles if '--exe' in c]
        need(bool(executable) and all('-CFLAGS' in c and '-Werror' in c[c.index('-CFLAGS') + 1] for c in executable), stage + ' warning flags')
    need(p['part'] == 'xc7a100tcsg324-1' and p['top'] == 'cs88_pipeline_v91k' and p['image_id'] == IMAGE, 'tool/part')
    need(p['clock_period_ns'] in (8.0,10.0) and p['start_mode'] == 'rtl' and p['cpus'] == 2 and
         p['max_threads'] == 2 and p['memory_limit_bytes'] == 8*1024**3 and
         p['memory_swap_limit_bytes'] == 8*1024**3 and p['timeout_seconds'] == 3600, 'clock/resource contract')
    for name in ('run.tcl','report.tcl'):
        need(sha(build / name) == p['recipe_sha256'][name] == base['recipe_sha256'][name], 'recipe drift')
    clock = FLOW / ('clock-125.xdc' if p['clock_period_ns'] == 8.0 else 'clock-100.xdc')
    need(sha(build / 'component.xdc') == sha(clock) == p['recipe_sha256']['component.xdc'], 'clock drift')
    need(sha(build / 'inputs.tcl') == p['recipe_sha256']['inputs.tcl'], 'input Tcl drift')
    # Reconstruct the complete Tcl independently: a matching hash alone would
    # not prove that synthesis actually reads the audited ordered snapshots.
    mapped = Path('/build') / build.name
    def word(value):
        value = str(value)
        need(not any(c in value for c in '{}\r\n'), 'unsafe Tcl path')
        return '{' + value + '}'
    order = base['source_order']
    label = '125' if p['clock_period_ns'] == 8.0 else '100'
    expected_tcl = [
        'set part xc7a100tcsg324-1',
        'set trial_id {parser-scratch-' + label + '}',
        'set start_mode {rtl}',
        'set expected_period_ns ' + str(p['clock_period_ns']),
        'set opt_directive {Default}',
        'set place_directive {ExtraNetDelay_high}',
        'set phys_directive {NONE}',
        'set route_directive {Default}',
        'set rtl_sources [list ' + ' '.join(word(mapped / 'snapshot' / n)
                                            for n in order['rtl_read_order_aliases']) + ']',
        'set include_dirs [list ' + ' '.join(word(mapped / 'snapshot' / n)
                                             for n in order['include_directory_aliases']) + ']',
        'set constraint_file ' + word(mapped / 'component.xdc'),
    ]
    need((build / 'inputs.tcl').read_text() == '\n'.join(expected_tcl) + '\n',
         'generated Tcl differs from audited ordered snapshots and recipe')
    runtext = (build / 'run.tcl').read_text()
    need(runtext.index('read_xdc $constraint_file') < runtext.index('synth_design -top'), 'clock order')
    forbidden = re.compile(r'\b(set_false_path|set_multicycle_path|set_clock_groups|set_max_delay|set_min_delay|disable_timing|waiver)\b', re.I)
    for name in ('run.tcl','report.tcl','component.xdc'):
        need(not forbidden.search((build / name).read_text()), 'timing exception')
    for rel, digest in p['tooling_sha256'].items():
        need(sha(ROOT / rel) == digest, 'tool drift')
    inputs = build / 'inputs.json'
    need(sha(inputs) == p['inputs_sha256'] and load(inputs) == {k:v for k,v in p.items() if k != 'inputs_sha256'}, 'input drift')
    result = {'schema':'v129-native-preflight-audit-v1', 'status':'PASS_V129_NATIVE_PREFLIGHT_AUDIT',
              'auditor':args.auditor, 'preflight_sha256':sha(path), 'native_source_sha256':sha(NATIVE),
              'audit_source_sha256':sha(Path(__file__)), 'independent_source_recipe_resource_checks':True,
              'source_snapshot_count':len(origins), 'changed_vs_v128':sorted(CHANGES),
              'recipe_sha256':p['recipe_sha256'], 'timing_exceptions_or_waivers':False}
    out = path.parent / 'audit.json'
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(out)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('V129_PREFLIGHT_AUDIT_FAIL:', exc, file=sys.stderr)
        raise SystemExit(1)
