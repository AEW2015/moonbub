#!/usr/bin/env python3
"""Independent receipt/archive replay and deterministic V92 result summary."""
import gzip
import hashlib
import json
from pathlib import Path
import struct
import zlib

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT/'experiments/python-gamebub-v92'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def receipt(path):
    pointer = json.loads(path.read_text())
    report_path = ROOT/pointer['selected_report']
    report = json.loads(report_path.read_text())
    assert report['status'].startswith('PASS'), (path, report['status'])
    for name, digest in report['source_sha256'].items():
        assert sha(ROOT/name) == digest, ('stale source/input', name)
    for key in ('artifacts_sha256', 'artifact_sha256'):
        for name, digest in report.get(key, {}).items():
            assert sha(report_path.parent/name) == digest, ('changed artifact', name)
    return report_path, report


def main():
    native_path, native = receipt(AREA/'native/index.json')
    python_path, python = receipt(AREA/'python/index.json')
    selection_path, selection = receipt(AREA/'selection/results.json')
    wire_path, wire = receipt(AREA/'wire/results.json')
    tests_path, tests = receipt(AREA/'wire/tests.json')
    rows = [json.loads(line) for line in wire_path.with_name('frames.jsonl').read_text().splitlines()]
    by_key = {(r['policy'], r['cohort'], r['fid']): r for r in rows}
    assert len(rows) == len(by_key) == 1828
    count = 0
    # Reparse every retained actual frame without importing the assembler or
    # receiver. Verify lengths, all CRCs, selected masks and commitment binding.
    with gzip.open(wire_path.with_name('packets.bin.gz'), 'rb') as stream:
        while True:
            prefix = stream.read(8)
            if not prefix:
                break
            assert len(prefix) == 8
            meta_size, size = struct.unpack('<II', prefix)
            assert 0 < meta_size < 16384 and 132 <= size <= 49152
            meta = json.loads(stream.read(meta_size))
            packet = stream.read(size)
            assert len(packet) == size and packet[:5] == b'CS92\x01'
            row = by_key[(meta['policy'], meta['cohort'], meta['fid'])]
            assert meta == row and hashlib.sha256(packet).hexdigest() == row['packet_sha256']
            assert zlib.crc32(packet[:-4]) == int.from_bytes(packet[-4:], 'big')
            assert packet[52:84].hex() == row['decoded']['root']
            assert packet[84:116].hex() == row['decoded']['seal']
            mode_size, q_size, hud_size, data_size = struct.unpack_from('>4I', packet, 36)
            assert size == 132+mode_size+q_size+hud_size+data_size
            at = 128+mode_size+q_size
            begin = at
            for axis in range(3):
                chunks = struct.unpack_from('>I', packet, at)[0]
                at += 4
                assert chunks == 1
                blocks, length = struct.unpack_from('>II', packet, at)
                at += 8
                chunk = packet[at:at+length]
                assert chunk[:5] == b'EC92\x01' and chunk[5] == 0
                assert chunk[6] == row['plane_masks'][axis] and chunk[7] == 0
                assert blocks == struct.unpack_from('<I', chunk, 8)[0]
                assert length == 48+sum(struct.unpack_from('<4I', chunk, 16))
                assert zlib.crc32(chunk[:-4]) == int.from_bytes(chunk[-4:], 'little')
                at += length
            assert at-begin == data_size and at+hud_size+4 == size
            assert row['wire_bytes'] == size <= row['budget'] <= 49152
            count += 1
    assert count == len(rows)
    policies = {s['policy']: s for s in wire['summaries']}
    for policy, summary in policies.items():
        selected = [r for r in rows if r['policy'] == policy]
        assert len(selected) == 457
        for k in ('ab_decisions', 'ab_renorm', 'br_bits'):
            assert sum(r[k] for r in selected) == summary[k]
        assert sum(r['wire_bytes'] for r in selected) == summary['wire_bytes']['total']
        assert max(r['wire_bytes'] for r in selected) == summary['wire_bytes']['max']
    context = policies['context_work15']
    whole = policies['whole_plane_work15']
    contexts = {(r['cohort'], r['fid']): r for r in rows if r['policy'] == 'context_work15'}
    wholes = {(r['cohort'], r['fid']): r for r in rows if r['policy'] == 'whole_plane_work15'}
    for ident in contexts:
        a, b = contexts[ident], wholes[ident]
        assert (a['ab_decisions'], a['ab_renorm'], a['br_bits'], a['mask'], a['wire_bytes']) <= (b['ab_decisions'], b['ab_renorm'], b['br_bits'], b['mask'], b['wire_bytes'])
    old_ab = sum(r['old_AB38_bytes'] for r in rows if r['policy'] == 'context_byte_min')
    old_plane_min = sum(r['old_plane_min_bytes'] for r in rows if r['policy'] == 'context_byte_min')
    result = dict(schema='cu66-v92-summary-v1', status='PASS_REPLAYED_V92_SOFTWARE_EVIDENCE',
                  baseline_commit='3b068d7aaea62ab7422e3fa63f68c365fe503aa9',
                  evidence={str(p.relative_to(ROOT)): sha(p) for p in (native_path, python_path, selection_path, wire_path, tests_path)},
                  version=dict(v92a='qualified research grammar', v92b='actual bytes qualified',
                               v92c='software parity/host accounting qualified for retained corpus',
                               v92d='open: integrated costing and promoted RTL adapter'),
                  physical_30fps_proven=False, validated_under10ms_proven=False,
                  frames=457, actual_component_candidates=native['actual_candidates'], full_packets=count,
                  exhaustive_combinations=wire['exhaustive_combinations'],
                  old_AB38_complete_bytes=old_ab, old_plane_min_complete_bytes=old_plane_min,
                  byte_min_complete_delta_vs_old_AB38=policies['context_byte_min']['wire_bytes']['total']-old_ab,
                  component_byte_min_delta_vs_old_AB38=native['totals']['min_bytes']-native['totals']['old_bytes'],
                  policies=wire['summaries'],
                  context_work15_fewer_AB_decisions=whole['ab_decisions']-context['ab_decisions'],
                  context_work15_byte_delta=context['wire_bytes']['total']-whole['wire_bytes']['total'],
                  context_work15_changed_frames=sum(contexts[k]['mask'] != wholes[k]['mask'] for k in contexts),
                  native_frame_generation_ns=native['frame_generation_ns'], native_peak_rss_kib=native['native_peak_rss_kib'],
                  selection_search_ns=wire['pareto_search_ns'], selection_peak_states=wire['pareto_peak'],
                  independent_python_checks=python['checks_count'], protocol_checks=tests['checks_count'])
    (AREA/'summary.json').write_text(json.dumps(result, indent=2)+'\n')
    lines = ['# V92 measured results', '',
        'The retained software campaign passes; **V92a–c are qualified for this corpus and V92d remains open**.', '',
        f'- {native["native_sources"]} sources, {native["chunks"]:,} plane chunks and {native["actual_candidates"]:,} actual EC92 candidates.',
        f'- {native["coefficient_values"]:,} coefficient values match; native decodes every selector pattern, and independent Python decodes both alternatives for every distinct context.',
        f'- {count:,} complete CS92 packets reproduce exact coefficients, canonical/reference pixels, semantic HUD, RGB565, content root and seal.',
        f'- {wire["exhaustive_combinations"]:,} frame combinations checked against bounded selection, plus the independent synthetic selector tests.',
        f'- {python["checks_count"]} independent grammar checks and {tests["checks_count"]} complete-protocol checks pass. Native fixtures add 80 roundtrips and 4,656 rejections.', '',
        '| Policy | Total complete bytes | Maximum frame bytes | AB decisions | BR bit reads |',
        '|---|---:|---:|---:|---:|']
    for p in wire['summaries']:
        lines.append(f'| {p["policy"]} | {p["wire_bytes"]["total"]:,} | {p["wire_bytes"]["max"]:,} | {p["ab_decisions"]:,} | {p["br_bits"]:,} |')
    delta = result['byte_min_complete_delta_vs_old_AB38']
    lines += ['', f'Frozen CS88 all-AB38 complete bytes: **{old_ab:,}**. EC92 minimum-byte selection changes this by **{delta:+,} B ({delta/old_ab*100:+.4f}%)**, including its six extra header bytes per frame.',
        f'The matched 15% contextual policy removes **{result["context_work15_fewer_AB_decisions"]:,}** additional adaptive decisions versus whole-plane selection, changes total bytes by **{result["context_work15_byte_delta"]:+,}**, and changes {result["context_work15_changed_frames"]} frame choices. Plain Rice bit reads remain charged.', '',
        '## Host preparation and bounds', '',
        f'Linux native candidate generation: minimum **{native["frame_generation_ns"]["min"]/1e6:.3f} ms**, median **{native["frame_generation_ns"]["median"]/1e6:.3f} ms**, p95 **{native["frame_generation_ns"]["p95"]/1e6:.3f} ms**, maximum **{native["frame_generation_ns"]["max"]/1e6:.3f} ms** per frame. This includes both coders, discarded assemblies/hashes and frozen coefficient extraction, with encoder internal parity validation included.',
        f'Native collector peak RSS: **{native["native_peak_rss_kib"]:,} KiB**. This covers the helper process, not all Python/archival memory or a whole Sunshine session.',
        f'Bounded Python selection has median **{wire["pareto_search_ns"]["median"]/1e6:.3f} ms**, maximum **{wire["pareto_search_ns"]["max"]/1e6:.3f} ms**, and maximum **{wire["pareto_peak"]["max"]}** proposed states in this corpus. Exhaustive verification and full-frame assembly/CRC/validation are outside that selection timer.', '',
        'No live capture/DCT, Sunshine cadence, ESP32 firmware, QSPI DMA, physical SDRAM or FPGA timing is measured here. The corpus is one related precompressed walkthrough family in four reset histories, not independent raw gameplay captures.', '',
        '## Decision and next gate', '',
        'Keep EC92 as a research candidate. Its compression gain is small; the useful result is the exact byte/work tradeoff with bounded host search. The supported V91 RTL remains BR88-only. Before promotion, charge an implemented mixed arithmetic/Rice adapter against the actual shared-memory/display service, then rerun complete-path goldens and fixed 30-Hz source releases. V91l, hardware 30 fps and complete validated under-10-ms decoding remain open.', '',
        'Machine-readable [summary](../../experiments/python-gamebub-v92/summary.json) binds the selected immutable evidence. Reproduction, wire grammar and scope are in the [README](README.md).', '']
    (ROOT/'docs/cu66-v92/results.md').write_text('\n'.join(lines))
    print(result['status'], 'packets', count, 'byte_delta', delta)


if __name__ == '__main__':
    main()
