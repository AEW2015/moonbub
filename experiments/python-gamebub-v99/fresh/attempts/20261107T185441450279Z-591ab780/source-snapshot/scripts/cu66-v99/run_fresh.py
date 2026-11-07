#!/usr/bin/env python3
"""Fresh shared RGB -> real restricted CU66 candidates and receiver goldens."""
from datetime import datetime, timezone
from fractions import Fraction
import gc
import hashlib
import json
from pathlib import Path
import platform
import shutil
import sys
import time
import uuid

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT/'experiments/python-gamebub-v99'
SOURCES = ROOT/'experiments/python-gamebub-v98/sources'
sys.path.insert(0, str(AREA/'encoder'))
sys.path.insert(0, str(ROOT/'experiments/python-gamebub-v98'))
import fresh_cu66 as encoder
import metrics


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, obj):
    path.write_text(json.dumps(obj, indent=2, allow_nan=False)+'\n')


def gate():
    mem = {line.split(':')[0]: int(line.split()[1]) for line in Path('/proc/meminfo').read_text().splitlines()}
    psi = Path('/proc/pressure/memory').read_text()
    full = float(next(line for line in psi.splitlines() if line.startswith('full ')).split()[1].split('=')[1])
    assert mem['MemAvailable'] >= 8*1024*1024 and full < 1, 'need available RAM>=8GiB and full PSI avg10<1'
    return {'available_kib': mem['MemAvailable'], 'memory_psi': psi}


def expand565(words):
    r = (words >> 11).astype(np.uint8)
    g = ((words >> 5) & 63).astype(np.uint8)
    b = (words & 31).astype(np.uint8)
    return np.stack(((r << 3) | (r >> 2), (g << 2) | (g >> 4), (b << 3) | (b >> 2)), -1)


