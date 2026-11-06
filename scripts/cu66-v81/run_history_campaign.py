#!/usr/bin/env python3
"""Run four independent finite histories against one qualified immutable build."""
import argparse
import concurrent.futures
import hashlib
import json
import subprocess
import time
import uuid
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'fpga/experiments/cu66-v81'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--prefetch',type=int,choices=(2,3),default=3)
    parser.add_argument('--workers',type=int,choices=range(1,5),default=4)
    args=parser.parse_args()
    out=AREA/'campaigns'/f'prefetch{args.prefetch}-{uuid.uuid4().hex[:12]}'
    out.mkdir(parents=True)
    index=ROOT/'experiments/cu66-native-v69/index.tsv'
    runner=ROOT/'scripts/cu66-v81/run_system.py'
    counts={}
    for line in index.read_text().splitlines():
        c=int(line.split('\t')[0]);counts[c]=counts.get(c,0)+1
    assert counts=={0:119,1:119,2:119,3:100}
    pins={str(p.relative_to(ROOT)):sha(p)for p in(index,runner,Path(__file__).resolve())}
    start=time.monotonic();cases=[]

    def case(cohort):
        cmd=['python3',str(runner),'--prefetch',str(args.prefetch),'--cohort',str(cohort),
             '--frames','full','--mode','fixed30','--tac','2','--skip-build']
        log=out/f'cohort{cohort}.log';begin=time.monotonic()
        with log.open('w')as stream:
            p=subprocess.run(cmd,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,timeout=18000)
        lines=log.read_text().splitlines()
        records=[json.loads(line)for line in lines if line.startswith('{')]
        final=records[-1]if records else None
        result=dict(cohort=cohort,requested_sources=counts[cohort],command=cmd,
                    exit_code=p.returncode,wall_seconds=time.monotonic()-begin,
                    log=str(log.relative_to(ROOT)),sha256=sha(log),runner_result=final)
        if final and final.get('results_path'):
            path=Path(final['results_path']).resolve()
            assert path.is_relative_to(ROOT)
            result['results_path']=str(path.relative_to(ROOT));result['results_sha256']=sha(path)
        return result

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers)as pool:
        futures={pool.submit(case,c):c for c in sorted(counts)}
        for f in concurrent.futures.as_completed(futures):
            try:r=f.result()
            except Exception as exc:r=dict(cohort=futures[f],requested_sources=counts[futures[f]],exit_code=None,error=repr(exc))
            cases.append(r);print(json.dumps(r),flush=True)
    assert pins=={name:sha(ROOT/name)for name in pins},'campaign driver inputs changed'
    passed=len(cases)==4 and all(r.get('exit_code')==0 and (r.get('runner_result') or {}).get('status')=='V81_SYSTEM_PASS'for r in cases)
    report=dict(schema='cu81-independent-history-campaign-v1',
         status='PASS_ALL_REQUESTED_HISTORIES'if passed else'FAIL_RETAINED_HISTORIES',
         prefetch=args.prefetch,workers=args.workers,requested_sources=457,
         source_sha256=pins,cases=sorted(cases,key=lambda r:r['cohort']),
         wall_seconds=time.monotonic()-start,
         scope='Four independent histories, one initial reset each and no per-source resets. Functional gate only.',
         limitations=['Not1800distinct-source60s or18000-source600s qualification.',
                      'Modeled100MHz; zero-simtime nativeCPU HUD; no liveESP32 or target fit/route/CDC.'])
    (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'results_path':str((out/'results.json').relative_to(ROOT))}),flush=True)
    if not passed:raise SystemExit(1)


if __name__=='__main__':main()
