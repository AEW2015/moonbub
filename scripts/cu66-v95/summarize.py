#!/usr/bin/env python3
"""Recount complete CS95 archives and bind qualified receipts to the decision."""
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import struct
import zlib

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v95'


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    pins = {}

    def read(path):
        path = ROOT / path
        pins[str(path.relative_to(ROOT))] = sha(path)
        return json.loads(path.read_text())

    def verify(report, path):
        assert report['status'].startswith('PASS'), (path, report['status'])
        for key in ('source_sha256', 'archive_sha256'):
            for name, expected in report.get(key, {}).items():
                assert sha(ROOT / name) == expected, ('stale evidence', path, name)
        for key in ('artifacts_sha256', 'artifact_sha256'):
            for name, expected in report.get(key, {}).items():
                artifact = (ROOT / path).parent / name
                assert sha(artifact) == expected, ('artifact changed', path, name)

    reports = {}
    for name in ('native/index.json', 'python/index.json', 'python/corpus-index.json',
                 'wire/results.json', 'wire/tests.json', 'selection/results.json'):
        path = str((AREA / name).relative_to(ROOT))
        pointer = read(path)
        selected = pointer.get('selected_report', path)
        report = read(selected)
        verify(report, selected)
        reports[name] = report
    repeat = read('experiments/python-gamebub-v95/native/repeat-check.json')
    assert repeat['status'] == 'PASS_BYTE_IDENTICAL_REPEAT'
    assert repeat['first'] == reports['wire/results.json']['native_input_report']
    native = reports['native/index.json']
    assert repeat['second'] == json.loads((AREA / 'native/index.json').read_text())['selected_report']
    wire = reports['wire/results.json']
    attempt = (ROOT / json.loads((AREA / 'wire/results.json').read_text())['selected_report']).parent
    rows = [json.loads(line) for line in (attempt / 'frames.jsonl').read_text().splitlines()]
    assert len(rows) == 4113
    expected = {(r['policy'], r['cohort'], r['fid']): r for r in rows}
    controls = {(r['cohort'], r['fid']): r for r in rows if r['policy'] == 'control'}
    total_control = sum(r['wire_bytes'] for r in controls.values())
    active_control = sum(r['residual_blocks'] for r in controls.values())
    summaries = []
    for policy in wire['policies']:
        counts = Counter()
        worst = None
        with gzip.open(attempt / ('packets-' + policy + '.bin.gz'), 'rb') as stream:
            while True:
                header = stream.read(8)
                if not header:
                    break
                assert len(header) == 8
                ml, pl = struct.unpack('<II', header)
                assert ml < 16384 and pl <= 2097152
                meta = json.loads(stream.read(ml))
                packet = stream.read(pl)
                assert len(packet) == pl and packet[:4] == b'CS95'
                assert meta == expected[(policy, meta['cohort'], meta['fid'])]
                assert hashlib.sha256(packet).hexdigest() == meta['packet_sha256']
                assert zlib.crc32(packet[:-4]) == struct.unpack('>I', packet[-4:])[0]
                maplen, qlen, hudlen, datalen = struct.unpack_from('>IIII', packet, 36)
                at = 128 + maplen + qlen
                end = at + datalen
                assert end + hudlen + 4 == pl
                pal = residual = 0
                for axis, bound in enumerate((5400, 1350, 1350)):
                    n, = struct.unpack_from('>I', packet, at)
                    at += 4
                    assert n <= bound
                    last = -1
                    for _ in range(n):
                        pos, length = struct.unpack_from('>HH', packet, at)
                        at += 4
                        assert last < pos < bound and 2 <= length <= 138
                        last = pos
                        kind = packet[at]
                        assert kind <= 4
                        counts['record_kind_' + str(kind)] += 1
                        at += length
                        assert at <= end
                    blocks, entropylen = struct.unpack_from('>II', packet, at)
                    at += 8
                    assert blocks <= bound - n
                    if blocks:
                        assert packet[at:at + 4] == b'EC92' and entropylen > 0
                    else:
                        assert entropylen == 0
                    at += entropylen
                    assert at <= end
                    pal += n
                    residual += blocks
                assert at == end
                assert pal == meta['avoided_tiles'] == meta['decoded']['palette_tiles']
                assert residual == meta['residual_blocks'] == meta['decoded']['residual_tiles']
                control = controls[(meta['cohort'], meta['fid'])]
                assert pal + residual == control['residual_blocks']
                if policy in ('control', 'byte_min', 'work5', 'work15'):
                    assert pl <= 49152 and meta['strict_receiver']
                if policy in ('work5', 'work15'):
                    pct = 105 if policy == 'work5' else 115
                    assert pl <= min(49152, control['wire_bytes'] * pct // 100)
                if policy == 'byte_min':
                    assert pl == control['wire_bytes'] and pal == 0
                counts.update(frames=1, wire_bytes=pl, palette_tiles=pal,
                              residual_blocks=residual, fits_49152=int(pl <= 49152),
                              frames_using_palettes=int(pal > 0))
                delta = pl - control['wire_bytes']
                candidate = dict(cohort=meta['cohort'], fid=meta['fid'],
                                 wire_bytes=pl, extra_bytes=delta,
                                 extra_percent=100 * delta / control['wire_bytes'])
                if worst is None or candidate['extra_percent'] > worst['extra_percent']:
                    worst = candidate
        assert counts['frames'] == 457
        recorded = next(s for s in wire['summaries'] if s['policy'] == policy)
        assert counts['wire_bytes'] == recorded['wire_bytes']['total']
        assert counts['palette_tiles'] == recorded['avoided_tiles']
        summaries.append(dict(policy=policy, **dict(counts),
                              wire_max=recorded['wire_bytes']['max'],
                              byte_delta_percent=100 * (counts['wire_bytes'] / total_control - 1),
                              bypassed_block_percent=100 * counts['palette_tiles'] / active_control,
                              worst_relative_frame=worst))
    pins[str(Path(__file__).resolve().relative_to(ROOT))] = sha(Path(__file__).resolve())
    result = dict(schema='cu66-v95-qualified-summary-v1', status='PASS',
                  input_sha256=pins, frames=457, full_packets_recounted=4113,
                  native_variants=native['actual_variants'],
                  independent_unit_checks=reports['python/index.json']['checks_count'],
                  protocol_checks=reports['wire/tests.json']['checks_count'],
                  selection_scenarios=reports['selection/results.json']['scenarios'],
                  native_frame_generation_ns=native['frame_generation_ns'],
                  independently_checked_palette_records=reports['python/corpus-index.json']['palette_records'],
                  control_bytes=total_control, control_residual_blocks=active_control,
                  policies=summaries,
                  decision='Retain control for rate; keep work-budget palette lane research-only.',
                  physical_30fps_proven=False, validated_under10ms_proven=False,
                  original_coefficient_parity_claimed=False, promoted_to_RTL=False,
                  limitations=['Predecoded canonical targets; capture/DCT/target generation unmeasured.',
                               'Bypassed block counts are work proxies, not FPGA latency or SDRAM measurements.',
                               'One precompressed walkthrough family plus synthetic fixtures; no new raw captures.',
                               'No palette RTL, ESP32 firmware integration, device mapping or routed timing.',
                               'Whole-plane profile tuple selection is not global tile-subset optimization.'])
    (AREA / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS_V95_SUMMARY', len(rows), 'packets;', total_control, 'control bytes')
    for row in summaries:
        print(row['policy'], row['wire_bytes'], row['palette_tiles'],
              round(row['byte_delta_percent'], 3), round(row['bypassed_block_percent'], 3))


if __name__ == '__main__':
    main()
