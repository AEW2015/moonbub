#!/usr/bin/env python3
"""Join authenticated logical path events from completed bounded system traces."""
import csv
import gzip
import hashlib
import json
import statistics
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'fpga/experiments/cu66-v81'
PASS = 'PASS_ACTUAL_DECODE_CANONICAL_AND_NATIVE_DISPLAY'
BASES = (0x080000, 0x480000, 0x880000)
OFFSETS = (0, 172800, 216000)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def describe(values):
    ordered = sorted(values)
    return dict(samples=len(values), min=ordered[0], median=statistics.median(ordered),
                max=ordered[-1], exact_histogram={str(k): v for k, v in sorted(Counter(values).items())})


def analyze(path):
    d = json.loads(path.read_text())
    assert d['status'] == PASS and 'wall_seconds' in d
    meta = d['trace']; trace = ROOT / meta['path']
    assert sha(trace) == meta['sha256']
    raw_hash = hashlib.sha256(); raw_bytes = 0
    with gzip.open(trace, 'rb') as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b''):
            raw_hash.update(part); raw_bytes += len(part)
    assert raw_hash.hexdigest() == meta['raw_sha256'] and raw_bytes == meta['raw_bytes']
    tiles = {}; blocks = {}; events = Counter()
    names = {'ref_first_valid': 'offer', 'ref_request': 'lookup', 'ref_response': 'response',
             'tile_write_request': 'write', 'backend_write_done': 'backend', 'tile_write_done': 'done',
             'prefetch_fill': 'fill'}
    block_names = {'prefetch_raw_request': 'request', 'prefetch_snapshot': 'snapshot',
                   'prefetch_block_commit': 'commit'}
    with gzip.open(trace, 'rt', newline='') as stream:
        for row in csv.DictReader(stream):
            event = row['event']; events[event] += 1
            if event not in names and event not in block_names:
                continue
            generation = int(row['owner_generation']); context = int(row['frame_generation'])
            bank, plane, index, cycle = (int(row[k]) for k in ('bank', 'plane', 'tile_index', 'cycle'))
            assert generation == context and 0 <= bank <= 2 and 0 <= plane <= 2
            assert 0 <= index < (5400 if plane == 0 else 1350)
            key = (generation, plane, index)
            if event in names:
                item = tiles.setdefault(key, {})
                name = names[event]; assert name not in item
                item[name] = cycle; item[name + '_bank'] = bank
            else:
                address = int(row['address'])
                relative = address - BASES[bank] - OFFSETS[plane] - index * 32
                assert relative in (0, 8, 16, 24)
                item = blocks.setdefault((*key, relative // 8), {})
                name = block_names[event]; assert name not in item
                item[name] = cycle; item[name + '_bank'] = bank
    assert dict(events) == meta['event_counts']
    frame_rows = []
    for timing, frame in zip(d['timings'], d['frames']):
        generation = frame['generation']; metrics = {}
        def record(name, value):
            metrics.setdefault(name, []).append(value)
        for plane, count in ((0, 5400), (1, 1350), (2, 1350)):
            for index in range(count):
                item = tiles[generation, plane, index]
                assert item['write'] < item['backend'] <= item['done'] < timing['validated_ready_cycle']
                assert item['write_bank'] == item['backend_bank'] == item['done_bank']
                record('write_accept_to_backend_done', item['backend'] - item['write'])
                record('backend_done_to_receiver_done', item['done'] - item['backend'])
                if 'lookup' in item:
                    assert item['offer'] <= item['lookup'] < item['response'] <= item['write']
                    assert item['offer_bank'] == item['lookup_bank'] == item['response_bank']
                    record('first_offer_to_lookup_accept', item['lookup'] - item['offer'])
                    record('lookup_accept_to_response', item['response'] - item['lookup'])
                if d['prefetch'] == 3 and not frame['key']:
                    commits = []
                    for block in range(4):
                        b = blocks[generation, plane, index, block]
                        assert b['request'] < b['snapshot'] < b['commit']
                        assert b['request_bank'] == b['snapshot_bank'] == b['commit_bank'] == item['fill_bank']
                        record('logical_request_to_bridge_snapshot', b['snapshot'] - b['request'])
                        record('bridge_snapshot_to_core_commit', b['commit'] - b['snapshot'])
                        if block:
                            previous = blocks[generation, plane, index, block - 1]
                            assert previous['commit'] < b['request']
                            record('previous_block_commit_to_next_request', b['request'] - previous['commit'])
                        commits.append(b['commit'])
                    assert commits[-1] == item['fill']
                    if 'lookup' in item:
                        assert item['fill'] < item['lookup']
                        record('fill_to_first_offer', item['offer'] - item['fill'])
        frame_rows.append(dict(generation=generation, fid=frame['fid'], key=frame['key'],
                               metrics_cycles={k: describe(v) for k, v in metrics.items()}))
    return dict(path=str(path.relative_to(ROOT)), results_sha256=sha(path), mode=d['prefetch'],
                cohort=d['cohort'], trace_sha256=sha(trace), trace_raw_sha256=meta['raw_sha256'],
                event_counts=dict(events), frames=frame_rows)


def main():
    selected = []
    for cohort in (0, 3):
        for mode in (2, 3):
            folder = AREA / 'system' / f'cohort{cohort}-frames4-fixed30-prefetch{mode}-tac2'
            eligible = []
            for path in sorted(folder.glob('attempt*/results.json')):
                d = json.loads(path.read_text())
                if d.get('status') == PASS and d.get('trace') and 'wall_seconds' in d:
                    eligible.append(path)
            assert eligible, f'completed four-source trace missing: {folder}'
            selected.append(eligible[-1])
    out = AREA / 'path-analysis'; out.mkdir(exist_ok=True)
    report = dict(schema='cu81-authenticated-path-analysis-v1', status='PASS',
                  script_sha256=sha(Path(__file__)), runs=[analyze(p) for p in selected],
                  memory_period_ps=10000,
                  semantics=['Logical raw requests, bridge snapshots and core commits have authenticated tags.',
                             'Physical controller command owner_generation remains unknown; no ownership is inferred from its context.',
                             'First-offer, accepted lookup, backend completion and receiver completion are distinct events.',
                             'Intervals overlap work and arbitration; they are not additive critical-path components.',
                             'Raw/snapshot/block coverage exists only for mode3; mode2 zero events mean uninstrumented, not zero work.',
                             'Only completed bounded traces are selected; these are not sustained-source or hardware qualification.'])
    (out / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
    print('V81_PATH_ANALYSIS_PASS', len(selected), 'completed traces')


if __name__ == '__main__':
    main()
