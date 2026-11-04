#!/usr/bin/env python3
"""Actual new-profile packets and interleaved plain/shared-analysis controls."""
from pathlib import Path
import hashlib
import importlib.util
import json
import math
import os
import platform
import sys
import time
import zlib
import numpy as np
import model as m

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OLD = HERE.parent / 'python-game-mandatory-hud-study'
OLD_CACHE = HERE.parent / 'python-game-hud-cache-study'
V22 = HERE.parent / 'python-game-joint-commit-study'
SHARED = HERE.parent / 'python-game-shared-analysis-study'


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(array):
    return hashlib.sha256(array.tobytes()).hexdigest()


def measured(fn):
    start = time.perf_counter_ns()
    value = fn()
    return value, (time.perf_counter_ns() - start) / 1e6


def blob(data):
    encoded = zlib.compress(data, 9)
    name = 'objects/' + hashlib.sha256(encoded).hexdigest() + '.zlib'
    p = HERE / name
    p.parent.mkdir(exist_ok=True)
    if not p.exists():
        p.write_bytes(encoded)
    return dict(path=name, raw_bytes=len(data), raw_sha256=hashlib.sha256(data).hexdigest(),
                stored_sha256=hashlib.sha256(encoded).hexdigest())


def raw(desc, folder=HERE):
    p = Path(desc['path'])
    assert not p.is_absolute() and '..' not in p.parts
    data = (folder / p).read_bytes()
    assert hashlib.sha256(data).hexdigest() == desc['stored_sha256']
    decoder = zlib.decompressobj()
    out = decoder.decompress(data, desc['raw_bytes'] + 1)
    assert decoder.eof and not decoder.unconsumed_tail and not decoder.unused_data
    assert len(out) == desc['raw_bytes'] and hashlib.sha256(out).hexdigest() == desc['raw_sha256']
    return out


def quality(source, display):
    a = m.C.corpus.expand565(source).astype(np.float64)
    b = m.C.corpus.expand565(display).astype(np.float64)
    summed = int(np.sum((a[37:442] - b[37:442]) ** 2))
    count = 405 * 720 * 3
    return summed, count, summed / count


def wire_counts(body_bytes, ack_bytes):
    fragments = math.ceil(body_bytes / 1008)
    return dict(fragments=fragments, data_forward_bytes=body_bytes + fragments * 75,
                frame_forward_control_bytes=128, frame_reverse_control_bytes=192,
                packet_credit_reverse_bytes=fragments * 57, joint_ack_reverse_bytes=ack_bytes + 28)


def counters(encoder):
    return dict(analyze_calls=int(encoder.analysis_count), forward_plane_calls=int(encoder.forward_calls))


def pins():
    paths = {ROOT / p for p in load(OLD / 'results.json')['source_sha256']}
    paths |= {OLD / 'results.json', OLD_CACHE / 'results.json', V22 / 'results.json', V22 / 'analysis.json',
              HERE.parent / 'python-game-gap-span-study/model.py',
              HERE.parent / 'python-game-hud-cache-study/model.py',
              HERE.parent / 'python-game-display-compose-study/model.py', V22 / 'model.py',
              SHARED / 'model.py', SHARED / 'test_model.py',
              HERE.parent / 'python-game-service-study/benchmark.py'}
    paths |= set(HERE.glob('*.py'))
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(paths)}


def one(sender, receiver, rgb, fid, policy, old_case, old_cached):
    old = old_case['rows'][fid]
    profiles = (tuple(old['selected_profile']),) if policy == 'fixed_v20_profiles' else None
    before = counters(sender.base)
    candidate, build_ms = measured(lambda: sender.build(rgb, fid, force_key=fid in (0, 24),
                                                       promote=fid in (8, 16, 32, 40), profiles=profiles))
    after = counters(sender.base)
    work = {k: after[k] - before[k] for k in before}
    row = dict(id=fid, input_sha256=digest(rgb), accepted=candidate.accepted,
               build_ms=build_ms, build_info=candidate.info, work=work)
    # end_source releases the analysis context before build returns. Retained
    # last_source_info records work/peak context arrays, not still-live storage.
    if hasattr(sender.base, 'last_source_info'):
        row['shared_source_info'] = sender.base.last_source_info
    assert candidate.accepted, (policy, fid, candidate.info)
    packet, commit_ms = measured(lambda: sender.commit(candidate))
    base, hud = m.compose.unbind(packet)
    meta = m.C.identity(base)
    before_publish = receiver.published_snapshot()
    task, prepare_ms = measured(lambda: receiver.prepare(packet))
    assert receiver.published_snapshot() == before_publish
    assert task.display.shape == (480, 720)
    yuv_tag = m.C.reference_tag(task.planes).hex()
    display_hash = digest(task.display)
    receiver.mark_writes_drained(task)
    ack, present_ms = measured(lambda: receiver.present(task, vblank=True))
    _, ack_ms = measured(lambda: sender.ack(ack))
    assert digest(receiver.display) == display_hash
    original = m.C.corpus.rgb565(rgb)
    for x, y, w, h in m.hc.RECTANGLES:
        np.testing.assert_array_equal(receiver.display[y:y + h, x:x + w], original[y:y + h, x:x + w])
    error_sum, error_count, mse = quality(original, receiver.display)
    row.update(packet=blob(packet), ack=blob(ack), packet_bytes=len(packet), ack_bytes=len(ack),
               base_bytes=len(base), hud_bytes=len(hud), selected_profile=candidate.info['selected_profile'],
               key=meta['key'], promoted=meta['promoted'], reference_bank=meta['reference_bank'],
               reference_id=meta['reference_id'], reference_tag=meta['reference_tag'].hex(),
               stored_tag=meta['stored_tag'].hex(), destination_bank=meta['destination_bank'],
               commit_ms=commit_ms, receive_prepare_ms=prepare_ms, present_ms=present_ms, ack_apply_ms=ack_ms,
               display_rgb565_sha256=display_hash, canonical_yuv_tag=yuv_tag,
               exact_hud_words=21120, active_squared_channel_error=error_sum,
               active_channel_samples=error_count, active_rgb565_channel_mse=mse,
               wire=wire_counts(len(packet), len(ack)),
               source_original_hud=old_cached['rows'][fid]['original_patches'])
    index = next((i for i, vector in enumerate(old_case['vectors']) if vector['id'] == fid), None)
    if index is not None:
        row['v20_source_vector_index'] = index
    return row


