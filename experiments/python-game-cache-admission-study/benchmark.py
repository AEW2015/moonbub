#!/usr/bin/env python3
"""Actual paired normal/cached rate admission at unchanged 720x480 syntax."""
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import sys
import time

import numpy as np
import cache_admission as ca

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'python-codec-study'))
import corpus


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(a):
    return hashlib.sha256(a.tobytes()).hexdigest()


def stats(values):
    return dict(n=len(values), mean=float(np.mean(values)), p50=float(np.percentile(values, 50)),
                p95=float(np.percentile(values, 95)), max=max(values))


def run_case(name, cohort, frames, manifest, keys):
    config = ca.normal.Config()
    baseline, cached = ca.normal.Controller(config=config), ca.Controller(config=config)
    rx = ca.gm.Receiver()
    rows = []
    for i, rgb in enumerate(frames):
        before = dict(last_issued=cached.encoder.last_issued, generation=cached.encoder._generation,
                      anchor_id=cached.encoder.anchor_id, pending_ids=sorted(cached.encoder.pending))
        outputs, wall, calls = {}, {}, {}
        order = (('baseline', baseline), ('cached', cached)) if i % 2 == 0 else (('cached', cached), ('baseline', baseline))
        for label, ctrl in order:
            n = ctrl.encoder.forward_calls
            start = time.perf_counter_ns()
            outputs[label] = ctrl.prepare(rgb, i, force_key=i in keys)
            wall[label] = (time.perf_counter_ns() - start) / 1e6
            calls[label] = ctrl.encoder.forward_calls - n
        a, b = outputs['baseline'], outputs['cached']
        assert a.packet == b.packet and a.selected == b.selected
        assert [x['bytes'] for x in a.attempts] == [x['bytes'] for x in b.attempts]
        assert (baseline.encoder.last_issued, baseline.encoder._generation, baseline.encoder.anchor_id,
                sorted(baseline.encoder.pending)) == (cached.encoder.last_issued, cached.encoder._generation,
                cached.encoder.anchor_id, sorted(cached.encoder.pending))
        after = dict(last_issued=cached.encoder.last_issued, generation=cached.encoder._generation,
                     anchor_id=cached.encoder.anchor_id, pending_ids=sorted(cached.encoder.pending))
        actual_hash = reference = packet_hash = None
        key = bool(i in keys or before['anchor_id'] is None)
        if b.accepted:
            actual, info = rx.receive(b.packet)
            actual_hash = digest(actual)
            assert actual_hash == baseline.encoder.expected_hash(i) == cached.encoder.expected_hash(i)
            reference, key = info['reference_id'], info['key']
            packet_hash = hashlib.sha256(b.packet).hexdigest()
            assert baseline.encoder.ack(i, epoch=1) and cached.encoder.ack(i, epoch=1)
            for x, y in zip(baseline.encoder._anchor, cached.encoder._anchor):
                np.testing.assert_array_equal(x, y)
        else:
            assert before == after
        rows.append(dict(id=i, source_rgb_sha256=manifest['frame_sha256'][i], width=rgb.shape[1], height=rgb.shape[0],
                         key=key, accepted=b.accepted, selected=b.selected,
                         packet_bytes=len(b.packet) if b.accepted else None,
                         baseline_packet_sha256=packet_hash, cached_packet_sha256=packet_hash,
                         decoded_rgb_sha256=actual_hash, reference_id=reference,
                         before_prepare_state=before, after_prepare_state=after,
                         baseline_attempts=a.attempts, cached_attempts=b.attempts,
                         baseline_prepare_wall_ms=wall['baseline'], cached_prepare_wall_ms=wall['cached'],
                         baseline_service_ms=a.service_ms, cached_service_ms=b.service_ms,
                         baseline_forward_calls=calls['baseline'], cached_forward_calls=calls['cached'],
                         cache=cached.last_cache.copy(), whole_packets_equal=True))
    summary = {}
    for group in ('all', 'admitted', 'rejected', 'cache_hit', 'cache_miss'):
        chosen = [r for r in rows if group == 'all'
                  or (group in ('admitted', 'rejected') and r['accepted'] == (group == 'admitted'))
                  or (group in ('cache_hit', 'cache_miss') and bool(r['cache']['hits']) == (group == 'cache_hit'))]
        if not chosen:
            continue
        summary[group] = dict(rows=len(chosen),
                             baseline_prepare_wall_ms=stats([r['baseline_prepare_wall_ms'] for r in chosen]),
                             cached_prepare_wall_ms=stats([r['cached_prepare_wall_ms'] for r in chosen]),
                             baseline_forward_calls=sum(r['baseline_forward_calls'] for r in chosen),
                             cached_forward_calls=sum(r['cached_forward_calls'] for r in chosen))
    return dict(name=name, cohort=cohort, manifest=manifest, keys=sorted(keys), frame_cap=config.frame_cap,
                rows=rows, summary=summary, distinct_source_rgb_images=len(set(manifest['frame_sha256'])),
                max_cache_bytes=max(r['cache']['bytes'] for r in rows))


