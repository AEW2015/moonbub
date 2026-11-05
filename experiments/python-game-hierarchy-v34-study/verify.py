#!/usr/bin/env python3
"""Independent frozen-frame/pixel checks plus actual HM34 archive verification."""
import argparse
import json
import numpy as np
import helpers as h


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--archives-only', action='store_true',
                        help='Skip host component repacking; still decode all components and retained frames/metrics.')
    args = parser.parse_args()
    data = h.load(h.HERE/'results.json')
    assert data['schema'] == 'gamebub-hierarchy-v34'
    assert data['causal_campaign'] is False and data['complete_frame_syntax'] is False
    assert h.pins() == data['source_sha256']
    original = h.load(h.SPLIT/'results.json')
    components = frames = frame_packets = 0
    for case, inp in h.old.cases():
        ref = None
        for prior, src in zip(case['rows'][:12], inp['rows'][:12]):
            row = next(r for r in data['rows'] if (r['scene'], r['id']) == (case['scene'], prior['id']))
            old = next(r for r in original['rows'] if (r['scene'], r['id']) == (case['scene'], prior['id']))
            source, pixels_original = h.n.source(src), h.n.original(src)
            assert h.digest(b''.join(a.astype('u1').tobytes() for a in source)) == row['source_sha256'] == src['common_yuv420_u8_sha256']
            tag = h.m.base.ZERO_TAG if ref is None else h.m.C.reference_tag(ref)
            assert tag.hex() == row['reference_tag'] == prior['reference_tag']
            control = row['control_baseline']
            control_packet = h.raw(control['base_packet'], h.SPLIT)
            assert control_packet == h.raw(prior['base_packet'], h.old.h.V32)
            control_pixels, _ = h.m.decode(control_packet, ref, expected_epoch=25,
                expected_reference_id=None if row['key'] else row['reference_id'])
            overlay = tuple(pixels_original[y:y+hh, x:x+w] for x, y, w, hh in h.n.RECTS)
            hybrid = h.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(control_pixels)), overlay)
            assert h.n.metric(pixels_original, hybrid) == control['hybrid'] == prior['hybrid']
            assert len(h.raw(control['packet'], h.SPLIT)) == control['complete_bytes'] == prior['body_bytes']
            parent_packet = h.raw(row['parent32_packet'], h.SPLIT)
            parent, parent_payload = h.vectors(parent_packet, 32)
            assert len(parent_payload) == row['parent32_gm27_motion_bytes']
            for trial, old_trial in zip(row['trials'], old['trials']):
                packet = h.raw(trial['retained_base_packet'], h.SPLIT)
                pair = h.raw(trial['retained_complete_packet'], h.SPLIT)
                assert packet == h.raw(old_trial['base_packet'], h.SPLIT)
                assert len(pair) == trial['original_complete_bytes'] == len(packet)+old['hud_bytes']+old['binding_bytes']
                child, gm27 = h.vectors(packet, 16)
                assert h.digest(parent.tobytes()) == trial['parent_field_sha256']
                assert h.digest(child.tobytes()) == trial['child_field_sha256']
                assert len(gm27) == trial['gm27_motion_bytes']
                if row['key']:
                    assert trial['hm34_packet'] is None and trial['hm34_motion_bytes'] == 0 and not gm27
                else:
                    component = h.raw(trial['hm34_packet'], h.HERE)
                    decoded, info = h.decoder.unpack(component, 720, 480, return_info=True)
                    np.testing.assert_array_equal(decoded, child)
                    if info['parent'] is not None:
                        np.testing.assert_array_equal(info['parent'], parent)
                    assert len(component) == trial['hm34_motion_bytes']
                    assert info['mode'] == trial['hm34_info']['selected_mode']
                    assert all(info[k] == v for k, v in trial['hm34_info']['wire_bytes'].items())
                    if not args.archives_only:
                        actual, work = h.model.pack(parent, child, 720, 480, return_info=True)
                        assert actual == component
                        for key in ('candidates', 'selected_mode', 'refinement_vectors', 'sparse_rice_parameters'):
                            assert work[key] == trial['hm34_info'][key]
                    components += 1
                assert trial['prospective_complete_bytes'] == len(pair)-len(gm27)+trial['hm34_motion_bytes']
                assert trial['hybrid'] == old_trial['hybrid']
                decoded, meta = h.m.decode(packet, ref, expected_epoch=25,
                    expected_reference_id=None if row['key'] else row['reference_id'])
                assert [h.n.digest(a) for a in decoded] == trial['output_plane_sha256']
                hybrid = h.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(decoded)), overlay)
                assert h.n.metric(pixels_original, hybrid) == trial['hybrid']
                assert h.n.digest(hybrid) == trial['hybrid_sha256']
                assert list(meta['plane_lengths']) == trial['residual_plane_bytes']
                assert meta['qmap_bytes'] == trial['qmap_bytes']
                frame_packets += 1
            assert h.guard(control, row['trials'], 'original_complete_bytes') == row['old_guard']
            assert h.guard(control, row['trials'], 'prospective_complete_bytes') == row['prospective_guard']
            ref = control_pixels
            frames += 1
    s = data['summary']
    assert components == s['actual_nonkey_component_roundtrips'] == 44
    assert frames == s['source_frames'] == 24 and frame_packets == 48
    for prefix, key in (('old_guard', 'old_guard'), ('prospective_guard', 'prospective_guard')):
        assert sum(r[key]['complete_bytes'] for r in data['rows']) == s[prefix+'_complete_bytes']
        assert sum(r[key]['hybrid']['active_squared_error'] for r in data['rows']) == s[prefix+'_source_rgb_sse']
    band = [r['trials'][1] for r in data['rows']]
    assert sum(t['gm27_motion_bytes'] for t in band) == s['raw_band16_old_motion_bytes']
    assert sum(t['hm34_motion_bytes'] for t in band) == s['raw_band16_hm34_motion_bytes']
    assert sum(t['prospective_complete_bytes'] for t in band) == s['raw_band16_prospective_complete_bytes']
    print(json.dumps(dict(source_frames=frames, retained_child_frame_metrics=frame_packets,
        verified_actual_hm34_components=components, exact_component_repack=not args.archives_only,
        whole_control_guard_before_bytes=s['old_guard_complete_bytes'],
        prospective_whole_control_guard_after_bytes=s['prospective_guard_complete_bytes'],
        original_source_mse_retained_exact=True, complete_frame_syntax=False, causal_campaign=False)))


if __name__ == '__main__':
    main()
