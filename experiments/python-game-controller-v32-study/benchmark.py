#!/usr/bin/env python3
"""Rotated causal full-resolution v32 trials; every losing encode is paid."""
from pathlib import Path
import hashlib
import importlib.util
import json
import math
import sys
import time
import zlib
import numpy as np
from controller import select_tier

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    sys.modules[name] = obj
    spec.loader.exec_module(obj)
    return obj


# Existing benchmark imports local 'model'/'protocol': resolve explicitly once.
sys.path.insert(0, str(HERE.parent / 'python-game-runtime-v28-study'))
b = module('controller32_helpers', HERE.parent / 'python-game-runtime-v28-study/benchmark.py')
sys.path.pop(0)
m, p, n = b.m, b.p, b.n
adaptive = module('controller32_adaptive', HERE.parent / 'python-game-adaptive-v29-study/model.py')
band = module('controller32_band', HERE.parent / 'python-game-band-v30-study/model.py')
shrink = module('controller32_shrink', HERE.parent / 'python-game-shrink-v32-study/model.py')
POLICIES = ('band_control', 'shrink_strict', 'shrink_budget')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pins():
    inherited = b.load(HERE.parent / 'python-game-controller-v30-study/results.json')['source_sha256']
    paths = {ROOT / k for k in inherited}
    paths |= {HERE.parent / 'python-game-controller-v30-study/results.json', HERE / 'benchmark.py', HERE / 'controller.py',
              HERE.parent / 'python-game-band-v30-study/model.py', HERE.parent / 'python-game-shrink-v32-study/model.py'}
    return {v.relative_to(ROOT).as_posix(): sha(v) for v in sorted(paths)}


def raw(desc, folder=HERE):
    path = Path(desc['path'])
    assert not path.is_absolute() and '..' not in path.parts
    assert 0 < desc['raw_bytes'] <= 1000000
    packed = (folder / path).read_bytes()
    assert hashlib.sha256(packed).hexdigest() == desc['stored_sha256']
    dc = zlib.decompressobj()
    out = dc.decompress(packed, desc['raw_bytes'] + 1)
    assert dc.eof and not dc.unused_data and not dc.unconsumed_tail
    assert len(out) == desc['raw_bytes'] and hashlib.sha256(out).hexdigest() == desc['raw_sha256']
    return out


def blob(data):
    packed = zlib.compress(data, 9)
    path = 'objects/' + hashlib.sha256(packed).hexdigest() + '.zlib'
    (HERE / 'objects').mkdir(exist_ok=True)
    (HERE / path).write_bytes(packed)
    return dict(path=path, raw_bytes=len(data), raw_sha256=hashlib.sha256(data).hexdigest(),
                stored_sha256=hashlib.sha256(packed).hexdigest())


def elapsed(fn):
    start = time.perf_counter_ns()
    result = fn()
    return result, (time.perf_counter_ns() - start) / 1e6


def attempt(prepared, q, kind, bg, hud, original, ref, refid, slot, policy):
    encode = (lambda: band.encode_with(m, prepared, q, rdo_lambda=1, policy='band_strict')) if kind.endswith('_band') else (lambda: m.encode_prepared(prepared, q, rdo_lambda=1))
    if kind.endswith('_shrink'):
        encode = lambda: shrink.encode_with(m, prepared, q, rdo_lambda=1, policy=policy)
    (base, expected, work), encode_ms = elapsed(encode)
    (decoded, meta), debug_ms = elapsed(lambda: m.decode(base, ref, expected_epoch=25,
                                      expected_reference_id=None if prepared.key else refid))
    for a, c in zip(decoded, expected):
        np.testing.assert_array_equal(a, c)
    start = time.perf_counter_ns()
    bare = m.C.corpus.rgb565(m.ft.planes_to_rgb(expected))
    hybrid = n.overlay(bare, tuple(original[y:y+h, x:x+w] for x, y, w, h in n.RECTS))
    metric = n.metric(original, hybrid)
    quality_ms = (time.perf_counter_ns() - start) / 1e6
    start = time.perf_counter_ns()
    flags = p.PUBLISH | (p.KEY if prepared.key else 0)
    pair = p.seal(p.PAIR.pack(b'CP27', 1, flags, 25, prepared.frame_id,
                             p.NO_SLOT if prepared.key else slot, 0 if prepared.key else 1-slot,
                             len(base), len(hud), p.digest(base), p.digest(hud)) + base + hud)
    if len(pair) <= 49152:
        p.parse_pair(pair)
    else:
        try:
            p.parse_pair(pair)
        except ValueError:
            pass
        else:
            raise AssertionError('overcap pair parsed')
    bind_ms = (time.perf_counter_ns() - start) / 1e6
    info = dict(kind=kind, background=bg, base_packet=blob(base), packet=blob(pair),
                base_bytes=len(base), complete_bytes=len(pair), cap_fit=len(pair) <= 49152,
                work=work, encode_ms=encode_ms, offline_debug_decode_ms=debug_ms,
                quality_ms=quality_ms, bind_ms=bind_ms, hybrid=metric,
                hybrid_rgb565_sha256=n.digest(hybrid), reconstructed_tag=meta['reconstructed_tag'].hex())
    return info, pair, expected, hybrid


