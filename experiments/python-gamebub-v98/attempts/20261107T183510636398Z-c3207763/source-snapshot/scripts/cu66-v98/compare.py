#!/usr/bin/env python3
"""Bounded common-input V98 controls. Saves failed attempts without replacing them."""
import argparse
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import sys
import time
import uuid

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT/'experiments/python-gamebub-v98'
sys.path.insert(0, str(AREA))
import metrics
import standard_controls as standard
import custom_controls as custom


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def dump(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False)+'\n')


def resource_gate():
    memory = {line.split(':')[0]: int(line.split()[1]) for line in
              Path('/proc/meminfo').read_text().splitlines() if ':' in line}
    pressure = Path('/proc/pressure/memory').read_text()
    full = float(next(line for line in pressure.splitlines() if line.startswith('full ')).split()[1].split('=')[1])
    if memory['MemAvailable'] < 8*1024*1024 or full >= 1:
        raise RuntimeError('host resource gate: need >=8GiB available RAM and memory full avg10<1')
    return {'MemAvailable_kib': memory['MemAvailable'], 'memory_pressure': pressure}


def dependencies():
    paths = {Path(__file__).resolve(), AREA/'source_prepare.py', AREA/'sources/manifest.json'}
    for module in tuple(sys.modules.values()):
        file = getattr(module, '__file__', None)
        if file:
            path = Path(file).resolve()
            if path.is_relative_to(ROOT) and path.suffix == '.py':
                paths.add(path)
    return sorted(paths)


