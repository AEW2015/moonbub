#!/usr/bin/env python3
"""Offline native-frame codec comparison and conditional ideal-link projections."""
import argparse
import hashlib
import io
import json
import math
import os
from pathlib import Path
import platform
import sys
import time

import av
import numpy as np
from PIL import Image, __version__ as pillow_version

import codec
import corpus
import pacing
import temporal
import budget

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SUNSHINE = Path(os.environ.get('GAMEBUB_SUNSHINE_TOOLS', str(ROOT/'repos/sunshine-30fps-study/tools/gamebub')))
sys.path.insert(0, str(SUNSHINE))
from msv1 import encode_receiver_jpeg


def distribution(values):
    return {key: float(value) for key, value in zip(
        ('mean', 'p50', 'p95', 'p99', 'max'),
        (np.mean(values), *np.percentile(values, [50, 95, 99]), max(values)))}


def psnr(mse):
    return None if mse == 0 else 10*math.log10(65025/mse)


def hud_sequence(count):
    base = corpus.synthetic_frames(count=3)[2][1]
    frames = []
    for i in range(count):
        frame = base.copy()
        frame[32:48, 16+i*16:32+i*16] = (255, 255, 255)
        frames.append(frame)
    return frames, {'source': 'synthetic coherent HUD/16-pixel-moving-square',
                    'source_fps': None, 'active_rects': [(0, 0, 720, 480)]*count,
                    'frame_sha256': [hashlib.sha256(x.tobytes()).hexdigest() for x in frames],
                    'timing_scope': 'synthetic sequence; no native capture cadence'}


