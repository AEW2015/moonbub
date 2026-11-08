#!/usr/bin/env python3
"""Fixed-policy reconstructed-reference GM25 experiments on retained v24 inputs.

Source acquisition/conversion is retained, not timed again. This is an offline
R/D campaign; a later CP25 replay checks admission and actual modeled ACKs.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import math
import platform
import sys
import time
import zlib
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
V24 = HERE.parent / 'python-game-standard-v24-study'


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


b = module('native25_base', HERE.parent / 'python-game-base-motion-v25-study/model.py')
RECTS = ((22, 54, 160, 24), (22, 82, 160, 24), (168, 360, 320, 24), (168, 390, 240, 24))
ROIS = ((16, 48, 192, 80), (160, 352, 400, 80))
PROFILES = {
    'zero_period8': dict(motion='zero', block=16, period=8, bg=16, roi=8, lam=0, penalty=0),
    'zero_period1': dict(motion='zero', block=16, period=1, bg=16, roi=8, lam=0, penalty=0),
    'block16_period1': dict(motion='block', block=16, period=1, bg=16, roi=8, lam=0, penalty=256),
    'block32_period1': dict(motion='block', block=32, period=1, bg=16, roi=8, lam=0, penalty=512),
    'zero_coarse': dict(motion='zero', block=16, period=1, bg=32, roi=8, lam=0, penalty=0),
    'zero_rdo4': dict(motion='zero', block=16, period=1, bg=16, roi=8, lam=4, penalty=0),
    'zero_rdo16': dict(motion='zero', block=16, period=1, bg=16, roi=8, lam=16, penalty=0),
    'block16_rdo4': dict(motion='block', block=16, period=1, bg=16, roi=8, lam=4, penalty=256),
    'zero_roi16_rdo4': dict(motion='zero', block=16, period=1, bg=32, roi=16, lam=4, penalty=0),
}


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path): return json.loads(Path(path).read_text())
def digest(a): return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def raw(desc, directory=V24):
    p = Path(desc['path'])
    assert not p.is_absolute() and '..' not in p.parts
    data = (directory / p).read_bytes()
    assert hashlib.sha256(data).hexdigest() == desc['stored_sha256']
    d = zlib.decompressobj(); value = d.decompress(data, desc['raw_bytes'] + 1)
    assert d.eof and not d.unused_data and not d.unconsumed_tail
    assert len(value) == desc['raw_bytes'] and hashlib.sha256(value).hexdigest() == desc['raw_sha256']
    return value


def blob(data):
    stored = zlib.compress(data, 9)
    path = 'objects/' + hashlib.sha256(stored).hexdigest() + '.zlib'
    (HERE / 'objects').mkdir(exist_ok=True)
    (HERE / path).write_bytes(stored)
    return dict(path=path, raw_bytes=len(data), raw_sha256=hashlib.sha256(data).hexdigest(), stored_sha256=hashlib.sha256(stored).hexdigest())


def source(row):
    a = np.frombuffer(raw(row['common_yuv420_u8']), np.uint8)
    return tuple(v.astype(np.int16) for v in (a[:345600].reshape(480, 720), a[345600:432000].reshape(240, 360), a[432000:].reshape(240, 360)))


def original(row): return np.frombuffer(raw(row['original_rgb565']), '<u2').reshape(480, 720)


def overlay(words, patches):
    out = words.copy()
    for (x, y, w, h), a in zip(RECTS, patches): out[y:y+h, x:x+w] = a
    return out


def metric(a, c):
    e = (b.C.corpus.expand565(a).astype(np.int64) - b.C.corpus.expand565(c).astype(np.int64)) ** 2
    s = int(e[37:442].sum()); n = 720 * 405 * 3
    return dict(active_squared_error=s, active_channel_samples=n, active_mse=s/n,
                active_psnr_db=None if not s else 10*math.log10(65025/(s/n)),
                hud_word_errors=sum(int(np.count_nonzero(a[y:y+h, x:x+w] != c[y:y+h, x:x+w])) for x, y, w, h in RECTS))


def pins():
    prev = load(V24 / 'results.json')
    paths = {ROOT / p for p in prev['source_sha256']}
    paths |= {V24 / 'results.json', HERE / 'benchmark.py'}
    paths |= set((HERE.parent / 'python-game-base-motion-v25-study').glob('*.py'))
    for inp in prev['inputs']:
        for row in inp['rows']:
            paths |= {V24 / row[k]['path'] for k in ('original_rgb565', 'common_yuv420_u8')}
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(paths)}


def summarize(rows):
    total = sum(r['base_bytes'] for r in rows)
    result = dict(frames=len(rows), base_bytes=total, base_Mbps_at30=total*8*30/len(rows)/1e6,
                  max_base_bytes=max(r['base_bytes'] for r in rows),
                  mean_encode_ms=sum(r['work']['encoder_wall_ms'] for r in rows)/len(rows),
                  mean_decode_ms=sum(r['decode_ms'] for r in rows)/len(rows),
                  published_reference_frames=sum(r['publish'] for r in rows),
                  search_sample_comparisons=sum(r['work']['analysis']['search']['sad_sample_operations'] for r in rows),
                  search_ms=sum(r['work']['search_ms'] for r in rows),
                  zeroed_blocks=sum(r['work']['rdo']['zeroed_blocks'] for r in rows),
                  decoder_reference_sample_reads=sum(r['work']['decoder_reference_sample_reads'] for r in rows),
                  reconstructed_reference_write_bytes=sum(1036800 for r in rows if r['publish']))
    for variant in ('bare', 'hybrid'):
        s = sum(r[variant]['active_squared_error'] for r in rows)
        n = sum(r[variant]['active_channel_samples'] for r in rows)
        result[variant] = dict(active_squared_error=s, active_channel_samples=n, active_mse=s/n,
                               active_psnr_db=10*math.log10(65025/(s/n)),
                               hud_word_errors=sum(r[variant]['hud_word_errors'] for r in rows))
    return result


def run(inp, profile, count=48):
    cfg = PROFILES[profile]
    ref, refid, slot = None, b.NO_REF, 0
    rows = []
    for row in inp['rows'][:count]:
        fid = row['id']; key = fid % 24 == 0
        if key: ref, refid, slot = None, b.NO_REF, 0
        publish = key or fid % cfg['period'] == 0
        src = source(row)
        mapped = b.roi.declared_map(720, 480, ROIS, cfg['roi'], 32 if key else cfg['bg'])
        packet, expected, work = b.encode_planes(src, ref, mapped, epoch=25, frame_id=fid, reference_id=refid,
                                                block_size=cfg['block'], motion_mode=cfg['motion'], penalty=cfg['penalty'], rdo_lambda=cfg['lam'])
        start = time.perf_counter_ns()
        decoded, meta = b.decode(packet, ref, expected_epoch=25, expected_reference_id=None if key else refid)
        decode_ms = (time.perf_counter_ns()-start)/1e6
        for x, y in zip(decoded, expected): np.testing.assert_array_equal(x, y)
        orig = original(row)
        patches = tuple(orig[y:y+h, x:x+w] for x, y, w, h in RECTS)
        bare = b.C.corpus.rgb565(b.ft.planes_to_rgb(decoded)); hybrid = overlay(bare, patches)
        dest = 0 if key else 1-slot if publish else 255
        rows.append(dict(id=fid, key=key, publish=publish, source_slot=255 if key else slot, destination_slot=dest,
                         reference_id=refid, base_bytes=len(packet), base_packet=blob(packet), work=work, decode_ms=decode_ms,
                         reconstructed_yuv_tag=meta['reconstructed_tag'].hex(),
                         bare_rgb565_sha256=digest(bare), hybrid_rgb565_sha256=digest(hybrid),
                         bare=metric(orig, bare), hybrid=metric(orig, hybrid)))
        if publish: ref, refid, slot = decoded, fid, dest
    result = dict(scene=inp['scene'], profile=profile, policy=cfg, rows=rows, summary=summarize(rows))
    print(json.dumps(dict(scene=inp['scene'], profile=profile, summary=result['summary'])), flush=True)
    return result


def main():
    p = argparse.ArgumentParser(); p.add_argument('--profiles', nargs='+', choices=list(PROFILES), default=list(PROFILES)); p.add_argument('--frames', type=int, default=48)
    args = p.parse_args(); assert args.frames == 48, 'full native campaign is fixed48'
    before = pins(); old = load(V24 / 'results.json'); cases = []
    result = dict(schema='gamebub-native-motion-v25', source_sha256=before, versions=dict(python=platform.python_version(), numpy=np.__version__),
                  scope=['Reused precompressed29.88fps windows, 720x480 coded/720x405 active; offline projection30IDs/s.',
                         'Fixed policies chosen before each complete window; key0/24 coarsebackground32; no lookahead in encode.',
                         'GM25 components are decoded with reconstructed reference only; actual CP25 admission/ACK replay is separate.',
                         'Pubsper8 versusper1 alter reference history; image improvements are not pure entropy gains.',
                         'Python hostwork/reference logicalbytes are not native ESP32/FPGA throughput or physical30fps.'], cases=cases)
    for inp in old['inputs']:
        for profile in args.profiles:
            cases.append(run(inp, profile))
            assert pins() == before
            (HERE / 'results.json').write_text(json.dumps(result, separators=(',', ':'), allow_nan=False)+'\n')


if __name__ == '__main__': main()
