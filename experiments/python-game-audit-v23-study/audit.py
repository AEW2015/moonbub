#!/usr/bin/env python3
"""Independent audit of the frozen V23 HD22 joint campaign."""
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
JOINT = EXP / 'python-game-hd22-joint-study'
V22 = EXP / 'python-game-joint-commit-study'
CAP = 49152
PAIR = struct.Struct('<4sBIIII16s16s')
HC22 = struct.Struct('<4sBIIIBBII16s16s4I4B')
JA23 = struct.Struct('<4sBII16sHH')
HA22_ACK = struct.Struct('<4sBIIIB16s16s')
AF03 = struct.Struct('<4sBBIIIBI16s')
HD22 = struct.Struct('<4sBBHHI16s16s')


def load(path):
    return json.loads(Path(path).read_text())


def digest(data):
    return hashlib.sha256(data).digest()


def sha_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def close(a, b, tol=1e-11):
    return math.isclose(float(a), float(b), rel_tol=tol, abs_tol=tol)


def pins(data):
    for rel, expected in data['source_sha256'].items():
        p = (ROOT / rel).resolve()
        if not p.is_file() or sha_file(p) != expected:
            raise AssertionError(f'source pin mismatch: {rel}')
    return len(data['source_sha256'])


def load_blob(desc, folder):
    path = Path(desc['path'])
    if path.is_absolute() or '..' in path.parts:
        raise AssertionError('unsafe artifact path')
    stored = (folder / path).read_bytes()
    if hashlib.sha256(stored).hexdigest() != desc['stored_sha256']:
        raise AssertionError(f'stored object digest mismatch: {path}')
    dec = zlib.decompressobj()
    raw = dec.decompress(stored, int(desc['raw_bytes']) + 1)
    if (not dec.eof or dec.unconsumed_tail or dec.unused_data or len(raw) != desc['raw_bytes']
            or hashlib.sha256(raw).hexdigest() != desc['raw_sha256']):
        raise AssertionError(f'bounded object decode mismatch: {path}')
    return raw


def crc_ok(data):
    return len(data) >= 4 and zlib.crc32(data[:-4]) == struct.unpack_from('<I', data, len(data)-4)[0]


def parse_cp23(packet):
    if not PAIR.size + 4 <= len(packet) <= CAP or not crc_ok(packet):
        raise AssertionError('CP23 complete cap/CRC')
    magic, ver, epoch, frame, nb, nh, bh, hh = PAIR.unpack_from(packet)
    if magic != b'CP23' or ver != 1 or not nb or not nh or len(packet) != PAIR.size + nb + nh + 4:
        raise AssertionError('CP23 framing')
    base = packet[PAIR.size:PAIR.size+nb]
    hud = packet[PAIR.size+nb:-4]
    if (digest(base)[:16], digest(hud)[:16]) != (bh, hh):
        raise AssertionError('CP23 component digest')
    if len(base) < 8 or base[:4] != b'AR03' or len(hud) < HC22.size + 4:
        raise AssertionError('CP23 inner profile')
    hf = HC22.unpack_from(hud)
    if (hf[0], hf[1], hf[2], hf[3]) != (b'HC22', 1, epoch, frame) or not crc_ok(hud):
        raise AssertionError('HC22 profile/identity/CRC')
    sizes = hf[11:15]
    modes = hf[15:19]
    if len(hud) != HC22.size + sum(sizes) + 4 or any(x not in (0, 1) for x in modes):
        raise AssertionError('HC22 patch framing/dispatch')
    pieces = []
    pos = HC22.size
    for n in sizes:
        pieces.append(hud[pos:pos+n])
        pos += n
    return dict(epoch=epoch, frame=frame, base=base, hud=hud, pieces=pieces, modes=modes,
                patch_sizes=sizes, packet_bytes=len(packet))


def parse_ja23(ack, pair):
    total = JA23.size + AF03.size + 4 + HA22_ACK.size + 4 + 4
    if len(ack) != total or not crc_ok(ack):
        raise AssertionError('JA23 length/CRC')
    magic, ver, epoch, frame, tag, nb, nh = JA23.unpack_from(ack)
    if (magic, ver, epoch, frame, tag, nb, nh) != (
            b'JA23', 1, pair['epoch'], pair['frame'], digest(pair['raw'])[:16], AF03.size+4, HA22_ACK.size+4):
        raise AssertionError('JA23 pair bind/lengths')
    a = ack[JA23.size:JA23.size+nb]
    h = ack[JA23.size+nb:-4]
    if not crc_ok(a) or not crc_ok(h):
        raise AssertionError('nested ACK CRC')
    if AF03.unpack_from(a)[0] != b'AF03' or HA22_ACK.unpack_from(h)[0] != b'HA22':
        raise AssertionError('JA23 nested profile')
    return len(ack)


