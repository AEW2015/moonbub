#!/usr/bin/env python3
"""Freeze the audited V91i1 admission checkpoint and its source/artifact bundle."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
MODEL = ROOT / 'experiments/python-gamebub-v91i'
AREA = ROOT / 'fpga/experiments/cu66-v91i'
BASELINE = 'f4428dcda2b039f815495d50500695046ce7d4a0'
SHARED = ['docs/gamebub-application-specific-codec-plan.md',
          'docs/gamebub-v91-v110-development-plan.md',
          'docs/literature-review-2026-11-06/README.md']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def main():
    audit = load(MODEL / 'audit.json')
    assert audit['status'].startswith('PASS'), audit['status']
    index = load(MODEL / 'vectors/index.json')
    selected = []
    for seed in (911101, 911102):
        matches = []
        for path in sorted((AREA / 'admission-attempts').glob('*/results.json')):
            report = load(path)
            if report.get('seed') != seed or report['status'] != 'PASS_RESTRICTED_CS88_STRUCTURAL_ADMISSION':
                continue
            if not all(sha(ROOT / name) == digest for name, digest in report['source_sha256'].items()):
                continue
            if not all(sha(MODEL / 'vectors' / name) == digest for name, digest in report['vectors_sha256'].items()):
                continue
            matches.append((path, report))
        assert matches, f'No current-source passing attempt for seed {seed}'
        selected.append(matches[-1])
    assert [row['report'] for row in audit['selected_attempts']] == [
        str(path.relative_to(ROOT)) for path, _ in selected]
    entries = index['entries']
    actual = [e for e in entries if e['class_'] == 'retained_actual_fixture']
    rows = []
    for path, report in selected:
        records = [json.loads(line) for line in (path.parent / 'simulation.jsonl').read_text().splitlines()]
        cases = [r for r in records if r['type'] == 'case']
        assert {r['id'] for r in cases} == {e['id'] for e in entries}
        rows.append(dict(report=str(path.relative_to(ROOT)), report_sha256=sha(path),
                         seed=report['seed'], case_rows=report['case_rows'],
                         admitted_rows=report['admitted_rows'], rejected_rows=report['rejected_rows'],
                         verdict=report['verdict']))
    summary = dict(schema='cu66-v91i1-admission-checkpoint-v1', status='PASS',
                   baseline_revision=BASELINE, selected_attempts=rows,
                   python_model_sha256=sha(MODEL / 'admission-model.py'),
                   model_report_sha256=sha(MODEL / 'admission-results.json'),
                   audit_sha256=sha(MODEL / 'audit.json'), vector_index_sha256=sha(MODEL / 'vectors/index.json'),
                   retained_actual_fixture_rows=len(actual),
                   actual_fixture_unique_packet_bytes=len({e['packet_sha256'] for e in actual}),
                   actual_fixture_unique_cohort_frame_identities=len({(e['cohort'], e['fid']) for e in actual}),
                   total_vector_rows=len(entries),
                   dispositions=dict(Counter(str(e['expected_error']) for e in entries)),
                   scope='Restricted CS88 structural admission only, with a trusted accepted-reference snapshot; no entropy consumer or state publication.',
                   unchanged_v91h_evidence={name: sha(ROOT / name) for name in (
                       'experiments/python-gamebub-v91h/summary.json',
                       'experiments/python-gamebub-v91h/audit.json', 'docs/cu66-v91h/README.md')},
                   full_frame_publication_timestamp=None,
                   full_frame_decode_under10ms_proven=False, hardware_distinct_30fps_proven=False,
                   next_gate='V91i2 entropy dispatch, positional binding and bounded provisional transaction ownership.')
    for name, digest in summary['unchanged_v91h_evidence'].items():
        frozen = subprocess.check_output(['git', 'show', BASELINE + ':' + name], cwd=ROOT)
        assert hashlib.sha256(frozen).hexdigest() == digest, name
    (MODEL / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    directories = ['docs/cu66-v91i', 'scripts/cu66-v91i',
                   'experiments/python-gamebub-v91i', 'fpga/experiments/cu66-v91i']
    manifest_path = MODEL / 'bundle-manifest.json'
    paths = [ROOT / name for name in SHARED]
    for name in directories:
        paths.extend(p for p in (ROOT / name).rglob('*')
                     if p.is_file() and '__pycache__' not in p.parts and p != manifest_path)
    manifest = dict(schema='cu66-v91i1-bundle-manifest-v1', baseline_revision=BASELINE,
                    scope='All new checkpoint files plus three updated shared plans; manifest excludes itself.',
                    files_sha256={str(p.relative_to(ROOT)): sha(p) for p in sorted(set(paths))},
                    prior_shared_plan_sha256={name: hashlib.sha256(subprocess.check_output(
                        ['git', 'show', BASELINE + ':' + name], cwd=ROOT)).hexdigest() for name in SHARED})
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    print('V91I1_SUMMARY_PASS', len(entries), 'vectors', len(manifest['files_sha256']), 'bundle files')


if __name__ == '__main__':
    main()
