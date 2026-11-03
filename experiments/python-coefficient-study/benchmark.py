#!/usr/bin/env python3
"""Compare FT02 coefficient syntax with FT01 and same-input receiver JPEG."""
import hashlib
import json
from pathlib import Path
import platform
import sys
import time

import numpy as np

import coeff_codec as c

HERE = Path(__file__).resolve().parent
CODEC = HERE.parent/'python-codec-study'
sys.path.insert(0, str(CODEC))
import corpus
import pacing

BASELINE = HERE.parent/'python-transform-study/results.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summary(values):
    return {key: float(value) for key, value in zip(('mean', 'p50', 'p95', 'max'),
            (np.mean(values), np.percentile(values, 50), np.percentile(values, 95), max(values)))}


def psnr(mse):
    return None if mse == 0 else float(10*np.log10(65025/mse))


def main():
    sources = [HERE/'coeff_codec.py', HERE/'benchmark.py', HERE/'test_coeff_codec.py',
               Path(c.frozen.__file__), CODEC/'corpus.py', CODEC/'pacing.py']
    hashes = {str(p.relative_to(HERE.parent)): digest(p) for p in sources}
    baseline_digest = digest(BASELINE)
    baseline = json.loads(BASELINE.read_text())
    scenes = []
    for scene in baseline['scenes']:
        source = scene['selected_source']
        frames, manifest = corpus.load_video(source['source'], max_frames=12,
                                              start_seconds=source['start_seconds'])
        if manifest['frame_sha256'] != source['frame_sha256'] or len(frames) != 12:
            raise AssertionError('source mismatch')
        rows = []
        for scale in (8, 16, 32):
            before = next(r for r in scene['transform_profiles'] if r['profile'] == f'FT01-scale{scale}')
            records = []
            for i, rgb in enumerate(frames):
                start = time.perf_counter_ns()
                packet = c.encode(rgb, scale)
                encoded = time.perf_counter_ns()
                out = c.decode(packet)
                finished = time.perf_counter_ns()
                if not np.array_equal(out, c.frozen.reconstruct(rgb, scale)):
                    raise AssertionError('FT02 frozen RGB mismatch')
                display = corpus.expand565(corpus.rgb565(out))
                output_hash = hashlib.sha256(display.tobytes()).hexdigest()
                if output_hash != before['records'][i]['output_rgb565_sha256']:
                    raise AssertionError('FT02 and FT01 display pixels differ')
                quality = corpus.metrics(rgb, display, tuple(manifest['active_rects'][i]))
                records.append({'index': i, 'input_sha256': manifest['frame_sha256'][i],
                                'output_rgb565_sha256': output_hash,
                                'pts': manifest['selected_pts'][i],
                                'time_seconds': manifest['selected_times_seconds'][i],
                                'bytes': len(packet), 'wire_bytes': pacing.wire_bytes(len(packet)),
                                'ft01_bytes': before['records'][i]['bytes'],
                                'quality_rgb565_output': quality,
                                'encoder_python_ms': (encoded-start)/1e6,
                                'decoder_python_ms': (finished-encoded)/1e6})
            wire_mean = float(np.mean([r['wire_bytes'] for r in records]))
            old_wire = before['modeled_wire_mbps_projected_30fps']
            row = {'profile': f'FT02-scale{scale}', 'frames': len(records),
                   'packet_bytes': summary([r['bytes'] for r in records]),
                   'modeled_wire_mbps_projected_30fps': wire_mean*8*30/1e6,
                   'wire_saving_fraction_vs_exact_FT01': 1-wire_mean*8*30/1e6/old_wire,
                   'active_rgb565_output_psnr_db': psnr(np.mean([r['quality_rgb565_output']['active']['mse'] for r in records])),
                   'over_48k_count': sum(r['bytes'] > 49152 for r in records),
                   'over_256k_count': sum(r['bytes'] > 262144 for r in records),
                   'encode_python_ms': summary([r['encoder_python_ms'] for r in records]),
                   'decode_python_ms': summary([r['decoder_python_ms'] for r in records]),
                   'records': records}
            rows.append(row)
            print(scene['name'], row['profile'], row['modeled_wire_mbps_projected_30fps'],
                  row['active_rgb565_output_psnr_db'], row['wire_saving_fraction_vs_exact_FT01'], flush=True)
        scenes.append({'name': scene['name'], 'role': scene['role'], 'source': manifest,
                       'profiles': rows, 'matched_subset_jpeg': scene['matched_subset_jpeg']})
    if hashes != {str(p.relative_to(HERE.parent)): digest(p) for p in sources} or digest(BASELINE) != baseline_digest:
        raise RuntimeError('executed sources/baseline changed')
    result = {'evidence': 'Python bounded coefficient model; no hardware speed or resource proof',
              'source_sha256': hashes, 'baseline_sha256': baseline_digest,
              'python': platform.python_version(), 'numpy': np.__version__,
              'numeric_basis_sha256': hashlib.sha256(b''.join(a.astype('<i8').tobytes() for a in
                                           (c.frozen.Q14, c.frozen.QY, c.frozen.QC, c.frozen.ZIGZAG))).hexdigest(),
              'frames_input': 48, 'frame_roundtrips': 144,
              'wire_model': {'payload': 1024, 'app_header': 40, 'ipv4_udp': 28,
                             'excludes': 'RF/link headers, feedback/retries, audio/input'},
              'scenes': scenes}
    (HERE/'results.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')


if __name__ == '__main__':
    main()
