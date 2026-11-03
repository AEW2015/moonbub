#!/usr/bin/env python3
"""Reconcile the v9 frozen software evidence, without rerunning timed campaigns."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(rel):
    return json.loads((ROOT / rel).read_text())


def resolve(path):
    marker = '/moonbub-30fps-study/'
    if marker in path:
        return ROOT / path.split(marker, 1)[1]
    p = Path(path)
    return p if p.is_absolute() else ROOT / p


def main():
    snapshot = load('docs/prototype-v9-provenance.json')
    for rel, expected in snapshot['file_sha256'].items():
        assert sha(ROOT / rel) == expected, ('snapshot', rel)
    bindings = 0
    for rel in snapshot['run_artifacts']:
        data = load(rel)
        for path, expected in data.get('source_sha256', {}).items():
            assert sha(resolve(path)) == expected, ('executed source', rel, path)
            bindings += 1
    tests = 0
    for rel, count in snapshot['test_counts'].items():
        log = (ROOT / rel / 'tests.log').read_text()
        match = re.search(r'^Ran (\d+) tests? in ', log, re.M)
        assert match and int(match[1]) == count and log.rstrip().endswith('OK'), rel
        tests += count
    helpers = {}
    for rel in ('experiments/python-game-pipeline-study/verify.py',
                'experiments/python-game-hud-study/verify.py'):
        result = subprocess.run([sys.executable, str(ROOT / rel)], check=True,
                                capture_output=True, text=True)
        helpers[rel] = json.loads(result.stdout)

    pipeline = load('experiments/python-game-pipeline-study/results.json')
    audit = load('experiments/python-game-audit-v9-study/audit.json')
    assert audit['source_pins_match_before_and_after']
    assert audit['external_media_hash_guard_match_before_and_after']
    assert not audit['inputs_missing']
    assert len(pipeline['cases']) == len(audit['pipeline']['cases']) == 12
    captures = prepared = decodes = eventual = 0
    measured_rates = []
    for case, audited in zip(pipeline['cases'], audit['pipeline']['cases']):
        r = case['result']
        captures += r['capture_count']
        prepared += r['prepared']
        decodes += len(r['commits'])
        ids = {p['id'] for p in r['presented']}
        eventual += len(ids)
        start, end = r['capture_window_ms']
        strict = {p['id'] for p in r['presented'] if start <= p['at_ms'] < end}
        assert len(strict) == audited['strict_count'] == r['metrics']['presented_count']
        assert len(ids) == audited['eventual_count']
        window = r['steady_window_ms']
        if window is not None:
            start, end = window
            assert end > start
            diagnostic = {p['id'] for p in r['presented'] if start <= p['at_ms'] < end}
            rate = len(diagnostic) * 1000 / (end - start)
            assert sorted(diagnostic) == audited['diagnostic_presentation_ids_in_steady_window']
            assert rate == audited['diagnostic_presentation_fps_rederived'] == r['metrics']['steady_fps']
            if case['kind'] == 'baseline' and r['config']['decoder_service'] == 'python_wall':
                measured_rates.append(rate)
    assert (captures, prepared, decodes, eventual) == (624, 576, 567, 567)
    assert sorted(measured_rates) == [27, 27, 28, 28]

    feedback = load('experiments/python-game-feedback-study/results.json')
    assert len(feedback['records']) == 8 and len(feedback['faults']) == 3
    assert feedback['all_resources_drained']
    assert all(r['decoded_rgb565_exact'] and r['feedback_matches_content']
               and r['payload_bytes_after_decode'] == 0 for r in feedback['records'])
    assert all(f['drained'] for f in feedback['faults'])
    assert feedback['forward_header_bytes'] == 31 and feedback['feedback_bytes'] == 24
    assert feedback['crc_residue_observation'] == {
        'distinct_valid_full_frame_crcs': 1, 'distinct_body_tags': 8}
    assert sum(r['unique_forward_ipv4_udp_bytes'] + r['duplicate_forward_ipv4_udp_bytes']
               for r in feedback['records']) == 40843
    assert sum(r['reverse_ipv4_udp_bytes'] for r in feedback['records']) == 416
    regression = load('experiments/python-game-feedback-study/regression.json')
    assert not regression['v8_gf01']['delivered_pin_retained_after_conflict']
    assert not regression['v8_gf01']['original_complete_can_commit']
    assert regression['v9_gf02']['delivered_pin_retained_after_conflict']
    assert regression['v9_gf02']['original_complete_can_commit']
    assert audit['hud']['main_patch_records'] == audit['hud']['main_patch_cap_failures'] == 36
    assert audit['hud']['main_roi_exact_word_records'] == 36
    assert audit['hud']['predictor_unchanged_from_display_only_patch_test']
    flat = load('experiments/python-game-hud-study/flat-results.json')['cases']
    assert [r['wrapped_bytes'] for r in flat] == [17894, 19963]
    assert all(not r['over_48k_cap'] and r['roi_rgb565_word_mismatches'] == 0 for r in flat)
    missing = []
    for path, expected in snapshot['input_sha256'].items():
        p = Path(path)
        if p.exists():
            assert sha(p) == expected, ('external input', path)
        else:
            missing.append(path)
    print(json.dumps({
        'snapshot_files': len(snapshot['file_sha256']),
        'executed_source_bindings': bindings, 'passing_tests': tests,
        'pipeline_cases': 12, 'capture_policy_evaluations': captures,
        'prepared': prepared, 'hash_checked_decodes': decodes,
        'measured_python_diagnostic_ids_per_second': sorted(set(measured_rates)),
        'golden_feedback_decodes': 8, 'functional_fault_campaigns': 3,
        'gf01_bug_reproduced_gf02_pin_retained': True,
        'wrapped_frames_rgb565_exact': 36, 'wrapped_frames_over_cap': 36,
        'favorable_flat_probe_bytes': [r['wrapped_bytes'] for r in flat],
        'missing_external_inputs': missing, 'helpers': helpers,
        'scope': 'Frozen software evidence checks; no network/hardware or real-time qualification'
    }, indent=2))


if __name__ == '__main__':
    main()
