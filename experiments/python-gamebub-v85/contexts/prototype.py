#!/usr/bin/env python3
"""Standalone finite-window context scheduling: selected native samples only."""
import datetime,gzip,hashlib,importlib.util,json,statistics,sys,time,tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
AREA=Path(__file__).resolve().parent
LOW=dict(decisions=2,renorm=2,stream_bytes=2,rice_values=1,events=1,raw_bytes=2,header_bytes=2,crc_bytes=2,emits=1,raw_bits=1,prob_init=1)
HIGH=dict(decisions=4,renorm=4,stream_bytes=4,rice_values=1,events=1,raw_bytes=4,header_bytes=4,crc_bytes=4,emits=1,raw_bits=2,prob_init=1)


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,p):
    spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def stats(v):return dict(min=min(v),median=statistics.median(v),max=max(v),total=sum(v))


def main():
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=AREA/'model-attempts'/stamp;out.mkdir(parents=True)
    index=json.loads((AREA/'index.json').read_text())
    sources=[Path(__file__).resolve(),AREA/'model.py',AREA/'data.py',AREA/'index.json',AREA/index['data']['path'],
             ROOT/'experiments/python-gamebub-v83/scheduler.py',ROOT/'scripts/cu66-v84/prototype_pipeline.py']
    pins={str(p.relative_to(ROOT)):sha(p) for p in sources}
    with tarfile.open(out/'sources.tar.gz','w:gz')as tar:
        for p in sources:
            if p.suffix!='.gz':tar.add(p,arcname=str(p.relative_to(ROOT)),recursive=False)
    report=dict(schema='cu66-v85-context-model-v1',status='FAIL',source_sha256=pins,
                clock_mhz_assumption=100,physical_timing_proven=False,full_corpus_scheduling=False)
    start=time.monotonic()
    try:
        data=load('cu85_context_data',AREA/'data.py');model=load('cu85_context_model',AREA/'model.py')
        scheduler=load('cu85_context_scheduler',ROOT/'experiments/python-gamebub-v83/scheduler.py')
        old=load('cu85_context_costs',ROOT/'scripts/cu66-v84/prototype_pipeline.py')
        assert LOW==old.LOW and HIGH==old.HIGH
        cases=[]
        # Small directed checks establish the rendezvous and shared-port behavior.
        synthetic=[]
        zero={k:0 for k in LOW}
        for kind in ('balanced','one_stream','fetch_bound'):
            shared=[dict(zero,emits=1) for _ in range(4)]
            contexts=[[dict(zero) for _ in range(4)] for _ in range(4)]
            for row in contexts:
                for i,work in enumerate(row):
                    work['decisions']=4 if kind=='balanced' or i==0 else 0
                    work['stream_bytes']=8 if kind=='fetch_bound' else 0
            for lanes in(1,2,4):
                for window in(1,4):
                    w=model.build(shared,contexts,LOW,window)
                    r=scheduler.schedule(w['jobs'],dict(fetch=1,arithmetic=lanes,emit=1),retain_timeline=True)
                    a=model.audit(w,r,lanes)
                    if window==1 and kind=='balanced':assert r['finish_cycles']==4*(32//lanes+1)
                    if window==1 and kind=='one_stream':assert r['finish_cycles']==36
                    synthetic.append(dict(kind=kind,lanes=lanes,window=window,**a))
        for frame in data.iter_frames():
            if not(frame['ordinal']<6 or frame['cohort']==3 and frame['fid']==50):continue
            for cost,weights in(('LOW',LOW),('HIGH',HIGH)):
                for window in(8,64):
                    w=model.build(frame['shared_work'],frame['context_work'],weights,window)
                    for lanes in(1,2,4):
                        r=scheduler.schedule(w['jobs'],dict(fetch=1,arithmetic=lanes,emit=1),retain_timeline=True)
                        a=model.audit(w,r,lanes)
                        row=dict(cohort=frame['cohort'],fid=frame['fid'],ordinal=frame['ordinal'],cost=cost,
                                 lanes=lanes,window=window,model_ms=r['finish_cycles']*1e-5,**a)
                        cases.append(row)
                        if frame['cohort']==3 and frame['fid']==50 and cost=='LOW' and window==8 and lanes in(1,4):
                            with gzip.open(out/f'witness-c3-f50-low-w8-l{lanes}.json.gz','wt')as stream:
                                json.dump(dict(workload=w,result=r,audit=a),stream,separators=(',',':'))
            print('CONTEXT_MODEL_SOURCE',frame['cohort'],frame['fid'],len(cases),flush=True)
        assert len(cases)==300
        (out/'rows.jsonl').write_text(''.join(json.dumps(r,separators=(',',':'))+'\n'for r in cases))
        summaries=[]
        for cost in('LOW','HIGH'):
            for window in(8,64):
                for lanes in(1,2,4):
                    rows=[r for r in cases if(r['cost'],r['window'],r['lanes'])==(cost,window,lanes)]
                    summaries.append(dict(cost=cost,window=window,lanes=lanes,sources=len(rows),
                                          model_ms=stats([r['model_ms'] for r in rows])))
        balance={}
        for cost,weights in(('LOW',LOW),('HIGH',HIGH)):
            context=[sum(v*weights[k] for k,v in t.items()if k not in model.FETCH_FIELDS)for t in index['context_totals']]
            balance[cost]=dict(context_compute_cycles=context,fraction_of_context_compute=[v/sum(context)for v in context],
                               shared_work_cycles=sum(v*weights[k]for k,v in index['shared_totals'].items()),
                               context_fetch_cycles=sum(sum(v*weights[k]for k,v in t.items()if k in model.FETCH_FIELDS)for t in index['context_totals']))
        assert pins=={name:sha(ROOT/name)for name in pins},'source mutation'
        report.update(status='PASS_SELECTED_CONTEXT_MODEL',sources_scheduled=25,schedules=300,
                      synthetic_checks=len(synthetic),synthetic=synthetic,summaries=summaries,all457_context_balance=balance,
                      artifacts_sha256={p.name:sha(p)for p in sorted(out.iterdir())if p.is_file()and p.name!='results.json'},
                      scope=['First6sources per cohort plus nativeworst c3f50; selected25sources notfull457 latency qualification.',
                             'Per-context sequential frontier preserved and each tile joins all four before ordered emission.',
                             'Shared fetch/control and context arithmetic have distinct resources even for one lane; not same hardware architecture as V84.',
                             'Context fetches are aggregated before arithmetic within a tile, not instruction-level execution.',
                             'Immediate external consumer; boundedwindow is in-flight coefficient assembly, not full inverse/display/ESP32 staging.',
                             'No RTL/Fmax/DSP/fit or sustained30fps/full validated under10ms claim.'])
    except BaseException as exc:
        report['failure']=repr(exc);raise
    finally:
        report['wall_seconds']=time.monotonic()-start
        (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
        print('CONTEXT_MODEL_REPORT',out/'results.json',report['status'],flush=True)


if __name__=='__main__':main()
