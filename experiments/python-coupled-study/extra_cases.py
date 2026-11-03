#!/usr/bin/env python3
"""Actual-codec synthetic cap stress and slower assumed decoder sensitivity."""
import dataclasses
import hashlib
import json
from pathlib import Path

import model
from model import Config, run
from stress_corpus import make_stress_frames
import stress_corpus

HERE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    source = json.loads((HERE/'results.json').read_text())
    paths = [HERE/'extra_cases.py', HERE/'model.py', HERE/'validation.py', HERE/'stress_corpus.py',
             Path(model.mc.__file__), Path(model.mc.cc.__file__), Path(model.mc.ft.__file__), Path(model.corpus.__file__)]
    hashes = {str(p): digest(p) for p in paths}
    cases = []
    for name, manifest in source['manifests'].items():
        if 'heldout' in name:
            continue
        frames, current = model.corpus.load_video(manifest['source'], max_frames=60,
                                                 start_seconds=manifest['start_seconds'])
        if current['frame_sha256'] != manifest['frame_sha256']:
            raise AssertionError('source corpus changed')
        result = run(frames, current, Config(feedback_ms=10, decode_ms=20))
        cases.append({'name': name, 'kind': 'assumed_decode20ms', 'manifest': current, 'result': result})
    frames, manifest = make_stress_frames()
    manifest['active_rects'] = [x['active_rect'] for x in manifest['frames']]
    manifest['frame_sha256'] = [x['sha256'] for x in manifest['frames']]
    for adaptive in (False, True):
        cfg = Config(feedback_ms=10, cap_backoff_scales=(8,16,32) if adaptive else ())
        result = run(frames, manifest, cfg)
        cases.append({'name': 'synthetic_cut_noise_recovery', 'kind': 'adaptive_cap' if adaptive else 'fixed_cap',
                      'manifest': manifest, 'result': result})
    if hashes != {str(p): digest(p) for p in paths}:
        raise RuntimeError('sources changed')
    report = {'evidence': 'Actual selected-frame re-encoding with assumed timing; synthetic stress is not gameplay',
              'source_sha256': hashes, 'baseline_sha256': digest(HERE/'results.json'), 'scenarios': cases}
    (HERE/'extra-results.json').write_text(json.dumps(report, indent=2)+'\n')
    for case in cases:
        r = case['result']
        print(case['name'], case['kind'], 'steady', r['steady_fps'], 'eventual', r['presented_after_drain'],
              'drops', r['drop_counts'], 'quality', r['pooled_presented_active_psnr_db'],
              'scales', r['presented_scale_histogram'], 'last', r['front_at_horizon'])


if __name__ == '__main__':
    main()
