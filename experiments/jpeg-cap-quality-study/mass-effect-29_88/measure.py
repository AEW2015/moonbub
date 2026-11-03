#!/usr/bin/env python3
"""Offline JPEG size and encode-time study on a second native-rate clip."""
import argparse
import csv
import hashlib
import json
import statistics
import sys
import time
from pathlib import Path

import av
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
PROJECT = HERE.parents[4]
GAMEBUB = PROJECT / 'repos' / 'sunshine-30fps-study' / 'tools' / 'gamebub'
sys.path.insert(0, str(GAMEBUB))
sys.path.insert(0, str(STUDY))
from host import canvas  # noqa: E402
from measure import CAP_BYTES, choose_policy, percentile  # noqa: E402
from msv1 import encode_receiver_jpeg  # noqa: E402

QUALITIES = (75, 80, 85, 90)


def stats(values):
    return {'count': len(values), 'mean': float(statistics.mean(values)),
            'p95': percentile(values, .95), 'max': max(values), 'min': min(values)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--clip', type=Path, default=PROJECT / 'media' / 'mass-effect-2600.mp4')
    parser.add_argument('--output', type=Path, default=HERE)
    args = parser.parse_args()
    if not args.clip.is_file():
        parser.error(f'clip not found: {args.clip}')
    args.output.mkdir(parents=True, exist_ok=True)

    container = av.open(str(args.clip))
    stream = container.streams.video[0]
    native_rate = str(stream.average_rate)
    rows = []
    with (args.output / 'per-frame.csv').open('w', newline='') as out:
        fields = ['frame_id', 'pts_seconds']
        for q in QUALITIES:
            fields += [f'q{q}_bytes', f'q{q}_encode_ms', f'q{q}_over_cap']
        fields += ['retry_action', 'retry_quality', 'retry_bytes']
        writer = csv.DictWriter(out, fieldnames=fields)
        writer.writeheader()
        for frame_id, frame in enumerate(container.decode(stream)):
            image = canvas(frame)
            row = {'frame_id': frame_id, 'pts_seconds': f'{float(frame.time):.9f}'}
            encoded = {}
            for q in QUALITIES:
                start = time.perf_counter_ns()
                jpeg = encode_receiver_jpeg(image, q)
                elapsed_ms = (time.perf_counter_ns() - start) / 1e6
                encoded[q] = jpeg
                row[f'q{q}_bytes'] = len(jpeg)
                row[f'q{q}_encode_ms'] = f'{elapsed_ms:.6f}'
                row[f'q{q}_over_cap'] = int(len(jpeg) > CAP_BYTES)
            action, quality = choose_policy(len(encoded[90]), len(encoded[80]))
            chosen = encoded.get(quality)
            row['retry_action'] = action
            row['retry_quality'] = '' if quality is None else quality
            row['retry_bytes'] = '' if chosen is None else len(chosen)
            writer.writerow(row)
            rows.append(row)
    container.close()
    if not rows:
        raise RuntimeError('clip contains no decoded video frames')

    quality_result = {}
    for q in QUALITIES:
        sizes = [int(r[f'q{q}_bytes']) for r in rows]
        times = [float(r[f'q{q}_encode_ms']) for r in rows]
        quality_result[str(q)] = {
            'jpeg_bytes': stats(sizes), 'encode_time_ms': stats(times),
            'over_cap_count': sum(n > CAP_BYTES for n in sizes),
            'over_cap_fraction': sum(n > CAP_BYTES for n in sizes) / len(rows),
        }
    chosen_sizes = [int(r['retry_bytes']) for r in rows if r['retry_bytes']]
    retry = {
        'policy': 'q90 if <= cap, otherwise encode/use same-frame q80; drop if q80 also exceeds cap',
        'sent_count': len(chosen_sizes), 'dropped_count': len(rows) - len(chosen_sizes),
        'q90_count': sum(r['retry_action'] == 'send_q90' for r in rows),
        'q80_retry_count': sum(r['retry_action'] == 'retry_q80' for r in rows),
        'chosen_jpeg_bytes': stats(chosen_sizes) if chosen_sizes else None,
        'encode_time_ms_sequential_q90_plus_retry': stats([
            float(r['q90_encode_ms']) + (float(r['q80_encode_ms']) if r['retry_action'] == 'retry_q80' else 0)
            for r in rows]),
        'note': 'Sequential offline timing includes q90 then q80 only on fallback frames; excludes capture, transfer, receiver and presentation.',
    }
    result = {
        'study': 'Offline sender JPEG size and encode timing; no transmission',
        'source_file': str(args.clip.resolve()),
        'source_sha256': hashlib.sha256(args.clip.read_bytes()).hexdigest(),
        'source_video': {'width': stream.codec_context.width, 'height': stream.codec_context.height,
                         'average_rate': native_rate, 'decoded_frame_count': len(rows)},
        'canvas': '720x480 RGB, source fitted into centered 720x405 region with black letterbox',
        'encoder': 'sunshine-30fps-study/tools/gamebub/msv1.py::encode_receiver_jpeg',
        'cap_bytes': CAP_BYTES, 'qualities': quality_result, 'q90_then_q80_retry': retry,
        'caveats': [
            'This is a separate local Mass Effect clip at native average rate, not the earlier 512x288 25fps combat clip.',
            'The source is a finite prerecorded gameplay segment; its scene content and encoding are not representative of all games or direct capture.',
            'JPEG size cap excludes protocol headers and transport framing.',
            'Encode times are offline sequential Python measurements on this host; they are not real-time game capture or target-device throughput.',
            'No claims are made about transmission, receiver behavior, display presentation, perceived quality or gameplay acceptance.',
        ],
    }
    (args.output / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
    lines = [f'# Second-clip JPEG cap study ({native_rate} fps)', '',
             f"**Offline only:** {len(rows):,} decoded frames from `{args.clip.name}` ({stream.codec_context.width}×{stream.codec_context.height}); rendered to 720×480. Cap: {CAP_BYTES:,} JPEG bytes.", '',
             '| JPEG quality | Mean bytes | p95 bytes | Max bytes | Over-cap frames | Mean encode ms | p95 encode ms | Max encode ms |',
             '|---:|---:|---:|---:|---:|---:|---:|---:|']
    for q in QUALITIES:
        item = quality_result[str(q)]
        size, timing = item['jpeg_bytes'], item['encode_time_ms']
        lines.append(f"| {q} | {size['mean']:.1f} | {size['p95']:.1f} | {size['max']} | {item['over_cap_count']} ({item['over_cap_fraction']:.1%}) | {timing['mean']:.3f} | {timing['p95']:.3f} | {timing['max']:.3f} |")
    lines += ['', '## q90 with one q80 retry', '',
              f"q90 fit/sent: {retry['q90_count']}; same-frame q80 retry: {retry['q80_retry_count']}; dropped after retry: {retry['dropped_count']}.",
              f"Chosen JPEG sizes: mean {retry['chosen_jpeg_bytes']['mean']:.1f} bytes, p95 {retry['chosen_jpeg_bytes']['p95']:.1f}, max {retry['chosen_jpeg_bytes']['max']}. Sequential q90-plus-conditional-q80 encode time: mean {retry['encode_time_ms_sequential_q90_plus_retry']['mean']:.3f} ms, p95 {retry['encode_time_ms_sequential_q90_plus_retry']['p95']:.3f} ms.", '',
              'The retry result is an offline size-policy calculation. Per-frame timing is measured sequentially and does not represent realtime capture or target hardware.', '',
              'The source is a limited local prerecorded segment. Its resolution, compression, action content and scene distribution constrain generalization. These results do not establish image-quality acceptance, network delivery, receiver behavior or presentation.', '',
              'Reproduce from the prototype root with `.venv/bin/python repos/moonbub-30fps-study/experiments/jpeg-cap-quality-study/mass-effect-29_88/measure.py`. `per-frame.csv` and `results.json` retain per-frame inputs and aggregate results.']
    (args.output / 'SUMMARY.md').write_text('\n'.join(lines) + '\n')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
