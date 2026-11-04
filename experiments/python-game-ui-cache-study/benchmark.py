#!/usr/bin/env python3
"""Paired frozen/cached UI selection; common actual GM01 base, full720x480."""
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import sys
import time

import numpy as np
import ui_cache as u

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
    cfg = u.hybrid.Config()
    cache = u.PatchCache()
    enc = u.hybrid.gm.Encoder()
    receivers = {label: u.hybrid.Decoder() for label in ('baseline', 'cached')}
    mapped = u.hybrid.gm.roi.declared_map(720, 480, u.hybrid.BROAD, 8, 16)
    rows = []
    for i, rgb in enumerate(frames):
        base = enc.prepare(rgb, i, scale_map=mapped, force_key=i in keys)
        decisions, wall = {}, {}
        order = ('baseline', 'cached') if i % 2 == 0 else ('cached', 'baseline')
        for label in order:
            began = time.perf_counter_ns()
            decisions[label] = (u.hybrid.select_frame(base, rgb, cfg) if label == 'baseline'
                                else u.select(base, rgb, cache, cfg))
            wall[label] = (time.perf_counter_ns() - began) / 1e6
        a, b = decisions['baseline'], decisions['cached']
        assert a.packet == b.packet and a.selected_pixels == b.selected_pixels
        assert [(r['patch_bytes'], r['selected_in_output']) for r in a.attempts] == [(r['patch_bytes'], r['selected_in_output']) for r in b.attempts]
        output_hash = None
        exact_errors = 0
        if b.accepted:
            decoded = {label: receivers[label].receive(decisions[label].packet)[0] for label in ('baseline', 'cached')}
            np.testing.assert_array_equal(decoded['baseline'], decoded['cached'])
            original, actual = corpus.rgb565(rgb), corpus.rgb565(decoded['cached'])
            for selected in b.selected:
                x, y, w, h = selected['rect']
                exact_errors += int(np.count_nonzero(actual[y:y+h, x:x+w] != original[y:y+h, x:x+w]))
            assert exact_errors == 0
            output_hash = digest(decoded['cached'])
        rows.append(dict(id=i, source_rgb_sha256=manifest['frame_sha256'][i], width=720, height=480,
                         whole_source_changed=(i > 0 and manifest['frame_sha256'][i] != manifest['frame_sha256'][i-1]),
                         base_bytes=len(base), base_sha256=hashlib.sha256(base).hexdigest(), accepted=b.accepted,
                         packet_bytes=len(b.packet) if b.accepted else None, format=b.format,
                         baseline_packet_sha256=hashlib.sha256(a.packet).hexdigest() if a.accepted else None,
                         cached_packet_sha256=hashlib.sha256(b.packet).hexdigest() if b.accepted else None,
                         decoded_rgb_sha256=output_hash, selected_rgb565_mismatches=exact_errors,
                         selected_pixels=b.selected_pixels, selected=b.selected,
                         baseline_attempts=a.attempts, cached_attempts=b.attempts,
                         baseline_wall_ms=wall['baseline'], cached_wall_ms=wall['cached'],
                         baseline_service_ms=a.service_ms, cached_service_ms=b.service_ms,
                         cache_entries=len(cache._entries), persistent_cache_bytes=cache.persistent_bytes()))
        assert enc.ack(i, epoch=1)
    return dict(name=name, cohort=cohort, manifest=manifest, rows=rows, keys=sorted(keys),
                frame_cap=cfg.frame_cap, rectangles=cfg.rectangles, patch_policy=cfg.patch_policy,
                max_entries=cache.max_entries, distinct_source_rgb_images=len(set(manifest['frame_sha256'])),
                hit_attempts=sum(a['candidate_details']['cache_hit'] for r in rows for a in r['cached_attempts']),
                hits_on_changed_whole_source=sum(a['candidate_details']['cache_hit'] for r in rows if r['whole_source_changed'] for a in r['cached_attempts']),
                max_persistent_cache_bytes=max(r['persistent_cache_bytes'] for r in rows),
                summary={label: stats([r[label + '_wall_ms'] for r in rows]) for label in ('baseline', 'cached')})


