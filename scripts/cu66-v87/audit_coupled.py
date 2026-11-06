#!/usr/bin/env python3
"""Independent retained-timeline audit for the V87 prospective coupled graph.

No scheduler or graph-builder functions are called. This checks the supplied
job DAG, independently infers tile consumers, and measures finite reservations.
It is not a hardware or arithmetic-correctness test.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import gzip
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


def highwater(intervals, capacity=None):
    points=[]
    for start,finish in intervals:
        assert type(start)is int and type(finish)is int and 0<=start<=finish
        if finish>start:points.extend(((start,1),(finish,-1)))
    live=peak=0
    for _,delta in sorted(points):
        live+=delta;assert live>=0
        if capacity is not None:assert live<=capacity,('capacity',live,capacity)
        peak=max(peak,live)
    assert live==0
    return peak


def verify(work,timeline,capacities,windows=None,*,group_slots=4):
    jobs=work['jobs'];by_id={j['id']:j for j in jobs};rows={r['id']:r for r in timeline}
    assert len(by_id)==len(jobs)==len(rows)==len(timeline)
    assert by_id.keys()==rows.keys()
    assert all(type(cap)is int and cap>0 for cap in capacities.values())
    outgoing={i:[] for i in by_id};degree={}
    for ident,j in by_id.items():
        assert len(set(j['deps']))==len(j['deps'])
        assert all(dep in by_id for dep in j['deps'])
        degree[ident]=len(j['deps'])
        for dep in j['deps']:outgoing[dep].append(ident)
    ready=[i for i,n in degree.items()if n==0];seen=0
    while ready:
        ident=ready.pop();seen+=1
        for child in outgoing[ident]:
            degree[child]-=1
            if degree[child]==0:ready.append(child)
    assert seen==len(jobs),'cyclic graph'
    resource_intervals=defaultdict(list);resource_work=defaultdict(int)
    typed=defaultdict(dict)
    for ident,j in by_id.items():
        r=rows[ident];assert r['resource']==j['resource']
        assert type(j['duration'])is int and j['duration']>=0
        assert type(r['start'])is int and type(r['finish'])is int and r['start']>=0
        assert r['finish']-r['start']==j['duration'],('duration',ident)
        assert len(set(j['deps']))==len(j['deps'])
        assert all(dep in by_id and rows[dep]['finish']<=r['start'] for dep in j['deps']),('dependency',ident)
        if j['resource'] is not None:
            assert j['resource'] in capacities
            resource_work[j['resource']]+=j['duration']
            resource_intervals[j['resource']].append((r['start'],r['finish']))
        if 'tile'in j and j['kind'] not in ('context_fetch','context_compute'):
            assert j['tile']not in typed[j['kind']],('duplicate tile stage',j['kind'])
            typed[j['kind']][j['tile']]=j
        if windows and j['resource']=='memory' and r['finish']>r['start']:
            period=windows['period']
            for n in range(r['start']//period,(r['finish']-1)//period+1):
                assert all(r['finish']<=n*period+lo or r['start']>=n*period+hi for lo,hi in windows['blocked']),('reserved memory window',ident)
    peaks={r:highwater(iv,capacities[r]) for r,iv in resource_intervals.items()}
    # Publication must depend on every priced operation, irrespective of one
    # scheduler's accidental execution order.
    visited=set();pending=[work['complete']]
    while pending:
        i=pending.pop()
        if i not in visited:
            visited.add(i);pending.extend(by_id[i]['deps'])
    assert visited==by_id.keys(),'unfenced operation'
    finish=max((r['finish']for r in timeline),default=0)
    assert rows[work['complete']]['finish']==finish
    front=work['frontend'];count=len(front['setups']);window=front['window']
    assert len(front['emits'])==len(front['consumers'])==count
    assert set(typed['map_lookup'])==set(typed['shared_setup'])==set(typed['tile_emit'])==set(typed['coefficient_arrival'])==set(range(count))
    assert window==work['credits']['capacities']['coefficients']
    context_fetch={};context_compute={}
    for j in jobs:
        if j['kind'] in ('context_fetch','context_compute'):
            key=(j['tile'],j['context']);target=context_fetch if j['kind']=='context_fetch' else context_compute
            assert key not in target;target[key]=j
    assert set(context_fetch)==set(context_compute)=={(t,c)for t in range(count)for c in range(4)}
    prev_setup=None;prev_emit=None;last_context=[None]*4
    inferred_coeff=[]
    for tile in range(count):
        setup=typed['shared_setup'][tile];emit=typed['tile_emit'][tile];arrival=typed['coefficient_arrival'][tile];lookup=typed['map_lookup'][tile]
        assert setup['id']==front['setups'][tile] and emit['id']==front['emits'][tile]
        assert setup['resource']=='fetch' and emit['resource']=='emit'
        group=lookup['group'];assert setup['group']==group
        assert work['groups'][group]['start']in setup['deps']
        assert front['metadata']in setup['deps']
        if prev_setup is not None:assert prev_setup in setup['deps']
        if prev_emit is not None:assert prev_emit in emit['deps']
        computes=[]
        for context in range(4):
            fetch=context_fetch[tile,context];compute=context_compute[tile,context]
            assert fetch['resource']=='fetch' and compute['resource']=='arithmetic'
            assert setup['id']in fetch['deps'] and fetch['id']in compute['deps']
            if last_context[context]is not None:assert last_context[context]in fetch['deps']
            assert compute['id']in emit['deps']
            last_context[context]=compute['id'];computes.append(compute['id'])
        assert arrival['duration']==0 and arrival['resource']is None
        assert emit['id']in arrival['deps'] and arrival['id']in lookup['deps']
        consumer=typed['inverse'].get(tile,lookup)
        assert consumer['id']==front['consumers'][tile]
        if tile>=window:
            assert front['consumers'][tile-window]in setup['deps'],'coefficient release must be consumer, not emitter'
        inferred_coeff.append((setup,consumer))
        if tile in typed['dequant']:
            quant=typed['dequant'][tile]
            assert arrival['id']in quant['deps'] and quant['id']in consumer['deps']
        prev_setup=setup['id'];prev_emit=emit['id']
    constraints=work['credits']['constraints'];stages={}
    for name,producer_kind in (('reference','reference_read'),('inverse','inverse'),('coefficients','shared_setup')):
        inferred=inferred_coeff if name=='coefficients'else[(j,typed['reconstruct'].get(tile,typed['copy_ready'].get(tile)))for tile,j in sorted(typed[producer_kind].items())]
        records=constraints[name];capacity=work['credits']['capacities'][name]
        assert len(records)==len(inferred)
        intervals=[]
        for n,((producer,consumer),record)in enumerate(zip(inferred,records,strict=True)):
            assert consumer is not None
            assert producer['tile']==consumer['tile']==record['tile']
            assert record['producer']==producer['id'] and record['consumer']==consumer['id']
            prior=None if n<capacity else inferred[n-capacity][1]['id']
            assert record['release_before_production']==prior
            if prior is not None:assert prior in producer['deps']
            assert rows[consumer['id']]['finish']>=rows[producer['id']]['finish']
            intervals.append((rows[producer['id']]['start'],rows[consumer['id']]['finish']))
        stages[name]=dict(reservations=len(intervals),capacity=capacity,peak=highwater(intervals,capacity))
    groups=[]
    for gi,g in enumerate(work['groups']):
        assert by_id[g['start']]['kind']=='group_start' and by_id[g['release']]['kind']=='group_release'
        if gi>=group_slots:assert work['groups'][gi-group_slots]['release']in by_id[g['start']]['deps']
        groups.append((rows[g['start']]['start'],rows[g['release']]['finish']))
    group_peak=highwater(groups,group_slots)
    # A materialized 64xsigned32 dequant result is an additional 256B object.
    # Its ownership interval is contained by the retained coefficient credit,
    # so <=window such objects can be live without changing scheduling edges.
    dequant_intervals=[]
    for tile,quant in typed['dequant'].items():
        setup=typed['shared_setup'][tile];inverse=typed['inverse'][tile]
        assert rows[setup['id']]['start']<=rows[quant['id']]['start']
        assert rows[quant['id']]['finish']<=rows[inverse['id']]['start']
        dequant_intervals.append((rows[quant['id']]['start'],rows[inverse['id']]['finish']))
    dequant_peak=highwater(dequant_intervals,window)
    logical_bytes=dict(reference=work['credits']['capacities']['reference']*64,
                       inverse=work['credits']['capacities']['inverse']*192,
                       coefficients=window*128,output_groups=group_slots*16*64,
                       materialized_dequant_results=(window*256 if dequant_intervals else 0))
    # Exact frontend resource totals, independent of the builder's arithmetic.
    totals={r:sum(j['duration']for j in jobs if j['resource']==r)for r in ('fetch','arithmetic','emit')}
    assert totals==front['work_cycles']
    return dict(status='PASS_INDEPENDENT_COUPLED_TIMELINE_AUDIT',jobs=len(jobs),tile_count=count,
                timeline_sha256=hashlib.sha256(json.dumps(timeline,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
                finish_cycles=finish,resource_work_cycles=dict(sorted(resource_work.items())),
                resource_peaks=peaks,stages=stages,group_peak=group_peak,
                complete_fence_covers_all_jobs=True,context_order_and_consumer_release=True,
                dequant_staging=dict(reservations=len(dequant_intervals),peak_slots=dequant_peak,
                                     assumed_bytes_per_materialized_result=256,
                                     ownership='Dequant producer start through inverse consumer finish; subset of coefficient-credit lifetime.'),
                logical_stage_reservation_bytes=logical_bytes,
                total_logical_stage_reservation_bytes=sum(logical_bytes.values()),
                storage_scope='Logical staging only; original coefficients and materialized signed32 dequant results coexist conservatively. Tree/maps, engine working registers, ports, transport and physical RAM rounding are extra.')


def main():
    p=argparse.ArgumentParser();p.add_argument('witness',nargs='+');p.add_argument('--output',required=True);a=p.parse_args()
    results=[]
    for name in a.witness:
        path=Path(name)
        opener=gzip.open if path.suffix=='.gz'else open
        with opener(path,'rt')as f:d=json.load(f)
        config=d.get('config',{})
        windows=d.get('windows',config.get('windows'))
        result=verify(d.get('workload',d.get('work')),d['result']['timeline'],d['capacities'],windows)
        results.append(dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),audit=result))
    out=dict(schema='cu66-v87-independent-coupled-audit-v1',status='PASS',auditor_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),witnesses=results,
             scope='Independent supplied job/timeline/consumer-lifetime audit, not arithmetic or hardware timing qualification.')
    Path(a.output).write_text(json.dumps(out,indent=2)+'\n');print('V87_INDEPENDENT_COUPLED_AUDIT_PASS witnesses='+str(len(results)))

if __name__=='__main__':main()
