#!/usr/bin/env python3
"""Independent Python-side arithmetic and provenance checks for v26 studies.

Decoder/pixel replay is evidence from the corresponding experiment verifier;
this module independently checks accounting, source lineage, archives, and
frozen comparison thresholds.  It does not prove native FPGA throughput.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import zlib

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
V25_AUDIT = ROOT / 'experiments/python-game-audit-v25-study/audit.json'
V24_RESULTS = ROOT / 'experiments/python-game-standard-v24-study/results.json'
COMBINED_V25_RESULTS = ROOT / 'experiments/python-game-combined-motion-v25-study/results.json'
COUNTER_RESULTS = ROOT / 'experiments/python-game-rdo-counter-v26-study/results.json'
PREDICTION_RESULTS = ROOT / 'experiments/python-game-prediction-v26-study/results.json'
ENTROPY_RESULTS = ROOT / 'experiments/python-game-entropy-v26-study/results.json'
PREDICTION_FULL_RESULTS = ROOT / 'experiments/python-game-prediction-v26-study/full_results.json'
COUNTER_ARCHIVE = ROOT / 'experiments/python-game-capped-key-v25-study'
IDS_PER_SECOND = 30
MAX_PACKET_BYTES = 49_152
HUD_WORDS = 21_120
CHANNELS_PER_ACTIVE_FRAME = 720 * 405 * 3
NO_REF = 0xFFFFFFFF


def projected_mbps(body_bytes: int, frames: int, ids_per_second: int = IDS_PER_SECOND) -> float:
    """Project complete body bytes at a nominal ID rate; this is not FPS."""
    if type(body_bytes) is not int or body_bytes < 0:
        raise ValueError('body bytes must be a nonnegative integer')
    if type(frames) is not int or frames <= 0:
        raise ValueError('frame count must be a positive integer')
    if type(ids_per_second) is not int or ids_per_second <= 0:
        raise ValueError('nominal ID rate must be a positive integer')
    return body_bytes * 8 * ids_per_second / frames / 1_000_000


def complete_body_bytes(components: dict[str, int]) -> int:
    """Sum declared per-frame body components, rejecting invalid accounting."""
    if not components or any(type(v) is not int or v < 0 for v in components.values()):
        raise ValueError('body components must be nonempty nonnegative integers')
    return sum(components.values())


def passes_frozen_pair(rate_mbps: float, mse: float, rate_limit: float, mse_limit: float) -> bool:
    """Both measured quantities must meet their exact retained thresholds."""
    values = (rate_mbps, mse, rate_limit, mse_limit)
    if any(not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0 for v in values):
        raise ValueError('rate and MSE values must be finite and nonnegative')
    return rate_mbps <= rate_limit and mse <= mse_limit


def enforce_packet_cap(packet_bytes: int, cap: int = MAX_PACKET_BYTES) -> bool:
    if type(packet_bytes) is not int or packet_bytes < 0 or type(cap) is not int or cap <= 0:
        raise ValueError('packet size and cap must be valid integers')
    return packet_bytes <= cap


def exact_hud_words(rectangles) -> int:
    """Count explicit non-overlapping (x,y,w,h) word rectangles."""
    checked, total = [], 0
    for rect in rectangles:
        if len(rect) != 4 or any(type(v) is not int for v in rect):
            raise ValueError('HUD rectangle must contain four integers')
        x, y, w, h = rect
        if min(x, y) < 0 or min(w, h) <= 0:
            raise ValueError('invalid HUD rectangle bounds')
        if any(x < ox + ow and ox < x + w and y < oy + oh and oy < y + h
               for ox, oy, ow, oh in checked):
            raise ValueError('HUD rectangles overlap')
        checked.append((x, y, w, h))
        total += w * h
    return total


def compare_lineage(old_rows, new_rows, *, allow_reference_change=False):
    """Require identical source IDs/hashes and disclose reference-tag changes."""
    def indexed(rows):
        out = {}
        for row in rows:
            fid = row.get('id')
            if type(fid) is not int or fid in out:
                raise ValueError('frame IDs must be unique integers')
            out[fid] = row
        return out
    old, new = indexed(old_rows), indexed(new_rows)
    if old.keys() != new.keys():
        raise ValueError('paired frame ID sets differ')
    changed = []
    for fid in sorted(old):
        if old[fid].get('source_sha256') != new[fid].get('source_sha256'):
            raise ValueError(f'source identity mismatch at frame {fid}')
        if old[fid].get('reference_id') != new[fid].get('reference_id'):
            changed.append(fid)
    if changed and not allow_reference_change:
        raise ValueError('reference lineage differs across compared rows')
    return changed


def read_object(desc, base_dir, *, max_raw_bytes=2_000_000):
    """Verify stored/raw hashes and lengths with bounded zlib decompression."""
    rel = Path(desc['path'])
    if rel.is_absolute() or '..' in rel.parts:
        raise ValueError('unsafe archive object path')
    stored = (Path(base_dir) / rel).read_bytes()
    if 'stored_bytes' in desc and len(stored) != int(desc['stored_bytes']):
        raise ValueError('stored object length mismatch')
    if hashlib.sha256(stored).hexdigest() != desc['stored_sha256']:
        raise ValueError('stored object hash mismatch')
    raw_len = int(desc['raw_bytes'])
    if raw_len < 0 or raw_len > max_raw_bytes:
        raise ValueError('raw object outside audit bound')
    dec = zlib.decompressobj()
    raw = dec.decompress(stored, raw_len + 1)
    if len(raw) != raw_len or not dec.eof or dec.unused_data or dec.unconsumed_tail:
        raise ValueError('invalid bounded zlib object')
    if hashlib.sha256(raw).hexdigest() != desc['raw_sha256']:
        raise ValueError('raw object hash mismatch')
    return raw


def read_descriptor(desc, default_dir):
    """Read a descriptor's declared archive root when present, otherwise default."""
    if 'directory' not in desc:
        return read_object(desc, default_dir)
    rel = Path(desc['directory'])
    if rel.is_absolute() or '..' in rel.parts:
        raise ValueError('unsafe archive directory')
    return read_object(desc, ROOT / rel)


