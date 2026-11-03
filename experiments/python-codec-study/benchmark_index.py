#!/usr/bin/env python3
"""Measure quantization-index coding against the exact existing corpus/outputs."""
import hashlib
import json
from pathlib import Path
import time

import numpy as np

import benchmark
import codec
import corpus
import index_codec
import zero_run_codec
import pacing

HERE = Path(__file__).resolve().parent


def main():
    baseline_path = HERE/'results.json'
    baseline = json.loads(baseline_path.read_text())
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
              for p in (HERE/'benchmark_index.py', HERE/'index_codec.py', HERE/'zero_run_codec.py', HERE/'codec.py', HERE/'corpus.py')}
    rows = []
    for name, manifest in baseline['corpora'].items():
        if name == 'synthetic-hud':
            frames, new_manifest = benchmark.hud_sequence(len(manifest['frame_sha256']))
        else:
            frames, new_manifest = corpus.load_video(manifest['source'],
                                                     max_frames=len(manifest['frame_sha256']))
        if new_manifest['frame_sha256'] != manifest['frame_sha256']:
            raise AssertionError('corpus has changed')
        for profile, module, q in (('dpcm-index-q2', index_codec, 2), ('dpcm-index-q4', index_codec, 4),
                                   ('dpcm-zero-run-q2', zero_run_codec, 2), ('dpcm-zero-run-q4', zero_run_codec, 4)):
            series = []
            original = next(row for row in baseline['rows'] if row['corpus'] == name and row['profile'] == f'dpcm-q{q}')
            for i, rgb in enumerate(frames):
                words = corpus.rgb565(rgb)
                start = time.perf_counter_ns()
                packet = module.encode(words, quant_step=q)
                encoded = time.perf_counter_ns()
                decoded = module.decode(packet)
                finished = time.perf_counter_ns()
                if not np.array_equal(decoded, codec.quantize(words, q)):
                    raise AssertionError('quantized reconstruction mismatch')
                digest = hashlib.sha256(decoded.astype('<u2').tobytes()).hexdigest()
                if digest != original['per_frame'][i]['reconstruction_sha256']:
                    raise AssertionError('outputs must be identical to the compared candidate')
                quality = corpus.metrics(rgb, corpus.expand565(decoded), tuple(manifest['active_rects'][i]))
                series.append({'index': i, 'bytes': len(packet), 'wire_bytes': pacing.wire_bytes(len(packet)),
                               'encode_ms_python': (encoded-start)/1e6,
                               'decode_ms_python': (finished-encoded)/1e6,
                               'reconstruction_sha256': digest, 'quality': quality})
            mean_wire = np.mean([x['wire_bytes'] for x in series])
            row = {'corpus': name, 'profile': profile, 'frames': len(series),
                   'projected_wire_mbps_at_30fps': mean_wire*8*30/1e6,
                   'wire_saving_fraction_vs_identical_output_dpcm': 1-mean_wire/original['wire_bytes']['mean'],
                   'active_rgb565_output_psnr_db': benchmark.psnr(np.mean([x['quality']['active']['mse'] for x in series])),
                   'size_bytes': benchmark.distribution([x['bytes'] for x in series]),
                   'over_48k': sum(x['bytes'] > 49152 for x in series),
                   'encode_ms_python': benchmark.distribution([x['encode_ms_python'] for x in series]),
                   'decode_ms_python': benchmark.distribution([x['decode_ms_python'] for x in series]),
                   'per_frame': series}
            rows.append(row)
            print(json.dumps({k: v for k, v in row.items() if k not in ('per_frame',)}), flush=True)
    result = {'evidence': 'offline Python quantization-index prototype; no hardware',
              'baseline_sha256': hashlib.sha256(baseline_path.read_bytes()).hexdigest(),
              'source_hashes': hashes, 'rows': rows}
    (HERE/'results-index.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')


if __name__ == '__main__':
    main()
