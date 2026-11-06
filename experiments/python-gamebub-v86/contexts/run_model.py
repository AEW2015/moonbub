#!/usr/bin/env python3
"""Four independent cohorts in parallel; no source history is repeated as data."""
import datetime,hashlib,importlib.util,json,subprocess,sys,time,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];AREA=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m


def main():
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=AREA/'model-sessions'/f'{stamp}-{uuid.uuid4().hex[:8]}';out.mkdir(parents=True);start=time.monotonic()
    model=load('cu86_test_model',AREA/'model.py');scheduler=load('cu86_test_scheduler',ROOT/'experiments/python-gamebub-v83/scheduler.py')
    weights=load('cu86_test_weights',AREA/'prototype.py').LOW;synthetic=[];zero={k:0 for k in weights}
    for kind in ('balanced','one_stream','fetch_bound'):
        shared=[dict(zero,emits=1) for _ in range(4)];contexts=[[dict(zero) for _ in range(4)] for _ in range(4)]
        for row in contexts:
            for i,w in enumerate(row):w['decisions']=4 if kind=='balanced' or i==0 else 0;w['stream_bytes']=8 if kind=='fetch_bound' else 0
        for lanes in (1,2,4):
            for window in (1,4):
                w=model.build(shared,contexts,weights,window);r=scheduler.schedule(w['jobs'],dict(fetch=1,arithmetic=lanes,emit=1),retain_timeline=True)
                a=model.audit(w,r,lanes)
                if window==1 and kind=='balanced':assert r['finish_cycles']==4*(32//lanes+1)
                if window==1 and kind=='one_stream':assert r['finish_cycles']==36
                synthetic.append(dict(kind=kind,lanes=lanes,window=window,**a))
    children=[]
    for cohort in range(4):
        command=[sys.executable,str(AREA/'prototype.py'),'--cohort',str(cohort)]
        log=(out/f'cohort{cohort}.log').open('w');process=subprocess.Popen(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        children.append((cohort,command,process,log))
    print('REENCODED_CONTEXT_MODEL_SESSION',out,flush=True);records=[]
    for cohort,command,process,log in children:
        code=process.wait();log.close();path=out/f'cohort{cohort}.log';lines=path.read_text().splitlines()
        selected=[line.split('REENCODED_CONTEXT_MODEL_REPORT ',1)[1].rsplit(' ',1)[0] for line in lines if line.startswith('REENCODED_CONTEXT_MODEL_REPORT ')]
        records.append(dict(cohort=cohort,command=command,exit_code=code,log=str(path.relative_to(ROOT)),log_sha256=sha(path),report=str(Path(selected[-1]).relative_to(ROOT)) if selected else None))
        print('REENCODED_CONTEXT_COHORT_EXIT',cohort,code,flush=True)
    result=dict(schema='cu66-v86-context-model-session-v1',status='PASS' if all(r['exit_code']==0 for r in records) else 'FAIL',cohorts=records,
                synthetic_checks=len(synthetic),synthetic=synthetic,wall_seconds=time.monotonic()-start,
                source_sha256={str(p.relative_to(ROOT)):sha(p) for p in (Path(__file__),AREA/'model.py',AREA/'prototype.py')})
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n');print('REENCODED_CONTEXT_SESSION_REPORT',out/'results.json',result['status'],flush=True)
    return 0 if result['status']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