def main():
    modules = [u.hybrid, u.hybrid.row, u.hybrid.hp, u.hybrid.gm, corpus, u.hybrid.gm.ft,
               u.hybrid.gm.roi, u.hybrid.gm.mt, u.hybrid.gm.token_coeff, u.hybrid.gm.word_coeff,
               u.hybrid.gm.word_coeff.frozen_codec]
    paths = [HERE / 'ui_cache.py', HERE / 'benchmark.py', HERE / 'test_ui_cache.py'] + [Path(m.__file__) for m in modules]
    pins = {str(p): sha(p) for p in paths}
    media = Path(os.environ.get('GAMEBUB_MEDIA_DIR', str(HERE.parents[3] / 'media')))
    inputs = []
    for cohort, start, count in (('native_temporal', 1, 60), ('heldout_key', 4, 8)):
        for clip in ('mass-effect-combat', 'mass-effect-2600'):
            frames, manifest = corpus.load_video(media / (clip + '.mp4'), max_frames=count, start_seconds=start)
            inputs.append((clip + '-' + cohort, cohort, frames, manifest,
                           set(range(count)) if cohort == 'heldout_key' else {0, 30}))
    yy, xx = np.indices((480, 720))
    for changing in (False, True):
        frames = []
        for i in range(12):
            rgb = np.stack(((xx + i * 5) % 256, (yy + i * 7) % 256, ((xx + yy) // 3 + i * 11) % 256), axis=2).astype(np.uint8)
            for index, (x, y, w, h) in enumerate(u.hybrid.COMPACT):
                ly, lx = np.indices((h, w))
                mask = ((lx // 4 + ly // 4) % 2).astype(bool)
                dark = [16 + (i * 8 if changing else 0), 32, 48]
                bright = [240, 224 - (i * 8 if changing else 0), 208]
                rgb[y:y+h, x:x+w] = np.where(mask[..., None], bright, dark)
            frames.append(rgb)
        name = 'moving-background-' + ('changing-ui' if changing else 'static-ui')
        manifest = dict(source='synthetic:' + name, synthetic=True, frame_count=len(frames),
                        frame_sha256=[digest(a) for a in frames], active_rects=[(0, 0, 720, 480)] * len(frames))
        inputs.append((name, 'synthetic', frames, manifest, {0}))
    cases = []
    for args in inputs:
        case = run_case(*args)
        cases.append(case)
        print(case['name'], 'hits', case['hit_attempts'], 'changed-source-hits', case['hits_on_changed_whole_source'],
              'selector_ms', case['summary']['baseline']['mean'], '->', case['summary']['cached']['mean'], flush=True)
    assert pins == {str(p): sha(p) for p in paths}
    result = dict(evidence='Bounded exact RGB565 region payload cache through unchanged HP01/HR01 selection and validation.',
                  source_sha256=pins, versions=dict(python=platform.python_version(), **{x: importlib.metadata.version(x) for x in ('numpy', 'Pillow', 'av')}),
                  cases=cases, paired_source_ids=sum(len(c['rows']) for c in cases),
                  timing_scope='Alternating AB/BA whole selector wall includes current word conversion, equality lookup, copies/metadata, actual miss encodes, full patch decoding validation, cap checks and HG assembly. Common GM preparation, source capture/resize and independent output/oracle verification excluded. Host load uncontrolled.',
                  memory_scope='At most4 PC entries of exact RGB565 source rectangle plus immutable full HP01/HR01 bytes and historical metadata. Persistent byte counts exclude object/metadata overhead and transient words/replaced old+new entries. Not peak target memory proof.',
                  cohort_scope='Native120IDs are related precompressed25/29.88fps with repeats, not live30distinctfps. Heldout16keys and synthetic24 controls separate. Configured rectangles are not verified true gameHUDs.',
                  protocol_scope='Same full GM01/HG01 bytes and selected exact RGB565 words. Cache is only host work reuse; receiver still fully validates/decodes payloads, full packets still sent. No rate savings or change in immutable YUV reference.',
                  integration_scope='Standalone selector campaign only. This UI cache is NOT included in parent finite execution results. No native sender/firmware/RTL, physicalSDRAM or hardware30fps claim.')
    (HERE / 'results.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')


if __name__ == '__main__':
    main()
