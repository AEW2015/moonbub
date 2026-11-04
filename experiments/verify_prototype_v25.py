#!/usr/bin/env python3
"""Offline verification of retained v25 compression and functional evidence."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent


def safe(raw):
    p = Path(raw)
    assert not p.is_absolute() and '..' not in p.parts
    actual = (ROOT / p).resolve()
    assert actual.is_relative_to(ROOT)
    return actual


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path): return json.loads(safe(path).read_text())


def run(path, *args):
    p = subprocess.run([sys.executable, str(safe(path)), *args], capture_output=True, text=True)
    if p.returncode:
        sys.stderr.write(p.stdout + p.stderr)
        p.check_returncode()
    return p.stdout.strip()


def main():
    manifest = load('docs/prototype-v25-provenance.json')
    assert manifest['schema'] == 'gamebub-v25-provenance'
    for p, expected in manifest['file_sha256'].items(): assert sha(safe(p)) == expected, ('inventory', p)
    for p, expected in manifest['frozen_v24_sha256'].items(): assert sha(safe(p)) == expected, ('frozen v24', p)
    tests = 0
    for folder, expected in manifest['test_counts'].items():
        log = safe(folder+'/tests.log').read_text()
        found = re.search(r'^Ran (\d+) tests? in ', log, re.M)
        assert found and int(found[1]) == expected and log.rstrip().endswith('OK'), folder
        tests += expected
    snapshots = 0
    for artifact in manifest['run_artifacts']:
        for p, expected in load(artifact)['source_sha256'].items():
            assert sha(safe(p)) == expected, ('source snapshot', artifact, p)
            snapshots += 1
    helpers = {folder: run(folder+'/verify.py') for folder in manifest['stored_helpers']}
    audit = run('experiments/python-game-audit-v25-study/audit.py', '--check')
    combined = load('experiments/python-game-combined-motion-v25-study/results.json')
    assert combined['counts']['native_source_frames'] == 96
    assert combined['counts']['joint_decisions'] == 1344
    assert len(combined['cases']) == 28 and len(combined['rejected_cohorts']) == 4
    assert all(c['summary']['cap_fit_frames'] == 48 and c['summary']['hud_word_errors'] == 0 for c in combined['cases'])
    # The audit may refresh deterministic result files; every retained byte must
    # still match the inventory after all helper processes return.
    for p, expected in manifest['file_sha256'].items(): assert sha(safe(p)) == expected, ('post-replay inventory', p)
    print(json.dumps(dict(snapshot_files=len(manifest['file_sha256']), frozen_v24_files=len(manifest['frozen_v24_sha256']),
                          source_snapshot_bindings=snapshots, recorded_passing_tests=tests,
                          retained_verifiers=helpers, independent_audit=audit,
                          native_source_frames=96, selected_gm25_components=1344,
                          joint_decisions=1344, rejected_joint_cohorts=4,
                          exact_joint_hud_words=combined['counts']['exact_hud_words'],
                          physical_30fps_proven=False, native_endpoint_or_fpga_implemented=False,
                          hevc_av1_compression_parity_proven=False), indent=2))


if __name__ == '__main__': main()
