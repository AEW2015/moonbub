#!/usr/bin/env python3
"""Independent integrity and arithmetic audit for the V98 common-input run.

This intentionally does not import compare.py, metrics.py, standard_controls,
or custom_controls. It audits retained reports and byte artifacts directly.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v98'


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def close(a, b, rel=1e-10, abs_tol=1e-9):
    return math.isclose(float(a), float(b), rel_tol=rel, abs_tol=abs_tol)


def check(condition, message, errors, counters, key):
    counters[key] = counters.get(key, 0) + 1
    if not condition:
        errors.append(message)


def distribution(values):
    vals = sorted(float(v) for v in values)
    if not vals:
        return {'n': 0, 'min': None, 'median': None, 'p95_nearest_rank': None, 'max': None}
    n = len(vals)
    median = (vals[n // 2] if n % 2 else (vals[n // 2 - 1] + vals[n // 2]) / 2)
    return {'n': n, 'min': vals[0], 'median': median,
            'p95_nearest_rank': vals[math.ceil(.95 * n) - 1], 'max': vals[-1]}


def audit(index_path: Path) -> dict:
    errors: list[str] = []
    counts: dict[str, int] = {}
    index_path = index_path.resolve()
    index = read_json(index_path)
    report_path = ROOT / index['attempt_json']
    report_bytes = report_path.read_bytes()
    check(sha_bytes(report_bytes) == index['sha256'], 'index report hash mismatch', errors, counts, 'index_hash')
    report = json.loads(report_bytes)
    attempt = ROOT / report['attempt']
    check(report.get('status') == 'PASS', f"run status is {report.get('status')}", errors, counts, 'run_status')

    manifest_path = AREA / 'sources/manifest.json'
    manifest = read_json(manifest_path)
    check(sha_file(AREA/'source_prepare.py') == manifest['preparation']['script_sha256'],
          'manifest preparation script hash mismatch', errors, counts, 'preparation_script_pin')
    check(sha_file(manifest_path) == report['input_manifest_sha256'],
          'input manifest hash differs from run record', errors, counts, 'manifest_hash')
    clip_by_id = {clip['clip_id']: clip for clip in manifest['clips']}
    recorded_clips = {clip['clip_id']: clip for clip in report.get('source_clips', [])}
    check(recorded_clips == {clip['clip_id']: clip for clip in manifest['clips']},
          'run source metadata differs from manifest', errors, counts, 'complete_source_metadata')
    check(set(clip_by_id) == set(recorded_clips), 'run source clip IDs differ from current manifest', errors, counts,
          'manifest_clip_set')

    # Validate every common input and exact rational cadence from source PTS.
    for clip_id, clip in clip_by_id.items():
        source_path = AREA / 'sources' / clip['npz_path']
        check(source_path.exists() and sha_file(source_path) == clip['npz_sha256'],
              f'{clip_id}: NPZ missing or hash mismatch', errors, counts, 'source_npz_hash')
        try:
            import numpy as np
            with np.load(source_path, allow_pickle=False) as archive:
                check(archive.files == ['rgb'], f'{clip_id}: NPZ keys are {archive.files}', errors, counts,
                      'source_npz_keys')
                rgb = archive['rgb']
            check(rgb.dtype == np.uint8 and list(rgb.shape) == clip['shape'] == [30, 480, 720, 3],
                  f'{clip_id}: RGB shape/dtype mismatch', errors, counts, 'source_rgb_shape')
            frame_hashes = [sha_bytes(frame.tobytes()) for frame in rgb]
            check(frame_hashes == clip['frame_sha256'], f'{clip_id}: source RGB frame hashes mismatch',
                  errors, counts, 'source_frame_hashes')
            check(len(set(frame_hashes)) == clip['unique_rgb_count'],
                  f'{clip_id}: unique RGB count mismatch', errors, counts, 'source_unique_frames')
        except Exception as e:
            errors.append(f'{clip_id}: failed loading input NPZ: {type(e).__name__}: {e}')

        fps_text = clip.get('selected_fps') or clip['source_metadata'].get('selected_fps') or \
                   clip['source_metadata'].get('source_fps') or clip.get('frame_rate')
        stamps = clip['timestamps']
        try:
            fps = Fraction(fps_text)
            times = [Fraction(item['seconds']) for item in stamps]
            uniform = len(times) == clip['frame_count'] and all(
                times[i + 1] - times[i] == 1 / fps for i in range(len(times) - 1))
            check(uniform, f'{clip_id}: timestamps are not uniform at selected rate {fps_text}', errors, counts,
                  'source_cadence')
            check(len(stamps) == clip['frame_count'] and all(
                Fraction(item['pts']) * Fraction(item['time_base']) == Fraction(item['seconds'])
                for item in stamps), f'{clip_id}: timestamp PTS/time_base mismatch', errors, counts,
                  'source_pts_consistency')
        except Exception as e:
            errors.append(f'{clip_id}: invalid selected cadence metadata: {e}')

        source_meta = clip.get('source_metadata', {})
        original = source_meta.get('path')
        expected_source_hash = source_meta.get('sha256')
        if expected_source_hash:
            check(bool(original) and Path(original).is_file() and sha_file(Path(original)) == expected_source_hash,
                  f'{clip_id}: original source file missing/hash mismatch', errors, counts, 'original_source_hash')

    # Check every pinned source file against its raw snapshot, then the attempt's
    # artifact inventory, including retained elementary streams and quality JSON.
    pins = report.get('source_sha256', {})
    for relative, digest in pins.items():
        live = ROOT / relative
        snapshot = attempt / 'source-snapshot' / relative
        check(live.is_file() and sha_file(live) == digest,
              f'pinned live source changed/missing: {relative}', errors, counts, 'live_source_pin')
        check(snapshot.is_file() and sha_file(snapshot) == digest,
              f'raw source snapshot changed/missing: {relative}', errors, counts, 'raw_snapshot_pin')
    artifact_hashes = report.get('artifact_sha256', {})
    for relative, digest in artifact_hashes.items():
        file = attempt / relative
        check(file.is_file() and sha_file(file) == digest,
              f'attempt artifact hash mismatch: {relative}', errors, counts, 'artifact_hash')

    # Independent per-case packet, rate, latency, syntax and pooled-quality audit.
    audited_cases = []
    for case in report.get('cases', []):
        cid = case['case_id']
        clip = clip_by_id.get(case['clip_id'])
        if clip is None:
            errors.append(f'{cid}: unknown clip'); continue
        check(case['source_npz_sha256'] == clip['npz_sha256'], f'{cid}: case input NPZ pin mismatch', errors,
              counts, 'case_npz_pin')
        check(case['input_frame_sha256'] == clip['frame_sha256'], f'{cid}: case source frame hash identity mismatch',
              errors, counts, 'case_frame_identity')
        info_path = ROOT / case['info_path']
        quality_path = ROOT / case['quality_path']
        check(info_path.is_file() and sha_file(info_path) == case['info_sha256'],
              f'{cid}: codec-info hash mismatch', errors, counts, 'codec_info_hash')
        check(quality_path.is_file() and sha_file(quality_path) == case['quality_sha256'],
              f'{cid}: quality JSON hash mismatch', errors, counts, 'quality_hash')
        try:
            info, quality = read_json(info_path), read_json(quality_path)
            n = int(case['frame_count'])
            packets = info['packets']
            check(len(packets) == n, f'{cid}: packet ledger has {len(packets)} entries, expected {n}', errors,
                  counts, 'packet_count')

            if case['codec'] == 'gm01':
                stream_info = info['stream']
                stream_path = Path(stream_info['path'])
                stream_bytes = stream_path.read_bytes()
                check(len(stream_bytes) == stream_info['bytes'] == info['total_bytes'],
                      f'{cid}: GM01 stream size mismatch', errors, counts, 'stream_bytes')
                check(sha_bytes(stream_bytes) == stream_info['sha256'], f'{cid}: GM01 stream hash mismatch', errors,
                      counts, 'stream_hash')
                cursor = 0
                for index, packet in enumerate(packets):
                    start, size = int(packet['offset']), int(packet['bytes'])
                    check(start == cursor, f'{cid}: packet {index} offset is not contiguous', errors, counts,
                          'packet_offsets')
                    chunk = stream_bytes[start:start + size]
                    check(len(chunk) == size and sha_bytes(chunk) == packet['sha256'],
                          f'{cid}: GM01 packet {index} byte slice/hash mismatch', errors, counts,
                          'packet_slice_hash')
                    cursor = start + size
                check(cursor == len(stream_bytes), f'{cid}: GM01 packet slices do not cover stream', errors, counts,
                      'packet_stream_coverage')
                extra_bytes = int(info.get('extradata_bytes', 0))
                flush_only = int(info.get('packets_only_at_flush', -1))
                output_ids = [int(pts) for item in info.get('decode_calls', [])
                              for pts in item.get('emitted_pts', [])]
                first_lag = (int(packets[0]['id']) - int(packets[0]['pts'])) if packets else None
                stream_total = len(stream_bytes)
            else:
                stream_path = Path(info['stream_path'])
                extra_path = Path(info['extradata_path'])
                stream_bytes, extra_bytes_data = stream_path.read_bytes(), extra_path.read_bytes()
                extra_bytes = len(extra_bytes_data)
                check(len(stream_bytes) == info['elementary_stream_bytes'],
                      f'{cid}: standard stream byte length mismatch', errors, counts, 'stream_bytes')
                check(len(extra_bytes_data) == info['extradata_bytes'],
                      f'{cid}: extradata byte length mismatch', errors, counts, 'extradata_bytes')
                check(sha_bytes(stream_bytes) == info['elementary_stream_sha256'],
                      f'{cid}: standard stream hash mismatch', errors, counts, 'stream_hash')
                check(sha_bytes(extra_bytes_data) == info['extradata_sha256'],
                      f'{cid}: extradata hash mismatch', errors, counts, 'extradata_hash')
                cursor = 0
                for index, packet in enumerate(packets):
                    size = int(packet['bytes'])
                    chunk = stream_bytes[cursor:cursor + size]
                    check(len(chunk) == size and sha_bytes(chunk) == packet['sha256'],
                          f'{cid}: packet {index} concatenated stream slice/hash mismatch', errors, counts,
                          'packet_slice_hash')
                    cursor += size
                check(cursor == len(stream_bytes), f'{cid}: packet byte ledger does not cover stream', errors,
                      counts, 'packet_stream_coverage')
                flush_only = int(info.get('packets_returned_only_at_flush', -1))
                first = info.get('first_packet') or {}
                first_lag = first.get('input_lag_frames')
                output_ids = [int(x) for x in info.get('output_pts', [])]
                availability_ids = [int(x['pts']) for x in info.get('output_availability', [])]
                check(info.get('inspection_returncode') == 0,
                      f'{cid}: syntax inspection returncode is {info.get("inspection_returncode")}', errors,
                      counts, 'syntax_returncode')
                syntax = info.get('inspection', {}).get('observed_syntax', {})
                if case['codec'] == 'jpeg':
                    jpeg_frames = info.get('inspection', {}).get('frames', [])
                    check(len(jpeg_frames) == n and all(frame.get('sof_marker') == 'SOF0 baseline sequential'
                                                        for frame in jpeg_frames),
                          f'{cid}: JPEG marker audit did not find {n} baseline SOF0 images', errors, counts,
                          'jpeg_sof0_syntax')
                    check(all(frame.get('width') == 720 and frame.get('height') == 480 and
                              frame.get('precision') == 8 for frame in jpeg_frames),
                          f'{cid}: JPEG SOF dimensions/precision mismatch', errors, counts, 'jpeg_dimensions')
                else:
                    check(bool(syntax), f'{cid}: syntax trace has no observed syntax fields', errors, counts,
                          'syntax_nonempty')
                if case['codec'] == 'hevc':
                    reorder = syntax.get('sps_max_num_reorder_pics', {}).get('values', [])
                    slices = syntax.get('slice_type', {}).get('values', [])
                    check(reorder == [0], f'{cid}: HEVC observed reorder values {reorder}, expected [0]', errors,
                          counts, 'hevc_reorder_zero')
                    check(bool(slices) and 0 not in slices,
                          f'{cid}: HEVC observed slice types {slices}, B-slice type 0 was present',
                          errors, counts, 'hevc_no_b_slice')
                elif case['codec'] == 'av1':
                    shown = syntax.get('show_frame', {}).get('values', [])
                    frame_types = syntax.get('frame_type', {}).get('values', [])
                    check(shown == [1], f'{cid}: AV1 show_frame values {shown}, expected [1]', errors, counts,
                          'av1_show_frame')
                    check(0 in frame_types and 1 in frame_types,
                          f'{cid}: AV1 frame_type values {frame_types}, expected key and inter frames', errors,
                          counts, 'av1_key_inter')
                stream_total = len(stream_bytes) + extra_bytes

            check(first_lag == 0, f'{cid}: first packet input lag is {first_lag}, expected 0', errors, counts,
                  'first_packet_lag')
            check(flush_only == 0, f'{cid}: {flush_only} packets returned only at flush', errors, counts,
                  'flush_packets')
            check(sorted(output_ids) == list(range(n)),
                  f'{cid}: decoded/output frame IDs {output_ids[:6]}... do not cover source input IDs', errors,
                  counts, 'decoded_frame_ids')
            if case['codec'] != 'gm01':
                check(availability_ids == output_ids, f'{cid}: decoded availability list differs from output IDs',
                      errors, counts, 'decoded_availability')
                check(int(info.get('decoded_frames_only_at_flush', -1)) == 0,
                      f'{cid}: decoded frames appear only at decoder flush', errors, counts, 'flush_decoded')
                check(all(p['pts'] == p['dts'] and p['input_lag_frames'] == 0 for p in packets) and
                      all(v['input_lag_frames'] == 0 and v['phase'] == 'input'
                          for v in info['output_availability']),
                      f'{cid}: packet reorder or delayed decoded output observed', errors, counts,
                      'all_packet_and_output_lag_zero')
            else:
                check(int(info.get('dropped_frames', -1)) == 0 and len(info.get('decode_calls', [])) == n,
                      f'{cid}: GM01 decode frame count/drop mismatch', errors, counts, 'decoded_frame_ids')

            # Recompute summary byte/rate values independently from ledger rows.
            grouped = [0] * n
            for packet in packets:
                pts = int(packet['pts'])
                check(0 <= pts < n, f'{cid}: packet PTS outside input sequence: {pts}', errors, counts,
                      'packet_pts_range')
                if 0 <= pts < n:
                    grouped[pts] += int(packet['bytes'])
            grouped[0] += extra_bytes
            fps = Fraction(clip.get('selected_fps') or clip['source_metadata'].get('selected_fps') or
                           clip['source_metadata'].get('source_fps') or clip.get('frame_rate'))
            summary = case['summary']
            total = sum(grouped)
            check(total == stream_total == summary['coded_bytes'],
                  f'{cid}: recomputed coded byte total {total} differs from report', errors, counts,
                  'summary_coded_bytes')
            check(close(total / n, summary['mean_bytes_per_frame']),
                  f'{cid}: mean coded bytes/frame mismatch', errors, counts, 'summary_mean_bytes')
            rate = total / n * 8 * float(fps) / 1e6
            check(close(rate, summary['coded_mbps_at_source_cadence']),
                  f'{cid}: coded Mbps at selected cadence mismatch', errors, counts, 'summary_rate')
            check(sum(size > 49152 for size in grouped) == summary['access_units_over_49152'],
                  f'{cid}: access unit cap count mismatch', errors, counts, 'summary_cap_count')
            expected_dist = distribution(grouped)
            actual_dist = summary['access_unit_bytes']
            for metric, value in expected_dist.items():
                check(metric in actual_dist and close(value, actual_dist[metric]),
                      f'{cid}: access-unit distribution field {metric} mismatch', errors, counts,
                      'summary_distribution')
            # Conversion-inclusive timing fences are re-summed, never treated
            # as target timing or as capture-to-display latency.
            timings = {
                'encode_frontend_ms': [c['encode_call_ms']+c.get('convert_ms', 0) for c in info['frame_calls']],
                'decode_to_rgb_ms': [c['decode_ms']+c.get('rgb_convert_ms', 0) for c in info['decode_calls']]}
            for fence, values in timings.items():
                for key, value in distribution(values).items():
                    check(close(summary[fence][key], value),
                          f'{cid}: {fence} {key} mismatch', errors, counts, 'timing_fence_distribution')

            # Pool per-frame squared-error sums / pixel counts, independent of
            # precomputed pooled fields. Temporal statistics use the frame rows.
            qrows = quality['frames']
            check(len(qrows) == n and [int(row['id']) for row in qrows] == list(range(n)),
                  f'{cid}: quality frame identity/count mismatch', errors, counts, 'quality_frame_count')
            for region in ('active', 'roi', 'background'):
                se = sum(float(row['regions'][region]['squared_error_sum']) for row in qrows)
                pixels = sum(int(row['regions'][region]['pixels']) for row in qrows)
                mse = se / pixels if pixels else float('nan')
                pooled = quality['pooled'][region]['mse']
                check(pixels > 0 and close(mse, pooled),
                      f'{cid}: pooled {region} MSE from per-frame SSE/pixels mismatches', errors, counts,
                      'quality_pooled_mse')
                if region in ('active', 'roi'):
                    check(close(mse, summary[f'{region}_mse']),
                          f'{cid}: case summary {region} MSE differs from quality rows', errors, counts,
                          'quality_summary_mse')
                    expected_psnr = 10*math.log10(65025/mse) if mse else None
                    check((expected_psnr is None and summary[f'{region}_psnr_db'] is None) or
                          (expected_psnr is not None and close(expected_psnr, summary[f'{region}_psnr_db'])),
                          f'{cid}: {region} PSNR mismatch', errors, counts, 'quality_summary_psnr')
            temporal = [float(row['temporal_error_mse']) for row in qrows[1:]]
            check(close(sum(temporal) / len(temporal), quality['temporal_error_mse_mean']) and
                  close(max(temporal), quality['temporal_error_mse_max']),
                  f'{cid}: temporal error pooled summary mismatch', errors, counts, 'quality_temporal')
            audited_cases.append({'case_id': cid, 'codec': case['codec'], 'coded_bytes': total,
                                  'frame_count': n, 'selected_fps': str(fps),
                                  'output_frame_count': len(output_ids), 'syntax_returncode':
                                  info.get('inspection_returncode') if case['codec'] != 'gm01' else None})
        except Exception as e:
            errors.append(f'{cid}: auditor exception: {type(e).__name__}: {e}')

    return {
        'schema': 'v98-independent-audit-v1',
        'auditor_sha256': sha_file(Path(__file__).resolve()),
        'status': 'PASS' if not errors else 'FAIL',
        'index_path': str(index_path.relative_to(ROOT)) if index_path.is_relative_to(ROOT) else str(index_path),
        'index_sha256': sha_file(index_path),
        'attempt_json': str(report_path.relative_to(ROOT)),
        'attempt_report_sha256': sha_bytes(report_bytes),
        'case_count': len(audited_cases),
        'audited_cases': audited_cases,
        'check_counts': counts,
        'errors': errors,
        'limitations': [
            'Game-video inputs are decoded compressed-source frames, not raw gameplay captures.',
            'Synthetic ROI rectangles probe interior HUD-like regions and omit drawn boundary pixels; they do not represent complete HUD coverage.',
            'Game ROI rectangles are generic geometric probes with unverified HUD semantics.',
            'This audit verifies report, packet, cadence, source, and pooled-quality arithmetic; it does not establish target-hardware throughput or visual quality beyond the recorded pixel metrics.'
        ]
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index', type=Path, default=AREA / 'index.json')
    parser.add_argument('--output', type=Path, default=AREA / 'audit.json')
    args = parser.parse_args()
    result = audit(args.index)
    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print(json.dumps({'status': result['status'], 'case_count': result['case_count'],
                      'check_counts': result['check_counts'], 'errors': result['errors']}, indent=2))
    if result['status'] != 'PASS':
        sys.exit(1)


if __name__ == '__main__':
    main()