def summarize(rows):
    count = len(rows)
    total = sum(r['body_bytes'] for r in rows)
    sse = sum(r['hybrid']['active_squared_error'] for r in rows)
    samples = sum(r['hybrid']['active_channel_samples'] for r in rows)
    return dict(frames=count, complete_bytes=total, coded_body_Mbps_at30=total * 240 / count / 1e6,
                base_bytes=sum(r['base_bytes'] for r in rows), hud_bytes=sum(r['hud_bytes'] for r in rows),
                binding_bytes=60 * count, maximum_complete_bytes=max(r['body_bytes'] for r in rows),
                cap_fit_frames=sum(r['body_bytes'] <= 49152 for r in rows),
                active_squared_error=sse, active_channel_samples=samples, active_mse=sse / samples,
                active_psnr_db=10 * math.log10(65025 / (sse / samples)),
                hud_word_errors=sum(r['hybrid']['hud_word_errors'] for r in rows), exact_hud_words=count * 21120,
                paid_candidate_encodes=sum(len(r['attempts']) for r in rows),
                mean_paid_base_encode_ms=sum(r['paid_base_encode_ms'] for r in rows) / count,
                mean_base_policy_service_ms=sum(r['base_policy_service_ms'] for r in rows) / count,
                mean_receiver_ms=sum(r['receive_ms'] for r in rows) / count,
                sad_sample_operations=sum(a['search']['sad_sample_operations'] for r in rows for a in r['analyses'].values()),
                search_reference_fetches=sum(a['search'].get('reference_sample_fetches', 0) for r in rows for a in r['analyses'].values()),
                quiet_blocks=sum(a['search'].get('quiet_blocks', 0) for r in rows for a in r['analyses'].values()),
                active_blocks=sum(a['search'].get('active_blocks', 0) for r in rows for a in r['analyses'].values()),
                selected_alternative_planes=sum(a['work'].get('selected_alternative_planes', 0) for r in rows for a in r['attempts'] if a['selected']),
                selected_band_frames=sum(r['selected_kind'].endswith('_band') for r in rows),
                selected_shrink_frames=sum(r['selected_kind'].endswith('_shrink') for r in rows),
                selected_changed_blocks=sum(a['work'].get('changed_blocks', 0) for r in rows for a in r['attempts'] if a['selected']),
                selected_removed_coefficients=sum(a['work'].get('removed_coefficients', 0) for r in rows for a in r['attempts'] if a['selected']),
                same_history_shadow_complete_bytes=sum(r['baseline_complete_bytes'] for r in rows),
                same_history_shadow_sse=sum(r['baseline_source_sse'] for r in rows),
                ec26_size_counter_calls=sum(a['work'].get('ec26_size_counter_calls', 0) for r in rows for a in r['attempts']),
                coarse_fallback_frames=[r['id'] for r in rows if r['selected_background'] == 32])


