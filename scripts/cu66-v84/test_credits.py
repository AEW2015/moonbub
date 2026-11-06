#!/usr/bin/env python3
"""Directed construction, finite-credit and native V84 wrapper tests."""
from __future__ import annotations
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v84'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    credits = load('cu84_credit_tests', AREA/'credits.py')
    workload = load('cu84_base_workload', ROOT/'experiments/python-gamebub-v83/workload.py')
    scheduler = load('cu84_base_scheduler', ROOT/'experiments/python-gamebub-v83/scheduler.py')
    audit = load('cu84_base_audit', ROOT/'experiments/python-gamebub-v83/audit.py')
    commitment = load('cu84_base_commitment', ROOT/'scripts/cu66-v82/prototype_commitment.py')
    residency = load('cu84_base_residency', ROOT/'fpga/experiments/cu66-v81/residency/model.py')
    native = load('cu84_base_native', ROOT/'experiments/python-gamebub-v82/native/data.py')
    checks = []
    cases = []
    capacities = dict(memory=1, inverse=1, reconstruct=1, hash=1,
                      tree_r=1, tree_w=1, map_r=1, map_w=1, entropy=1)

    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        checks.append(name)

    def reject(name, fn):
        try:
            fn()
        except (ValueError, KeyError, TypeError):
            checks.append(name)
        else:
            raise AssertionError('accepted invalid credits: '+name)

    def exercise(base, costs, slots, label):
        snapshot = copy.deepcopy(base)
        w = credits.augment(base, costs, ref_slots=slots,
                            inverse_slots=slots, coefficient_slots=slots)
        check(label+' input-unchanged', base == snapshot)
        by_id = {j['id']:j for j in w['jobs']}
        check(label+' old-ids-kinds-durations-resources-preserved', all(
            all(by_id[j['id']][field] == j[field] for field in ('kind','duration','resource'))
            and set(j['deps']) <= set(by_id[j['id']]['deps']) for j in base['jobs']))
        check(label+' old-priced-counts-preserved', all(
            w['counts'][k] == v for k,v in base['counts'].items() if k != 'task_count'))
        check(label+' arrivals-and-work-accounted',
              w['counts']['entropy_tiles'] == len(costs)
              and w['counts']['entropy_work_cycles'] == sum(costs)
              and w['counts']['task_count'] == len(base['jobs'])+len(costs))
        entropy = {j['tile']:j for j in w['jobs'] if j['kind']=='entropy_tile'}
        lookup = {j['tile']:j for j in w['jobs'] if j['kind']=='map_lookup'}
        inverse = {j['tile']:j for j in w['jobs'] if j['kind']=='inverse'}
        reads = {j['tile']:j for j in w['jobs'] if j['kind']=='reference_read'}
        recon = {j['tile']:j for j in w['jobs'] if j['kind']=='reconstruct'}
        copy_ready = {j['tile']:j for j in w['jobs'] if j['kind']=='copy_ready'}
        check(label+' map-waits-for-own-mode', all(entropy[t]['id'] in j['deps'] for t,j in lookup.items()))
        check(label+' entropy-serial-group-gated', all(
            w['groups'][j['group']]['start'] in j['deps'] and
            (t==0 or entropy[t-1]['id'] in j['deps']) for t,j in entropy.items()))
        expected = dict(
            reference=[(t, j['id'], (recon[t] if t in recon else copy_ready[t])['id'],64) for t,j in sorted(reads.items())],
            inverse=[(t,j['id'],recon[t]['id'],192) for t,j in sorted(inverse.items())],
            coefficients=[(t,j['id'],(inverse[t] if t in inverse else lookup[t])['id'],128) for t,j in sorted(entropy.items())])
        check(label+' independently-bound-consumers', all(
            [(r['tile'],r['producer'],r['consumer'],r['bytes']) for r in w['credits']['constraints'][kind]]==records
            for kind,records in expected.items()))
        check(label+' fifo-credit-edges', all(
            r['release_before_production'] == (None if i<slots else records[i-slots]['consumer'])
            and (i<slots or records[i-slots]['consumer'] in by_id[r['producer']]['deps'])
            for records in w['credits']['constraints'].values() for i,r in enumerate(records)))
        result = scheduler.schedule(w['jobs'], capacities, retain_timeline=True)
        common = audit.verify(w['jobs'],result['timeline'],capacities,
                              groups=w['groups'],group_slots=w['assumptions']['group_slots'])
        lifetimes = credits.audit_lifetimes(w,result['timeline'])
        check(label+' every-declared-edge-time-causal', common['finish_cycles']==result['finish_cycles'])
        check(label+' bounded-intermediate-reservations', all(r['peak_reserved_slots']<=slots for r in lifetimes.values()))
        check(label+' entropy-work-exact', result['resources']['entropy']['work_cycles']==sum(costs))
        check(label+' complete-after-every-operation',result['finish_by_id'][w['complete']]==result['finish_cycles'])
        size = w['counts']['group_payload_buffer_bytes']+slots*(64+192+128)
        check(label+' explicit-logical-reservation-bytes',w['credits']['total_logical_stage_reservations_bytes']==size)
        cases.append(dict(label=label,slots=slots,tiles=len(costs),finish_cycles=result['finish_cycles'],
                          entropy_work_cycles=sum(costs),lifetimes=lifetimes,
                          reserved_bytes=w['credits']['total_logical_stage_reservations_bytes']))
        return w,result

    geometry = (40,8,5,3,2)
    hidden=bytes(int(i in (4,7,9)) for i in range(10))
    pixels=[bytes([128 if h else i+1])*64 for i,h in enumerate(hidden)]
    tree=commitment.CommitmentTree(granularity=4,geometry=geometry)
    model=residency.Residency(10)
    bases=[]
    for ordinal,change in enumerate((None,1,None,None,2,None)):
        key=ordinal==0
        previous=list(pixels)
        if change is not None:
            pixels[change]=bytes([50+ordinal])*64
        same=bytes(int(a==b) for a,b in zip(previous,pixels)) if not key else bytes(10)
        copy_mask=bytes(int(not key and not hidden[t] and same[t]) for t in range(10))
        frame=dict(fid=ordinal,refid=0xffffffff if key else ordinal-1,key=key,generation=ordinal+1,
                   geometry=geometry,tiles=list(pixels),hidden_mask=hidden,copy_ref_mask=copy_mask,same_mask=same,hud=b'test-hud')
        candidate=0 if model.reference is None else (model.reference+1)%3
        elided=[not key and bool(same[t]) and bool(model.masks[t]&(1<<candidate)) for t in range(10)]
        plan=tree.plan(frame,copy_mask)
        base=workload.build(frame,elided,plan,granularity=4,group_slots=4,hud_blocks=11,
                            inverse_cycles=64,reconstruct_cycles=64)
        bases.append(base)
        for slots in (1,2,4,8,64):
            exercise(base,[1+(i*7+ordinal)%19 for i in range(10)],slots,f'synthetic-{ordinal}-slots{slots}')
        model.begin(ordinal,str(ordinal),candidate,key,pixels,same)
        model.step();model.commit();model.present();tree.commit(plan)
    base=bases[1]
    wrapped,result=exercise(base,[0]*10,64,'zero-arrival-control')
    baseline=scheduler.schedule(base['jobs'],{k:v for k,v in capacities.items() if k!='entropy'},retain_timeline=True)
    check('synthetic-zero64-equals-base',baseline['finish_cycles']==result['finish_cycles'])
    delayed,_=exercise(base,[200]*10,2,'front-end-backpressure')
    r=scheduler.schedule(delayed['jobs'],capacities,retain_timeline=True)
    entropy=[j for j in delayed['jobs'] if j['kind']=='entropy_tile']
    starts={j['id']:j['start'] for j in r['timeline']}
    finish={j['id']:j['finish'] for j in r['timeline']}
    check('mode-arrival-positive-and-serial',all(finish[j['id']]>=200*(i+1) for i,j in enumerate(entropy)))
    tampered=copy.deepcopy(r['timeline'])
    record=delayed['credits']['constraints']['coefficients'][2]
    for row in tampered:
        if row['id']==record['producer']:
            row['start']=0
    reject('reject-premature-coefficient-credit-reuse',lambda:credits.audit_lifetimes(delayed,tampered))
    reject('reject-zero-capacity',lambda:credits.augment(base,[0]*10,ref_slots=0))
    reject('reject-bool-capacity',lambda:credits.augment(base,[0]*10,inverse_slots=True))
    reject('reject-short-costs',lambda:credits.augment(base,[0]*9))
    reject('reject-negative-cost',lambda:credits.augment(base,[-1]+[0]*9))
    reject('reject-bool-cost',lambda:credits.augment(base,[True]+[0]*9))
    bad=copy.deepcopy(base);bad['jobs'][-1]['deps'].append(bad['complete'])
    reject('reject-cyclic-input',lambda:credits.augment(bad,[0]*10))
    model=None;tree=None
    native_frames=0
    for original in native.iter_frames():
        if native_frames==8:
            break
        frame=dict(original,generation=original['ordinal']+1)
        if model is None:
            model=residency.Residency(8100);tree=commitment.CommitmentTree(granularity=16)
        candidate=0 if model.reference is None else (model.reference+1)%3
        elided=[not frame['key'] and bool(frame['same_mask'][i]) and bool(model.masks[i]&(1<<candidate)) for i in range(8100)]
        plan=tree.plan(frame,frame['copy_ref_mask'])
        base=workload.build(frame,elided,plan,group_slots=4,inverse_cycles=64,reconstruct_cycles=64)
        _,r=exercise(base,[1+(i%13) for i in range(8100)],8,f'native-{native_frames}-slots8')
        if native_frames in (0,1):
            _,zero=exercise(base,[0]*8100,64,f'native-{native_frames}-zero64')
            old=scheduler.schedule(base['jobs'],{k:v for k,v in capacities.items() if k!='entropy'})
            check(f'native-{native_frames}-zero64-equals-base',old['finish_cycles']==zero['finish_cycles'])
        model.begin(frame['fid'],frame['packet_sha256'],candidate,frame['key'],frame['tiles'],frame['same_mask'])
        model.step();model.commit();model.present();tree.commit(plan)
        native_frames+=1
    paths=[Path(__file__).resolve(),AREA/'credits.py',ROOT/'experiments/python-gamebub-v83/workload.py',
           ROOT/'experiments/python-gamebub-v83/scheduler.py',ROOT/'experiments/python-gamebub-v83/audit.py',
           ROOT/'scripts/cu66-v82/prototype_commitment.py',ROOT/'fpga/experiments/cu66-v81/residency/model.py',
           ROOT/'experiments/python-gamebub-v82/native/data.py',ROOT/'experiments/python-gamebub-v82/native/index.json']
    report=dict(schema='cu66-v84-credit-tests-v1',status='PASS',checks=len(checks),check_names=checks,
                cases=cases,native_frames=native_frames,synthetic_frames=6,
                source_sha256={str(p.relative_to(ROOT)):digest(p) for p in paths},
                scope='Directed FIFO/admission/lifetime construction tests and native-count preservation; no physical timing or ESP32 throughput proof.')
    (AREA/'credits-tests.json').write_text(json.dumps(report,indent=2)+'\n')
    print('V84_CREDITS_TESTS_PASS',len(checks),'native',native_frames,'cases',len(cases))


if __name__=='__main__':
    main()