def evaluate(name, frames, manifest):
    rows = []
    profiles = [('tile-lossless', 1, False, False), ('dpcm-lossless', 1, True, False),
                ('dpcm-q2', 2, True, False), ('dpcm-q4', 4, True, False),
                ('delta-q2', 2, True, True)]
    profiles += [(f'jpeg-q{q}', q, False, False) for q in (50, 65, 80)]
    profiles += [('jpeg-budget8', 8, False, False)]
    for label, q, dpcm, delta in profiles:
        reference = None
        receiver = temporal.Receiver(epoch=1) if delta else None
        series = []
        for index, rgb in enumerate(frames):
            packed = corpus.rgb565(rgb)
            started = time.perf_counter_ns()
            account = {}
            if label == 'jpeg-budget8':
                packet, account = budget.choose_jpeg(Image.fromarray(rgb))
                if packet is None:
                    raise RuntimeError('budget policy dropped a frame; do not omit it from corpus statistics')
            elif label.startswith('jpeg'):
                packet = bytes(encode_receiver_jpeg(Image.fromarray(rgb), q))
            elif delta:
                target = codec.quantize(packed, q)
                packet = temporal.encode(target, reference if index % 30 else None,
                                         frame_id=index, reference_id=index-1, use_dpcm=dpcm)
            else:
                packet = codec.encode(packed, quant_step=q, use_dpcm=dpcm)
            encoded_at = time.perf_counter_ns()
            if label.startswith('jpeg'):
                with Image.open(io.BytesIO(packet)) as image:
                    intermediate = np.asarray(image.convert('RGB'))
                decoded_at = time.perf_counter_ns()
                decoded = corpus.rgb565(intermediate)
            elif delta:
                decoded, account = receiver.receive(packet)
                decoded_at = time.perf_counter_ns()
                intermediate = corpus.expand565(decoded)
                if not np.array_equal(decoded, target):
                    raise AssertionError('temporal reconstruction mismatch')
                reference = decoded
            else:
                decoded = codec.decode(packet)
                decoded_at = time.perf_counter_ns()
                intermediate = corpus.expand565(decoded)
                if not np.array_equal(decoded, codec.quantize(packed, q)):
                    raise AssertionError('intra reconstruction mismatch')
                account = codec.stats(packet)
            rect = tuple(manifest['active_rects'][index])
            quality = corpus.metrics(rgb, corpus.expand565(decoded), rect)
            preoutput = corpus.metrics(rgb, intermediate, rect)
            series.append({'index': index, 'bytes': len(packet), 'wire_bytes': pacing.wire_bytes(len(packet)),
                           'encode_ms_python': (encoded_at-started)/1e6,
                           'decode_ms_python': (decoded_at-encoded_at)/1e6,
                           'quality': quality, 'pre_rgb565_quality': preoutput,
                           'reconstruction_sha256': hashlib.sha256(decoded.astype('<u2').tobytes()).hexdigest(),
                           'accounting': account})
        sizes = [x['bytes'] for x in series]
        wire = [x['wire_bytes'] for x in series]
        active_mse = float(np.mean([x['quality']['active']['mse'] for x in series]))
        full_mse = float(np.mean([x['quality']['mse'] for x in series]))
        source_fps = manifest.get('source_fps')
        if source_fps:
            from fractions import Fraction
            source_fps = float(Fraction(source_fps))
        times = manifest.get('selected_times_seconds', [])
        observed_fps = ((len(times)-1)/(times[-1]-times[0])
                        if len(times) > 1 and all(t is not None for t in times) and times[-1] > times[0]
                        else None)
        projections = []
        for rate in (8, 12, 20):
            for phase in (0, 8.333333):
                model = pacing.simulate(sizes, link_mbps=rate, phase_ms=phase, cap=262144,
                                        references=[None if i % 30 == 0 else i-1 for i in range(len(sizes))]
                                        if delta else None)
                model.pop('records')
                projections.append({'link_mbps': rate, 'phase_ms': phase, **model})
        row = {'corpus': name, 'profile': label, 'frames': len(frames),
               'size_bytes': distribution(sizes), 'wire_bytes': distribution(wire),
               'wire_mbps_at_native_fps': None if source_fps is None else np.mean(wire)*8*source_fps/1e6,
               'wire_mbps_at_observed_selected_pts_cadence': None if observed_fps is None else np.mean(wire)*8*observed_fps/1e6,
               'projected_wire_mbps_at_30fps': np.mean(wire)*8*30/1e6,
               'active_rgb565_output_psnr_db': psnr(active_mse),
               'full_rgb565_output_psnr_db': psnr(full_mse),
               'over_48k': sum(x > 49152 for x in sizes), 'over_256k': sum(x > 262144 for x in sizes),
               'encode_ms_python': distribution([x['encode_ms_python'] for x in series]),
               'decode_ms_python': distribution([x['decode_ms_python'] for x in series]),
               'ideal_link_30fps_projections': projections, 'per_frame': series}
        rows.append(row)
        print(json.dumps({key: row[key] for key in ('corpus', 'profile', 'projected_wire_mbps_at_30fps',
                         'active_rgb565_output_psnr_db', 'over_48k')}), flush=True)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--frames', type=int, default=30)
    parser.add_argument('--output', type=Path, default=HERE/'results.json')
    parser.add_argument('--media-dir', type=Path, default=ROOT/'media')
    args = parser.parse_args()
    if not 1 <= args.frames <= 120:
        parser.error('frames must be 1..120')
    manifests, rows = {}, []
    source_paths = [*sorted(HERE.glob('*.py')), SUNSHINE/'msv1.py', SUNSHINE/'host.py']
    hashes = {str(p.relative_to(HERE)) if p.parent == HERE else 'sunshine/'+p.name:
              hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}
    for name in ('mass-effect-combat', 'mass-effect-2600', 'synthetic-hud'):
        if name == 'synthetic-hud':
            frames, manifest = hud_sequence(min(args.frames, 30))
        else:
            frames, manifest = corpus.load_video(args.media_dir/f'{name}.mp4', max_frames=args.frames)
        if not frames:
            raise RuntimeError(f'empty corpus: {name}')
        manifests[name] = manifest
        rows.extend(evaluate(name, frames, manifest))
        result = {'evidence': 'Python offline codec and conditional schedule models; no hardware',
                  'versions': {'python': platform.python_version(), 'numpy': np.__version__,
                               'pillow': pillow_version, 'pyav': av.__version__},
                  'source_hashes': hashes,
                  'schedule_assumptions': {'fps': 30, 'decode_ms': 8, 'qspi_mbps': 160,
                                           'refresh_hz': 60, 'policy': 'latest',
                                           'packet_payload': 1024, 'app_header': 40, 'ipv4_udp_header': 28,
                                           'excludes': 'capture/encode time, RF/link-layer overhead, audio/input/ACK, retries, physical service'},
                  'corpora': manifests, 'rows': rows}
        args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    current_hashes = {str(p.relative_to(HERE)) if p.parent == HERE else 'sunshine/'+p.name:
                      hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}
    if current_hashes != hashes:
        raise RuntimeError('source files changed during benchmark; discard this run')


if __name__ == '__main__':
    main()
