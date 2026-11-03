#!/usr/bin/env python3
"""Analyze the complete-line snapshot of a streaming verifier's JSONL."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re

HZ = 100_000_000

def analyze(data, manifest):
    # A concurrent writer may have left a trailing partial line. Never use it.
    end = data.rfind(b'\n') + 1
    prefix = data[:end]
    rows = [json.loads(line) for line in prefix.splitlines()]
    if not rows:
        raise ValueError('no complete verified records')
    frames = manifest['frames']
    for i, row in enumerate(rows):
        if row['id'] != i + 1 or row['frame_id'] != row['id']:
            raise ValueError('missing, duplicate or reordered frame ID')
        if i >= len(frames) or frames[i]['id'] != i or frames[i]['jpeg_sha256'] != row['jpeg_sha256']:
            raise ValueError('fixture manifest mismatch')
        if not re.fullmatch(r'[0-9a-f]{64}', row['rtl_dump_sha256']):
            raise ValueError('invalid verified dump hash')
        a, c, p = (row[k] for k in ('arrival_cycle', 'commit_cycle', 'present_cycle'))
        if not (a <= c <= p) or row['arrival_to_present_cycles'] != p-a:
            raise ValueError('inconsistent timestamps')
        if i and (a <= rows[i-1]['arrival_cycle'] or p <= rows[i-1]['present_cycle']):
            raise ValueError('non-increasing timestamps')
        if row['writes'] != 345600 or row['bursts'] != 43200 or row['cmodel_exact_pixels'] != 345600 or row['underruns'] != 0:
            raise ValueError('verification metadata mismatch')
    ages = sorted(r['present_cycle']-r['arrival_cycle'] for r in rows)
    intervals = [b['present_cycle']-a['present_cycle'] for a,b in zip(rows,rows[1:])]
    def ms(cycles): return cycles * 1000 / HZ
    def stats(values):
        if not values: return None
        s = sorted(values)
        return {'count': len(s), 'min_ms': ms(s[0]),
                **{f'p{q}_ms': ms(s[math.ceil(q*len(s)/100)-1]) for q in (50, 95, 99)},
                'max_ms': ms(s[-1])}
    misses = sum(age*30 > HZ for age in ages)
    span = rows[-1]['present_cycle'] - rows[0]['present_cycle']
    return {'scope': 'simulated verified prefix; not hardware, end-to-end latency, or proof of completed run',
            'snapshot_sha256': hashlib.sha256(prefix).hexdigest(), 'snapshot_bytes': len(prefix),
            'trailing_partial_bytes_ignored': len(data)-end,
            'manifest_frames': len(frames), 'verified_frames': len(rows),
            'first_id': rows[0]['id'], 'last_id': rows[-1]['id'],
            'clock_hz': HZ, 'percentile_method': 'nearest rank ceil(p*N), 1-indexed',
            'arrival_to_presentation': stats(ages), 'presentation_intervals': stats(intervals),
            'presentation_fps_first_to_last': (len(rows)-1)*HZ/span if span else None,
            'arrival_to_presentation_deadline': {'numerator_seconds': 1, 'denominator_seconds': 30,
                'comparison': 'miss if age > 1/30 second; equality meets deadline',
                'misses': misses, 'meets': len(rows)-misses}}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('verified', type=Path)
    p.add_argument('manifest', type=Path)
    args = p.parse_args()
    try:
        data = args.verified.read_bytes()
        manifest_bytes = args.manifest.read_bytes()
        result = analyze(data, json.loads(manifest_bytes))
        result['manifest_sha256'] = hashlib.sha256(manifest_bytes).hexdigest()
        print(json.dumps(result, indent=2, sort_keys=True))
    except (ValueError, KeyError, TypeError, OSError) as e:
        p.exit(1, f'analysis failed: {e}\n')
if __name__ == '__main__': main()
