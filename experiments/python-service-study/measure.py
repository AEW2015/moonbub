#!/usr/bin/env python3
"""Measure reference-Python wall service; never substitute this for FPGA timing."""
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import time

import numpy as np

HERE = Path(__file__).resolve().parent
for p in (HERE.parent/'python-motion-study', HERE.parent/'python-codec-study'):
    sys.path.insert(0, str(p))
import motion_codec as mc
import corpus


def stats(values):
    return {k: float(v) for k, v in zip(('mean', 'p50', 'p95', 'max'),
            (np.mean(values), *np.percentile(values, [50, 95]), max(values)))}


def main():
    root = HERE.parents[3]
    media = Path(os.environ.get('GAMEBUB_MEDIA_DIR', str(root/'media')))
    paths = [HERE/'measure.py', Path(mc.__file__), Path(mc.cc.__file__), Path(mc.ft.__file__), Path(corpus.__file__)]
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    scenes = []
    for name in ('mass-effect-combat', 'mass-effect-2600'):
        frames, manifest = corpus.load_video(media/f'{name}.mp4', max_frames=15, start_seconds=4)
        enc, dec = mc.Encoder(), mc.Receiver()
        # Warm separately, preserving the declared measured session as independent.
        warm_e, warm_d = mc.Encoder(2), mc.Receiver(2)
        warm_d.receive(warm_e.prepare(frames[0], 0, quant_scale=8, mode='zero'))
        records = []
        begin_all = time.perf_counter_ns()
        for i, rgb in enumerate(frames):
            start = time.perf_counter_ns()
            packet = enc.prepare(rgb, i, quant_scale=8, mode='zero')
            encoded = time.perf_counter_ns()
            decoded, info = dec.receive(packet)
            received = time.perf_counter_ns()
            if not np.array_equal(decoded, enc.prepared_rgb()):
                raise AssertionError('reference reconstruction mismatch')
            enc.ack(info['frame_id'], epoch=info['epoch'])
            records.append({'id': i, 'packet_bytes': len(packet),
                            'encode_python_wall_ms': (encoded-start)/1e6,
                            'decode_python_wall_ms': (received-encoded)/1e6,
                            'combined_measured_calls_ms': (received-start)/1e6,
                            'input_sha256': manifest['frame_sha256'][i]})
        total_ms = (time.perf_counter_ns()-begin_all)/1e6
        scenes.append({'name': name, 'manifest': manifest, 'records': records,
                       'encode_ms': stats([x['encode_python_wall_ms'] for x in records]),
                       'decode_ms': stats([x['decode_python_wall_ms'] for x in records]),
                       'combined_call_ms': stats([x['combined_measured_calls_ms'] for x in records]),
                       'offline_loop_frames_per_second': len(frames)*1000/total_ms,
                       'calls_over_33_333ms': sum(x['combined_measured_calls_ms'] > 1000/30 for x in records)})
    if hashes != {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}:
        raise RuntimeError('measurement sources changed')
    result = {'evidence': 'Reference-Python wall service on this host; concurrent load is uncontrolled; no FPGA/native timing claim',
              'python': platform.python_version(), 'numpy': np.__version__,
              'host_machine': platform.machine(), 'source_sha256': hashes,
              'profile': 'MT02 scale8 zero motion, one key thenACKedPframes',
              'excludes': 'source decode/scale, network, QSPI, vblank, optical response',
              'scenes': scenes}
    (HERE/'results.json').write_text(json.dumps(result, indent=2)+'\n')
    for row in scenes:
        print(row['name'], 'encode p50', row['encode_ms']['p50'], 'decode p50', row['decode_ms']['p50'],
              'offline fps', row['offline_loop_frames_per_second'])


if __name__ == '__main__':
    main()
