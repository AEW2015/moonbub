#!/usr/bin/env python3
"""Combine native entropy observations with finite staging-credit DAGs."""
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
AREA = ROOT / 'experiments/python-gamebub-v84'
NATIVE = ROOT / 'experiments/python-gamebub-v82/native'
ENTROPY = AREA / 'entropy'
CONTROL = ROOT / 'experiments/python-gamebub-v82/execution/attempt-20261106T052617072164Z-c382bb87/g16-frames.jsonl'
V83 = ROOT / 'experiments/python-gamebub-v83/summary.json'
RESERVED = dict(period=10000, blocked=[(0, 2000)])
LOW = dict(decisions=2, renorm=2, stream_bytes=2, rice_values=1, events=1,
           raw_bytes=2, header_bytes=2, crc_bytes=2, emits=1, raw_bits=1, prob_init=1)
HIGH = dict(decisions=4, renorm=4, stream_bytes=4, rice_values=1, events=1,
            raw_bytes=4, header_bytes=4, crc_bytes=4, emits=1, raw_bits=2, prob_init=1)
CONFIGS = [
    dict(name='v83_control', slots=None, weights=None, read_gap=18, write_gap=16, windows=None),
    dict(name='credits64_zero_arrival', slots=64, weights=None, read_gap=18, write_gap=16, windows=None),
    dict(name='credits8_zero_arrival', slots=8, weights=None, read_gap=18, write_gap=16, windows=None),
    dict(name='credits2_zero_arrival', slots=2, weights=None, read_gap=18, write_gap=16, windows=None),
    dict(name='credits8_primitive_low', slots=8, weights=LOW, read_gap=18, write_gap=16, windows=None),
    dict(name='credits8_primitive_high', slots=8, weights=HIGH, read_gap=18, write_gap=16, windows=None),
    dict(name='credits8_low_reserved20', slots=8, weights=LOW, read_gap=18, write_gap=16, windows=RESERVED),
    dict(name='credits8_low_service12_reserved20', slots=8, weights=LOW, read_gap=12, write_gap=12, windows=RESERVED),
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
    parser.add_argument('--limit', type=int, default=0)
    parser.add_argument('--cohort', type=int, choices=range(4))
    args = parser.parse_args()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA / 'campaigns' / f'attempt-{stamp}-{uuid.uuid4().hex[:8]}'
    out.mkdir(parents=True)
    previous = json.loads(V83.read_text())
    previous_rows = []
    control_paths = []
    for name in previous['evidence_sha256']:
        if name.endswith('/results.json'):
            path = (ROOT / name).with_name('frames.jsonl')
            control_paths.append(path)
            previous_rows += [json.loads(line) for line in path.read_text().splitlines()]
    previous_control = {(r['cohort'], r['fid']):r for r in previous_rows
                        if r['configuration'] == 'bounded_groups_current_hash1'}
    assert len(previous_control) == 457
    entropy_index = json.loads((ENTROPY / 'index.json').read_text())
    sources = [Path(__file__).resolve(), AREA/'audit.py', AREA/'credits.py',
               ROOT/'experiments/python-gamebub-v83/workload.py', ROOT/'experiments/python-gamebub-v83/scheduler.py',
               ROOT/'experiments/python-gamebub-v83/audit.py', ROOT/'scripts/cu66-v82/prototype_commitment.py',
               ROOT/'experiments/python-gamebub-v82/execution.py',
               ROOT/'fpga/experiments/cu66-v81/residency/model.py', NATIVE/'data.py', NATIVE/'index.json',
               ENTROPY/'data.py', ENTROPY/'index.json', ENTROPY/entropy_index['data']['path'],
               CONTROL, V83, *control_paths]
    sources += sorted((NATIVE/'data').glob('*.gz'))
    pins = {str(p.relative_to(ROOT)):sha(p) for p in sources}
    with tarfile.open(out/'sources.tar.gz', 'w:gz') as tar:
        for path in sources:
            if path.suffix != '.gz':
                tar.add(path, arcname=str(path.relative_to(ROOT)), recursive=False)
    report = dict(schema='cu66-v84-entropy-credit-campaign-v1', status='FAIL', configurations=CONFIGS,
                  source_sha256=pins, source_archive_sha256=sha(out/'sources.tar.gz'), cohort=args.cohort,
                  smoke_limit=args.limit, clock_mhz_assumption=100,
                  timing_is_physical=False, rtl_changed=False, esp32_simulated=False,
                  limitations=[
                      'Native primitive counts are observed; their clock weights and inverse/reconstruction64 cycles are assumptions, not timing bounds.',
                      'Encoded input fully present at release; no Wi-Fi/QSPI/ESP32/CPU/GUI transport model.',
                      'Sequential entropy production is backpressured by group and coefficient credits; no current-RTL cycle equivalence.',
                      'COPY still pays existing AB38 entropy work; deleting it requires a new encoder/profile.',
                      '20% reserved windows restart phase0 per source; no continuous LCD/refresh/deadline model.',
                      'Memory intervals aggregate BL8 costs without row/direction/controller timing.',
                      'COPY transfer ports, dequant/inverse working state, RAM rounding, finite descriptor/ready queues and CDC unpriced.',
                      'Four histories from one walkthrough family; no sustained30fps or full validated under10ms proof.'])
    started = time.monotonic()
    try:
        native = load('cu84_native', NATIVE/'data.py')
        entropy = load('cu84_entropy', ENTROPY/'data.py')
        commitment = load('cu84_tree', ROOT/'scripts/cu66-v82/prototype_commitment.py')
        residency = load('cu84_residency', ROOT/'fpga/experiments/cu66-v81/residency/model.py')
        cost = load('cu84_cost', ROOT/'experiments/python-gamebub-v82/execution.py')
        workload = load('cu84_workload', ROOT/'experiments/python-gamebub-v83/workload.py')
        scheduler = load('cu84_scheduler', ROOT/'experiments/python-gamebub-v83/scheduler.py')
        generic_audit = load('cu84_generic_audit', ROOT/'experiments/python-gamebub-v83/audit.py')
        credits = load('cu84_credits', AREA/'credits.py')
        credit_audit = load('cu84_credit_audit', AREA/'audit.py')
        controls = [json.loads(line) for line in CONTROL.read_text().splitlines()]
        rows, old_cohort, processed = [], None, 0
        with (out/'frames.jsonl').open('w') as stream:
            for n, (original, observed) in enumerate(zip(native.iter_frames(), entropy.iter_frames(), strict=True)):
                for key in ('cohort', 'ordinal', 'fid', 'key', 'packet_sha256', 'canonical_sha256', 'hud_sha256', 'display_sha256'):
                    assert original[key] == observed[key]
                assert observed['zero_mask'] == ''.join(str(v) for v in original['zero_coeff_mask'])
                if args.cohort is not None and original['cohort'] != args.cohort:
                    continue
                if args.limit and processed >= args.limit:
                    break
                frame = dict(original, generation=original['ordinal']+1)
                if old_cohort != frame['cohort']:
                    model = residency.Residency(8100)
                    tree = commitment.CommitmentTree(granularity=16)
                    old_cohort = frame['cohort']
                candidate = 0 if model.reference is None else (model.reference+1)%3
                elided = [not frame['key'] and bool(frame['same_mask'][i]) and bool(model.masks[i] & (1<<candidate)) for i in range(8100)]
                plan = tree.plan(frame, frame['copy_ref_mask'])
                control = controls[n]
                assert (frame['cohort'], frame['fid']) == (control['cohort'], control['fid'])
                assert (plan['root'].hex(), plan['seal'].hex()) == (control['root'], control['seal'])
                account = cost.account(frame, elided, plan)
                assert account['logical_BL8'] == control['logical_BL8'] and account['metadata'] == control['metadata']
                model.begin(frame['fid'], frame['packet_sha256'], candidate, frame['key'], frame['tiles'], frame['same_mask'])
                model.step();model.commit(authenticated=True);tree.commit(plan);model.present()
                assert model.banks[model.reference] == frame['tiles']
                native_totals = {field:sum(t[field] for t in observed['tile_work']) for field in entropy.FIELDS}
                for config in CONFIGS:
                    base = workload.build(frame, elided, plan, inverse_cycles=64, reconstruct_cycles=64,
                                          read_gap=config['read_gap'], write_gap=config['write_gap'], group_slots=4)
                    tile_costs = [sum(tile[k]*v for k,v in config['weights'].items()) for tile in observed['tile_work']] if config['weights'] else [0]*8100
                    slots = config['slots']
                    work = credits.augment(base, tile_costs, ref_slots=slots, inverse_slots=slots, coefficient_slots=slots) if slots else base
                    capacities = dict(memory=1, inverse=1, reconstruct=1, hash=1, tree_r=1, tree_w=1, map_r=1, map_w=1, entropy=1)
                    result = scheduler.schedule(work['jobs'], capacities, memory_windows=config['windows'], retain_timeline=True)
                    audited = generic_audit.verify(work['jobs'], result['timeline'], capacities, config['windows'], work['groups'], 4)
                    lifetimes = credit_audit.verify(work, result['timeline'], ref_slots=slots, inverse_slots=slots, coefficient_slots=slots) if slots else None
                    if slots:
                        check = credits.audit_lifetimes(work, result['timeline'])
                        for name, other in (('reference','reference'),('inverse','inverse'),('coefficient','coefficients')):
                            assert lifetimes['stages'][name]['peak_slots'] == check[other]['peak_reserved_slots']
                    assert result['finish_cycles'] == audited['finish_cycles'] == result['finish_by_id'][work['complete']]
                    if config['name']=='v83_control':
                        assert result['finish_cycles'] == previous_control[(frame['cohort'], frame['fid'])]['finish_cycles']
                    expected_memory = ((account['logical_BL8']['reference_reads']+2640)*config['read_gap'] + (account['logical_BL8']['canonical_writes']+2640)*config['write_gap'])
                    assert audited['resource_work_cycles']['memory'] == expected_memory
                    assert audited['resource_work_cycles']['hash'] == account['hash_compression_blocks']*64
                    assert audited['resource_work_cycles'].get('entropy',0) == sum(tile_costs)
                    for r, capacity in capacities.items():
                        assert result['finish_cycles'] >= (audited['resource_work_cycles'].get(r,0)+capacity-1)//capacity
                    compact_counts = {k:v for k,v in work['counts'].items() if k not in ('group_starts','group_releases')}
                    row = dict(configuration=config['name'], cohort=frame['cohort'], ordinal=frame['ordinal'], fid=frame['fid'], key=frame['key'],
                               root=plan['root'].hex(), seal=plan['seal'].hex(), finish_cycles=result['finish_cycles'], model_ms=result['finish_cycles']*1e-5,
                               counts=compact_counts, audit=audited, staging=lifetimes,
                               native_entropy_totals=native_totals, entropy_work_cycles=sum(tile_costs),
                               timeline_sha256=hashlib.sha256(json.dumps(result['timeline'],sort_keys=True,separators=(',',':')).encode()).hexdigest())
                    stream.write(json.dumps(row,separators=(',',':'))+'\n');rows.append(row)
                    if frame['cohort']==0 and frame['ordinal'] in (0,1) and config['name'] in ('credits8_primitive_low','credits2_zero_arrival'):
                        with gzip.open(out/f"witness-c0-f{frame['fid']}-{config['name']}.json.gz",'wt') as f:
                            json.dump(dict(config=config,capacities=capacities,workload=work,result=result,audit=audited,staging=lifetimes),f,separators=(',',':'))
                processed += 1
                if processed==1 or processed%10==0:
                    print(f'V84_PIPELINE_PROGRESS cohort={args.cohort} frames={processed} schedules={len(rows)} wall={time.monotonic()-started:.1f}s',flush=True)
        expected = (119,119,119,100)[args.cohort] if args.cohort is not None else 457
        assert processed == (args.limit or expected)
        summaries = []
        for config in CONFIGS:
            for key in (True,False,None):
                group = [r for r in rows if r['configuration']==config['name'] and (key is None or r['key']==key)]
                if group:
                    summaries.append(dict(configuration=config['name'],key=key,sources=len(group),model_ms=stat([r['model_ms'] for r in group]),
                                          entropy_work_ms=stat([r['entropy_work_cycles']*1e-5 for r in group]),
                                          conditional_under10ms=sum(r['finish_cycles']<1_000_000 for r in group),
                                          conditional_within30fps_period=sum(r['finish_cycles']<=100_000_000//30 for r in group)))
        assert pins == {name:sha(ROOT/name) for name in pins}, 'executed input/source mutation'
        report.update(status='PASS_SMOKE_ONLY' if args.limit else 'PASS_CONDITIONAL_COHORT_SCHEDULES',native_sources=processed,schedules=len(rows),summaries=summaries,
                      artifacts_sha256={p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file() and p.name!='results.json'})
    except BaseException as exc:
        report['failure']=repr(exc)
        raise
    finally:
        report['wall_seconds']=time.monotonic()-started
        (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
        print('V84_PIPELINE_REPORT',out/'results.json',report['status'],flush=True)


if __name__=='__main__':
    main()
