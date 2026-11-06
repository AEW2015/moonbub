#!/usr/bin/env python3
"""Independent read-only audit for the selected V91 RTL result and harness."""
import gzip
import hashlib
import json
from pathlib import Path
import re
import statistics

ROOT = Path(__file__).resolve().parents[3]
AREA = ROOT / 'fpga/experiments/cu66-v91'
VECTOR_INDEX = ROOT / 'experiments/python-gamebub-v91/rtl-vectors/index.json'
VECTOR_FILE = ROOT / 'experiments/python-gamebub-v91/rtl-vectors/cases.jsonl.gz'
FIELDS = ('cycles', 'input_accepted', 'symbols', 'consumed_bits', 'input_wait', 'output_stall')
CONFIGS = [(serial, word_bits, stalls) for stalls in (0, 1)
           for word_bits in (32, 16) for serial in (0, 1)]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def totals_for(rows):
    return {field: sum(row[field] for row in rows) for field in FIELDS}


def dist(values):
    values = sorted(values)
    return dict(count=len(values), min=min(values), median=statistics.median(values),
                p95=values[min(len(values)-1, int(.95*len(values)))],
                p99=values[min(len(values)-1, int(.99*len(values)))],
                max=max(values), total=sum(values))


def vector_text(cases):
    lines = []
    for case in cases:
        lines.append(f"{case['id']} {case['bit_size']} {case['data_hex'] or '-'} {len(case['requests'])}\n")
        lines.extend(' '.join(map(str, request)) + '\n' for request in case['requests'])
    return ''.join(lines).encode()