def summary(case):
    rows = case['rows']
    forward = sum(r['wire']['data_forward_bytes'] + r['wire']['frame_forward_control_bytes'] for r in rows)
    reverse = sum(sum(r['wire'][k] for k in ('frame_reverse_control_bytes', 'packet_credit_reverse_bytes',
                                           'joint_ack_reverse_bytes')) for r in rows)
    return dict(scene=case['scene'], policy=case['policy'], decisions=len(rows),
                complete_bytes=sum(r['packet_bytes'] for r in rows),
                maximum_complete_bytes=max(r['packet_bytes'] for r in rows),
                maximum_ack_bytes=max(r['ack_bytes'] for r in rows),
                exact_hud_words=sum(r['exact_hud_words'] for r in rows),
                mean_active_rgb565_channel_mse=sum(r['active_rgb565_channel_mse'] for r in rows) / len(rows),
                losing_builds=sum(sum(not a['accepted'] for a in r['build_info']['attempts']) for r in rows),
                total_analyze_calls=sum(r['work']['analyze_calls'] for r in rows),
                total_forward_plane_calls=sum(r['work']['forward_plane_calls'] for r in rows),
                paid_build_ms=sum(r['build_ms'] for r in rows),
                paid_receive_prepare_ms=sum(r['receive_prepare_ms'] for r in rows),
                forward_ipv4_udp_bytes=forward, reverse_ipv4_udp_bytes=reverse,
                projected_forward_Mbps_at30=forward / len(rows) * 30 * 8 / 1e6,
                projected_reverse_Mbps_at30=reverse / len(rows) * 30 * 8 / 1e6,
                profiles={str(p): sum(r['selected_profile'] == list(p) for r in rows)
                          for p in ((8, 16), (8, 32), (16, 32), (32, 32))})


def comparisons(cases):
    old = load(V22 / 'results.json')
    projections = load(V22 / 'analysis.json')
    out = []
    for scene in ('mass-effect-2600', 'mass-effect-7200'):
        fixed, plain, shared = [next(c for c in cases if c['scene'] == scene and c['policy'] == name)
                                for name in ('fixed_v20_profiles', 'adaptive_plain', 'adaptive_shared')]
        previous = next(c for c in old['cases'] if c['scene'] == scene and c['policy'] == 'adaptive')
        projected = next(c for c in projections['cases'] if c['scene'] == scene)
        byte_identical = []
        for a, b in zip(plain['rows'], shared['rows']):
            assert a['input_sha256'] == b['input_sha256']
            assert (a['packet']['raw_sha256'], a['ack']['raw_sha256'], a['display_rgb565_sha256'], a['canonical_yuv_tag']) == (
                b['packet']['raw_sha256'], b['ack']['raw_sha256'], b['display_rgb565_sha256'], b['canonical_yuv_tag'])
            assert a['selected_profile'] == b['selected_profile']
            byte_identical.append(a['id'])
        fixed_summary, plain_summary, shared_summary = (summary(c) for c in (fixed, plain, shared))
        assert fixed_summary['complete_bytes'] == projected['projected_hd22_pair_bytes']
        for row, expected in zip(fixed['rows'], projected['rows']):
            assert row['packet_bytes'] == expected['projected_hd22_pair_bytes']
        same_refs = [a['id'] for a, b in zip(plain['rows'], previous['rows'])
                     if all(a[k] == b[k] for k in ('key', 'promoted', 'reference_bank', 'reference_id', 'reference_tag'))]
        out.append(dict(scene=scene, exact_plain_shared_packet_ack_display_ids=byte_identical,
                        actual_fixed_total_bytes=fixed_summary['complete_bytes'],
                        previous_v22_hd22_projection_bytes=projected['projected_hd22_pair_bytes'],
                        plain_analyze_calls=plain_summary['total_analyze_calls'],
                        shared_analyze_calls=shared_summary['total_analyze_calls'],
                        plain_forward_plane_calls=plain_summary['total_forward_plane_calls'],
                        shared_forward_plane_calls=shared_summary['total_forward_plane_calls'],
                        paired_plain_build_ms=plain_summary['paid_build_ms'],
                        paired_shared_build_ms=shared_summary['paid_build_ms'],
                        measured_build_saving_percent=100 * (plain_summary['paid_build_ms'] - shared_summary['paid_build_ms']) / plain_summary['paid_build_ms'],
                        v22_adaptive_bytes=sum(r['packet_bytes'] for r in previous['rows']),
                        v23_adaptive_bytes=plain_summary['complete_bytes'],
                        v22_adaptive_mse=sum(r['active_rgb565_channel_mse'] for r in previous['rows']) / 48,
                        v23_adaptive_mse=plain_summary['mean_active_rgb565_channel_mse'],
                        same_reference_ids_vs_v22=same_refs,
                        scope='plain/shared same packets/images; v22-v23 adaptive histories may differ. Paired interleaved host timing is a single trial, not target calibration or universal speedup.'))
    return out


