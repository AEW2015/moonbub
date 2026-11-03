#!/usr/bin/env python3
"""Measure RGB PSNR for q90, q80, and the one-retry 48 KiB policy offline."""
import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import sys

import av
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
GAMEBUB = PROJECT / 'repos' / 'sunshine-30fps-study' / 'tools' / 'gamebub'
sys.path.insert(0, str(GAMEBUB))
from host import canvas, clip_frames  # noqa: E402
from msv1 import encode_receiver_jpeg  # noqa: E402

CAP_BYTES = 48 * 1024


def percentile(values, fraction):
    ordered = sorted(values)
    pos = (len(ordered) - 1) * fraction
    low, high = math.floor(pos), math.ceil(pos)
    if low == high:
        return float(ordered[low])
    return ordered[low] + (ordered[high] - ordered[low]) * (pos - low)


def summarize(values):
    finite = [v for v in values if v is not None]
    result = {'count': len(values), 'finite_psnr_count': len(finite),
              'perfect_match_count': len(values) - len(finite)}
    names = ('mean', 'p5', 'median', 'p95', 'min', 'max')
    stats = ([float(np.mean(finite)), percentile(finite, .05), percentile(finite, .5),
              percentile(finite, .95), min(finite), max(finite)] if finite else [None] * 6)
    result.update({f'{name}_db_finite_only': stat for name, stat in zip(names, stats)})
    return result


def choose_policy(size90, size80, cap=CAP_BYTES):
    """Return action and selected quality for q90 with one q80 fallback."""
    if size90 <= cap:
        return 'send_q90', 90
    if size80 <= cap:
        return 'retry_q80', 80
    return 'drop_after_retry', None


