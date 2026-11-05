#!/usr/bin/env python3
"""Actual HM34 components on both frozen child16 trial fields, fixed reference.

Complete body sizes are prospective replacement arithmetic, not new frames.
Every component is built, archived, syntax-decoded and field-exact checked.
"""
import json
import platform
import time
from collections import Counter
import numpy as np
import helpers as h


def elapsed(fn):
    began = time.perf_counter_ns()
    value = fn()
    return value, (time.perf_counter_ns()-began)/1e6


def build():
    before = h.pins()
    frozen = h.load(h.SPLIT/'results.json')
    rows = []
    for old in frozen['rows']:
        parent_packet = h.raw(old['baseline']['base_packet'], h.SPLIT)
        parent, parent_payload = h.vectors(parent_packet, 32)
        parent_meta = h.m.parse_metadata(parent_packet)
        trials = []
        child_fields = []
        for trial in old['trials']:
            base_packet = h.raw(trial['base_packet'], h.SPLIT)
            child, gm27 = h.vectors(base_packet, 16)
            child_fields.append(child)
            if old['key']:
                packet, info, pack_ms, unpack_ms = b'', dict(selected_mode_name='key_zero_motion',
                    component_bytes=0, candidates=[], refinement_vectors=0, header_bytes=0, crc_bytes=0), 0., 0.
                assert not gm27 and not parent_payload and not child.any()
            else:
                (packet, info), pack_ms = elapsed(lambda: h.model.pack(parent, child,
                    parent_meta['width'], parent_meta['height'], return_info=True))
                (decoded, wire), unpack_ms = elapsed(lambda: h.decoder.unpack(packet,
                    parent_meta['width'], parent_meta['height'], return_info=True))
                np.testing.assert_array_equal(decoded, child)
                info['wire_bytes'] = {k: wire[k] for k in
                    ('header_bytes', 'crc_bytes', 'parent_bytes', 'refinement_bytes', 'component_bytes')}
                assert sum(info['wire_bytes'][k] for k in
                    ('header_bytes', 'crc_bytes', 'parent_bytes', 'refinement_bytes')) == len(packet)
            new_bytes = trial['complete_bytes']-len(gm27)+len(packet)
            trials.append(dict(kind=trial['kind'], gm27_motion_bytes=len(gm27), hm34_motion_bytes=len(packet),
                hm34_packet=None if old['key'] else h.blob(packet), hm34_info=info,
                parent_field_sha256=h.digest(parent.tobytes()), child_field_sha256=h.digest(child.tobytes()),
                retained_base_packet=trial['base_packet'], retained_complete_packet=trial['packet'],
                original_complete_bytes=trial['complete_bytes'], prospective_complete_bytes=new_bytes,
                byte_delta=new_bytes-trial['complete_bytes'], hybrid=trial['hybrid'],
                output_plane_sha256=trial['output_plane_sha256'], hybrid_sha256=trial['hybrid_sha256'],
                qmap_bytes=trial['qmap_bytes'], residual_plane_bytes=trial['residual_plane_bytes'],
                original_decoder_reference_sample_reads=trial['work']['decoder_reference_sample_reads'],
                source_pixels_and_residuals_unchanged=True, pack_ms=pack_ms, unpack_ms=unpack_ms))
        np.testing.assert_array_equal(*child_fields)
        old_guard = h.guard(old['control_baseline'], trials, 'original_complete_bytes')
        new_guard = h.guard(old['control_baseline'], trials, 'prospective_complete_bytes')
        assert old_guard['complete_bytes'] == old['selected_complete_bytes']
        assert old_guard['hybrid'] == old['selected_hybrid']
        rows.append(dict(scene=old['scene'], id=old['id'], key=old['key'],
            reference_id=old['reference_id'], reference_tag=old['reference_tag'],
            source_sha256=old['source_sha256'], parent32_packet=old['baseline']['base_packet'],
            parent32_gm27_motion_bytes=len(parent_payload), control_baseline=old['control_baseline'],
            trials=trials, old_guard=old_guard, prospective_guard=new_guard))
        print(json.dumps(dict(scene=old['scene'], id=old['id'],
            old_motion=[t['gm27_motion_bytes'] for t in trials],
            new_motion=[t['hm34_motion_bytes'] for t in trials],
            modes=[t['hm34_info']['selected_mode_name'] for t in trials],
            before=old_guard['selected_kind'], after=new_guard['selected_kind'])), flush=True)
    band = [r['trials'][1] for r in rows]
    summary = dict(source_frames=len(rows), trial_fields=sum(len(r['trials']) for r in rows),
        actual_nonkey_component_roundtrips=sum(not r['key'] for r in rows)*2,
        keys=sum(r['key'] for r in rows), key_motion_bytes=0,
        modes=dict(Counter(t['hm34_info']['selected_mode_name'] for r in rows for t in r['trials'])),
        parent32_motion_bytes=sum(r['parent32_gm27_motion_bytes'] for r in rows),
        raw_band16_old_motion_bytes=sum(t['gm27_motion_bytes'] for t in band),
        raw_band16_hm34_motion_bytes=sum(t['hm34_motion_bytes'] for t in band),
        raw_band16_motion_bytes_saved=sum(t['gm27_motion_bytes']-t['hm34_motion_bytes'] for t in band),
        raw_band16_original_complete_bytes=sum(t['original_complete_bytes'] for t in band),
        raw_band16_prospective_complete_bytes=sum(t['prospective_complete_bytes'] for t in band),
        actual_control_complete_bytes=sum(r['control_baseline']['complete_bytes'] for r in rows),
        actual_control_source_rgb_sse=sum(r['control_baseline']['hybrid']['active_squared_error'] for r in rows),
        old_guard_complete_bytes=sum(r['old_guard']['complete_bytes'] for r in rows),
        old_guard_source_rgb_sse=sum(r['old_guard']['hybrid']['active_squared_error'] for r in rows),
        prospective_guard_complete_bytes=sum(r['prospective_guard']['complete_bytes'] for r in rows),
        prospective_guard_source_rgb_sse=sum(r['prospective_guard']['hybrid']['active_squared_error'] for r in rows),
        old_guard_selected_trials=sum(r['old_guard']['selected_kind'] != 'v32_control' for r in rows),
        prospective_guard_selected_trials=sum(r['prospective_guard']['selected_kind'] != 'v32_control' for r in rows),
        old_guard_qualified_trials=sum(len(r['old_guard']['qualified_trial_kinds']) for r in rows),
        prospective_guard_qualified_trials=sum(len(r['prospective_guard']['qualified_trial_kinds']) for r in rows),
        mean_nonkey_pack_ms=sum(t['pack_ms'] for r in rows for t in r['trials'])/sum(not r['key'] for r in rows)/2,
        mean_nonkey_unpack_ms=sum(t['unpack_ms'] for r in rows for t in r['trials'])/sum(not r['key'] for r in rows)/2,
        raw_band16_decoder_reference_sample_reads=sum(t['original_decoder_reference_sample_reads'] for t in band),
        additional_motion_decoder_reference_sample_reads=0)
    state = dict(geometry=[720, 480], parent_grid=[15, 23], child_grid=[30, 45],
        parent_vectors=345, child_vectors=1350, parent_field_int8_bytes=690,
        child_field_int8_bytes=2700, retained_hierarchical_vector_state_bytes=3390,
        flat_vector_state_bytes=2700, max_actual_component_bytes=2719,
        gm27_median_streaming_two_rows_int8_bytes_parent=92,
        gm27_median_streaming_two_rows_int8_bytes_child=180,
        hierarchical_refinement_components_max=2700, sparse_gap_symbols_max=1350,
        group_presence_bits=345, child_mask_bits_max=1380,
        source_pixel_samples=0, reference_pixel_samples=0,
        explanation='Logical bounded syntax state and symbol counts, not Python heap/RSS, FPGA fit, cycles or hardware resources. '
                    'GM27 predictor modes can use two vector rows; actual Python decoder materializes fields and temporary NumPy arrays. '
                    'Prediction/residual pixel work is unchanged from exact frozen child16 vectors.')
    assert h.pins() == before
    return dict(schema='gamebub-hierarchy-v34', parent_commit='9c29165b816d49e2dec1c153712d1293b4781c6b',
        source_sha256=before, summary=summary, logical_decoder_state=state, rows=rows,
        environment=dict(python=platform.python_version(), numpy=np.__version__, platform=platform.platform()),
        causal_campaign=False, complete_frame_syntax=False, physical_30fps_proven=False,
        scope=['Actual bounded HM34 motion components only. All header, parent map, index, mask, delta, padding and CRC bytes paid.',
            'Both archived child16 trial fields from each of 24 frozen v33 sources preserved exactly. Keys charge zero motion.',
            'Prospective complete sizes replace only each old motion component; no new GM34/CP34 complete frame claimed here.',
            'Whole accepted v32 control guard retained from split-v33 evidence; current source SSE is unchanged for each exact-vector trial.',
            'Fixed previous accepted v32 references; no selected trial feeds the next reference. No causal/combined gain or hardware claim.',
            'One component pack/unpack timing sample per nonkey trial; inherited source search/encode work is not rerun or newly timed.'])


if __name__ == '__main__':
    result = build()
    (h.HERE/'results.json').write_text(json.dumps(result, separators=(',', ':'), allow_nan=False)+'\n')
    print(json.dumps(result['summary']), flush=True)
