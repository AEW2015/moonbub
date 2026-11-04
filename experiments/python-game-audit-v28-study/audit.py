#!/usr/bin/env python3
"""Independent byte, arithmetic, and provenance audit of unified GM27/CP27.

The separate unified-v27 verifier owns full reconstruction/pixel replay. This
module checks retained serialized evidence and does not claim native throughput.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct
import sys
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


def close(a, b, tol=1e-12):
    return math.isclose(float(a),float(b),rel_tol=tol,abs_tol=tol)


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


def candidate_work(attempts: list[dict]) -> dict:
    """Sum actual paid work over every attempt, including rejected candidates."""
    if not isinstance(attempts, list) or not attempts:
        raise ValueError('candidate attempt list is empty')
    paid = 0.0
    blocks = 0
    selected = 0
    for attempt in attempts:
        ms = attempt.get('encode_ms')
        count = attempt.get('search_blocks')
        if isinstance(ms, bool) or not isinstance(ms, (int, float)) or not math.isfinite(ms) or ms < 0:
            raise ValueError('invalid paid candidate encode time')
        if type(count) is not int or count < 0:
            raise ValueError('invalid candidate search work count')
        if type(attempt.get('selected')) is not bool:
            raise ValueError('candidate selection flag missing')
        paid += float(ms)
        blocks += count
        selected += int(attempt['selected'])
    if selected != 1:
        raise ValueError('candidate attempts must identify exactly one selected result')
    return dict(attempts=len(attempts), selected_attempts=selected,
                paid_encode_ms=paid, search_blocks=blocks)


def source_hashes(paths, *, root: Path) -> dict:
    """Return sorted repository-relative SHA-256 pins for explicit input paths."""
    root = Path(root).resolve()
    result = {}
    for source in paths:
        path = Path(source).resolve()
        try:
            rel = path.relative_to(root).as_posix()
        except ValueError as exc:
            raise ValueError('source path outside inventory root') from exc
        if not path.is_file():
            raise ValueError(f'missing source input: {rel}')
        if rel in result:
            raise ValueError(f'duplicate source input: {rel}')
        result[rel] = sha_file(path)
    return dict(sorted(result.items()))


def verify_source_hashes(pins: dict, *, root: Path) -> None:
    if not isinstance(pins, dict) or not pins:
        raise ValueError('source hash inventory missing')
    expected = source_hashes([Path(root) / rel for rel in pins], root=root)
    if expected != dict(sorted(pins.items())):
        raise ValueError('source hash inventory mismatch')


def audit_input_paths(paths: list[str]) -> list[str]:
    """Normalize a source inventory while excluding generated audit outputs."""
    excluded = {'audit.json', 'audit.log'}
    return sorted({Path(p).as_posix() for p in paths if Path(p).name not in excluded})


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


def _percentile95(values):
    ordered = sorted(float(x) for x in values)
    if not ordered:
        raise ValueError('empty timing sample')
    pos = (len(ordered) - 1) * 0.95
    lo = math.floor(pos); hi = math.ceil(pos)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (pos - lo)


def _timing_stats(values):
    values = [float(x) for x in values]
    if not values or any(not math.isfinite(x) or x < 0 for x in values):
        raise ValueError('invalid timing sample list')
    ordered = sorted(values)
    mid = len(values) // 2
    median = ordered[mid] if len(values) % 2 else (ordered[mid-1] + ordered[mid]) / 2
    return dict(mean_ms=sum(values) / len(values), median_ms=median,
                p95_ms=_percentile95(values), minimum_ms=ordered[0], maximum_ms=ordered[-1])


def _tap_work_from_vectors(vectors, plane_shapes, block_size):
    h, w = plane_shapes[0]
    mw, mh = vectors.shape[1], vectors.shape[0]
    if (mw, mh) != ((w + block_size - 1)//block_size, (h + block_size - 1)//block_size):
        raise ValueError('tap vector grid differs from frame geometry')
    plane_work = []
    total_reads = 0
    frozen_reads = 0
    for plane, (ph, pw) in enumerate(plane_shapes):
        bs, den = (block_size, 2) if plane == 0 else (block_size // 2, 4)
        counts = {1: 0, 2: 0, 4: 0}
        reads = 0
        for by in range(mh):
            bh = min(bs, ph - by * bs)
            for bx in range(mw):
                bw = min(bs, pw - bx * bs)
                dx, dy = map(int, vectors[by, bx])
                taps = (1 + (dx % den != 0)) * (1 + (dy % den != 0))
                pixels = bh * bw
                counts[taps] += pixels
                reads += taps * pixels
        if sum(counts.values()) != ph * pw:
            raise ValueError('tap pixel partition does not cover plane')
        plane_work.append(dict(plane=plane, samples=ph*pw, denominator=den,
                               pixels_by_taps={str(k): counts[k] for k in (1,2,4)},
                               reference_sample_fetches=reads))
        total_reads += reads
        frozen_reads += 4 * ph * pw
    return dict(reference_sample_fetches=total_reads, frozen_reference_sample_fetches=frozen_reads,
                plane_work=plane_work)


def audit_taps_campaign():
    taps_path = ROOT / 'experiments/python-game-taps-v28-study/results.json'
    v27_path = ROOT / 'experiments/python-game-unified-v27-study/results.json'
    taps = load(taps_path)
    v27 = load(v27_path)
    if taps.get('schema') != 'gamebub-taps-v28' or v27.get('schema') != 'gamebub-unified-v27':
        raise ValueError('tap probe or frozen GM27 schema mismatch')
    pins = _verify_pins(taps.get('source_sha256'))
    v27cases = _case_map(v27)
    actual = _case_map(taps)
    if len(actual) != 4:
        raise ValueError('tap probe must cover both scenes and both policies')
    decoder_path = ROOT / 'experiments/python-game-decoder-v27-study/model.py'
    spec = importlib.util.spec_from_file_location('audit_v28_syntax_motion', decoder_path)
    decoder = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = decoder
    spec.loader.exec_module(decoder)
    frames = p_rows = archive_count = archive_bytes = 0
    old_times = []; new_times = []; reads = 0
    for scene in ('mass-effect-2600','mass-effect-7200'):
        for policy in ('frozen_trace','unified_causal'):
            case = actual[(scene,policy)]
            base_case = v27cases[(scene,policy)]
            if case.get('accepted_frames') != 48 or len(base_case['rows']) != 48:
                raise ValueError('tap probe/frame source count')
            rows = case.get('P_rows', [])
            if policy == 'frozen_trace' and rows:
                raise ValueError('tap P replay must be restricted to causal reference policy')
            expected_ids = [i for i in range(48) if i % 24 != 0] if policy == 'unified_causal' else []
            if [r.get('frame_id') for r in rows] != expected_ids:
                raise ValueError(f'{scene}/{policy} P input IDs do not match non-key frames')
            for row in rows:
                frame = row['frame_id']; refid = frame - 1
                source_row = base_case['rows'][frame]
                ref_row = base_case['rows'][refid]
                if row['reference_id'] != refid or row['base_packet'] != source_row['base_packet']:
                    raise ValueError(f'{scene}:{frame} tap source/reference association')
                if row['reference_packet'] != ref_row['base_packet']:
                    raise ValueError(f'{scene}:{frame} tap reference packet does not pair with prior accepted row')
                packet = read_object(row['base_packet'], ROOT / 'experiments/python-game-unified-v27-study')
                reference_packet = read_object(row['reference_packet'], ROOT / 'experiments/python-game-unified-v27-study')
                pm = parse_gm27(packet); rm = parse_gm27(reference_packet)
                if (pm['frame'], pm['reference_id'], pm['key']) != (frame, refid, False):
                    raise ValueError(f'{scene}:{frame} retained GM27 source packet identity')
                if (rm['frame'], rm['reconstructed_tag'].hex()) != (refid, row['reference_tag']):
                    raise ValueError(f'{scene}:{frame} retained GM27 reference tag')
                shapes = row['reference_plane_shapes']
                if shapes != [[480,720],[240,360],[240,360]]:
                    raise ValueError('tap probe reference plane geometry')
                vector_shape = row['vector_shape']
                bs = row['block_size']
                f = GM27.unpack_from(packet)
                mv_bytes = int(f[13])
                nq = int(f[12])
                offset = GM27.size + nq
                wire_vectors = packet[offset:offset+mv_bytes]
                import numpy as np
                mw, mh = (720+bs-1)//bs, (480+bs-1)//bs
                if len(wire_vectors) != mv_bytes:
                    raise ValueError(f'{scene}:{frame} vector substream length mismatch')
                vectors = decoder.unpack_vectors(wire_vectors, mw, mh)
                if vectors.tobytes().hex() != row['vectors_hex']:
                    raise ValueError(f'{scene}:{frame} vector map differs from compressed packet syntax')
                expected_shape = ((480+bs-1)//bs, (720+bs-1)//bs, 2)
                if vector_shape != list(expected_shape) or vectors.size != math.prod(expected_shape):
                    raise ValueError(f'{scene}:{frame} vector map shape')
                computed = _tap_work_from_vectors(vectors, [tuple(x) for x in shapes], bs)
                reported = row['work']
                for key in ('reference_sample_fetches','frozen_reference_sample_fetches','plane_work'):
                    if reported.get(key) != computed[key]:
                        raise ValueError(f'{scene}:{frame} actual tap count mismatch: {key}')
                if reported.get('clamped_duplicate_taps_deduplicated') is not False:
                    raise ValueError('tap counts must retain duplicate clamped logical gathers')
                old_ms = row['old_ms']; new_ms = row['new_ms']
                if len(old_ms) != 5 or len(new_ms) != 5:
                    raise ValueError('tap predictor timing rounds missing')
                old_times.extend(old_ms); new_times.extend(new_ms)
                reads += computed['reference_sample_fetches']
                p_rows += 1
                for descriptor, raw in ((row['base_packet'],packet),(row['reference_packet'],reference_packet)):
                    archive_count += 1; archive_bytes += len(raw)
            frames += case['accepted_frames']
    old_stats = _timing_stats(old_times); new_stats = _timing_stats(new_times)
    if (taps.get('replay') != dict(accepted_frames=192,bit_exact=True,reconstructed_tags_exact=True,global_predict_unmodified=True)
            or taps['timing']['P_inputs'] != p_rows
            or taps['timing']['rounds'] != 5
            or taps['logical_reads'] != dict(old=2_073_600*p_rows,new=reads)):
        raise ValueError('tap campaign summary dimensions/logical read totals')
    for label, computed in (('old',old_stats),('new',new_stats)):
        if taps['timing'][label] != computed:
            raise ValueError(f'tap {label} timing summary arithmetic differs from retained samples')
    expected_speedup = old_stats['mean_ms'] / new_stats['mean_ms']
    if not math.isclose(taps['timing']['mean_speedup'],expected_speedup,rel_tol=0,abs_tol=1e-12):
        raise ValueError('tap predictor mean speedup arithmetic')
    return dict(source_pins_verified=pins,accepted_frame_ids=frames,paired_p_inputs=p_rows,
                exact_vector_maps_checked=p_rows,per_plane_tap_accounting_checked=p_rows*3,
                archive_references_read=archive_count,archive_raw_bytes_checked=archive_bytes,
                actual_reference_gathers=reads,frozen_reference_gathers=2_073_600*p_rows,
                old_timing=old_stats,new_timing=new_stats,mean_speedup=expected_speedup,
                scope='Audited logical Python gathers and retained timing samples; not fitted hardware traffic or native frame rate.')


def audit_parity_campaign():
    folder=ROOT/'experiments/python-game-runtime-v28-study'
    parity=load(folder/'parity.json');old=load(UNIFIED/'results.json')
    if parity.get('schema')!='gamebub-lazy-parity-v28' or len(parity.get('cases',[]))!=2:
        raise ValueError('lazy parity probe schema/case count')
    pins=_verify_pins(parity.get('source_sha256'));oldcases=_case_map(old)
    rows_checked=bytes_checked=0;reports=[]
    for case in parity['cases']:
        scene=case['scene'];prior=oldcases[(scene,'unified_causal')]
        rows=case['rows']
        if len(rows)!=48 or [r['id'] for r in rows]!=list(range(48)):
            raise ValueError(f'{scene} exact encoder parity row IDs')
        frozen_times=[];lazy_times=[];frozen_cp=frozen_sp=lazy_cp=lazy_sp=sizecalls=0
        prior_base_tag=bytes(16)
        for i,row in enumerate(rows):
            oldrow=prior['rows'][i];packet=read_object(row['packet'],folder)
            expected=read_object(oldrow['base_packet'],UNIFIED)
            meta=parse_gm27(packet)
            key=i%24==0
            if (packet!=expected or row.get('packet_bytes_equal') is not True
                    or row['reference_id'] != (NO_REF if key else i-1)
                    or row['key'] is not key or meta['frame']!=i or meta['key'] is not key
                    or meta['reconstructed_tag'].hex()!=row['reconstructed_tag']
                    or row['reconstructed_tag']!=oldrow['reconstructed_tag']):
                raise ValueError(f'{scene}:{i} optimized encoder differs from frozen accepted packet')
            if key:
                if meta['reference_tag']!=bytes(16):raise ValueError('parity key nonzero reference tag')
            elif meta['reference_tag']!=prior_base_tag:
                raise ValueError(f'{scene}:{i} parity packet reference tag continuity')
            prior_base_tag=meta['reconstructed_tag']
            if row['selected_kind']!=oldrow['selected_kind'] or row['background']!=oldrow['selected_background']:
                raise ValueError(f'{scene}:{i} parity mode/background changed')
            for label in ('frozen_ms','lazy_ms'):
                value=row[label]
                if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<0:
                    raise ValueError('parity encode timing invalid')
            frozen_times.append(float(row['frozen_ms']));lazy_times.append(float(row['lazy_ms']))
            fw,lw=row['frozen_work'],row['lazy_work']
            if fw['packet_bytes']!=len(packet) or lw['packet_bytes']!=len(packet):
                raise ValueError(f'{scene}:{i} parity actual packet byte counters')
            frozen_cp+=int(fw['legacy_cp02_encode_calls']);lazy_cp+=int(lw['actual_cp02_encode_calls'])
            frozen_sp+=int(fw['legacy_sp01_construct_calls']);lazy_sp+=int(lw['actual_sp01_construct_calls'])
            sizecalls+=int(lw['legacy_size_counter_calls']);bytes_checked+=len(packet);rows_checked+=1
        summary=case['summary'];expected_summary=dict(frames=48,mean_frozen_encode_ms=sum(frozen_times)/48,
            mean_lazy_encode_ms=sum(lazy_times)/48,encode_speedup=sum(frozen_times)/sum(lazy_times),
            frozen_cp02_constructions=frozen_cp,lazy_cp02_constructions=lazy_cp,
            frozen_sp01_constructions=frozen_sp,lazy_sp01_constructions=lazy_sp,
            lazy_size_counter_calls=sizecalls,complete_packet_parity=True)
        if summary!=expected_summary:
            raise ValueError(f'{scene} parity summary arithmetic mismatch')
        reports.append(dict(scene=scene,summary=expected_summary,rows=48,actual_bytes_compared=sum(len(read_object(r['packet'],folder)) for r in rows)))
    return dict(source_pins_verified=pins,rows_checked=rows_checked,packet_bytes_checked=bytes_checked,cases=reports,
                scope='Actual exact parity against frozen accepted GM27 packets, paid encoder timing and construction counters; no pixel replay in this audit.')


def audit_search_probe():
    folder=ROOT/'experiments/python-game-search-v28-study'
    data=load(folder/'results.json')
    if data.get('schema')!='gamebub-search-v28-probe1' or len(data.get('rows',[]))!=24:
        raise ValueError('search probe schema/row count')
    pins=_verify_pins(data.get('source_sha256'));old=load(UNIFIED/'results.json');oldcases=_case_map(old)
    names=('exhaustive','sample4','sample2','sample4_refine2')
    aggregates={name:dict(bytes=0,sse=0,samples=0,cap=0,hud=0,p_analysis=[],p_search=[],whole=[],sad=0,reads=0) for name in names}
    checked=archive_bytes=0;scene_ids={}
    for row in data['rows']:
        scene=row['scene'];i=row['id'];prior=oldcases[(scene,'unified_causal')]['rows'][i]
        scene_ids.setdefault(scene,[]).append(i)
        if row.get('reference_id')!=prior['reference_id']:
            raise ValueError(f'{scene}:{i} probe source reference identity')
        accepted=read_object(row['accepted_packet'],folder)
        if accepted!=read_object(prior['packet'],UNIFIED):
            raise ValueError(f'{scene}:{i} search probe fixed accepted CP27 input')
        accepted_pair=parse_cp27(accepted)
        for name in names:
            item=row['variants'][name]
            base=read_object(item['base_packet'],folder);packet=read_object(item['packet'],folder)
            pair=parse_cp27(packet)
            if pair['base']!=base or pair['frame']!=i or pair['epoch']!=25:
                raise ValueError(f'{scene}:{i}/{name} actual CP27/base association')
            if len(base)!=item['base_bytes'] or len(packet)!=item['complete_bytes']:
                raise ValueError(f'{scene}:{i}/{name} actual packet sizes')
            if complete_body_bytes(len(base),len(pair['hud']),60)!=len(packet) or bool(len(packet)<=CAP)!=item['cap_fit']:
                raise ValueError(f'{scene}:{i}/{name} complete bytes/cap')
            sse,samples,_=quality_stats(item['hybrid'])
            if item['hybrid'].get('hud_word_errors')!=0:
                raise ValueError(f'{scene}:{i}/{name} HUD exactness')
            a=aggregates[name];a['bytes']+=len(packet);a['sse']+=sse;a['samples']+=samples
            a['cap']+=int(len(packet)<=CAP);a['hud']+=item['hybrid']['hud_word_errors']
            if i%24:
                a['p_analysis'].append(float(item['analysis']['analysis_wall_ms']))
                a['p_search'].append(float(item['analysis']['search_ms']))
                a['sad']+=int(item['analysis']['search']['sad_sample_operations'])
                a['reads']+=int(item['analysis']['search']['reference_sample_fetches'])
            a['whole'].append(float(item['whole_base_encode_ms']))
            checked+=1;archive_bytes+=len(base)+len(packet)
    if any(ids!=list(range(12)) for ids in scene_ids.values()) or set(scene_ids)!={'mass-effect-2600','mass-effect-7200'}:
        raise ValueError('search probe must pair first 12 exact source frames for each scene')
    for name,a in aggregates.items():
        summary=data['summaries'][name]
        expected=dict(frames=24,p_frames=22,complete_bytes=a['bytes'],active_mse=a['sse']/a['samples'],cap_fit_frames=a['cap'],
            hud_word_errors=a['hud'],mean_p_analysis_ms=sum(a['p_analysis'])/22,mean_p_search_ms=sum(a['p_search'])/22,
            mean_whole_base_encode_ms=sum(a['whole'])/24,p_sad_sample_operations=a['sad'],p_reference_sample_fetches=a['reads'])
        if any((not close(summary.get(k),v,1e-12)) if isinstance(v,float) else summary.get(k)!=v
               for k,v in expected.items()):
            raise ValueError(f'{name} search probe summary arithmetic differs from rows')
    return dict(source_pins_verified=pins,rows_checked=checked,variants=names,
                candidate_payloads_checked=archive_bytes,summary=data['summaries'],
                scope='First 12 frames per scene against frozen accepted references; probe summary is separate from v28 causal campaign results.')

def audit_runtime_campaign():
    runtime = ROOT/'experiments/python-game-runtime-v28-study'
    path = runtime/'results.json'
    data = load(path)
    if data.get('schema') != 'gamebub-runtime-v28':
        raise ValueError('runtime-v28 campaign schema')
    pins = _verify_pins(data.get('source_sha256'))
    old = load(UNIFIED/'results.json')
    standard = load(V24)
    input_data = _case_map(old)
    actual = _case_map(data)
    expected = {(scene,policy) for scene in ('mass-effect-2600','mass-effect-7200')
                for policy in ('exhaustive','sample4_refine2','sample2')}
    if actual.keys() != expected:
        raise ValueError('runtime-v28 campaign case matrix')
    old_causal = {(scene):input_data[(scene,'unified_causal')] for scene in ('mass-effect-2600','mass-effect-7200')}
    standard_input = {x['scene']:{r['id']:r['common_yuv420_u8_sha256'] for r in x['rows']}
                      for x in standard['inputs']}
    parsed_pairs=parsed_acks=candidate_objects=archive_objects=archive_bytes=0
    cap_rejects=quality_rejects=paid_attempts=paid_analyses=0
    comparisons={};reports=[];standard_reports={}
    spec=importlib.util.spec_from_file_location('audit_v28_runtime_motion_syntax',ROOT/'experiments/python-game-decoder-v27-study/model.py')
    decoder=importlib.util.module_from_spec(spec);sys.modules[spec.name]=decoder;spec.loader.exec_module(decoder)
    object_seen=set()
    for scene in ('mass-effect-2600','mass-effect-7200'):
        scene_cases={policy:actual[(scene,policy)] for policy in ('exhaustive','sample4_refine2','sample2')}
        oldcase=old_causal[scene]
        paired_hashes={}
        for policy,case in scene_cases.items():
            rows=case['rows']
            if len(rows)!=48 or [r['id'] for r in rows]!=list(range(48)):
                raise ValueError(f'{scene}/{policy} source IDs missing or reordered')
            prior_rows=oldcase['rows']
            totals=dict(body=0,base=0,hud=0,sse=0,samples=0,hud_errors=0,paid=0,service=0,receiver=0,ack=0,
                        attempts=0,analyses=0,sad=0,search_reads=0,selected_reads=0,cp02=0)
            max_body=0;capfit=0;attempt_count=0;analysis_count=0
            first_hashes=[]
            previous_base_tag=bytes(16);previous_hud_tag=bytes(16)
            for i,row in enumerate(rows):
                prior=prior_rows[i]
                key=(i%24==0)
                expected_base_reference_tag=previous_base_tag
                expected_hud_reference_tag=previous_hud_tag
                if row['key']!=key or row['reference_id'] != (NO_REF if key else i-1):
                    raise ValueError(f'{scene}/{policy}:{i} key/reference continuity')
                src_hash=row.get('source_common_yuv_sha256')
                if src_hash != standard_input[scene][i] or src_hash != prior['source_common_yuv_sha256']:
                    raise ValueError(f'{scene}/{policy}:{i} source image pairing differs')
                paired_hashes.setdefault(i,set()).add(src_hash)
                packet=read_object(row['packet'],runtime)
                base=read_object(row['base_packet'],runtime)
                hud=read_object(row['hud_packet'],runtime)
                ack=read_object(row['ack'],runtime)
                pair=parse_cp27(packet);ack_meta=parse_ja27(ack,pair)
                parsed_pairs+=1;parsed_acks+=1
                if (pair['epoch'],pair['frame'],pair['bytes']) != (25,i,len(packet)):
                    raise ValueError(f'{scene}/{policy}:{i} CP27 identity/body bytes')
                if pair['base']!=base or pair['hud']!=hud:
                    raise ValueError(f'{scene}/{policy}:{i} retained pair component mismatch')
                bm,hm=pair['base_meta'],pair['hud_meta']
                if (bm['epoch'],bm['frame'],bm['key'])!=(25,i,key):
                    raise ValueError(f'{scene}/{policy}:{i} GM27 profile/identity')
                if len(base)!=row['base_bytes'] or len(hud)!=row['hud_bytes'] or len(ack)!=65:
                    raise ValueError(f'{scene}/{policy}:{i} component/ACK length metadata')
                if (hm['epoch'],hm['frame'],hm['width'],hm['height'])!=(25,i,720,480) or hm['patch_words']!=HUD_WORDS:
                    raise ValueError(f'{scene}/{policy}:{i} exact current HUD profile/word count')
                if row['binding_bytes']!=60 or complete_body_bytes(len(base),len(hud),60)!=len(packet):
                    raise ValueError(f'{scene}/{policy}:{i} complete body reconciliation')
                if len(packet)>CAP or not row['body_bytes']==len(packet):
                    raise ValueError(f'{scene}/{policy}:{i} complete body cap/metadata')
                if (bm['reference_id'] != row['reference_id'] or hm['reference_id'] != row['reference_id']):
                    raise ValueError(f'{scene}/{policy}:{i} base/HUD reference IDs')
                if key:
                    if bm['reference_tag']!=bytes(16) or hm['reference_tag']!=bytes(16):
                        raise ValueError(f'{scene}/{policy}:{i} key carries a reference tag')
                elif bm['reference_tag']!=previous_base_tag or hm['reference_tag']!=previous_hud_tag:
                    raise ValueError(f'{scene}/{policy}:{i} source ref content tag does not follow selected prior frame')
                previous_base_tag=bm['reconstructed_tag'];previous_hud_tag=hm['out_tag']
                if row['source_slot']!=pair['source'] or row['destination_slot']!=pair['destination']:
                    raise ValueError(f'{scene}/{policy}:{i} bank metadata')
                expected_ack=dict(epoch=25,frame_id=i,source_slot=row['source_slot'],destination_slot=row['destination_slot'],
                                  published=True,pair_tag=pair['pair_tag'].hex(),base_tag=bm['reconstructed_tag'].hex(),hud_tag=hm['out_tag'].hex())
                if row['ack_meta']!=expected_ack or ack_meta['epoch']!=25 or ack_meta['frame']!=i:
                    raise ValueError(f'{scene}/{policy}:{i} JA27 actual/JSON binding')
                sse,samples,mse=quality_stats(row['hybrid'])
                if row['hybrid'].get('hud_word_errors')!=0:
                    raise ValueError(f'{scene}/{policy}:{i} exact HUD overlay error')
                if policy=='exhaustive':
                    if (packet != read_object(prior['packet'],UNIFIED)
                            or row['hybrid_rgb565_sha256']!=prior['hybrid_rgb565_sha256']
                            or row['reconstructed_tag']!=prior['reconstructed_tag']
                            or (sse,samples,mse)!=quality_stats(prior['hybrid'])):
                        raise ValueError(f'{scene}:{i} exhaustive optimized output differs from frozen v27')
                if row['reconstructed_tag']!=bm['reconstructed_tag'].hex():
                    raise ValueError(f'{scene}/{policy}:{i} reconstructed tag differs from GM27')
                attempts=row.get('attempts',[]);analyses=row.get('analyses',{})
                if not attempts or set(analyses)!=({'zero'} if key else {'zero','half32'}):
                    raise ValueError(f'{scene}/{policy}:{i} candidate or analysis inventory')
                zero_sse={}
                attempt_rows=[]
                for attempt in attempts:
                    cp=read_object(attempt['packet'],runtime);ab=read_object(attempt['base_packet'],runtime)
                    cm=parse_cp27(cp)
                    if (cm['base']!=ab or cm['hud']!=hud or cm['epoch']!=25 or cm['frame']!=i
                            or len(cp)!=attempt['complete_bytes'] or len(ab)!=attempt['base_bytes']):
                        raise ValueError(f'{scene}/{policy}:{i} candidate component association/size')
                    cbm,chm=cm['base_meta'],cm['hud_meta']
                    if (cbm['reference_id']!=row['reference_id'] or chm['reference_id']!=row['reference_id']
                            or chm['patch_words']!=HUD_WORDS or (cbm['width'],cbm['height'])!=(720,480)):
                        raise ValueError(f'{scene}/{policy}:{i} candidate reference/HUD geometry')
                    if key:
                        if cbm['reference_tag']!=bytes(16) or chm['reference_tag']!=bytes(16):
                            raise ValueError(f'{scene}/{policy}:{i} independent candidate key has reference tags')
                    elif cbm['reference_tag']!=expected_base_reference_tag or chm['reference_tag']!=expected_hud_reference_tag:
                        raise ValueError(f'{scene}/{policy}:{i} candidate uses a mismatched accepted reference')
                    if complete_body_bytes(len(ab),len(cm['hud']),60)!=len(cp):
                        raise ValueError(f'{scene}/{policy}:{i} candidate complete bytes do not sum')
                    fits=len(cp)<=CAP
                    if attempt['cap_fit'] is not fits:
                        raise ValueError(f'{scene}/{policy}:{i} candidate cap flag')
                    ass,ans,am=quality_stats(attempt['hybrid'])
                    if ans!=samples:
                        raise ValueError(f'{scene}/{policy}:{i} candidate active sample domain differs')
                    if attempt['kind']=='zero':zero_sse[attempt['background']]=ass
                    attempt_rows.append((attempt,cm,ass,ans,am,fits))
                    cap_rejects+=int(not fits);quality_rejects+=int(attempt.get('quality_eligible') is False)
                    candidate_objects+=1
                    for desc,blob in ((attempt['packet'],cp),(attempt['base_packet'],ab)):
                        key_obj=(desc.get('directory'),desc['path'],desc['stored_sha256'])
                        if key_obj not in object_seen: object_seen.add(key_obj);archive_objects+=1;archive_bytes+=len(blob)
                for attempt,cm,ass,ans,am,fits in attempt_rows:
                    eligible_quality=ass<=zero_sse[attempt['background']]
                    if attempt.get('quality_eligible') is not eligible_quality:
                        raise ValueError(f'{scene}/{policy}:{i} same-background zero-candidate SSE guard')
                    if attempt.get('selected') and not (fits and eligible_quality):
                        raise ValueError(f'{scene}/{policy}:{i} selected over-cap or quality-ineligible candidate')
                selected=[x for x in attempt_rows if x[0].get('selected')]
                if len(selected)!=1:
                    raise ValueError(f'{scene}/{policy}:{i} exactly-one selected attempt')
                chosen=selected[0][0]
                if (chosen['kind'],chosen['background'])!=(row['selected_kind'],row['selected_background']):
                    raise ValueError(f'{scene}/{policy}:{i} row selected mode/background mismatch')
                eligible=[x[0] for x in attempt_rows if x[0]['background']==chosen['background'] and x[5] and x[2]<=zero_sse[chosen['background']]]
                if not eligible or chosen['complete_bytes']!=min(x['complete_bytes'] for x in eligible):
                    raise ValueError(f'{scene}/{policy}:{i} not minimum actual eligible complete body')
                bgs=list(dict.fromkeys(a['background'] for a in attempts))
                if bgs not in ([16],[16,32]) or (bgs==[16,32] and any(x[5] and x[2]<=zero_sse.get(16,-1) for x in attempt_rows if x[0]['background']==16)):
                    raise ValueError(f'{scene}/{policy}:{i} declared coarse fallback ordering')
                paid=sum(float(a['analysis_wall_ms']) for a in analyses.values())+sum(float(a['encode_ms']) for a in attempts)
                if not math.isclose(float(row['paid_base_encode_ms']),paid,rel_tol=0,abs_tol=1e-7):
                    raise ValueError(f'{scene}/{policy}:{i} paid analysis plus all attempt encode timing')
                service=paid+sum(float(a['quality_ms'])+float(a['bind_ms']) for a in attempts)
                if not math.isclose(float(row['base_policy_service_ms']),service,rel_tol=0,abs_tol=1e-7):
                    raise ValueError(f'{scene}/{policy}:{i} policy service including losing quality/bind work')
                for kind,aw in analyses.items():
                    if int(aw.get('forward_plane_calls',0))!=3:
                        raise ValueError(f'{scene}/{policy}:{i} paid source-forward plane calls')
                    sw=aw.get('search',{})
                    totals['sad']+=int(sw.get('sad_sample_operations',0))
                    totals['search_reads']+=int(sw.get('reference_sample_fetches',0))
                    attempt_count+=0
                selected_attempt=selected[0]
                # Decode only the small GM27 motion-map syntax and verify the reported tap count.
                if key:
                    decoded_reads=0
                else:
                    selected_base=selected_attempt[1]['base']
                    fields=GM27.unpack_from(selected_base);nq,nv=int(fields[12]),int(fields[13])
                    offset=GM27.size+nq;mv=selected_base[offset:offset+nv]
                    grid_w=(720+31)//32;grid_h=(480+31)//32
                    vectors=decoder.unpack_vectors(mv,grid_w,grid_h)
                    taps_work=_tap_work_from_vectors(vectors,[(480,720),(240,360),(240,360)],32)
                    decoded_reads=taps_work['reference_sample_fetches']
                winner_work=selected_attempt[0]['work']
                if (winner_work.get('decoder_reference_sample_reads')!=decoded_reads
                        or winner_work.get('tap_work',{}).get('reference_sample_fetches')!=decoded_reads):
                    raise ValueError(f'{scene}/{policy}:{i} selected decoder logical tap count')
                totals['selected_reads']+=decoded_reads
                totals['body']+=len(packet);totals['base']+=len(base);totals['hud']+=len(hud)
                totals['sse']+=sse;totals['samples']+=samples;totals['hud_errors']+=row['hybrid']['hud_word_errors']
                totals['paid']+=paid;totals['service']+=service;totals['receiver']+=float(row['receive_ms']);totals['ack']+=float(row['ack_ms'])
                totals['attempts']+=len(attempts);totals['analyses']+=len(analyses);totals['cp02']+=sum(int(a['work'].get('actual_cp02_encode_calls',0)) for a in attempts)
                max_body=max(max_body,len(packet));capfit+=int(len(packet)<=CAP)
                for desc,blob in ((row['packet'],packet),(row['base_packet'],base),(row['hud_packet'],hud),(row['ack'],ack)):
                    key_obj=(desc.get('directory'),desc['path'],desc['stored_sha256'])
                    if key_obj not in object_seen:object_seen.add(key_obj);archive_objects+=1;archive_bytes+=len(blob)
            if any(len(v)!=1 for v in paired_hashes.values()):
                raise ValueError(f'{scene}/{policy} paired source hashes diverge')
            mse=totals['sse']/totals['samples']
            summary=case['summary']
            expected_summary=dict(frames=48,complete_bytes=totals['body'],coded_body_Mbps_at30=totals['body']*240/48/1e6,
                base_bytes=totals['base'],hud_bytes=totals['hud'],binding_bytes=48*60,maximum_complete_bytes=max_body,
                cap_fit_frames=capfit,active_squared_error=totals['sse'],active_channel_samples=totals['samples'],active_mse=mse,
                active_psnr_db=10*math.log10(65025/mse),hud_word_errors=totals['hud_errors'],exact_hud_words=48*HUD_WORDS,
                paid_candidate_encodes=totals['attempts'],paid_analyses=totals['analyses'],mean_paid_base_encode_ms=totals['paid']/48,
                mean_base_policy_service_ms=totals['service']/48,mean_receiver_ms=totals['receiver']/48,mean_ack_validation_ms=totals['ack']/48,
                sad_sample_operations=totals['sad'],search_reference_fetches=totals['search_reads'],selected_decoder_reference_fetches=totals['selected_reads'],
                selected_half32_frames=sum(r['selected_kind']=='half32' for r in rows),
                coarse_fallback_frames=[r['id'] for r in rows if r['selected_background']==32],
                actual_cp02_constructions=totals['cp02'],baseline_complete_bytes=oldcase['summary']['complete_bytes'],
                baseline_active_mse=oldcase['summary']['active_mse'],byte_ratio_to_v27=totals['body']/oldcase['summary']['complete_bytes'],
                mse_ratio_to_v27=mse/oldcase['summary']['active_mse'])
            diffs={k:(summary.get(k),v) for k,v in expected_summary.items()
                   if ((not close(summary.get(k),v,1e-12)) if isinstance(v,float) else summary.get(k)!=v)}
            if diffs:
                raise ValueError(f'{scene}/{policy} summary differs from rows: {diffs}')
            report=dict(scene=scene,policy=policy,summary=expected_summary,
                        selected_quality_relation_to_v27=('lower' if mse<oldcase['summary']['active_mse'] else 'equal' if mse==oldcase['summary']['active_mse'] else 'higher'),
                        all_paid_attempts=totals['attempts'],source_policy_service_ms_per_frame=totals['service']/48,
                        scope='Measured Python host work and actual retained CP27 bytes; nominal 30-ID/s rate is a projection.')
            reports.append(report)
        for i in range(48):
            if len({scene_cases[p]['rows'][i]['source_common_yuv_sha256'] for p in scene_cases})!=1:
                raise ValueError(f'{scene}:{i} source pixels not shared across policies')
        causal=scene_cases['sample4_refine2']
        hud_by_id={r['id']:r['hud_bytes'] for r in causal['rows']}
        standard_reports[scene]=_standard_rows(standard,(scene,'unified_causal'),hud_by_id,causal['summary']['active_mse'])
    # Read any retained candidate/archive descriptors not already visited, still with strict bounded inflate.
    for desc in _walk_objects(data):
        key_obj=(desc.get('directory'),desc['path'],desc['stored_sha256'])
        if key_obj not in object_seen:
            raw=read_object(desc,runtime);object_seen.add(key_obj);archive_objects+=1;archive_bytes+=len(raw)
    return dict(source_pins_verified=pins,cases=reports,standards_same_HU25=standard_reports,
                parsed_cp27_pairs=parsed_pairs,parsed_ja27_acks=parsed_acks,
                candidate_attempt_objects=candidate_objects,unique_archived_objects=archive_objects,
                unique_archived_raw_bytes=archive_bytes,cap_rejected_attempts=cap_rejects,
                quality_guard_rejected_attempts=quality_rejects,
                scope='Full-pixel replay remains attributed to the retained campaign verifier; this audit rechecks archive bytes, framing, source/reference lineage, exact SSE arithmetic and paid work.')

def build_audit() -> dict:
    taps = audit_taps_campaign()
    parity = audit_parity_campaign()
    search_probe = audit_search_probe()
    runtime_path=ROOT/'experiments/python-game-runtime-v28-study/results.json'
    runtime_campaign=None
    if runtime_path.is_file():
        runtime_data=load(runtime_path)
        if len(runtime_data.get('cases',[]))==6 and all(len(c.get('rows',[]))==48 for c in runtime_data['cases']):
            runtime_campaign=audit_runtime_campaign()
    if runtime_campaign is None:
        raise ValueError('full six-case v28 runtime campaign is not complete')
    frozen = load(ROOT/'experiments/python-game-unified-v27-study/results.json')
    frozen_cases = _case_map(frozen)
    primary = frozen_cases[('mass-effect-2600','unified_causal')]['summary']
    complex_scene = frozen_cases[('mass-effect-7200','unified_causal')]['summary']
    if (primary['complete_bytes'],primary['active_mse']) != (524016,14.058610039437585):
        raise ValueError('frozen primary unified_causal baseline differs from pinned v27')
    if (complex_scene['complete_bytes'],complex_scene['active_mse']) != (1195676,26.174528273129095):
        raise ValueError('frozen complex unified_causal baseline differs from pinned v27')
    inputs = [ROOT/'experiments/python-game-taps-v28-study/results.json',
              ROOT/'experiments/python-game-search-v28-study/results.json',
              ROOT/'experiments/python-game-unified-v27-study/results.json',
              ROOT/'experiments/python-game-runtime-v28-study/parity.json',
              ROOT/'experiments/python-game-runtime-v28-study/results.json',
              HERE/'audit.py',HERE/'test_audit.py',HERE/'AUDIT-CHECKLIST.md',HERE/'README.md',HERE/'tests.log',
              ROOT/'experiments/python-game-taps-v28-study/model.py',
              ROOT/'experiments/python-game-taps-v28-study/benchmark.py',
              ROOT/'experiments/python-game-taps-v28-study/test_model.py',
              ROOT/'experiments/python-game-search-v28-study/model.py',
              ROOT/'experiments/python-game-search-v28-study/benchmark.py',
              ROOT/'experiments/python-game-search-v28-study/test_model.py',
              ROOT/'experiments/python-game-runtime-v28-study/model.py',
              ROOT/'experiments/python-game-runtime-v28-study/protocol.py',
              ROOT/'experiments/python-game-runtime-v28-study/benchmark.py',
              ROOT/'experiments/python-game-runtime-v28-study/verify.py',
              ROOT/'experiments/python-game-runtime-v28-study/SCHEMA.md',
              ROOT/'experiments/python-game-unified-v27-study/model.py',
              ROOT/'experiments/python-game-unified-v27-study/protocol.py',
              ROOT/'experiments/python-game-decoder-v27-study/model.py',
              V24]
    return dict(schema='gamebub-independent-audit-v28',
                source_sha256=source_hashes(inputs,root=ROOT),
                taps=taps,
                lazy_encoder_parity=parity,
                search_probe=search_probe,
                runtime_campaign=runtime_campaign,
                baseline=dict(policy='unified_causal',primary_bytes=primary['complete_bytes'],
                              primary_mse=primary['active_mse'],complex_bytes=complex_scene['complete_bytes'],
                              complex_mse=complex_scene['active_mse']),
                profile=dict(width=720,height=480,active_height=405,hud_words_per_frame=21120,
                             complete_body_cap=49152,complete_binding_bytes=60,ack_bytes=65),
                scope=dict(decoder='Tap probe supplies a retained exact-packet replay report; this audit checks packet/reference/vector bindings and gathers, not pixels.',
                           rate='Nominal 30 source IDs/s projections are not measured native frame rates.',
                           native='HEVC/AV1 comparisons require actual access-unit bytes with current HU/CP overhead at measured operating points.'))
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
