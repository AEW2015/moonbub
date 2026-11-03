#!/usr/bin/env python3
"""Repeat recorded size traces through finite scenario timing, not new captures."""
import dataclasses
import hashlib
import json
from pathlib import Path

from model import Config, simulate

HERE = Path(__file__).resolve().parent
INPUT = HERE.parent/'python-codec-study/results.json'


def main():
    source = json.loads(INPUT.read_text())
    rows, traces = [], {}
    for corpus in ('mass-effect-combat', 'mass-effect-2600'):
        old = next(r for r in source['rows'] if r['corpus'] == corpus and r['profile'] == 'jpeg-budget8')
        trace = [x['bytes'] for x in old['per_frame']]
        sizes = [trace[i % len(trace)] for i in range(1800)]
        traces[corpus] = {'trace_frames': len(trace), 'simulated_inputs': 1800,
                          'repetition': 'cyclic size replay; no new frames or pixel decoding',
                          'trace_sha256': hashlib.sha256(json.dumps(trace).encode()).hexdigest(),
                          'source_manifest': source['corpora'][corpus]}
        for link in (8, 12):
            for decode in (8, 20, 40):
                for qspi in (160, 40):
                    cfg = Config(link_mbps=link, decode_ms=decode, qspi_mbps=qspi)
                    row = simulate(sizes, cfg)
                    row.update(corpus=corpus, scenario='service_sweep')
                    rows.append(row)
        for name, changes in (
                ('scan65', {'refresh_hz': 65.076}),
                ('jitter8', {'ready_jitter_ms': 8}),
                ('jitter40', {'ready_jitter_ms': 40}),
                ('periodic_stall', {'link_stalls': tuple((10000+i*10000, 10100+i*10000) for i in range(5))}),
                ('loss', {'loss_ids': tuple(range(100, 1800, 100))}),
                ('one_compressed_slot', {'compressed_slots': 1}),
                ('two_framebuffers', {'framebuffers': 2}),
                ('large_slots', {'frame_cap': 262144}),
                ('low_link', {'link_mbps': 4})):
            row = simulate(sizes, dataclasses.replace(Config(), **changes))
            row.update(corpus=corpus, scenario=name)
            rows.append(row)
        # Same independent sizes but explicit reference chain, to expose recovery.
        refs = [None if i % 30 == 0 else i-1 for i in range(1800)]
        row = simulate(sizes, Config(loss_ids=tuple(range(100, 1800, 100))), refs)
        row.update(corpus=corpus, scenario='temporal_dependency_loss_synthetic')
        rows.append(row)
    summaries = []
    for row in rows:
        detail = {k: row.pop(k) for k in ('presented', 'decoded_events', 'drops', 'allocation_events')}
        # Full event detail for one baseline and one overload; keep presented
        # IDs and dropped IDs for every case without duplicating all ledgers.
        cfg = row['config']
        retain = (row['corpus'] == 'mass-effect-combat' and
                  row['scenario'] == 'service_sweep' and cfg['link_mbps'] == 8 and
                  cfg['qspi_mbps'] == 160 and cfg['decode_ms'] in (8, 40))
        row['presented_ids'] = [x['id'] for x in detail['presented']]
        row['drop_ids_by_reason'] = {reason: [x['id'] for x in detail['drops'] if x['reason'] == reason]
                                    for reason in row['drops_by_reason']}
        if retain:
            row['detail'] = detail
        summaries.append(row)
        print(row['corpus'], row['scenario'], cfg['link_mbps'], cfg['qspi_mbps'], cfg['decode_ms'],
              'strict', row['presented_strict'], 'drain', row['presented_after_drain'],
              'steady_fps', row['steady_fps'], 'p95age', row['steady_age_ms']['p95'],
              'drops', row['drops_by_reason'], flush=True)
    result = {'scope': 'finite capacity/event simulation; all service constants assumed, no physical FPS proof',
              'input_sha256': hashlib.sha256(INPUT.read_bytes()).hexdigest(),
              'source_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in (HERE/'model.py', HERE/'test_model.py', HERE/'run.py')},
              'predeclared_windows': {'capture_ms': [0, 60000], 'steady_ms': [5000, 55000],
                                      'drain_ms': 2000, 'boundary': '[start,end)'},
              'traces': traces, 'scenario_count': len(rows), 'scenarios': summaries}
    (HERE/'results.json').write_text(json.dumps(result, indent=2)+'\n')


if __name__ == '__main__':
    main()