def frame_psnr(reference, encoded):
    with Image.open(io.BytesIO(bytes(encoded))) as image:
        decoded = np.asarray(image.convert('RGB'), dtype=np.float32)
    error = reference.astype(np.float32) - decoded
    mse = float(np.mean(error * error))
    return None if mse == 0 else 10.0 * math.log10((255.0 * 255.0) / mse)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--clip', type=Path, default=PROJECT / 'media' / 'mass-effect-combat.mp4')
    parser.add_argument('--fps', type=int, default=25)
    parser.add_argument('--output', type=Path, default=HERE)
    args = parser.parse_args()
    if not args.clip.is_file():
        parser.error(f'clip not found: {args.clip}')
    if args.fps <= 0:
        parser.error('fps must be positive')
    args.output.mkdir(parents=True, exist_ok=True)

    rows = []
    q90_over, q80_over, selected_over = 0, 0, 0
    retry_frame_ids = []
    with (args.output / 'per-frame.csv').open('w', newline='') as stream:
        columns = ['frame_id', 'pts_seconds', 'q90_bytes', 'q90_rgb_psnr_db',
                   'q80_bytes', 'q80_rgb_psnr_db', 'policy_action', 'selected_quality',
                   'selected_bytes', 'selected_rgb_psnr_db', 'fallback_psnr_delta_db']
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for frame_id, source_frame in enumerate(clip_frames(args.clip, args.fps)):
            reference = np.asarray(canvas(source_frame), dtype=np.uint8)
            q90 = encode_receiver_jpeg(Image.fromarray(reference), 90)
            q80 = encode_receiver_jpeg(Image.fromarray(reference), 80)
            size90, size80 = len(q90), len(q80)
            psnr90, psnr80 = frame_psnr(reference, q90), frame_psnr(reference, q80)
            q90_over += size90 > CAP_BYTES
            q80_over += size80 > CAP_BYTES
            action, selected_quality = choose_policy(size90, size80)
            if action == 'send_q90':
                selected_jpeg, selected_psnr = q90, psnr90
            elif action == 'retry_q80':
                selected_jpeg, selected_psnr = q80, psnr80
                retry_frame_ids.append(frame_id)
            else:
                selected_jpeg, selected_psnr = None, None
                selected_over += 1
            delta = None if psnr80 is None or psnr90 is None else psnr80 - psnr90
            row = {
                'frame_id': frame_id,
                'pts_seconds': f'{float(source_frame.time):.9f}',
                'q90_bytes': size90,
                'q90_rgb_psnr_db': '' if psnr90 is None else f'{psnr90:.8f}',
                'q80_bytes': size80,
                'q80_rgb_psnr_db': '' if psnr80 is None else f'{psnr80:.8f}',
                'policy_action': action,
                'selected_quality': '' if selected_quality is None else selected_quality,
                'selected_bytes': '' if selected_jpeg is None else len(selected_jpeg),
                'selected_rgb_psnr_db': '' if selected_psnr is None else f'{selected_psnr:.8f}',
                'fallback_psnr_delta_db': '' if delta is None else f'{delta:.8f}',
            }
            writer.writerow(row)
            rows.append(row)

    if not rows:
        raise RuntimeError('sampler returned no frames')
    def series(field):
        return [None if r[field] == '' else float(r[field]) for r in rows]
    selected = series('selected_rgb_psnr_db')
    q90_sizes = [int(r['q90_bytes']) for r in rows]
    q80_sizes = [int(r['q80_bytes']) for r in rows]
    selected_sizes = [int(r['selected_bytes']) for r in rows if r['selected_bytes']]
    q90_sent = [None if r['q90_rgb_psnr_db'] == '' else float(r['q90_rgb_psnr_db']) for r in rows if int(r['q90_bytes']) <= CAP_BYTES]
    fallback_deltas = [float(r['fallback_psnr_delta_db']) for r in rows if r['policy_action'] == 'retry_q80' and r['fallback_psnr_delta_db']]
    result = {
        'study': 'Offline RGB PSNR against upscaled sampled source frames',
        'source_file': str(args.clip.resolve()),
        'source_sha256': hashlib.sha256(args.clip.read_bytes()).hexdigest(),
        'sample_count': len(rows),
        'sampling_fps': args.fps,
        'canvas': {'size': '720x480 RGB', 'content': '720x405 centered; black letterbox'},
        'encoder': {'function': 'sunshine-30fps-study/tools/gamebub/msv1.py::encode_receiver_jpeg',
                    'profile': 'baseline 4:2:0, no restart, nonprogressive, default Huffman',
                    'qualities': [90, 80]},
        'cap_bytes': CAP_BYTES,
        'comparison': {
            'fixed_q90_theoretical_all_frames': {
                'size_bytes': {'mean': float(np.mean(q90_sizes)), 'p95': percentile(q90_sizes, .95), 'max': max(q90_sizes)},
                'rgb_psnr_db': summarize(series('q90_rgb_psnr_db')),
                'over_cap_count': q90_over,
            },
            'drop_only_q90_frames_that_fit': {
                'sent_count': len(q90_sent), 'dropped_count': q90_over,
                'sent_rgb_psnr_db': summarize(q90_sent),
            },
            'fixed_q80_all_frames': {
                'size_bytes': {'mean': float(np.mean(q80_sizes)), 'p95': percentile(q80_sizes, .95), 'max': max(q80_sizes)},
                'rgb_psnr_db': summarize(series('q80_rgb_psnr_db')),
                'over_cap_count': q80_over,
            },
            'q90_then_single_q80_retry': {
                'sent_count': len(selected), 'dropped_count': selected_over,
                'q90_count': sum(r['policy_action'] == 'send_q90' for r in rows),
                'q80_retry_count': len(retry_frame_ids),
                'chosen_frame_size_bytes': {'mean': float(np.mean(selected_sizes)),
                                             'p95': percentile(selected_sizes, .95), 'max': max(selected_sizes)},
                'chosen_rgb_psnr_db': summarize(selected),
                'fallback_q80_minus_q90_rgb_psnr_db': summarize(fallback_deltas),
                'fallback_undefined_exact_pair_count': sum(
                    r['policy_action'] == 'retry_q80' and not r['fallback_psnr_delta_db'] for r in rows),
                'retry_frame_ids': retry_frame_ids,
            },
        },
        'metric_caveats': [
            'RGB PSNR compares decoded JPEG against the same 720x480 canvas made from the already-compressed 512x288 source; zero-error frames are reported as exact matches because their PSNR is infinite.',
            'q90 theoretical quality includes oversized frames that a drop-only policy cannot send.',
            'The retry policy uses q90 when it fits and q80 only for q90-over-cap frames; only selected frames count in its chosen-quality PSNR distribution.',
            'The cap is JPEG bytes only. MSV1 headers, transport overhead, encode deadlines, network, receiver and display are excluded.',
            'Offline sample does not establish perceptual acceptability for gameplay.',
        ],
        'scope': 'No sender session, adaptation, packetization, network or hardware execution.',
    }
    (args.output / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
    q90_all = result['comparison']['fixed_q90_theoretical_all_frames']['rgb_psnr_db']
    q90_fit = result['comparison']['drop_only_q90_frames_that_fit']['sent_rgb_psnr_db']
    q80_all = result['comparison']['fixed_q80_all_frames']['rgb_psnr_db']
    hybrid = result['comparison']['q90_then_single_q80_retry']
    lines = [
        '# q90 vs q80 48 KiB retry image-quality study', '',
        f"**Offline only:** {len(rows):,} native-{args.fps} fps samples. PSNR compares decoded JPEG to the same upscaled 720×480 canvas.", '',
        '| Policy/population | Frames (finite / exact) | Mean PSNR dB* | p5* | Median* | p95* | Min* | Max* | Over cap / dropped |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|',
    ]
    def line(label, stats, n, over):
        if stats['finite_psnr_count']:
            values = [f"{stats[k]:.3f}" for k in ('mean_db_finite_only', 'p5_db_finite_only', 'median_db_finite_only', 'p95_db_finite_only', 'min_db_finite_only', 'max_db_finite_only')]
        else:
            values = ['n/a'] * 6
        lines.append(f"| {label} | {stats['finite_psnr_count']} / {stats['perfect_match_count']} | {' | '.join(values)} | {over} |")
    line('Fixed q90, theoretical all frames', q90_all, q90_all['count'], q90_over)
    line('Drop-only q90, frames sent', q90_fit, q90_fit['count'], q90_over)
    line('Fixed q80, all frames', q80_all, q80_all['count'], q80_over)
    line('q90 then one q80 retry, frames sent', hybrid['chosen_rgb_psnr_db'], hybrid['sent_count'], hybrid['dropped_count'])
    delta_stats = hybrid['fallback_q80_minus_q90_rgb_psnr_db']
    lines += ['', '*Finite PSNR statistics exclude exact pixel matches: PSNR is mathematically infinite when MSE is zero. Exact-match frame counts are shown separately.', '', f"The retry policy used q90 on {hybrid['q90_count']:,} frames and q80 on {hybrid['q80_retry_count']:,} q90-over-cap frames; it dropped {hybrid['dropped_count']:,}. On retried frames, q80 minus q90 PSNR mean was {delta_stats['mean_db_finite_only']:.3f} dB (min {delta_stats['min_db_finite_only']:.3f}, max {delta_stats['max_db_finite_only']:.3f}); {hybrid['fallback_undefined_exact_pair_count']} exact-match pairs have undefined delta.", '', 'These measurements quantify distortion versus an already-compressed, low-resolution source after upscaling. They do not establish perceptual quality or gameplay acceptance. Oversized q90 frames in the theoretical distribution are not sendable under the cap; the drop-only row excludes them and reports their count separately.', '', 'No transmission or hardware was used. See `README.md` for source details and reproduction.']
    (args.output / 'SUMMARY.md').write_text('\n'.join(lines) + '\n')
    print((args.output / 'SUMMARY.md').read_text())


if __name__ == '__main__':
    main()
