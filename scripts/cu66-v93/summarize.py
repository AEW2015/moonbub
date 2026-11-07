#!/usr/bin/env python3
"""Reparse retained CS93 bytes and bind reproducible software comparisons."""
import gzip
import hashlib
import json
from pathlib import Path
import struct
import zlib

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT/'experiments/python-gamebub-v93'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def receipt(path):
    pointer = json.loads(path.read_text())
    target = ROOT/pointer['selected_report']
    value = json.loads(target.read_text())
    assert value['status'].startswith('PASS'), (target, value['status'])
    for name, digest in value['source_sha256'].items():
        assert sha(ROOT/name) == digest, ('stale source', name)
    for key in ('artifacts_sha256', 'artifact_sha256'):
        for name, digest in value.get(key, {}).items():
            assert sha(target.parent/name) == digest, ('changed artifact', name)
    return target, value


def main():
    native_path, native = receipt(AREA/'native/index.json')
    python_path, python = receipt(AREA/'python/index.json')
    selection_path, selection = receipt(AREA/'selection/results.json')
    wire_path, wire = receipt(AREA/'wire/results.json')
    test_path, tests = receipt(AREA/'wire/tests.json')
    rows = list(map(json.loads, wire_path.with_name('frames.jsonl').read_text().splitlines()))
    by_key = {(r['policy'], r['cohort'], r['fid']): r for r in rows}
    assert len(rows) == len(by_key) == 4113
    count = 0
    with gzip.open(wire_path.with_name('packets.bin.gz'), 'rb') as stream:
        while True:
            prefix = stream.read(8)
            if not prefix:
                break
            assert len(prefix) == 8
            meta_size, size = struct.unpack('<II', prefix)
            assert 0 < meta_size < 16384 and 132 <= size <= 2097152
            meta = json.loads(stream.read(meta_size))
            packet = stream.read(size)
            assert len(packet) == size and packet[:5] == b'CS93\x01'
            row = by_key[(meta['policy'], meta['cohort'], meta['fid'])]
            assert meta == row and hashlib.sha256(packet).hexdigest() == row['packet_sha256']
            assert zlib.crc32(packet[:-4]) == int.from_bytes(packet[-4:], 'big')
            assert packet[52:84].hex() == row['decoded']['root'] and packet[84:116].hex() == row['decoded']['seal']
            mode_size, q_size, hud_size, data_size = struct.unpack_from('>4I', packet, 36)
            assert size == 132+mode_size+q_size+hud_size+data_size
            at = 128+mode_size+q_size
            start = at
            for axis in range(3):
                assert struct.unpack_from('>I', packet, at)[0] == 1
                at += 4
                blocks, length = struct.unpack_from('>II', packet, at)
                at += 8
                chunk = packet[at:at+length]
                assert chunk[:5] == b'EC93\x01' and chunk[5] == 0 and chunk[7] == 0
                assert chunk[6] == row['selectors'][axis] and struct.unpack_from('<I', chunk, 8)[0] == blocks
                assert length == 48+sum(struct.unpack_from('<4I', chunk, 16))
                assert zlib.crc32(chunk[:-4]) == int.from_bytes(chunk[-4:], 'little')
                at += length
            assert at-start == data_size and at+hud_size+4 == size
            assert row['wire_bytes'] == size and row['fits_49152'] == (size <= 49152)
            if not row['diagnostic_receiver']:
                assert size <= 49152
            if row['budget'] is not None:
                assert size <= row['budget'] <= 49152
            count += 1
    assert count == len(rows)
    summaries = {r['policy']: r for r in wire['summaries']}
    for policy, summary in summaries.items():
        group = [r for r in rows if r['policy'] == policy]
        assert len(group) == 457
        assert sum(r['wire_bytes'] for r in group) == summary['wire_bytes']['total']
        assert max(r['wire_bytes'] for r in group) == summary['wire_bytes']['max']
        for key in ('ab_decisions', 'ab_renorm', 'plain_bits', 'arithmetic_inits', 'group_headers'):
            assert sum(r[key] for r in group) == summary[key]
    # Explicit anchors ensure the approximation never loses the supported
    # V92 work candidate under the identical complete-byte allowance.
    for ident in {(r['cohort'], r['fid']) for r in rows}:
        new, old = by_key[('work15', *ident)], by_key[('v92_work15', *ident)]
        rank = lambda r: (r['ab_decisions'], r['ab_renorm'], r['plain_bits'], r['wire_bytes'])
        assert rank(new) <= rank(old), ident
    new = summaries['work15']
    old = summaries['v92_work15']
    decisions_removed = old['ab_decisions']-new['ab_decisions']
    byte_delta = new['wire_bytes']['total']-old['wire_bytes']['total']
    byte_min_delta = summaries['byte_min']['wire_bytes']['total']-summaries['v92_byte_min']['wire_bytes']['total']
    ab, hy, br, sg = [summaries[k] for k in ('all_AB', 'prefix_suffix', 'all_BR', 'small_group')]
    hy_decision_percent = 100*(ab['ab_decisions']-hy['ab_decisions'])/ab['ab_decisions']
    hy_byte_percent = 100*(hy['wire_bytes']['total']-ab['wire_bytes']['total'])/ab['wire_bytes']['total']
    sg_plain_percent = 100*(br['plain_bits']-sg['plain_bits'])/br['plain_bits']
    sg_byte_percent = 100*(sg['wire_bytes']['total']-br['wire_bytes']['total'])/br['wire_bytes']['total']
    summary = dict(schema='cu66-v93-summary-v1', status='PASS_REPLAYED_V93_SOFTWARE_EVIDENCE',
                   baseline_commit='cadc1891acc06950f241307a408897c91c706638',
                   evidence={str(p.relative_to(ROOT)): sha(p) for p in (native_path, python_path, selection_path, wire_path, test_path)},
                   version=dict(v93a='specified fixed mechanisms', v93b='actual bytes and independent readers qualified',
                                v93c='software corpus comparison qualified', v93d='research decision only; integrated RTL/latency promotion open'),
                   physical_30fps_proven=False, validated_under10ms_proven=False, frames=457,
                   component_packets=native['actual_candidates'], complete_packets=count,
                   coefficient_values=native['coefficient_values'], policies=wire['summaries'],
                   byte_min_delta_vs_V92=byte_min_delta, work15_AB_decisions_removed=decisions_removed,
                   HY_vs_AB_arithmetic_decision_reduction_percent=hy_decision_percent,
                   HY_vs_AB_complete_byte_growth_percent=hy_byte_percent,
                   SG_vs_BR_plain_bit_reduction_percent=sg_plain_percent,
                   SG_vs_BR_complete_byte_growth_percent=sg_byte_percent,
                   work15_AB_decisions_removed_percent=100*decisions_removed/old['ab_decisions'],
                   work15_byte_delta_vs_V92=byte_delta,
                   work15_byte_delta_percent=100*byte_delta/old['wire_bytes']['total'],
                   native_frame_generation_ns=native['frame_generation_ns'],
                   native_peak_rss_kib=native['native_peak_rss_kib'], two_policy_search_ns=wire['two_search_ns'],
                   beam_peak=wire['beam_peak'], beam_truncated_stages=wire['beam_truncated_stages'],
                   independent_python_checks=python['checks_count'], protocol_checks=tests['checks_count'])
    (AREA/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    lines = ['# V93 measured results', '',
             '**V93a–c software evidence is qualified for the retained corpus. Product promotion remains open.**', '',
             f'- {native["native_sources"]} sources, {native["chunks"]:,} planes and {native["actual_candidates"]:,} actual component packets.',
             f'- {native["coefficient_values"]:,} coefficient values match; native and independent Python verify all four alternatives.',
             f'- {count:,} complete CS93 packets preserve exact coefficients, canonical/reference pixels, HUD, RGB565, roots and seals.',
             f'- {python["checks_count"]:,} independent grammar checks, including all 256 selectors; {tests["checks_count"]} complete-protocol checks.', '',
             '| Policy | Complete bytes | Max bytes | Frames fitting 49,152 B | Arithmetic decisions | Plain bit reads |',
             '|---|---:|---:|---:|---:|---:|']
    for row in wire['summaries']:
        lines.append(f'| {row["policy"]} | {row["wire_bytes"]["total"]:,} | {row["wire_bytes"]["max"]:,} | {row["fits_49152"]}/457 | {row["ab_decisions"]:,} | {row["plain_bits"]:,} |')
    lines += ['', f'Uniform HY replaces **{ab["ab_decisions"]-hy["ab_decisions"]:,} arithmetic decisions ({hy_decision_percent:.2f}%)** with plain suffix reads versus uniform AB, at **{hy_byte_percent:.3f}% more complete bytes**. All 457 HY frames fit the target cap; maximum {hy["wire_bytes"]["max"]:,} bytes. This is the useful prefix-bypass tradeoff, rather than a new compression gain.',
              f'Uniform SG uses **{sg_plain_percent:.2f}% fewer plain bit reads** than BR but **{sg_byte_percent:.3f}% more complete bytes**, charging {sg["group_headers"]:,} group headers ({sg["group_headers"]*6:,} bytes). Eight SG frames exceed the target cap. Smaller Rice payloads alone are an insufficient selection criterion.',
              f'Exact minimum-byte selection changes V92 by **{byte_min_delta:+,} bytes**. Neither the all-suffix bypass rule nor fixed 32-event Rice grouping improves the minimum-byte frontier on these inputs.',
              f'At the same complete-byte allowance, the bounded work15 policy removes **{decisions_removed:,} ({summary["work15_AB_decisions_removed_percent"]:.2f}%)** remaining arithmetic decisions versus the frozen V92 work15 control, with **{byte_delta:+,} bytes ({summary["work15_byte_delta_percent"]:+.3f}%)**. This compares actual work counts; plain reads, initialization and group metadata remain real work. It is not a measured FPGA speedup.', '',
              '## Host preparation and search', '',
              f'Native generation per frame: minimum **{native["frame_generation_ns"]["min"]/1e6:.3f} ms**, median **{native["frame_generation_ns"]["median"]/1e6:.3f} ms**, p95 **{native["frame_generation_ns"]["p95"]/1e6:.3f} ms**, maximum **{native["frame_generation_ns"]["max"]/1e6:.3f} ms** on this Linux host. All four method preparations, five assemblies/hashes and discarded alternatives are included; source coefficient extraction and the frozen encoder internal verification are included.',
              f'Native collector peak RSS is **{native["native_peak_rss_kib"]:,} KiB**. It excludes the parent Python/archive process and live application memory. The native report also records process-family RSS observations separately.',
              f'The two bounded work-policy searches together take median **{wire["two_search_ns"]["median"]/1e6:.3f} ms**, maximum **{wire["two_search_ns"]["max"]/1e6:.3f} ms** per frame. Maximum proposals in a stage: **{wire["beam_peak"]}**. Pareto truncation occurred in **{wire["beam_truncated_stages"]}** stages; results are not globally optimal certificates.', '',
              'These are host component timings. Live capture/DCT, Sunshine cadence, ESP32/QSPI, physical shared SDRAM/display service, parser setup and achieved FPGA clock are unmeasured.', '',
              '## Decision', '',
              'Retain the fixed suffix-bypass method as a conditional work-proxy candidate. Keep V92 as the supported reference and reject fixed SG32 as the default size policy on this corpus; its group headers outweigh the local parameter benefit. No new method is promoted into RTL or the application firmware by this study.',
              f'The work15 proxy selects {new["method_streams"][3]:,} SG streams and charges their bytes, but does not price {new["group_headers"]:,} group-header parse operations as calibrated cycles. Its lower arithmetic/plain counts cost extra wire traffic; do not adopt that objective as a latency policy before adding measured metadata/setup and shared-memory costs.',
              'The homogeneous controls use a diagnostic 2-MiB receiver where needed; only the selected policies and frozen V92 controls use normal 49,152-byte admission. Cap-fit counts above are separate from diagnostic acceptance. RAW fallback is tested, but no frame-level overflow recovery profile is qualified for arbitrary future content.',
              'The suffix-bypass rule and group size were fixed before observation. Histograms are descriptive, not a trained held-out policy. All 457 sources remain one related precompressed walkthrough family; independent raw captures and matched-quality standard-codec comparisons remain open.',
              'Next qualify any proposed prefix/suffix hardware adapter against the actual memory/display bottleneck and complete frame goldens. V91l, V92d, sustained hardware 30 fps and complete validated under-10-ms decoding remain open.', '',
              '[Machine-readable summary](../../experiments/python-gamebub-v93/summary.json) · [Grammar and reproduction](README.md)', '']
    (ROOT/'docs/cu66-v93/results.md').write_text('\n'.join(lines))
    print(summary['status'], 'complete packets', count, 'decisions removed', decisions_removed, 'byte delta', byte_delta)


if __name__ == '__main__':
    main()
