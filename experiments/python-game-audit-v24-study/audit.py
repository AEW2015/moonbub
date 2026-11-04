#!/usr/bin/env python3
"""Independent replay and arithmetic audit of the frozen v24 codec study."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import zlib

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
EXP = HERE.parent
STUDY = EXP / 'python-game-standard-v24-study'
V23 = EXP / 'python-game-hd22-joint-study'
LAZY = EXP / 'python-game-lazy-owned-study'
RECOVERY = EXP / 'python-game-recovery-v24-study'
CAP = 49152


def load(path):
    return json.loads(Path(path).read_text())


def sha(data):
    return hashlib.sha256(data).hexdigest()


def sha_file(path):
    return sha(Path(path).read_bytes())


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def raw_blob(desc, folder=STUDY):
    rel = Path(desc['path'])
    if rel.is_absolute() or '..' in rel.parts:
        raise AssertionError('artifact path escapes study directory')
    stored = (folder / rel).read_bytes()
    if sha(stored) != desc['stored_sha256']:
        raise AssertionError(f'stored artifact digest mismatch: {rel}')
    dec = zlib.decompressobj()
    raw = dec.decompress(stored, int(desc['raw_bytes']) + 1)
    if (not dec.eof or dec.unused_data or dec.unconsumed_tail
            or len(raw) != desc['raw_bytes'] or sha(raw) != desc['raw_sha256']):
        raise AssertionError(f'bounded artifact decode mismatch: {rel}')
    return raw


def close(a, b, tol=1e-12):
    return math.isclose(float(a), float(b), rel_tol=tol, abs_tol=tol)


def make_metrics(model, source, display):
    if source.shape != (480, 720) or display.shape != source.shape:
        raise AssertionError('canvas geometry')
    if source.dtype != np.uint16 or display.dtype != np.uint16:
        raise AssertionError('RGB565 word representation')
    a = model.C.corpus.expand565(source).astype(np.int32)
    b = model.C.corpus.expand565(display).astype(np.int32)
    delta = a.astype(np.int64) - b.astype(np.int64)
    squared = delta * delta
    active_sse = int(squared[37:442].sum())
    samples = 405 * 720 * 3
    hud_words = hud_sse = 0
    for x, y, w, h in model.RECTANGLES:
        hud_words += int(np.count_nonzero(source[y:y+h, x:x+w] != display[y:y+h, x:x+w]))
        hud_sse += int(squared[y:y+h, x:x+w].sum())
    mse = active_sse / samples
    return dict(active_squared_error=active_sse, active_channel_samples=samples,
                active_mse=mse,
                active_psnr_db=None if not mse else 10 * math.log10(65025 / mse),
                hud_word_errors=hud_words, hud_squared_channel_error=hud_sse,
                hud_channel_samples=21120 * 3)


def wire(body, fragments):
    if type(body) is not int or body < 0:
        raise AssertionError('bad body byte count')
    expected_fragments = math.ceil(body / 1008)
    if fragments != expected_fragments:
        raise AssertionError('fragment count')
    return dict(body_bytes=body, under_complete_cap=body <= CAP,
                forward_data_ip_udp_bytes=body + fragments * 75,
                frame_forward_control_bytes=128,
                reverse_model_bytes=fragments * 57 + 192 + 134 + 28,
                fragments=fragments)


def aggregate(rows, variant):
    records = [row[variant] for row in rows]
    sse = sum(row['metric']['active_squared_error'] for row in records)
    samples = sum(row['metric']['active_channel_samples'] for row in records)
    mse = sse / samples
    n = len(records)
    body = sum(row['bytes'] for row in records)
    forward = sum(row['wire']['forward_data_ip_udp_bytes'] + row['wire']['frame_forward_control_bytes']
                  for row in records)
    reverse = sum(row['wire']['reverse_model_bytes'] for row in records)
    return dict(frames=n, complete_bytes=body, coded_body_Mbps_at30=body / n * 30 * 8 / 1e6,
                mean_bytes=body / n, maximum_bytes=max(row['bytes'] for row in records),
                cap_fit_frames=sum(row['bytes'] <= CAP for row in records),
                active_squared_error=sse, active_channel_samples=samples, active_mse=mse,
                active_psnr_db=None if not mse else 10 * math.log10(65025 / mse),
                hud_word_errors=sum(row['metric']['hud_word_errors'] for row in records),
                hypothetical_forward_Mbps_at30=forward / n * 30 * 8 / 1e6,
                hypothetical_reverse_Mbps_at30=reverse / n * 30 * 8 / 1e6)


def operating_points(cases, baselines):
    results = []
    for custom in baselines:
        for variant in ('bare', 'hybrid'):
            target = custom['summary'][variant]
            for codec in ('libx265', 'libsvtav1'):
                cohort = [c for c in cases if c['scene'] == custom['scene'] and c['codec'] == codec]
                eligible = [c for c in cohort if c['summary'][variant]['active_mse'] <= target['active_mse']]
                picked = min(eligible, key=lambda c: c['summary'][variant]['complete_bytes']) if eligible else None
                nearest = min(cohort, key=lambda c: abs(c['summary'][variant]['active_mse'] - target['active_mse']))
                results.append(dict(
                    scene=custom['scene'], custom_profile=custom['profile'], variant=variant,
                    codec=codec, target_custom_mse=target['active_mse'],
                    custom_bytes=target['complete_bytes'],
                    measured_parameters=[c['parameter'] for c in cohort],
                    sampled_quality_range_covers_target=(min(c['summary'][variant]['active_mse'] for c in cohort)
                                       <= target['active_mse']
                                       <= max(c['summary'][variant]['active_mse'] for c in cohort)),
                    lowest_bytes_measured_at_least_target_quality=(None if picked is None else dict(
                        profile=picked['profile'], parameter=picked['parameter'],
                        bytes=picked['summary'][variant]['complete_bytes'],
                        mse=picked['summary'][variant]['active_mse'],
                        custom_to_native_byte_ratio=(target['complete_bytes'] /
                                                     picked['summary'][variant]['complete_bytes']))),
                    nearest_measured_quality=dict(profile=nearest['profile'], parameter=nearest['parameter'],
                        bytes=nearest['summary'][variant]['complete_bytes'],
                        mse=nearest['summary'][variant]['active_mse']),
                    scope='Measured operating points only. At-least quality means this MSE threshold, not matched quality, BD-rate, perceptual equivalence, or target feasibility.'))
    return results


def audit_lazy_campaign():
    data = load(LAZY / 'results.json')
    v23 = load(V23 / 'results.json')
    if data.get('schema') != 'gamebub-owned-lazy-v24':
        raise AssertionError('lazy campaign schema')
    for rel, expected in data['source_sha256'].items():
        if sha_file(ROOT / rel) != expected:
            raise AssertionError(f'lazy source pin mismatch: {rel}')
    cases = {(c['scene'], c['policy']): c for c in data['cases']}
    if len(cases) != 6 or data['counts'] != dict(cases=6, source_acquisitions=96, frame_decisions=288):
        raise AssertionError('lazy campaign dimensions')
    packet_ack_matches = checked = copied = guards = 0
    for scene in ('mass-effect-2600', 'mass-effect-7200'):
        policies = [cases[(scene, p)] for p in ('plain', 'eager', 'owned_lazy')]
        v23_fixed = next(c for c in v23['cases'] if c['scene'] == scene and c['policy'] == 'adaptive_plain')
        if any(len(c['rows']) != 48 for c in policies):
            raise AssertionError('lazy row count')
        for i, rows in enumerate(zip(*(c['rows'] for c in policies))):
            if [r['id'] for r in rows] != [i, i, i]:
                raise AssertionError('lazy ID association')
            packet_bytes = [raw_blob(r['packet'], LAZY) for r in rows]
            ack_bytes = [raw_blob(r['ack'], LAZY) for r in rows]
            if not (packet_bytes[0] == packet_bytes[1] == packet_bytes[2]
                    and ack_bytes[0] == ack_bytes[1] == ack_bytes[2]
                    and len({r['display_rgb565_sha256'] for r in rows}) == 1):
                raise AssertionError(f'lazy packet/ACK/display parity: {scene}:{i}')
            prior = v23_fixed['rows'][i]
            if (packet_bytes[0] != raw_blob(prior['packet'], V23)
                    or ack_bytes[0] != raw_blob(prior['ack'], V23)
                    or rows[0]['display_rgb565_sha256'] != prior['display_rgb565_sha256']):
                raise AssertionError(f'lazy stream does not match frozen v23: {scene}:{i}')
            packet_ack_matches += 1
            if any(len(packet_bytes[j]) != r['packet_bytes'] or r['packet_bytes'] > CAP
                   or len(ack_bytes[j]) != r['ack_bytes'] or r['ack_bytes'] != 134
                   for j, r in enumerate(rows)):
                raise AssertionError('lazy serialized pair size')
            frags = math.ceil(rows[0]['packet_bytes'] / 1008)
            expected_wire = dict(fragments=frags, data_forward_bytes=rows[0]['packet_bytes'] + frags * 75,
                                 frame_forward_control_bytes=128, frame_reverse_control_bytes=192,
                                 packet_credit_reverse_bytes=frags * 57,
                                 joint_ack_reverse_bytes=rows[0]['ack_bytes'] + 28)
            if any(r['wire'] != expected_wire for r in rows):
                raise AssertionError('lazy packet wire totals')
            if any(r['work']['forward_plane_calls'] != 3 * r['work']['analyze_calls'] for r in rows):
                raise AssertionError('lazy paid analysis/forward work')
            own = rows[2]['build_info']['capture']
            if (own['copied_bytes'] != 1036800 or not own['released']
                    or own['active_readers_after'] != 0 or own['peak_pool_slots'] > 2
                    or own['retained_pool_pixel_bytes_after'] != 0):
                raise AssertionError('lazy owned capture release/budget')
            if rows[2]['shared_source_info']['source_guard_calls'] != 0 or rows[2]['shared_source_info']['source_guard_bytes'] != 0:
                raise AssertionError('lazy ownership retained source hashes')
            copied += own['copied_bytes']
            guards += rows[2]['shared_source_info']['source_guard_bytes']
            checked += 1
    if copied != 99532800 or guards != 0 or checked != 96:
        raise AssertionError('lazy pooled copy/guard totals')
    for comparison in data['comparisons']:
        if comparison['identical_packet_ack_display_ids'] != list(range(48)):
            raise AssertionError('lazy comparison parity IDs')
        expected_saving = 100 * (comparison['paid_build_ms']['plain'] - comparison['paid_build_ms']['owned_lazy']) / comparison['paid_build_ms']['plain']
        if not close(expected_saving, comparison['owned_vs_plain_build_saving_percent']):
            raise AssertionError('lazy performance comparison arithmetic')
    return dict(cases=len(cases), decisions=checked * 3, paired_identical_rows=packet_ack_matches,
                copied_snapshot_bytes=copied, owned_source_guard_bytes=guards,
                explicit_decode_or_hardware_claim=False)


def audit_recovery_campaign():
    data = load(RECOVERY / 'results.json')
    if data.get('schema') != 'gamebub-recovery-v24':
        raise AssertionError('recovery schema')
    for rel, expected in data['source_sha256'].items():
        if sha_file(ROOT / rel) != expected:
            raise AssertionError(f'recovery source pin mismatch: {rel}')
    model = load_module('audit_v24_recovery_model', RECOVERY / 'model.py')
    if (data['control_bytes'] != model.CONTROL_BYTES or model.CONTROL_BYTES != 46
            or data['profile_sha256_128'] != model.PROFILE_TAG.hex()):
        raise AssertionError('recovery fixed control/profile binding')
    cases = data['results']['cases']
    if len(cases) != 10:
        raise AssertionError('recovery campaign count')
    controls = delivered = lost = complete = 0
    by_name = {c['name']: c for c in cases}
    expected_names = {'nominal', 'all_go_ack_lost'} | {f'single_loss_kind_{k}' for k in range(1, 9)}
    if set(by_name) != expected_names:
        raise AssertionError('recovery nominal/single-loss cohort')
    for case in cases:
        app = ip_udp = case_lost = 0
        for row in case['trace']:
            packet = bytes.fromhex(row['bytes'])
            parsed = model.parse(packet)
            if len(packet) != 46 or parsed['kind'] != row['kind'] or parsed['profile'] != model.PROFILE_TAG:
                raise AssertionError('recovery serialized control bytes/profile/CRC')
            app += len(packet)
            ip_udp += len(packet) + 28
            controls += 1
            if row['delivered']:
                delivered += 1
            else:
                case_lost += 1
                lost += 1
        if (app != case['control_application_bytes'] or ip_udp != case['control_ipv4_udp_bytes']
                or case_lost != case['lost_messages']):
            raise AssertionError(f'recovery loss accounting: {case["name"]}')
        if case['complete']:
            complete += 1
            if case['host_phase'] != 'RUNNING' or case['target_phase'] != 'RUNNING' or case['output'] is None:
                raise AssertionError('successful recovery terminal state')
            verify_probe(model, case['output'])
        elif case['name'] == 'all_go_ack_lost':
            if (case['host_phase'], case['target_phase'], case['output']) != ('SAFE_STOP', 'RUNNING', None):
                raise AssertionError('persistent GO_ACK loss state')
        else:
            raise AssertionError('unexpected incomplete finite-loss campaign')
    reboot = data['results']['reboot_sequence']
    if [o['epoch'] for o in reboot['outputs']] != [1, 2, 3] or len(reboot['traces']) != 3:
        raise AssertionError('reboot epoch sequence')
    for output in reboot['outputs']:
        verify_probe(model, output)
    old_packet = bytes.fromhex(reboot['outputs'][0]['packet_hex'])
    target = model.m.JointReceiver(epoch=2)
    before = target.published_snapshot()
    try:
        target.prepare(old_packet)
    except ValueError:
        pass
    else:
        raise AssertionError('stale prior-epoch frame was accepted')
    if target.published_snapshot() != before or not reboot['stale_epoch_data_rejected']:
        raise AssertionError('stale epoch failure mutated receiver state')
    if (complete != 9 or lost != 13 or controls != 100 or delivered != controls - lost):
        raise AssertionError('recovery campaign aggregate loss counts')
    return dict(campaigns=len(cases), recovered=complete, control_messages=controls,
                lost_controls_charged=lost, reboot_epochs=[1, 2, 3], stale_data_rejected=True,
                physical_30fps_proven=False)


def verify_probe(model, output):
    packet = bytes.fromhex(output['packet_hex'])
    ack = bytes.fromhex(output['ack_hex'])
    base, hud = model.m.compose.unbind(packet)
    meta, hm = model.m.C.identity(base), model.m.hc.parse(hud)
    if (meta['epoch'] != output['epoch'] or meta['frame_id'] != output['frame']
            or not meta['key'] or hm['refslot'] != model.m.hc.NO_REF
            or not output['key'] or not output['hud_independent'] or output['exact_hud_words'] != 21120):
        raise AssertionError('new-epoch independent key/full HUD semantics')
    receiver = model.m.JointReceiver(epoch=output['epoch'])
    task = receiver.prepare(packet)
    receiver.mark_writes_drained(task)
    actual_ack = receiver.present(task)
    if actual_ack != ack or sha(receiver.display.tobytes()) != output['display_rgb565_sha256']:
        raise AssertionError('recovery CP23/JA23 probe replay')
    rgb = np.full((480, 720, 3), [44, 96, 156], dtype=np.uint8)
    words = model.m.C.corpus.rgb565(rgb)
    for x, y, w, h in model.m.hc.RECTANGLES:
        if not np.array_equal(receiver.display[y:y+h, x:x+w], words[y:y+h, x:x+w]):
            raise AssertionError('recovery full HUD did not restore source words')


def build_audit():
    data = load(STUDY / 'results.json')
    old = load(V23 / 'results.json')
    if data.get('schema') != 'gamebub-standard-compare-v24':
        raise AssertionError('unexpected v24 campaign schema')
    for rel, expected in data['source_sha256'].items():
        path = ROOT / rel
        if not path.is_file() or sha_file(path) != expected:
            raise AssertionError(f'source pin mismatch: {rel}')

    model = load_module('audit_v24_native_model', STUDY / 'model.py')
    scene_inputs = {}
    source_rows_checked = yuv_tags_checked = sidecars_checked = 0
    for source in data['inputs']:
        scene = source['scene']
        if scene in scene_inputs or len(source['rows']) != 48:
            raise AssertionError('duplicate scene or wrong source row count')
        prior = next(c for c in old['cases'] if c['scene'] == scene and c['policy'] == 'adaptive_plain')
        if len(prior['rows']) != 48:
            raise AssertionError('v23 source row count')
        patches = []
        rx = model.joint.hc.Receiver()
        inputs = []
        for i, (row, prev) in enumerate(zip(source['rows'], prior['rows'])):
            if row['id'] != i or row['input_rgb_sha256'] != prev['input_sha256']:
                raise AssertionError(f'RGB input identity mismatch against v23: {scene}:{i}')
            raw_words = raw_blob(row['original_rgb565'])
            if len(raw_words) != 720 * 480 * 2:
                raise AssertionError(f'RGB565 source canvas length mismatch: {scene}:{i}')
            words = np.frombuffer(raw_words, '<u2').reshape(480, 720).copy()
            yuv_raw = raw_blob(row['common_yuv420_u8'])
            if len(yuv_raw) != 518400 or sha(yuv_raw) != row['common_yuv420_u8_sha256']:
                raise AssertionError(f'common YUV420 source hash mismatch: {scene}:{i}')
            yuv = np.frombuffer(yuv_raw, np.uint8)
            planes = (yuv[:345600].reshape(480, 720), yuv[345600:432000].reshape(240, 360),
                      yuv[432000:].reshape(240, 360))
            sidecar = raw_blob(row['hc22'])
            cp23 = raw_blob(prev['packet'], V23)
            _, expected_sidecar = model.joint.compose.unbind(cp23)
            if sidecar != expected_sidecar:
                raise AssertionError(f'HC22 sidecar differs from paired v23 CP23: {scene}:{i}')
            rx.receive(sidecar)
            current = tuple(p.copy() for p in rx.display['patches'])
            for (x, y, w, h), patch in zip(model.RECTANGLES, current):
                if not np.array_equal(patch, words[y:y+h, x:x+w]):
                    raise AssertionError(f'HC22 is not exact source HUD: {scene}:{i}')
            roundtrip = model.C.corpus.rgb565(model.C.gm.ft.planes_to_rgb(planes))
            if make_metrics(model, words, roundtrip) != row['no_compression_roundtrip_bare']:
                raise AssertionError(f'common-color floor mismatch: {scene}:{i}')
            if make_metrics(model, words, model.overlay(roundtrip, current)) != row['no_compression_roundtrip_hybrid']:
                raise AssertionError(f'hybrid common-color floor mismatch: {scene}:{i}')
            patches.append(current)
            inputs.append(words)
            source_rows_checked += 1
            yuv_tags_checked += 1
            sidecars_checked += 1
        scene_inputs[scene] = dict(words=inputs, patches=patches, source=source)

    if set(scene_inputs) != {'mass-effect-2600', 'mass-effect-7200'}:
        raise AssertionError('expected two v23 scenes')
    if data['counts'] != dict(unique_source_acquisitions=96, native_cases=len(data['cases']),
                              native_codec_outputs=48 * len(data['cases']), custom_reference_outputs=192):
        raise AssertionError('v24 campaign counts')
    if data['counts']['native_cases'] < 16:
        raise AssertionError('native profile sweep omitted required HEVC/AV1 settings')

    custom_recomputed = 0
    for base in data['custom_baselines']:
        scene = base['scene']
        policy = base['profile']
        oldcase = next(c for c in old['cases'] if c['scene'] == scene and c['policy'] == policy)
        if len(base['rows']) != 48:
            raise AssertionError('custom baseline row count')
        # Baseline summaries are audited against actual frozen v23 packets and
        # receiver output, including the exact serialized pair size.
        receiver = model.C.Receiver()
        expected_rows = []
        for i, prev in enumerate(oldcase['rows']):
            pair = raw_blob(prev['packet'], V23)
            base_packet, hud_packet = model.joint.compose.unbind(pair)
            base_rgb, _, _ = receiver.receive(base_packet)
            bare = model.C.corpus.rgb565(base_rgb)
            hybrid = model.overlay(bare, scene_inputs[scene]['patches'][i])
            source_words = scene_inputs[scene]['words'][i]
            if model.digest(hybrid) != prev['display_rgb565_sha256']:
                raise AssertionError(f'v23 baseline image identity mismatch: {scene}:{policy}:{i}')
            expected_rows.append(dict(
                id=i,
                bare=dict(bytes=len(base_packet), metric=make_metrics(model, source_words, bare),
                          wire=wire(len(base_packet), math.ceil(len(base_packet) / 1008)),
                          output_sha256=model.digest(bare)),
                hybrid=dict(bytes=len(pair), metric=make_metrics(model, source_words, hybrid),
                            wire=wire(len(pair), math.ceil(len(pair) / 1008)),
                            output_sha256=model.digest(hybrid))))
            custom_recomputed += 1
        if base['rows'] != expected_rows:
            raise AssertionError(f'custom baseline row mismatch: {scene}:{policy}')
        for variant in ('bare', 'hybrid'):
            expected_summary = aggregate(expected_rows, variant)
            given_summary = base['summary'][variant]
            for k, value in expected_summary.items():
                if isinstance(value, float):
                    if not close(given_summary[k], value):
                        raise AssertionError(f'custom {variant} summary mismatch: {scene}:{policy}:{k}')
                elif given_summary[k] != value:
                    raise AssertionError(f'custom {variant} summary mismatch: {scene}:{policy}:{k}')

    cases = data['cases']
    packets_checked = decoded_outputs = variant_metrics_checked = 0
    key_ids = set()
    for case in cases:
        ref = case['reference']
        if ref['unconsumed_options'] or ref['packets_only_at_flush'] != 0:
            raise AssertionError('encoder options/flush behavior')
        packet_rows = ref['packets']
        pts = [p['pts'] for p in packet_rows]
        dts = [p['dts'] for p in packet_rows]
        expected_keys = [0, 24]
        if pts != list(range(48)) or dts != pts or ref['key_ids'] != expected_keys:
            raise AssertionError('packet identity/order/key interval')
        if [p['pts'] for p in packet_rows if p['is_key']] != expected_keys:
            raise AssertionError('actual packet key IDs')
        if [c['emitted_pts'] for c in ref['frame_calls']] != [[i] for i in range(48)]:
            raise AssertionError('encoder emission lags')
        if not close(ref['encode_codec_total_ms'],
                     sum(c['encode_ms'] for c in ref['frame_calls']) + ref['encoder_flush_ms']):
            raise AssertionError('stored aggregate encode timing')
        packet_payloads = []
        for p in packet_rows:
            data_bytes = raw_blob(p['packet'])
            if len(data_bytes) != p['bytes']:
                raise AssertionError('packet payload length')
            packet_payloads.append(dict(pts=p['pts'], dts=p['dts'], is_key=p['is_key'], data=data_bytes))
            packets_checked += 1
        extras = raw_blob(ref['extradata'])
        if len(extras) != ref['extradata_bytes']:
            raise AssertionError('extradata byte length')
        outputs, dec_info = model.decode(packet_payloads, extras, case['codec'])
        if sorted(outputs) != list(range(48)) or dec_info['frames_only_at_decode_flush'] != 0:
            raise AssertionError('decoded native output coverage/flush')
        if not close(ref['decode_codec_total_ms'],
                     sum(c['decode_ms'] for c in ref['decode_calls']) + ref['decoder_flush_ms']):
            raise AssertionError('stored aggregate decode timing')
        if [c['packet_pts'] for c in ref['decode_calls']] != pts:
            raise AssertionError('stored packet decode call association')
        source = scene_inputs[case['scene']]
        rows = case['rows']
        if len(rows) != 48:
            raise AssertionError('native row count')
        for i, row in enumerate(rows):
            if row['id'] != i or row['coded_access_unit_bytes'] != len(packet_payloads[i]['data']) + (len(extras) if i == 0 else 0):
                raise AssertionError(f'per-ID packet/extradata accounting: {case["profile"]}:{i}')
            native_bare = outputs[i]
            native_hybrid = model.overlay(native_bare, source['patches'][i])
            for variant, display in (('bare', native_bare), ('hybrid', native_hybrid)):
                rec = row[variant]
                coded = row['coded_access_unit_bytes']
                hud = source['source']['rows'][i]['hc22']['raw_bytes'] if variant == 'hybrid' else 0
                body = coded + hud + (57 if variant == 'hybrid' else 0)
                expected_wire = wire(body, math.ceil(body / 1008))
                if rec['bytes'] != body or rec['wire'] != expected_wire:
                    raise AssertionError(f'row byte/wire accounting: {case["profile"]}:{i}:{variant}')
                if rec['output_sha256'] != model.digest(display):
                    raise AssertionError(f'decoded display hash mismatch: {case["profile"]}:{i}:{variant}')
                expected_metric = make_metrics(model, source['words'][i], display)
                if rec['metric'] != expected_metric:
                    raise AssertionError(f'RGB565 quality mismatch: {case["profile"]}:{i}:{variant}')
                if variant == 'hybrid' and expected_metric['hud_word_errors'] != 0:
                    raise AssertionError('hybrid HUD is not exact')
                variant_metrics_checked += 1
            decoded_outputs += 1
        for variant in ('bare', 'hybrid'):
            expected_summary = aggregate(rows, variant)
            given_summary = case['summary'][variant]
            for k, value in expected_summary.items():
                if isinstance(value, float):
                    if not close(given_summary[k], value):
                        raise AssertionError(f'native {variant} summary mismatch: {case["profile"]}:{k}')
                elif given_summary[k] != value:
                    raise AssertionError(f'native {variant} summary mismatch: {case["profile"]}:{k}')
        key_ids.add(tuple(ref['key_ids']))

    recomputed_ops = operating_points(cases, data['custom_baselines'])
    if recomputed_ops != data['operating_points']:
        raise AssertionError('sampled operating point selectors')
    if key_ids != {(0, 24)}:
        raise AssertionError('campaign key interval evidence')
    if not all('not matched quality' in item for item in [c['scope'] for c in data['operating_points']]):
        raise AssertionError('operating point claim boundary')
    if not any('currentCP23receiver acceptsAR03only' in item for item in data['scope']):
        raise AssertionError('native standard interoperability scope')
    if not any('No Gamebub standards decoder' in item for item in data['scope']):
        raise AssertionError('hardware claim boundary')

    lazy = audit_lazy_campaign()
    recovery = audit_recovery_campaign()
    return dict(status='verified', native_cases=len(cases), native_outputs=decoded_outputs,
                retained_rgb565_source_canvases_checked=source_rows_checked,
                v23_input_rgb_hash_links_checked=source_rows_checked,
                common_yuv420_source_tags_checked=yuv_tags_checked,
                exact_hc22_sidecars_checked=sidecars_checked, custom_baseline_rows_replayed=custom_recomputed,
                native_packet_blobs_checked=packets_checked, native_output_ids_redecoded=decoded_outputs,
                independently_recomputed_bare_hybrid_quality_rows=variant_metrics_checked,
                actual_native_profiles=sorted({c['profile'] for c in cases}),
                key_ids=sorted(next(iter(key_ids))),
                exact_hybrid_hud_words=decoded_outputs * 21120,
                operating_points_recomputed=len(recomputed_ops),
                lazy_ownership=lazy, recovery_profile_reset=recovery,
                scope=dict(source='Offline source evidence: each recorded RGB input hash links to its pinned v23 row; retained RGB565 canvases and YUV420 planes are digest/size checked; source videos are not reacquired',
                           native='Host PyAV/FFmpeg software reference only; no Game Bub HEVC/AV1 decoder or hardware fit proof',
                           timing='Native component timings do not prove end-to-end latency or sustained distinct-source 30 fps',
                           quality='Native codec parameters are not numerically comparable; selected actual points are not a BD-rate or perceptual match',
                           hybrid='Native decoded base plus exact actual HC22 sidecar; CP23 binding/ACK/transport charges are hypothetical'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = build_audit()
    target = HERE / 'audit.json'
    if args.check:
        if load(target) != result:
            raise SystemExit('audit.json differs from independent recomputation')
        print('PASS: v24 source pins, actual native streams, RGB565 quality, byte accounting, and claim limits')
    else:
        target.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
        print(f'wrote {target.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
