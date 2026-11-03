#!/usr/bin/env python3
"""Verify the iteration5 portable snapshot and recorded run source bindings."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT = ROOT / 'docs/prototype-v5-provenance.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_recorded(path):
    p = Path(path)
    if not p.is_absolute():
        return ROOT / p
    # Recorded run hashes preserve the original machine path. Resolve the
    # checkout-relative source after relocation without changing that record.
    marker = '/moonbub-30fps-study/'
    return ROOT / path.split(marker, 1)[1] if marker in path else p


def main():
    snapshot = json.loads(SNAPSHOT.read_text())
    for path, expected in snapshot['file_sha256'].items():
        assert sha(ROOT / path) == expected, ('snapshot mismatch', path)
    bound = 0
    for rel in snapshot['run_artifacts']:
        doc = json.loads((ROOT / rel).read_text())
        for path, expected in doc.get('source_sha256', {}).items():
            assert sha(resolve_recorded(path)) == expected, ('executed source changed', rel, path)
            bound += 1
    for rel, expected in snapshot['test_counts'].items():
        log = (ROOT / rel / 'tests.log').read_text()
        match = re.search(r'^Ran (\d+) tests? in ', log, re.M)
        assert match and int(match[1]) == expected and log.rstrip().endswith('OK'), ('test log', rel)
    for name in ('results.json', 'anchor-results.json'):
        doc = json.loads((ROOT / 'experiments/python-fast-entropy-study' / name).read_text())
        assert sum(s['paired_checks'] for s in doc['scenes']) == 72
        for scene in doc['scenes']:
            assert len(scene['records']) == scene['paired_checks']
            for row in scene['records']:
                assert row['input_sha256'] == scene['manifest']['frame_sha256'][row['frame']]
    async_doc = json.loads((ROOT / 'experiments/python-async-anchor-study/results.json').read_text())
    assert len(async_doc['cases']) == 7
    for case in async_doc['cases']:
        r = case['result']
        assert all(slot is None for slot in r['unresolved_slots']) and not r['pending_controls'] and not r['pending_display_credits']
        assert r['peaks']['slots'] <= 2 and r['peaks']['sender_anchors'] <= 2 and r['peaks']['receiver_anchors'] <= 2
        assert r['peaks']['packet_bytes'] <= 2 * 49152
        assert r['transmitted_wire_bytes'] == r['control_wire_bytes'] + r['display_wire_bytes']
        assert r['metrics']['capture_count'] == len(case['manifest']['frame_sha256'])
    service = json.loads((ROOT / 'experiments/python-async-anchor-study/service-results.json').read_text())
    assert len(service['cases']) == 4
    assert service['timing_evidence_sha256'] == sha(ROOT / 'experiments/python-fast-entropy-study/results.json')
    # Inputs may intentionally live outside the checkout; check them if present,
    # and explicitly report missing inputs instead of treating that as a pass.
    checked_inputs, missing_inputs = [], []
    for path, expected in snapshot['input_sha256'].items():
        p = Path(path)
        if p.exists():
            assert sha(p) == expected, ('input changed', path)
            checked_inputs.append(path)
        else:
            missing_inputs.append(path)
    print(json.dumps({'snapshot_files_checked': len(snapshot['file_sha256']),
                      'executed_source_bindings_checked': bound,
                      'passing_tests': sum(snapshot['test_counts'].values()),
                      'paired_packet_checks': 144, 'async_cases': 7, 'service_cases': 4,
                      'input_files_checked': checked_inputs, 'missing_external_inputs': missing_inputs}, indent=2))


if __name__ == '__main__':
    main()
