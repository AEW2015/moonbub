#!/usr/bin/env python3
"""Replay actual v20 base goldens with HC21; reconcile real-source byte budgets."""
from pathlib import Path
import hashlib
import json
import platform
import time
import zlib
import numpy as np
import model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OLD = HERE.parent / 'python-game-mandatory-hud-study'
CACHE = HERE.parent / 'python-game-hud-cache-study'
C = model.codec


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text())


def raw(desc, folder=OLD):
    p = Path(desc['path'])
    assert not p.is_absolute() and '..' not in p.parts
    stored = (folder / p).read_bytes()
    assert hashlib.sha256(stored).hexdigest() == desc['stored_sha256']
    decoder = zlib.decompressobj()
    result = decoder.decompress(stored, desc['raw_bytes'] + 1)
    assert decoder.eof and not decoder.unused_data and not decoder.unconsumed_tail
    assert len(result) == desc['raw_bytes'] and hashlib.sha256(result).hexdigest() == desc['raw_sha256']
    return result


def array(desc):
    assert desc['dtype'] in ('|u1', '<i2', '<u2')
    return np.frombuffer(raw(desc['blob']), dtype=desc['dtype']).reshape(desc['shape'])


def blob(data):
    b = zlib.compress(data, 9)
    folder = HERE / 'objects'
    folder.mkdir(exist_ok=True)
    name = hashlib.sha256(b).hexdigest() + '.cb21.zlib'
    (folder / name).write_bytes(b)
    return dict(path='objects/' + name, stored_sha256=hashlib.sha256(b).hexdigest(),
                raw_sha256=hashlib.sha256(data).hexdigest(), raw_bytes=len(data))


def decode_base(packet, fixture):
    rx = C.Receiver()
    for slot, b in fixture['pre_banks'].items():
        if b is not None:
            planes = tuple(array(p) for p in b['planes'])
            assert C.reference_tag(planes).hex() == b['tag']
            rx.banks[int(slot)] = C.Bank(b['id'], bytes.fromhex(b['tag']), planes)
    rx.last_frame_id = fixture['id'] - 1
    task = rx.begin(packet)
    samples = 0
    for plane, expected in zip(task.planes, fixture['decoded_yuv']):
        np.testing.assert_array_equal(plane, array(expected))
        samples += plane.size
    rgb, info, ack = rx.complete(task)
    assert ack == C.feedback(C.identity(packet))
    assert not info['patches'] and not rx.readers and rx.active is None
    for slot, b in fixture['post_banks'].items():
        bank = rx.banks[int(slot)]
        assert (bank is None) == (b is None)
        if bank is not None:
            assert (bank.frame_id, bank.tag.hex()) == (b['id'], b['tag'])
    return C.corpus.rgb565(rgb), samples


def replay_vector(packet, fixture, rx):
    base, hud = model.unbind(packet, enforce_frame_cap=False)
    display, samples = decode_base(base, fixture)
    ack = rx.receive(hud)
    for rect, patch in zip(model.cache.RECTANGLES, rx.display['patches']):
        x, y, w, h = rect
        display[y:y + h, x:x + w] = patch
    np.testing.assert_array_equal(display, array(fixture['display_rgb565']))
    return ack, display.size, samples


def pins():
    paths = {ROOT / p for p in read_json(OLD / 'results.json')['source_sha256']}
    paths |= {OLD / 'results.json', CACHE / 'results.json'}
    paths |= set((OLD / 'objects').glob('*'))
    for folder in (HERE, CACHE, HERE.parent / 'python-game-hud-delta-study'):
        paths |= set(folder.glob('*.py'))
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(paths)}