def audit():
    public_path = AREA / 'results.json'
    public = json.loads(public_path.read_text())
    result_path = ROOT / public['selected_report']
    result = json.loads(result_path.read_text())
    attempt = result_path.parent
    assert result['status'] == public['status'] == 'PASS_COMPONENT_SIMULATION'
    assert {k: v for k, v in public.items() if k != 'selected_report'} == result
    assert result['seed'] == result['verdict']['seed'] == 910033

    # Current inputs, source snapshots, vectors, and every recorded attempt
    # artifact must match their recorded digests.
    for relative, digest in result['source_sha256'].items():
        assert sha(ROOT / relative) == digest, relative
        assert sha(attempt / 'sources' / relative) == digest, relative
    assert sha(VECTOR_FILE) == result['vectors_sha256']
    assert sha(attempt / 'cases.jsonl.gz') == result['vectors_sha256']
    for relative, digest in result['artifacts_sha256'].items():
        assert sha(attempt / relative) == digest, relative
    assert all(command['exit_code'] == 0 for command in result['commands'])
    compile_argv = next(command['argv'] for command in result['commands']
                        if 'verilator' in command['argv'] and '--build' in command['argv'])
    assert '-Wall' in compile_argv and '--assert' in compile_argv and '-j' in compile_argv
    compile_log = (attempt / 'compile.log').read_text()
    assert not re.search(r'%Warning|%Error|\bwarning:|\berror:', compile_log, re.I)

    # Verify the vector export's own fixture digest and generator/source pins.
    index = json.loads(VECTOR_INDEX.read_text())
    assert sha(VECTOR_FILE) == index['fixture']['gzip_sha256']
    for relative, digest in index['source_sha256'].items():
        assert sha(ROOT / relative) == digest, relative
    cases = [json.loads(line) for line in gzip.open(VECTOR_FILE, 'rt')]
    raw_vectors = gzip.decompress(VECTOR_FILE.read_bytes())
    assert hashlib.sha256(raw_vectors).hexdigest() == index['fixture']['jsonl_sha256']
    assert hashlib.sha256(vector_text(cases)).hexdigest() == result['text_vectors_sha256']
    actual = [case for case in cases if case['id'].startswith('actual:')]
    synthetic = [case for case in cases if case['id'].startswith('synthetic:')]
    assert len(actual) == index['actual_cases'] == 48
    assert len(synthetic) == index['synthetic_cases'] == 1472
    assert len(cases) == index['cases'] == result['vector_cases'] == 1520
    expected_sources = {f"actual:c{cohort}:f{fid}" for cohort, fid in index['selection']}
    actual_sources = {':'.join(case['id'].split(':')[:3]) for case in actual}
    assert actual_sources == expected_sources
    request_count = sum(len(case['requests']) for case in cases)
    assert request_count == index['requests'] == result['vector_requests'] == 173061
    actual_requests = sum(len(case['requests']) for case in actual)
    synthetic_requests = sum(len(case['requests']) for case in synthetic)
    assert (actual_requests, synthetic_requests) == (147327, 25734)
    assert sum(case['bit_size'] for case in actual) == 517981
    assert sum(case['bit_size'] for case in synthetic) == 425888
    assert sum(case['bit_size'] for case in cases) == index['coded_bits'] == 943869

    # Reconstruct every aggregate from simulation case rows; no producer
    # summary is trusted as the source for these sums.
    simulation = [json.loads(line) for line in (attempt / 'simulation.jsonl').read_text().splitlines()]
    cases_run = [row for row in simulation if row['type'] == 'case']
    total_rows = [row for row in simulation if row['type'] == 'total']
    verdicts = [row for row in simulation if row['type'] == 'verdict']
    assert len(cases_run) == len(cases) * 8 == 12160
    assert len(total_rows) == len(CONFIGS) == 8 and len(verdicts) == 1
    assert {(row['serial'], row['word_bits'], row['stalls']) for row in total_rows} == set(CONFIGS)
    assert verdicts[0] == result['verdict']
    assert verdicts[0]['status'] == 'TEST_PASS' and verdicts[0]['directed_checks'] == 104
    vector_ids = [case['id'] for case in cases]
    assert len(set(vector_ids)) == len(vector_ids)
    assert [(row['id'], row['serial'], row['word_bits'], row['stalls']) for row in cases_run] == [
        (case['id'], serial, width, stalls)
        for case in cases for stalls in (0, 1) for width in (32, 16) for serial in (0, 1)]

    grouped, per_source = {}, {}
    for row in cases_run:
        population = 'actual' if row['id'].startswith('actual:') else 'synthetic'
        groups = [(population, row['word_bits'], row['serial'], row['stalls'])]
        if population == 'actual':
            source = ':'.join(row['id'].split(':')[:3])
            groups.append((source, row['word_bits'], row['serial'], row['stalls']))
        for key in groups:
            target = grouped.setdefault(key, dict(streams=0, **{field: 0 for field in FIELDS}))
            target['streams'] += 1
            for field in FIELDS:
                target[field] += row[field]
    assert len(grouped) == 48  # actual, synthetic, and four individual actual sources × configs
    for total in total_rows:
        key = ('all', total['word_bits'], int(total['serial']), int(total['stalls']))
        matched = [row for row in cases_run if
                   (row['word_bits'], int(row['serial']), int(row['stalls'])) == key[1:]]
        assert totals_for(matched) == {field: total[field] for field in FIELDS}
        assert total['symbols'] == 173061 and total['consumed_bits'] == 943869

    # Compare the runner's population/source tables to independently rebuilt
    # sums, then calculate actual, synthetic-only, and mixed gains distinctly.
    for item in result['population_totals']:
        key = (item['population'], item['word_bits'], int(item['serial']), int(item['stalls']))
        expected = grouped[key]
        assert item['streams'] == expected['streams']
        assert {field: item[field] for field in FIELDS} == {field: expected[field] for field in FIELDS}
    assert len(result['population_totals']) == len(grouped)

    reported_population_ratios = {
        (item['population'], item['word_bits'], item['stalls']): item
        for item in result['population_comparisons']
    }
    assert len(reported_population_ratios) == len(grouped) // 2
    for population in sorted({key[0] for key in grouped}):
        for width in (16, 32):
            for stalls in (0, 1):
                fast = grouped[(population, width, 0, stalls)]
                serial = grouped[(population, width, 1, stalls)]
                item = reported_population_ratios[(population, width, stalls)]
                assert item['fast_cycles'] == fast['cycles']
                assert item['serial_cycles'] == serial['cycles']
                assert item['serial_over_fast'] == serial['cycles'] / fast['cycles']
                for field in ('input_accepted', 'symbols', 'consumed_bits'):
                    assert fast[field] == serial[field]

    def ratio(pop, width, stalls):
        fast = grouped[(pop, width, 0, stalls)]['cycles']
        serial = grouped[(pop, width, 1, stalls)]['cycles']
        return serial / fast

    actual_gain = ratio('actual', 32, 0)
    synthetic_gain = ratio('synthetic', 32, 0)
    mixed_gain = next(row['serial_over_fast'] for row in result['comparisons']
                      if row['word_bits'] == 32 and row['stalls'] == 0)
    assert round(actual_gain, 2) == 1.41
    assert round(mixed_gain, 2) == 1.87
    # Synthetic-only vectors have a larger gain than the mixed aggregate.
    assert synthetic_gain > mixed_gain

    # Reconstruct source/readiness random scheduling from source: exactly three
    # xorshift draws per active cycle; seed is independent of parser mode.
    tb = (AREA / 'tb_rice.cpp').read_text()
    rtl = (AREA / 'br88_rice_elastic.sv').read_text()
    runner = (ROOT / 'scripts/cu66-v91/run_rtl.py').read_text()
    assert 'rng=1469598103934665603ULL' in tb
    assert 'rng^=base_seed^(word16?0x16161616ULL:0x32323232ULL)' in tb
    assert 'const bool offer_word=random()%4!=0,offer_request=random()%4!=0,accept_output=random()%4!=0;' in tb
    assert 'while (completed<c.requests.size())' in tb
    assert 'if (!pending_word && loaded<c.bits && (!stalls || offer_word))' in tb
    assert 'if (!pending_request && accepted<c.requests.size() && (!stalls || offer_request))' in tb
    assert 'd.out_ready=!stalls || accept_output;' in tb
    assert 'if (held && !d.reset && !d.stream_start)' in tb
    assert 'held output payload changed' in tb and 'held output valid dropped' in tb
    assert 'd.count_cycles==cycles' in tb and '++completed' in tb
    assert 'count_cycles<=count_cycles+1\'b1' in rtl
    assert 'if (out_valid && out_ready)' in rtl
    assert 'fence="stream_start edge excluded; every subsequent rising edge through final response delivery included"' in runner
    assert "totals['cycles']" not in runner  # no alternate report-only cycle source

    directed_contract = {
        'bad_request_widths': all(token in tb for token in ('request(20,24)', 'request(31,24)', 'request(0,25)', 'request(0,31)')),
        'short_empty_and_truncated_prefix_suffix': all(token in tb for token in ('start(0,word16,serial)', 'start(7,word16,serial)', 'start(3,word16,serial)')),
        'bad_source_words_and_sticky_errors': 'for (unsigned kind=0;kind<6;++kind)' in tb and 'response(3,0,0)' in tb,
        'reset_and_restart_abort_pending_or_held': all(token in tb for token in ('Restart aborts a pending request', 'Reset aborts a pending request', 'discard a held response')),
        'maximum_39_bit_literal': 'directed:max39' in tb and '0xffffff,39' in tb,
        'final_response_delivery_in_cycle_fence': 'if (e.response)' in tb and '++completed;' in tb and 'count_cycles<=count_cycles+1\'b1' in rtl,
    }
    assert all(directed_contract.values())
    assert result['fence'] == 'stream_start edge excluded; every subsequent rising edge through final response delivery included'
    assert 'not whole packet CRC/scatter/decoder or routed hardware timing' in result['scope']

    return dict(schema='cu66-v91-independent-rtl-audit-v1', status='PASS',
                result_path=str(result_path.relative_to(ROOT)),
                selected_attempt=result_path.parent.name, seed=result['seed'],
                result_sha256=sha(result_path), public_result_sha256=sha(public_path),
                vectors_sha256=result['vectors_sha256'],
                source_pins_checked=len(result['source_sha256']),
                vector_source_pins_checked=len(index['source_sha256']),
                attempt_artifacts_checked=len(result['artifacts_sha256']),
                compile=dict(exit_code=0, verilator_wall_clean=True,
                             command_has_assert=True, command_has_wall=True,
                             tool_version=(attempt/'tool-version.log').read_text().strip(),
                             compiler_version=(attempt/'compiler-version.log').read_text().splitlines()[0]),
                vector_split=dict(actual_cases=len(actual), actual_requests=actual_requests,
                                  actual_coded_bits=517981, synthetic_cases=len(synthetic),
                                  synthetic_requests=synthetic_requests, synthetic_coded_bits=425888,
                                  combined_cases=len(cases), combined_requests=request_count),
                simulation=dict(case_rows=len(cases_run), configurations=8, requests_per_configuration=173061,
                                directed_checks=104, totals_reconstructed=True,
                                source_groups_checked=4),
                population_sums={population: {
                    f'{width}bit_stalls{stalls}': {
                        'streams': grouped[(population, width, 0, stalls)]['streams'],
                        'fast_cycles': grouped[(population, width, 0, stalls)]['cycles'],
                        'serial_cycles': grouped[(population, width, 1, stalls)]['cycles'],
                        'input_accepted': grouped[(population, width, 0, stalls)]['input_accepted'],
                        'symbols': grouped[(population, width, 0, stalls)]['symbols'],
                        'consumed_bits': grouped[(population, width, 0, stalls)]['consumed_bits'],
                        'input_wait_fast': grouped[(population, width, 0, stalls)]['input_wait'],
                        'input_wait_serial': grouped[(population, width, 1, stalls)]['input_wait'],
                        'output_stall_fast': grouped[(population, width, 0, stalls)]['output_stall'],
                        'output_stall_serial': grouped[(population, width, 1, stalls)]['output_stall'],
                    }
                    for width in (16, 32) for stalls in (0, 1)
                } for population in sorted({key[0] for key in grouped})},
                gains=dict(actual_32bit_no_stall_serial_over_fast=actual_gain,
                           synthetic_only_32bit_no_stall_serial_over_fast=synthetic_gain,
                           mixed_all_vectors_32bit_no_stall_serial_over_fast=mixed_gain,
                           note='Synthetic-only and mixed-corpus gains are reported separately from actual-source gain.'),
                directed_contract=directed_contract,
                held_payload_and_trace_schedule='Source contract checked: stable held output payload; three deterministic per-cycle draws; same seed per case and word width across parser modes; producers hold payload until acceptance.',
                fence=result['fence'],
                scope='Behavioral RTL component audit; no frame, packet decoder, synthesis, routed timing, or hardware claim.')


if __name__ == '__main__':
    report = audit()
    (AREA / 'independent-audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print('PASS', report['vector_split']['actual_cases'], report['vector_split']['synthetic_cases'], report['simulation']['case_rows'])
