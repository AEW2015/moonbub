#!/usr/bin/env python3
"""Independent byte, arithmetic, and provenance audit of unified GM27/CP27.

The separate unified-v27 verifier owns full reconstruction/pixel replay. This
module checks retained serialized evidence and does not claim native throughput.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import zlib

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
UNIFIED = ROOT / 'experiments/python-game-unified-v27-study'
V26_FULL = ROOT / 'experiments/python-game-prediction-v26-study/full_results.json'
V26_ENTROPY = ROOT / 'experiments/python-game-entropy-v26-study/results.json'
V24 = ROOT / 'experiments/python-game-standard-v24-study/results.json'
CAP = 49_152
HUD_WORDS = 21_120
NO_REF = 0xFFFFFFFF
CP27 = struct.Struct('<4sBBIIBBII16s16s')
GM27 = struct.Struct('<4sBBIIIHHBB16s16sIIIII')
HU25 = struct.Struct('<4sBBIIIHH16s16s4I4B16H')
JA27 = struct.Struct('<4sBII16s16s16s')


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    return sha(path.read_bytes())


def load(path: Path):
    return json.loads(path.read_text())


def projected_mbps(complete_bytes: int, frames: int, ids_per_second: int = 30) -> float:
    if any(type(v) is not int for v in (complete_bytes, frames, ids_per_second)):
        raise ValueError('rate inputs must be integers')
    if complete_bytes < 0 or frames <= 0 or ids_per_second <= 0:
        raise ValueError('invalid rate inputs')
    return complete_bytes * 8 * ids_per_second / frames / 1_000_000


def complete_body_bytes(base_bytes: int, hud_bytes: int, binding_bytes: int = 60) -> int:
    values = (base_bytes, hud_bytes, binding_bytes)
    if any(type(v) is not int or v < 0 for v in values):
        raise ValueError('component byte counts must be nonnegative integers')
    return sum(values)


def under_cap(size: int, cap: int = CAP) -> bool:
    if type(size) is not int or type(cap) is not int or size < 0 or cap <= 0:
        raise ValueError('invalid packet size/cap')
    return size <= cap


def quality_stats(metric: dict) -> tuple[int, int, float]:
    sse, samples = metric.get('active_squared_error'), metric.get('active_channel_samples')
    if type(sse) is not int or type(samples) is not int or sse < 0 or samples <= 0:
        raise ValueError('invalid active SSE/sample totals')
    mse = sse / samples
    declared = metric.get('active_mse')
    if declared is not None and declared != mse:
        raise ValueError('active MSE does not equal integer SSE/sample count')
    return sse, samples, mse


def candidate_eligible(complete_bytes: int, active_sse: int, zero_candidate_sse: int,
                       cap: int = CAP) -> bool:
    if any(type(v) is not int for v in (complete_bytes, active_sse, zero_candidate_sse, cap)):
        raise ValueError('candidate guard inputs must be integers')
    if min(complete_bytes, active_sse, zero_candidate_sse) < 0 or cap <= 0:
        raise ValueError('invalid candidate guard inputs')
    return complete_bytes <= cap and active_sse <= zero_candidate_sse


def lineage(left: list, right: list, *, ref_field='reference_id') -> None:
    if len(left) != len(right):
        raise ValueError('lineage row counts differ')
    for a, b in zip(left, right):
        if a.get('id') != b.get('id') or a.get('source_common_yuv_sha256') != b.get('source_common_yuv_sha256'):
            raise ValueError(f'source lineage differs at frame {a.get("id")}')
        if ref_field in a and ref_field in b and a[ref_field] != b[ref_field]:
            raise ValueError(f'reference lineage differs at frame {a.get("id")}')


def read_object(desc: dict, base_dir: Path, *, max_raw_bytes=2_000_000, enforce_repo_root=True) -> bytes:
    path = Path(desc['path'])
    if path.is_absolute() or '..' in path.parts:
        raise ValueError('unsafe object path')
    declared_dir = desc.get('directory')
    folder = ROOT / declared_dir if declared_dir else base_dir
    folder = folder.resolve()
    allowed = (ROOT / declared_dir).resolve() if declared_dir else base_dir.resolve()
    if folder != allowed or (enforce_repo_root and ROOT not in folder.parents):
        raise ValueError('object root outside repository')
    stored = (folder / path).read_bytes()
    if 'stored_bytes' in desc and len(stored) != desc['stored_bytes']:
        raise ValueError('stored length mismatch')
    if sha(stored) != desc['stored_sha256']:
        raise ValueError('stored SHA-256 mismatch')
    raw_len = desc['raw_bytes']
    if type(raw_len) is not int or not 0 <= raw_len <= max_raw_bytes:
        raise ValueError('raw object exceeds audit bound')
    dec = zlib.decompressobj()
    raw = dec.decompress(stored, raw_len + 1)
    if (len(raw) != raw_len or not dec.eof or dec.unused_data or dec.unconsumed_tail
            or sha(raw) != desc['raw_sha256']):
        raise ValueError('bounded object decode/hash mismatch')
    return raw


def _crc_ok(data: bytes) -> bool:
    return len(data) >= 4 and zlib.crc32(data[:-4]) == struct.unpack_from('<I', data, len(data) - 4)[0]


def parse_hu25(packet: bytes) -> dict:
    if len(packet) < HU25.size + 4 or len(packet) > CAP or not _crc_ok(packet):
        raise ValueError('HU25 length/CRC')
    f = HU25.unpack_from(packet)
    magic, version, count, epoch, frame, refid, width, height, ref_tag, out_tag = f[:10]
    sizes, kinds, rects = f[10:14], f[14:18], f[18:]
    if (magic, version) != (b'HU25', 1) or count > 4 or (width, height) != (720,480):
        raise ValueError('HU25 profile/geometry')
    if not epoch or frame >= NO_REF or out_tag == bytes(16):
        raise ValueError('HU25 identity/output tag')
    if refid == NO_REF and ref_tag != bytes(16):
        raise ValueError('HU25 independent reference tag')
    if refid != NO_REF and (refid >= frame or ref_tag == bytes(16)):
        raise ValueError('HU25 past reference identity')
    if (len(packet) != HU25.size + sum(sizes) + 4
            or any(k not in (1, 2) for k in kinds[:count])
            or any(n <= 0 for n in sizes[:count])):
        raise ValueError('HU25 exact payload framing')
    rectangles = [tuple(rects[4*i:4*i+4]) for i in range(count)]
    for i, (x, y, w, h) in enumerate(rectangles):
        if not w or not h or x + w > width or y + h > height:
            raise ValueError('HU25 rectangle bounds')
        for ox, oy, ow, oh in rectangles[:i]:
            if x < ox + ow and ox < x + w and y < oy + oh and oy < y + h:
                raise ValueError('HU25 overlapping rectangles')
    if any(sizes[i] or kinds[i] or any(rects[4*i:4*i+4]) for i in range(count, 4)):
        raise ValueError('HU25 unused slots not zero padded')
    return dict(epoch=epoch, frame=frame, reference_id=refid, width=width,height=height,
                out_tag=out_tag,
                reference_tag=ref_tag, patch_words=sum(w*h for x,y,w,h in rectangles),
                rectangles=rectangles, bytes=len(packet))


def parse_gm27(packet: bytes) -> dict:
    if len(packet) < GM27.size + 4 or len(packet) > 2_000_000 or not _crc_ok(packet):
        raise ValueError('GM27 length/CRC')
    f = GM27.unpack_from(packet)
    (magic, version, flags, epoch, frame, refid, width, height, block, limit,
     ref_tag, out_tag, nq, nv, ny, ncb, ncr) = f
    if (magic, version, flags, block, limit) not in ((b'GM27',1,0,16,18),(b'GM27',1,0,32,18),
                                                        (b'GM27',1,1,16,18),(b'GM27',1,1,32,18)):
        raise ValueError('GM27 profile/flags')
    if not epoch or frame >= NO_REF or not (1 <= width <= 720 and 1 <= height <= 480):
        raise ValueError('GM27 identity/geometry')
    key = bool(flags)
    if key and (refid != NO_REF or ref_tag != bytes(16) or nv):
        raise ValueError('GM27 key reference fields')
    if not key and (refid >= frame or ref_tag == bytes(16) or not nv):
        raise ValueError('GM27 P reference fields')
    if out_tag == bytes(16) or nq == 0 or any(n == 0 for n in (ny,ncb,ncr)):
        raise ValueError('GM27 map/plane bounds')
    if len(packet) != GM27.size + nq + nv + ny + ncb + ncr + 4:
        raise ValueError('GM27 exact substream lengths')
    return dict(epoch=epoch, frame=frame, reference_id=refid,key=key,width=width,height=height,
                reference_tag=ref_tag, reconstructed_tag=out_tag, bytes=len(packet))


def parse_cp27(packet: bytes) -> dict:
    if len(packet) < CP27.size + 4 or len(packet) > CAP or not _crc_ok(packet):
        raise ValueError('CP27 complete cap/CRC')
    magic, ver, flags, epoch, frame, source, dest, nb, nh, bt, ht = CP27.unpack_from(packet)
    if (magic, ver) != (b'CP27', 1) or flags not in (0, 2, 3):
        raise ValueError('CP27 profile/flags')
    if len(packet) != CP27.size + nb + nh + 4:
        raise ValueError('CP27 exact lengths')
    base = packet[CP27.size:CP27.size+nb]
    hud = packet[CP27.size+nb:-4]
    if hashlib.sha256(base).digest()[:16] != bt or hashlib.sha256(hud).digest()[:16] != ht:
        raise ValueError('CP27 component digest')
    bm, hm = parse_gm27(base), parse_hu25(hud)
    key = flags == 3
    if (bm['epoch'], bm['frame'], hm['epoch'], hm['frame']) != (epoch, frame, epoch, frame):
        raise ValueError('CP27 nested identity mismatch')
    if (bm['width'],bm['height']) != (hm['width'],hm['height']):
        raise ValueError('CP27 nested geometry mismatch')
    if bm['key'] != key or (key and (source, dest) != (255,0)):
        raise ValueError('CP27 base/bank semantics')
    if not key and (source not in (0,1) or dest != (1-source if flags == 2 else 255)):
        raise ValueError('CP27 P bank semantics')
    if key != (hm['reference_id'] == NO_REF) or (not key and hm['reference_id'] >= frame):
        raise ValueError('CP27 HUD reference semantics')
    return dict(epoch=epoch, frame=frame, flags=flags, source=source, destination=dest,
                base=base, hud=hud, base_meta=bm, hud_meta=hm,
                pair_tag=hashlib.sha256(packet).digest()[:16], bytes=len(packet))


def parse_ja27(ack: bytes, pair: dict) -> dict:
    if len(ack) != JA27.size + 4 or not _crc_ok(ack):
        raise ValueError('JA27 exact length/CRC')
    magic, ver, epoch, frame, pair_tag, base_tag, hud_tag = JA27.unpack_from(ack)
    expected = (b'JA27', 1, pair['epoch'], pair['frame'], pair['pair_tag'],
                pair['base_meta']['reconstructed_tag'], pair['hud_meta']['out_tag'])
    if (magic, ver, epoch, frame, pair_tag, base_tag, hud_tag) != expected:
        raise ValueError('JA27 pair/reconstruction binding')
    return dict(epoch=epoch, frame=frame, bytes=len(ack))


def _walk_objects(value):
    if isinstance(value, dict):
        if all(k in value for k in ('path','raw_bytes','raw_sha256','stored_sha256')):
            yield value
        else:
            for child in value.values():
                yield from _walk_objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_objects(child)


def _case_map(data):
    result = {}
    for case in data['cases']:
        key = (case['scene'], case['policy'])
        if key in result:
            raise ValueError('duplicate campaign case')
        result[key] = case
    return result


def _verify_pins(pins: dict) -> int:
    if not isinstance(pins, dict) or not pins:
        raise ValueError('source pins missing')
    for rel, expected in sorted(pins.items()):
        p = Path(rel)
        if p.is_absolute() or '..' in p.parts or len(expected) != 64:
            raise ValueError('unsafe source pin')
        path = ROOT / p
        if not path.is_file() or sha_file(path) != expected:
            raise ValueError(f'source pin mismatch: {rel}')
    return len(pins)


def _source_hashes(paths) -> dict:
    out = {}
    for path in paths:
        path = Path(path).resolve()
        rel = path.relative_to(ROOT).as_posix()
        if path == (HERE / 'audit.json').resolve() or path == (HERE / 'audit.log').resolve():
            continue
        out[rel] = sha_file(path)
    return dict(sorted(out.items()))


def _standard_rows(standard, case_key, hud_by_id, target_mse):
    scene = case_key[0]
    candidates = []
    for case in standard['cases']:
        if case['scene'] != scene:
            continue
        ids = [row['id'] for row in case['rows']]
        if ids != list(range(48)):
            raise ValueError('standard source frame IDs incomplete')
        total = sse = samples = max_bytes = 0
        for row in case['rows']:
            metric = row['hybrid']['metric']
            row_sse, row_samples, _ = quality_stats(metric)
            complete = complete_body_bytes(row['coded_access_unit_bytes'], hud_by_id[row['id']], 60)
            total += complete; sse += row_sse; samples += row_samples
            max_bytes = max(max_bytes, complete)
        mse = sse / samples
        candidates.append(dict(codec=case['codec'], profile=case['profile'], frames=48,
                               complete_bytes=total, max_complete_bytes=max_bytes,
                               active_squared_error=sse, active_channel_samples=samples,
                               active_mse=mse, same_current_HU25_and_60B_binding=True,
                               at_least_custom_quality=mse <= target_mse,
                               cap_fits=max_bytes <= CAP))
    eligible = [x for x in candidates if x['at_least_custom_quality'] and x['cap_fits']]
    if not eligible:
        raise ValueError(f'no sampled native operating point meets custom quality for {scene}')
    selected = {}
    for codec in sorted({x['codec'] for x in eligible}):
        selected[codec] = min((x for x in eligible if x['codec'] == codec), key=lambda x:x['complete_bytes'])
    return dict(sampled_operating_points=sorted(candidates,key=lambda x:(x['codec'],x['profile'])),
                selected_same_HU25={k:selected[k] for k in sorted(selected)})


def build_audit() -> dict:
    data = load(UNIFIED / 'results.json')
    v26 = load(V26_FULL)
    entropy = load(V26_ENTROPY)
    standard = load(V24)
    if data.get('schema') != 'gamebub-unified-v27':
        raise ValueError('unexpected unified-v27 schema')
    if v26.get('schema') != 'gamebub-fractional-full-v26' or entropy.get('schema') != 'gamebub-entropy-v26' or standard.get('schema') != 'gamebub-standard-compare-v24':
        raise ValueError('unexpected frozen comparison schema')
    source_pin_count = _verify_pins(data['source_sha256'])
    v26_map, entropy_map = _case_map(v26), _case_map(entropy)
    input_yuv = {item['scene']: {row['id']: row['common_yuv420_u8_sha256'] for row in item['rows']}
                 for item in standard['inputs']}
    actual = _case_map(data)
    expected_keys = {(scene, policy) for scene in ('mass-effect-2600','mass-effect-7200')
                     for policy in ('frozen_trace','unified_causal')}
    if actual.keys() != expected_keys:
        raise ValueError('campaign must retain two scenes and both policies')
    if data.get('counts') != dict(unique_source_frames=96, accepted_pairs=192, exact_hud_words=192*HUD_WORDS):
        raise ValueError('campaign count metadata mismatch')
    object_seen = set(); object_count = object_raw_bytes = parsed_pairs = parsed_acks = 0
    reports, standards, timing = [], {}, []
    for scene in ('mass-effect-2600','mass-effect-7200'):
        old = v26_map[(scene,'causal-actual-byte-zero-or-half32-SSE-gate')]
        old_entropy = entropy_map[(scene,'block_major')]
        scene_reports = {}
        for policy in ('frozen_trace','unified_causal'):
            case = actual[(scene,policy)]
            rows = case['rows']
            if len(rows) != 48 or [r['id'] for r in rows] != list(range(48)):
                raise ValueError(f'{scene}/{policy} frame IDs incomplete or reordered')
            base_total = body_total = sse_total = sample_total = hud_total = max_body = 0
            candidate_bytes = attempts_total = analyses_total = cap_rejections = quality_rejections = 0
            paid_cpu_ms = receiver_ms = ack_ms = 0.0
            hud_by_id = {}
            previous_base_tag = previous_hud_tag = bytes(16)
            for i, row in enumerate(rows):
                prior = old['rows'][i]
                if row['key'] != (i % 24 == 0):
                    raise ValueError(f'{scene}/{policy}:{i} key cadence mismatch')
                if row['source_common_yuv_sha256'] != input_yuv[scene][i]:
                    raise ValueError(f'{scene}/{policy}:{i} source YUV differs from retained v24 input')
                if row['reference_id'] != row['id'] - 1 and not row['key']:
                    raise ValueError(f'{scene}/{policy}:{i} causal base reference must be prior frame')
                packet = read_object(row['packet'], UNIFIED)
                base = read_object(row['base_packet'], UNIFIED)
                hud = read_object(row['hud_packet'], UNIFIED)
                ack = read_object(row['ack'], UNIFIED)
                pair = parse_cp27(packet)
                am = parse_ja27(ack, pair)
                parsed_pairs += 1; parsed_acks += 1
                if pair['frame'] != i or pair['epoch'] != 25 or pair['bytes'] != row['body_bytes']:
                    raise ValueError(f'{scene}/{policy}:{i} CP27 identity/byte count')
                if pair['base'] != base or pair['hud'] != hud:
                    raise ValueError(f'{scene}/{policy}:{i} CP27 component objects differ')
                bm, hm = pair['base_meta'], pair['hud_meta']
                if len(base) != row['base_bytes'] or len(hud) != row['hud_bytes']:
                    raise ValueError(f'{scene}/{policy}:{i} actual component byte fields')
                if hm['reference_id'] != (NO_REF if row['key'] else i - 1):
                    raise ValueError(f'{scene}/{policy}:{i} HU25 last-accepted reference lineage')
                if hm['patch_words'] != HUD_WORDS or row['binding_bytes'] != 60 or len(ack) != 65:
                    raise ValueError(f'{scene}/{policy}:{i} exact HUD/binding/ACK bytes')
                if complete_body_bytes(len(base),len(hud),60) != len(packet):
                    raise ValueError(f'{scene}/{policy}:{i} complete body components do not sum')
                if row['body_bytes'] > CAP or row['source_slot'] != pair['source'] or row['destination_slot'] != pair['destination']:
                    raise ValueError(f'{scene}/{policy}:{i} cap/bank metadata')
                if row['reference_id'] != bm['reference_id'] or row['reference_id'] >= i and not row['key']:
                    raise ValueError(f'{scene}/{policy}:{i} base reference lineage')
                if row['key']:
                    if bm['reference_tag'] != bytes(16) or hm['reference_tag'] != bytes(16):
                        raise ValueError(f'{scene}/{policy}:{i} independent key has nonzero reference tag')
                elif bm['reference_tag'] != previous_base_tag or hm['reference_tag'] != previous_hud_tag:
                    raise ValueError(f'{scene}/{policy}:{i} base/HUD reference tag lineage')
                previous_base_tag=bm['reconstructed_tag'];previous_hud_tag=hm['out_tag']
                ack_meta=row['ack_meta']
                expected_ack_meta=dict(epoch=25,frame_id=i,source_slot=row['source_slot'],
                    destination_slot=row['destination_slot'],published=True,
                    pair_tag=pair['pair_tag'].hex(),base_tag=bm['reconstructed_tag'].hex(),
                    hud_tag=hm['out_tag'].hex())
                if ack_meta != expected_ack_meta:
                    raise ValueError(f'{scene}/{policy}:{i} JSON ACK metadata differs from actual JA27')
                if row['selected_kind'] != ('zero' if row['key'] else row['selected_kind']):
                    raise ValueError('key selected kind must be zero')
                sse, samples, mse = quality_stats(row['hybrid'])
                if row['hybrid'].get('hud_word_errors') != 0:
                    raise ValueError('accepted candidate has HUD word errors')
                if row['hybrid_rgb565_sha256'] != prior['hybrid_rgb565_sha256'] and policy == 'frozen_trace':
                    raise ValueError(f'{scene}:{i} frozen-trace display hash differs from v26')
                if row['reconstructed_tag'] != prior['reconstructed_tag'] and policy == 'frozen_trace':
                    raise ValueError(f'{scene}:{i} frozen-trace reconstructed tag differs from v26')
                if (sse,samples,mse) != quality_stats(prior['hybrid']) and policy == 'frozen_trace':
                    raise ValueError(f'{scene}:{i} frozen-trace exact active SSE differs from v26')
                if policy == 'frozen_trace' and (row['selected_kind'],row['selected_background']) != (prior['selected_kind'],prior['selected_background']):
                    raise ValueError(f'{scene}:{i} frozen-trace encoder choice differs from v26')
                hud_by_id[i] = len(hud)
                base_total += len(base); body_total += len(packet); sse_total += sse; sample_total += samples
                hud_total += len(hud); max_body = max(max_body,len(packet))
                attempts = row['attempts']; analyses = row['analyses']
                if not attempts or not analyses:
                    raise ValueError(f'{scene}/{policy}:{i} omitted paid candidate/analysis work')
                attempts_total += len(attempts); analyses_total += len(analyses)
                paid = sum(float(v['analysis_wall_ms']) for v in analyses.values()) + sum(float(a['encode_ms']) for a in attempts)
                if not math.isclose(float(row['paid_base_encode_ms']),paid,rel_tol=0,abs_tol=1e-8):
                    raise ValueError(f'{scene}/{policy}:{i} paid losing-work timing sum')
                paid_cpu_ms += float(row['paid_base_encode_ms']); receiver_ms += float(row['receive_ms']); ack_ms += float(row['ack_validation_ms'])
                zero_sse_by_bg = {}
                checked_attempts = []
                for a in attempts:
                    ap = read_object(a['packet'],UNIFIED); ab = read_object(a['base_packet'],UNIFIED)
                    parsed = parse_cp27(ap)
                    if (parsed['base'] != ab or parsed['hud'] != hud or parsed['frame'] != i
                            or parsed['epoch'] != 25 or len(ab) != a['base_bytes'] or len(ap) != a['complete_bytes']):
                        raise ValueError(f'{scene}/{policy}:{i} candidate object/byte mismatch')
                    if complete_body_bytes(len(ab),len(parsed['hud']),60) != len(ap):
                        raise ValueError('candidate complete bytes do not reconcile')
                    capfit = len(ap) <= CAP
                    if bool(a['cap_fit']) != capfit:
                        raise ValueError(f'{scene}/{policy}:{i} candidate cap flag mismatch')
                    as_sse, as_samples, as_mse = quality_stats(a['hybrid'])
                    if (as_samples != samples or a.get('quality_eligible') is not True and a.get('quality_eligible') is not False):
                        raise ValueError(f'{scene}/{policy}:{i} candidate quality metadata')
                    if a['kind'] == 'zero': zero_sse_by_bg[a['background']] = as_sse
                    checked_attempts.append((a,capfit,as_sse,as_samples,as_mse))
                    candidate_bytes += len(ap)
                    cap_rejections += int(not capfit); quality_rejections += int(a.get('quality_eligible') is False)
                    for descriptor in (a['packet'],a['base_packet']):
                        key=(descriptor.get('directory'),descriptor['path'],descriptor['stored_sha256'])
                        if key not in object_seen:
                            object_seen.add(key); object_count += 1
                            object_raw_bytes += descriptor['raw_bytes']
                for a,capfit,as_sse,as_samples,as_mse in checked_attempts:
                    if policy == 'unified_causal' and a.get('quality_eligible') != (as_sse <= zero_sse_by_bg[a['background']]):
                        raise ValueError(f'{scene}/{policy}:{i} same-reference zero SSE guard mismatch')
                    expected_eligible = candidate_eligible(a['complete_bytes'],as_sse,zero_sse_by_bg.get(a['background'],as_sse)) if policy == 'unified_causal' else capfit
                    if a.get('selected') and not (expected_eligible and capfit):
                        raise ValueError(f'{scene}/{policy}:{i} selected candidate failed cap/SSE guard')
                chosen = next((x for x in checked_attempts if x[0].get('selected')),None)
                if chosen is None:
                    raise ValueError(f'{scene}/{policy}:{i} missing selected attempt')
                if (chosen[0]['kind'],chosen[0]['background']) != (row['selected_kind'],row['selected_background']):
                    raise ValueError(f'{scene}/{policy}:{i} selected attempt disagrees with row')
                if policy == 'unified_causal':
                    selected_bg = chosen[0]['background']
                    eligible = [x for x in checked_attempts if x[0]['background']==selected_bg and x[1] and x[2] <= zero_sse_by_bg[selected_bg]]
                    if not eligible or chosen[0]['complete_bytes'] != min(x[0]['complete_bytes'] for x in eligible):
                        raise ValueError(f'{scene}:{i} did not choose minimum actual eligible complete bytes')
                    backgrounds = list(dict.fromkeys(a['background'] for a in attempts))
                    if backgrounds not in ([16],[16,32]) or (backgrounds==[16,32] and any(x[1] and x[2] <= zero_sse_by_bg[16] for x in checked_attempts if x[0]['background']==16)):
                        raise ValueError(f'{scene}:{i} fine-then-coarse fallback order')
                for descriptor in (row['packet'],row['base_packet'],row['hud_packet'],row['ack']):
                    key=(descriptor.get('directory'),descriptor['path'],descriptor['stored_sha256'])
                    if key not in object_seen:
                        object_seen.add(key); object_count += 1
                        object_raw_bytes += descriptor['raw_bytes']
            mse = sse_total / sample_total
            summary = case['summary']
            expected_summary = dict(frames=48,complete_bytes=body_total,base_bytes=base_total,hud_bytes=hud_total,
                                    binding_bytes=48*60,maximum_complete_bytes=max_body,cap_fit_frames=48,
                                    exact_hud_words=48*HUD_WORDS,active_squared_error=sse_total,
                                    active_channel_samples=sample_total,active_mse=mse)
            for key,value in expected_summary.items():
                if summary.get(key) != value:
                    raise ValueError(f'{scene}/{policy} summary {key} does not sum rows')
            if summary.get('coded_body_Mbps_at30') != projected_mbps(body_total,48):
                raise ValueError(f'{scene}/{policy} nominal rate arithmetic mismatch')
            report = dict(scene=scene,policy=policy,frames=48,base_bytes=base_total,hud_bytes=hud_total,
                          binding_bytes=48*60,complete_bytes=body_total,maximum_complete_bytes=max_body,
                          cap_fit_frames=48,exact_hud_words=48*HUD_WORDS,active_squared_error=sse_total,
                          active_channel_samples=sample_total,active_mse=mse,complete_body_Mbps_at30=projected_mbps(body_total,48),
                          actual_candidate_attempts=attempts_total,actual_paid_analyses=analyses_total,
                          candidate_complete_bytes_constructed=candidate_bytes,cap_rejected_attempts=cap_rejections,
                          quality_guard_rejected_attempts=quality_rejections,
                          mean_paid_analysis_and_encode_ms=paid_cpu_ms/48,mean_receiver_ms=receiver_ms/48,
                          mean_ack_validation_ms=ack_ms/48,
                          timing_scope='Measured Python host CPU costs; projected 30 IDs/s rate is not measured FPS.')
            scene_reports[policy]=report
            timing.append(dict(scene=scene,policy=policy,mean_paid_analysis_and_encode_ms=paid_cpu_ms/48,
                               mean_receiver_ms=receiver_ms/48,mean_ack_validation_ms=ack_ms/48))
        frozen = scene_reports['frozen_trace']; causal = scene_reports['unified_causal']
        ec_case = old_entropy['summary']
        if ec_case.get('frames') != 48 or ec_case.get('exact_hud_words') != 48*HUD_WORDS:
            raise ValueError(f'{scene} frozen entropy-v26 control dimensions')
        frozen['frozen_v26_block_major_control'] = dict(
            complete_bytes=ec_case['complete_bytes'], active_squared_error=ec_case['active_squared_error'],
            active_channel_samples=ec_case['active_channel_samples'], active_mse=ec_case['active_mse'],
            relation='separate retained EC26 block-major campaign; not asserted byte- or image-identical to direct GM27')
        causal['active_mse_change_vs_frozen_prediction_v26'] = causal['active_mse'] - old['summary']['active_mse']
        causal['quality_relation_vs_frozen_prediction_v26'] = (
            'lower' if causal['active_mse'] < old['summary']['active_mse'] else
            'equal' if causal['active_mse'] == old['summary']['active_mse'] else 'higher')
        hud_current = {r['id']: r['hud_bytes'] for r in actual[(scene,'unified_causal')]['rows']}
        standards[scene] = _standard_rows(standard,(scene,'unified_causal'),hud_current,causal['active_mse'])
        reports.extend([scene_reports['frozen_trace'],scene_reports['unified_causal']])
    for desc in _walk_objects(data):
        key=(desc.get('directory'),desc['path'],desc['stored_sha256'])
        if key not in object_seen:
            read_object(desc,UNIFIED)
            object_seen.add(key);object_count+=1;object_raw_bytes+=desc['raw_bytes']
    audit_sources = {UNIFIED/'results.json',V26_FULL,V26_ENTROPY,V24,
                     HERE/'audit.py',HERE/'test_audit.py',HERE/'AUDIT-CHECKLIST.md',
                     UNIFIED/'benchmark.py',UNIFIED/'model.py',UNIFIED/'protocol.py',UNIFIED/'SCHEMA.md',UNIFIED/'README.md',UNIFIED/'tests.log'}
    for path in audit_sources:
        if not path.is_file():
            raise ValueError(f'missing pinned source/input: {path.relative_to(ROOT)}')
    source_hashes = _source_hashes(audit_sources)
    return dict(schema='gamebub-independent-audit-v27',source_sha256=source_hashes,
                source_pin_count=source_pin_count,verified_unique_archived_objects=object_count,
                verified_archived_raw_bytes=object_raw_bytes,actual_cp27_pairs_parsed=parsed_pairs,
                actual_ja27_acks_parsed=parsed_acks,
                cases=reports,standards_same_current_HU25=standards,cpu_timing=timing,
                profile_acceptance='GM27 syntax-only bounded motion-map parsing is intentional; receiver acceptance does not enforce sender-optimal re-encoding. Full motion and entropy semantics are validated before publication by the retained receiver verifier.',
                decoder_evidence='Full pixel/reconstruction replay is separately attributed to the source-pinned unified-v27 verifier; this audit checks retained objects and arithmetic without repeating heavy decode.',
                scope=dict(rate='Complete CP27 bytes projected at nominal 30 source IDs/s; not measured FPS or physical traffic.',
                           cpu='Single-host Python CPU timing fields are reported separately and exclude neither losing candidate work nor analysis.',
                           hardware='No FPGA fit, native FPS, RF delivery, or end-to-end hardware throughput is established.'))


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('--check',action='store_true',help='require existing audit.json to equal deterministic output byte for byte')
    args=parser.parse_args(argv)
    result=build_audit()
    encoded=json.dumps(result,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n'
    target=HERE/'audit.json'
    if args.check:
        if not target.is_file() or target.read_text()!=encoded:
            raise SystemExit('audit.json differs from deterministic audit output')
        print('PASS audit.json byte-identical')
    else:
        target.write_text(encoded)
        print('PASS wrote audit.json')


if __name__=='__main__':
    main()
