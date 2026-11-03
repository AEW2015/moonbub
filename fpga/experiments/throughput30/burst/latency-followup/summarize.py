#!/usr/bin/env python3
"""Summarize measured frame-stage latencies from the two isolated RTL runs."""
import re, statistics, sys
from pathlib import Path

def rows(path):
    lines = Path(path).read_text().splitlines()
    if 'TEST_PASS_NETWORK_QSPI_TRACE' not in lines:
        raise ValueError(f'missing PASS: {path}')
    result = [{k: int(v) for k, v in re.findall(r'(\w+)=(\d+)', line)}
              for line in lines if line.startswith('FRAME_RESULT ')]
    if len(result) != 10 or [r['id'] for r in result] != list(range(10)):
        raise ValueError(f'expected 10 ordered frames: {path}')
    for r in result:
        if not (r['capture_cycle'] <= r['network_complete_cycle'] <= r['commit_cycle']
                <= r['decode_ready_cycle'] <= r['present_cycle']):
            raise ValueError('timestamps out of order')
    return result

for label, path in zip(('baseline', 'optimistic', 'guarded', 'faster-link'), sys.argv[1:], strict=True):
    rr = rows(path)
    stages = [('network','capture_cycle','network_complete_cycle'),
              ('queue_and_qspi','network_complete_cycle','commit_cycle'),
              ('decode_and_drain','commit_cycle','decode_ready_cycle'),
              ('boundary_wait','decode_ready_cycle','present_cycle'),
              ('total','capture_cycle','present_cycle')]
    print(label)
    for name, a, b in stages:
        values = [(r[b] - r[a])/100000 for r in rr]
        print(f'{name}: mean={statistics.mean(values):.5f} ms max={max(values):.5f} ms')
