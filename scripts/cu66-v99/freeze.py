#!/usr/bin/env python3
"""Freeze a research RC1 and its exact evidence, without product promotion."""
import csv
from fractions import Fraction
import gzip
import hashlib
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT/'experiments/python-gamebub-v99'
NATIVE = AREA/'native/attempts/20261107T185742458Z'
CS88 = AREA/'cs88/attempts/20261107T190043503Z'
GOLDENS = AREA/'cs88/rtl-facing-attempts/20261107T1909-new-user-q16'
DIRECT = AREA/'direct/attempts/20261107T191209501Z'
BASELINE = '35949d6f41366cd5725b433a136fadb1b6ce95f6'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def dump(path, obj):
    path.write_text(json.dumps(obj, indent=2, allow_nan=False)+'\n')


def bound(path):
    return {'path': str(path.relative_to(ROOT)), 'sha256': sha(path)}


def main():
    pointer = read(AREA/'fresh/index.json')
    fresh_path = ROOT/pointer['attempt_json']
    assert sha(fresh_path) == pointer['sha256']
    fresh = read(fresh_path)
    native, cs88, direct = read(NATIVE/'summary.json'), read(CS88/'results.json'), read(DIRECT/'results.json')
    assert fresh['status'] == 'PASS_SOFTWARE_CAMPAIGN'
    assert native['pass'] and native['frames'] == 360
    assert cs88['status'] == 'PASS_FRESH_NATIVE_CS88_PARITY' and cs88['profile'] == 'v91-group3'
    assert direct['status'] == 'PASS_DIRECT_FRESH_NATIVE_CS88_EXACT'
    assert direct['frames'] == 120 and direct['native_exact_ACKs'] == 120
    assert direct['synthetic_cross_key_control']['native_exact_ACKs'] == 32
    assert direct['actual_packets_equal_control'] == 120
    for record in (fresh, cs88, direct, read(GOLDENS/'results.json')):
        for name, digest in record['source_sha256'].items():
            assert sha(ROOT/name) == digest, ('stale measured source', name)
    audit_paths = [AREA/name for name in ('audit-fresh.json', 'audit-native.json', 'audit-cs88.json', 'audit-direct.json')]
    for path in audit_paths:
        assert read(path)['status'].startswith('PASS'), ('audit not passed', path)
    cases = {case['case_id']: case for case in fresh['cases']}
    rows = [json.loads(line) for line in (CS88/'frames.jsonl').read_text().splitlines()]
    selected = [row for row in rows if row['quant_scale'] == 16]
    assert len(selected) == 120 and all(row['fits_49152'] for row in selected)
    chains = [chain for chain in cs88['chains'] if chain['quant_scale'] == 16]
    assert len(chains) == 4 and all(chain['input_frames'] == 30 and chain['entire_sequence_49152_eligible'] for chain in chains)
    assert all(row['map_method'] == (0 if row['key'] else 3) and
               row['qmap_method'] in (2, 6) and row['block_size'] == 32 and
               row['chunk_profile_cap'] == 65536 and row['remaining_adaptive_decisions'] == 0 for row in selected)
    first_disk = read(ROOT/fresh['cases'][1]['records_path'])['records'][0]
    raw_hud = gzip.decompress(Path(first_disk['hud_path']).read_bytes())
    width, height, count = struct.unpack_from('<HHB', raw_hud)
    rectangles, cursor = [], 5
    for _ in range(count):
        rect = struct.unpack_from('<4H', raw_hud, cursor)
        rectangles.append(list(rect))
        cursor += 8+rect[2]*rect[3]*2
    assert cursor == len(raw_hud) and (width, height) == (720, 480)
    evidence = [fresh_path, NATIVE/'receipt.json', NATIVE/'summary.json', CS88/'results.json',
                GOLDENS/'results.json', DIRECT/'results.json', *audit_paths]
    test_pointer = read(AREA/'validation/index.json')
    test_path = ROOT/test_pointer['receipt']
    assert sha(test_path) == test_pointer['sha256'] and read(test_path)['status'] == 'PASS'
    evidence.append(test_path)
    profile = {
        'schema': 'v99-rc1-profile-v1', 'name': 'CS88-V99-RC1-Q16-BR88',
        'status': 'FROZEN_RESEARCH_CANDIDATE_ONLY', 'baseline_commit': BASELINE,
        'existing_wire_magic': 'CS88', 'wire_version': 1,
        'new_MB97_profile_number_assigned': False,
        'active_firmware_support': False, 'deployed_custom_FPGA_support': False,
        'geometry': {'coded_width': 720, 'coded_height': 480, 'samples': 'full-range 8-bit YUV420',
                     'canonical_bytes': 518400, 'RGB565_bytes': 691200,
                     'tiles_8x8_Y_Cb_Cr': [5400, 1350, 1350]},
        'parameters': {'motion_block_size': 32, 'base_motion': 'zero only', 'coefficient_codec': 'BR88 only',
                       'coefficient_range_inclusive': [-2048, 2048], 'chunk_block_cap': 65536,
                       'complete_packet_cap_bytes_including_outer_CRC': 49152,
                       'key_mode_method': 0, 'P_mode_method': 3, 'mode_body_max_bytes': 976,
                       'QM87_methods': [2, 6], 'QM87_body_plus_header_and_CRC_max_bytes': 354,
                       'default_uniform_quant_scale': 16, 'default_uniform_quant_code': 1,
                       'diagnostic_scales_not_default': [8, 32], 'key_interval_input_ids': 30,
                       'canonical_reference': 'previous validated accepted frame, with explicit key reset',
                       'C2_tree_granularity_tiles': 16, 'C2_profile_id': 'CU66-V82-CONTENT-SHA256-TREE-2'},
        'HUD': {'fixed_rectangles_xywh': rectangles, 'words_bytes': len(raw_hud)-5-8*count,
                'CU66_hash_preimage': 'LE geometry,count,rectangles,words',
                'CS88_hash_preimage': 'concatenated LE RGB565 words only',
                'display_policy': 'exact source RGB565 words in these fixed rectangles, composed after base conversion'},
        'transaction': {'wire_generation': 'strictly increasing uint64 accepted generation',
                        'CS88_wire_has_epoch_field': False,
                        'CU66_upstream_control_epoch_only': 25,
                        'transport_epoch_and_core_generation_binding': 'integration required; no existing opaque-profile alias',
                        'release_reference': 'after complete actual C2/HUD/seal validation and write drain',
                        'present': 'separate vblank and scanout-drain gate',
                        'overflow': 'reject without reference/publication advance; re-encode from accepted state or explicitly reset/negotiate fallback',
                        'current_direct_fixed_q16_overflow_fallback_implemented': False},
        'fallback': {'format': 'existing baseline JPEG/MSV1', 'deployment': 'existing separate supported profile/image',
                     'simultaneous_custom_and_JPEG_fit_qualified': False},
        'qualification': {'fresh_CU66_attempts': 360, 'native_CU66_parity_frames': 360,
                          'native_CU66_atomic_rejection_trials': 3948,
                          'native_CS88_parity_frames': 360, 'selected_q16_frames': 120,
                          'selected_q16_complete_cases': 4, 'selected_max_packet_bytes': max(r['wire_bytes'] for r in selected),
                          'selected_total_bytes': sum(r['wire_bytes'] for r in selected),
                          'direct_packet_equality_frames': 120, 'additional_cross_key_control_frames': 32,
                          'new_source_RTL_facing_goldens_only': True, 'new_source_RTL_simulation': False,
                          'placed_routed_candidate': False, 'hardware_30fps': False, 'hardware_under10ms': False},
        'evidence': [bound(path) for path in evidence],
        'open_gates': ['original held-out raw captures and perceptual/HUD tests',
                       'native real-time Sunshine encoder: Python HUD/transform and helper IPC costs remain too high',
                       'real ESP32/RTOS/Wi-Fi/QSPI capability and service integration',
                       'complete live RTL reconstruction/HUD/C2/publication/shared-display join',
                       'finite physical memory, ports, CDC, Artix tool support and exact target constraints',
                       'V100-V110 mapping, placement, routing and timing',
                       '1800 distinct frames/60s then18000/600s on target at30Hz',
                       'separate validated complete FPGA decoding strictly under10ms']}
    dump(AREA/'profile.json', profile)
    dump(AREA/'qualification.json', {'status': 'PASS_RC1_SOFTWARE_NATIVE_SCOPE',
        'profile': bound(AREA/'profile.json'), 'evidence': profile['evidence'],
        'product_freeze_complete': False, 'physical_hardware_qualification': False})
    source_by_id = {clip['clip_id']: clip for clip in fresh['source_clips']}
    direct_by_id = {case['clip_id']: case for case in direct['cases']}
    summaries = []
    for chain in cs88['chains']:
        case = cases[chain['clip_id']]
        source = source_by_id[case['source_clip_id']]
        fps = Fraction(source['source_metadata'].get('selected_fps', source['source_metadata']['source_fps']))
        summaries.append({'case_id': chain['clip_id'], 'quant_scale': chain['quant_scale'],
                          'CU66_bytes': case['candidate_bytes_all_attempts'], 'CS88_bytes': chain['total_bytes'],
                          'CS88_mbps_at_selected_source_cadence': chain['total_bytes']/chain['input_frames']*8*float(fps)/1e6,
                          'max_packet_bytes': chain['max_bytes'], 'over_cap_packets': chain['oversize_49152'],
                          'complete_input_sequence_under_cap': chain['entire_sequence_49152_eligible'],
                          'active_psnr_db': case['active_psnr_db_accepted_only'],
                          'ROI_psnr_db': case['roi_psnr_db_accepted_only'],
                          'direct_packet_ready_ms': direct_by_id[chain['clip_id']]['packet_ready_ms'] if chain['quant_scale'] == 16 else None,
                          'direct_HUD_ms': direct_by_id[chain['clip_id']]['phases']['fresh_HUD_ms'] if chain['quant_scale'] == 16 else None})
    summary = {'schema': 'v99-research-summary-v1', 'status': 'PASS_RC1_SOFTWARE_NATIVE_ONLY',
               'profile': bound(AREA/'profile.json'), 'qualification': bound(AREA/'qualification.json'),
               'CU66_CPU_receive_to_RGB565_ms': native['receive_to_published_rgb565_ms'],
               'CPU_timer_not_selected_CS88_or_FPGA': True,
               'CS88_V91_subset_all_scales_diagnostic': {'frames': cs88['received_packets'], 'fit_packets': cs88['fit_packets_49152'],
                  'over_cap_packets': cs88['oversize_packets_49152'], 'total_bytes': cs88['total_wire_bytes']},
               'direct': {'source_frames': 120, 'native_ACKs_including_control': 152,
                          'packet_ready_ms': direct['packet_ready_ms'],
                          'physical_30fps': False, 'unpaced_Python_and_native_helper_only': True},
               'source_frame_ids': 120, 'per_clip_unique_RGBs': 109,
               'cases': summaries, 'scope': 'Fresh same-source software/native candidate and conditional hardware handoff; not deployed firmware or a complete RTL build.'}
    dump(AREA/'summary.json', summary)
    with (AREA/'results.csv').open('w', newline='') as stream:
        fields = ['case_id', 'quant_scale', 'CU66_bytes', 'CS88_bytes', 'CS88_mbps_at_selected_source_cadence',
                  'max_packet_bytes', 'over_cap_packets', 'complete_input_sequence_under_cap', 'active_psnr_db', 'ROI_psnr_db']
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n', extrasaction='ignore')
        writer.writeheader()
        writer.writerows(summaries)
    for folder, path in ((AREA/'native', NATIVE/'receipt.json'), (AREA/'cs88', CS88/'results.json'),
                         (AREA/'direct', DIRECT/'results.json'), (AREA/'cs88', GOLDENS/'results.json')):
        filename = 'rtl-facing-index.json' if path.parent == GOLDENS else 'index.json'
        dump(folder/filename, bound(path))
    print('PASS_V99_RESEARCH_FREEZE', len(selected), 'selected frames; physical gates OPEN')


if __name__ == '__main__':
    main()
