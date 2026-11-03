#!/usr/bin/env python3
"""Replay offline access-unit sizes on an ideal, fixed-rate FIFO payload link."""
import json
from pathlib import Path


def replay(lengths, mbps):
    finish = 0.0
    elapsed = []
    for i, length in enumerate(lengths):
        arrival = i / 30.0
        finish = max(arrival, finish) + length * 8 / (mbps * 1e6)
        elapsed.append((finish - arrival) * 1000)
    ranked = sorted(elapsed)
    return sum(t > 1000 / 30 + 1e-8 for t in elapsed), ranked[int(.95 * (len(ranked)-1))], max(elapsed)


def main():
    assert replay([1000] * 90, 8)[0] == 0
    assert replay([50000] * 90, 8)[0] == 90
    records = json.loads((Path(__file__).parent / 'access-unit-sizes.json').read_text())
    for r in records:
        if r['target_mbps'] != 4:
            continue
        for rate in (8, 12):
            late, p95, maximum = replay(r['frame_bytes'], rate)
            print(f"{r['scene']:18} {r['codec']:5} {rate:2}Mb/s late={late:2}/90 p95={p95:.1f}ms max={maximum:.1f}ms")


if __name__ == '__main__':
    main()
