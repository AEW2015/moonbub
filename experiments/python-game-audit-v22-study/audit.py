#!/usr/bin/env python3
"""Independent v22 packet, quality, and complete-byte audit."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import re
import struct
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
ROOT = HERE.parents[1]
JOINT = EXP / 'python-game-joint-commit-study'
GAP = EXP / 'python-game-gap-span-study'
OLD = EXP / 'python-game-mandatory-hud-study'
CACHE = EXP / 'python-game-hud-cache-study'
COMPOSE = EXP / 'python-game-display-compose-study'
FRAME_CAP = 49152
PAIR_HEADER = struct.Struct('<4sBIIII16s16s')
PAIR_OVERHEAD = PAIR_HEADER.size + 4
HC21_OVERHEAD = 83


def read(path):
    return json.loads(Path(path).read_text())


def sha(data):
    return hashlib.sha256(data).hexdigest()


def sha_file(path):
    return sha(Path(path).read_bytes())


def close(a, b, tol=1e-10):
    return math.isclose(float(a), float(b), rel_tol=tol, abs_tol=tol)


def verify_pins(data, folder):
    pins = data['source_sha256']
    for rel, expected in pins.items():
        path = (ROOT / rel).resolve()
        if not path.is_file() or sha_file(path) != expected:
            raise AssertionError(f'source pin mismatch: {rel}')
    return len(pins)


def test_count(path, expected):
    s = Path(path).read_text()
    m = re.search(r'^Ran (\d+) tests? in ', s, re.M)
    if not m or int(m.group(1)) != expected or not s.rstrip().endswith('OK'):
        raise AssertionError(f'test log mismatch: {path}')
    return int(m.group(1))


def load_blob(desc, folder):
    path = Path(desc['path'])
    if path.is_absolute() or '..' in path.parts:
        raise AssertionError('unsafe artifact path')
    stored = (folder / path).read_bytes()
    if sha(stored) != desc['stored_sha256']:
        raise AssertionError(f'stored object SHA mismatch: {path}')
    dec = zlib.decompressobj()
    raw = dec.decompress(stored, int(desc['raw_bytes']) + 1)
    if (not dec.eof or dec.unconsumed_tail or dec.unused_data
            or len(raw) != desc['raw_bytes'] or sha(raw) != desc['raw_sha256']):
        raise AssertionError(f'bounded object decode mismatch: {path}')
    return raw


def parse_pair(packet):
    if len(packet) < PAIR_OVERHEAD or len(packet) > FRAME_CAP:
        raise AssertionError('complete pair cap/length')
    if zlib.crc32(packet[:-4]) != struct.unpack_from('<I', packet, len(packet)-4)[0]:
        raise AssertionError('outer pair CRC')
    magic, ver, epoch, frame, nb, nh, bh, hh = PAIR_HEADER.unpack_from(packet)
    if magic != b'CB21' or ver != 1 or len(packet) != PAIR_OVERHEAD + nb + nh:
        raise AssertionError('pair envelope shape')
    base = packet[PAIR_HEADER.size:PAIR_HEADER.size+nb]
    hud = packet[PAIR_HEADER.size+nb:-4]
    if (hashlib.sha256(base).digest()[:16] != bh
            or hashlib.sha256(hud).digest()[:16] != hh):
        raise AssertionError('pair component binding')
    return epoch, frame, base, hud


def verifier_summary(path):
    data = read(path)
    physical = data.get('physical_30fps_proven', data.get('physical_dma_or_30fps_proven'))
    if physical is not False:
        raise AssertionError(f'unsupported cadence proof in {path}')
    return data


def build_audit():
    joint = read(JOINT / 'results.json')
    gap = read(GAP / 'results.json')
    projection = read(JOINT / 'analysis.json')
    old = read(OLD / 'results.json')
    old_cache = read(CACHE / 'results.json')
    old_compose = read(COMPOSE / 'results.json')
    if joint.get('schema') != 'gamebub-joint-commit-v22' or gap.get('schema') != 'gamebub-gap-span-v22':
        raise AssertionError('unexpected v22 schema')
    if projection.get('schema') != 'gamebub-v22-combined-projection':
        raise AssertionError('unexpected projection schema')
    pins = dict(joint=verify_pins(joint, ROOT), gap=verify_pins(gap, ROOT),
                projection=verify_pins(projection, ROOT))
    tests = dict(joint=test_count(JOINT/'tests.log', 21), gap=test_count(GAP/'tests.log', 10))
    jverify = verifier_summary(JOINT/'verify.log')
    gverify = verifier_summary(GAP/'verify.log')
    if (jverify.get('actual_joint_decisions'), jverify.get('exact_original_hud_words'),
            jverify.get('crc_negative_rejections'), jverify.get('synchronous_joint_publication_implemented')) != (192, 4055040, 192, True):
        raise AssertionError('joint retained replay totals')
    if (gverify.get('patch_decisions'), gverify.get('updates'), gverify.get('independent_scalar_words'),
            gverify.get('crc_negatives')) != (528, 132, 2787840, len(gap.get('goldens', []))):
        raise AssertionError('HD22 scalar replay totals')

    old_mandatory = {c['scene']: c for c in old['cases'] if c['policy'] == 'mandatory'}
    old_cached = {c['name']: c for c in old_cache['cases']}
    old_budget = {c['scene']: c for c in old_compose['budgets']}
    joint_cases = {(c['scene'], c['policy']): c for c in joint['cases']}
    gap_cases = {c['name']: c for c in gap['cases']}
    proj_cases = {c['scene']: c for c in projection['cases']}
    profile_results = []
    gap_results = []
    packet_decodes = 0
    for scene in ('mass-effect-2600', 'mass-effect-7200'):
        fixed = joint_cases[(scene, 'fixed_v20_profiles')]
        adaptive = joint_cases[(scene, 'adaptive')]
        fixed_summary = next(s for s in joint['summary'] if (s['scene'], s['policy']) == (scene, 'fixed_v20_profiles'))
        adaptive_summary = next(s for s in joint['summary'] if (s['scene'], s['policy']) == (scene, 'adaptive'))
        native_gap = gap_cases[scene]
        old_rows = old_mandatory[scene]['rows']
        cached_rows = old_cached[scene]['rows']
        budget_rows = old_budget[scene]['rows']
        if not (len(fixed['rows']) == len(adaptive['rows']) == len(native_gap['rows']) == 48):
            raise AssertionError(f'row count: {scene}')
        fixed_total = projected_total = hud_old_total = hud_new_total = 0
        projected_forward_bytes = projected_reverse_bytes = 0
        fixed_errors = []
        adaptive_errors = []
        same_ref_fixed = []
        same_ref_adaptive = []
        matched = []
        same_refs = []
        frame_rows = []
        for i, (f, a, g, v20, cache_row, budget) in enumerate(zip(
                fixed['rows'], adaptive['rows'], native_gap['rows'], old_rows, cached_rows, budget_rows)):
            if not (f['id'] == a['id'] == g['frame'] == v20['id'] == budget['id'] == i):
                raise AssertionError(f'frame identity: {scene}:{i}')
            if f['input_sha256'] != v20['input_sha256'] or a['input_sha256'] != v20['input_sha256']:
                raise AssertionError(f'source identity: {scene}:{i}')
            if not f['accepted'] or not a['accepted'] or f['packet_bytes'] > FRAME_CAP or a['packet_bytes'] > FRAME_CAP:
                raise AssertionError(f'unexpected rejected joint frame: {scene}:{i}')
            # Decode and inspect the actual stored CB21 packet, including its binding hashes.
            raw_pair = load_blob(f['packet'], JOINT)
            epoch, frame, base, hud = parse_pair(raw_pair)
            if (len(raw_pair), len(base), len(hud)) != (f['packet_bytes'], f['base_bytes'], f['hud_bytes']):
                raise AssertionError(f'joint packet byte mismatch: {scene}:{i}')
            if (epoch, frame) != (1, i) or len(raw_pair) > FRAME_CAP:
                raise AssertionError(f'joint identity/cap mismatch: {scene}:{i}')
            packet_decodes += 1
            # Fixed stored profile choices must reproduce frozen v21 base/predictor bytes and quality.
            if (f['packet_bytes'] != budget['cb21_complete_bytes']
                    or f['active_rgb565_channel_mse'] != v20['active_rgb565_mse']
                    or f['reference_bank'] != v20['reference_bank']
                    or f['reference_id'] != v20['reference_id']
                    or f['reference_tag'] != v20['reference_tag']
                    or f['stored_tag'] != v20['stored_tag']
                    or f['destination_bank'] != v20['destination_bank']):
                raise AssertionError(f'fixed-v20 source-history mismatch: {scene}:{i}')
            fixed_errors.append(f['active_rgb565_channel_mse'])
            adaptive_errors.append(a['active_rgb565_channel_mse'])
            fixed_total += f['packet_bytes']
            hud_old_total += g['hc21_bytes']
            hud_new_total += g['proposed_same_overhead_bytes']
            if g['hc21_bytes'] != cache_row['sidecar_bytes'] or g['hc21_bytes'] != f['hud_bytes']:
                raise AssertionError(f'gap/HC21 sidecar identity: {scene}:{i}')
            # Recheck fallback selection from paid legacy, HD21, and HD22 sizes.
            for po in g['patches']:
                if po['selected_bytes'] != min(po['legacy_bytes'], po['hd22_bytes']) or po['hd22_bytes'] > po['hd21_bytes']:
                    raise AssertionError(f'HD22 fallback arithmetic: {scene}:{i}')
            if g['proposed_same_overhead_bytes'] != HC21_OVERHEAD + sum(p['selected_bytes'] for p in g['patches']):
                raise AssertionError(f'HD22 sidecar bytes: {scene}:{i}')
            projected = f['packet_bytes'] - g['hc21_bytes'] + g['proposed_same_overhead_bytes']
            if projected != budget['cb21_complete_bytes'] - g['hc21_bytes'] + g['proposed_same_overhead_bytes']:
                raise AssertionError(f'projected pair identity: {scene}:{i}')
            if projected > FRAME_CAP:
                raise AssertionError(f'projected pair over cap: {scene}:{i}')
            projected_total += projected
            # The exact net complete-pair projection replaces only sidecar bytes; the pair binder is retained.
            if projected != f['packet_bytes'] - (g['hc21_bytes'] - g['proposed_same_overhead_bytes']):
                raise AssertionError('pair overhead was not conserved')
            fragments = math.ceil(projected / 1008)
            projected_forward_bytes += projected + fragments * (31 + 16 + 28) + 2 * (36 + 28)
            projected_reverse_bytes += fragments * (29 + 28) + 3 * (36 + 28) + f['ack_bytes'] + 28
            same = all(f[k] == a[k] for k in ('key', 'promoted', 'reference_bank', 'reference_id', 'reference_tag'))
            matched.append(i)
            if same:
                same_refs.append(i)
                same_ref_fixed.append(f['active_rgb565_channel_mse'])
                same_ref_adaptive.append(a['active_rgb565_channel_mse'])
            frame_rows.append(dict(id=i, actual_pair_bytes=f['packet_bytes'], projected_pair_bytes=projected,
                                   fixed_mse=f['active_rgb565_channel_mse'], adaptive_mse=a['active_rgb565_channel_mse']))
        if fixed_total != sum(r['packet_bytes'] for r in fixed['rows']):
            raise AssertionError('fixed total consistency')
        if not close(sum(fixed_errors)/48, fixed_summary['mean_active_rgb565_channel_mse']):
            raise AssertionError(f'fixed MSE summary: {scene}')
        if not close(sum(adaptive_errors)/48, adaptive_summary['mean_active_rgb565_channel_mse']):
            raise AssertionError(f'adaptive MSE summary: {scene}')
        # Recompute aligned-rate and aligned-quality comparison, including common-reference subset.
        comp = next(x for x in joint['comparisons'] if x['scene'] == scene)
        if comp['matched_source_ids'] != matched or comp['same_reference_ids'] != same_refs:
            raise AssertionError(f'comparison row membership: {scene}')
        if not close(comp['fixed_mean_mse'], sum(fixed_errors)/48) or not close(comp['adaptive_mean_mse'], sum(adaptive_errors)/48):
            raise AssertionError(f'comparison MSE: {scene}')
        if not close(comp['same_reference_fixed_mean_mse'], sum(same_ref_fixed)/len(same_ref_fixed)) or not close(comp['same_reference_adaptive_mean_mse'], sum(same_ref_adaptive)/len(same_ref_adaptive)):
            raise AssertionError(f'same-reference MSE: {scene}')
        pj = proj_cases[scene]
        if (pj['actual_fixed_joint_bytes'] != fixed_total or pj['projected_hd22_pair_bytes'] != projected_total
                or pj['complete_cap_fits'] != 48 or pj['maximum_projected_pair_bytes'] != max(r['projected_pair_bytes'] for r in frame_rows)):
            raise AssertionError(f'combined projection summary: {scene}')
        calculated_saving = 100 * (fixed_total-projected_total)/fixed_total
        forward_mbps = projected_forward_bytes / 48 * 30 * 8 / 1e6
        reverse_mbps = projected_reverse_bytes / 48 * 30 * 8 / 1e6
        if not close(pj['fixed_image_complete_saving_percent'], calculated_saving):
            raise AssertionError(f'complete saving percent: {scene}')
        if not (close(pj['projected_forward_Mbps_at30'], forward_mbps)
                and close(pj['projected_reverse_Mbps_at30'], reverse_mbps)):
            raise AssertionError(f'projected transport arithmetic: {scene}')
        gap_saving_pct = 100 * (hud_old_total-hud_new_total)/hud_old_total
        gap_results.append(dict(scene=scene, native_frames=48,
                                hc21_sidecar_bytes=hud_old_total, projected_hd22_sidecar_bytes=hud_new_total,
                                sidecar_saving_bytes=hud_old_total-hud_new_total,
                                sidecar_saving_percent=gap_saving_pct,
                                actual_fixed_pair_bytes=fixed_total, projected_complete_pair_bytes=projected_total,
                                complete_pair_saving_bytes=fixed_total-projected_total,
                                complete_pair_saving_percent=calculated_saving,
                                max_projected_pair_bytes=pj['maximum_projected_pair_bytes'],
                                projected_forward_Mbps_at30=forward_mbps,
                                projected_reverse_Mbps_at30=reverse_mbps))
        profile_results.append(dict(scene=scene, fixed_bytes=fixed_total,
                                    fixed_mse=sum(fixed_errors)/48,
                                    adaptive_bytes=adaptive_summary['complete_bytes'],
                                    adaptive_mse=sum(adaptive_errors)/48,
                                    adaptive_extra_bytes=adaptive_summary['complete_bytes']-fixed_total,
                                    adaptive_bytes_delta_percent=100*(adaptive_summary['complete_bytes']-fixed_total)/fixed_total,
                                    adaptive_quality_mse_delta=sum(adaptive_errors)/48-sum(fixed_errors)/48,
                                    same_reference_ids=same_refs,
                                    same_reference_fixed_mse=sum(same_ref_fixed)/len(same_ref_fixed),
                                    same_reference_adaptive_mse=sum(same_ref_adaptive)/len(same_ref_adaptive)))

    synthetic = {c['name']: c for c in gap['cases'] if c['name'].startswith('synthetic-')}
    if any(c['summary']['proposed_same_overhead_bytes'] != c['summary']['hc21_bytes'] for c in synthetic.values()):
        raise AssertionError('synthetic fallback regressions must remain visible')
    if not jverify.get('physical_dma_or_30fps_proven') is False or not gverify.get('physical_30fps_proven') is False:
        raise AssertionError('unsupported hardware/throughput claim')
    return dict(status='verified', source_pins= pins, source_test_counts=tests,
                retained_replays=dict(joint_decisions=jverify['actual_joint_decisions'],
                                      exact_hud_words=jverify['exact_original_hud_words'],
                                      HD22_patch_decisions=gverify['patch_decisions'],
                                      HD22_scalar_words=gverify['independent_scalar_words']),
                stored_joint_pair_packets_parsed=packet_decodes,
                native_gap_and_complete_pair_recomputed=gap_results,
                base_profile_quality_comparison=profile_results,
                synthetic_gap_savings=dict((k, v['summary']['proposed_same_overhead_bytes']-v['summary']['hc21_bytes'])
                                           for k, v in synthetic.items()),
                scope=dict(fixed_v20_profiles='stored chosen-map trace; image/bytes control, omits v20 controller search, not a fair timing or deployable causal policy baseline',
                           HD22='separate actual packet encode/decode, but combined full-pair figures are a projection with zero new dispatch-byte assumption',
                           physical='no DMA, ESP32/SRAM/QSPI/RF, RTL/resource/timing or measured end-to-end 30fps proof'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    result = build_audit()
    target = HERE / 'audit.json'
    if args.check:
        if read(target) != result:
            raise SystemExit('audit.json differs from independent recomputation')
        print('PASS: v22 pins, packet arithmetic, quality tradeoffs, gap projection, and scope')
    else:
        target.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
        print(f'wrote {target.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
