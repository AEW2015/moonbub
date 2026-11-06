"""Counter reconciliation and analysis of clocked V91f receipts."""
import gzip
import hashlib
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v91f'
CONTRACT_PATH = AREA / 'telemetry-contract.json'
LEGACY_FIELDS = ('cycles', 'input_bytes', 'dense_coefficients', 'read_requests', 'write_requests',
                 'output_stalls', 'metadata_wait', 'memory_pending_edges', 'used_bytes')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def cases():
    return [json.loads(line) for line in gzip.open(ROOT / 'experiments/python-gamebub-v91e/vectors/coefficients.jsonl.gz', 'rt')]


def config_key(row):
    return row['id'], row['memory_profile'], row['write_overlap']


def validate_rows(rows, vector_rows):
    contract = read(CONTRACT_PATH)
    records = [row for row in rows if row['type'] == 'case']
    by_id = {row['id']: row for row in vector_rows}
    assert len(records) == len(by_id) * 4
    assert {config_key(row) for row in records} == {(identity, profile, clear) for identity in by_id for profile in (0, 1) for clear in (0, 1)}
    for row in records:
        golden = by_id[row['id']]
        o = row['observability']
        p, s = o['packet_state_cycles'], o['scratch_state_cycles']
        e, ts = o['overlapping_edges'], o['timestamps']
        assert len(p) == 16 and len(s) == 32
        assert sum(p) == sum(s) == row['cycles']
        assert e['memory_pending'] == row['memory_pending_edges']
        if not row['write_overlap']:
            assert s[9] + s[11] == e['memory_pending']
            assert s[8] + s[10] == row['read_requests'] + row['write_requests'] + e['memory_request_stall']
        assert s[20] + s[22] == row['dense_coefficients'] + e['dense_stall']
        assert e['dense_stall'] == row['output_stalls'] and e['metadata_wait'] == row['metadata_wait']
        assert p[1] == row['input_bytes'] + e['input_starved']
        assert ts['integrated_done'] == row['cycles'] == ts['last_dense'] + 1
        ordered = [ts[key] for key in ('first_input', 'last_input', 'metadata_accept', 'last_sparse_coef',
                   'packet_done_observed', 'seal_accepted', 'scratch_sealed_observed', 'first_dense', 'last_dense', 'integrated_done')]
        assert ordered[0] >= 1 and ordered == sorted(ordered)
        expected = [golden['blocks'] * 64, 0, 0, 0] if golden['raw'] else [golden['blocks'], *golden['counts']]
        assert o['coefficient_handshakes_by_band'] == expected
        assert o['band_end_handshakes_by_band'] == ([1, 0, 0, 0] if golden['raw'] else [1, 1, 1, 1])
        for band, count in enumerate(expected):
            first, last, end = o['first_coefficient_by_band'][band], o['last_coefficient_by_band'][band], o['band_end_by_band'][band]
            assert bool(first) == bool(last) == bool(count)
            if count:
                assert ts['metadata_accept'] < first <= last < end <= ts['packet_done_observed']
            elif not golden['raw']:
                assert end > 0
        for field, bound in contract['highwater_bounds'].items():
            assert 0 <= o['highwaters'][field] <= bound
        assert row['dense_coefficients'] == golden['blocks'] * 64
        assert row['read_requests'] == row['write_requests'] == golden['used_bytes'] // 16
        assert row['input_bytes'] == len(bytes.fromhex(golden['packet_hex']))
        assert sum(s[index] for index in (24, 25, 27, 28, 29, 30, 31)) == 0
    keyed = {config_key(row): row for row in records}
    for identity in by_id:
        for profile in (0, 1):
            a, b = keyed[(identity, profile, 0)], keyed[(identity, profile, 1)]
            assert a['request_service_hash'] == b['request_service_hash']
            assert a['memory_pending_edges'] == b['memory_pending_edges']
        for profile in (0, 1):
            on = keyed[(identity, profile, 1)]
            assert on['serial_clear'] == 0
            counters = on['observability']['write_overlap_counters']
            assert counters['physical_accepts'] == counters['physical_acks'] == on['write_requests'] - 2
            assert counters['enqueues'] == on['write_requests'] - 2
    return records


