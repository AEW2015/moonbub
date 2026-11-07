#!/usr/bin/env python3
"""Publish the measured common-input frontier after the independent audit."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT/'experiments/python-gamebub-v98'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    pointer = json.loads((AREA/'index.json').read_text())
    path = ROOT/pointer['attempt_json']
    assert sha(path) == pointer['sha256']
    report = json.loads(path.read_text())
    assert report['status'] == 'PASS'
    audit = json.loads((AREA/'audit.json').read_text())
    assert audit['status'] == 'PASS'
    # Audit ledger is bound independently to this immutable selected attempt.
    assert pointer['sha256'] in json.dumps(audit)
    for name, digest in report['source_sha256'].items():
        assert sha(ROOT/name) == digest, ('stale measured source', name)
    assert len(report['cases']) == 52 and len(report['source_clips']) == 4
    cases = []
    custom_pairs = []
    for case in report['cases']:
        info = json.loads((ROOT/case['info_path']).read_text())
        row = dict(case_id=case['case_id'], **case['summary'])
        row['codec'] = case['codec']
        row['source_npz_sha256'] = case['source_npz_sha256']
        row['first_packet_elapsed_ms'] = info.get('first_packet_elapsed_ms')
        row['first_decoded_output_elapsed_ms'] = info.get('first_decoded_output_elapsed_ms')
        row['native_syntax_observed'] = info.get('inspection', {}).get('observed_syntax')
        cases.append(row)
    for clip in report['source_clips']:
        selected = {c['case_id'].split('/')[1]: c for c in report['cases'] if c['clip_id'] == clip['clip_id']}
        a, b = selected['gm01-16'], selected['gm01-global16']
        ia, ib = [json.loads((ROOT/c['info_path']).read_text()) for c in (a, b)]
        qa, qb = [json.loads((ROOT/c['quality_path']).read_text()) for c in (a, b)]
        custom_pairs.append({
            'source': clip['clip_id'],
            'global_vs_zero_packets_identical': [p['sha256'] for p in ia['packets']] == [p['sha256'] for p in ib['packets']],
            'global_vs_zero_display_identical': [p['display_rgb_sha256'] for p in qa['frames']] ==
                                                [p['display_rgb_sha256'] for p in qb['frames']],
            'global_translation_offsets': sorted({(p['dx'], p['dy']) for p in ib['packets']}),
            'zero_frontend_median_ms': a['summary']['encode_frontend_ms']['median'],
            'global_frontend_median_ms': b['summary']['encode_frontend_ms']['median']})
    summary = {
        'schema': 'v98-qualified-software-comparison-v1', 'status': 'PASS_SOFTWARE_SCOPE_ONLY',
        'input_sha256': {pointer['attempt_json']: pointer['sha256'],
                         str((AREA/'audit.json').relative_to(ROOT)): sha(AREA/'audit.json'),
                         str((AREA/'index.json').relative_to(ROOT)): sha(AREA/'index.json')},
        'source_sequences': len(report['source_clips']),
        'source_frame_ids': sum(c['frame_count'] for c in report['source_clips']),
        'sum_per_clip_unique_rgb': sum(c['unique_rgb_count'] for c in report['source_clips']),
        'profile_runs': len(cases),
        'codec_frame_roundtrips': sum(c['frame_count'] for c in report['cases']),
        'independent_raw_gameplay_capture_gate': 'OPEN: all game sources are precompressed H.264',
        'current_cu66_fresh_rgb_encode_gate': 'OPEN: GM01 is historical, not current CU66 syntax or policy',
        'hud_readability_gate': 'OPEN: geometric/synthetic interior ROI pixel errors only; no OCR or player study',
        'hardware_30fps_gate': 'OPEN: native CPU/Python controls, not ESP32/QSPI/FPGA/display',
        'hardware_under_10ms_gate': 'OPEN: no complete placed or physical target decoder timing',
        'rate_scope': 'Complete elementary bytes plus extradata; GM01 includes its headers/CRCs. No mux/network/FEC/ACK overhead.',
        'cap_scope': '49152-byte AU diagnostic, not a universal syntax or transport limit; no admission dropping in these controls.',
        'quality_scope': 'Same 720x480 RGB inputs and canonical full-range YUV420 samples/inverse, then RGB565 display quantization. '
                         'PSNR/ROI/temporal error proxies, no perceptual equality or BD-rate claim.',
        'latency_scope': 'Single unpaced host pass, 30 samples per case. Conversion-inclusive frontend/backend CPU times; '
                         'sample extrema and nearest-rank p95 are diagnostic, not hardware or production tail guarantees.',
        'frontiers': report['rate_quality_frontier'],
        'global_motion_control': custom_pairs,
        'cases': cases,
        'decision': 'Retain HEVC/AV1 as software rate-quality anchors and JPEG as the deployed intra control. '
                    'Do not promote historical GM01 or replace current CU66 based on this comparison. '
                    'Build a fresh-RGB current-CU66 encoder and raw-capture corpus before a current-codec gap claim.'}
    (AREA/'summary.json').write_text(json.dumps(summary, indent=2, allow_nan=False)+'\n')
    with (AREA/'frontier.csv').open('w', newline='') as stream:
        fields = ['case_id', 'coded_bytes', 'coded_mbps_at_source_cadence', 'coded_mbps_at_hypothetical_30',
                  'active_psnr_db', 'roi_psnr_db', 'worst_frame_psnr_db',
                  'access_units_over_49152', 'encode_frontend_median_ms',
                  'decode_to_rgb_median_ms', 'decode_to_rgb_max_ms', 'nondominated']
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        for case in cases:
            row = {name: case[name] for name in fields if name in case}
            row['encode_frontend_median_ms'] = case['encode_frontend_ms']['median']
            row['decode_to_rgb_median_ms'] = case['decode_to_rgb_ms']['median']
            row['decode_to_rgb_max_ms'] = case['decode_to_rgb_ms']['max']
            row['nondominated'] = case['case_id'] in summary['frontiers'][case['case_id'].split('/')[0]]
            writer.writerow(row)
    print('PASS_V98_SUMMARY', len(cases), 'controls;', summary['codec_frame_roundtrips'], 'roundtrips')


if __name__ == '__main__':
    main()