def main():
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+uuid.uuid4().hex[:8]
    out = AREA/'fresh/attempts'/stamp
    out.mkdir(parents=True)
    report = {'schema': 'v99-fresh-cu66-campaign-v1', 'status': 'FAIL',
              'attempt': str(out.relative_to(ROOT)), 'baseline_commit': '35949d6f41366cd5725b433a136fadb1b6ce95f6',
              'cases': [], 'source_sha256': {}, 'hardware_measured': False}
    started = time.perf_counter_ns()
    try:
        report['resources_start'] = gate()
        pins = encoder.source_pins()
        for path in (Path(__file__).resolve(), Path(metrics.__file__), SOURCES/'manifest.json'):
            pins[str(path.relative_to(ROOT))] = sha(path)
        report['source_sha256'] = pins
        for name in pins:
            dest = out/'source-snapshot'/name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT/name, dest)
        manifest = json.loads((SOURCES/'manifest.json').read_text())
        report['source_manifest_sha256'] = sha(SOURCES/'manifest.json')
        report['source_clips'] = manifest['clips']
        report['host'] = {'platform': platform.platform(), 'python': platform.python_version()}
        v98_index = json.loads((ROOT/'experiments/python-gamebub-v98/index.json').read_text())
        v98 = json.loads((ROOT/v98_index['attempt_json']).read_text())
        assert sha(ROOT/v98_index['attempt_json']) == v98_index['sha256']
        report['v98_anchor_report'] = v98_index
        anchor_info = json.loads((ROOT/v98['cases'][0]['info_path']).read_text())
        all_ledger = []
        for clip in manifest['clips']:
            path = SOURCES/clip['npz_path']
            assert sha(path) == clip['npz_sha256']
            with np.load(path, allow_pickle=False) as npz:
                frames = npz['rgb']
            frame_shas = [hashlib.sha256(frame.tobytes()).hexdigest() for frame in frames]
            assert frame_shas == clip['frame_sha256']
            frames.setflags(write=False)
            fps = Fraction(clip['source_metadata'].get('selected_fps', clip['source_metadata']['source_fps']))
            roi = [item['rect'] if isinstance(item, dict) else item for item in clip['roi']['rectangles']]
            for scale in (8, 16, 32):
                gate()
                case_id = clip['clip_id']+'-q'+str(scale)
                dest = out/clip['clip_id']/('q'+str(scale))
                print('START', case_id, flush=True)
                result = encoder.encode_sequence(frames, quant_scale=scale, output_dir=dest, clip_id=case_id)
                assert result['input_color_code_sha256'] == anchor_info['color_implementation_sha256'], 'different input color arithmetic'
                assert result['source_sha256'] == {name: sha(ROOT/name) for name in result['source_sha256']}
                assert [r['source_rgb_sha256'] for r in result['records']] == frame_shas
                accepted_ids = [i for i, row in enumerate(result['records']) if row['accepted']]
                accepted_source = [frames[i] for i in accepted_ids]
                accepted_display = [expand565(result['outputs_rgb565'][i]) for i in accepted_ids]
                quality = (metrics.sequence_quality(accepted_source, accepted_display, clip['active_rect'], roi)
                           if accepted_ids else None)
                complete = len(accepted_ids) == len(frames)
                if quality is not None and not complete:
                    quality['temporal_error_mse_mean'] = None
                    quality['temporal_error_mse_max'] = None
                    for row in quality['frames']:
                        row['input_frame_id'] = accepted_ids[row['id']]
                        row['temporal_error_mse'] = None
                dump(dest/'quality.json', {'accepted_input_ids': accepted_ids, 'all_inputs_admitted': complete,
                    'scope': 'accepted-only pixel quality; temporal diagnostic valid only if complete input sequence admitted',
                    'quality': quality})
                disk = json.loads((dest/'records.json').read_text())
                sizes = [r['bytes'] for r in disk['records']]
                case = {'case_id': case_id, 'source_clip_id': clip['clip_id'], 'quant_scale': scale,
                    'records_path': str((dest/'records.json').relative_to(ROOT)),
                    'records_sha256': sha(dest/'records.json'), 'quality_path': str((dest/'quality.json').relative_to(ROOT)),
                    'quality_sha256': sha(dest/'quality.json'), 'source_npz_sha256': clip['npz_sha256'],
                    'source_frame_sha256': frame_shas,
                    'input_frames': len(frames), 'accepted_frames': len(accepted_ids),
                    'rejected_frames': len(frames)-len(accepted_ids), 'accepted_input_ids': accepted_ids,
                    'all_inputs_admitted': complete, 'candidate_bytes_all_attempts': sum(sizes),
                    'accepted_bytes': sum(r['bytes'] for r in disk['records'] if r['accepted']),
                    'complete_candidate_bytes': metrics.distribution(sizes),
                    'offered_candidate_mbps_at_selected_cadence_including_rejects': sum(sizes)/len(frames)*8*float(fps)/1e6,
                    'encoder_prepare_ms': metrics.distribution([r['encode_ms'] for r in disk['records']]),
                    'active_psnr_db_accepted_only': quality['pooled']['active']['psnr_db'] if quality else None,
                    'roi_psnr_db_accepted_only': quality['pooled']['roi']['psnr_db'] if quality else None}
                ledger = [json.loads(line) for line in Path(result['ledger_path']).read_text().splitlines()]
                all_ledger.extend(ledger)
                report['cases'].append(case)
                print('DONE', case_id, json.dumps(case), flush=True)
                dump(out/'results.json', report)
                del result, disk, quality, accepted_display
                gc.collect()
            assert sha(path) == clip['npz_sha256']
        assert pins == {name: sha(ROOT/name) for name in pins}, 'measured code/input manifest changed'
        ledger_path = out/'accepted-ledger.jsonl'
        ledger_path.write_text(''.join(json.dumps(row, sort_keys=True)+'\n' for row in all_ledger))
        report['ledger_path'] = str(ledger_path.relative_to(ROOT))
        report['ledger_sha256'] = sha(ledger_path)
        report['candidate_attempts'] = sum(c['input_frames'] for c in report['cases'])
        report['accepted_frames'] = len(all_ledger)
        report['rejected_frames'] = report['candidate_attempts']-len(all_ledger)
        report['complete_case_count'] = sum(c['all_inputs_admitted'] for c in report['cases'])
        report['resources_end'] = gate()
        report['status'] = 'PASS_SOFTWARE_CAMPAIGN'
    except BaseException as error:
        report['error'] = type(error).__name__+': '+str(error)
        raise
    finally:
        report['wall_ms'] = (time.perf_counter_ns()-started)/1e6
        report['artifact_sha256'] = {str(p.relative_to(out)): sha(p) for p in sorted(out.rglob('*'))
            if p.is_file() and p.name != 'results.json' and 'source-snapshot' not in p.parts}
        dump(out/'results.json', report)
        if report['status'] == 'PASS_SOFTWARE_CAMPAIGN':
            dump(AREA/'fresh/index.json', {'attempt_json': str((out/'results.json').relative_to(ROOT)),
                                        'sha256': sha(out/'results.json')})


if __name__ == '__main__':
    main()