def budget(cases):
    old = {case['scene']: case for case in read_json(OLD / 'results.json')['cases'] if case['policy'] == 'mandatory'}
    summaries = []
    for case in cases:
        scene = case['name']
        if scene not in old:
            continue
        source = old[scene]
        assert len(case['rows']) == len(source['rows']) == 48
        rows = []
        for row, previous in zip(case['rows'], source['rows']):
            assert row['frame'] == previous['id']
            assert row['source_sha256'] == previous['input_sha256']
            assert row['legacy_patch_bytes'] == previous['patch_bytes']
            original = previous['packet_bytes']
            combined = original - previous['patch_bytes'] + row['sidecar_bytes'] + model.OVERHEAD
            legacy = model.transport_counts(original)
            proposed = model.transport_counts(combined, row['ack_bytes'])
            rows.append(dict(id=row['frame'], original_complete_bytes=original, cb21_complete_bytes=combined,
                             complete_cap_fits=combined <= model.FRAME_CAP,
                             unchanged_base_bytes=original - previous['patch_bytes'],
                             hud_sidecar_bytes=row['sidecar_bytes'], fixture_binding_bytes=model.OVERHEAD,
                             legacy_transport=legacy, proposed_transport=proposed,
                             network_bound_sweep=[model.necessary_network_bound(proposed, rate, delay)
                                                  for rate in (8, 12, 16, 24, 40)
                                                  for delay in (0, 5, 15, 30, 40)]))
        sums = {}
        for name in ('legacy_transport', 'proposed_transport'):
            forward = sum(r[name]['data_forward_bytes'] + r[name]['frame_forward_control_bytes'] for r in rows)
            reverse = sum(sum(r[name][k] for k in ('frame_reverse_control_bytes', 'packet_credit_reverse_bytes',
                                                  'reference_ack_reverse_bytes', 'hud_ack_reverse_bytes')) for r in rows)
            sums[name] = dict(forward_ipv4_udp_bytes=forward, reverse_ipv4_udp_bytes=reverse,
                              forward_Mbps_at30=forward / 48 * 30 * 8 / 1e6,
                              reverse_Mbps_at30=reverse / 48 * 30 * 8 / 1e6)
        original = sum(r['original_complete_bytes'] for r in rows)
        proposed = sum(r['cb21_complete_bytes'] for r in rows)
        summaries.append(dict(scene=scene, frames=len(rows),
                              original_complete_bytes=original, cb21_complete_bytes=proposed,
                              complete_saving_percent=100 * (original - proposed) / original,
                              complete_cap_fits=sum(r['complete_cap_fits'] for r in rows),
                              maximum_complete_bytes=max(r['cb21_complete_bytes'] for r in rows),
                              minimum_complete_bytes=min(r['cb21_complete_bytes'] for r in rows),
                              transport=sums, rows=rows))
    assert len(summaries) == 2
    return summaries


def main():
    source_pins = pins()
    start = time.perf_counter()
    old = read_json(OLD / 'results.json')
    vectors = []
    for case in old['cases']:
        if case['policy'] != 'mandatory':
            continue
        sender, rx = model.cache.Sender(), model.cache.Receiver()
        for index, fixture in enumerate(case['vectors']):
            base = model.strip_patches(raw(fixture['packet']))
            hud, info = sender.prepare(array(fixture['source']), fixture['id'])
            pair = model.bind(base, hud)
            assert model.unbind(pair, enforce_frame_cap=False) == (base, hud)
            fits = len(pair) <= model.FRAME_CAP
            if fits:
                assert model.unbind(pair) == (base, hud)
            else:
                try:
                    model.unbind(pair)
                except ValueError:
                    pass
                else:
                    raise AssertionError('oversized pair admitted')
            bad = pair[:-1] + bytes([pair[-1] ^ 1])
            before = (rx.last_frame, rx.last_generation, rx.last_bodytag)
            try:
                model.unbind(bad)
            except ValueError:
                pass
            else:
                raise AssertionError('corrupt pair admitted')
            assert before == (rx.last_frame, rx.last_generation, rx.last_bodytag)
            ack, pixels, samples = replay_vector(pair, fixture, rx)
            sender.accept_ack(ack)
            vectors.append(dict(scene=case['scene'], fixture_index=index, id=fixture['id'],
                                packet=blob(pair), base_bytes=len(base), hud_bytes=len(hud),
                                complete_bytes=len(pair), complete_cap_fits=fits,
                                exact_display_words=pixels, exact_yuv_samples=samples,
                                negative_crc_rejected=True, original_packet_sha256=fixture['packet']['raw_sha256']))
    cache_result = read_json(CACHE / 'results.json')
    summaries = budget(cache_result['cases'])
    assert source_pins == pins(), 'source changed during run'
    result = dict(schema='gamebub-display-compose-v21', source_sha256=source_pins,
                  vectors=vectors, budgets=summaries,
                  exact_display_words=sum(v['exact_display_words'] for v in vectors),
                  exact_yuv_samples=sum(v['exact_yuv_samples'] for v in vectors),
                  python_wall_seconds=time.perf_counter() - start,
                  versions=dict(python=platform.python_version(), numpy=np.__version__),
                  limits=[
                      'CB21 is an offline fixture container, not an implemented GF03 or endpoint profile.',
                      'Positive component replay also checks over-cap fixtures diagnostically. Cap rejection is a separate gate; no candidate-admission policy or joint atomic base/HUD publication is implemented.',
                      'Old base bytes, quantization, reference history and reconstructed YUV are preserved. New HC21 cache history is display-only.',
                      'Native rows use the same two reused 48-frame 29.88fps source windows as v20; scheduled30 arithmetic is not live30fps.',
                      'Necessary network bounds permit independent-direction overlap and omit CPU/DMA/QSPI/scanout/RF/retries/input/audio. HA21 bytes are counted, not cache-ACK latency calibration.',
                      'No new ESP32, native Sunshine endpoint, RTL, resource or physical30fps proof.'])
    (HERE / 'results.json').write_text(json.dumps(result, separators=(',', ':'), allow_nan=False) + '\n')
    print(json.dumps({k: result[k] for k in ('schema', 'exact_display_words', 'exact_yuv_samples', 'python_wall_seconds')}, indent=2))
    for summary in summaries:
        print(json.dumps({k: v for k, v in summary.items() if k != 'rows'}, indent=2))


if __name__ == '__main__':
    main()
