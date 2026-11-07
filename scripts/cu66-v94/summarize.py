#!/usr/bin/env python3
"""Bind V94 whole-wire, parameter search and independent RTL evidence."""
import gzip
import hashlib
import json
from pathlib import Path
import struct
import zlib

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT/'experiments/python-gamebub-v94'
RTL = ROOT/'fpga/experiments/cu66-v94-rans'
WORK = ('ab_decisions', 'ab_renorm', 'literal_bits', 'ans_symbols',
        'ans_renorm_bytes', 'model_tables', 'model_entries', 'ans_lanes')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def receipt(pointer):
    selected = json.loads(pointer.read_text())
    path = ROOT/selected['selected_report']
    report = json.loads(path.read_text())
    assert report['status'].startswith('PASS'), (path, report['status'])
    for name, digest in report['source_sha256'].items():
        assert sha(ROOT/name) == digest, ('stale source/input', name)
    for key in ('artifact_sha256', 'artifacts_sha256'):
        for name, digest in report.get(key, {}).items():
            assert sha(path.parent/name) == digest, ('changed artifact', name)
    return path, report


def audit_packets(path, report):
    rows = list(map(json.loads, path.with_name('frames.jsonl').read_text().splitlines()))
    lookup = {(r['policy'], r['cohort'], r['fid']): r for r in rows}
    assert len(lookup) == len(rows) == report['packets']
    total = 0
    for policy in report['policies']:
        count = 0
        with gzip.open(path.with_name(f'packets-{policy}.bin.gz'), 'rb') as stream:
            while True:
                prefix = stream.read(8)
                if not prefix:
                    break
                assert len(prefix) == 8
                meta_size, size = struct.unpack('<II', prefix)
                assert 0 < meta_size < 16384 and 132 <= size <= 2097152
                meta = json.loads(stream.read(meta_size))
                packet = stream.read(size)
                row = lookup[(meta['policy'], meta['cohort'], meta['fid'])]
                assert row == meta and len(packet) == size
                assert hashlib.sha256(packet).hexdigest() == row['packet_sha256']
                assert packet[:5] == b'CS94\x01' and zlib.crc32(packet[:-4]) == int.from_bytes(packet[-4:], 'big')
                assert packet[52:84].hex() == row['decoded']['root'] and packet[84:116].hex() == row['decoded']['seal']
                mode, quantizer, hud, residual = struct.unpack_from('>4I', packet, 36)
                assert size == 132+mode+quantizer+hud+residual
                at = begin = 128+mode+quantizer
                model_tables = ans_lanes = 0
                for _ in range(3):
                    assert struct.unpack_from('>I', packet, at)[0] == 1
                    at += 4
                    blocks, length = struct.unpack_from('>II', packet, at)
                    at += 8
                    chunk = packet[at:at+length]
                    assert chunk[:5] == b'EC94\x01' and chunk[5] == chunk[7] == 0
                    assert struct.unpack_from('<I', chunk, 8)[0] == blocks
                    lengths = struct.unpack_from('<4I', chunk, 16)
                    counts = struct.unpack_from('<3I', chunk, 32)
                    assert 48+sum(lengths) == length
                    assert zlib.crc32(chunk[:-4]) == int.from_bytes(chunk[-4:], 'little')
                    pos = 44
                    for context, extent in enumerate(lengths):
                        method = (chunk[6] >> (2*context)) & 3
                        if method >= 2:
                            _, _, scale, table_mode, identity, nbytes, nbits, symbols = struct.unpack_from('<BBBB4I', chunk, pos)
                            models = 2 if context else 1
                            assert scale in (8, 9, 10) and table_mode == 0
                            tables = chunk[pos+20:pos+20+models*32]
                            assert zlib.crc32(tables) == identity
                            assert all(sum(struct.unpack_from('<16H', tables, m*32)) == 1 << scale for m in range(models))
                            assert symbols == (2*counts[context-1] if context else blocks)
                            lanes = 2 if method == 2 else 4
                            assert 20+32*models+nbytes+(nbits+7)//8 == extent
                            assert lanes*4 <= nbytes <= lanes*4+2*symbols
                            states = struct.unpack_from('<'+'I'*lanes, chunk, pos+20+models*32)
                            assert all((1 << 23) <= x < (1 << 31) for x in states)
                            model_tables += models
                            ans_lanes += lanes
                        pos += extent
                    assert pos+4 == length
                    at += length
                assert at-begin == residual and at+hud+4 == size
                assert model_tables == row['model_tables'] and ans_lanes == row['ans_lanes']
                assert row['fits_49152'] == (size <= 49152)
                if policy in ('all_AB', 'byte_min', 'v92_byte_min', 'rate_byte_min'):
                    assert size <= 49152
                count += 1
        assert count == 457
        total += count
    assert total == len(rows)
    for summary in report['summaries']:
        group = [r for r in rows if r['policy'] == summary['policy']]
        assert sum(r['wire_bytes'] for r in group) == summary['wire_bytes']['total']
        assert max(r['wire_bytes'] for r in group) == summary['wire_bytes']['max']
        assert sum(r['fits_49152'] for r in group) == summary['fits_49152']
        for key in WORK:
            assert sum(r[key] for r in group) == summary[key]
    return rows


