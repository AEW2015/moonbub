#!/usr/bin/env python3
"""Same-image HD22 projection kept separate from actual HC21 joint replay."""
from pathlib import Path
import argparse
import hashlib
import json
import math

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
GAP = HERE.parent / 'python-game-gap-span-study'


def load(path):
    return json.loads(Path(path).read_text())


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def wire(body, ack):
    n = math.ceil(body / 1008)
    return dict(forward=body + n * 75 + 128,
                reverse=n * 57 + 192 + ack + 28)


def build():
    actual = load(HERE / 'results.json')
    gap = load(GAP / 'results.json')
    cases = []
    for case in actual['cases']:
        if case['policy'] != 'fixed_v20_profiles':
            continue
        native = next(c for c in gap['cases'] if c['name'] == case['scene'])
        rows = []
        assert len(native['rows']) == len(case['rows']) == 48
        for a, g in zip(case['rows'], native['rows']):
            assert a['id'] == g['frame']
            assert a['hud_bytes'] == g['hc21_bytes']
            body = a['packet_bytes'] - g['hc21_bytes'] + g['proposed_same_overhead_bytes']
            assert body > 0
            rows.append(dict(id=a['id'], actual_joint_bytes=a['packet_bytes'],
                             projected_hd22_pair_bytes=body, hud_bytes_saved=g['hc21_bytes'] - g['proposed_same_overhead_bytes'],
                             assumed_new_dispatch_overhead_bytes=0,
                             complete_cap_fits=body <= 49152,
                             prospective_wire=wire(body, a['ack_bytes'])))
        old_bytes = sum(r['actual_joint_bytes'] for r in rows)
        new_bytes = sum(r['projected_hd22_pair_bytes'] for r in rows)
        forward = sum(r['prospective_wire']['forward'] for r in rows)
        reverse = sum(r['prospective_wire']['reverse'] for r in rows)
        cases.append(dict(scene=case['scene'], frames=48, actual_fixed_joint_bytes=old_bytes,
                          projected_hd22_pair_bytes=new_bytes,
                          fixed_image_complete_saving_percent=100 * (old_bytes - new_bytes) / old_bytes,
                          complete_cap_fits=sum(r['complete_cap_fits'] for r in rows),
                          maximum_projected_pair_bytes=max(r['projected_hd22_pair_bytes'] for r in rows),
                          projected_forward_Mbps_at30=forward / 48 * 30 * 8 / 1e6,
                          projected_reverse_Mbps_at30=reverse / 48 * 30 * 8 / 1e6,
                          rows=rows))
    paths = (HERE / 'analyze.py', HERE / 'results.json', GAP / 'results.json')
    return dict(schema='gamebub-v22-combined-projection',
                source_sha256={p.relative_to(ROOT).as_posix(): digest(p) for p in paths},
                cases=cases,
                scope=[
                    'Same original RGB565/cache histories and unchanged fixed-profile video base. All HD22 packets actually encode/decode in the separate gap study.',
                    'Replacing HC21 selected bodies with HD22 is a complete-byte projection with unchanged83-byte cache envelope and57-byte pair binder.',
                    'No new dispatch/version overhead is assumed; a real negotiated format may add bytes. Current joint receiver only implements HD21/HC21 dispatch.',
                    'Projected GF03/token/PC18/FG19/JA22/IPUDP counts are arithmetic, not a real integrated HD22 endpoint or hardware FPS result.'])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = build()
    path = HERE / 'analysis.json'
    if args.check:
        assert load(path) == result, 'analysis.json differs from recomputation'
        print('PASS: same-image HD22 projection; native dispatch and physical30fps remain unimplemented')
    else:
        path.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
        print(json.dumps([{k: v for k, v in c.items() if k != 'rows'} for c in result['cases']], indent=2))


if __name__ == '__main__':
    main()
