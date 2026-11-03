#!/usr/bin/env python3
"""Actual paired MA01 key/P preparation costs, with byte/pixel equality checks."""
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import time

import numpy as np

from key_encoder import Encoder, fast_anchor, fast_coeff, frozen

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'python-codec-study'))
import corpus


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stats(values):
    return {k: float(v) for k, v in zip(('mean', 'p50', 'p95', 'max'),
            (np.mean(values), *np.percentile(values, [50, 95]), max(values)))}


def compare(encoders, rgb, frame, phase):
    packets, elapsed, oracles = {}, {}, {}
    labels = ('frozen', 'v5_p_fast', 'key_fast')
    order = labels[phase % 3:] + labels[:phase % 3]
    for label in order:
        start = time.perf_counter_ns()
        packets[label] = encoders[label].prepare(rgb, frame, quant_scale=8, mode='zero')
        elapsed[label] = (time.perf_counter_ns() - start) / 1e6
    assert packets['frozen'] == packets['v5_p_fast'] == packets['key_fast'], 'wire changed'
    for label in labels:
        start = time.perf_counter_ns()
        oracles[label] = encoders[label].expected_hash(frame)
        elapsed[label + '_oracle'] = (time.perf_counter_ns() - start) / 1e6
    receiver = frozen.AnchorReceiver()
    enc = encoders['key_fast']
    if not enc.pending[frame]['key']:
        receiver.anchor_id, receiver._anchor = enc.anchor_id, enc._anchor
    actual, _ = receiver.receive(packets['key_fast'])
    expected = hashlib.sha256(actual.tobytes()).hexdigest()
    assert all(v == expected for v in oracles.values()), 'pixel hash changed'
    return {'kind': 'KEY' if enc.pending[frame]['key'] else 'P', 'frame': frame,
            'bytes': len(packets['key_fast']), 'packet_sha256': hashlib.sha256(packets['key_fast']).hexdigest(),
            'reconstructed_rgb_sha256': expected, 'prepare_ms': {k: elapsed[k] for k in labels},
            'oracle_ms': {k: elapsed[k + '_oracle'] for k in labels},
            'new_key_stages_ms': dict(enc.last_prepare_stages_ms),
            'new_p_oracle_packet_bytes': enc.oracle_packet_bytes(),
            'new_reference_array_bytes': enc.retained_reference_bytes()}


def encoders():
    return {'frozen': frozen.AnchorEncoder(), 'v5_p_fast': fast_anchor.Encoder(), 'key_fast': Encoder()}


def summaries(records):
    result = {}
    for kind in ('all', 'KEY', 'P'):
        rows = [r for r in records if kind == 'all' or r['kind'] == kind]
        if not rows:
            continue
        result[kind] = {label: stats([r['prepare_ms'][label] for r in rows])
                        for label in ('frozen', 'v5_p_fast', 'key_fast')}
        result[kind]['key_fast_over_33_333_ms'] = sum(r['prepare_ms']['key_fast'] > 1000 / 30 for r in rows)
        result[kind]['count'] = len(rows)
    return result


def main():
    media = Path(os.environ.get('GAMEBUB_MEDIA_DIR', str(HERE.parents[3] / 'media')))
    sources = [HERE / 'benchmark.py', HERE / 'key_encoder.py', HERE / 'test_key_encoder.py',
               Path(fast_anchor.__file__), Path(fast_coeff.__file__), Path(frozen.__file__),
               Path(frozen.mt.__file__), Path(frozen.mt.ft.__file__), Path(frozen.mt.cc.__file__), Path(corpus.__file__)]
    hashes = {str(p): digest(p) for p in sources}
    scenes, key_cases = [], []
    for clip in ('mass-effect-combat', 'mass-effect-2600'):
        frames, manifest = corpus.load_video(media / f'{clip}.mp4', max_frames=12, start_seconds=4)
        records = []
        for repeat in range(3):
            group = encoders()
            for i, rgb in enumerate(frames):
                row = compare(group, rgb, i, repeat + i)
                row.update(repeat=repeat, input_sha256=manifest['frame_sha256'][i])
                records.append(row)
                for enc in group.values():
                    enc.ack(i, epoch=1)
        scenes.append({'name': clip, 'manifest': manifest, 'paired_triples': len(records),
                       'summary_ms': summaries(records), 'records': records})
        for start in (1, 4):
            frames, manifest = corpus.load_video(media / f'{clip}.mp4', max_frames=12, start_seconds=start)
            rows = []
            for index, i in enumerate(range(0, 12, 2)):
                group = encoders()
                row = compare(group, frames[i], 0, index + start)
                row.update(source_index=i, input_sha256=manifest['frame_sha256'][i])
                rows.append(row)
            key_cases.append({'name': f'{clip}-start{start}', 'manifest': manifest,
                              'paired_triples': len(rows), 'summary_ms': summaries(rows), 'records': rows})
    assert hashes == {str(p): digest(p) for p in sources}, 'sources changed during run'
    keys = [r for c in key_cases for r in c['records']]
    stage_names = [k for k in keys[0]['new_key_stages_ms'] if k != 'kind']
    result = {'evidence': 'Actual Python host wall time; exact packet and receiver RGB hash comparison, no hardware/native real-time claim',
              'profile': 'MA01 quant8 zero-motion; frozen keys versus v5 lazy-P keys versus fast-key/lazy-oracle',
              'python': platform.python_version(), 'numpy': np.__version__, 'source_sha256': hashes,
              'measurement': 'Sequential grouped variants with cyclic timing order, uncontrolled concurrent load, no affinity or isolated warmup. Optional oracle, source decode/scale, receiver validation, network, QSPI and vblank excluded from prepare.',
              'ownership': 'One persistent key YUV420 array set per endpoint; newly-owned reconstruction frozen without extra copy. P oracle retains packet until ACK/expiry. Transforms, prediction, RGB oracle and receiver verification are additional transient host arrays.',
              'scenes': scenes, 'independent_key_cases': key_cases,
              'all_independent_keys': summaries(keys),
              'independent_key_stage_ms': {k: stats([r['new_key_stages_ms'][k] for r in keys]) for k in stage_names}}
    (HERE / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
    for scene in scenes:
        print(scene['name'], json.dumps(scene['summary_ms']))
    print('independent_key24', json.dumps(result['all_independent_keys']))
    print('key_stages', json.dumps(result['independent_key_stage_ms']))


if __name__ == '__main__':
    main()