def source_hashes(paths, root=ROOT):
    """Return deterministic repo-relative SHA-256 pins, excluding outputs."""
    pairs = []
    for path in paths:
        p = Path(path).resolve()
        rel = p.relative_to(Path(root).resolve()).as_posix()
        if rel == (HERE / 'audit.json').relative_to(ROOT).as_posix():
            continue
        pairs.append((rel, hashlib.sha256(p.read_bytes()).hexdigest()))
    return dict(sorted(pairs))


def verify_source_pins(pins, root=ROOT):
    """Verify repository-relative source snapshots carried by a result file."""
    if not isinstance(pins, dict) or not pins:
        raise ValueError('source pin map must be a nonempty object')
    for rel, expected in sorted(pins.items()):
        p = Path(rel)
        if p.is_absolute() or '..' in p.parts or len(expected) != 64:
            raise ValueError('unsafe path or invalid SHA-256 source pin')
        path = Path(root) / p
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f'source pin mismatch: {rel}')
    return len(pins)


def frozen_thresholds():
    """Read exact per-scene v25 threshold pairs from retained audit JSON."""
    audit = json.loads(V25_AUDIT.read_text())
    if audit.get('schema') != 'gamebub-independent-audit-v25':
        raise ValueError('unexpected frozen v25 audit schema')
    result = {}
    for case in audit['cases']:
        scene = case['scene']
        pair = (case['complete_body_rate_target_Mbps'], case['active_mse_target'])
        if scene in result and result[scene] != pair:
            raise ValueError(f'inconsistent frozen threshold pairs for {scene}')
        result[scene] = pair
    if not result:
        raise ValueError('frozen v25 threshold table is empty')
    return result


def _load_json(path):
    return json.loads(Path(path).read_text())


def _walk_objects(value):
    """Yield archive descriptors recursively without interpreting their data."""
    if isinstance(value, dict):
        if all(k in value for k in ('path', 'raw_bytes', 'raw_sha256', 'stored_sha256')):
            yield value
        else:
            for child in value.values():
                yield from _walk_objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_objects(child)


def _verify_result_objects(data, directory):
    seen = set()
    total_bytes = 0
    for desc in _walk_objects(data):
        key = (desc['path'], desc['stored_sha256'])
        if key in seen:
            continue
        seen.add(key)
        raw = read_descriptor(desc, directory)
        total_bytes += len(raw)
    return dict(unique_objects=len(seen), verified_raw_bytes=total_bytes)


