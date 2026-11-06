#!/usr/bin/env python3
"""Native-frame causal scheduling study; all cycle costs are conditional inputs."""
from __future__ import annotations
import argparse
import datetime
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics
import sys
import tarfile
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v83'
CONTROL = ROOT / 'experiments/python-gamebub-v82/execution/attempt-20261106T052617072164Z-c382bb87/g16-frames.jsonl'
RESERVED = dict(period=10000, blocked=[(0, 2000)])
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


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def stat(values):
    return dict(min=min(values), median=statistics.median(values), max=max(values), total=sum(values))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=0, help='smoke subset only; cannot qualify full corpus')
    parser.add_argument('--cohort', type=int, choices=range(4), help='one independently reset native history')
    args = parser.parse_args()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA / 'campaigns' / f'attempt-{stamp}-{uuid.uuid4().hex[:8]}'
    out.mkdir(parents=True)
    sources = [Path(__file__).resolve(), AREA / 'scheduler.py', AREA / 'workload.py', AREA / 'audit.py',
               ROOT / 'scripts/cu66-v82/prototype_commitment.py',
               ROOT / 'experiments/python-gamebub-v82/execution.py',
               ROOT / 'experiments/python-gamebub-v82/native/data.py',
               ROOT / 'experiments/python-gamebub-v82/native/index.json',
               ROOT / 'fpga/experiments/cu66-v81/residency/model.py', CONTROL]
    sources += sorted((ROOT / 'experiments/python-gamebub-v82/native/data').glob('*.gz'))
    pins = {str(p.relative_to(ROOT)): sha(p) for p in sources}
    with tarfile.open(out / 'sources.tar.gz', 'w:gz') as tar:
        for p in sources:
            if p.suffix != '.gz':
                tar.add(p, arcname=str(p.relative_to(ROOT)), recursive=False)
    report = dict(schema='cu66-v83-causal-pipeline-v1', status='FAIL', configurations=CONFIGS,
                  source_sha256=pins, source_archive_sha256=sha(out / 'sources.tar.gz'),
                  physical_performance_proven=False, rtl_changed=False, native_only=True,
                  clock_mhz_assumption=100, smoke_limit=args.limit,
                  cohort=args.cohort,
                  limitations=[
                      'Prospective deterministic task DAG, not cycle-accurate RTL or measured hardware.',
                      'Per-BL8 service intervals aggregate four blocks per tile; no bank/row/turnaround/electrical model.',
                      'Eight-cycle service, 64/256-cycle inverse and 64-cycle reconstruction are sensitivity assumptions, not implemented rates.',
                      '20% reservations are illustrative interference, not pixel deadlines or qualified refresh service.',
                      'Reservation phase restarts at zero per independently scheduled source; continuous phase/deadline arbitration is not proved.',
                      'Eight-cycle BL8 cost is the payload-only x16 ideal, excluding command/row/turnaround costs; feasibility is not established.',
                      'Encoded packet is fully received at release; entropy/ingress/ESP32/CPU/HUD semantic hash omitted.',
                      'Hash input assembly and fixed header/context precomputation are unpriced.',
                      'Physical display bank leases and group-buffer/hash input ports are assumed, not modeled or fitted.',
                      'Four cohorts from one walkthrough family, not sustained 60/600-second distinct-source validation.',
                      'No new wire format, bitrate/quality superiority, target fit or 30fps/sub10ms proof.'])
    started = time.monotonic()
    try:
        native = load('cu83_native', ROOT / 'experiments/python-gamebub-v82/native/data.py')
        commitment = load('cu83_commitment', ROOT / 'scripts/cu66-v82/prototype_commitment.py')
        residency = load('cu83_residency', ROOT / 'fpga/experiments/cu66-v81/residency/model.py')
        execution = load('cu83_execution', ROOT / 'experiments/python-gamebub-v82/execution.py')
        workload = load('cu83_workload', AREA / 'workload.py')
        scheduler = load('cu83_scheduler', AREA / 'scheduler.py')
        auditor = load('cu83_audit', AREA / 'audit.py')
        controls = [json.loads(line) for line in CONTROL.read_text().splitlines()]
        rows = []
        processed = 0
        old_cohort = None
        with (out / 'frames.jsonl').open('w') as stream:
            for n, original in enumerate(native.iter_frames()):
                if args.cohort is not None and original['cohort'] != args.cohort:
                    continue
                if args.limit and processed >= args.limit:
                    break
                frame = dict(original, generation=original['ordinal'] + 1)
                control = controls[n]
                if frame['cohort'] != old_cohort:
                    model = residency.Residency(8100)
                    tree = commitment.CommitmentTree(granularity=16)
                    old_cohort = frame['cohort']
                candidate = 0 if model.reference is None else (model.reference + 1) % 3
                elided = [not frame['key'] and bool(frame['same_mask'][i]) and
                          bool(model.masks[i] & (1 << candidate)) for i in range(8100)]
                plan = tree.plan(frame, frame['copy_ref_mask'])
                assert (frame['cohort'], frame['fid']) == (control['cohort'], control['fid'])
                assert (plan['root'].hex(), plan['seal'].hex()) == (control['root'], control['seal'])
                account = execution.account(frame, elided, plan)
                assert account['logical_BL8'] == control['logical_BL8']
                assert account['metadata'] == control['metadata']
                model.begin(frame['fid'], frame['packet_sha256'], candidate, frame['key'], frame['tiles'], frame['same_mask'])
                model.step()
                assert model.tx.elisions == sum(elided)
                model.commit(authenticated=True)
                tree.commit(plan)
                model.present()
                assert model.banks[model.reference] == frame['tiles']
                for config in CONFIGS:
                    work = workload.build(frame, elided, plan, inverse_cycles=config['inverse_cycles'],
                                          read_gap=config['read_gap'], write_gap=config['write_gap'],
                                          reconstruct_cycles=64, group_slots=config['group_slots'])
                    counts = work['counts']
                    expected_counts = dict(reference_read_BL8=account['logical_BL8']['reference_reads'],
                                           canonical_write_BL8=account['logical_BL8']['canonical_writes'],
                                           HUD_read_BL8=account['logical_BL8']['HUD_reads'],
                                           HUD_write_BL8=account['logical_BL8']['HUD_writes'],
                                           tree_r_words32=account['metadata']['tree_read_words32'],
                                           tree_w_words32=account['metadata']['tree_write_words32'],
                                           map_r_entries=account['metadata']['map_read_entries'],
                                           map_w_entries=account['metadata']['map_write_entries'],
                                           hash_compression_blocks=account['hash_compression_blocks'])
                    assert {k:counts.get(k, 0) for k in expected_counts} == expected_counts
                    capacities = dict(memory=1, inverse=1, reconstruct=1, hash=config['hash_lanes'], tree_r=1, tree_w=1, map_r=1, map_w=1)
                    result = scheduler.schedule(work['jobs'], capacities, memory_windows=config['windows'], retain_timeline=True)
                    checked = auditor.verify(work['jobs'], result['timeline'], capacities, config['windows'],
                                              work.get('groups', []), config['group_slots'])
                    assert checked['finish_cycles'] == result['finish_cycles']
                    assert result['finish_by_id'][work['complete']] == result['finish_cycles']
                    assert result['finish_cycles'] >= max((checked['resource_work_cycles'].get(r, 0) + cap - 1) // cap for r, cap in capacities.items())
                    memory_work = ((expected_counts['reference_read_BL8'] + expected_counts['HUD_read_BL8']) * config['read_gap'] +
                                   (expected_counts['canonical_write_BL8'] + expected_counts['HUD_write_BL8']) * config['write_gap'])
                    assert checked['resource_work_cycles']['memory'] == memory_work
                    assert checked['resource_work_cycles']['hash'] == 64 * account['hash_compression_blocks']
                    row = dict(configuration=config['name'], cohort=frame['cohort'], ordinal=frame['ordinal'],
                               fid=frame['fid'], key=frame['key'], root=plan['root'].hex(), seal=plan['seal'].hex(),
                               finish_cycles=result['finish_cycles'], model_ms=result['finish_cycles'] * 1e-5,
                               counts=work['counts'], audit=checked,
                               timeline_sha256=hashlib.sha256(json.dumps(result['timeline'], sort_keys=True, separators=(',', ':')).encode()).hexdigest())
                    stream.write(json.dumps(row, separators=(',', ':')) + '\n')
                    rows.append(row)
                    # Reproducible complete DAG/timeline witnesses for an initial key and cold delta.
                    if frame['cohort'] == 0 and frame['ordinal'] in (0, 1) and config['name'] in ('bounded_groups_current', 'bounded_groups_target8_reserved20'):
                        witness = dict(config=config, capacities=capacities, workload=work, result=result, audit=checked)
                        with gzip.open(out / f"witness-c0-f{frame['fid']}-{config['name']}.json.gz", 'wt') as f:
                            json.dump(witness, f, separators=(',', ':'))
                processed += 1
                if processed % 10 == 0 or processed == 1:
                    print(f'PIPELINE_NATIVE_PROGRESS cohort={args.cohort} frames={processed} schedules={len(rows)} wall={time.monotonic()-started:.1f}s', flush=True)
        count = len(rows) // len(CONFIGS)
        expected = (119, 119, 119, 100)[args.cohort] if args.cohort is not None else 457
        assert count == (args.limit or expected)
        summaries = []
        for config in CONFIGS:
            selected = [r for r in rows if r['configuration'] == config['name']]
            for key in (True, False, None):
                group = [r for r in selected if key is None or r['key'] == key]
                if group:
                    summaries.append(dict(configuration=config['name'], key=key, sources=len(group),
                                          cycles=stat([r['finish_cycles'] for r in group]),
                                          model_ms=stat([r['model_ms'] for r in group]),
                                          conditional_under10ms=sum(r['finish_cycles'] < 1_000_000 for r in group),
                                          conditional_within30fps_period=sum(r['finish_cycles'] <= 100_000_000 // 30 for r in group)))
        assert pins == {p: sha(ROOT / p) for p in pins}, 'sources changed during campaign'
        qualified_status = 'PASS_CONDITIONAL_CAUSAL_SCHEDULES' if args.cohort is None else 'PASS_CONDITIONAL_COHORT_SCHEDULES'
        report.update(status=qualified_status if not args.limit else 'PASS_SMOKE_ONLY',
                      native_frames=count, audited_schedules=len(rows), summaries=summaries,
                      artifacts_sha256={p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file() and p.name!='results.json'})
    except Exception as exc:
        report['failure'] = repr(exc)
        raise
    finally:
        report['wall_seconds'] = time.monotonic() - started
        (out / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
        print('PIPELINE_REPORT', out / 'results.json', report['status'], flush=True)


if __name__ == '__main__':
    main()
