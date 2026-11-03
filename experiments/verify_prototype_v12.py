#!/usr/bin/env python3
"""Verify the v12 research snapshot without rerunning performance work."""
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
    return json.loads((ROOT / relative).read_text())


def source_path(original):
    marker = '/moonbub-30fps-study/'
    return ROOT / original.split(marker, 1)[1] if marker in original else Path(original)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sunshine-root', type=Path, default=ROOT.parent / 'sunshine-30fps-study')
    args = parser.parse_args()
    manifest = load('docs/prototype-v12-provenance.json')
    for relative, expected in manifest['file_sha256'].items():
        assert sha(ROOT / relative) == expected, ('snapshot', relative)
    bindings = 0
    for relative in manifest['run_artifacts']:
        result = load(relative)
        for original, expected in result['source_sha256'].items():
            assert sha(source_path(original)) == expected, ('executed source', relative, original)
            bindings += 1
    tests = 0
    for directory, expected in manifest['test_counts'].items():
        log = (ROOT / directory / 'tests.log').read_text()
        match = re.search(r'^Ran (\d+) tests? in ', log, re.M)
        assert match and int(match[1]) == expected and log.rstrip().endswith('OK'), directory
        tests += expected
    helpers = {}
    for directory in manifest['stored_helpers']:
        script = 'check_stored_results.py' if directory.endswith('refresh-study') else 'verify.py'
        completed = subprocess.run([sys.executable, str(ROOT / directory / script)],
                                   check=True, capture_output=True, text=True)
        helpers[directory] = completed.stdout.strip()
    subprocess.run([sys.executable, str(ROOT / 'experiments/python-game-refresh-study/analyze.py'), '--check'],
                   check=True, capture_output=True, text=True)

    audit = load('experiments/python-game-audit-v12-study/audit.json')
    assert not audit['evidence_gaps']
    assert audit['source_pins_stable_and_matching'] and audit['media_hashes_stable_and_matching']
    assert audit['sparse_audit']['unique_rgb_content_hashes'] == 92
    assert audit['memo_audit']['all_bitstreams_unchanged'] and audit['memo_audit']['memo_hits'] == 40
    assert audit['rate_motion_audit']['decision_rows'] == 462
    assert audit['rate_motion_audit']['actual_rate_admitted'] == 151
    assert audit['refresh_audit']['capture_events_summed_across_runs'] == 1020
    assert audit['refresh_audit']['runs_with_unresolved_work_at_end'] == 0
    assert not audit['refresh_audit']['physical_30fps_proven']

    missing = []
    for original, expected in manifest['input_sha256'].items():
        path = Path(original)
        if path.exists():
            assert sha(path) == expected, ('external media', original)
        else:
            missing.append(original)
    peer = args.sunshine_root / manifest['sunshine_readme']['path']
    peer_checked = peer.exists()
    if peer_checked:
        assert sha(peer) == manifest['sunshine_readme']['sha256'], 'paired Sunshine README'
    print(json.dumps({'snapshot_files': len(manifest['file_sha256']),
                      'executed_source_bindings': bindings, 'passing_recorded_tests': tests,
                      'read_only_helpers': helpers, 'controlled_refresh_analysis': 'passed',
                      'source_ids_in_sparse_pairs': 120, 'distinct_sparse_rgb_images': 92,
                      'memo_pairs': 156, 'actual_rate_decisions': 462, 'refresh_cases': 17,
                      'missing_external_media': missing, 'paired_sunshine_readme_checked': peer_checked,
                      'primary_target': '720x480 coded, 720x405 active, 30 distinct displayed fps',
                      'physical_30fps_proven': False}, indent=2))


if __name__ == '__main__':
    main()
