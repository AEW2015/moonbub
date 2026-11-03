#!/usr/bin/env python3
"""Read-only descriptive analysis of recorded presentations, not a new RTL verdict."""
import argparse
import json
from pathlib import Path

CYCLES_PER_SECOND = 100_000_000
WINDOW = 60 * CYCLES_PER_SECOND


def analyze(rows):
    if len(rows) < 2:
        raise ValueError('at least two frames required')
    for i, row in enumerate(rows):
        if row['frame_id'] != i + 1 or any(type(row[k]) is not int for k in ('arrival_cycle', 'present_cycle')):
            raise ValueError('invalid sequential frame IDs or cycle values')
        if row['arrival_cycle'] != rows[0]['arrival_cycle'] + i * 10_000_000 // 3:
            raise ValueError('capture cadence is not the expected rational 30 Hz')
        if row['present_cycle'] < row['arrival_cycle']:
            raise ValueError('presentation precedes capture')
    times = [r['present_cycle'] for r in rows]
    gaps = [b-a for a,b in zip(times,times[1:])]
    if min(gaps) <= 0:
        raise ValueError('presentations must be strictly increasing')
    # For window (start,start+60s], all integer-cycle timestamps fit exactly when
    # last-60s <= start <= first-1. This describes a moved observation window,
    # not a new run with altered timing or a substitute for the capture deadline.
    start_low, start_high = times[-1]-WINDOW, times[0]-1
    origin = rows[0]['arrival_cycle']
    ordered = sorted(gaps)
    def percentile(p):
        return ordered[(len(ordered)-1)*p//100]
    return {
        'scope': 'Offline descriptive analysis of archived timestamps; shifting the observation window does not change the original capture-window verdict or predict modified hardware.',
        'cycles_per_second': CYCLES_PER_SECOND, 'frames':len(rows),
        'capture_epoch_cycle':origin, 'first_presentation_cycle':times[0], 'last_presentation_cycle':times[-1],
        'capture_window_presentations':sum(origin < t <= origin+WINDOW for t in times),
        'capture_window_last_lateness_cycles':times[-1]-(origin+WINDOW),
        'presentation_span_cycles':times[-1]-times[0],
        'presentation_span_fps':(len(times)-1)*CYCLES_PER_SECOND/(times[-1]-times[0]),
        'inter_presentation_cycles':{'min':min(gaps),'p50':percentile(50),'p95':percentile(95),'p99':percentile(99),'max':max(gaps)},
        'all_recorded_presentations_fit_some_60s_window':start_low <= start_high,
        'observation_window_start_offset_cycles_inclusive': [start_low-origin,start_high-origin] if start_low <= start_high else None,
        'percentile_method':'sorted nearest-rank lower index floor((n-1)*p/100)',
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('verified_jsonl', type=Path)
    args=parser.parse_args()
    rows=[json.loads(line) for line in args.verified_jsonl.read_text().splitlines() if line.strip()]
    print(json.dumps(analyze(rows), indent=2, sort_keys=True))

if __name__ == '__main__':
    main()
