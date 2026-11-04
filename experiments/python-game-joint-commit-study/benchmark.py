#!/usr/bin/env python3
"""Actual sequential joint candidates, private decode and gated publication.

Offline native source decode is excluded; all candidate attempts are measured.
No capture clock, ESP32 execution, RF, QSPI or hardware FPS is modeled here.
"""
from pathlib import Path
import hashlib
import json
import os
import platform
import time
import zlib
import numpy as np
import model as m

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OLD = HERE.parent / 'python-game-mandatory-hud-study'
OLD_CACHE = HERE.parent / 'python-game-hud-cache-study'
OLD_COMPOSE = HERE.parent / 'python-game-display-compose-study'


def read_json(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(a):
    return hashlib.sha256(a.tobytes()).hexdigest()


def measured(fn):
    t = time.perf_counter_ns()
    out = fn()
    return out, (time.perf_counter_ns() - t) / 1e6


def blob(data):
    compressed = zlib.compress(data, 9)
    name = 'objects/' + hashlib.sha256(compressed).hexdigest() + '.zlib'
    p = HERE / name
    p.parent.mkdir(exist_ok=True)
    if not p.exists():
        p.write_bytes(compressed)
    return dict(path=name, raw_bytes=len(data), raw_sha256=hashlib.sha256(data).hexdigest(),
                stored_sha256=hashlib.sha256(compressed).hexdigest())


def raw(desc, folder=HERE):
    path = Path(desc['path'])
    assert not path.is_absolute() and '..' not in path.parts
    data = (folder / path).read_bytes()
    assert hashlib.sha256(data).hexdigest() == desc['stored_sha256']
    dec = zlib.decompressobj()
    out = dec.decompress(data, desc['raw_bytes'] + 1)
    assert dec.eof and not dec.unconsumed_tail and not dec.unused_data
    assert len(out) == desc['raw_bytes'] and hashlib.sha256(out).hexdigest() == desc['raw_sha256']
    return out


def mse(source_words, display):
    a = m.C.corpus.expand565(source_words).astype(np.float64)
    b = m.C.corpus.expand565(display).astype(np.float64)
    squared_sum = int(np.sum((a[37:442] - b[37:442]) ** 2))
    count = 405 * 720 * 3
    return squared_sum, count, squared_sum / count


def wire_counts(body_bytes, ack_bytes):
    d = m.compose.transport_counts(body_bytes, m.hc.ACK.size + 4)
    # Joint JA22 replaces two independent AF03/HA21 datagrams. Preserve all
    # frame controls and per-fragment PC18 permits as separate byte accounting.
    d['reference_ack_reverse_bytes'] = 0
    d['hud_ack_reverse_bytes'] = 0
    d['joint_ack_reverse_bytes'] = ack_bytes + 28
    return d


def pins():
    old = read_json(OLD / 'results.json')
    paths = {ROOT / p for p in old['source_sha256']}
    paths |= {OLD / 'results.json', OLD_CACHE / 'results.json', OLD_COMPOSE / 'results.json',
              Path(m.hc.__file__), Path(m.compose.__file__), Path(m.hc.hd.__file__),
              HERE.parent / 'python-game-service-study/benchmark.py'}
    paths |= {HERE / name for name in ('model.py', 'test_model.py', 'benchmark.py', 'verify.py')}
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(paths)}


def summary(case):
    rows = case['rows']
    good = [r for r in rows if r['accepted']]
    forward = sum(r['wire']['data_forward_bytes'] + r['wire']['frame_forward_control_bytes'] for r in good)
    reverse = sum(sum(r['wire'][k] for k in ('frame_reverse_control_bytes', 'packet_credit_reverse_bytes',
                                           'joint_ack_reverse_bytes')) for r in good)
    return dict(scene=case['scene'], policy=case['policy'], decisions=len(rows), commits=len(good),
                whole_frame_rejects=len(rows) - len(good), exact_hud_words=sum(r['exact_hud_words'] for r in good),
                complete_bytes=sum(r['packet_bytes'] for r in good),
                maximum_complete_bytes=max((r['packet_bytes'] for r in good), default=0),
                maximum_ack_bytes=max((r['ack_bytes'] for r in good), default=0),
                mean_active_rgb565_channel_mse=sum(r['active_rgb565_channel_mse'] for r in good) / len(good),
                paid_build_ms=sum(r['build_ms'] for r in rows),
                paid_receive_prepare_ms=sum(r['receive_prepare_ms'] for r in good),
                paid_present_ms=sum(r['present_ms'] for r in good),
                forward_ipv4_udp_bytes=forward, reverse_ipv4_udp_bytes=reverse,
                projected_forward_Mbps_at30=forward / len(rows) * 30 * 8 / 1e6,
                projected_reverse_Mbps_at30=reverse / len(rows) * 30 * 8 / 1e6,
                profiles={str(p): sum(r['selected_profile'] == list(p) for r in good)
                          for p in ((8, 16), (8, 32), (16, 32), (32, 32))})


