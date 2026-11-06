#!/usr/bin/env python3
"""Necessary service budgets from frozen native traffic; not a timing simulator."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT/'experiments/python-gamebub-v82/execution/attempt-20261106T052617072164Z-c382bb87/g16-frames.jsonl'
OUT = Path(__file__).resolve().parent
DEADLINE = 1_000_000  # Assumed 100 MHz and exactly 10 ms.

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def stats(values):
    return dict(min=min(values), median=statistics.median(values), max=max(values), total=sum(values))

def main():
    rows = [json.loads(line) for line in SOURCE.read_text().splitlines()]
    assert len(rows) == 457
    assert len({(r['cohort'],r['fid']) for r in rows}) == 457
    expected = (119,119,119,100)
    assert tuple(sum(r['cohort']==c for r in rows) for c in range(4)) == expected
    detailed=[]
    configs = (
        dict(name='current_18r_16w', read=18, write=16, copy_write_elision=False),
        dict(name='hypothetical_service12', read=12, write=12, copy_write_elision=False),
        dict(name='counterfactual_copy_alias_18r_16w', read=18, write=16, copy_write_elision=True),
        dict(name='counterfactual_copy_alias_service12', read=12, write=12, copy_write_elision=True),
    )
    for r in rows:
        m=r['logical_BL8']
        assert m['reference_reads'] == r['reference_read_tiles']*4
        assert r['reference_read_tiles'] == sum(r[k] for k in ('decode_reference_tiles','materialize_copy_reference_tiles','mixed_leaf_hash_only_reference_tiles'))
        assert m['canonical_writes'] == r['physical_store_tiles']*4
        assert m['HUD_reads'] == m['HUD_writes'] == 2640
        assert m['total']==sum(m[k] for k in ('reference_reads','canonical_writes','HUD_reads','HUD_writes'))
        reads=m['reference_reads']+m['HUD_reads']; writes=m['canonical_writes']+m['HUD_writes']
        work=reads*18+writes*16
        assert work-18 == r['conditional_data_service_floor_cycles']
        # This is only a traffic counterfactual. No alias/lease/display path is implemented.
        avoidable_writes=4*r['materialize_copy_reference_tiles']
        assert 0<=avoidable_writes<=m['canonical_writes']
        for c in configs:
            w=writes-(avoidable_writes if c['copy_write_elision'] else 0)
            work=reads*c['read']+w*c['write']
            detailed.append(dict(configuration=c['name'],cohort=r['cohort'],fid=r['fid'],key=r['key'],
                                 root=r['root'],seal=r['seal'],reads_BL8=reads,writes_BL8=w,
                                 traffic_BL8=reads+w,memory_busy_cycles=work,
                                 no_reservation_necessary_ms=work/100000,
                                 reservation20_necessary_ms=work/80000,
                                 omitted_COPY_writes_BL8=writes-w,
                                 necessary_equal_service_max_cycles_no_reservation=DEADLINE/(reads+w),
                                 necessary_equal_service_max_cycles_reserved20=0.8*DEADLINE/(reads+w)))
    summaries=[]
    for c in configs:
        group=[r for r in detailed if r['configuration']==c['name']]
        maximum=max(group,key=lambda r:r['memory_busy_cycles'])
        summaries.append(dict(configuration=c['name'],sources=len(group),
                              traffic_BL8=stats([r['traffic_BL8'] for r in group]),
                              busy_cycles=stats([r['memory_busy_cycles'] for r in group]),
                              no_reservation_necessary_ms=stats([r['no_reservation_necessary_ms'] for r in group]),
                              reservation20_necessary_ms=stats([r['reservation20_necessary_ms'] for r in group]),
                              memory_work_strictly_within10ms_no_reservation=sum(r['memory_busy_cycles']<DEADLINE for r in group),
                              memory_work_strictly_within10ms_reserved20=sum(r['memory_busy_cycles']<0.8*DEADLINE for r in group),
                              maximum_work_witness=maximum))
    original=[r for r in detailed if r['configuration']==configs[0]['name']]
    cold=max(original,key=lambda r:r['traffic_BL8'])
    assert (cold['cohort'],cold['fid'],cold['traffic_BL8'])==(0,1,68904)
    assert cold['memory_busy_cycles']==1170192
    assert max(r['memory_busy_cycles'] for r in detailed if r['configuration']==configs[1]['name'])==826848
    assert next(r for r in detailed if r['configuration']==configs[2]['name'] and (r['cohort'],r['fid'])==(0,1))['memory_busy_cycles']==930064
    (OUT/'frames.jsonl').write_text(''.join(json.dumps(r,separators=(',',':'))+'\n' for r in detailed))
    report=dict(schema='cu66-v87-memory-service-necessary-budgets-v1',status='PASS_NECESSARY_TRAFFIC_ACCOUNTING',
                native_sources=457,configurations=configs,source_sha256={str(SOURCE.relative_to(ROOT)):sha(SOURCE),
                str(Path(__file__).resolve().relative_to(ROOT)):sha(Path(__file__).resolve()),
                'experiments/python-gamebub-v82/execution.py':sha(ROOT/'experiments/python-gamebub-v82/execution.py')},
                frames_sha256=sha(OUT/'frames.jsonl'),assumed_clock_MHz=100,deadline_ms=10,
                summaries=summaries,cold_witness=cold,
                equal_service_strict_required_cycles_per_BL8=dict(no_reservation=DEADLINE/68904,reserved20=0.8*DEADLINE/68904),
                qualification='Necessary aggregate service constraints only. Durations include completion service for every BL8; frozen V82 successor-gap floor omits final18cycles. No task scheduling, controller, row/refresh, physical target, continuous display or ingress qualification. 20% reservation division ignores fragmentation, so actual nonpreemptive service may be slower. Counterfactual COPY-write alias cases retain every reference read but remove nonresident COPY stores; correctness requires a new leased/indirect physical layout not implemented here.',
                physical_30fps_proven=False,validated_under10ms_proven=False)
    (OUT/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    print('V87_MEMORY_NECESSARY_BUDGET_PASS sources=457 scenarios=4')
    for r in summaries:
        print(r['configuration'],'max_ms=',r['no_reservation_necessary_ms']['max'],'reserved20=',r['reservation20_necessary_ms']['max'],'strict_memory10=',r['memory_work_strictly_within10ms_reserved20'])

if __name__=='__main__':
    main()
