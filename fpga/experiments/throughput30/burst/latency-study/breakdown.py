#!/usr/bin/env python3
"""Break down verified prefix ages; commit-to-present includes several stages."""
import json
import statistics
import sys
from pathlib import Path
from analyze import analyze

def describe(values):
    values = sorted(values)
    return {'min_ms': values[0]/100000, 'median_ms': statistics.median(values)/100000,
            'max_ms': values[-1]/100000}

def main():
    if len(sys.argv) != 3:
        raise SystemExit('usage: breakdown.py VERIFIED.jsonl MANIFEST.json')
    raw = Path(sys.argv[1]).read_bytes()
    meta = analyze(raw, json.loads(Path(sys.argv[2]).read_bytes()))
    rows = [json.loads(line) for line in raw[:meta['snapshot_bytes']].splitlines()]
    for row in rows:
        if row['queue_wait_cycles'] < 0 or row['upload_cycles'] < 0 or row['queue_wait_cycles'] + row['upload_cycles'] != row['commit_cycle'] - row['arrival_cycle']:
            raise ValueError('queue + upload does not equal arrival-to-commit')
    missed = [r for r in rows if r['arrival_to_present_cycles']*30 > 100_000_000]
    def group(records):
        if not records: return None
        return {'count': len(records), 'queue_wait_over_one_cycle': sum(r['queue_wait_cycles'] > 1 for r in records),
                'queue_wait': describe([r['queue_wait_cycles'] for r in records]),
                'upload_through_commit': describe([r['upload_cycles'] for r in records]),
                'commit_to_present_includes_processing_and_boundary_wait': describe([r['present_cycle']-r['commit_cycle'] for r in records]),
                'arrival_to_present': describe([r['arrival_to_present_cycles'] for r in records])}
    print(json.dumps({'snapshot_sha256': meta['snapshot_sha256'], 'all': group(rows),
                      'deadline_misses': group(missed),
                      'presentation_intervals_ms': describe([b['present_cycle']-a['present_cycle'] for a,b in zip(rows,rows[1:])]) if len(rows)>1 else None,
                      'note': 'commit-to-present is not pure vblank wait; no pending timestamp is present'}, indent=2))
if __name__ == '__main__': main()
