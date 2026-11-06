#!/usr/bin/env python3
"""Verify the complete V83 retained campaign without rerunning its scheduler.

All 3,656 schedules have retained producer audit/count summaries. Four complete
DAG/timeline witnesses receive a fresh independent timeline audit here. Neither
class is physical FPGA timing, a sustained stream, or an ESP32 transport proof.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import statistics
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v83'
CONTROL = ROOT / 'experiments/python-gamebub-v82/execution/attempt-20261106T052617072164Z-c382bb87/g16-frames.jsonl'
INDEX = ROOT / 'experiments/python-gamebub-v82/native/index.json'
EXPECTED_COHORTS = (119, 119, 119, 100)
RESERVED = dict(period=10000, blocked=[[0, 2000]])
CONFIGS = [
    dict(name='serial_groups_current', read_gap=18, write_gap=16, group_slots=1, hash_lanes=1, inverse_cycles=64, windows=None),
    dict(name='bounded_groups_current_hash1', read_gap=18, write_gap=16, group_slots=4, hash_lanes=1, inverse_cycles=64, windows=None),
    dict(name='bounded_groups_current', read_gap=18, write_gap=16, group_slots=4, hash_lanes=4, inverse_cycles=64, windows=None),
    dict(name='bounded_groups_current_reserved20', read_gap=18, write_gap=16, group_slots=4, hash_lanes=4, inverse_cycles=64, windows=RESERVED),
    dict(name='bounded_groups_target12_reserved20', read_gap=12, write_gap=12, group_slots=4, hash_lanes=4, inverse_cycles=64, windows=RESERVED),
    dict(name='bounded_groups_target8', read_gap=8, write_gap=8, group_slots=4, hash_lanes=4, inverse_cycles=64, windows=None),
    dict(name='bounded_groups_target8_reserved20', read_gap=8, write_gap=8, group_slots=4, hash_lanes=4, inverse_cycles=64, windows=RESERVED),
    dict(name='bounded_groups_target8_inverse256_reserved20', read_gap=8, write_gap=8, group_slots=4, hash_lanes=4, inverse_cycles=256, windows=RESERVED),
]
BY_CONFIG = {c['name']: c for c in CONFIGS}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def local(path):
    path = Path(path)
    path = path.resolve() if path.is_absolute() else (ROOT / path).resolve()
    path.relative_to(ROOT)
    return path


def relative(path):
    return str(local(path).relative_to(ROOT))


def stat(values):
    return dict(min=min(values), median=statistics.median(values), max=max(values), total=sum(values))


def summaries(rows):
    result = []
    for config in CONFIGS:
        chosen = [r for r in rows if r['configuration'] == config['name']]
        for key in (True, False, None):
            group = [r for r in chosen if key is None or r['key'] == key]
            if group:
                cycles = [r['finish_cycles'] for r in group]
                result.append(dict(configuration=config['name'], key=key, sources=len(group),
                                   cycles=stat(cycles), model_ms=stat([v * 1e-5 for v in cycles]),
                                   conditional_under10ms=sum(v < 1_000_000 for v in cycles),
                                   conditional_within30fps_period=sum(v <= 100_000_000 // 30 for v in cycles)))
    return result


def pins_current(pins):
    assert pins and all(re.fullmatch('[0-9a-f]{64}', value) for value in pins.values())
    for name, digest in pins.items():
        assert relative(name) == name, ('noncanonical pin path', name)
        assert sha(local(name)) == digest, ('current source mismatch', name)


def verify_tests():
    sched_path = AREA / 'scheduler-tests.json'
    sched = read(sched_path)
    assert sched['status'] == 'PASS' and sched['count'] == len(sched['checks']) == 37
    assert sched['source_sha256'] == sha(AREA / 'scheduler.py')
    assert sched['test_sha256'] == sha(ROOT / 'scripts/cu66-v83/test_scheduler.py')
    assert all(c['status'] in ('PASS', 'PASS_REJECT') for c in sched['checks'])
    work_path = AREA / 'workload-tests.json'
    work = read(work_path)
    assert work['status'] == 'PASS' and work['checks'] == len(work['cases']) == 206
    assert work['timing_is_physical'] is False
    pins_current(work['source_sha256'])
    audit_path = AREA / 'audit-tests.json'
    audit = read(audit_path)
    assert audit['passed'] == len(audit['checks']) == 10 and audit['failed'] == 0
    assert all(c['result'] in ('accepted_as_expected', 'rejected_as_expected') for c in audit['checks'])
    pins_current(audit['source_sha256'])
    return {relative(p):sha(p) for p in (sched_path, work_path, audit_path)}


def capacities(config):
    return dict(memory=1, inverse=1, reconstruct=1, hash=config['hash_lanes'],
                tree_r=1, tree_w=1, map_r=1, map_w=1)


def check_row(row, control, native):
    config = BY_CONFIG[row['configuration']]
    assert (row['cohort'], row['ordinal'], row['fid'], row['key']) == (
        native['cohort'], native['ordinal'], native['fid'], native['key'])
    assert (row['root'], row['seal']) == (control['root'], control['seal'])
    c = row['counts']
    expected = dict(reference_read_BL8=control['logical_BL8']['reference_reads'],
                    canonical_write_BL8=control['logical_BL8']['canonical_writes'],
                    HUD_read_BL8=control['logical_BL8']['HUD_reads'],
                    HUD_write_BL8=control['logical_BL8']['HUD_writes'],
                    tree_r_words32=control['metadata']['tree_read_words32'],
                    tree_w_words32=control['metadata']['tree_write_words32'],
                    map_r_entries=control['metadata']['map_read_entries'],
                    map_w_entries=control['metadata']['map_write_entries'],
                    hash_compression_blocks=control['hash_compression_blocks'],
                    tree_clone_nodes=control['metadata']['tree_clone_nodes'],
                    physical_store_tiles=control['physical_store_tiles'],
                    resident_store_elisions=control['resident_store_elisions'])
    assert all(c.get(k, 0) == v for k, v in expected.items()), ('V82 count mismatch', row['cohort'], row['fid'])
    modes = {'CONST128':control['const_tiles'], 'COPY_REF':control['copy_tiles'],
             'RESIDUAL':8100-control['const_tiles']-control['copy_tiles']}
    assert {k:c['mode_tiles'].get(k, 0) for k in modes} == modes
    assert sum(c['mode_tiles'].values()) == 8100
    assert c.get('inverse_tiles', 0) == c.get('reconstruct_tiles', 0) == modes['RESIDUAL']
    assert c['hash_cycles'] == c['hash_compression_blocks'] * 64
    assert c['groups'] == len(c['group_starts']) == len(c['group_releases']) == 508
    assert len(set(c['group_starts'])) == len(set(c['group_releases'])) == 508
    assert c['group_payload_buffer_bytes'] == config['group_slots'] * 1024
    assert c['clone_temporary_bytes'] == 32
    audit = row['audit']
    assert audit['jobs'] == c['task_count']
    assert type(row['finish_cycles']) is int and row['finish_cycles'] > 0
    assert row['finish_cycles'] == audit['finish_cycles']
    assert row['model_ms'] == row['finish_cycles'] * 1e-5
    work = dict(memory=(expected['reference_read_BL8'] + expected['HUD_read_BL8']) * config['read_gap'] +
                       (expected['canonical_write_BL8'] + expected['HUD_write_BL8']) * config['write_gap'],
                inverse=c.get('inverse_tiles', 0) * config['inverse_cycles'],
                reconstruct=c.get('reconstruct_tiles', 0) * 64,
                hash=c['hash_compression_blocks'] * 64,
                tree_r=c['tree_r_words32'], tree_w=c['tree_w_words32'],
                map_r=c['map_r_entries'], map_w=c['map_w_entries'])
    assert audit['resource_work_cycles'] == {k:v for k, v in work.items() if v}
    caps = capacities(config)
    assert all(0 <= value <= caps[name] for name, value in audit['resource_peak'].items())
    assert 0 < audit['group_peak'] <= config['group_slots']
    assert row['finish_cycles'] >= max((value + caps[name] - 1) // caps[name] for name, value in work.items())
    assert re.fullmatch('[0-9a-f]{64}', row['timeline_sha256'])


def verify_witness(path, rows, audit_module):
    with gzip.open(path, 'rt') as stream:
        witness = json.load(stream)
    config = witness['config']
    assert config == BY_CONFIG[config['name']]
    caps = capacities(config)
    assert witness['capacities'] == caps
    workload, result = witness['workload'], witness['result']
    timeline = result['timeline']
    checked = audit_module.verify(workload['jobs'], timeline, caps, config['windows'],
                                  workload['groups'], config['group_slots'])
    assert checked == witness['audit']
    assert checked['finish_cycles'] == result['finish_cycles']
    by_id = {entry['id']:entry for entry in timeline}
    assert result['finish_by_id'] == {str(i):r['finish'] for i, r in by_id.items()}
    assert by_id[workload['complete']]['finish'] == result['finish_cycles']
    # Witness filename identities are fixed by the runner and independently
    # cross-bound to a retained native row below.
    matched = re.fullmatch(r'witness-c0-f([01])-(.+)\.json\.gz', path.name)
    assert matched and matched[2] == config['name']
    key = (0, int(matched[1]), config['name'])
    row = rows[key]
    assert workload['counts'] == row['counts'] and checked == row['audit']
    assert result['tasks'] == len(workload['jobs'])
    assert result['resources'].keys() == caps.keys()
    for name, cap in caps.items():
        resource = result['resources'][name]
        assert resource['capacity'] == cap
        assert resource['work_cycles'] == checked['resource_work_cycles'].get(name, 0)
        assert resource['task_count'] == sum(j['resource']==name for j in workload['jobs'])
        assert resource['max_active'] == checked['resource_peak'].get(name, 0)
    digest = hashlib.sha256(json.dumps(timeline, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    assert digest == row['timeline_sha256']
    # Independently check the semantically important group reuse and final fence
    # edges, beyond the generic supplied-DAG timeline audit.
    jobs = {j['id']:j for j in workload['jobs']}
    ancestors, frontier = set(), [workload['complete']]
    while frontier:
        ident = frontier.pop()
        if ident not in ancestors:
            ancestors.add(ident)
            frontier.extend(jobs[ident]['deps'])
    assert ancestors == jobs.keys(), 'completion fence lacks an operation dependency'
    groups = workload['groups']
    group_jobs = {gi:[] for gi in range(len(groups))}
    for job in jobs.values():
        if job.get('group') is not None:
            group_jobs[job['group']].append(job)
    for gi, group in enumerate(groups):
        expected_deps = [] if gi < config['group_slots'] else [groups[gi-config['group_slots']]['release']]
        assert jobs[group['start']]['deps'] == expected_deps
        assert jobs[group['start']]['kind'] == 'group_start'
        assert jobs[group['release']]['kind'] == 'group_release'
        members = group_jobs[gi]
        release_dependencies = set(jobs[group['release']]['deps'])
        required = {j['id'] for j in members if j['kind'] in ('canonical_write', 'map_shadow_entry')}
        assert required <= release_dependencies
        leaves = [j for j in members if j['kind']=='hash_leaf']
        assert len(leaves) <= 1
        if leaves:
            leaf = leaves[0]
            payloads = {j['id'] for j in members if j['kind'] in ('copy_ready', 'const_generate', 'reconstruct')}
            dependencies = set(leaf['deps'])
            for dependency in leaf['deps']:
                if jobs[dependency]['kind'] == 'hash_metadata_read':
                    dependencies.update(jobs[dependency]['deps'])
            assert payloads <= dependencies, 'leaf hash missing payload readiness'
            assert any(j['kind']=='hash_digest_write' and leaf['id'] in j['deps']
                       and j['id'] in release_dependencies for j in members)
    invalid = {j['tile']:j['id'] for j in jobs.values() if j['kind']=='map_invalidate'}
    reads = {j['tile']:j['id'] for j in jobs.values() if j['kind']=='reference_read'}
    inverses = {j['tile']:j['id'] for j in jobs.values() if j['kind']=='inverse'}
    for job in jobs.values():
        if job['resource']=='memory':
            assert job['kind'] in ('reference_read', 'canonical_write', 'HUD_read', 'HUD_write')
            gap = config['read_gap'] if job['kind'] in ('reference_read', 'HUD_read') else config['write_gap']
            assert job['duration'] == job['BL8'] * gap
        elif job['resource']=='inverse':
            assert job['duration'] == config['inverse_cycles']
        elif job['resource']=='reconstruct':
            assert job['duration'] == 64
        elif job['resource']=='hash':
            assert job['duration'] == job['compression_blocks'] * 64
        elif job['resource'] in ('tree_r', 'tree_w'):
            assert job['duration'] == job['words32']
        elif job['resource'] in ('map_r', 'map_w'):
            assert job['duration'] == job['entries']
        else:
            assert job['resource'] is None
            assert job['duration'] == (1 if job['kind']=='const_generate' else 0)
        if job['kind'] == 'canonical_write':
            assert invalid[job['tile']] in job['deps']
        if job['kind'] == 'reconstruct':
            assert inverses[job['tile']] in job['deps']
            if job['tile'] in reads:
                assert reads[job['tile']] in job['deps']
        if job['kind'] in ('canonical_write', 'HUD_read', 'map_shadow_entry'):
            assert job['id'] in jobs[workload['complete']]['deps'] or by_id[job['id']]['finish'] <= by_id[workload['complete']]['start']
    assert result['physical_timing_proven'] is False
    return dict(path=relative(path), sha256=sha(path), jobs=len(jobs),
                finish_cycles=checked['finish_cycles'], independently_reaudited=True)


def verify_workspace(witnesses):
    path = AREA/'workspace.json'
    workspace = read(path)
    assert workspace['schema'] == 'cu66-v83-workspace-v1' and workspace['status'] == 'PASS'
    assert workspace['residual_tile_bytes'] == 192
    expected_sources = {'scripts/cu66-v83/workspace_analysis.py',
                        'fpga/experiments/cu66-v69/inverse/cu66_idct8x8.sv'}
    assert workspace['source_sha256'].keys() == expected_sources
    pins_current(workspace['source_sha256'])
    rtl = local('fpga/experiments/cu66-v69/inverse/cu66_idct8x8.sv').read_text()
    width = re.search(r'output\s+logic\s+\[(\d+):0\]\s+out_tile', rtl)
    assert width and int(width[1])+1 == 1536
    records = workspace['witnesses']
    expected_pins = {w['path']:w['sha256'] for w in witnesses}
    assert len(records) == 4 and {r['path']:r['sha256'] for r in records} == expected_pins

    def peak(intervals):
        points = []
        for start, end, size in intervals:
            assert 0 <= start <= end and size >= 0
            if end > start:
                points.extend(((start, size), (end, -size)))
        total = high = 0
        for _, change in sorted(points):
            total += change
            assert total >= 0
            high = max(high, total)
        assert total == 0
        return high

    for record in records:
        with gzip.open(local(record['path']), 'rt') as stream:
            witness = json.load(stream)
        assert record['configuration'] == witness['config']['name']
        assert record['group_slots'] == witness['config']['group_slots'] == 4
        assert record['maximum_admitted_tiles'] == 64
        assert record['conservative_static_workspace_bytes'] == 20480
        assert record['output_group_allocation_bytes'] == 4096
        jobs = witness['workload']['jobs']
        timing = {r['id']:r for r in witness['result']['timeline']}
        groups = witness['workload']['groups']
        group_sizes = {g:0 for g in range(len(groups))}
        consumed = {}
        for job in jobs:
            if job['kind']=='map_lookup':
                group_sizes[job['group']] += 1
            elif job['kind']=='reconstruct':
                consumed[job['tile']] = timing[job['id']]['finish']
        intervals = {'output_groups':[], 'reference_inputs':[], 'inverse_results':[]}
        for gi, group in enumerate(groups):
            intervals['output_groups'].append((timing[group['start']]['start'],
                                                timing[group['release']]['finish'], 64*group_sizes[gi]))
        for job in jobs:
            if job['kind'] not in ('reference_read', 'inverse'):
                continue
            start = timing[job['id']]['finish']
            finish = consumed.get(job['tile'], timing[groups[job['group']]['release']]['finish'])
            category, size = ('reference_inputs',64) if job['kind']=='reference_read' else ('inverse_results',192)
            intervals[category].append((start, finish, size))
        assert record['stage_peak_bytes'] == {name:peak(values) for name, values in intervals.items()}
        combined = peak([item for values in intervals.values() for item in values])
        assert record['combined_observed_logical_bytes'] == combined <= 20480
    return dict(path=relative(path), sha256=sha(path), witnesses=4,
                residual_tile_bytes=192, conservative_four_group_workspace_bytes=20480,
                source_sha256=workspace['source_sha256'])


def verify(session_path):
    session_path = local(session_path)
    if session_path.is_dir():
        session_path /= 'results.json'
    session = read(session_path)
    assert session['schema'] == 'cu66-v83-parallel-session-v1' and session['status'] == 'PASS'
    assert session['runner_sha256'] == sha(ROOT / 'scripts/cu66-v83/run_campaign.py')
    records = session['cohorts']
    assert len(records) == 4 and [r['cohort'] for r in records] == list(range(4))
    test_pins = verify_tests()
    index = read(INDEX)
    assert index['record_count'] == len(index['frames']) == 457
    assert tuple(index['cohort_counts']) == EXPECTED_COHORTS
    native = {(f['cohort'], f['fid']):f for f in index['frames']}
    controls = {(r['cohort'], r['fid']):r for r in map(json.loads, CONTROL.read_text().splitlines())}
    assert len(native) == len(controls) == 457 and native.keys() == controls.keys()
    expected_sources = {
        'scripts/cu66-v83/prototype_pipeline.py', 'experiments/python-gamebub-v83/scheduler.py',
        'experiments/python-gamebub-v83/workload.py', 'experiments/python-gamebub-v83/audit.py',
        'scripts/cu66-v82/prototype_commitment.py', 'experiments/python-gamebub-v82/execution.py',
        'experiments/python-gamebub-v82/native/data.py', 'experiments/python-gamebub-v82/native/index.json',
        'fpga/experiments/cu66-v81/residency/model.py', relative(CONTROL)}
    chunk_pins = {relative(INDEX.parent/c['path']):c['gzip_sha256'] for c in index['chunks']}
    expected_sources.update(chunk_pins)
    all_rows, all_pins, evidence_pins, witness_paths = {}, None, {}, []
    for record in records:
        cohort = record['cohort']
        assert record['exit_code'] == 0
        assert record['command'][1:] == ['scripts/cu66-v83/prototype_pipeline.py', '--cohort', str(cohort)]
        log_path = local(record['log'])
        assert log_path.parent == session_path.parent and log_path.name == f'cohort{cohort}.log'
        assert sha(log_path) == record['log_sha256']
        report_path = local(record['report'])
        report = read(report_path)
        assert report['schema'] == 'cu66-v83-causal-pipeline-v1'
        assert report['status'] == 'PASS_CONDITIONAL_COHORT_SCHEDULES'
        assert report['cohort'] == cohort and report['smoke_limit'] == 0
        assert report['configurations'] == CONFIGS
        assert report['native_frames'] == EXPECTED_COHORTS[cohort]
        assert report['audited_schedules'] == EXPECTED_COHORTS[cohort] * len(CONFIGS)
        assert report['physical_performance_proven'] is report['rtl_changed'] is False
        assert report['native_only'] is True and report['clock_mhz_assumption'] == 100
        assert log_path.read_text().splitlines()[-1] == f"PIPELINE_REPORT {report_path} {report['status']}"
        pins = report['source_sha256']
        assert pins.keys() == expected_sources
        assert all(pins[k] == v for k, v in chunk_pins.items())
        pins_current(pins)
        if all_pins is None:
            all_pins = pins
        assert pins == all_pins
        archive = report_path.parent/'sources.tar.gz'
        assert sha(archive) == report['source_archive_sha256']
        with tarfile.open(archive, 'r:gz') as tar:
            members = tar.getmembers()
            expected_members = {name for name in pins if not name.endswith('.gz')}
            assert len(members) == len(expected_members)
            assert {m.name for m in members} == expected_members
            for member in members:
                assert member.isfile()
                assert hashlib.sha256(tar.extractfile(member).read()).hexdigest() == pins[member.name]
        artifacts = report['artifacts_sha256']
        actual_files = {p.name for p in report_path.parent.iterdir() if p.is_file() and p.name!='results.json'}
        assert artifacts.keys() == actual_files
        for name, digest in artifacts.items():
            assert Path(name).name == name and sha(report_path.parent/name) == digest
        expected_witnesses = {f'witness-c0-f{fid}-{config}.json.gz' for fid in (0, 1)
                              for config in ('bounded_groups_current', 'bounded_groups_target8_reserved20')} if cohort == 0 else set()
        assert {name for name in artifacts if name.startswith('witness-')} == expected_witnesses
        assert actual_files == {'sources.tar.gz', 'frames.jsonl'} | expected_witnesses
        rows = [json.loads(line) for line in (report_path.parent/'frames.jsonl').read_text().splitlines()]
        assert len(rows) == EXPECTED_COHORTS[cohort] * len(CONFIGS)
        expected_keys = {(cohort, f['fid'], config['name']) for f in index['frames']
                         if f['cohort']==cohort for config in CONFIGS}
        cohort_rows = {}
        for row in rows:
            key = (row['cohort'], row['fid'], row['configuration'])
            assert key not in cohort_rows and key not in all_rows, ('duplicate source schedule', key)
            assert key in expected_keys
            check_row(row, controls[key[:2]], native[key[:2]])
            cohort_rows[key] = row
        assert cohort_rows.keys() == expected_keys
        assert report['summaries'] == summaries(rows)
        all_rows.update(cohort_rows)
        witness_paths.extend(report_path.parent/name for name in sorted(expected_witnesses))
        for path in (report_path, log_path):
            evidence_pins[relative(path)] = sha(path)
    assert len(all_rows) == 457 * len(CONFIGS) == 3656
    assert len(witness_paths) == 4
    spec = importlib.util.spec_from_file_location('cu83_evidence_audit', AREA/'audit.py')
    audit_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit_module)
    witnesses = [verify_witness(path, all_rows, audit_module) for path in witness_paths]
    workspace = verify_workspace(witnesses)
    pins_current(all_pins)
    ordered_rows = [all_rows[(f['cohort'], f['fid'], config['name'])]
                    for f in index['frames'] for config in CONFIGS]
    return dict(schema='cu66-v83-evidence-summary-v1', status='PASS_CONDITIONAL_MODEL_EVIDENCE',
                session=relative(session_path), session_sha256=sha(session_path),
                verifier_sha256=sha(Path(__file__)), configurations=CONFIGS,
                native_sources=457, cohorts=list(EXPECTED_COHORTS), schedules=3656,
                keys=sum(f['key'] for f in index['frames']), deltas=sum(not f['key'] for f in index['frames']),
                source_sha256=all_pins, test_reports_sha256=test_pins, evidence_sha256=evidence_pins,
                scheduler_checks=37, workload_checks=206, audit_checks=10,
                independently_reaudited_witnesses=witnesses,
                workspace=workspace,
                summaries=summaries(ordered_rows), physical_timing_proven=False,
                sustained_30fps_proven=False, validated_under10ms_proven=False,
                scope=[
                    'All3656 retained rows independently checked against exact native/V82 identity, counts, source hashes and report statistics.',
                    'Four full DAG/timeline witnesses independently reaudited; the remaining3652 timelines are producer-audited, with hashes and summaries retained rather than full timelines.',
                    'The timeline auditor checks supplied DAG edges; directed construction tests and witness checks cover selected semantic dependency rules, not an exhaustive proof.',
                    '100MHz and8/12/18read/8/12/16write service intervals are conditional inputs, not target timing or electrical guarantees.',
                    'Eight-cycle BL8 is the payload-only x16 ideal; row/command/turnaround costs may prevent it.',
                    'Each source starts independently with reservation phase0;20% blocking is illustrative, not continuous scanout/refresh/deadline qualification.',
                    'No measured decoder speed, wire/ESP32/entropy throughput, target fit or quality/bitrate superiority claim.'])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', required=True)
    parser.add_argument('--output', default='experiments/python-gamebub-v83/summary.json')
    parser.add_argument('--verify-summary', action='store_true')
    args = parser.parse_args()
    summary = verify(args.session)
    output = local(args.output)
    if args.verify_summary:
        assert read(output) == summary, 'retained summary differs from recomputed evidence'
    else:
        with output.open('x') as stream:
            stream.write(json.dumps(summary, indent=2)+'\n')
    print(f'V83_EVIDENCE_PASS sources={summary["native_sources"]} schedules={summary["schedules"]} witnesses=4 scheduler=37 workload=206 audit=10')
    print('V83_SUMMARY', output)


if __name__ == '__main__':
    main()