def main():
    before = pins()
    sharing = load_module('joint23_shared_source', SHARED / 'model.py')
    source = load_module('joint23_native_source', HERE.parent / 'python-game-service-study/benchmark.py')
    old = load(OLD / 'results.json')
    cache = load(OLD_CACHE / 'results.json')
    media = Path(os.environ.get('GAMEBUB_MEDIA_DIR', str(HERE.parents[3] / 'media')))
    cases = []
    for scene in ('mass-effect-2600', 'mass-effect-7200'):
        frames, manifest = source.native(media / (scene + '.mp4'), n=48, start=4)
        old_case = next(c for c in old['cases'] if c['scene'] == scene and c['policy'] == 'mandatory')
        old_cached = next(c for c in cache['cases'] if c['name'] == scene)
        names = ('fixed_v20_profiles', 'adaptive_plain', 'adaptive_shared')
        senders = {name: m.JointSender(base_encoder_class=sharing.SharedEncoder if name == 'adaptive_shared' else m.C.Encoder) for name in names}
        receivers = {name: m.JointReceiver() for name in names}
        local = {name: dict(scene=scene, policy=name, manifest=manifest, rows=[]) for name in names}
        box_times = []
        for fid, native in enumerate(frames):
            (rgb, _), box_ms = measured(lambda: m.C.corpus._letterbox(native, 720, 480))
            box_times.append(box_ms)
            assert digest(rgb) == old_case['rows'][fid]['input_sha256']
            order = ('adaptive_plain', 'adaptive_shared') if fid % 2 == 0 else ('adaptive_shared', 'adaptive_plain')
            for name in ('fixed_v20_profiles', *order):
                local[name]['rows'].append(one(senders[name], receivers[name], rgb, fid, name, old_case, old_cached))
        manifest['box_ms_shared_per_acquisition'] = box_times
        for name in names:
            cases.append(local[name])
            print(json.dumps(summary(local[name])), flush=True)
    assert before == pins(), 'source changed during campaign'
    data = dict(schema='gamebub-integrated-hd22-v23', source_sha256=before, cases=cases,
                summary=[summary(c) for c in cases], comparisons=comparisons(cases),
                counts=dict(source_acquisitions=96, frame_decisions=288, cases=6),
                versions=dict(python=platform.python_version(), numpy=np.__version__),
                scope=[
                    'Actual HC22/HA22/CP23/JA23 serialization and receiver decode. Older profiles fail closed; capability/reset handshake is not implemented.',
                    'Fixed-v20-map trace is an offline image/byte control, not a causal mode selector or fair performance baseline.',
                    'Adaptive plain/shared controls run interleaved per source with alternating order. All context prep/validation/cleanup and actual rejected build work are inside build_ms; no hidden precomputed analysis.',
                    'Single paired host trial. Analysis/forward-call elimination is exact work evidence; Python timing has no native/ESP32/DSP throughput interpretation.',
                    'Both clips are reused precompressed29.88fps regression windows; 96 acquisitions reused across288 decisions, not fresh live30fps.',
                    'BOX is measured once per acquired source and shared by all three controls; offline PyAV extraction, diagnostic hash/quality/original-word comparisons and object export excluded from build clocks.',
                    'Array/storage counters do not measure total heap or mapped BRAM/SRAM. Source-analysis cache resides on the host, not ESP32.',
                    'Injected write-drain/vblank calls are logical permissions, not DMA/CDC/physical memory fences. Native endpoints, RF/QSPI/FIFO schedule, resource/timing fit and physical30fps remain open.'])
    (HERE / 'results.json').write_text(json.dumps(data, separators=(',', ':'), allow_nan=False) + '\n')


if __name__ == '__main__':
    main()