def compare_v91e(records, seed):
    audit_path = ROOT / 'experiments/python-gamebub-v91e/audit.json'
    audit = read(audit_path)
    control = next(item for item in audit['integrated_rtl']['selected_seeds'] if item['verdict']['seed'] == seed)
    path = ROOT / 'fpga/experiments/cu66-v91e/pipeline-attempts' / control['attempt'] / 'results.json'
    assert sha(path) == control['result_sha256']
    old = [json.loads(line) for line in path.with_name('simulation.jsonl').read_text().splitlines()]
    old_rows = {(r['id'], r['memory_profile']): r for r in old if r['type'] == 'case' and r['serial_clear'] == 0}
    new_rows = {(r['id'], r['memory_profile']): r for r in records if r['write_overlap'] == 0}
    assert len(old_rows) == 40 and old_rows.keys() == new_rows.keys()
    for key, before in old_rows.items():
        assert all(before[field] == new_rows[key][field] for field in LEGACY_FIELDS), key
    return dict(status='PASS_EXACT_FROZEN_V91E_MASK_METRICS', baseline_report=str(path.relative_to(ROOT)),
                baseline_result_sha256=sha(path), baseline_audit_sha256=sha(audit_path),
                compared_rows=len(old_rows), metrics=list(LEGACY_FIELDS), metric_values_compared=len(old_rows) * len(LEGACY_FIELDS))


def validate_tiles(path, records, vector_rows):
    keyed = {config_key(row): row for row in records}
    blocks = {row['id']: row['blocks'] for row in vector_rows}
    raw_mode = {row['id']: row['raw'] for row in vector_rows}
    groups = {}
    with gzip.open(path, 'rt') as source:
        for line in source:
            event = json.loads(line)
            key = config_key(event)
            group = groups.setdefault(key, [])
            assert key in keyed and event['block'] == len(group)
            assert event['first_dense'] <= event['last_dense']
            assert event['last_dense'] - event['first_dense'] >= 63
            # Coded tiles emit64 consecutive scalars when always ready. RAW
            # fetches/extracts each scalar separately, including cache misses.
            if event['memory_profile'] == 0 and not raw_mode[event['id']]:
                assert event['last_dense'] - event['first_dense'] == 63
            if group:
                assert event['first_dense'] > group[-1]['last_dense']
            group.append(event)
    assert groups.keys() == keyed.keys()
    result = []
    for key, events in groups.items():
        row = keyed[key]
        assert len(events) == blocks[row['id']]
        assert events[0]['first_dense'] == row['observability']['timestamps']['first_dense']
        assert events[-1]['last_dense'] == row['observability']['timestamps']['last_dense']
        gaps = [b['first_dense'] - a['last_dense'] - 1 for a, b in zip(events, events[1:])]
        spans = [event['last_dense'] - event['first_dense'] + 1 for event in events]
        result.append(dict(id=key[0], memory_profile=key[1], write_overlap=key[2], tiles=len(events),
                           delivery_span_min=min(spans), delivery_span_max=max(spans),
                           intertile_gap_min=min(gaps) if gaps else None,
                           intertile_gap_median=statistics.median(gaps) if gaps else None,
                           intertile_gap_max=max(gaps) if gaps else None))
    return result


def aggregate(records):
    contract = read(CONTRACT_PATH)
    results = []
    for population in ('legacy_actual', 'appended_actual', 'all_actual', 'other'):
        def included(row):
            actual = row['id'].startswith('actual:')
            appended = row['id'].startswith('actual:c3:f28:')
            return {'legacy_actual': actual and not appended, 'appended_actual': appended,
                    'all_actual': actual, 'other': not actual}[population]
        for profile in (0, 1):
            for clear in (0, 1):
                subset = [row for row in records if included(row) and row['memory_profile'] == profile and row['write_overlap'] == clear]
                if not subset:
                    continue
                hist = [sum(row['observability']['scratch_state_cycles'][index] for row in subset) for index in range(32)]
                groups = {name: sum(hist[index] for index in indexes) for name, indexes in contract['exclusive_scratch_groups'].items()}
                total = sum(row['cycles'] for row in subset)
                assert sum(groups.values()) == total
                results.append(dict(population=population, memory_profile=profile, write_overlap=clear, packets=len(subset),
                    cycles=total, dense_coefficients=sum(row['dense_coefficients'] for row in subset),
                    groups=groups, group_percent={name: 100 * cycles / total for name, cycles in groups.items()},
                    overlapping_edges={name: sum(row['observability']['overlapping_edges'][name] for row in subset)
                                       for name in subset[0]['observability']['overlapping_edges']},
                    post_last_input_coefficient_done_cycles=sum(row['cycles'] - row['observability']['timestamps']['last_input'] for row in subset),
                    highwaters={name: max(row['observability']['highwaters'][name] for row in subset)
                                for name in subset[0]['observability']['highwaters']}))
    return results