def wire(packet_bytes, ack_bytes):
    frags = (packet_bytes + 1007) // 1008
    forward = packet_bytes + frags * 75 + 128
    reverse = 192 + frags * 57 + ack_bytes + 28
    return frags, forward, reverse


def test_log_count(path, expected):
    s = Path(path).read_text()
    m = re.search(r'^Ran (\d+) tests? in ', s, re.M)
    if not m or int(m.group(1)) != expected or not s.rstrip().endswith('OK'):
        raise AssertionError(f'test log count mismatch: {path}')
    return int(m.group(1))


def build_audit():
    data = load(JOINT / 'results.json')
    v22 = load(V22 / 'results.json')
    projection = load(V22 / 'analysis.json')
    if data.get('schema') != 'gamebub-integrated-hd22-v23':
        raise AssertionError('unexpected campaign schema')
    pin_count = pins(data)
    joint_tests = test_log_count(JOINT / 'tests.log', 25)
    # The shared-analysis suite is pinned and has its own retained test log.
    shared_dir = EXP / 'python-game-shared-analysis-study'
    shared_tests = test_log_count(shared_dir / 'tests.log', 16)
    retained = load(JOINT / 'verify.log')
    if (retained['actual_joint_decisions'], retained['exact_original_hud_words'],
            retained['actual_hd22_span_patches'], retained['paired_packet_ack_display_identical_decisions'],
            retained['physical_30fps_proven']) != (288, 6082560, 456, 96, False):
        raise AssertionError('retained joint verifier totals/scope')
    if len(data['cases']) != 6 or data['counts'] != dict(source_acquisitions=96, frame_decisions=288, cases=6):
        raise AssertionError('campaign cohort dimensions')
    by_case = {(c['scene'], c['policy']): c for c in data['cases']}
    old_fixed = {(c['scene'], c['policy']): c for c in v22['cases']}
    projected = {c['scene']: c for c in projection['cases']}
    summary_rows = {(s['scene'], s['policy']): s for s in data['summary']}
    packet_count = paired_count = hd22_count = total_spans = 0
    results = []
    adaptive_tradeoffs = []
    analysis_memory = []
    for scene in ('mass-effect-2600', 'mass-effect-7200'):
        fixed = by_case[(scene, 'fixed_v20_profiles')]
        plain = by_case[(scene, 'adaptive_plain')]
        shared = by_case[(scene, 'adaptive_shared')]
        prior_fixed = old_fixed[(scene, 'fixed_v20_profiles')]
        prior_adaptive = old_fixed[(scene, 'adaptive')]
        prior_proj = projected[scene]
        if not all(len(c['rows']) == 48 for c in (fixed, plain, shared)) or not (
                len(prior_fixed['rows']) == len(prior_adaptive['rows']) == 48):
            raise AssertionError(f'row count {scene}')
        sum_fixed = sum_forward_fixed = sum_reverse_fixed = 0
        sum_plain = sum_shared = sum_v22_adaptive = 0
        v22_adaptive_mse = []
        v23_adaptive_mse = []
        same_reference_ids = []
        plain_calls = plain_forward = shared_calls = shared_forward = 0
        guard_calls = guard_bytes = 0
        context_array_bytes = max_context_readers = 0
        context_lease_count = 0
        quality_vals = []
        exact_hud_words = 0
        spans = 0
        for i, (f, p, s, oldf, olda) in enumerate(zip(
                fixed['rows'], plain['rows'], shared['rows'], prior_fixed['rows'], prior_adaptive['rows'])):
            if (f['id'], p['id'], s['id'], oldf['id'], olda['id']) != (i, i, i, i, i):
                raise AssertionError('source row identity')
            if not (f['input_sha256'] == p['input_sha256'] == s['input_sha256'] == oldf['input_sha256'] == olda['input_sha256']):
                raise AssertionError(f'source pin mismatch in row {scene}:{i}')
            for row in (f, p, s):
                packet = load_blob(row['packet'], JOINT)
                ack = load_blob(row['ack'], JOINT)
                parsed = parse_cp23(packet)
                if len(packet) != row['packet_bytes'] or parsed['packet_bytes'] > CAP:
                    raise AssertionError('actual serialized CP23 byte count/cap')
                if (len(parsed['base']), len(parsed['hud'])) != (row['base_bytes'], row['hud_bytes']):
                    raise AssertionError('actual CP23 component sizes')
                if parsed['frame'] != i or parsed['epoch'] != 1:
                    raise AssertionError('CP23 frame identity')
                if row['exact_hud_words'] != 21120 or row['active_channel_samples'] != 874800:
                    raise AssertionError('coverage counts')
                for mode, piece in zip(parsed['modes'], parsed['pieces']):
                    if mode == 1:
                        if len(piece) < HD22.size + 4 or piece[:4] != b'HD22' or not crc_ok(piece):
                            raise AssertionError('actual HD22 dispatch/CRC')
                        magic, version, inner_mode, w, h, size, ref, tag = HD22.unpack_from(piece)
                        if magic != b'HD22' or version != 1 or len(piece) != HD22.size + size + 4:
                            raise AssertionError('HD22 framing')
                        hd22_count += 1
                        spans += int(inner_mode == 2)
                        total_spans += int(inner_mode == 2)
                    elif not piece.startswith((b'HP01', b'HR01')):
                        raise AssertionError('unknown legacy patch dispatch')
                parse_ja23(ack, parsed | {'raw': packet})
                if len(ack) != row['ack_bytes'] or row['ack_bytes'] != 134:
                    raise AssertionError('actual JA23 ACK bytes')
                packet_count += 1
                frags, fwd, rev = wire(len(packet), len(ack))
                if row['wire'] != dict(fragments=frags, data_forward_bytes=len(packet)+frags*75,
                                        frame_forward_control_bytes=128, frame_reverse_control_bytes=192,
                                        packet_credit_reverse_bytes=frags*57, joint_ack_reverse_bytes=len(ack)+28):
                    raise AssertionError('wire framing fields')
                if row['active_rgb565_channel_mse'] != row['active_squared_channel_error'] / row['active_channel_samples']:
                    raise AssertionError('quality arithmetic')
                if row['accepted'] is not True:
                    raise AssertionError('campaign rejected accepted row')
                if row is f:
                    sum_fixed += len(packet)
                    sum_forward_fixed += fwd
                    sum_reverse_fixed += rev
                    exact_hud_words += row['exact_hud_words']
                    if (row['display_rgb565_sha256'], row['canonical_yuv_tag'], row['active_rgb565_channel_mse']) != (
                            oldf['display_rgb565_sha256'], oldf['canonical_yuv_tag'], oldf['active_rgb565_channel_mse']):
                        raise AssertionError(f'fixed control image/YUV/quality changed: {scene}:{i}')
                    if (row['packet_bytes'], row['packet_bytes'] - row['base_bytes'] - row['hud_bytes']) != (
                            row['packet_bytes'], 57):
                        raise AssertionError('CP23 complete pair framing cost')
                    quality_vals.append(row['active_rgb565_channel_mse'])
                elif row is p:
                    sum_plain += len(packet)
                    sum_v22_adaptive += olda['packet_bytes']
                    v22_adaptive_mse.append(olda['active_rgb565_channel_mse'])
                    v23_adaptive_mse.append(row['active_rgb565_channel_mse'])
                    if all(row[k] == olda[k] for k in ('key', 'promoted', 'reference_bank', 'reference_id', 'reference_tag')):
                        same_reference_ids.append(i)
                    attempts = len(row['build_info']['attempts'])
                    if row['work'] != dict(analyze_calls=attempts, forward_plane_calls=3*attempts):
                        raise AssertionError('plain analysis/forward calls are not actual paid map calls')
                    plain_calls += row['work']['analyze_calls']; plain_forward += row['work']['forward_plane_calls']
                else:
                    sum_shared += len(packet)
                    if row['work'] != dict(analyze_calls=1, forward_plane_calls=3):
                        raise AssertionError('shared analysis/forward call count')
                    shared_calls += row['work']['analyze_calls']; shared_forward += row['work']['forward_plane_calls']
                    si = row['shared_source_info']
                    if si['retained_analysis_array_bytes'] != 5184000 or si['retained_source_copy_bytes'] != 0:
                        raise AssertionError('shared context retained-array accounting')
                    if si['context_lease_released'] != bool(si['dedicated_context_lease']):
                        raise AssertionError('shared context lease cleanup')
                    guard_calls += si['source_guard_calls']
                    guard_bytes += si['source_guard_bytes']
                    context_array_bytes = max(context_array_bytes, si['retained_analysis_array_bytes'])
                    max_context_readers = max(max_context_readers, si['additional_context_reader_descriptors'])
                    context_lease_count += int(si['dedicated_context_lease'])
            if (p['packet']['raw_sha256'], p['ack']['raw_sha256'], p['display_rgb565_sha256'], p['canonical_yuv_tag']) != (
                    s['packet']['raw_sha256'], s['ack']['raw_sha256'], s['display_rgb565_sha256'], s['canonical_yuv_tag']):
                raise AssertionError(f'plain/shared serialized or decoded divergence: {scene}:{i}')
            if p['selected_profile'] != s['selected_profile']:
                raise AssertionError('plain/shared map selection divergence')
            paired_count += 1
            if f['active_rgb565_channel_mse'] != oldf['active_rgb565_channel_mse']:
                raise AssertionError('fixed profile quality differs from frozen v22 image control')
            if (f['packet_bytes'] != prior_proj['rows'][i]['projected_hd22_pair_bytes']
                    or f['packet_bytes'] != oldf['packet_bytes'] - oldf['hud_bytes'] + f['hud_bytes']):
                raise AssertionError('actual fixed CP23 size differs from v22 HD22 projection')
        sf, sp, ss = summary_rows[(scene, 'fixed_v20_profiles')], summary_rows[(scene, 'adaptive_plain')], summary_rows[(scene, 'adaptive_shared')]
        if sum_fixed != sf['complete_bytes'] or sum_plain != sp['complete_bytes'] or sum_shared != ss['complete_bytes']:
            raise AssertionError('case byte summary')
        if (plain_calls, plain_forward, shared_calls, shared_forward) != (
                sp['total_analyze_calls'], sp['total_forward_plane_calls'],
                ss['total_analyze_calls'], ss['total_forward_plane_calls']):
            raise AssertionError('summary source-call counters')
        if not close(sf['mean_active_rgb565_channel_mse'], sum(quality_vals)/48):
            raise AssertionError('fixed quality mean')
        if (round(sum_forward_fixed / 48 * 30 * 8 / 1e6, 6), round(sum_reverse_fixed / 48 * 30 * 8 / 1e6, 6)) != (
                sf['projected_forward_Mbps_at30'], sf['projected_reverse_Mbps_at30']):
            raise AssertionError('independent fixed rate arithmetic')
        if sf['maximum_complete_bytes'] != max(r['packet_bytes'] for r in fixed['rows']):
            raise AssertionError('fixed complete-packet maximum')
        results.append(dict(scene=scene, fixed_complete_bytes=sum_fixed,
                            fixed_projected_rate_forward_Mbps_at30=sf['projected_forward_Mbps_at30'],
                            fixed_projected_rate_reverse_Mbps_at30=sf['projected_reverse_Mbps_at30'],
                            fixed_max_complete_bytes=sf['maximum_complete_bytes'],
                            adaptive_plain_bytes=sum_plain, adaptive_shared_bytes=sum_shared,
                            adaptive_plain_analyze_forward=[plain_calls, plain_forward],
                            adaptive_shared_analyze_forward=[shared_calls, shared_forward],
                            exact_hud_words=exact_hud_words))
        old_v22_summary = next(x for x in v22['summary'] if x['scene'] == scene and x['policy'] == 'adaptive')
        if sum_v22_adaptive != old_v22_summary['complete_bytes']:
            raise AssertionError('v22 adaptive byte re-sum')
        if same_reference_ids != list(range(48)):
            raise AssertionError(f'adaptive predictor identity history changed in {scene}')
        adaptive_tradeoffs.append(dict(scene=scene,
                                       v22_adaptive_complete_bytes=sum_v22_adaptive,
                                       v23_adaptive_complete_bytes=sum_plain,
                                       byte_change=sum_plain-sum_v22_adaptive,
                                       byte_change_percent=100*(sum_plain-sum_v22_adaptive)/sum_v22_adaptive,
                                       v22_adaptive_mean_mse=sum(v22_adaptive_mse)/48,
                                       v23_adaptive_mean_mse=sum(v23_adaptive_mse)/48,
                                       mean_mse_change=sum(v23_adaptive_mse)/48-sum(v22_adaptive_mse)/48,
                                       mean_mse_improvement_percent=100*(sum(v22_adaptive_mse)-sum(v23_adaptive_mse))/sum(v22_adaptive_mse),
                                       same_reference_ids=same_reference_ids,
                                       v22_fine_frames=sum(r['selected_profile'] == [8, 16] for r in prior_adaptive['rows']),
                                       v23_fine_frames=sum(r['selected_profile'] == [8, 16] for r in plain['rows']),
                                       note='HD22 sidecar savings can admit finer adaptive base maps; this couples rate and quality policy.'))
        analysis_memory.append(dict(scene=scene, preparations=48, source_guard_calls=guard_calls,
                                    source_guard_bytes=guard_bytes,
                                    retained_analysis_array_bytes_per_context=context_array_bytes,
                                    dedicated_context_leases=context_lease_count,
                                    maximum_additional_context_descriptors=max_context_readers,
                                    cleanup='all referenced context leases released before candidate semantic snapshots'))
    comparisons = {c['scene']: c for c in data['comparisons']}
    cpu = {}
    for scene in ('mass-effect-2600', 'mass-effect-7200'):
        c = comparisons[scene]
        if c['exact_plain_shared_packet_ack_display_ids'] != list(range(48)):
            raise AssertionError('plain/shared parity coverage')
        if scene == 'mass-effect-2600':
            old_ms, new_ms = c['paired_plain_build_ms'], c['paired_shared_build_ms']
            if not new_ms > old_ms:
                raise AssertionError('report primary CPU regression faithfully')
        else:
            old_ms, new_ms = c['paired_plain_build_ms'], c['paired_shared_build_ms']
            if not new_ms < old_ms:
                raise AssertionError('complex CPU improvement expected for this trial')
        cpu[scene] = dict(plain_ms=old_ms, shared_ms=new_ms,
                          change_percent=100*(new_ms-old_ms)/old_ms,
                          interpretation='one paired host trial; not a universal or target speed claim')
    complex_case = comparisons['mass-effect-7200']
    if (complex_case['plain_analyze_calls'], complex_case['shared_analyze_calls'],
            complex_case['plain_forward_plane_calls'], complex_case['shared_forward_plane_calls']) != (59, 48, 177, 144):
        raise AssertionError('complex retry analysis reduction')
    if (complex_case['paired_plain_build_ms'], complex_case['paired_shared_build_ms']) != (1920.602364, 1845.635036):
        raise AssertionError('frozen complex host trial values')
    if (comparisons['mass-effect-2600']['paired_plain_build_ms'], comparisons['mass-effect-2600']['paired_shared_build_ms']) != (1503.45225, 1552.081586):
        raise AssertionError('frozen simple host trial values')
    if retained['adaptive_plain_forward_plane_calls'] != 321 or retained['adaptive_shared_forward_plane_calls'] != 288:
        raise AssertionError('retained verifier counters')
    if total_spans != retained['actual_hd22_span_patches']:
        raise AssertionError('independently counted actual HD22 span patches')
    if (sum(x['source_guard_calls'] for x in analysis_memory), sum(x['source_guard_bytes'] for x in analysis_memory),
            sum(x['retained_analysis_array_bytes_per_context'] for x in analysis_memory) // 5184000,
            max(x['maximum_additional_context_descriptors'] for x in analysis_memory)) != (203, 210470400, 2, 1):
        raise AssertionError('source guard and bounded context memory totals')
    return dict(status='verified', source_pin_count=pin_count,
                source_test_counts=dict(joint=joint_tests, shared=shared_tests),
                retained_replay=dict(decisions=retained['actual_joint_decisions'],
                                     exact_hud_words=retained['exact_original_hud_words'],
                                     actual_hd22_span_patches=retained['actual_hd22_span_patches'],
                                     paired_plain_shared_decisions=retained['paired_packet_ack_display_identical_decisions']),
                actual_cp23_packet_parses=packet_count, actual_ja23_acks_parsed=packet_count,
                actual_hd22_dispatches=hd22_count, inferred_hd22_span_patch_dispatches=total_spans,
                plain_shared_paired_rows=paired_count, independent_fixed_rate_rows=96,
                fixed_cp23_rate_and_quality=results, adaptive_rate_quality_tradeoff=adaptive_tradeoffs,
                host_cpu_trial=cpu, shared_analysis_memory=analysis_memory,
                scope=dict(wire='serialized CP23/JA23 application bytes plus the stated fixed 1008-byte fragment model and listed controls; arithmetic projection, not captured RF traffic',
                           physical='no native profile enablement, transport/RF/DMA/RTL or physical 30-fps proof',
                           quality='MSE is expanded active RGB565 channel error; fixed control images/YUV tags match v22, adaptive map quality may change when smaller HUD bytes admit a finer map'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    result = build_audit()
    target = HERE / 'audit.json'
    if args.check:
        if load(target) != result:
            raise SystemExit('audit.json differs from independent recomputation')
        print('PASS: v23 pins, actual CP23/JA23 bytes, rate parity, quality, work counters, and limits')
    else:
        target.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
        print(f'wrote {target.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
