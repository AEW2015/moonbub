#!/usr/bin/env python3
"""Compare actual successful component runs; clock conversions are conditional."""
import csv
import hashlib
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v114'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def cases(path, expected_hash):
    assert sha(path) == expected_hash
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    verdict = [r for r in rows if r.get('type') == 'verdict']
    assert len(verdict) == 1 and verdict[0]['status'] == 'TEST_PASS'
    result = {(r['id'], r['memory_profile']): r for r in rows
              if r.get('type') == 'case' and r['error'] == 0}
    assert len(result) == 12
    return result


def main():
    new_path = AREA / 'spatial/results.json'
    old_path = ROOT / 'experiments/python-gamebub-v113/spatial/results.json'
    new, old = load(new_path), load(old_path)
    assert new['status'] == 'PASS_V114_SPATIAL_CANONICAL' and new['actual_RTL_run']
    assert old['status'] == 'PASS_V113_SPATIAL_CANONICAL' and old['actual_RTL_run']
    new_receipt, old_receipt = ROOT/new['selected_receipt'], ROOT/old['selected_receipt']
    assert load(new_receipt) == {k:v for k,v in new.items() if k != 'selected_receipt'}
    assert load(old_receipt) == {k:v for k,v in old.items() if k != 'selected_receipt'}
    rows, pins = [], {}
    for seed in (107601, 107602):
        name = f'candidate-{seed}-simulation.jsonl'
        a, b = new_receipt.parent/name, old_receipt.parent/name
        current = cases(a, new['artifact_sha256'][name])
        baseline = cases(b, old['artifact_sha256'][name])
        pins[str(a.relative_to(ROOT))] = sha(a)
        pins[str(b.relative_to(ROOT))] = sha(b)
        assert current.keys() == baseline.keys()
        for key, row in current.items():
            before = baseline[key]
            assert row['canonical']['samples'] == before['canonical']['samples'] == 518400
            first_to_done = row['done_cycle'] - row['first_input'] + 1
            first_to_pixel = row['canonical']['last_pixel_cycle'] - row['first_input'] + 1
            assert first_to_done >= first_to_pixel > 0
            rows.append(dict(seed=seed, case=key[0], profile=key[1],
                             baseline_cycles=before['cycles'], candidate_cycles=row['cycles'],
                             change_cycles=row['cycles']-before['cycles'],
                             component_first_byte_to_done_cycles=first_to_done,
                             component_first_byte_to_last_pixel_cycles=first_to_pixel,
                             conditional_done_ms_at125MHz=first_to_done/125000,
                             conditional_done_ms_at100MHz=first_to_done/100000))
    groups = {}
    for profile in (0, 1):
        selected = [r for r in rows if r['profile'] == profile]
        counts = [r['component_first_byte_to_done_cycles'] for r in selected]
        groups[str(profile)] = dict(cases=len(counts), minimum_cycles=min(counts),
                                    median_cycles=statistics.median(counts), maximum_cycles=max(counts),
                                    minimum_identity=min(selected,key=lambda r:r['component_first_byte_to_done_cycles']),
                                    maximum_identity=max(selected,key=lambda r:r['component_first_byte_to_done_cycles']))
    report = dict(schema='v114-actual-component-cycle-comparison-v1',
                  status='MEASURED_COMPONENT_CYCLES_CONDITIONAL_CLOCK_CONVERSIONS_ONLY',
                  qualification=dict(path=str(new_path.relative_to(ROOT)),sha256=sha(new_path)),
                  baseline=dict(path=str(old_path.relative_to(ROOT)),sha256=sha(old_path)),
                  source_sha256={str(Path(__file__).resolve().relative_to(ROOT)):sha(Path(__file__))},
                  transcript_sha256=pins, successful_case_profiles=24, rows=rows, profiles=groups,
                  assumed_conversion_clocks_Hz=[100000000,125000000],
                  hardware_30fps=False, complete_validated_decode_under10ms=False,
                  limits=['Actual component bench cycles, not host encode/capture/network/firmware/display latency.',
                          'First input means first accepted component byte; local done lacks complete C2/HUD seal and parent publication.',
                          'Failed-frame provisional prefixes are excluded from complete-frame latency statistics.',
                          'Profile0 fast service is deterministic; profile1 uses the same seeded policy but scheduling changes random draw times.',
                          '100/125MHz conversions assume clocks; neither a requested clock nor a cycle budget proves achieved timing.',
                          'This is a fixed corpus with reset/recovery tests, not a sustained 30fps hardware or 60/600-second system campaign.'])
    (AREA/'performance.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    with (AREA/'performance.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    print(json.dumps(groups,sort_keys=True))


if __name__ == '__main__':
    main()