def run_case(scene, policy, frames, manifest, old_case, old_cached, old_budgets):
    sender, receiver = m.JointSender(), m.JointReceiver()
    rows = []
    for fid, native in enumerate(frames):
        (rgb, _), box_ms = measured(lambda: m.C.corpus._letterbox(native, 720, 480))
        old = old_case['rows'][fid]
        assert digest(rgb) == old['input_sha256']
        before = sender.snapshot()
        profiles = (tuple(old['selected_profile']),) if policy == 'fixed_v20_profiles' else None
        c, build_ms = measured(lambda: sender.build(rgb, fid, force_key=fid in (0, 24),
                                                     promote=fid in (8, 16, 32, 40), profiles=profiles))
        row = dict(id=fid, input_sha256=digest(rgb), box_ms=box_ms, build_ms=build_ms,
                   accepted=c.accepted, build_info=c.info)
        if not c.accepted:
            assert sender.snapshot() == before
            if sender.active_candidate is c:
                sender.discard(c)
            assert sender.snapshot() == before
            rows.append(row)
            continue
        packet, commit_ms = measured(lambda: sender.commit(c))
        base, hud = m.compose.unbind(packet)
        meta = m.C.identity(base)
        rx_before = receiver.published_snapshot()
        task, prepare_ms = measured(lambda: receiver.prepare(packet))
        # Private reconstruction is observable to this diagnostic oracle, not
        # to scanout or ACK consumers. Its contents cannot publish by decoding.
        assert receiver.published_snapshot() == rx_before
        canonical = m.C.reference_tag(task.planes).hex()
        private_display = digest(task.display)
        receiver.mark_writes_drained(task)
        ack, present_ms = measured(lambda: receiver.present(task, vblank=True))
        assert digest(receiver.display) == private_display
        _, ack_ms = measured(lambda: sender.ack(ack))
        expected = m.C.corpus.rgb565(rgb)
        exact = 0
        for x, y, w, h in m.hc.RECTANGLES:
            np.testing.assert_array_equal(receiver.display[y:y + h, x:x + w], expected[y:y + h, x:x + w])
            exact += w * h
        error_sum, error_count, error_mse = mse(expected, receiver.display)
        row.update(packet=blob(packet), ack=blob(ack), packet_bytes=len(packet), ack_bytes=len(ack),
                   base_bytes=len(base), hud_bytes=len(hud), selected_profile=c.info['selected_profile'],
                   key=meta['key'], promoted=meta['promoted'], reference_bank=meta['reference_bank'],
                   reference_id=meta['reference_id'], reference_tag=meta['reference_tag'].hex(),
                   stored_tag=meta['stored_tag'].hex(), destination_bank=meta['destination_bank'],
                   commit_ms=commit_ms, receive_prepare_ms=prepare_ms, present_ms=present_ms, ack_apply_ms=ack_ms,
                   display_rgb565_sha256=private_display, canonical_yuv_tag=canonical, exact_hud_words=exact,
                   active_squared_channel_error=error_sum, active_channel_samples=error_count,
                   active_rgb565_channel_mse=error_mse, wire=wire_counts(len(packet), len(ack)),
                   receiver_persistent_yuv_array_bytes=receiver.base.retained_bytes(),
                   receiver_hud_array_bytes=sum(p.nbytes for bank in receiver.hud.banks if bank is not None for p in bank['patches']),
                   visible_rgb565_array_bytes=receiver.display.nbytes,
                   private_reconstruction_yuv_array_bytes=sum(p.nbytes for p in task.planes),
                   source_original_hud=old_cached['rows'][fid]['original_patches'])
        matching = next((i for i, v in enumerate(old_case['vectors']) if v['id'] == fid), None)
        if matching is not None:
            row['v20_source_vector_index'] = matching
        if policy == 'fixed_v20_profiles':
            assert len(packet) == old_budgets['rows'][fid]['cb21_complete_bytes']
            assert error_mse == old['active_rgb565_mse']
            for k in ('reference_bank', 'reference_id', 'reference_tag', 'stored_tag', 'destination_bank'):
                old_value = old[k]
                current = row[k]
                assert current == old_value, (scene, fid, k, current, old_value)
        rows.append(row)
    return dict(scene=scene, policy=policy, manifest=manifest, rows=rows)