def frame(srcrow, prior, policy, state):
    fid = srcrow['id']
    key = fid % 24 == 0
    if key:
        state.update(ref=None, refid=m.NO_REF, slot=0)
    ref, refid, slot = state['ref'], state['refid'], state['slot']
    source, original = n.source(srcrow), n.original(srcrow)
    hud = raw(prior['hud_packet'], ROOT / prior['hud_packet']['directory'])
    kinds = ('zero',) if key else ('zero', 'half32')
    prepared, analyses = {}, {}
    for kind in kinds:
        kwargs = dict(epoch=25, frame_id=fid, reference_id=refid, block_size=32,
                      motion_mode='zero' if kind == 'zero' else 'block', motion_precision='half', penalty=0)
        prepared[kind] = adaptive.analyze_with(m.base, source, ref, search_policy='adaptive_zero2', **kwargs)
        analyses[kind] = prepared[kind].work
    attempts, selected = [], None
    for bg in (16, 32):
        q = m.roi.declared_map(720, 480, n.ROIS, 8, bg)
        group = [attempt(prepared[kind], q, kind, bg, hud, original, ref, refid, slot, policy) for kind in kinds]
        group += [attempt(prepared[kind], q, kind + '_band', bg, hud, original, ref, refid, slot, policy) for kind in kinds]
        if policy != 'band_control':
            group += [attempt(prepared[kind], q, kind + '_shrink', bg, hud, original, ref, refid, slot, policy) for kind in kinds]
        attempts += [v[0] for v in group]
        chosen, tier_baseline = select_tier([v[0] for v in group], policy)
        if chosen is not None:
            selected = next(v for v in group if v[0] is chosen)
            break
    assert selected is not None
    info, pair, expected, expected_hybrid = selected
    for a in attempts:
        a['selected'] = a is info
    (decoded, patches, ack), receive_ms = elapsed(lambda: state['rx'].receive(pair))
    ackmeta, ack_ms = elapsed(lambda: p.validate_ack(ack, pair))
    for a, c in zip(decoded, expected):
        np.testing.assert_array_equal(a, c)
    for patch, (x, y, w, h) in zip(patches, n.RECTS):
        np.testing.assert_array_equal(patch['words'], original[y:y+h, x:x+w])
    hybrid = n.overlay(m.C.corpus.rgb565(m.ft.planes_to_rgb(decoded)), tuple(v['words'] for v in patches))
    np.testing.assert_array_equal(hybrid, expected_hybrid)
    paid = sum(v['analysis_wall_ms'] for v in analyses.values()) + sum(a['encode_ms'] for a in attempts)
    service = paid + sum(a['quality_ms'] + a['bind_ms'] for a in attempts)
    row = dict(id=fid, key=key, reference_id=refid, source_slot=p.NO_SLOT if key else slot,
               destination_slot=0 if key else 1-slot, source_common_yuv_sha256=srcrow['common_yuv420_u8_sha256'],
               reference_tag=prepared['zero'].reference_tag.hex(), baseline_kind=tier_baseline['kind'],
               baseline_source_sse=tier_baseline['hybrid']['active_squared_error'], baseline_complete_bytes=tier_baseline['complete_bytes'],
               quality_budget_percent=1 if policy=='shrink_budget' else 0, selected_kind=info['kind'], selected_background=info['background'],
               packet=info['packet'], base_packet=info['base_packet'], body_bytes=len(pair), base_bytes=info['base_bytes'],
               hud_bytes=len(hud), binding_bytes=60, hud_packet=prior['hud_packet'], ack=blob(ack), ack_meta=ackmeta,
               attempts=attempts, analyses=analyses, paid_base_encode_ms=paid, base_policy_service_ms=service,
               receive_ms=receive_ms, ack_ms=ack_ms, hybrid=info['hybrid'], hybrid_rgb565_sha256=n.digest(hybrid),
               reconstructed_tag=info['reconstructed_tag'])
    state.update(ref=decoded, refid=fid, slot=0 if key else 1-slot)
    return row


def main():
    before = pins()
    inputs = b.load(n.V24 / 'results.json')['inputs']
    old = b.load(b.OLD / 'results.json')['cases']
    prior30 = b.load(HERE.parent / 'python-game-controller-v30-study/results.json')['cases']
    cases = []
    for inp in inputs:
        prior = next(c for c in old if c['scene'] == inp['scene'] and c['policy'] == 'unified_causal')
        states = {policy: dict(rx=p.Receiver(epoch=25), ref=None, refid=m.NO_REF, slot=0) for policy in POLICIES}
        rows = {policy: [] for policy in POLICIES}
        for src, previous in zip(inp['rows'], prior['rows']):
            # Rotate policy order while maintaining three separate causal histories.
            offset = src['id'] % len(POLICIES)
            order = POLICIES[offset:] + POLICIES[:offset]
            for policy in order:
                row = frame(src, previous, policy, states[policy])
                rows[policy].append(row)
            if (src['id'] + 1) % 12 == 0:
                print(json.dumps(dict(scene=inp['scene'], frames_per_policy=src['id'] + 1)), flush=True)
        old30 = next(c for c in prior30 if c['scene'] == inp['scene'] and c['policy'] == 'band_strict')
        for row, oldrow in zip(rows['band_control'], old30['rows']):
            assert raw(row['packet']) == raw(oldrow['packet'], HERE.parent / 'python-game-controller-v30-study')
            assert raw(row['ack']) == raw(oldrow['ack'], HERE.parent / 'python-game-controller-v30-study')
            assert row['hybrid'] == oldrow['hybrid']
        for policy in POLICIES:
            item = dict(scene=inp['scene'], policy=policy, rows=rows[policy], summary=summarize(rows[policy]))
            cases.append(item)
            print(json.dumps(dict(scene=inp['scene'], policy=policy, summary=item['summary'])), flush=True)
        assert pins() == before, 'sources changed during benchmark'
        data = dict(schema='gamebub-controller-v32', source_sha256=before, cases=cases,
                    geometry=dict(coded=[720, 480], active=[720, 405], exact_hud_words=21120, complete_cap=49152),
                    physical_30fps_proven=False, unchanged_GM27_wire=True,
                    scope=['Three independently reconstructed causal histories; rotated policy order each frame.',
                           'Shrink admission against v30 band-controller shadow requires actual complete byte saving and current same-history shadow RGB SSE guard (strict0% or budget1%).',
                           'Two 48-frame windows reused from 96 retained 29.88fps images, not a new corpus.',
                           'Base policy time includes all analyses, attempted encodes, quality scoring and binding checks.',
                           'Excludes fixture acquisition/conversion, preencoded HUD generation, debug decode, artifact I/O, network and display.',
                           '30fps byte rates are nominal projections, not measured native endpoint throughput.'])
        (HERE / 'results.json').write_text(json.dumps(data, separators=(',', ':'), allow_nan=False) + '\n')


if __name__ == '__main__':
    main()
