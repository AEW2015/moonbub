#!/usr/bin/env python3
"""Actual lossless patch candidates on fixed ACKed source-word histories."""
from pathlib import Path
import hashlib
import importlib.util
import json
import platform
import sys
import time
import zlib
import numpy as np
import model as m

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OLD = HERE.parent / 'python-game-hud-cache-study'
spec = importlib.util.spec_from_file_location('hud25_old_cache', OLD / 'model.py')
cache = importlib.util.module_from_spec(spec); sys.modules[spec.name] = cache; spec.loader.exec_module(cache)
RECTS = cache.RECTANGLES


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path): return json.loads(Path(path).read_text())
def measured(fn):
    t = time.perf_counter_ns(); out = fn(); return out, (time.perf_counter_ns() - t) / 1e6


def pins():
    paths = {ROOT / p for p in load(OLD / 'results.json')['source_sha256']}
    paths |= {OLD / 'results.json', HERE.parent / 'python-game-gap-span-study/model.py',
              HERE.parent / 'python-game-gap-span-study/results.json'}
    paths |= set((OLD / 'objects').glob('*'))
    paths |= {HERE / n for n in ('model.py', 'benchmark.py', 'verify.py', 'test_model.py', 'README.md', 'SCHEMA.md')}
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(paths)}


def raw(desc, folder=OLD):
    path = Path(desc['path']); assert not path.is_absolute() and '..' not in path.parts
    data = (folder / path).read_bytes(); assert hashlib.sha256(data).hexdigest() == desc['stored_sha256']
    dec = zlib.decompressobj(); out = dec.decompress(data, desc['raw_bytes'] + 1)
    assert dec.eof and not dec.unused_data and not dec.unconsumed_tail and len(out) == desc['raw_bytes']
    assert hashlib.sha256(out).hexdigest() == desc['raw_sha256']; return out


def blob(data):
    stored = zlib.compress(data, 9); path = 'objects/' + hashlib.sha256(stored).hexdigest() + '.zlib'
    (HERE / 'objects').mkdir(exist_ok=True)
    (HERE / path).write_bytes(stored)
    return dict(path=path, raw_bytes=len(data), raw_sha256=hashlib.sha256(data).hexdigest(), stored_sha256=hashlib.sha256(stored).hexdigest())


def arrays(row):
    return tuple(np.frombuffer(raw(d), dtype='<u2').reshape(rect[3], rect[2]) for rect, d in zip(RECTS, row['original_patches']))


def canvas(patches):
    rgb = np.zeros((480, 720, 3), np.uint8)
    for (x, y, w, h), words in zip(RECTS, patches): rgb[y:y+h, x:x+w] = cache.legacy.codec.corpus.expand565(words)
    return rgb


def run_case(case, *, export=True):
    selector = cache.legacy.ui.PatchSelector(rectangles=RECTS)
    confirmed = None
    rows, goldens = [], []
    for source in case['rows']:
        current = arrays(source)
        full, legacy_ms = measured(lambda: selector.select(canvas(current), 98304))
        assert len(full.patches) == 4
        details, decoded = [], []
        for i, (words, legacy) in enumerate(zip(current, full.patches)):
            reference = None if confirmed is None else confirmed[i]
            old, old_ms = measured(lambda: m.old.encode(words, reference))
            (nomotion, noinfo), nomotion_ms = measured(lambda: m.encode_with_info(words, reference, motion=False))
            (packet, info), full_ms = measured(lambda: m.encode_with_info(words, reference))
            assert len(packet) <= len(nomotion) <= len(old)
            selected = legacy if len(legacy) <= len(packet) else packet
            kind = 'legacy' if selected is legacy else info['mode']
            def receive():
                return cache.legacy.ui.validate_patches((selected,), 720, 480)[0]['words'] if kind == 'legacy' else m.decode(selected, reference)
            output, decode_ms = measured(receive)
            np.testing.assert_array_equal(output, words)
            decoded.append(output)
            detail = dict(index=i, shape=list(words.shape), legacy_bytes=len(legacy), hd22_bytes=len(old),
                          no_motion_bytes=len(nomotion), hd25_bytes=len(packet), selected_bytes=len(selected),
                          old_selected_bytes=min(len(legacy), len(old)), no_motion_selected_bytes=min(len(legacy), len(nomotion)),
                          selected_kind=kind, hd25_mode=info['mode'], no_motion_mode=noinfo['mode'],
                          old_ms=old_ms, no_motion_ms=nomotion_ms, full_ms=full_ms, decode_ms=decode_ms,
                          full_info=info, packet_sha256=hashlib.sha256(packet).hexdigest())
            details.append(detail)
            if export and (source['frame'] in (0, 1, 24) and i == 0 or (info['mode'] in ('global_motion', 'tile_motion') and not any(v['meta']['mode_name'] == info['mode'] for v in goldens))):
                goldens.append(dict(case=case['name'], frame=source['frame'], patch=i, shape=list(words.shape),
                                    current=blob(words.astype('<u2').tobytes()), reference=None if reference is None else blob(reference.astype('<u2').tobytes()),
                                    packet=blob(packet), meta=m.inspect(packet, reference)))
        rows.append(dict(frame=source['frame'], legacy_ms=legacy_ms, patches=details,
                         old_hud_bytes=83 + sum(p['old_selected_bytes'] for p in details),
                         no_motion_hud_bytes=83 + sum(p['no_motion_selected_bytes'] for p in details),
                         new_hud_bytes=83 + sum(p['selected_bytes'] for p in details),
                         exact_words=sum(p.size for p in decoded),
                         paid_old_encode_ms=legacy_ms + sum(p['old_ms'] for p in details),
                         paid_no_motion_encode_ms=legacy_ms + sum(p['no_motion_ms'] for p in details),
                         paid_new_encode_ms=legacy_ms + sum(p['full_ms'] for p in details)))
        confirmed = tuple(p.copy() for p in decoded)
    summary = summarize(case['name'], rows)
    return dict(name=case['name'], rows=rows, summary=summary), goldens