def comparisons(cases):
    out = []
    for scene in ('mass-effect-2600', 'mass-effect-7200'):
        fixed, adaptive = [c for c in cases if c['scene'] == scene]
        a = {r['id']: r for r in fixed['rows'] if r['accepted']}
        b = {r['id']: r for r in adaptive['rows'] if r['accepted']}
        ids = sorted(a.keys() & b.keys())
        same_refs = [i for i in ids if all(a[i][k] == b[i][k] for k in ('key', 'promoted', 'reference_bank', 'reference_id', 'reference_tag'))]
        out.append(dict(scene=scene, matched_source_ids=ids, same_reference_ids=same_refs,
                        fixed_total_bytes=sum(a[i]['packet_bytes'] for i in ids),
                        adaptive_total_bytes=sum(b[i]['packet_bytes'] for i in ids),
                        fixed_mean_mse=sum(a[i]['active_rgb565_channel_mse'] for i in ids) / len(ids),
                        adaptive_mean_mse=sum(b[i]['active_rgb565_channel_mse'] for i in ids) / len(ids),
                        same_reference_fixed_mean_mse=sum(a[i]['active_rgb565_channel_mse'] for i in same_refs) / len(same_refs),
                        same_reference_adaptive_mean_mse=sum(b[i]['active_rgb565_channel_mse'] for i in same_refs) / len(same_refs),
                        scope='same sources; adapted keys/promotions change later predictor history, so aggregate is a rate/quality policy comparison'))
    return out


def main():
    before = pins()
    source = m.hc.load('joint22_native_source', HERE.parent / 'python-game-service-study/benchmark.py')
    old = read_json(OLD / 'results.json')
    cached = read_json(OLD_CACHE / 'results.json')
    budgets = read_json(OLD_COMPOSE / 'results.json')
    media = Path(os.environ.get('GAMEBUB_MEDIA_DIR', str(HERE.parents[3] / 'media')))
    cases = []
    for scene in ('mass-effect-2600', 'mass-effect-7200'):
        native, manifest = source.native(media / (scene + '.mp4'), n=48, start=4)
        old_case = next(c for c in old['cases'] if c['scene'] == scene and c['policy'] == 'mandatory')
        old_cached = next(c for c in cached['cases'] if c['name'] == scene)
        old_budgets = next(c for c in budgets['budgets'] if c['scene'] == scene)
        for policy in ('fixed_v20_profiles', 'adaptive'):
            case = run_case(scene, policy, native, manifest, old_case, old_cached, old_budgets)
            cases.append(case)
            print(json.dumps(summary(case)), flush=True)
    assert before == pins(), 'source changed during campaign'
    result = dict(schema='gamebub-joint-commit-v22', source_sha256=before, cases=cases,
                  summary=[summary(c) for c in cases], comparisons=comparisons(cases),
                  counts=dict(source_acquisitions=96, frame_decisions=192, cases=4),
                  versions=dict(python=platform.python_version(), numpy=np.__version__),
                  scope=[
                      'Actual Python build/admit/commit/private decode/write-gate/vblank publication/jointACK; no transport event or physical timing model.',
                      'All bounded map attempts and competing HUD encoders are paid in build_ms. Offline PyAV source decode, verification/export/correctness work and quality/tag diagnostic oracles excluded.',
                      'Two existing precompressed29.88fps source windows, reused across controls, not fresh live30fps.',
                      'Fixed profile sequence matches v20 base history and v21 composition bytes. Adaptive selects from current complete bytes, changes quality and later prediction; not a pure entropy gain.',
                      'Fixed-profile control replays the stored v20 selected-map trace, intentionally omitting that older controller search; it is an image/byte control, not a deployable causal selector or fair host-service baseline.',
                      'Explicit synchronous write-drain/vblank calls are functional permissions, not actual DMA/fence/CDC or line-deadline proof.',
                      'Recorded ndarray bytes are named arrays, not total allocator peak, FPGA memory mapping or ESP32 SRAM/DMA calibration.',
                      'CB21/JA22 are laboratory profile bytes; installed endpoints, RF/QSPI/FIFO transport, reset negotiation and FPGA RTL/resource/timing/physical30fps remain unimplemented.'])
    (HERE / 'results.json').write_text(json.dumps(result, separators=(',', ':'), allow_nan=False) + '\n')


if __name__ == '__main__':
    main()
