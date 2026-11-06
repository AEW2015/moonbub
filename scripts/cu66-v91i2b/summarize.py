#!/usr/bin/env python3
"""Freeze the refill A/B evidence and the direct handoff to V91j."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v91i2b'
BASELINE = 'eb3ea59500115220f58d5075a05f4c1dc413bc6a'
SHARED = ['docs/gamebub-application-specific-codec-plan.md',
          'docs/gamebub-v91-v110-development-plan.md',
          'docs/literature-review-2026-11-06/README.md']
PRIMARY = ('actual_001', 'actual_006', 'actual_043', 'actual_031')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def main():
    audit = read(AREA / 'audit.json')
    assert audit['status'] == 'PASS_INDEPENDENT_REFILL_AND_EXACT_CONTROL_AUDIT'
    attempts, performance, fences = [], [], []
    for item in audit['attempts']:
        path = ROOT / item['path']
        assert sha(path) == item['sha256']
        report = read(path)
        assert report['status'] == 'PASS_BOUNDED_REFILL_OVERLAP_WITH_EXACT_CONTROL'
        assert all(sha(ROOT / name) == value for name, value in report['source_sha256'].items())
        cases = {}
        for label in ('serial', 'overlap'):
            rows = [json.loads(line) for line in (path.parent / f'simulation-{label}.jsonl').read_text().splitlines()]
            cases[label] = {(row['id'], row['memory_profile']): row for row in rows if row['type'] == 'case'}
            assert len(cases[label]) == 22
        for profile in (0, 1):
            before = sum(cases['serial'][identity, profile]['cycles'] for identity in PRIMARY)
            after = sum(cases['overlap'][identity, profile]['cycles'] for identity in PRIMARY)
            performance.append(dict(seed=report['seed'], memory_profile=profile,
                                    native_frames=4, serial_cycles=before, overlap_cycles=after,
                                    saved_cycles=before - after, reduction_percent=100 * (before - after) / before))
            for identity in PRIMARY:
                control, winner = cases['serial'][identity, profile], cases['overlap'][identity, profile]
                if profile == 0:
                    assert control['cycles'] - winner['cycles'] == 2 * winner['refill_bytes'] - 2 * winner['core_starts']
                fences.append(dict(seed=report['seed'], id=identity, memory_profile=profile,
                                   serial_start_to_coefficient_done=control['cycles'],
                                   overlap_start_to_coefficient_done=winner['cycles'],
                                   overlap_packet_complete_to_coefficient_done=winner['done_cycle'] - winner['last_input'],
                                   cache_preload_cycles=winner['cache_cycles']))
        assert report['verdicts'][0]['refill_overlap'] == 0 and report['verdicts'][1]['refill_overlap'] == 1
        assert [row['directed_checks'] for row in report['verdicts']] == [10, 12]
        assert report['standalone_verdict']['directed_checks'] == 12
        attempts.append(dict(path=str(path.relative_to(ROOT)), sha256=sha(path), seed=report['seed'],
                             verdicts=report['verdicts'], baseline_control=report['baseline_control'],
                             standalone_verdict=report['standalone_verdict']))
    assert {row['seed'] for row in attempts} == {911201, 911202}
    prior = {}
    for name in ('experiments/python-gamebub-v91i2/summary.json', 'experiments/python-gamebub-v91i2/audit.json',
                 'docs/cu66-v91i2/README.md', 'fpga/experiments/cu66-v91i2/cs88_pipeline_v91i2a.sv'):
        original = subprocess.check_output(['git', 'show', BASELINE + ':' + name], cwd=ROOT)
        assert hashlib.sha256(original).hexdigest() == sha(ROOT / name)
        prior[name] = sha(ROOT / name)
    readiness = read(AREA / 'v91j-reuse-readiness.json')
    assert readiness['status'] == 'PASS_CONSTANT_COMPATIBILITY'
    summary = dict(schema='cu66-v91i2b-bounded-refill-qualified-v1', status='PASS', baseline_revision=BASELINE,
                   attempts=attempts, native_frame_performance=performance, coefficient_fences=fences,
                   total_coefficient_comparisons=sum(v['dense_comparisons'] for r in attempts for v in r['verdicts']),
                   prior_evidence_unchanged=prior, queue_model_sha256=sha(AREA / 'queue_model.py'),
                   queue_model_report_sha256=sha(AREA / 'queue-results.json'),
                   audit_sha256=sha(AREA / 'audit.json'), independent_verifier_sha256=sha(AREA / 'verify_results.py'),
                   v91j_readiness_sha256=sha(AREA / 'v91j-reuse-readiness.json'),
                   performance_caveat='FAST isolates deterministic refill work; SLOW uses the same seeded service rule but not an identical absolute ready-low trace after scheduling changes.',
                   full_frame_publication_timestamp=None, full_frame_decode_under10ms_proven=False,
                   hardware_distinct_30fps_proven=False,
                   next_milestone='V91j directly: reuse/requalify existing dequantizer and Q14 IDCT behind bounded coefficient-tile assembly and epoch/metadata ownership. No further V91i subcheckpoint is required to start the supported BR88 path.')
    (AREA / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    manifest_path = AREA / 'bundle-manifest.json'
    paths = [ROOT / name for name in SHARED]
    for directory in ('docs/cu66-v91i2b', 'scripts/cu66-v91i2b',
                      'experiments/python-gamebub-v91i2b', 'fpga/experiments/cu66-v91i2b'):
        paths.extend(path for path in (ROOT / directory).rglob('*')
                     if path.is_file() and '__pycache__' not in path.parts and path != manifest_path)
    manifest = dict(schema='cu66-v91i2b-bundle-manifest-v1', baseline_revision=BASELINE,
                    files_sha256={str(path.relative_to(ROOT)): sha(path) for path in sorted(set(paths))},
                    prior_shared_plan_sha256={name: hashlib.sha256(subprocess.check_output(
                        ['git', 'show', BASELINE + ':' + name], cwd=ROOT)).hexdigest() for name in SHARED})
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    print('V91I2B_SUMMARY_PASS', summary['total_coefficient_comparisons'], 'coefficient checks;',
          len(manifest['files_sha256']), 'bundle files; next V91j')


if __name__ == '__main__':
    main()
