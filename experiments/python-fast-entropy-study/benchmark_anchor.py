#!/usr/bin/env python3
"""Paired actual MA01 preparation timings; lazy P oracle is outside service."""
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import time

import numpy as np
from fast_anchor import Encoder, frozen
import fast_coeff

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'python-codec-study'))
import corpus


def stats(values):
    return {name: float(value) for name, value in zip(("mean", "p50", "p95", "max"),
            (np.mean(values), *np.percentile(values, [50, 95]), max(values)))}


def main():
    media = Path(os.environ.get('GAMEBUB_MEDIA_DIR', str(HERE.parents[3] / 'media')))
    sources = [HERE / 'benchmark_anchor.py', HERE / 'fast_anchor.py', HERE / 'fast_coeff.py',
               HERE / 'benchmark.py', Path(frozen.__file__), Path(frozen.mt.__file__),
               Path(frozen.mt.ft.__file__), Path(fast_coeff.frozen.__file__), Path(corpus.__file__)]
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    scenes = []
    for clip in ('mass-effect-combat', 'mass-effect-2600'):
        frames, manifest = corpus.load_video(media / f'{clip}.mp4', max_frames=12, start_seconds=4)
        records = []
        for repeat in range(3):
            old, new, rx = frozen.AnchorEncoder(), Encoder(), frozen.AnchorReceiver()
            for i, rgb in enumerate(frames):
                packets, timings = {}, {}
                order = (('old', old), ('fast', new)) if (i + repeat) % 2 == 0 else (('fast', new), ('old', old))
                for label, enc in order:
                    began = time.perf_counter_ns()
                    packets[label] = enc.prepare(rgb, i, quant_scale=8, mode='zero')
                    timings[label] = (time.perf_counter_ns() - began) / 1e6
                assert packets['old'] == packets['fast'], 'MA01 packet changed'
                actual, info = rx.receive(packets['fast'])
                expected = hashlib.sha256(actual.tobytes()).hexdigest()
                assert expected == old.expected_hash(i) == new.expected_hash(i), 'RGB oracle changed'
                old.ack(i, epoch=1)
                new.ack(i, epoch=1)
                records.append({'repeat': repeat, 'frame': i, 'kind': 'KEY' if i == 0 else 'P',
                                'input_sha256': manifest['frame_sha256'][i],
                                'packet_sha256': hashlib.sha256(packets['fast']).hexdigest(),
                                'bytes': len(packets['fast']), 'old_prepare_ms': timings['old'],
                                'fast_prepare_ms': timings['fast']})
        totals = {}
        for label in ('old', 'fast'):
            totals[label + '_all_ms'] = stats([r[label + '_prepare_ms'] for r in records])
            totals[label + '_p_ms'] = stats([r[label + '_prepare_ms'] for r in records if r['kind'] == 'P'])
            totals[label + '_key_ms'] = stats([r[label + '_prepare_ms'] for r in records if r['kind'] == 'KEY'])
        scenes.append({'name': clip, 'manifest': manifest, 'paired_checks': len(records),
                       **totals, 'records': records})
    assert hashes == {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}, 'source changed'
    result = {'evidence': 'Actual paired Python wall time under uncontrolled host load; not target/native or hardware FPS',
              'profile': 'MA01 quant8 zero motion: keys unchanged; P skips unnecessary host IDCT/RGB and uses fast CP02',
              'python': platform.python_version(), 'numpy': np.__version__, 'source_sha256': hashes,
              'scope': 'prepare includes anchor-key reconstruction; lazy P reconstruction oracle, source capture/scale, network, QSPI, vblank excluded. All packets and oracle RGB exactly match frozen MA01.',
              'measurement': '12 frames per clip, 3 independent repetitions, alternating old/new order, no CPU affinity or isolated warmup',
              'scenes': scenes}
    (HERE / 'anchor-results.json').write_text(json.dumps(result, indent=2) + '\n')
    for scene in scenes:
        print(scene['name'], {k:v for k,v in scene.items() if k.endswith('_ms')})


if __name__ == '__main__':
    main()
