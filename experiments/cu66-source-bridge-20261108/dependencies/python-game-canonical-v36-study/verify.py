#!/usr/bin/env python3
"""Independent CN36 framing/support/causal replay using frozen GM27 grammar.

The v36 encoder, source mask, wrapper parser and receiver are never imported.
Only the frozen <=v35 source access, GM27 receive syntax and HX33 decoder are
shared. Hidden support is enumerated from scalar RGB sample dependencies.
"""
from functools import lru_cache
from pathlib import Path
import hashlib
import importlib.util
import json
import struct
import sys
import zlib

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    sys.modules[name] = obj
    spec.loader.exec_module(obj)
    return obj


frozen = module('cn36_verify_frozen35', HERE.parent/'python-game-controller-v35-study/helpers.py')
m, n, hud = frozen.m, frozen.n, frozen.p.hud
HEADER = struct.Struct('<4sBBHIIHH16s16s16sII')
CAP = 49152
PROFILE = hashlib.sha256(json.dumps(n.RECTS, separators=(',', ':')).encode()).digest()[:16]


@lru_cache(maxsize=None)
def safe_blocks(width=720, height=480):
    """Enumerate every RGB dependency rather than trust producer support bounds."""
    covered = np.zeros((height, width), dtype=bool)
    for x, y, w, h in n.RECTS:
        covered[y:y+h, x:x+w] = True
    supports = []
    for size in (width, height):
        axis = [[] for _ in range(size//2)]
        for output in range(size):
            reads = {output//2}
            if output % 2:
                reads.add(min(output//2+1, size//2-1))
            for sample in reads:
                axis[sample].append(output)
        supports.append(axis)
    result = []
    for plane in range(3):
        w, h = (width, height) if plane == 0 else (width//2, height//2)
        blocks = np.zeros(((h+7)//8, (w+7)//8), dtype=bool)
        for by in range(h//8):
            for bx in range(w//8):
                x, y = bx*8, by*8
                if plane == 0:
                    xs, ys = range(x, x+8), range(y, y+8)
                else:
                    xs = sorted({v for sample in range(x, x+8) for v in supports[0][sample]})
                    ys = sorted({v for sample in range(y, y+8) for v in supports[1][sample]})
                blocks[by, bx] = bool(covered[np.ix_(ys, xs)].all())
        blocks.flags.writeable = False
        result.append(blocks)
    return tuple(result)


def normalize(planes):
    out = tuple(p.copy() for p in planes)
    for plane, blocks in zip(out, safe_blocks(), strict=True):
        for by, bx in np.argwhere(blocks):
            plane[by*8:by*8+8, bx*8:bx*8+8] = 128
    return out


def parse(packet):
    if type(packet) is not bytes or not HEADER.size+8 <= len(packet) <= CAP:
        raise ValueError('CN36 bounded immutable packet')
    if zlib.crc32(packet[:-4]) != struct.unpack('<I', packet[-4:])[0]:
        raise ValueError('CN36 CRC')
    magic, version, flags, epoch, fid, rid, w, h, profile, rt, ot, nb, nh = HEADER.unpack_from(packet)
    if magic != b'CN36' or version != 1 or flags not in (0, 1, 2, 3) or epoch != 25:
        raise ValueError('CN36 profile/flags/epoch')
    if (w, h) != (720, 480) or profile != PROFILE:
        raise ValueError('CN36 fixed geometry/hidden-support contract')
    key, skip = bool(flags & 1), bool(flags & 2)
    if fid >= m.NO_REF or ot == bytes(16):
        raise ValueError('CN36 frame/output identity')
    if key:
        if rid != m.NO_REF or rt != bytes(16):
            raise ValueError('CN36 independent key')
    elif rid >= fid or rt == bytes(16):
        raise ValueError('CN36 prior normalized reference')
    if nb < m.HEADER.size+7 or nh < hud.p.HUD.size+4 or len(packet) != HEADER.size+nb+nh+4:
        raise ValueError('CN36 exact lengths')
    base, overlay = packet[HEADER.size:HEADER.size+nb], packet[HEADER.size+nb:-4]
    bm, hm = m.parse_metadata(base, expected_epoch=25), hud._meta(overlay)
    if (bm['frame_id'], bm['reference_id'], bm['width'], bm['height'], bm['key'], bm['reference_tag']) != (fid, rid, w, h, key, rt):
        raise ValueError('CN36 bound base identity')
    # Inner GM27/HX33 retain epoch25; CN36/profiletag declare new semantics.
    if (hm['epoch'], hm['frame_id'], hm['reference_id'], hm['width'], hm['height']) != (25, fid, rid, w, h):
        raise ValueError('CN36 bound HX33 identity')
    if tuple(hm['rectangles']) != n.RECTS:
        raise ValueError('CN36 exact opaque rectangle declaration')
    return dict(key=key, skip=skip, frame_id=fid, reference_id=rid,
                reference_tag=rt, output_tag=ot, base=base, hud=overlay,
                base_meta=bm, hud_meta=hm)


class Receiver:
    """Publish only after independent semantic decode, normalization and tags."""
    def __init__(self):
        self.reference = None
        self.reference_id = m.NO_REF
        self.patches = None
        self.last_id = -1

    def receive(self, packet):
        meta = parse(packet)
        fid, key = meta['frame_id'], meta['key']
        if fid <= self.last_id:
            raise ValueError('CN36 monotonic publication')
        if key:
            reference, rid, href = None, None, None
        else:
            reference, rid, href = self.reference, self.reference_id, self.patches
            if reference is None or rid != meta['reference_id'] or m.C.reference_tag(reference) != meta['reference_tag']:
                raise ValueError('CN36 actual normalized reference identity')
        planes, inner = m.decode(meta['base'], reference, expected_epoch=25, expected_reference_id=rid)
        if meta['skip'] and any(np.any(c[blocks.reshape(-1)]) for c, blocks in zip(inner['coefficients'], safe_blocks(), strict=True)):
            raise ValueError('CN36 skipped hidden residuals must be zero')
        normalized = normalize(planes)
        if m.C.reference_tag(normalized) != meta['output_tag']:
            raise ValueError('CN36 normalized output tag')
        patches, _ = hud.decode_hud(meta['hud'], href, expected_epoch=25, expected_reference_id=rid)
        self.reference, self.reference_id, self.patches, self.last_id = normalized, fid, patches, fid
        return normalized, patches, meta


def metric(planes, original, patches):
    words = m.C.corpus.rgb565(m.ft.planes_to_rgb(planes))
    display = n.overlay(words, tuple(p['words'] for p in patches))
    return n.metric(original, display), hashlib.sha256(display.tobytes()).hexdigest()


def raw(desc):
    return frozen.raw(desc, HERE)


def main():
    import math
    data = frozen.load(HERE/'results.json')
    assert data['schema'] == 'gamebub-canonical-v36'
    assert data['physical_30fps_proven'] is False and data['new_RTL_implemented'] is False
    assert data['HEVC_AV1_superiority_proven'] is False
    assert data['profile']['wrapper_bytes'] == HEADER.size+4 == 80
    assert data['profile']['profile_tag'] == PROFILE.hex()
    assert data['profile']['hidden_blocks'] == [int(v.sum()) for v in safe_blocks()]
    for path, expected in data['source_sha256'].items():
        assert frozen.sha(ROOT/path) == expected, path
    inputs = frozen.load(n.V24/'results.json')['inputs']
    scenes = ('mass-effect-2600', 'mass-effect-7200')
    assert [c['scene'] for c in data['cases']] == list(scenes)
    verified = equal_frames = exact_hud = candidates = omitted = 0
    for case in data['cases']:
        inp = next(v for v in inputs if v['scene'] == case['scene'])
        assert [r['id'] for r in case['rows']] == list(range(48))
        receivers = {name: Receiver() for name in ('full', 'skip')}
        legacy = frozen.p.Receiver()
        for src, row in zip(inp['rows'], case['rows'], strict=True):
            fid, key = row['id'], row['id'] % 24 == 0
            expected_rid = m.NO_REF if key else fid-1
            assert row['key'] == key and row['reference_id'] == expected_rid
            assert row['source_sha256'] == src['common_yuv420_u8_sha256']
            assert row['reference_tag'] == (bytes(16) if key else m.C.reference_tag(receivers['full'].reference)).hex()
            original = n.original(src)
            expected_patches = tuple(original[y:y+h, x:x+w] for x, y, w, h in n.RECTS)
            decoded = {}
            metas = {}
            for name in ('full', 'skip'):
                variant = row[name]
                packet, inner = raw(variant['packet']), raw(variant['inner'])
                planes, patches, meta = receivers[name].receive(packet)
                assert meta['skip'] == (name == 'skip') and meta['key'] == key
                assert meta['base'] == inner and meta['reference_id'] == expected_rid
                assert len(packet) == variant['complete_bytes'] == len(inner)+len(meta['hud'])+80 <= CAP
                assert variant['binding_bytes'] == 80 and variant['inner_bytes'] == len(inner)
                assert variant['hud_bytes'] == len(meta['hud'])
                assert meta['hud'] == frozen.raw(row['hud_packet'], frozen.HUD)
                for actual, expected in zip(patches, expected_patches, strict=True):
                    np.testing.assert_array_equal(actual['words'], expected)
                    exact_hud += expected.size
                quality, tag = metric(planes, original, patches)
                assert quality == variant['hybrid'] and tag == variant['display_sha256']
                assert m.C.reference_tag(planes).hex() == variant['normalized_tag']
                parsed = m.parse(inner, expected_epoch=25)
                assert parsed['block_size'] == 32 and not np.any(parsed['vectors'])
                np.testing.assert_array_equal(parsed['scale_map'], m.roi.declared_map(720, 480, n.ROIS, 8, row['background']))
                decoded[name], metas[name] = planes, parsed
                verified += 1
            for a, b in zip(decoded['full'], decoded['skip'], strict=True):
                np.testing.assert_array_equal(a, b)
            for full, skip, mask in zip(metas['full']['coefficients'], metas['skip']['coefficients'], safe_blocks(), strict=True):
                mask = mask.reshape(-1)
                np.testing.assert_array_equal(full[~mask], skip[~mask])
                assert not np.any(skip[mask])
                omitted += int(np.count_nonzero(full[mask]))
            assert row['skip_work']['zeroed_block_counts'] == [256, 19, 19]
            assert row['skip_work']['removed_nonzero_coefficients'] == sum(int(np.count_nonzero(c[mask.reshape(-1)])) for c, mask in zip(metas['full']['coefficients'], safe_blocks(), strict=True))
            np.testing.assert_array_equal(metas['full']['vectors'], metas['skip']['vectors'])
            np.testing.assert_array_equal(metas['full']['scale_map'], metas['skip']['scale_map'])
            assert row['full']['display_sha256'] == row['skip']['display_sha256']
            assert row['full']['hybrid'] == row['skip']['hybrid']
            equal_frames += 1
            variant = row['legacy_fixed']
            packet = raw(variant['packet'])
            pixels, patches, ack = legacy.receive(packet)
            frozen.p.validate_ack(ack, packet)
            lm = frozen.p.parse_pair(packet)
            assert lm['base'] == raw(variant['inner'])
            assert len(packet) == variant['complete_bytes'] == len(lm['base'])+len(lm['hud'])+60 <= CAP
            assert variant['binding_bytes'] == 60 and variant['inner_bytes'] == len(lm['base'])
            assert variant['hud_bytes'] == len(lm['hud'])
            assert lm['hud'] == frozen.raw(row['hud_packet'], frozen.HUD)
            q, tag = metric(pixels, original, patches)
            assert q == variant['hybrid'] and tag == variant['display_sha256']
            assert m.C.reference_tag(pixels).hex() == variant['reconstructed_tag']
            lparsed = m.parse(lm['base'], expected_epoch=25)
            assert lparsed['block_size'] == 32 and not np.any(lparsed['vectors'])
            np.testing.assert_array_equal(lparsed['scale_map'], metas['full']['scale_map'])
            for actual, expected in zip(patches, expected_patches, strict=True):
                np.testing.assert_array_equal(actual['words'], expected)
                exact_hud += expected.size
            verified += 1
            tiers = [c['background'] for c in row['candidates']]
            assert tiers in ([16], [16, 32]) and tiers[-1] == row['background']
            assert row['candidates'][-1]['cap_fit'] and all(not c['cap_fit'] for c in row['candidates'][:-1])
            for trial in row['candidates']:
                packets = {k: raw(v) for k, v in trial['packets'].items()}
                assert set(packets) == {'full', 'skip', 'legacy_fixed'}
                assert all(len(packets[k]) == trial[k+'_bytes'] for k in packets)
                assert trial['cap_fit'] == (max(map(len, packets.values())) <= CAP)
                assert all(zlib.crc32(p[:-4]) == struct.unpack('<I', p[-4:])[0] for p in packets.values())
                if trial is row['candidates'][-1]:
                    assert all(packets[k] == raw(row[k]['packet']) for k in packets)
                candidates += 3
            paid = row['analysis_ms'] + sum(c['full_encode_ms']+c['skip_proof_reparse_entropy_rebuild_ms']
                   +sum(c['normalize_ms'])+sum(c['wrap_ms']) for c in row['candidates'])
            assert math.isclose(paid, row['paid_proof_encoder_ms'], abs_tol=1e-9)
            legacy_paid = row['legacy_fixed_analysis_ms'] + sum(c['legacy_fixed_encode_ms']+c['legacy_fixed_wrap_ms'] for c in row['candidates'])
            assert math.isclose(legacy_paid, row['legacy_fixed_paid_encoder_ms'], abs_tol=1e-9)
        for name in ('full', 'skip', 'legacy_fixed'):
            values = [r[name] for r in case['rows']]
            summary = case['summary'][name]
            sse = sum(v['hybrid']['active_squared_error'] for v in values)
            samples = sum(v['hybrid']['active_channel_samples'] for v in values)
            assert summary['frames'] == 48 and summary['complete_bytes'] == sum(v['complete_bytes'] for v in values)
            assert summary['maximum_complete_bytes'] == max(v['complete_bytes'] for v in values)
            assert summary['active_squared_error'] == sse and summary['active_channel_samples'] == samples
            assert summary['active_mse'] == sse/samples
            assert summary['inner_bytes'] == sum(v['inner_bytes'] for v in values)
            assert summary['hud_bytes'] == sum(v['hud_bytes'] for v in values)
            assert summary['binding_bytes'] == sum(v['binding_bytes'] for v in values)
            assert math.isclose(summary['nominal_Mbps_at30'], summary['complete_bytes']*240/48/1e6)
            frame_mse = [v['hybrid']['active_mse'] for v in values]
            assert summary['peak_frame_mse'] == max(frame_mse)
            assert math.isclose(summary['mean_adjacent_frame_mse_change'], sum(abs(a-b) for a, b in zip(frame_mse, frame_mse[1:]))/47)
            assert math.isclose(summary['mean_receiver_ms'], sum(v['decode_ms'] for v in values)/48)
            if name == 'legacy_fixed':
                assert summary['mean_paid_proof_encoder_ms'] is None
                assert math.isclose(summary['mean_legacy_fixed_paid_encoder_ms'], sum(r['legacy_fixed_paid_encoder_ms'] for r in case['rows'])/48)
            else:
                assert summary['mean_legacy_fixed_paid_encoder_ms'] is None
                assert math.isclose(summary['mean_paid_proof_encoder_ms'], sum(r['paid_proof_encoder_ms'] for r in case['rows'])/48)
    assert verified == 288 and equal_frames == 96 and exact_hud == 6082560
    probe = data['motion_probe']
    inp = next(v for v in inputs if v['scene'] == probe['scene'])
    assert [r['id'] for r in probe['rows']] == list(range(6))
    receivers = {name: Receiver() for name in ('full', 'skip')}
    covered = np.zeros((480, 720), bool)
    for x, y, w, h in n.RECTS:
        covered[y:y+h, x:x+w] = True
    motion_decodes = motion_crossing = 0
    for src, row in zip(inp['rows'][:6], probe['rows'], strict=True):
        fid = row['id']
        assert row['key'] == (fid == 0)
        assert row['reference_id'] == (m.NO_REF if fid == 0 else fid-1)
        assert row['source_sha256'] == src['common_yuv420_u8_sha256']
        pair = {}
        for name in ('full', 'skip'):
            variant = row[name]
            packet = raw(variant['packet'])
            planes, patches, meta = receivers[name].receive(packet)
            assert meta['skip'] == (name == 'skip') and meta['base'] == raw(variant['inner'])
            assert len(packet) == variant['complete_bytes'] <= CAP
            assert m.C.reference_tag(planes).hex() == variant['normalized_tag']
            quality, tag = metric(planes, n.original(src), patches)
            assert quality == variant['hybrid'] and tag == variant['display_sha256']
            parsed = m.parse(meta['base'], expected_epoch=25)
            assert parsed['block_size'] == 32
            if fid == 0:
                assert not np.any(parsed['vectors']) and row['configured_vector_halfpel'] is None
                assert row['hidden_to_visible_luma_samples'] == 0 and row['nonzero_vectors'] == 0
            else:
                np.testing.assert_array_equal(parsed['vectors'], np.broadcast_to([-3, 1], parsed['vectors'].shape))
                assert row['configured_vector_halfpel'] == [-3, 1]
                assert row['nonzero_vectors'] == parsed['vectors'].shape[0]*parsed['vectors'].shape[1]
                indicator = normalize(tuple(np.zeros_like(v) for v in planes))
                predicted = m.predict(indicator, parsed['vectors'], 32)
                crossing = int(np.count_nonzero((predicted[0] != 0) & ~covered))
                assert crossing == row['hidden_to_visible_luma_samples'] > 0
                if name == 'full':
                    motion_crossing += crossing
            pair[name] = (planes, parsed)
            motion_decodes += 1
        for a, b in zip(pair['full'][0], pair['skip'][0], strict=True):
            np.testing.assert_array_equal(a, b)
        for a, b, mask in zip(pair['full'][1]['coefficients'], pair['skip'][1]['coefficients'], safe_blocks(), strict=True):
            np.testing.assert_array_equal(a[~mask.reshape(-1)], b[~mask.reshape(-1)])
            assert not np.any(b[mask.reshape(-1)])
        assert row['full']['display_sha256'] == row['skip']['display_sha256']
    print(json.dumps(dict(verified_causal_frames=verified, exact_canonical_frame_pairs=equal_frames,
                          actual_candidate_packets=candidates, exact_HUD_words=exact_hud,
                          omitted_nonzero_coefficients=omitted,
                          fractional_motion_probe_decodes=motion_decodes,
                          hidden_to_visible_luma_sample_events=motion_crossing,
                          source_pins=len(data['source_sha256']),
                          new_encoder_imported=False, physical_30fps_proven=False)))


if __name__ == '__main__':
    main()
