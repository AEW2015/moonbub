#!/usr/bin/env python3
"""Same-source standard/native codecs and exact-HUD hybrid comparisons."""
from pathlib import Path
import hashlib
import json
import os
import platform
import time
import zlib
import av
import numpy as np
import model as m

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
V23 = HERE.parent / 'python-game-hd22-joint-study'


def load(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def blob(data):
    stored = zlib.compress(data, 9)
    name = 'objects/' + hashlib.sha256(stored).hexdigest() + '.zlib'
    target = HERE / name
    target.parent.mkdir(exist_ok=True)
    if not target.exists():
        target.write_bytes(stored)
    return dict(path=name, raw_bytes=len(data), raw_sha256=hashlib.sha256(data).hexdigest(),
                stored_sha256=hashlib.sha256(stored).hexdigest())


def raw(desc, folder=HERE):
    relative = Path(desc['path'])
    assert not relative.is_absolute() and '..' not in relative.parts
    stored = (folder / relative).read_bytes()
    assert hashlib.sha256(stored).hexdigest() == desc['stored_sha256']
    dec = zlib.decompressobj()
    out = dec.decompress(stored, desc['raw_bytes'] + 1)
    assert dec.eof and not dec.unused_data and not dec.unconsumed_tail
    assert len(out) == desc['raw_bytes'] and hashlib.sha256(out).hexdigest() == desc['raw_sha256']
    return out


def original(desc):
    return np.frombuffer(raw(desc), '<u2').reshape(480, 720)


def common_tag(planes):
    h = hashlib.sha256()
    for p in planes:
        h.update(p.astype(np.uint8).tobytes())
    return h.hexdigest()


def aggregate(rows, variant):
    records = [r[variant] for r in rows]
    summed = sum(x['metric']['active_squared_error'] for x in records)
    samples = sum(x['metric']['active_channel_samples'] for x in records)
    mse = summed / samples
    complete = sum(x['bytes'] for x in records)
    forward = sum(x['wire']['forward_data_ip_udp_bytes'] + x['wire']['frame_forward_control_bytes'] for x in records)
    reverse = sum(x['wire']['reverse_model_bytes'] for x in records)
    return dict(frames=len(rows), complete_bytes=complete,
                coded_body_Mbps_at30=complete / len(rows) * 30 * 8 / 1e6,
                mean_bytes=complete / len(rows), maximum_bytes=max(x['bytes'] for x in records),
                cap_fit_frames=sum(x['bytes'] <= 49152 for x in records),
                active_squared_error=summed, active_channel_samples=samples, active_mse=mse,
                active_psnr_db=None if mse == 0 else 10 * np.log10(65025 / mse),
                hud_word_errors=sum(x['metric']['hud_word_errors'] for x in records),
                hypothetical_forward_Mbps_at30=forward / len(rows) * 30 * 8 / 1e6,
                hypothetical_reverse_Mbps_at30=reverse / len(rows) * 30 * 8 / 1e6)


def source_inputs(scene, old, source):
    media = Path(os.environ.get('GAMEBUB_MEDIA_DIR', str(HERE.parents[3] / 'media')))
    acquired, manifest = source.native(media / (scene + '.mp4'), n=48, start=4)
    reference = next(c for c in old['cases'] if c['scene'] == scene and c['policy'] == 'adaptive_plain')
    frames, planes, rows, patches = [], [], [], []
    cache = m.joint.hc.Receiver()
    for i, native in enumerate(acquired):
        start = time.perf_counter_ns()
        rgb, _ = m.C.corpus._letterbox(native, 720, 480)
        box_ms = (time.perf_counter_ns() - start) / 1e6
        assert m.digest(rgb) == reference['rows'][i]['input_sha256']
        packet = raw(reference['rows'][i]['packet'], V23)
        _, hud = m.joint.compose.unbind(packet)
        cache.receive(hud)
        current = tuple(p.copy() for p in cache.display['patches'])
        words = m.C.corpus.rgb565(rgb)
        for (x, y, w, h), p in zip(m.RECTANGLES, current):
            np.testing.assert_array_equal(p, words[y:y+h, x:x+w])
        start = time.perf_counter_ns()
        planar = m.C.gm.ft.rgb_to_planes(rgb)
        conversion_ms = (time.perf_counter_ns() - start) / 1e6
        floor = m.C.corpus.rgb565(m.C.gm.ft.planes_to_rgb(planar))
        common_bytes = b''.join(p.astype(np.uint8).tobytes() for p in planar)
        rows.append(dict(id=i, input_rgb_sha256=m.digest(rgb), original_rgb565=blob(words.astype('<u2').tobytes()),
                         common_yuv420_u8_sha256=common_tag(planar), common_yuv420_u8=blob(common_bytes), hc22=blob(hud),
                         box_ms=box_ms, common_input_color_ms=conversion_ms,
                         no_compression_roundtrip_bare=m.metric(words, floor),
                         no_compression_roundtrip_hybrid=m.metric(words, m.overlay(floor, current))))
        frames.append(rgb)
        planes.append(planar)
        patches.append(current)
    return frames, planes, patches, dict(scene=scene, manifest=manifest, rows=rows)


def custom_baselines(scene, old, inputs, patches):
    cases = []
    for policy in ('fixed_v20_profiles', 'adaptive_plain'):
        reference = next(c for c in old['cases'] if c['scene'] == scene and c['policy'] == policy)
        rx = m.C.Receiver()
        rows = []
        for i, previous in enumerate(reference['rows']):
            pair = raw(previous['packet'], V23)
            base, hud = m.joint.compose.unbind(pair)
            base_rgb, _, _ = rx.receive(base)
            bare = m.C.corpus.rgb565(base_rgb)
            combined = m.overlay(bare, patches[i])
            source = original(inputs['rows'][i]['original_rgb565'])
            assert m.digest(combined) == previous['display_rgb565_sha256']
            bm, hm = m.metric(source, bare), m.metric(source, combined)
            assert hm['active_mse'] == previous['active_rgb565_channel_mse']
            assert len(pair) == len(base) + len(hud) + 57
            rows.append(dict(id=i, bare=dict(bytes=len(base), metric=bm, wire=m.accounting(len(base)),
                                           output_sha256=m.digest(bare)),
                             hybrid=dict(bytes=len(pair), metric=hm,
                                         wire=m.accounting(len(base), len(hud), binding=True),
                                         output_sha256=m.digest(combined))))
        cases.append(dict(scene=scene, codec='custom', profile=policy, rows=rows,
                          summary=dict(bare=aggregate(rows, 'bare'), hybrid=aggregate(rows, 'hybrid')),
                          scope='Frozen v23 AR03 base and actual CP23 complete bytes; fixed map trace is an image/byte control, not a causal timing baseline.'))
    return cases


def native_case(scene, name, parameter, planes, inputs, patches):
    print('BEGIN', scene, name, parameter, flush=True)
    packets, extras, info = m.encode(planes, name, parameter)
    output, decoder_info = m.decode(packets, extras, name)
    assert sorted(output) == list(range(48))
    pts = [p['pts'] for p in packets]
    assert pts == list(range(48)), pts
    assert [p['dts'] for p in packets] == pts
    keys = [p['pts'] for p in packets if p['is_key']]
    assert keys == [0, 24], keys
    assert info['packets_only_at_flush'] == 0
    assert decoder_info['frames_only_at_decode_flush'] == 0
    assert [c['emitted_pts'] for c in info['frame_calls']] == [[i] for i in range(48)]
    rows = []
    encoded = []
    for i, p in enumerate(packets):
        original_words = original(inputs['rows'][i]['original_rgb565'])
        bare = output[i]
        hybrid = m.overlay(bare, patches[i])
        count = len(p['data']) + (len(extras) if i == 0 else 0)
        hud_bytes = inputs['rows'][i]['hc22']['raw_bytes']
        rows.append(dict(id=i, coded_access_unit_bytes=count,
                         bare=dict(bytes=count, metric=m.metric(original_words, bare),
                                   wire=m.accounting(count), output_sha256=m.digest(bare)),
                         hybrid=dict(bytes=count + hud_bytes + 57, metric=m.metric(original_words, hybrid),
                                     wire=m.accounting(count, hud_bytes, binding=True), output_sha256=m.digest(hybrid))))
        encoded.append(dict(pts=p['pts'], dts=p['dts'], is_key=p['is_key'], bytes=len(p['data']), packet=blob(p['data'])))
    info.update(decoder_info)
    info.update(packets=encoded, extradata=blob(extras), extradata_bytes=len(extras), key_ids=keys,
                encode_codec_total_ms=sum(x['encode_ms'] for x in info['frame_calls']) + info['encoder_flush_ms'],
                decode_codec_total_ms=sum(x['decode_ms'] for x in info['decode_calls']) + info['decoder_flush_ms'],
                output_pixel_contract='common frozen YUV420 samples -> native decode -> frozen RGB conversion -> RGB565')
    case = dict(scene=scene, codec=name, profile=name + '_q' + str(parameter), parameter=parameter,
                rows=rows, reference=info,
                summary=dict(bare=aggregate(rows, 'bare'), hybrid=aggregate(rows, 'hybrid')))
    print(json.dumps(dict(scene=scene, codec=name, parameter=parameter, summary=case['summary'],
                          encode_codec_total_ms=info['encode_codec_total_ms'], decode_codec_total_ms=info['decode_codec_total_ms'])), flush=True)
    return case


def operating_points(cases, baselines):
    out = []
    for custom in baselines:
        for variant in ('bare', 'hybrid'):
            target = custom['summary'][variant]
            for name in ('libx265', 'libsvtav1'):
                cohort = [c for c in cases if c['scene'] == custom['scene'] and c['codec'] == name]
                eligible = [c for c in cohort if c['summary'][variant]['active_mse'] <= target['active_mse']]
                picked = min(eligible, key=lambda c: c['summary'][variant]['complete_bytes']) if eligible else None
                nearest = min(cohort, key=lambda c: abs(c['summary'][variant]['active_mse'] - target['active_mse']))
                out.append(dict(scene=custom['scene'], custom_profile=custom['profile'], variant=variant,
                                codec=name, target_custom_mse=target['active_mse'],
                                custom_bytes=target['complete_bytes'], measured_parameters=[c['parameter'] for c in cohort],
                                sampled_quality_range_covers_target=(min(c['summary'][variant]['active_mse'] for c in cohort) <= target['active_mse'] <= max(c['summary'][variant]['active_mse'] for c in cohort)),
                                lowest_bytes_measured_at_least_target_quality=None if picked is None else dict(profile=picked['profile'], parameter=picked['parameter'],
                                    bytes=picked['summary'][variant]['complete_bytes'], mse=picked['summary'][variant]['active_mse'],
                                    custom_to_native_byte_ratio=target['complete_bytes'] / picked['summary'][variant]['complete_bytes']),
                                nearest_measured_quality=dict(profile=nearest['profile'], parameter=nearest['parameter'],
                                    bytes=nearest['summary'][variant]['complete_bytes'], mse=nearest['summary'][variant]['active_mse']),
                                scope='Measured operating points only. At-least quality means this MSE threshold, not matched quality, BD-rate, perceptual equivalence, or target feasibility.'))
    return out


def pins():
    old = load(V23 / 'results.json')
    paths = {ROOT / p for p in old['source_sha256']}
    paths |= {V23 / 'results.json', V23 / 'model.py', HERE.parent / 'python-game-service-study/benchmark.py'}
    paths |= {HERE / p for p in ('model.py', 'benchmark.py', 'verify.py', 'test_model.py')}
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(paths)}


