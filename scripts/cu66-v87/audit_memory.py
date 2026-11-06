#!/usr/bin/env python3
"""Independently recompute V87 memory-service bounds from frozen V82 traffic."""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'experiments/python-gamebub-v82/execution/attempt-20261106T052617072164Z-c382bb87/g16-frames.jsonl'
EXECUTION = ROOT / 'experiments/python-gamebub-v82/execution.py'
ANALYSIS = ROOT / 'experiments/python-gamebub-v87/memory/analyze.py'
RESULTS = ROOT / 'experiments/python-gamebub-v87/memory/results.json'
FRAMES = ROOT / 'experiments/python-gamebub-v87/memory/frames.jsonl'
DOC = ROOT / 'docs/cu66-v87/memory.md'
OUT = ROOT / 'experiments/python-gamebub-v87/memory-independent-audit.json'
DEADLINE = 1_000_000


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def stats(xs):
    return {'min': min(xs), 'median': __import__('statistics').median(xs), 'max': max(xs), 'total': sum(xs)}


def main():
    source, generated = read_jsonl(SOURCE), read_jsonl(FRAMES)
    report = json.loads(RESULTS.read_text())
    doc = DOC.read_text()
    errors = []

    def check(condition, message):
        if not condition:
            errors.append(message)

    check(len(source) == 457 and len({(r['cohort'], r['fid']) for r in source}) == 457, 'frozen V82 source count/uniqueness')
    check(len(generated) == 457 * 4, 'generated rows are not four scenarios per source')
    check(report.get('status') == 'PASS_NECESSARY_TRAFFIC_ACCOUNTING', 'status')
    check(report.get('native_sources') == 457 and len(report.get('configurations', [])) == 4, 'reported sources/scenarios')
    check(report.get('source_sha256', {}).get(str(SOURCE.relative_to(ROOT))) == sha(SOURCE), 'frozen V82 frame source pin')
    check(report.get('source_sha256', {}).get(str(EXECUTION.relative_to(ROOT))) == sha(EXECUTION), 'V82 execution source pin')
    check(report.get('source_sha256', {}).get(str(ANALYSIS.relative_to(ROOT))) == sha(ANALYSIS), 'analysis source pin')
    check(report.get('frames_sha256') == sha(FRAMES), 'generated rows hash')
    check(report.get('physical_30fps_proven') is False and report.get('validated_under10ms_proven') is False, 'qualification flags')
    check('necessary aggregate service constraints only' in report.get('qualification', '').lower(), 'necessary-bound qualification')
    check('not a' not in report.get('qualification', '').lower(), 'qualification text')

    configs = [
        ('current_18r_16w', 18, 16, False),
        ('hypothetical_service12', 12, 12, False),
        ('counterfactual_copy_alias_18r_16w', 18, 16, True),
        ('counterfactual_copy_alias_service12', 12, 12, True),
    ]
    check([(c['name'], c['read'], c['write'], c['copy_write_elision']) for c in report.get('configurations', [])] == configs, 'scenario definitions')
    indexed = {(r['cohort'], r['fid']): r for r in source}
    actual = {(r['configuration'], r['cohort'], r['fid']): r for r in generated}
    check(len(indexed) == 457 and len(actual) == len(generated), 'generated row uniqueness')

    recomputed = {}
    for name, read_cycles, write_cycles, alias in configs:
        rows = []
        for s in source:
            key = (name, s['cohort'], s['fid'])
            row = actual.get(key)
            check(row is not None, f'missing output row {key}')
            if row is None:
                continue
            m = s['logical_BL8']
            reads = m['reference_reads'] + m['HUD_reads']
            writes = m['canonical_writes'] + m['HUD_writes']
            omitted = 4 * s['materialize_copy_reference_tiles'] if alias else 0
            writes -= omitted
            busy = reads * read_cycles + writes * write_cycles
            traffic = reads + writes
            check(m['reference_reads'] == s['reference_read_tiles'] * 4, f'reference BL8 accounting {key}')
            check(m['canonical_writes'] == s['physical_store_tiles'] * 4, f'canonical write accounting {key}')
            check(m['HUD_reads'] == 2640 and m['HUD_writes'] == 2640, f'HUD traffic {key}')
            for field, expected in [('reads_BL8', reads), ('writes_BL8', writes), ('traffic_BL8', traffic),
                                    ('memory_busy_cycles', busy), ('omitted_COPY_writes_BL8', omitted)]:
                check(row.get(field) == expected, f'{field} arithmetic {key}')
            check(math.isclose(row.get('no_reservation_necessary_ms', -1), busy / 100000, abs_tol=1e-10), f'no-reservation conversion {key}')
            check(math.isclose(row.get('reservation20_necessary_ms', -1), busy / 80000, abs_tol=1e-10), f'reserved conversion {key}')
            check(math.isclose(row.get('necessary_equal_service_max_cycles_no_reservation', -1), DEADLINE / traffic, abs_tol=1e-10), f'equal-service threshold {key}')
            check(math.isclose(row.get('necessary_equal_service_max_cycles_reserved20', -1), 0.8 * DEADLINE / traffic, abs_tol=1e-10), f'reserved threshold {key}')
            check(row.get('root') == s['root'] and row.get('seal') == s['seal'] and row.get('key') == s['key'], f'frozen source identity {key}')
            rows.append((row, busy, traffic))
        if not rows:
            continue
        busy_values = [x[1] for x in rows]
        traffic_values = [x[2] for x in rows]
        strict_no_res = sum(b < DEADLINE for b in busy_values)
        strict_reserved = sum(b < 0.8 * DEADLINE for b in busy_values)
        witness = max(rows, key=lambda x: x[1])[0]
        recomputed[name] = {'sources': len(rows), 'traffic_BL8': stats(traffic_values),
                            'busy_cycles': stats(busy_values),
                            'strict_10ms_no_reservation': strict_no_res,
                            'strict_10ms_reserved20': strict_reserved,
                            'max_witness': {'cohort': witness['cohort'], 'fid': witness['fid'],
                                            'traffic_BL8': witness['traffic_BL8'],
                                            'memory_busy_cycles': witness['memory_busy_cycles']}}
        summary = next((x for x in report.get('summaries', []) if x['configuration'] == name), {})
        check(summary.get('sources') == len(rows), f'{name} summary count')
        check(summary.get('traffic_BL8') == stats(traffic_values), f'{name} traffic summary')
        check(summary.get('busy_cycles') == stats(busy_values), f'{name} work summary')
        check(summary.get('memory_work_strictly_within10ms_no_reservation') == strict_no_res, f'{name} strict no-reservation count')
        check(summary.get('memory_work_strictly_within10ms_reserved20') == strict_reserved, f'{name} strict reserved count')
        check(summary.get('maximum_work_witness', {}).get('cohort') == witness['cohort'] and
              summary.get('maximum_work_witness', {}).get('fid') == witness['fid'], f'{name} max witness')

    current = recomputed.get('current_18r_16w', {})
    check(current.get('max_witness') == {'cohort': 0, 'fid': 1, 'traffic_BL8': 68904, 'memory_busy_cycles': 1170192}, 'cold witness')
    check(current.get('strict_10ms_no_reservation') == 413 and current.get('strict_10ms_reserved20') == 186, 'current strict counts')
    check(recomputed.get('hypothetical_service12', {}).get('strict_10ms_reserved20') == 417, 'service12 reserved strict count')
    check(recomputed.get('counterfactual_copy_alias_18r_16w', {}).get('strict_10ms_reserved20') == 298, 'alias current reserved strict count')
    check(recomputed.get('counterfactual_copy_alias_service12', {}).get('strict_10ms_reserved20') == 457, 'alias service12 reserved strict count')

    # Check every document table value and central threshold against recomputation.
    table_expectations = [
        ('Current 18-cycle reads / 16-cycle writes', 1170192, 14.62740, 186),
        ('Hypothetical 12-cycle reads and writes', 826848, 10.33560, 417),
        ('Counterfactual COPY-store alias, current service', 1062224, 13.27780, 298),
        ('Counterfactual COPY-store alias, 12-cycle service', 745872, 9.32340, 457),
    ]
    for label, cycles, reserved_ms, count in table_expectations:
        check(label in doc, f'doc scenario label: {label}')
        check(f'{cycles/100000:.5f}' in doc and f'{reserved_ms:.5f}' in doc and f'{count}/457' in doc, f'doc numeric row: {label}')
    threshold = 800000 / 68904
    threshold_no_res = 1000000 / 68904
    doc_thresholds = [11.61035, 14.51295]
    check(abs(doc_thresholds[0] - threshold) < 0.00001 and abs(doc_thresholds[1] - threshold_no_res) < 0.00001, 'documented strict equal-service thresholds within stated decimal precision')
    check('necessary aggregate-service bound' in doc and 'insufficient to establish a 10-ms' in doc, 'doc warns bounds do not predict completion')
    check('40 still exceed it' in doc, 'doc correctly says 40 service12 rows exceed reserved budget')

    audit = {'schema': 'cu66-v87-memory-independent-audit-v1',
             'status': 'PASS' if not errors else 'FAIL',
             'frozen_source_sha256': sha(SOURCE), 'v82_execution_sha256': sha(EXECUTION),
             'analysis_sha256': sha(ANALYSIS), 'generated_frames_sha256': sha(FRAMES),
             'source_rows': len(source), 'scenario_rows': len(generated),
             'scenarios': recomputed,
             'cold_frame_equal_service_threshold_cycles_per_BL8': {
                 'no_reservation_strictly_below': threshold_no_res,
                 'reserved20_strictly_below': threshold},
             'interpretation': 'Traffic arithmetic and necessary aggregate service budgets only; these values are not predicted completion times or hardware qualification.',
             'documentation_precision_note': 'The two strict equal-service thresholds are shown to five decimal places; the exact values from 800000/68904 and 1000000/68904 are retained in this audit. Rounded strict thresholds should be explicitly marked approximate if used as cutoffs.',
             'errors': errors}
    OUT.write_text(json.dumps(audit, indent=2) + '\n')
    print(json.dumps({'status': audit['status'], 'sources': len(source),
                      'scenario_rows': len(generated), 'errors': errors}, indent=2))
    raise SystemExit(0 if not errors else 1)


if __name__ == '__main__':
    main()
