#!/usr/bin/env python3
"""Check that verification-only hardening preserves paired V78 transaction timing.

Final observation windows may differ. Compare every old per-transaction field
and all first-presentation milestones, retaining repeat/tail differences as
observations rather than silently rewriting them.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--new', required=True, help='V79 result path relative to repo')
    parser.add_argument('--baseline', default='fpga/experiments/cu66-v78/system/frames4-fixed30-tac2/results.json')
    parser.add_argument('--output', default='fpga/experiments/cu66-v79/paired-comparison.json')
    args = parser.parse_args()
    old_path, new_path = ROOT/args.baseline, ROOT/args.new
    old, new = (json.loads(p.read_text()) for p in (old_path, new_path))
    assert new['cohort'] == 0 and new['arrival_mode'] == old['arrival_mode'] and new['tac_ns'] == old['tac_ns']
    assert len(new['frames']) >= len(old['frames'])
    compared = 0
    changed = []
    same_length = len(new['frames']) == len(old['frames'])
    for before, after in zip(old['frames'], new['frames']):
        for key, value in before.items():
            assert after[key] == value, ('transaction changed', before['fid'], key, value, after[key])
            compared += 1
    observation_fields = {'native_hud_prepare_wall_ns', 'last_correct_pixel_ps', 'complete_rasters'}
    for before, after in zip(old['timings'], new['timings']):
        for key, value in before.items():
            if key in observation_fields and (not same_length or key == 'native_hud_prepare_wall_ns'):
                if value != after[key]:
                    changed.append(dict(generation=before['generation'], field=key,
                                        baseline=value, monitored=after[key]))
                continue
            assert after[key] == value, ('milestone changed', before['fid'], key, value, after[key])
            compared += 1
    if same_length:
        for key, value in old['summary'].items():
            assert new['summary'][key] == value, ('summary changed', key, value, new['summary'][key])
            compared += 1
    report = dict(schema='cu79-v78-paired-comparison-v1', status='PASS_UNCHANGED_PAIRED_TRANSACTIONS',
                  sources=len(old['frames']), exact_fields=compared,
                  comparison_mode='complete-paired-run' if same_length else 'paired-prefix',
                  source_sha256={str(p.relative_to(ROOT)): sha(p) for p in (old_path, new_path, Path(__file__).resolve())},
                  observation_differences=changed,
                  scope='Paired original fields and first full-raster milestones are identical. CPU wall time and repeat/final-tail observations are not timing-equivalence gates.',
                  limitations=['Not RTL formal equivalence, hardware timing or 30fps qualification.'])
    (ROOT/args.output).write_text(json.dumps(report, indent=2)+'\n')
    print(f'V79_PAIRED_COMPARISON_PASS sources={report["sources"]} exact_fields={compared}')


if __name__ == '__main__':
    main()