def _check_counter(data, directory):
    if data.get('schema') != 'gamebub-rdo-counter-v26':
        raise ValueError('unexpected counter-v26 schema')
    rows = data['rows']
    by_scene = {}
    actual_attempts = logical_calls = logical_bytes = 0
    frozen_wall = fast_wall = frozen_rdo = fast_rdo = analysis_ms = 0.0
    for row in rows:
        scene, fid = row['scene'], row['id']
        if type(fid) is not int or fid < 0 or fid in by_scene.setdefault(scene, set()):
            raise ValueError('counter frame IDs are not unique integers')
        by_scene[scene].add(fid)
        if row['key'] != (fid % 24 == 0):
            raise ValueError('counter key IDs differ from frozen reference window')
        if row['key'] and row['reference_id'] != NO_REF:
            raise ValueError('counter key has a foreign reference ID')
        if not row['key'] and not 0 <= row['reference_id'] < fid:
            raise ValueError('counter reference ID is not a prior frame')
        analysis_ms += float(row['analysis_ms'])
        if not row['attempts']:
            raise ValueError('counter source row has no encoder attempts')
        for attempt in row['attempts']:
            actual_attempts += 1
            packet = read_object(attempt['packet'], directory)
            if len(packet) != attempt['packet_bytes'] or hashlib.sha256(packet).hexdigest() != attempt['packet_sha256']:
                raise ValueError('counter attempt packet bytes/hash mismatch')
            if attempt['packet_sha256'] != attempt['packet']['raw_sha256']:
                raise ValueError('counter attempt packet hash differs from archive descriptor')
            times, rdots = attempt['wall_ms'], attempt['rdo_ms']
            frozen_wall += float(times['frozen']); fast_wall += float(times['fast'])
            frozen_rdo += float(rdots['frozen']); fast_rdo += float(rdots['fast'])
            rdo = attempt['rdo']
            logical_calls += int(rdo['cp02_logical_probe_calls'])
            logical_bytes += int(rdo['cp02_logical_probe_bytes'])
            if int(rdo['cp02_probe_calls']) or int(rdo['cp02_probe_bytes']):
                raise ValueError('size-only counter unexpectedly constructed probe packets')
    if len(rows) != 96 or set(by_scene) != {'mass-effect-2600', 'mass-effect-7200'}:
        raise ValueError('counter study must retain 96 rows over two source windows')
    for scene, ids in by_scene.items():
        if ids != set(range(48)):
            raise ValueError(f'incomplete counter IDs for {scene}')
    summary, csummary = data['summary'], data['counter']
    if actual_attempts != summary['attempts']:
        raise ValueError('counter attempt count mismatch')
    if len(csummary['manifest']) != 8:
        raise ValueError('counter sample manifest should retain eight source planes')
    for sample in csummary['manifest']:
        indices = sample['indices']
        if indices != sorted(set(indices)) or any(type(i) is not int or not 0 <= i < 65536 for i in indices):
            raise ValueError('counter sample coefficient indices are malformed')
    exact_packet_bytes = int(csummary['exact_packet_bytes'])
    if exact_packet_bytes <= 0 or csummary['blocks'] != 4096 or len(csummary['sizes_sha256']) != 64:
        raise ValueError('counter aggregate size-vector evidence is malformed')
    if csummary['counter_constructed_packets'] != 0 or summary['actual_probe_packets'] != 0:
        raise ValueError('counter claims constructed probe packets')
    if not summary['all_packet_coefficient_reconstruction_equal'] or not summary['all_packet_bytes_equal_retained_v25']:
        raise ValueError('counter parity assertions are not all true')
    if logical_calls != summary['logical_probe_calls'] or logical_bytes != summary['logical_probe_bytes']:
        raise ValueError('counter logical probe totals mismatch')
    expected_totals = {
        'frozen': (frozen_wall, frozen_rdo, frozen_wall + frozen_rdo),
        'fast': (fast_wall, fast_rdo, fast_wall + fast_rdo),
    }
    for name, (wall, rdo, analysis_plus) in expected_totals.items():
        enc = summary[name]
        if abs(float(enc['total_encode_prepared_ms']) - wall) > 1e-6:
            raise ValueError(f'{name} prepared-encode time sum mismatch')
        if abs(float(enc['total_rdo_ms']) - rdo) > 1e-6:
            raise ValueError(f'{name} RDO time sum mismatch')
        if abs(float(enc['total_analysis_plus_attempts_ms']) - (analysis_ms + wall)) > 1e-5:
            raise ValueError(f'{name} analysis-plus-encode time sum mismatch')
    if abs(summary['encode_prepared_speedup'] - frozen_wall / fast_wall) > 1e-12:
        raise ValueError('counter prepared encode speedup arithmetic mismatch')
    if abs(summary['rdo_speedup'] - frozen_rdo / fast_rdo) > 1e-12:
        raise ValueError('counter RDO speedup arithmetic mismatch')
    samples = csummary['counter_ms']
    oracles = csummary['oracle_ms']
    if sorted(samples)[len(samples)//2] != csummary['counter_median_ms'] or sorted(oracles)[len(oracles)//2] != csummary['oracle_median_ms']:
        raise ValueError('counter timing median mismatch')
    if abs(csummary['speedup_median'] - csummary['oracle_median_ms'] / csummary['counter_median_ms']) > 1e-12:
        raise ValueError('counter median speedup arithmetic mismatch')
    return dict(rows=len(rows), attempts=actual_attempts, exact_isolated_packet_bytes=exact_packet_bytes,
                logical_probe_calls=logical_calls, logical_probe_bytes=logical_bytes,
                prepared_encode_speedup=summary['encode_prepared_speedup'],
                rdo_speedup=summary['rdo_speedup'], constructed_probe_packets=0)


def _check_prediction(data, directory):
    if data.get('schema') != 'gamebub-prediction-v26':
        raise ValueError('unexpected prediction-v26 schema')
    frames = int(data['frames_per_scene'])
    if frames != 12 or len(data['cases']) < 1:
        raise ValueError('prediction cohort size/schema mismatch')
    hud_rects = ((22, 54, 160, 24), (22, 82, 160, 24),
                 (168, 360, 320, 24), (168, 390, 240, 24))
    if exact_hud_words(hud_rects) != HUD_WORDS:
        raise ValueError('prediction HU25 geometry does not define exactly 21,120 words')
    identities, cases = {}, []
    for case in data['cases']:
        rows = case['rows']
        if len(rows) != frames or [r['id'] for r in rows] != list(range(frames)):
            raise ValueError('prediction cohort must retain ordered IDs 0..11')
        scene = case['scene']
        case_identity = []
        base_bytes = sse = samples = 0
        for row in rows:
            raw = read_object(row['base_packet'], directory)
            if len(raw) != row['base_bytes'] or len(raw) != row['work']['packet_bytes']:
                raise ValueError('prediction base packet byte mismatch')
            if len(raw) > MAX_PACKET_BYTES:
                raise ValueError('prediction base packet exceeds frozen CP cap')
            if row['reference_tag'] != row['work']['reference_tag'] or row['reference_tag'] != row['work']['analysis']['reference_tag']:
                raise ValueError('prediction row/work reference tags differ')
            if int(row['hybrid']['hud_word_errors']) != 0:
                raise ValueError('prediction exact-HUD profile has word errors')
            if int(row['hybrid']['active_channel_samples']) != CHANNELS_PER_ACTIVE_FRAME:
                raise ValueError('prediction per-row active sample count mismatch')
            if abs(float(row['hybrid']['active_mse']) - int(row['hybrid']['active_squared_error']) / CHANNELS_PER_ACTIVE_FRAME) > 1e-12:
                raise ValueError('prediction per-row MSE arithmetic mismatch')
            # The retained golden YUV is the variant's reconstruction, not the
            # common source frame; compare source IDs plus ACK-visible reference
            # ID/tag and use the result's common source-file pins.
            case_identity.append((row['id'], row['reference_id'], row['reference_tag']))
            base_bytes += len(raw)
            sse += int(row['hybrid']['active_squared_error'])
            samples += int(row['hybrid']['active_channel_samples'])
        key = (scene, case.get('kind'), case.get('variant'))
        identities.setdefault((scene, case.get('kind')), []).append((key, case_identity))
        summary = case['summary']
        if summary['frames'] != frames or summary['base_bytes'] != base_bytes:
            raise ValueError('prediction summary frame/byte sum mismatch')
        if abs(summary['base_Mbps_at30'] - projected_mbps(base_bytes, frames)) > 1e-12:
            raise ValueError('prediction nominal-30 body-rate projection mismatch')
        if summary['active_squared_error'] != sse or summary['active_channel_samples'] != samples:
            raise ValueError('prediction summary SSE/sample sum mismatch')
        if abs(summary['active_mse'] - sse / samples) > 1e-12:
            raise ValueError('prediction pooled MSE mismatch')
        cases.append(dict(scene=scene, kind=case.get('kind'), variant=case.get('variant'), frames=frames,
                          base_bytes=base_bytes, base_Mbps_at30=projected_mbps(base_bytes, frames),
                          active_mse=sse / samples, active_samples=samples,
                          exact_hud_words=frames * HUD_WORDS,
                          projected_rate_is_not_native_fps=True))
    lineage = []
    for (scene, kind), entries in identities.items():
        reference = entries[0][1]
        for key, value in entries[1:]:
            if [r[0] for r in value] != [r[0] for r in reference] or [r[1] for r in value] != [r[1] for r in reference]:
                raise ValueError(f'prediction variants differ in source IDs/reference IDs: {scene}/{kind}')
            tag_changes = [a[0] for a, b in zip(reference, value) if a[2] != b[2]]
            if kind == 'matched' and tag_changes:
                raise ValueError(f'matched prediction variants differ in ACKed reference tags: {scene}/{key[2]}')
            lineage.append(dict(scene=scene, kind=kind, variant=key[2],
                                reference_ids_identical=True, differing_reference_tag_ids=tag_changes,
                                reference_tags_paired=(len(tag_changes) == 0)))
    return dict(frames_per_scene=frames, cases=cases,
                lineage_comparisons=lineage,
                scope='12 retained frames per variant; base-only nominal rate and exact-HUD-associated MSE; no complete joint envelope or native FPS claim.')


def _standard_same_hud(scene, custom_mse, hud_rows, standards):
    if len(hud_rows) != 48:
        raise ValueError('standards same-HU25 projection requires 48 rows')
    hbytes = [int(r['hud_bytes']) for r in hud_rows]
    if any(int(r['binding_bytes']) != 60 for r in hud_rows):
        raise ValueError('CP26 envelope binding must remain 60 bytes/frame')
    report = {}
    for codec in ('libx265', 'libsvtav1'):
        eligible = []
        measured = []
        for case in standards['cases']:
            if case['scene'] != scene or case['codec'] != codec:
                continue
            if len(case['rows']) != 48:
                raise ValueError('frozen v24 standard row count mismatch')
            std_mse = float(case['summary']['hybrid']['active_mse'])
            projected_bytes = sum(int(r['coded_access_unit_bytes']) + hb + 60
                                  for r, hb in zip(case['rows'], hbytes))
            opt = dict(profile=case['profile'], hybrid_mse=std_mse,
                       same_HU25_complete_bytes=projected_bytes,
                       same_HU25_Mbps_at30=projected_mbps(projected_bytes, 48),
                       at_least_custom_measured_quality=std_mse <= custom_mse)
            measured.append(opt)
            if opt['at_least_custom_measured_quality']:
                eligible.append(opt)
        if not measured:
            raise ValueError(f'missing frozen v24 {codec} profiles for {scene}')
        report[codec] = dict(sampled_options=measured,
                             selected_same_HU25=min(eligible, key=lambda x: x['same_HU25_complete_bytes']) if eligible else None)
    return report


def _check_entropy(data, directory, standards, frozen_v25, thresholds):
    if data.get('schema') != 'gamebub-entropy-v26':
        raise ValueError('unexpected entropy-v26 schema')
    frozen_cases = {(c['scene'], c['profile']): c for c in frozen_v25['cases']}
    by_pair, case_reports = {}, []
    for case in data['cases']:
        scene, policy, rows = case['scene'], case['policy'], case['rows']
        if len(rows) != 48 or [r['id'] for r in rows] != list(range(48)):
            raise ValueError('entropy CP26 case must retain 48 ordered source IDs')
        if scene not in thresholds:
            raise ValueError(f'no frozen rate/MSE pair for {scene}')
        body = base_bytes = hud_bytes = binding = old_body = sse = samples = 0
        exact_hud = 0
        row_identity = []
        max_packet = 0
        for row in rows:
            bp = read_object(row['base_packet'], directory)
            hp = read_object(row['hud_packet'], directory)
            packet = read_object(row['packet'], directory)
            ack = read_object(row['ack'], directory)
            if len(bp) != row['base_bytes'] or len(hp) != row['hud_bytes']:
                raise ValueError('entropy inner packet byte mismatch')
            if row['binding_bytes'] != 60 or len(packet) != row['complete_bytes']:
                raise ValueError('entropy complete CP26 byte/binding mismatch')
            if len(packet) != len(bp) + len(hp) + 60:
                raise ValueError('entropy complete body composition mismatch')
            if len(packet) > MAX_PACKET_BYTES:
                raise ValueError('entropy accepted CP26 pair exceeds frozen cap')
            if len(ack) != 65:
                raise ValueError('JA26 ACK must be exactly 65 bytes')
            if zlib.crc32(packet[:-4]) != int.from_bytes(packet[-4:], 'little'):
                raise ValueError('CP26 outer CRC mismatch')
            if packet[:4] != b'CP26' or packet[4] != 1:
                raise ValueError('CP26 outer magic/version mismatch')
            flags = packet[5]
            epoch = int.from_bytes(packet[6:10], 'little')
            frame = int.from_bytes(packet[10:14], 'little')
            source_slot, dest_slot = packet[14], packet[15]
            nbase = int.from_bytes(packet[16:20], 'little')
            nhud = int.from_bytes(packet[20:24], 'little')
            if frame != row['id'] or epoch != 25 or nbase != len(bp) or nhud != len(hp):
                raise ValueError('CP26 outer identity/length header mismatch')
            if packet[24:40] != hashlib.sha256(bp).digest()[:16] or packet[40:56] != hashlib.sha256(hp).digest()[:16]:
                raise ValueError('CP26 inner packet digest binding mismatch')
            if packet[56:-4] != bp + hp:
                raise ValueError('CP26 body does not contain the archived inner packets')
            key = bool(flags & 1); publish = bool(flags & 2)
            if flags not in (0, 2, 3) or key != bool(row['key']) or key != (row['id'] % 24 == 0):
                raise ValueError('CP26 key/publish flag mismatch')
            if key:
                if source_slot != 255 or dest_slot != 0 or row['reference_id'] != NO_REF:
                    raise ValueError('CP26 key bank/reference identity mismatch')
            elif source_slot not in (0, 1) or dest_slot != (1 - source_slot if publish else 255):
                raise ValueError('CP26 predicted bank transition mismatch')
            if packet[-4:] != zlib.crc32(packet[:-4]).to_bytes(4, 'little'):
                raise ValueError('CP26 CRC mismatch')
            if ack[:4] != b'JA26' or ack[4] != 1 or ack[5:9] != epoch.to_bytes(4, 'little') or ack[9:13] != frame.to_bytes(4, 'little'):
                raise ValueError('JA26 identity binding mismatch')
            if ack[13:29] != hashlib.sha256(packet).digest()[:16]:
                raise ValueError('JA26 complete-pair digest mismatch')
            if ack[29:45].hex() != row['reconstructed_yuv_tag']:
                raise ValueError('JA26 reconstructed-base tag mismatch')
            if ack[45:61] != hp[38:54]:
                raise ValueError('JA26 reconstructed-HUD tag mismatch')
            if zlib.crc32(ack[:-4]) != int.from_bytes(ack[-4:], 'little'):
                raise ValueError('JA26 CRC mismatch')
            if int(row['hybrid']['hud_word_errors']) != 0:
                raise ValueError('entropy row has exact HUD word errors')
            active = row['hybrid']
            if int(active['active_channel_samples']) != CHANNELS_PER_ACTIVE_FRAME:
                raise ValueError('entropy per-row active sample count mismatch')
            if abs(float(active['active_mse']) - int(active['active_squared_error']) / CHANNELS_PER_ACTIVE_FRAME) > 1e-12:
                raise ValueError('entropy per-row MSE arithmetic mismatch')
            baseline_profile = row['baseline_case_profile']
            baseline_case = frozen_cases.get((scene, baseline_profile))
            if baseline_case is None:
                raise ValueError(f'missing frozen v25 baseline case {scene}/{baseline_profile}')
            baseline_row = baseline_case['rows'][row['id']]
            if (row['reference_id'] != baseline_row['reference_id']
                    or row['hud_packet']['raw_sha256'] != baseline_row['hud_packet']['raw_sha256']
                    or row['old_base_bytes'] != baseline_row['base_bytes']
                    or row['old_complete_bytes'] != baseline_row['body_bytes']
                    or row['hud_bytes'] != baseline_row['hud_bytes']
                    or row['hybrid_rgb565_sha256'] != baseline_row['hybrid_rgb565_sha256']
                    or row['reconstructed_yuv_tag'] != baseline_row['reconstructed_yuv_tag']
                    or active['active_squared_error'] != baseline_row['hybrid']['active_squared_error']
                    or active['active_channel_samples'] != baseline_row['hybrid']['active_channel_samples']
                    or active['hud_word_errors'] != baseline_row['hybrid']['hud_word_errors']):
                raise ValueError('entropy result did not retain exact frozen v25 quality/HUD/reference row')
            row_identity.append((row['id'], row['source_common_yuv_sha256'], row['reference_id'],
                                 hashlib.sha256(hp).hexdigest(), row['reconstructed_yuv_tag'],
                                 row['hybrid_rgb565_sha256']))
            body += len(packet); base_bytes += len(bp); hud_bytes += len(hp); binding += 60
            old_body += int(row['old_complete_bytes'])
            sse += int(active['active_squared_error']); samples += int(active['active_channel_samples'])
            exact_hud += HUD_WORDS; max_packet = max(max_packet, len(packet))
        by_pair.setdefault(scene, []).append((policy, row_identity))
        summary = case['summary']
        computed = dict(complete_bytes=body, base_bytes=base_bytes, hud_bytes=hud_bytes,
                        binding_bytes=binding, old_complete_bytes=old_body,
                        active_squared_error=sse, active_channel_samples=samples,
                        maximum_complete_bytes=max_packet, cap_fit_frames=48,
                        exact_hud_words=exact_hud, hud_word_errors=0)
        for field, value in computed.items():
            if summary.get(field) != value:
                raise ValueError(f'entropy {field} sum mismatch for {scene}/{policy}')
        rate = projected_mbps(body, 48)
        old_rate = projected_mbps(old_body, 48)
        mse = sse / samples
        if abs(summary['coded_body_Mbps_at30'] - rate) > 1e-12 or abs(summary['old_body_Mbps_at30'] - old_rate) > 1e-12:
            raise ValueError('entropy nominal-30 complete-body rate mismatch')
        if abs(summary['active_mse'] - mse) > 1e-12:
            raise ValueError('entropy pooled active MSE mismatch')
        frozen_rate, frozen_mse = thresholds[scene]
        same_hud = _standard_same_hud(scene, mse, rows, standards)
        case_reports.append(dict(scene=scene, policy=policy, frames=48, complete_bytes=body,
                                 body_Mbps_at30=rate, base_bytes=base_bytes, hud_bytes=hud_bytes,
                                 binding_bytes=binding, maximum_complete_bytes=max_packet,
                                 exact_hud_words=exact_hud, active_squared_error=sse,
                                 active_channel_samples=samples, active_mse=mse,
                                 frozen_v25_HEVC_rate_Mbps=frozen_rate,
                                 frozen_v25_HEVC_active_mse=frozen_mse,
                                 meets_frozen_v25_rate_and_MSE_pair=passes_frozen_pair(rate, mse, frozen_rate, frozen_mse),
                                 standards_same_HU25=same_hud))
    for scene, variants in by_pair.items():
        base_identity = variants[0][1]
        if any(identity != base_identity for _, identity in variants[1:]):
            raise ValueError(f'entropy layouts differ in source/reference/HUD/output lineage for {scene}')
    if sum(x['summary']['frames'] for x in data['cases']) != data['counts']['accepted_pairs']:
        raise ValueError('entropy accepted-pair count mismatch')
    if data['counts']['accepted_pairs'] != 192:
        raise ValueError('entropy result must retain 192 reused CP26 decisions')
    return dict(cases=case_reports, accepted_pairs=data['counts']['accepted_pairs'],
                source_ids_per_window=48, unique_source_frames=data['counts']['unique_source_frames'],
                exact_hud_words=data['counts']['exact_hud_words'],
                rate_interpretation='nominal 30 source IDs/s projection; not native FPS or new captures')


def _check_fractional_full(data, directory, frozen_v25, thresholds):
    """Check actual CP2F candidates/selection arithmetic without decoding pixels."""
    if data.get('schema') != 'gamebub-fractional-full-v26':
        raise ValueError('unexpected fractional full-window schema')
    frozen_cases = {(c['scene'], c['profile']): c for c in frozen_v25['cases']}
    reports = []
    for case in data['cases']:
        scene, rows = case['scene'], case['rows']
        if len(rows) != 48 or [r['id'] for r in rows] != list(range(48)):
            raise ValueError('full prediction case must retain 48 ordered IDs')
        baseline = frozen_cases.get((scene, 'capped_key_zero_rdo1'))
        if baseline is None:
            raise ValueError(f'missing frozen v25 paired baseline for {scene}')
        body = base_bytes = hud_bytes = binding = sse = samples = 0
        max_body = cap_fit = ack_bytes = selected_half = selected_zero = 0
        all_attempts = rejected_cap_attempts = gate_failures = analyses_paid = 0
        fallback_frames = []
        prior_tag, slot = None, 0
        for row, oldrow in zip(rows, baseline['rows']):
            fid = row['id']
            if row['key'] != (fid % 24 == 0):
                raise ValueError('CP2F full-window key schedule mismatch')
            if row['reference_id'] != oldrow['reference_id']:
                raise ValueError('CP2F source frame/reference ID pairing mismatch vs frozen cohort')
            if row['hud_packet']['raw_sha256'] != oldrow['hud_packet']['raw_sha256'] or row['hud_bytes'] != oldrow['hud_bytes']:
                raise ValueError('CP2F reused HUD object/byte count differs from frozen HU25 row')
            hud = read_descriptor(row['hud_packet'], directory)
            if len(hud) != row['hud_bytes']:
                raise ValueError('CP2F HUD object byte length mismatch')
            if row['key']:
                if row['reference_id'] != NO_REF or row['source_slot'] != 255 or row['destination_slot'] != 0:
                    raise ValueError('CP2F key slot/reference identity mismatch')
            else:
                expected_ref = fid - 1
                if row['reference_id'] != expected_ref or row['source_slot'] != slot:
                    raise ValueError('CP2F does not use last accepted frame/bank')
                if row['analyses'][row['selected_kind']]['reference_tag'] != prior_tag:
                    raise ValueError('CP2F candidate analysis has a foreign reconstructed reference tag')
                if row['destination_slot'] != 1 - slot:
                    raise ValueError('CP2F accepted nonkey did not publish to opposite slot')
            attempts = row['attempts']
            if not attempts:
                raise ValueError('CP2F row has no paid candidates')
            all_attempts += len(attempts)
            groups = {}
            for attempt in attempts:
                bp = read_descriptor(attempt['base_packet'], directory)
                pkt = read_descriptor(attempt['packet'], directory)
                nbase, ncomplete = len(bp), len(pkt)
                if nbase != attempt['base_bytes'] or ncomplete != attempt['complete_bytes']:
                    raise ValueError('CP2F candidate packet length differs from retained accounting')
                if ncomplete != nbase + len(hud) + 60:
                    raise ValueError('CP2F candidate body omits HUD/binding bytes')
                if attempt['cap_fit'] != (ncomplete <= MAX_PACKET_BYTES):
                    raise ValueError('CP2F candidate cap flag mismatch')
                if pkt[:4] != b'CP2F' or pkt[4] != 1 or zlib.crc32(pkt[:-4]) != int.from_bytes(pkt[-4:], 'little'):
                    raise ValueError('CP2F candidate header/CRC mismatch')
                pair_flags = pkt[5]
                pair_epoch = int.from_bytes(pkt[6:10], 'little')
                pair_frame = int.from_bytes(pkt[10:14], 'little')
                pair_source, pair_dest = pkt[14], pkt[15]
                expected_flags = (1 if row['key'] else 0) | (2 if (row['key'] or row['id'] < 48) else 0)
                if (pair_flags != expected_flags or pair_epoch != 25 or pair_frame != fid
                        or pair_source != row['source_slot'] or pair_dest != row['destination_slot']):
                    raise ValueError('CP2F row/header flags, ID, epoch, or bank tags mismatch')
                if int.from_bytes(pkt[16:20], 'little') != nbase or int.from_bytes(pkt[20:24], 'little') != len(hud):
                    raise ValueError('CP2F candidate inner length header mismatch')
                if pkt[24:40] != hashlib.sha256(bp).digest()[:16] or pkt[40:56] != hashlib.sha256(hud).digest()[:16]:
                    raise ValueError('CP2F candidate inner SHA binding mismatch')
                if pkt[56:-4] != bp + hud:
                    raise ValueError('CP2F candidate body differs from retained components')
                metrics = attempt['hybrid']
                if int(metrics['active_channel_samples']) != CHANNELS_PER_ACTIVE_FRAME:
                    raise ValueError('CP2F candidate active sample count mismatch')
                if abs(float(metrics['active_mse']) - int(metrics['active_squared_error']) / CHANNELS_PER_ACTIVE_FRAME) > 1e-12:
                    raise ValueError('CP2F candidate MSE arithmetic mismatch')
                groups.setdefault(int(attempt['background']), []).append((attempt, bp, pkt))
                if not attempt['cap_fit']:
                    rejected_cap_attempts += 1
            # For every background, the half32 decision is gated by the exact
            # same-frame zero SSE, and zero itself remains the quality anchor.
            for background, options in groups.items():
                zero = next((a for a, _, _ in options if a['kind'] == 'zero'), None)
                if zero is None:
                    raise ValueError('CP2F candidate group has no zero quality anchor')
                zero_sse = int(zero['hybrid']['active_squared_error'])
                for attempt, _, _ in options:
                    should_qualify = (attempt['kind'] == 'zero'
                                      or int(attempt['hybrid']['active_squared_error']) <= zero_sse)
                    if bool(attempt['quality_eligible']) != should_qualify:
                        raise ValueError('CP2F same-reference zero-SSE quality gate mismatch')
                    if attempt['kind'] == 'half32' and not should_qualify:
                        gate_failures += 1
            eligible_groups = []
            for background in sorted(groups):
                eligible = [(a, bp, pkt) for a, bp, pkt in groups[background]
                            if a['cap_fit'] and a['quality_eligible']]
                if eligible:
                    eligible_groups = eligible
                    break
            if not eligible_groups:
                raise ValueError('CP2F row has no cap-fit quality-eligible candidate')
            expected_choice = min(eligible_groups, key=lambda item: item[0]['complete_bytes'])
            selected_attempt = next((a, bp, pkt) for a, bp, pkt in eligible_groups if a['selected']) if any(a['selected'] for a, _, _ in eligible_groups) else None
            if selected_attempt is None or selected_attempt != expected_choice:
                raise ValueError('CP2F selection did not choose minimum-byte eligible candidate at first viable background')
            chosen, bp, pkt = selected_attempt
            if sum(bool(a['selected']) for a, _, _ in [*[(x, y, z) for vals in groups.values() for x, y, z in vals]]) != 1:
                raise ValueError('CP2F exactly-one-selected candidate invariant failed')
            if row['selected_kind'] != chosen['kind'] or row['selected_background'] != chosen['background']:
                raise ValueError('CP2F selected summary identity differs from paid attempt')
            if row['base_packet']['raw_sha256'] != chosen['base_packet']['raw_sha256'] or row['packet']['raw_sha256'] != chosen['packet']['raw_sha256']:
                raise ValueError('CP2F selected bytes differ from candidate archive')
            if row['body_bytes'] != len(pkt) or row['base_bytes'] != len(bp) or row['hud_bytes'] != len(hud) or row['binding_bytes'] != 60:
                raise ValueError('CP2F selected row byte accounting mismatch')
            if len(pkt) > MAX_PACKET_BYTES:
                raise ValueError('CP2F selected pair exceeds frozen cap')
            if row['ack']['raw_bytes'] != 65:
                raise ValueError('JA2F descriptor does not declare exact 65 bytes')
            ack = read_descriptor(row['ack'], directory)
            if len(ack) != 65 or ack[:4] != b'JA2F' or ack[4] != 1:
                raise ValueError('JA2F packet size/magic/version mismatch')
            if zlib.crc32(ack[:-4]) != int.from_bytes(ack[-4:], 'little'):
                raise ValueError('JA2F CRC mismatch')
            epoch = int.from_bytes(pkt[6:10], 'little')
            if ack[5:9] != epoch.to_bytes(4, 'little') or ack[9:13] != fid.to_bytes(4, 'little'):
                raise ValueError('JA2F frame/epoch identity mismatch')
            if ack[13:29] != hashlib.sha256(pkt).digest()[:16] or ack[29:45].hex() != row['reconstructed_tag'] or ack[45:61] != hud[38:54]:
                raise ValueError('JA2F digest/base/HUD tag binding mismatch')
            if row['ack_meta']['pair_tag'] != ack[13:29].hex() or row['ack_meta']['base_tag'] != row['reconstructed_tag'] or row['ack_meta']['hud_tag'] != ack[45:61].hex():
                raise ValueError('JA2F retained metadata differs from actual ACK bytes')
            active = row['hybrid']
            if active['hud_word_errors'] != 0 or int(active['active_channel_samples']) != CHANNELS_PER_ACTIVE_FRAME:
                raise ValueError('CP2F selected row has HUD or sample-count errors')
            if abs(float(active['active_mse']) - int(active['active_squared_error']) / CHANNELS_PER_ACTIVE_FRAME) > 1e-12:
                raise ValueError('CP2F selected row MSE arithmetic mismatch')
            # Root's full verifier owns pixel equality.  Here the retained hashes
            # must at least agree with selected-attempt metadata and ACK tags.
            if row['hybrid_rgb565_sha256'] != chosen['hybrid_rgb565_sha256'] or row['reconstructed_tag'] != chosen['reconstructed_tag']:
                raise ValueError('CP2F selected output/hash/tag differs from candidate record')
            if row['key']:
                prior_tag, slot = row['reconstructed_tag'], 0
            else:
                prior_tag, slot = row['reconstructed_tag'], 1 - slot
            body += len(pkt); base_bytes += len(bp); hud_bytes += len(hud); binding += 60
            sse += int(active['active_squared_error']); samples += int(active['active_channel_samples'])
            max_body = max(max_body, len(pkt)); cap_fit += int(len(pkt) <= MAX_PACKET_BYTES)
            ack_bytes += len(ack); selected_half += int(chosen['kind'] == 'half32'); selected_zero += int(chosen['kind'] == 'zero')
            analyses_paid += len(row['analyses'])
            if len(groups) > 1:
                fallback_frames.append(fid)
        summary = case['summary']
        values = dict(frames=48, complete_bytes=body, base_bytes=base_bytes, hud_bytes=hud_bytes,
                      binding_bytes=binding, max_complete_bytes=max_body, cap_fit_frames=cap_fit,
                      active_squared_error=sse, active_channel_samples=samples,
                      hud_word_errors=0, selected_half32_frames=selected_half,
                      selected_zero_frames=selected_zero, rejected_cap_attempts=rejected_cap_attempts,
                      causal_quality_gate_failures=gate_failures, coarse_fallback_frames=fallback_frames,
                      ack_bytes=ack_bytes)
        for field, value in values.items():
            if summary.get(field) != value:
                raise ValueError(f'CP2F {field} accounting mismatch for {scene}')
        if summary['paid_candidate_encodes'] != all_attempts or summary['paid_analyses'] != analyses_paid:
            raise ValueError('CP2F paid-candidate work counts do not include all attempts')
        rate, mse = projected_mbps(body, 48), sse / samples
        if abs(summary['coded_body_Mbps_at30'] - rate) > 1e-12 or abs(summary['active_mse'] - mse) > 1e-12:
            raise ValueError('CP2F complete-body rate or pooled MSE mismatch')
        if summary['frozen_v25_complete_bytes'] != baseline['summary']['complete_bytes'] or summary['frozen_v25_active_mse'] != baseline['summary']['active_mse']:
            raise ValueError('CP2F paired v25 baseline thresholds changed')
        if summary['at_least_frozen_v25_aggregate_quality'] != (mse <= baseline['summary']['active_mse']):
            raise ValueError('CP2F old-custom-quality comparison mismatch')
        frozen_rate, frozen_mse = thresholds[scene]
        reports.append(dict(scene=scene, frames=48, complete_bytes=body, body_Mbps_at30=rate,
                            base_bytes=base_bytes, hud_bytes=hud_bytes, binding_bytes=binding,
                            maximum_complete_bytes=max_body, exact_hud_words=48*HUD_WORDS,
                            active_squared_error=sse, active_channel_samples=samples, active_mse=mse,
                            selected_half32_frames=selected_half, selected_zero_frames=selected_zero,
                            paid_candidate_encodes=all_attempts, rejected_cap_attempts=rejected_cap_attempts,
                            coarse_fallback_frames=fallback_frames,
                            old_custom_quality_met=(mse <= baseline['summary']['active_mse']),
                            old_custom_quality_mse=baseline['summary']['active_mse'],
                            frozen_v25_HEVC_rate_Mbps=frozen_rate, frozen_v25_HEVC_active_mse=frozen_mse,
                            meets_frozen_v25_rate_and_MSE_pair=passes_frozen_pair(rate, mse, frozen_rate, frozen_mse),
                            projected_rate_is_not_native_fps=True))
    return dict(cases=reports, scope='Two reused 48-frame windows; per-frame chosen CP2F candidate accounting and SSE gate checked; pixel replay is separate.',
                physical_30fps_proven=False)


def run_check():
    """Audit frozen v26 component results without replaying codec pixels."""
    counter = _load_json(COUNTER_RESULTS)
    prediction = _load_json(PREDICTION_RESULTS)
    prediction_full = _load_json(PREDICTION_FULL_RESULTS)
    entropy = _load_json(ENTROPY_RESULTS)
    standards = _load_json(V24_RESULTS)
    if standards.get('schema') != 'gamebub-standard-compare-v24':
        raise ValueError('unexpected frozen v24 standards schema')
    thresholds = frozen_thresholds()
    v25audit = _load_json(V25_AUDIT)
    verify_source_pins(v25audit['source_sha256'])
    verify_source_pins(counter['source_sha256'])
    verify_source_pins(prediction['source_sha256'])
    verify_source_pins(prediction_full['source_sha256'])
    verify_source_pins(entropy['source_sha256'])
    object_reports = {
        # Counter rows intentionally point to immutable v25 packet blobs rather
        # than making duplicate objects in the v26 study directory.
        'counter': _verify_result_objects(counter, COUNTER_ARCHIVE),
        'prediction': _verify_result_objects(prediction, PREDICTION_RESULTS.parent),
        'prediction_full': _verify_result_objects(prediction_full, PREDICTION_FULL_RESULTS.parent),
        'entropy': _verify_result_objects(entropy, ENTROPY_RESULTS.parent),
    }
    counter_report = _check_counter(counter, COUNTER_ARCHIVE)
    prediction_report = _check_prediction(prediction, PREDICTION_RESULTS.parent)
    frozen_v25 = _load_json(COMBINED_V25_RESULTS)
    if frozen_v25.get('schema') != 'gamebub-combined-motion-v25':
        raise ValueError('unexpected frozen v25 combined baseline schema')
    entropy_report = _check_entropy(entropy, ENTROPY_RESULTS.parent, standards, frozen_v25, thresholds)
    prediction_full_report = _check_fractional_full(prediction_full, PREDICTION_FULL_RESULTS.parent,
                                                     frozen_v25, thresholds)
    source_map = {}
    for result_path, data in ((COUNTER_RESULTS, counter), (PREDICTION_RESULTS, prediction),
                              (PREDICTION_FULL_RESULTS, prediction_full), (ENTROPY_RESULTS, entropy)):
        for rel, sha in data['source_sha256'].items():
            if rel in source_map and source_map[rel] != sha:
                raise ValueError(f'inconsistent source pin across v26 components: {rel}')
            source_map[rel] = sha
        rel = result_path.relative_to(ROOT).as_posix()
        source_map[rel] = hashlib.sha256(result_path.read_bytes()).hexdigest()
        extras = [result_path.parent / 'verify.py', result_path.parent / 'verify.log',
                  result_path.parent / 'run.log', result_path.parent / 'tests.log']
        if result_path == PREDICTION_FULL_RESULTS:
            extras.extend((result_path.parent / 'full_verify.py', result_path.parent / 'full_verify.log',
                           result_path.parent / 'full_tests.log', result_path.parent / 'full_run.log'))
        for extra in extras:
            if extra.is_file():
                source_map[extra.relative_to(ROOT).as_posix()] = hashlib.sha256(extra.read_bytes()).hexdigest()
    for p in (V25_AUDIT, V24_RESULTS, COMBINED_V25_RESULTS, HERE / 'audit.py', HERE / 'test_audit.py', HERE / 'AUDIT-CHECKLIST.md'):
        source_map[p.relative_to(ROOT).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    if hashlib.sha256(V24_RESULTS.read_bytes()).hexdigest() != v25audit['source_sha256'].get(V24_RESULTS.relative_to(ROOT).as_posix()):
        raise ValueError('frozen v25 audit does not pin current v24 thresholds')
    verify_source_pins(source_map)
    return dict(schema='gamebub-independent-audit-v26', source_sha256=dict(sorted(source_map.items())),
                source_pin_count=len(source_map), verified_objects=object_reports,
                frozen_threshold_source='v25 independent audit JSON, pinned to v24 measured standards JSON',
                counter=counter_report, prediction=prediction_report,
                prediction_full=prediction_full_report, entropy=entropy_report,
                decoder_evidence='Separate experiment verifier logs are source-pinned; audit does not repeat full decode/pixel replay.',
                hardware_scope='Python offline artifacts only; no native FPGA throughput or physical 30 FPS proof.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if not args.check:
        parser.error('use --check')
    result = run_check()
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n'
    (HERE / 'audit.json').write_text(rendered)
    print('v26 arithmetic/provenance audit passed')


if __name__ == '__main__':
    main()
