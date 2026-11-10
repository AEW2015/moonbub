#!/usr/bin/env python3
"""Summarize matched readonly producer-family observations, retaining absent-path gaps."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pin(path):
    return dict(path=str(path.resolve().relative_to(ROOT)), sha256=sha(path))


def rows(path):
    with path.open() as stream:
        return list(csv.DictReader(stream, delimiter='\t'))


def observation(path):
    d = json.loads(path.read_text())
    assert d['status'] == 'PASS_READONLY_OBSERVATION' and d['checkpoint_unchanged']
    assert not d['qualification'] and not d['new_implementation'] and not d['hardware_contact']
    assert d['runner_sha256'] == sha(ROOT / 'scripts/cu66-v125/inspect_producer.py')
    assert d['script_sha256'] == sha(ROOT / 'scripts/cu66-v125/inspect_producer.tcl')
    assert sha(ROOT / d['native_receipt']['path']) == d['native_receipt']['sha256']
    for name, expected in d['artifact_sha256'].items():
        assert sha(path.parent / name) == expected, name
    families = {}
    for row in rows(path.parent / 'targeted-paths.tsv'):
        row['slack_ns'] = float(row['slack_ns'])
        row['data_path_ns'] = float(row['data_path_ns'])
        row['logic_levels'] = int(row['logic_levels'])
        name = row['family']
        if name not in families or row['slack_ns'] < families[name]['slack_ns']:
            families[name] = row
    return dict(receipt=pin(path), worst_paths=families,
                register_widths=rows(path.parent / 'register-width-summary.tsv'),
                gaps=rows(path.parent / 'query-gaps.tsv'),
                owner_net_observations=[r for r in rows(path.parent / 'inspection.tsv')
                                        if r['kind'].startswith('OWNER_LANE_NET')])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline', type=Path, required=True)
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--output', type=Path, default=ROOT /
                   'experiments/python-gamebub-v125/producer-observations.json')
    a = p.parse_args()
    baseline, candidate = observation(a.baseline), observation(a.candidate)
    names = sorted(set(baseline['worst_paths']) | set(candidate['worst_paths']))
    comparison = {}
    for name in names:
        b, c = baseline['worst_paths'].get(name), candidate['worst_paths'].get(name)
        comparison[name] = dict(baseline=b, candidate=c,
            slack_delta_ns=round(c['slack_ns'] - b['slack_ns'], 6) if b and c else None)
    result = dict(schema='v125-matched-readonly-producer-path-comparison-v1',
                  status='PASS_OBSERVATION_INTEGRITY', baseline=baseline,
                  candidate=candidate, comparison=comparison,
                  summarizer_sha256=sha(Path(__file__)),
                  qualification=False, new_implementation=False,
                  scope='Same query/declared family, not guaranteed identical physical endpoints. '
                        'Absent paths are gaps; a positive subset does not qualify global timing.')
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(dict(status=result['status'], families=len(comparison),
                          output=str(a.output.resolve().relative_to(ROOT)))))


if __name__ == '__main__':
    main()