def main():
    native_path, native = receipt(AREA/'native/index.json')
    opt_native_path, opt_native = receipt(AREA/'native/optimized/index.json')
    python_path, python = receipt(AREA/'python/index.json')
    wire_path, wire = receipt(AREA/'wire/results.json')
    optimized_path, optimized = receipt(AREA/'optimized-wire/results.json')
    tests_path, tests = receipt(AREA/'wire/tests.json')
    rtl_path, rtl = receipt(RTL/'results.json')
    audit_path, audit = receipt(RTL/'audit.json')
    fast_area = ROOT/'fpga/experiments/cu66-v94-rans-fast'
    fast_path, fast = receipt(fast_area/'results.json')
    fast_audit_path, fast_audit = receipt(fast_area/'audit.json')
    assert audit['native_rtl_report'] == str(rtl_path.relative_to(ROOT))
    assert len(audit['controls']) == 3 and all(c['rejected'] for c in audit['controls'])
    assert fast['base_control_report'] == str(rtl_path.relative_to(ROOT))
    assert fast['identical_whole_RV94_inputs'] and fast_audit['identical_whole_RV94_inputs']
    assert fast_audit['native_rtl_report'] == str(fast_path.relative_to(ROOT))
    assert fast_audit['all_no_stall_deltas_equal_zero_refills']
    assert len(fast_audit['controls']) == 3 and all(c['rejected'] for c in fast_audit['controls'])
    assert fast['total_symbols'] == rtl['total_symbols'] and not fast['default_promotion'] and not fast['routed_clock_qualified']
    vector_manifest = json.loads((ROOT/rtl['vector_report']).read_text())
    actual_cases = {i for i, row in enumerate(vector_manifest['cases']) if row['kind'] == 'actual_corpus'}
    actual_pairs = [r for r in fast['paired_no_stall_rows'] if r['case'] in actual_cases]
    actual_base = sum(r['base_decode_cycles'] for r in actual_pairs)
    actual_fast = sum(r['fast_decode_cycles'] for r in actual_pairs)
    actual_comparison = dict(context_encodings=len(actual_pairs), symbols=sum(r['symbols'] for r in actual_pairs),
                             base_cycles=actual_base, fast_cycles=actual_fast,
                             saved_cycles=actual_base-actual_fast,
                             reduction_percent=100*(actual_base-actual_fast)/actual_base)
    assert actual_comparison['context_encodings'] == 19 and actual_comparison['symbols'] == 30809
    rows = audit_packets(wire_path, wire)
    opt_rows = audit_packets(optimized_path, optimized)
    policies = {r['policy']: r for r in wire['summaries']+optimized['summaries']}
    assert len(rows)+len(opt_rows) == 5484
    assert policies['byte_min']['wire_bytes']['total'] == policies['v92_byte_min']['wire_bytes']['total']
    difference = policies['rate_byte_min']['wire_bytes']['total']-policies['v92_byte_min']['wire_bytes']['total']
    assert difference == -11 and policies['rate_byte_min']['ans_symbols'] == 797
    repeat = json.loads((AREA/'native/repeat-check.json').read_text())
    assert repeat['status'] == 'PASS' and repeat['actual_packets'] == 12339
    for name, digest in repeat['source_sha256'].items():
        assert sha(ROOT/name) == digest
    repair = json.loads((RTL/'cancel-repair.json').read_text())
    assert repair['status'] == 'PASS_REPRODUCED_FAIL_THEN_REPAIRED'
    assert sha(ROOT/repair['failure_report']) == repair['failure_report_sha256']
    assert sha(ROOT/repair['passing_report']) == repair['passing_report_sha256']
    assert repair['passing_report'] == str(rtl_path.relative_to(ROOT))
    assert len(rtl['canceled_configuration']) == 2 and len(rtl['recoveries']) == 3
    evidence = [native_path, opt_native_path, python_path, wire_path, optimized_path, tests_path, rtl_path, audit_path, fast_path, fast_audit_path,
                AREA/'native/repeat-check.json', RTL/'cancel-repair.json']
    output = dict(schema='cu66-v94-summary-v1', status='PASS_PARTIAL_V94_BOUNDED_RANS',
                  baseline_commit='32940baf9007b7ed67f5b271c2a9856a5bc300d5',
                  evidence={str(p.relative_to(ROOT)): sha(p) for p in evidence},
                  scope='Inline byte-rANS host and symbol-kernel RTL checkpoint; full V94 remains partial.',
                  deferred=['tANS', 'calibration-only fixed tables', 'acknowledged model caches',
                            'complete mixed-method FPGA packet/literal/pixel/HUD/publication integration',
                            'routed timing/area and hardware 30fps/under10ms validation'],
                  physical_30fps_proven=False, validated_under10ms_proven=False, promoted=False,
                  source_frames=457, component_packets=native['actual_candidates']+opt_native['actual_candidates'],
                  complete_packets=len(rows)+len(opt_rows), coefficient_values=native['coefficient_values'],
                  policies=list(policies.values()), optimized_min_byte_delta_vs_V92=difference,
                  optimized_uniform_delta_vs_BR=policies['rate_ans2_s10']['wire_bytes']['total']-policies['all_BR']['wire_bytes']['total'],
                  rtl_symbols=rtl['total_symbols'], rtl_actual_corpus_symbols=rtl['actual_corpus_symbols'],
                  rtl_fast_cycles=rtl['fast_decode_cycles'], rtl_fast_symbols=rtl['fast_symbols'],
                  fast_variant_no_stall=fast['paired_no_stall_summary'],
                  fast_actual_context_no_stall=actual_comparison,
                  rtl_checker_negative_controls=3, protocol_checks=tests['checks_count'],
                  python_checks=python['checks_count'],
                  baseline_generation_ns=native['frame_generation_ns'], rate_generation_ns=opt_native['frame_generation_ns'])
    (AREA/'summary.json').write_text(json.dumps(output, indent=2)+'\n')
    lines = ['# V94 measured results', '',
             '**Partial V94: inline byte-rANS software and a real RTL category kernel pass. No product promotion.**', '',
             f'- 457 source frames; {output["component_packets"]:,} component packets and {output["complete_packets"]:,} complete CS94 reconstructions.',
             f'- {native["coefficient_values"]:,} intended coefficients retained; exact canonical/reference pixels, HUD, RGB565, roots and seals.',
             f'- {python["checks_count"]} independent Python grammar checks plus 4,608 native packets/all 256 selectors; {tests["checks_count"]} strict wire recovery checks.',
             '- Two full baseline campaigns reproduced all 12,339 packet bytes and per-packet operation metrics exactly.', '',
             '| Policy | Complete bytes | Max frame bytes | Fits 49,152 B | ANS categories | Inline tables |',
             '|---|---:|---:|---:|---:|---:|']
    for row in policies.values():
        lines.append(f'| {row["policy"]} | {row["wire_bytes"]["total"]:,} | {row["wire_bytes"]["max"]:,} | {row["fits_49152"]}/457 | {row["ans_symbols"]:,} | {row["model_tables"]:,} |')
    rate_delta = output['optimized_uniform_delta_vs_BR']
    lines += ['', '## Compression decision', '',
              'The initial six rANS variants use frozen BR-optimal Rice parameters and do not improve the minimum-byte frontier once inline models, descriptors and states are charged.',
              f'A separate bounded rate-aware parameter search evaluates {opt_native["totals"]["searched_ks"]:,} legal k candidates using normalized category entropy plus literal bits, then actually encodes the selected pair and keeps the frozen rANS stream if it is smaller. All search/discarded work is timed. This is not a proof of globally optimal rANS bitstreams.',
              f'Rate tuning saves **20,289 bytes** versus the frozen N2/S10 uniform rANS control. The guarded local minimum saves only **11 bytes across all 457 complete frames** versus V92: one 797-symbol chroma-DC context at cohort 0/frame 12 changes from a 228-byte AB stream to a 217-byte rANS stream. This is negligible compression benefit, not a reason to deploy another codec path.',
              f'The tuned uniform rANS control still uses **{rate_delta:+,} complete bytes** versus BR. Each homogeneous frame carries 21 inline models (672 bytes), plus 12 descriptors and initial state words. Table-free or cached estimates are not substituted for actual wire costs.',
              f'There is a tail-size tradeoff: tuned uniform rANS has a **{policies["rate_ans2_s10"]["wire_bytes"]["max"]:,}-byte maximum**, fitting all 457 sources; uniform BR reaches **{policies["all_BR"]["wire_bytes"]["max"]:,} bytes**, exceeding the cap on one source. The rANS mean-byte cost is {100*rate_delta/policies["all_BR"]["wire_bytes"]["total"]:.3f}% higher. This is a cap-management observation on this corpus, not a latency or general compression win.',
              'Keep the existing control. Cached-model, trained-model or tANS studies may change the tradeoff, but their protocols/costs are not implemented here. The corpus is one related precompressed walkthrough family, not independent raw captures or a generalization benchmark.', '',
              '## Actual RTL boundary and cycles', '',
              f'The repaired RTL passes **{rtl["total_symbols"]:,}** main-sweep category/state/cursor checks, including **{rtl["actual_corpus_symbols"]:,}** from actual contexts. This includes the optimized 797-symbol winner. Fifty-five vectors cover S=8/9/10, N=2/4, one/two models, empty/rare streams, 0/1/2 refills, two stall seeds and no-stall controls.',
              f'The no-stall sweep measures **{rtl["fast_decode_cycles"]:,} clocks for {rtl["fast_symbols"]:,} categories**, including refills. Every row satisfies `4×categories + refill bytes + input stalls + output stalls`; model/state preload is separately measured. One physical update engine serves the interleaved states.',
              'Independent math replay verifies all 67,673 vector categories. Three deliberately corrupted expected-category/state/cursor files fail the actual RTL checker. Eight malformed configuration/stream controls reject; three active cancellation retries and two same-edge configuration/reset races pass.',
              'Review exposed a same-edge cancellation handshake bug. The failing source/log/VCD are retained; the fix suppresses every ready/valid handshake and done while reset/abort is asserted. The complete regression, including the unchanged strengthened checker, passes afterward.',
              f'A separately compiled no-refill bypass variant preserves the entire RV94 workload and all {fast["total_symbols"]:,} main-sweep outputs. Matched no-stall clocks fall **{fast["paired_no_stall_summary"]["base_decode_cycles"]:,} → {fast["paired_no_stall_summary"]["fast_decode_cycles"]:,}**, saving **{fast["paired_no_stall_summary"]["saved_cycles"]:,} ({fast["paired_no_stall_summary"]["reduction_percent"]:.2f}%)**. Each case saves exactly its zero-refill-category count; nonzero-refill paths keep their service. All malformed/recovery/cancel tests and three corrupted-oracle controls also pass on the new binary.',
              f'The actual-source subset is **19 context encodings / 30,809 categories**, with clocks **{actual_base:,} → {actual_fast:,} ({actual_comparison["reduction_percent"]:.2f}% fewer)**. The remaining 36 vectors are synthetic; combining them yields the larger 21.67% figure. These context encodings cover a small selected workload, not sustained complete video frames.',
              'The bypass moves normalization detection onto the multiply/update path. Its routed clock may be lower; this is a cycle reduction at the component boundary, not an achieved-time or full-frame speedup. Keep the staged control until matched 7-series timing/resource results exist. Stalled-seed runs establish correctness only because their credit timing evolves with the changed clock count.',
              'Packet/table-ID/CRC parsing, literals, coefficients, pixels, HUD, physical memory/display and validated frame publication are outside the RTL kernel. Native complete-frame results do not execute that kernel. No complete-frame FPGA latency, routed clock, DSP mapping or hardware 30 fps is measured.', '',
              '## Host and resource accounting', '',
              f'Baseline candidate generation: median **{native["frame_generation_ns"]["median"]/1e6:.3f} ms**, p95 **{native["frame_generation_ns"]["p95"]/1e6:.3f} ms**, maximum **{native["frame_generation_ns"]["max"]/1e6:.3f} ms** per source on this Linux host. Rate-search campaign: median **{opt_native["frame_generation_ns"]["median"]/1e6:.3f} ms**, maximum **{opt_native["frame_generation_ns"]["max"]/1e6:.3f} ms**. These use different candidate sets and are not a matched host-speedup comparison.',
              'Generation includes source coefficient extraction, all prepared/discarded candidates, actual serialization/hashes and frozen encoder internal verification. Live capture/DCT and Sunshine/ESP32 operation are excluded. Native/Python RSS observations and independent verification wall time are in the retained reports.',
              'The kernel declares 704 model-payload bits and 128 lane-state bits, excluding control/multiply registers and the rest of the design. Its sixteen parallel comparisons have real read/fanout costs. Width feasibility for a DSP48E1 is not physical mapping or board fit.', '',
              '## Remaining V94 work', '',
              'V94a/b are qualified only for this inline byte-rANS scope. V94c remains a symbol-kernel checkpoint; tANS, fixed calibration-only models, acknowledged caches, complete frame RTL integration and physical cycle/port/resource qualification remain open. V94d is not promoted. V91l/V92d and hardware 30 fps/validated under-10-ms full decoding remain open.', '',
              '[Grammar/reproduction](README.md) · [RTL contract](../../fpga/experiments/cu66-v94-rans/README.md) · [Machine summary](../../experiments/python-gamebub-v94/summary.json)', '']
    (ROOT/'docs/cu66-v94/results.md').write_text('\n'.join(lines))
    print(output['status'], 'packets', output['complete_packets'], 'RTL symbols', output['rtl_symbols'], 'byte delta', difference)


if __name__ == '__main__':
    main()
