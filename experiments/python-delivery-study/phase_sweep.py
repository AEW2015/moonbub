#!/usr/bin/env python3
"""Predeclared capture-phase sweep of finite JPEG delivery scenario assumptions."""
import dataclasses
import hashlib
import json
from pathlib import Path

from model import Config, simulate

HERE = Path(__file__).resolve().parent
INPUT = HERE.parent/'python-codec-study/results.json'


def run():
    baseline = json.loads(INPUT.read_text())
    source_hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in (HERE/'model.py', HERE/'phase_sweep.py')}
    rows = []
    for source in baseline['rows']:
        if source['profile'] != 'jpeg-budget8' or source['corpus'] == 'synthetic-hud':
            continue
        trace = [x['bytes'] for x in source['per_frame']]
        sizes = [trace[i % len(trace)] for i in range(1800)]
        for refresh in (60, 65.076):
            for phase in (0, 4, 8, 12, 16, 20, 24, 28):
                for decode in (8, 20):
                    for jitter in (0, 4):
                        cfg = Config(refresh_hz=refresh, phase_ms=phase,
                                     decode_ms=decode, ready_jitter_ms=jitter)
                        result = simulate(sizes, cfg)
                        rows.append({'corpus': source['corpus'], 'config': dataclasses.asdict(cfg),
                                     'steady_fps': result['steady_fps'], 'strict_count': result['presented_strict'],
                                     'eventual_count': result['presented_after_drain'],
                                     'steady_age_ms': result['steady_age_ms'],
                                     'steady_gap_ms': result['steady_gap_ms'],
                                     'peak_occupancy': result['peak_occupancy'],
                                     'drops_by_reason': result['drops_by_reason']})
    result = {'evidence': 'finite ownership model; cyclic offline size traces, not native video or hardware',
              'input_sha256': hashlib.sha256(INPUT.read_bytes()).hexdigest(),
              'source_sha256': source_hashes, 'frames_per_scenario': 1800,
              'steady_window_ms': [5000, 55000], 'target_steady_count': 1500,
              'scenario_count': len(rows), 'scenarios': rows}
    (HERE/'phase-results.json').write_text(json.dumps(result, indent=2)+'\n')
    print('scenarios', len(rows), 'min/max steady fps', min(x['steady_fps'] for x in rows),
          max(x['steady_fps'] for x in rows), 'cases below target', sum(x['steady_fps'] < 30 for x in rows),
          'max p95 age', max(x['steady_age_ms']['p95'] for x in rows),
          'max strict count', max(x['strict_count'] for x in rows), flush=True)


if __name__ == '__main__':
    run()
