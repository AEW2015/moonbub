#!/usr/bin/env python3
"""Independent reconstruction audit for the V91b model and RTL evidence."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v91b'
VECTORS = AREA / 'context-vectors'
MODEL = AREA / 'results.json'
RTL_AREA = ROOT / 'fpga/experiments/cu66-v91b'
LIMITS = (1, 6, 21, 64)
ORDER = tuple(sorted(range(64), key=lambda n: (
    n // 8 + n % 8, n // 8 if (n // 8 + n % 8) % 2 else -(n // 8))))
MODEL_TOTAL_FIELDS = ('sources', 'chunks', 'coefficient_values', 'chunk_bytes',
                      'sparse_writes', 'held_samples', 'pending_high_water', 'contexts',
                      'zero_event_contexts', 'canonical_chunk_hash_matches')


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha(path):
    return sha_bytes(Path(path).read_bytes())


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest_object(value):
    return sha_bytes(json.dumps(value, separators=(',', ':')).encode())


def decode_sparse(row, rice_type):
    data = bytes.fromhex(row['data_hex'])
    assert len(data) == (row['bit_size'] + 7) // 8
    if row['bit_size'] % 8:
        assert data[-1] & ((1 << (8 - row['bit_size'] % 8)) - 1) == 0
    reader = rice_type(data, row['bit_size'])
    observed = []
    if row['band'] == 0:
        for block in range(row['event_count']):
            observed.append([block, 0, signed(reader.value(row['k0'], 14))])
    else:
        width = LIMITS[row['band']] - LIMITS[row['band'] - 1]
        position = -1
        for _ in range(row['event_count']):
            position += reader.value(row['k0'], 24) + 1
            assert position < row['blocks'] * width
            value = signed(reader.value(row['k1'], 12) + 1)
            assert value != 0 and -2048 <= value <= 2048
            block, local = divmod(position, width)
            observed.append([block, ORDER[LIMITS[row['band'] - 1] + local], value])
    reader.end()
    return observed


def signed(value):
    return -(value // 2) - 1 if value & 1 else value // 2


def packet_contexts(packet, blocks):
    """Extract packet context metadata after the frozen decoder validates it."""
    assert packet[:5] == b'BR88\x01' and packet[5] == 0
    assert struct.unpack_from('<IHH', packet, 6) == (blocks, 1, 0)
    lengths = struct.unpack_from('<4I', packet, 14)
    counts = struct.unpack_from('<3I', packet, 30)
    contexts, offset = [], 42
    for band, length in enumerate(lengths):
        k0, k1, bit_size = struct.unpack_from('<BBI', packet, offset)
        data = packet[offset + 6:offset + length]
        assert len(data) == (bit_size + 7) // 8
        contexts.append((k0, 255 if band == 0 else k1, bit_size, data,
                         blocks if band == 0 else counts[band - 1]))
        offset += length
    assert offset == len(packet) - 4
    return contexts, counts


def verify_vectors(entropy_data, frozen_codec):
    index = json.loads((VECTORS / 'index.json').read_text())
    vector_path = VECTORS / index['fixture']['path']
    raw = gzip.decompress(vector_path.read_bytes())
    assert sha(vector_path) == index['fixture']['gzip_sha256']
    assert sha_bytes(raw) == index['fixture']['jsonl_sha256']
    for relative, digest in index['source_sha256'].items():
        assert sha(ROOT / relative) == digest, relative
    rows = [json.loads(line) for line in raw.splitlines()]
    assert len(rows) == index['contexts'] == 55
    assert len({row['id'] for row in rows}) == len(rows)
    actual = [row for row in rows if row['case_type'] == 'actual']
    synthetic = [row for row in rows if row['case_type'] == 'synthetic']
    assert len(actual) == index['actual_contexts'] == 48
    assert len(synthetic) == index['synthetic_contexts'] == 7
    selection = {tuple(item) for item in index['selection']}
    seen_selected = set()
    actual_events_dc = actual_events_ac = 0
    decoded_by_source = {}
    for frame in entropy_data.iter_frames():
        identity = (frame['cohort'], frame['fid'])
        if identity not in selection:
            continue
        seen_selected.add(identity)
        for plane, chunks in enumerate(frame['variants']['65536']):
            for chunk_index, chunk in enumerate(chunks):
                coeffs = frozen_codec.decode(chunk['br88'], chunk['blocks'], 1)
                packed = struct.pack('<' + 'h' * len(coeffs), *coeffs)
                assert sha_bytes(packed) == chunk['coefficient_sha256']
                decoded_by_source[(identity[0], identity[1], plane, chunk_index)] = (chunk, coeffs)
    assert seen_selected == selection and len(decoded_by_source) == 12

    actual_map = {}
    for row in actual:
        source = row['source']
        assert row['expected_error'] == 0
        key = (source['cohort'], source['fid'], source['plane'], source['chunk'])
        assert key in decoded_by_source
        chunk, coeffs = decoded_by_source[key]
        contexts, _counts = packet_contexts(chunk['br88'], chunk['blocks'])
        band = row['band']
        k0, k1, bit_size, data, events = contexts[band]
        assert (row['blocks'], row['k0'], row['k1'], row['bit_size'],
                bytes.fromhex(row['data_hex']), row['event_count']) == (
                    chunk['blocks'], k0, k1, bit_size, data, events)
        assert row['coefficient_sha256'] == chunk['coefficient_sha256']
        expected = decode_sparse(row, frozen_codec.Rice)
        if band == 0:
            target = [[b, 0, coeffs[64 * b]] for b in range(chunk['blocks'])]
            actual_events_dc += events
        else:
            lo, hi = LIMITS[band - 1], LIMITS[band]
            target = [[b, ORDER[pos], coeffs[64 * b + ORDER[pos]]]
                      for b in range(chunk['blocks']) for pos in range(lo, hi)
                      if coeffs[64 * b + ORDER[pos]] != 0]
            actual_events_ac += events
        assert expected == row['expected'] == target
        assert len(expected) == events
        actual_map[(key, band)] = True
    assert len(actual_map) == 48
    assert actual_events_dc == index['actual_event_counts']['dc'] == 21177
    assert actual_events_ac == index['actual_event_counts']['ac_nonzero'] == 63075

    for row in synthetic:
        assert row['expected_error'] == 0
        assert decode_sparse(row, frozen_codec.Rice) == row['expected']
    assert sum(row['event_count'] for row in rows) == 84265
    assert sum(row['event_count'] == 0 for row in rows) == 3 + sum(
        row['event_count'] == 0 for row in actual)
    return dict(actual=len(actual), synthetic=len(synthetic),
                total_events=sum(row['event_count'] for row in rows),
                actual_dc_events=actual_events_dc, actual_ac_events=actual_events_ac,
                zero_event_contexts=sum(row['event_count'] == 0 for row in rows),
                gzip_sha256=sha(vector_path), jsonl_sha256=sha_bytes(raw))


def verify_model():
    public_path = AREA / 'results.json'
    public = json.loads(public_path.read_text())
    result_path = ROOT / public['selected_report']
    result = json.loads(result_path.read_text())
    attempt = result_path.parent
    assert result['schema'] == public['schema'] == 'cu66-v91b-context-model-v1'
    assert result['status'] == public['status'] == 'PASS_FULL_CORPUS_SPARSE_CONTEXT_MODEL'
    assert {key: value for key, value in public.items() if key != 'selected_report'} == result
    assert result['directed_all_passed'] and result['directed_checks'] == 99
    assert result['physical_30fps_proven'] is False
    assert result['complete_under10ms_proven'] is False
    assert 'Packet CRC is software-prevalidated, not RTL' in result['scope']

    snapshot_pins = 0
    for relative, digest in result['source_sha256'].items():
        assert sha(ROOT / relative) == digest, relative
        snapshot = attempt / 'sources' / relative
        if snapshot.exists():
            assert sha(snapshot) == digest, relative
            snapshot_pins += 1
    for relative, digest in result['artifacts_sha256'].items():
        assert sha(attempt / relative) == digest, relative
    directed = json.loads((attempt / 'directed.json').read_text())
    assert len(directed) == result['directed_checks']
    assert all(row['status'] == 'PASS' for row in directed)
    chunks_path = attempt / 'chunks.jsonl'
    chunk_rows = [json.loads(line) for line in chunks_path.read_text().splitlines()]
    assert len(chunk_rows) == 1371
    assert sha(chunks_path) == result['artifacts_sha256']['chunks.jsonl']

    entropy_dir = ROOT / 'experiments/python-gamebub-v88/entropy'
    entropy_data = load('v91b_audit_data', entropy_dir / 'data.py')
    frozen_codec = load('v91b_audit_codec', entropy_dir / 'codec.py')
    vector_audit = verify_vectors(entropy_data, frozen_codec)

    # Rebuild each row from the pinned original residual corpus, not from the
    # model's summaries. Frozen V88 decode also rechecks the canonical hash.
    observed_rows = {}
    identities = set()
    sums = dict(sources=0, chunks=0, coefficient_values=0, chunk_bytes=0,
                sparse_writes=0, held_samples=0, pending_high_water=0,
                contexts=0, zero_event_contexts=0, canonical_chunk_hash_matches=0)
    by_source = {}
    for frame in entropy_data.iter_frames():
        identity = (frame['cohort'], frame['fid'])
        assert identity not in identities
        identities.add(identity)
        sums['sources'] += 1
        for plane, plane_chunks in enumerate(frame['variants']['65536']):
            for chunk_index, chunk in enumerate(plane_chunks):
                packet, blocks = chunk['br88'], chunk['blocks']
                coefficients = frozen_codec.decode(packet, blocks, 1)
                coefficient_bytes = struct.pack('<' + 'h' * len(coefficients), *coefficients)
                coefficient_sha = sha_bytes(coefficient_bytes)
                assert coefficient_sha == chunk['coefficient_sha256']
                contexts, counts = packet_contexts(packet, blocks)
                event_total = blocks + sum(counts)
                zero_events = sum(count == 0 for count in counts)
                key = (identity[0], identity[1], frame['ordinal'], plane, chunk_index)
                expected = dict(cohort=identity[0], fid=identity[1], ordinal=frame['ordinal'],
                    plane=plane, chunk=chunk_index, blocks=blocks, bytes=len(packet),
                    packet_sha256=sha_bytes(packet), coefficient_values=len(coefficients),
                    coefficient_sha256=coefficient_sha, contexts=4,
                    zero_event_contexts=zero_events, matches_frozen=True)
                assert key not in observed_rows
                observed_rows[key] = expected
                by_source[key] = (packet, blocks, event_total, zero_events)
                sums['chunks'] += 1
                sums['coefficient_values'] += len(coefficients)
                sums['chunk_bytes'] += len(packet)
                sums['sparse_writes'] += event_total
                sums['contexts'] += 4
                sums['zero_event_contexts'] += zero_events
                sums['canonical_chunk_hash_matches'] += 1
    assert sums['sources'] == 457 and sums['chunks'] == 1371

    seen = set()
    for row in chunk_rows:
        key = (row['cohort'], row['fid'], row['ordinal'], row['plane'], row['chunk'])
        assert key in observed_rows and key not in seen
        seen.add(key)
        expected = observed_rows[key]
        for field, value in expected.items():
            assert row[field] == value, (key, field, row[field], value)
        ready, stalled = row['ready'], row['stalled']
        event_total = by_source[key][2]
        assert ready['writes'] == stalled['writes'] == event_total
        assert ready['held_samples'] == 0
        assert stalled['pending_high_water'] == int(event_total != 0)
        assert stalled['held_samples'] <= 7 * event_total
        assert ready['scratch_int16_values'] == stalled['scratch_int16_values'] == row['blocks'] * 64
        assert ready['raw'] is False and stalled['raw'] is False
        sums['held_samples'] += stalled['held_samples']
        sums['pending_high_water'] = max(sums['pending_high_water'], stalled['pending_high_water'])
    assert seen == set(observed_rows)

    assert sums['coefficient_values'] == 86444480
    assert sums['chunk_bytes'] == 4805106
    assert sums['sparse_writes'] == 6393038
    assert sums['contexts'] == 5484
    assert sums['zero_event_contexts'] == 909
    assert sums['held_samples'] == 22359009
    assert sums['pending_high_water'] == 1
    assert sums == {field: result['totals'][field] for field in MODEL_TOTAL_FIELDS}
    return dict(public_path=str(public_path.relative_to(ROOT)), selected_report=str(result_path.relative_to(ROOT)),
        selected_attempt=attempt.name, status=result['status'], result_sha256=sha(result_path),
        public_result_sha256=sha(public_path), source_pins_checked=len(result['source_sha256']),
        snapshot_pins_checked=snapshot_pins, artifact_pins_checked=len(result['artifacts_sha256']),
        chunk_rows=len(chunk_rows), reconstructed_totals=sums, vector_audit=vector_audit)


def verify_packet_checks():
    summary_path = AREA / 'packet-checks.json'
    summary = json.loads(summary_path.read_text())
    details_path = ROOT / summary['details_path']
    assert summary['schema'] == 'cu66-v91b-independent-packet-checks-v1'
    assert summary['status'] == 'PASS' and summary['seed'] == 911091
    assert summary['cases'] == 3209
    assert summary['accepted'] == 21 and summary['rejected'] == 3188
    assert summary['late_failure_after_provisional_DC_abort_checked'] is True
    assert sha(details_path) == summary['details_sha256']
    for relative, digest in summary['source_sha256'].items():
        assert sha(ROOT / relative) == digest, relative
    rows = [json.loads(line) for line in details_path.read_text().splitlines()]
    assert len(rows) == summary['cases']
    assert sum(row['outcome'] == 'accept' for row in rows) == summary['accepted']
    assert sum(row['outcome'] == 'reject' for row in rows) == summary['rejected']
    assert all(row['outcome'] in ('accept', 'reject') for row in rows)
    assert sum(row['name'] == 'valid_fixture' and row['outcome'] == 'accept' for row in rows) == 1
    return dict(status=summary['status'], cases=len(rows), accepted=summary['accepted'],
                rejected=summary['rejected'], details_sha256=sha(details_path),
                source_pins_checked=len(summary['source_sha256']),
                late_failure_after_provisional_DC_abort_checked=True)


def simulation_text(cases):
    lines = []
    for case in cases:
        expected = case['expected']
        lines.append(' '.join(map(str, (case['id'], case['blocks'], case['band'], case['k0'],
            case['k1'], case['event_count'], case['bit_size'], case['data_hex'] or '-',
            case.get('expected_error', 0), len(expected)))) + '\n')
        lines.extend(' '.join(map(str, coef)) + '\n' for coef in expected)
    return ''.join(lines).encode()


def audit_rtl_attempt(result_path, expected_seed, vector_rows):
    result = json.loads(result_path.read_text())
    attempt = result_path.parent
    assert result['schema'] == 'cu66-v91b-context-rtl-v1'
    assert result['status'] == 'PASS_CONTEXT_SIMULATION'
    assert result['seed'] == expected_seed
    assert result['verdict']['status'] == 'TEST_PASS'
    assert result['verdict']['seed'] == expected_seed
    assert result['verdict']['directed_checks'] == 172
    assert result['verdict']['cases'] == len(vector_rows) == 55
    assert result['verdict']['outputs_per_configuration'] == 84265
    assert result['verdict']['configurations'] == 8
    assert result['vector_cases'] == 55 and result['vector_requests'] == 84265
    assert result['actual_contexts'] == 48
    assert result['scope'].startswith('One BR88 context/band sparse adapter simulation only;')
    assert 'through final coefficient acceptance' in result['fence']
    assert result['vectors_sha256'] == sha(VECTORS / 'contexts.jsonl.gz')
    assert result['vector_index_sha256'] == sha(VECTORS / 'index.json')
    for relative, digest in result['source_sha256'].items():
        assert sha(ROOT / relative) == digest, relative
        assert sha(attempt / 'sources' / relative) == digest, relative
    for relative, digest in result['artifacts_sha256'].items():
        assert sha(attempt / relative) == digest, relative
    assert sha(attempt / 'cases.jsonl.gz') == result['vectors_sha256']
    assert sha(attempt / 'index.json') == result['vector_index_sha256']
    assert all(command['exit_code'] == 0 for command in result['commands'])
    build = next(command for command in result['commands']
                 if 'verilator' in command['argv'] and '--build' in command['argv'])
    argv = build['argv']
    assert '--assert' in argv and '-Wall' in argv and '-j' in argv and '-Werror' in argv[argv.index('-CFLAGS') + 1]
    compile_log = (attempt / 'compile.log').read_text()
    assert '%Warning' not in compile_log and '%Error' not in compile_log
    assert 'warning:' not in compile_log.lower() and 'error:' not in compile_log.lower()
    assert sha_bytes(simulation_text(vector_rows)) == result['text_vectors_sha256']

    sim_rows = [json.loads(line) for line in (attempt / 'simulation.jsonl').read_text().splitlines()]
    case_rows = [row for row in sim_rows if row['type'] == 'case']
    total_rows = [row for row in sim_rows if row['type'] == 'total']
    verdict_rows = [row for row in sim_rows if row['type'] == 'verdict']
    assert len(case_rows) == len(vector_rows) * 8
    assert len(total_rows) == 8 and verdict_rows == [result['verdict']]
    configs = [(serial, width, stalls) for stalls in (0, 1)
               for width in (32, 16) for serial in (0, 1)]
    expected_order = [(case['id'], serial, width, stalls)
                      for case in vector_rows for stalls in (0, 1)
                      for width in (32, 16) for serial in (0, 1)]
    assert [(row['id'], row['serial'], row['word_bits'], row['stalls']) for row in case_rows] == expected_order
    fields = ('cycles', 'input_accepted', 'symbols', 'consumed_bits', 'outputs', 'input_wait', 'output_stall')
    grouped = {}
    aggregate_by_config = {}
    for row in case_rows:
        assert row['outputs'] == len(next(case for case in vector_rows if case['id'] == row['id'])['expected'])
        assert row['cycles'] >= row['outputs'] and row['input_accepted'] >= 0
        population = 'actual' if row['id'].startswith('actual:') else 'synthetic'
        keys = [(population, row['word_bits'], int(row['serial']), int(row['stalls']))]
        if population == 'actual':
            keys.append((':'.join(row['id'].split(':')[:3]), row['word_bits'], int(row['serial']), int(row['stalls'])))
        for key in keys:
            value = grouped.setdefault(key, dict(streams=0, **{field: 0 for field in fields}))
            value['streams'] += 1
            for field in fields:
                value[field] += row[field]
        key = (row['serial'], row['word_bits'], row['stalls'])
        value = aggregate_by_config.setdefault(key, {field: 0 for field in fields})
        for field in fields:
            value[field] += row[field]
    assert len(grouped) == 48
    assert {(row['serial'], row['word_bits'], row['stalls']) for row in total_rows} == set(configs)
    for total in total_rows:
        assert {field: total[field] for field in fields} == aggregate_by_config[
            (total['serial'], total['word_bits'], total['stalls'])]
        assert total['outputs'] == 84265 and total['symbols'] == 147348
        assert total['consumed_bits'] == 518255
    assert len(result['population_totals']) == len(grouped)
    for item in result['population_totals']:
        key = (item['population'], item['word_bits'], int(item['serial']), int(item['stalls']))
        assert item['streams'] == grouped[key]['streams']
        assert {field: item[field] for field in fields} == {field: grouped[key][field] for field in fields}
    comparisons = {(row['population'], row['word_bits'], row['stalls']): row
                   for row in result['population_comparisons']}
    populations = sorted({key[0] for key in grouped})
    assert len(comparisons) == len(populations) * 4
    for population in populations:
        for width in (16, 32):
            for stalls in (0, 1):
                fast, serial = grouped[(population, width, 0, stalls)], grouped[(population, width, 1, stalls)]
                reported = comparisons[(population, width, stalls)]
                assert reported['fast_cycles'] == fast['cycles']
                assert reported['serial_cycles'] == serial['cycles']
                assert reported['serial_over_fast'] == serial['cycles'] / fast['cycles']
                for field in ('input_accepted', 'symbols', 'consumed_bits', 'outputs'):
                    assert fast[field] == serial[field]
    return dict(path=str(result_path.relative_to(ROOT)), attempt=attempt.name,
        seed=expected_seed, result_sha256=sha(result_path), source_pins_checked=len(result['source_sha256']),
        artifact_pins_checked=len(result['artifacts_sha256']), case_rows=len(case_rows),
        configurations=len(total_rows), directed_checks=result['verdict']['directed_checks'],
        compile=dict(exit_code=0, command_has_assert=True, command_has_wall=True,
                     command_has_werror=True, warning_free=True),
        reconstructed_totals=[dict(serial=serial, word_bits=width, stalls=stalls, **totals)
            for (serial, width, stalls), totals in sorted(aggregate_by_config.items(),
                key=lambda item: (int(item[0][2]), item[0][1], int(item[0][0])))],
        actual_cycles_32_ready=dict(fast=grouped[('actual', 32, 0, 0)]['cycles'],
                                     serial=grouped[('actual', 32, 1, 0)]['cycles']),
        actual_cycles_32_stalled=dict(fast=grouped[('actual', 32, 0, 1)]['cycles'],
                                       serial=grouped[('actual', 32, 1, 1)]['cycles']))


def verify_rtl(vector_rows):
    public_path = RTL_AREA / 'results.json'
    assert public_path.exists()
    public = json.loads(public_path.read_text())
    result_path = ROOT / public['selected_report']
    result = json.loads(result_path.read_text())
    assert public['status'] == result['status'] == 'PASS_CONTEXT_SIMULATION'
    assert {key: value for key, value in public.items() if key != 'selected_report'} == result
    assert result['seed'] == 910133
    selected = audit_rtl_attempt(result_path, 910133, vector_rows)
    prior_paths = [RTL_AREA / 'attempts/20261106T171846357743Z-30de16b2/results.json']
    prior = [audit_rtl_attempt(path, 910132, vector_rows) for path in prior_paths]
    assert json.loads(prior_paths[0].read_text())['source_sha256'] == result['source_sha256']
    assert json.loads(prior_paths[0].read_text())['vectors_sha256'] == result['vectors_sha256']
    return dict(status='PASS', audited=True, selected=selected, repeated_seed_runs=prior)


def audit():
    model = verify_model()
    packet = verify_packet_checks()
    index = json.loads((VECTORS / 'index.json').read_text())
    vector_rows = [json.loads(line) for line in gzip.open(VECTORS / index['fixture']['path'], 'rt')]
    rtl = verify_rtl(vector_rows)
    return dict(schema='cu66-v91b-independent-audit-v1', status='PASS',
                model=model, rtl=rtl,
                packet_checks=packet,
                scope='Independent frozen-corpus reconstruction and context-vector audit; functional model stalls are samples, not clock cycles. FPGA timing and full frame decoding are not established.')


if __name__ == '__main__':
    report = audit()
    (AREA / 'audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(report['status'], report['model']['chunk_rows'], report['model']['reconstructed_totals']['sparse_writes'])
