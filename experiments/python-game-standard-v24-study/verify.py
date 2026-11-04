#!/usr/bin/env python3
"""Retained native stream decode and independent exact-pixel quality replay."""
from pathlib import Path
import hashlib
import json
import numpy as np
import benchmark as b
import model as m

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def main():
    data = b.load(HERE / 'results.json')
    assert data['schema'] == 'gamebub-standard-compare-v24'
    for p, h in data['source_sha256'].items():
        assert b.sha(ROOT / p) == h, p
    sources = {x['scene']: x for x in data['inputs']}
    caches = {}
    for scene, source in sources.items():
        rx = m.joint.hc.Receiver()
        patches = []
        assert len(source['rows']) == 48
        for row in source['rows']:
            packet = b.raw(row['hc22'])
            rx.receive(packet)
            current = tuple(p.copy() for p in rx.display['patches'])
            original = b.original(row['original_rgb565'])
            for (x, y, w, h), p in zip(m.RECTANGLES, current):
                np.testing.assert_array_equal(original[y:y+h, x:x+w], p)
            yuv = b.raw(row['common_yuv420_u8'])
            assert len(yuv) == 518400 and hashlib.sha256(yuv).hexdigest() == row['common_yuv420_u8_sha256']
            words = np.frombuffer(yuv, np.uint8)
            planes = (words[:345600].reshape(480, 720), words[345600:432000].reshape(240, 360), words[432000:].reshape(240, 360))
            floor = m.C.corpus.rgb565(m.C.gm.ft.planes_to_rgb(planes))
            assert m.metric(original, floor) == row['no_compression_roundtrip_bare']
            assert m.metric(original, m.overlay(floor, current)) == row['no_compression_roundtrip_hybrid']
            patches.append(current)
        caches[scene] = patches
    # Re-derive all fixed/adaptive custom reference images and error sums too,
    # rather than merely copying prior JSON summary numbers.
    old = b.load(b.V23 / 'results.json')
    custom = []
    for scene, source in sources.items():
        custom.extend(b.custom_baselines(scene, old, source, caches[scene]))
    assert custom == data['custom_baselines']
    outputs = bare_word_errors = 0
    for case in data['cases']:
        ref = case['reference']
        assert not ref['unconsumed_options'] and ref['packets_only_at_flush'] == 0
        assert ref['key_ids'] == [0, 24]
        assert [r['pts'] for r in ref['packets']] == list(range(48))
        assert [r['dts'] for r in ref['packets']] == list(range(48))
        assert [r['pts'] for r in ref['packets'] if r['is_key']] == [0, 24]
        assert [x['emitted_pts'] for x in ref['frame_calls']] == [[i] for i in range(48)]
        packets = []
        for record in ref['packets']:
            packet = b.raw(record['packet'])
            assert len(packet) == record['bytes']
            packets.append(dict(pts=record['pts'], dts=record['dts'], is_key=record['is_key'], data=packet))
        extras = b.raw(ref['extradata'])
        assert len(extras) == ref['extradata_bytes']
        decoded, info = m.decode(packets, extras, case['codec'])
        assert sorted(decoded) == list(range(48)) and info['frames_only_at_decode_flush'] == 0
        scene = case['scene']
        for i, row in enumerate(case['rows']):
            source = sources[scene]['rows'][i]
            original = b.original(source['original_rgb565'])
            bare = decoded[i]
            hybrid = m.overlay(bare, caches[scene][i])
            coded = len(packets[i]['data']) + (len(extras) if i == 0 else 0)
            assert row['coded_access_unit_bytes'] == coded
            for variant, display in (('bare', bare), ('hybrid', hybrid)):
                assert m.digest(display) == row[variant]['output_sha256']
                assert m.metric(original, display) == row[variant]['metric']
                wire = m.accounting(coded, source['hc22']['raw_bytes'] if variant == 'hybrid' else 0,
                                    binding=variant == 'hybrid')
                assert row[variant]['wire'] == wire and row[variant]['bytes'] == wire['body_bytes']
            assert row['hybrid']['metric']['hud_word_errors'] == 0
            bare_word_errors += row['bare']['metric']['hud_word_errors']
            outputs += 1
        assert case['summary'] == dict(bare=b.aggregate(case['rows'], 'bare'), hybrid=b.aggregate(case['rows'], 'hybrid'))
    assert b.operating_points(data['cases'], data['custom_baselines']) == data['operating_points']
    assert outputs == data['counts']['native_codec_outputs']
    assert len(data['cases']) == data['counts']['native_cases']
    assert bare_word_errors > 0
    print(json.dumps(dict(native_cases=len(data['cases']), actual_native_outputs=outputs,
                          retained_original_source_canvases=96, independently_recomputed_variant_metrics=2 * outputs,
                          independently_recomputed_custom_outputs=192, common_color_roundtrip_checks=192,
                          exact_hybrid_hud_words=outputs * 21120, bare_native_hud_word_errors=bare_word_errors,
                          key_ids=[0, 24], no_packets_only_at_flush=True,
                          actual_native_stream_redecode=True, gamebub_standard_decoder_implemented=False,
                          physical_30fps_proven=False), indent=2))


if __name__ == '__main__':
    main()
