#!/usr/bin/env python3
"""All eight real CS88 masks on four selected bounded alias workloads."""
from __future__ import annotations
import datetime,gzip,hashlib,importlib.util,json,statistics,sys,time,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];AREA=ROOT/'experiments/python-gamebub-v90/exact'
SELECTED={(0,0),(0,1),(0,3),(3,50)}


def load(name,p):
    s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stats(values):return dict(min=min(values),median=statistics.median(values),max=max(values),total=sum(values))


def main():
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=AREA/'attempts'/(stamp+'-'+uuid.uuid4().hex[:8]);out.mkdir(parents=True)
    data=load('v90_exact_actual',ROOT/'experiments/python-gamebub-v90/policy/data.py')
    repricer=load('v90_exact_pricer',ROOT/'experiments/python-gamebub-v89/joint/model.py')
    alias=load('v90_exact_alias',ROOT/'experiments/python-gamebub-v88/alias/probe.py')
    scheduler=load('v90_exact_scheduler',ROOT/'experiments/python-gamebub-v83/scheduler.py')
    independent=load('v90_exact_independent',ROOT/'scripts/cu66-v87/audit_coupled.py')
    credits=load('v90_exact_credits',ROOT/'experiments/python-gamebub-v84/credits.py')
    old=json.loads((ROOT/'experiments/python-gamebub-v88/alias/probe.json').read_text())
    oldjoint=json.loads((ROOT/'experiments/python-gamebub-v89/joint/results.json').read_text());oldpath=ROOT/oldjoint['selected_report']
    oldrows=[r for r in map(json.loads,oldpath.with_name('rows.jsonl').read_text().splitlines()) if r['alias']]
    qualified=json.loads((ROOT/'experiments/python-gamebub-v88/wire/results.json').read_text());wirepath=ROOT/qualified['selected_report']
    candidate_path=wirepath.with_name('candidates.jsonl')
    candidates={(r['cohort'],r['fid'],r['mask']):r for r in map(json.loads,candidate_path.read_text().splitlines())}
    assert len(candidates)==3656
    originals={};snapshots={};sources=[Path(__file__).resolve(),ROOT/'experiments/python-gamebub-v90/policy/data.py',
        ROOT/'experiments/python-gamebub-v89/joint/model.py',ROOT/'experiments/python-gamebub-v89/observations/data.py',
        ROOT/'experiments/python-gamebub-v89/observations/index.json',ROOT/'experiments/python-gamebub-v88/alias/probe.py',
        ROOT/'experiments/python-gamebub-v88/alias/probe.json',ROOT/'experiments/python-gamebub-v83/scheduler.py',
        ROOT/'scripts/cu66-v87/audit_coupled.py',ROOT/'experiments/python-gamebub-v84/credits.py',oldpath,oldpath.with_name('rows.jsonl'),
        wirepath,candidate_path]
    for r in old['rows']:
        p=ROOT/r['witness'];sources.append(p)
        with gzip.open(p,'rt') as f:w=json.load(f)
        source=ROOT/w['source_witness'];trace=ROOT/w['source_trace'];sources.extend((source,trace))
        with gzip.open(source,'rt') as f:original=json.load(f)
        with gzip.open(trace,'rt') as f:snapshot=json.load(f)
        key=(r['cohort'],r['fid'])
        if key not in originals or original['config']['name']=='low_lanes2':originals[key]=original
        snapshots[key]=snapshot
    assert set(originals)==SELECTED
    pins={str(p.relative_to(ROOT)):sha(p) for p in set(sources)}
    for p in set(sources):
        if p.suffix=='.py':
            dest=out/'sources'/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
    report=dict(schema='cu66-v90-exhaustive-selected-timing-v1',status='FAIL',source_sha256=pins,
        source_ids=[list(x)for x in sorted(SELECTED)],masks=list(range(8)),costs=['LOW','HIGH'],clock_MHz_assumption=100,
        alias=True,packet_limit=49152,physical_30fps_proven=False,validated_under10ms_proven=False,
        scope=['Four selected sources, all eight actual CS88 masks, LOW/HIGH sensitivity costs, on-chip alias descriptor ports.',
               'Offline exhaustive decode oracle, not live host encoding or physical clock measurements.',
               'Producer counts are actual mixed observations; no ratio scaling or subtraction of old elapsed time.',
               'Constant sentinel is excluded. HUD semantic work, physical ports/controller, continuous display and ESP32 remain unqualified.'])
    capacities=dict(memory=1,inverse=1,reconstruct=1,hash=1,tree_r=1,tree_w=1,map_r=1,map_w=1,fetch=1,arithmetic=2,emit=1,dequant=1,alias_map_r=1,alias_map_w=1)
    rows=[];seen=set();started=time.monotonic()
    try:
        with (out/'rows.jsonl').open('w') as stream:
            for frames in data.iter_masks(masks=range(8),only=SELECTED):
                key=frames[0]['cohort'],frames[0]['fid'];assert key in SELECTED and key not in seen;seen.add(key)
                assert {f['mask']for f in frames}==set(range(8)) and len(frames)==8
                for frame in frames:
                    candidate=candidates[*key,frame['mask']]
                    assert frame['packet_sha256']==candidate['packet_sha256'] and frame['wire_bytes']==candidate['wire_bytes']
                    assert frame['canonical_sha256']==snapshots[key]['frame']['canonical_sha256']
                    for cost,weights in (('LOW',repricer.LOW),('HIGH',repricer.HIGH)):
                        priced=repricer.reprice(originals[key]['workload'],frame['shared_work'],frame['context_work'],weights,
                            wire_bytes=frame['wire_bytes'],metadata_bytes=frame['metadata_bytes'])
                        work=alias.transform(dict(originals[key],workload=priced),snapshots[key],True)
                        result=scheduler.schedule(work['jobs'],capacities,None,retain_timeline=True)
                        audit=independent.verify(work,result['timeline'],capacities,None)
                        lifetimes=credits.audit_lifetimes(work,result['timeline'])
                        timed={r['id']:r for r in result['timeline']};decode=timed[work['alias_trace']['decode_complete']]['finish']
                        row=dict(cohort=key[0],fid=key[1],mask=frame['mask'],cost=cost,alias=True,
                            packet_sha256=frame['packet_sha256'],wire_bytes=frame['wire_bytes'],metadata_bytes=frame['metadata_bytes'],
                            fits_49152=frame['wire_bytes']<=49152,observation_work_sha256=frame['work_sha256'],
                            decode_cycles=decode,conditional_decode_ms=decode/100000,
                            full_gather_cycles=result['finish_cycles'],conditional_base_gather_complete_ms=result['finish_cycles']/100000,
                            producer_work_cycles=work['frontend']['work_cycles'],memory_work_cycles=audit['resource_work_cycles']['memory'],
                            credit_peaks=lifetimes,independent_audit=audit,timeline_sha256=audit['timeline_sha256'])
                        if frame['mask'] in (0,7):
                            p=out/f'c{key[0]}-f{key[1]}-mask{frame["mask"]}-{cost}.json.gz'
                            with gzip.open(p,'wt') as f:json.dump(dict(capacities=capacities,windows=None,workload=work,result=result,independent_audit=audit,credits=lifetimes),f,separators=(',',':'))
                            row.update(witness=str(p.relative_to(ROOT)),witness_sha256=sha(p))
                        rows.append(row);stream.write(json.dumps(row,separators=(',',':'))+'\n');stream.flush()
                        print('V90_EXACT_PROGRESS',len(rows),key,frame['mask'],cost,round(time.monotonic()-started,2),flush=True)
        assert seen==SELECTED and len(rows)==64
        keyed={(r['cohort'],r['fid'],r['mask'],r['cost']):r for r in rows};controls=[]
        for oldrow in oldrows:
            r=keyed[oldrow['cohort'],oldrow['fid'],oldrow['mask'],oldrow['cost']]
            for field in ('decode_cycles','full_gather_cycles','packet_sha256','wire_bytes','observation_work_sha256','timeline_sha256'):
                assert r[field]==oldrow[field],('V89 unchanged control',field)
            controls.append(dict(cohort=r['cohort'],fid=r['fid'],mask=r['mask'],cost=r['cost'],policy=oldrow['policy'],decode_cycles=r['decode_cycles']))
        assert len(controls)==32
        oracles=[]
        for key in sorted(SELECTED):
            for cost in ('LOW','HIGH'):
                allowed=[r for r in rows if (r['cohort'],r['fid'],r['cost'])==(*key,cost) and r['fits_49152']]
                best=min(allowed,key=lambda r:(r['decode_cycles'],r['wire_bytes'],r['mask']))
                baseline=keyed[*key,0,cost]
                policy15=next(r for r in oldrows if (r['cohort'],r['fid'],r['cost'],r['policy'])==(*key,cost,'feedback_overhead15'))
                oracles.append(dict(cohort=key[0],fid=key[1],cost=cost,best_mask=best['mask'],packet_sha256=best['packet_sha256'],
                    wire_bytes=best['wire_bytes'],decode_cycles=best['decode_cycles'],conditional_decode_ms=best['conditional_decode_ms'],
                    baseline_mask0_decode_ms=baseline['conditional_decode_ms'],policy15_mask=policy15['mask'],policy15_decode_ms=policy15['conditional_decode_ms'],
                    savings_vs_policy15_cycles=policy15['decode_cycles']-best['decode_cycles'],conditional_under10ms=best['decode_cycles']<1000000))
        assert pins=={n:sha(ROOT/n)for n in pins},'executed sources changed'
        report.update(status='PASS_EXHAUSTIVE_SELECTED_CAUSAL_TIMING',unique_sources=4,schedules=64,unchanged_V89_control_matches=controls,
            exact_oracles=oracles,summary_by_cost=[dict(cost=c,sources=4,best_conditional_decode_ms=stats([r['conditional_decode_ms']for r in oracles if r['cost']==c]),
                best_under10ms=sum(r['conditional_under10ms']for r in oracles if r['cost']==c))for c in ('LOW','HIGH')])
    finally:
        report['wall_seconds']=time.monotonic()-started
        report['artifacts_sha256']={str(p.relative_to(out)):sha(p)for p in out.rglob('*')if p.is_file()}
        (out/'results.json').write_text(json.dumps(report,indent=2)+'\n');print('V90_EXACT_REPORT',out/'results.json',report['status'],flush=True)
    (AREA/'results.json').write_text(json.dumps(dict(report,selected_report=str((out/'results.json').relative_to(ROOT))),indent=2)+'\n')


if __name__=='__main__':main()