def summary(info, quality, count, fps):
    groups = {i: 0 for i in range(count)}
    for packet in info['packets']:
        groups[packet['pts']] += packet['bytes']
    groups[0] += info['extradata_bytes']
    sizes = list(groups.values())
    calls = info['frame_calls']
    seen = [pts for call in calls for pts in call['emitted_pts']]
    flush = [i for i in range(count) if i not in seen]
    lag = [call['id']-pts for call in calls for pts in call['emitted_pts']]
    assert len(set(seen)) == len(seen), 'duplicate emission'
    assert all(value >= 0 for value in lag)
    dec = [call['decode_ms'] for call in info['decode_calls']]
    return {
        'coded_bytes': sum(sizes), 'mean_bytes_per_frame': sum(sizes)/count,
        'coded_mbps_at_source_cadence': sum(sizes)/count*8*float(fps)/1e6,
        'coded_mbps_at_hypothetical_30': sum(sizes)/count*8*30/1e6,
        'access_unit_bytes': metrics.distribution(sizes),
        'access_units_over_49152': sum(size > 49152 for size in sizes),
        'encode_call_ms': metrics.distribution([call['encode_call_ms'] for call in calls]),
        'decode_call_ms': metrics.distribution(dec),
        'encode_frontend_ms': metrics.distribution([call['encode_call_ms']+call.get('convert_ms', 0)
                                                   for call in calls]),
        'decode_to_rgb_ms': metrics.distribution([call['decode_ms']+call.get('rgb_convert_ms', 0)
                                                 for call in info['decode_calls']]),
        'timing_scope': ('Frontend includes RGB-to-planes and plane copy where exposed; GM01 includes '
                         'analyze/candidate/commit. Backend includes receive or native decode plus RGB '
                         'conversion. Neither includes RGB565 packing, transport or display; verification '
                         'and file IO excluded. Call distributions are not paced latency or hardware costs.'),
        'encoder_output_lag_frames_max': max(lag, default=None),
        'ids_emitted_only_at_flush': flush,
        'active_mse': quality['pooled']['active']['mse'],
        'roi_mse': quality['pooled']['roi']['mse'],
        'active_psnr_db': quality['pooled']['active']['psnr_db'],
        'roi_psnr_db': quality['pooled']['roi']['psnr_db'],
        'worst_frame_psnr_db': quality['worst_active_frame_psnr_db'],
        'temporal_error_mse_mean': quality['temporal_error_mse_mean'],
        'temporal_error_mse_max': quality['temporal_error_mse_max'],
        'peak_access_unit_frame_ids': [i for i, size in enumerate(sizes) if size == max(sizes)],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--clip', action='append', help='Only these clip IDs; default all')
    parser.add_argument('--smoke', action='store_true', help='One quality point per codec')
    args = parser.parse_args()
    started = time.perf_counter_ns()
    attempt = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+uuid.uuid4().hex[:8]
    out = AREA/'attempts'/attempt
    out.mkdir(parents=True)
    report = {'schema': 'v98-common-input-controls-v1', 'status': 'FAIL',
              'attempt': str(out.relative_to(ROOT)), 'cases': [], 'baseline_frozen':
              '4234feadaabbad41cb53b47137c124166bf0fab8', 'target_hardware_measured': False}
    try:
        report['resources_start'] = resource_gate()
        paths = dependencies()
        pins = {str(p.relative_to(ROOT)): sha(p) for p in paths}
        report['source_sha256'] = pins
        for path in paths:
            target = out/'source-snapshot'/path.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
        report['host'] = {'platform': platform.platform(), 'python': platform.python_version(),
                          'machine': platform.machine(), 'logical_cpus': os.cpu_count(),
                          'cpuinfo': Path('/proc/cpuinfo').read_text().split('model name')[1].split('\n')[0].strip()}
        manifest = json.loads((AREA/'sources/manifest.json').read_text())
        report['input_manifest_sha256'] = sha(AREA/'sources/manifest.json')
        report['source_clips'] = manifest['clips']
        selected = [clip for clip in manifest['clips'] if not args.clip or clip['clip_id'] in args.clip]
        if not selected or (args.clip and set(args.clip)-{clip['clip_id'] for clip in selected}):
            raise ValueError('unknown/empty source selection')
        controls = ([('hevc', 36), ('av1', 38), ('jpeg', 6), ('gm01', 16)] if args.smoke else
                    [('hevc', p) for p in (28, 36, 44)]+[('av1', p) for p in (28, 38, 48)]+
                    [('jpeg', p) for p in (2, 6, 12)]+[('gm01', p) for p in (8, 16, 32, 'global16')])
        report['controls'] = controls
        for clip in selected:
            source = AREA/'sources'/clip['npz_path']
            assert sha(source) == clip['npz_sha256']
            with np.load(source, allow_pickle=False) as npz:
                assert npz.files == ['rgb']
                frames = npz['rgb']
            assert frames.shape == (clip['frame_count'], 480, 720, 3) and frames.dtype == np.uint8
            frame_shas = [hashlib.sha256(frame.tobytes()).hexdigest() for frame in frames]
            assert frame_shas == clip['frame_sha256']
            frames.setflags(write=False)
            fps = Fraction(clip['source_metadata'].get('selected_fps', clip['source_metadata']['source_fps']))
            roi = [r['rect'] if isinstance(r, dict) else r for r in clip['roi']['rectangles']]
            floor = metrics.sequence_quality(frames, [custom.gm.ft.planes_to_rgb(custom.gm.ft.rgb_to_planes(f))
                for f in frames], clip['active_rect'], roi)
            floor_path = out/clip['clip_id']/'common-color-floor.json'
            floor_path.parent.mkdir(parents=True)
            dump(floor_path, floor)
            for codec, parameter in controls:
                resource_gate()
                label = codec+'-'+str(parameter)
                dest = out/clip['clip_id']/label
                dest.mkdir()
                print('START', clip['clip_id'], label, flush=True)
                t = time.perf_counter_ns()
                if codec == 'gm01':
                    decoded, info = custom.run(frames, parameter, fps=float(fps), output_dir=dest)
                else:
                    decoded, info = standard.run(list(frames), codec, parameter, fps=fps, output_dir=dest)
                complete_call_ms = (time.perf_counter_ns()-t)/1e6
                assert len(decoded) == len(frames)
                assert [hashlib.sha256(frame.tobytes()).hexdigest() for frame in frames] == frame_shas
                quality = metrics.sequence_quality(frames, decoded, clip['active_rect'], roi)
                info_path = dest/'codec-info.json'
                dump(info_path, info)
                dump(dest/'quality.json', quality)
                # Actual source and decoded RGB565 samples, including known synthetic cut.
                samples = sorted({0, len(frames)//2, len(frames)-1})
                for index in samples:
                    Image.fromarray(metrics.displayed(decoded[index])).save(dest/f'decoded-{index:03}.png')
                case = {'case_id': clip['clip_id']+'/'+label, 'clip_id': clip['clip_id'],
                        'codec': codec, 'parameter': parameter, 'frame_count': len(frames),
                        'source_npz_sha256': clip['npz_sha256'], 'input_frame_sha256': frame_shas,
                        'info_path': str(info_path.relative_to(ROOT)), 'info_sha256': sha(info_path),
                        'quality_path': str((dest/'quality.json').relative_to(ROOT)),
                        'quality_sha256': sha(dest/'quality.json'),
                        'whole_wrapper_call_ms_including_verification_and_artifact_io': complete_call_ms,
                        'summary': summary(info, quality, len(frames), fps)}
                report['cases'].append(case)
                print('DONE', case['case_id'], json.dumps(case['summary']), flush=True)
                dump(out/'results.json', report)
            assert sha(source) == clip['npz_sha256']
        assert pins == {str(p.relative_to(ROOT)): sha(p) for p in paths}, 'code/input manifest changed during run'
        report['rate_quality_frontier'] = {clip['clip_id']: metrics.pareto([
            dict(case_id=case['case_id'], **case['summary']) for case in report['cases']
            if case['clip_id'] == clip['clip_id']]) for clip in selected}
        report['resources_end'] = resource_gate()
        report['status'] = 'PASS'
    except BaseException as error:
        report['error'] = type(error).__name__+': '+str(error)
        raise
    finally:
        report['wall_ms'] = (time.perf_counter_ns()-started)/1e6
        report['artifact_sha256'] = {str(p.relative_to(out)): sha(p) for p in sorted(out.rglob('*'))
            if p.is_file() and p.name != 'results.json' and 'source-snapshot' not in p.parts}
        dump(out/'results.json', report)
        if report['status'] == 'PASS':
            dump(AREA/'index.json', {'attempt_json': str((out/'results.json').relative_to(ROOT)),
                                    'sha256': sha(out/'results.json')})


if __name__ == '__main__':
    main()