def main():
    modules = [ca.gm, ca.normal, ca.gm.roi, ca.gm.ft, ca.gm.mt, ca.gm.token_coeff,
               ca.gm.word_coeff, ca.gm.word_coeff.frozen_codec, corpus]
    paths = [HERE / 'cache_admission.py', HERE / 'benchmark.py', HERE / 'test_cache_admission.py'] + [Path(m.__file__) for m in modules]
    pins = {str(p): sha(p) for p in paths}
    media = Path(os.environ.get('GAMEBUB_MEDIA_DIR', str(HERE.parents[3] / 'media')))
    inputs = []
    for cohort, start, count in (('native_temporal', 1, 60), ('heldout_key', 4, 8)):
        for clip in ('mass-effect-combat', 'mass-effect-2600'):
            frames, manifest = corpus.load_video(media / (clip + '.mp4'), max_frames=count, start_seconds=start)
            keys = set(range(count)) if cohort == 'heldout_key' else {0, 30}
            inputs.append((clip + '-' + cohort, cohort, frames, manifest, keys))
    rng = np.random.default_rng(1309)
    for name in ('flat-repeat', 'alternating-unique', 'noise-repeated-reject'):
        if name == 'flat-repeat':
            frames = [np.full((480, 720, 3), [40, 60, 80], np.uint8) for _ in range(12)]
        elif name == 'alternating-unique':
            frames = [np.full((480, 720, 3), [40 + i % 2, 60, 80], np.uint8) for i in range(12)]
        else:
            noise = [rng.integers(0, 256, (480, 720, 3), np.uint8) for _ in range(3)]
            frames = [np.full((480, 720, 3), [40, 60, 80], np.uint8)] + [noise[(i - 1) // 3].copy() for i in range(1, 10)] + [np.full((480, 720, 3), [40, 60, 80], np.uint8)] * 2
        manifest = dict(source='synthetic:' + name, synthetic=True, frame_count=len(frames),
                        frame_sha256=[digest(a) for a in frames], active_rects=[(0, 0, 720, 480)] * len(frames))
        inputs.append((name, 'synthetic', frames, manifest, {0}))
    cases = []
    for args in inputs:
        case = run_case(*args)
        cases.append(case)
        s = case['summary']['all']
        print(case['name'], 'hits', sum(r['cache']['hits'] > 0 for r in case['rows']),
              'rejects', sum(not r['accepted'] for r in case['rows']),
              'baseline_ms', s['baseline_prepare_wall_ms']['mean'],
              'cache_ms', s['cached_prepare_wall_ms']['mean'], flush=True)
    assert pins == {str(p): sha(p) for p in paths}
    result = dict(evidence='Actual bounded candidate/commit exact-source cache; same whole GM01 bytes, normal pre-commit cap admission.',
                  source_sha256=pins,
                  versions=dict(python=platform.python_version(), **{x: importlib.metadata.version(x) for x in ('numpy', 'Pillow', 'av')}),
                  cases=cases, paired_source_ids=sum(len(c['rows']) for c in cases),
                  admitted_pairs=sum(r['accepted'] for c in cases for r in c['rows']),
                  rejected_pairs=sum(not r['accepted'] for c in cases for r in c['rows']),
                  timing_scope='Alternating AB/BA whole prepare wall includes maps, exact lookup, source/payload copy, header/CRC, all fresh attempts and commit. Source capture/BOX resize and independent oracle/hash/decode outside these stage clocks. Host load uncontrolled.',
                  memory_scope='One PC immutable RGB source plus at most two immutable map/header/P-payload entries; no raw transform or coefficient arrays retained in cache. Existing pending packets, fresh transform/decoder workspaces, Python object/weakset overhead extra.',
                  cohort_scope='Native two60-ID windows are related precompressed25/29.88fps clips, not native30distinctfps. Heldout16allkeys and synthetic36 are separate controls. Rejected P packets may populate exact cache, but never consume credit or advance codec state.',
                  protocol_scope='Frozen GM01 full bytes; no new skip syntax, receiver mode or P reference. Cache preview is separately registered, generation/credit/reference-checked and commits only after complete cap fit. No wire rate savings.',
                  deployment_scope='Python only; parent finite integration is separate evidence. No installed sender, firmware, RTL, physical memory or sustained hardware30fps proof.')
    (HERE / 'results.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')


if __name__ == '__main__':
    main()
