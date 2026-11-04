#!/usr/bin/env python3
"""Read-only reconciliation of v13 Python codec and finite execution evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(relative):
    return json.loads((ROOT/relative).read_text())


def resolve(original):
    marker = '/moonbub-30fps-study/'
    return ROOT/original.split(marker, 1)[1] if marker in original else Path(original)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sunshine-root', type=Path, default=ROOT.parent/'sunshine-30fps-study')
    args = parser.parse_args()
    manifest = load('docs/prototype-v13-provenance.json')
    for path, expected in manifest['file_sha256'].items():
        assert sha(ROOT/path) == expected, ('snapshot', path)
    bindings = 0
    for path in manifest['run_artifacts']:
        result = load(path)
        for original, expected in result['source_sha256'].items():
            assert sha(resolve(original)) == expected, ('executed source', path, original)
            bindings += 1
    tests = 0
    for directory, expected in manifest['test_counts'].items():
        log = (ROOT/directory/'tests.log').read_text()
        count = re.search(r'^Ran (\d+) tests? in ', log, re.M)
        assert count and int(count[1]) == expected and log.rstrip().endswith('OK'), directory
        tests += expected
    helpers = {}
    for directory in manifest['stored_helpers']:
        result = subprocess.run([sys.executable, str(ROOT/directory/'verify.py')],
                                check=True, capture_output=True, text=True)
        helpers[directory] = result.stdout.strip()
    audit = load('experiments/python-game-audit-v13-study/audit.json')
    assert not audit['evidence_gaps']
    assert audit['source_pins']['all_match_and_stable']
    assert audit['cache_admission_audit']['all_compared_whole_packets_equal']
    assert audit['cache_admission_audit']['paired_source_ids_declared'] == 172
    assert audit['motion_gate_audit']['profile_decision_rows'] == 616
    assert audit['motion_gate_audit']['all_profile_candidate_attempts'] == 775
    assert audit['execution_audit']['capture_events_summed_across_runs'] == 1104
    assert audit['execution_audit']['runs_with_unresolved_work_at_end'] == 0
    assert audit['ui_cache_audit']['all_cached_packets_match_baseline']
    assert audit['ui_cache_audit']['cache_hit_attempts'] == 292
    assert audit['ui_cache_audit']['hits_on_changed_whole_source'] == 176
    assert audit['credit_window_audit']['case_count'] == 7
    assert audit['credit_window_audit']['capture_events_summed_across_runs'] == 780
    assert audit['credit_window_audit']['runs_with_unresolved_work_at_end'] == 0
    assert audit['credit_window_audit']['all_observed_peaks_fit_configured_pools']
    assert not audit['credit_window_audit']['hardware_timing_proven']
    missing = []
    for original, expected in manifest['input_sha256'].items():
        path = Path(original)
        if path.exists():
            assert sha(path) == expected, ('external media', original)
        else:
            missing.append(original)
    peer = args.sunshine_root/manifest['sunshine_readme']['path']
    peer_checked = peer.is_file()
    if peer_checked:
        assert sha(peer) == manifest['sunshine_readme']['sha256'], 'paired Sunshine README'
    print(json.dumps(dict(snapshot_files=len(manifest['file_sha256']),
                          executed_source_bindings=bindings, recorded_passing_tests=tests,
                          read_only_helpers=helpers, missing_external_media=missing,
                          paired_sunshine_readme_checked=peer_checked,
                          primary_target='720x480 coded,720x405 active,30 distinct displayed fps',
                          physical_30fps_proven=False), indent=2))


if __name__ == '__main__':
    main()