def summarize(name, rows):
    return dict(name=name, updates=len(rows), patches=4*len(rows),
                old_hud_bytes=sum(r['old_hud_bytes'] for r in rows),
                no_motion_hud_bytes=sum(r['no_motion_hud_bytes'] for r in rows),
                new_hud_bytes=sum(r['new_hud_bytes'] for r in rows),
                old_mean_encode_ms=sum(r['paid_old_encode_ms'] for r in rows)/len(rows),
                no_motion_mean_encode_ms=sum(r['paid_no_motion_encode_ms'] for r in rows)/len(rows),
                new_mean_encode_ms=sum(r['paid_new_encode_ms'] for r in rows)/len(rows),
                exact_words=sum(r['exact_words'] for r in rows),
                selected_modes={mode: sum(p['selected_kind'] == mode for r in rows for p in r['patches']) for mode in ('legacy', *m.NAMES)},
                raw_candidate_modes={mode: sum(p['hd25_mode'] == mode for r in rows for p in r['patches']) for mode in m.NAMES},
                logical_search_vectors=sum(p['full_info']['motion_search_vectors'] for r in rows for p in r['patches']),
                logical_search_compared_words=sum(p['full_info']['motion_compared_words'] for r in rows for p in r['patches']))


def controls():
    rng = np.random.default_rng(2505)
    ref = rng.integers(0, 65536, (24, 160), np.uint16)
    result = []
    for name in ('translation', 'scene_change'):
        rows, previous = [], None
        for i in range(12):
            cur = m.predict(ref, i % 4, (i // 4) % 3) if name == 'translation' else rng.integers(0, 65536, ref.shape, np.uint16)
            packet, info = m.encode_with_info(cur, previous)
            out = m.decode(packet, previous); np.testing.assert_array_equal(cur, out)
            rows.append(dict(id=i, bytes=len(packet), mode=info['mode'], packet=blob(packet),
                             current=blob(cur.astype('<u2').tobytes()), reference=None if previous is None else blob(previous.astype('<u2').tobytes()), shape=list(cur.shape)))
            previous = out
        result.append(dict(name=name, rows=rows, complete_bytes=sum(x['bytes'] for x in rows)))
    return result


def main():
    before = pins()
    old = load(OLD / 'results.json')
    cases, goldens = [], []
    for case in old['cases']:
        result, vectors = run_case(case)
        cases.append(result); goldens.extend(vectors)
        print(json.dumps(result['summary']), flush=True)
    controls_ = controls()
    assert before == pins(), 'source changed during campaign'
    data = dict(schema='gamebub-hud-motion-v25', source_sha256=before, cases=cases, goldens=goldens, controls=controls_,
                counts=dict(native_updates=96, reused_synthetic_updates=36, source_patch_decisions=528, extra_control_patches=24,
                            exact_words=sum(c['summary']['exact_words'] for c in cases)),
                versions=dict(python=platform.python_version(), numpy=np.__version__),
                scope=[
                    'Exact fixed source/cache histories; legacy full+HD22+HD25actualbytes compete, every winner independentlydecoded.',
                    'HD25 full pays all its byte-plane/component/intra/global/tiled candidate work. Separate no-motion rerun is an ablation, not charged twice to the full policy.',
                    '83-byte future HUD wrapper is an accounting projection until joint dispatch integration. No silent YUV/base quality change.',
                    'Motion search uses all 81 candidate component Exp-Golomb-length proxy scores to rank 3 global vectors and select each 16x8 tile; actual residual bytes choose the overall winner, not a claimed globally optimal MV rate search.',
                    'Logical search/refetch counts and Python clocks are not native DSP/FPGA/RF/QSPI throughput, memory fit, frameclock orphysical30fps proof.'])
    (HERE/'results.json').write_text(json.dumps(data, separators=(',', ':'), allow_nan=False)+'\n')


if __name__ == '__main__': main()