def main():
    before = pins()
    old = load(V23 / 'results.json')
    source = m.load_module('standard24_native_source', HERE.parent / 'python-game-service-study/benchmark.py')
    sources, cases, baselines = [], [], []
    for scene in ('mass-effect-2600', 'mass-effect-7200'):
        frames, planes, patches, inputs = source_inputs(scene, old, source)
        sources.append(inputs)
        controls = custom_baselines(scene, old, inputs, patches)
        baselines.extend(controls)
        for name, parameters, extras in (('libx265', (20, 28, 32, 36, 44), (50, 51)),
                                         ('libsvtav1', (20, 28, 38, 48), (56, 63))):
            cohort = [native_case(scene, name, q, planes, inputs, patches) for q in parameters]
            if name == 'libx265':
                # Refine the measured threshold comparison instead of fitting
                # an interpolated equal-quality claim across the wide28/36 gap.
                adaptive_target = next(c for c in controls if c['profile'] == 'adaptive_plain')['summary']['hybrid']['active_mse']
                q32 = next(c for c in cohort if c['parameter'] == 32)
                if q32['summary']['hybrid']['active_mse'] > adaptive_target:
                    cohort.append(native_case(scene, name, 31, planes, inputs, patches))
            # Extend only when the requested sweep never reaches a worse point
            # than the loosest custom target, keeping observed quality brackets.
            target = max(c['summary']['hybrid']['active_mse'] for c in controls)
            for q in extras:
                if max(c['summary']['hybrid']['active_mse'] for c in cohort) > target:
                    break
                cohort.append(native_case(scene, name, q, planes, inputs, patches))
            cases.extend(sorted(cohort, key=lambda c: c['parameter']))
    assert before == pins(), 'source changed during campaign'
    result = dict(schema='gamebub-standard-compare-v24', source_sha256=before, inputs=sources,
                  custom_baselines=baselines, cases=cases, operating_points=operating_points(cases, baselines),
                  counts=dict(unique_source_acquisitions=96, native_cases=len(cases),
                              native_codec_outputs=48 * len(cases), custom_reference_outputs=192),
                  versions=dict(python=platform.python_version(), numpy=np.__version__, pyav=av.__version__,
                                libraries={k: list(v) for k, v in av.library_versions.items()}),
                  scope=[
                      'Same two v23 48-frame windows starting4s, original29.88fps; nominal30 codec clock is a projection, not fresh native capture.',
                      'All encoders receive identical frozen GM YUV420 sample planes; all decoded planes use frozen RGB conversion and RGB565 display before originalRGB565 quality comparison.',
                      'Requested encoder settings do not prove a bounded HEVC/AV1 syntax subset, reference count or hardware decoder complexity. Actual packets/PTS/DTS/keyIDs/output association are retained.',
                      'Bare native byte counts include elementary packets and extradata; custom bare includes AR03 headers. Full custom bytes are actualCP23 packets.',
                      'Native+HC22 hybrid actually decodes both components and preserves exactHUD words, but bytebinding57/JA134/transport is prospective accounting: currentCP23receiver acceptsAR03only, not native HEVC/AV1.',
                      'Native codec timings are single-threaded host software component costs, not a fair Python-versus-optimized-C benchmark, end-to-end latency, ESP32/FPGA throughput or physical30fps.',
                      'No Gamebub standards decoder, native endpoint, RF/QSPI/scanout implementation or mapped FPGA resource/timing proof supplied.',
                      'No same-numerical-CRF equivalence, BD-rate or unbracketed matched-quality claim; operatingpoints identify actual sampled qualities only.'])
    (HERE / 'results.json').write_text(json.dumps(result, separators=(',', ':'), allow_nan=False) + '\n')
    print(json.dumps(result['counts']), flush=True)


if __name__ == '__main__':
    main()
