#!/usr/bin/env python3
"""Compare frozen direct writer and optional strip using identical oracle data."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
CONTAINER=os.environ.get('TASK_CONTAINER','gamebub-cu66-v69-build')


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    native=ROOT/'experiments/cu66-native-v69'
    baseline=json.loads((HERE/'baseline-files.json').read_text())['files_sha256']
    for f,h in baseline.items():assert sha(ROOT/f)==h,('frozen baseline changed',f)
    files=[HERE/'cu70_painter_strip.sv',HERE/'tb_painter_locality.cpp',HERE/'cu70_painter.sv',Path(__file__).resolve(),*native.glob('*.hpp'),native/'index.tsv',*sorted((native/'fixtures').glob('*.cu66'))]
    before={str(p.relative_to(ROOT)):sha(p)for p in files}
    commands=[]
    def run(argv,name,timeout=600):
        p=HERE/name
        with p.open('w')as log:r=subprocess.run(argv,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=timeout)
        commands.append({'argv':argv,'exit_code':r.returncode,'log':str(p.relative_to(ROOT)),'sha256':sha(p)})
        if r.returncode:raise RuntimeError(f'{name}: exit{r.returncode}; inspect retained log')
        return p.read_text()
    outputs=[]
    for variant in ['direct','strip']:
        top='cu70_painter'+('_strip'if variant=='strip'else'')
        run(['docker','exec',CONTAINER,'verilator','--cc','--exe','--build','-j','2','--Wall','--top-module',top,'--Mdir',f'/build/v70-display-locality-{variant}','-CFLAGS','-O2 -std=c++17'+(' -DUSE_STRIP'if variant=='strip'else''),str(HERE/(top+'.sv')),str(HERE/'tb_painter_locality.cpp')],f'locality-build-{variant}.log')
        for seed in [0,7001]:
            log=run(['docker','exec',CONTAINER,f'/build/v70-display-locality-{variant}/V{top}',str(native/'index.tsv'),str(seed)],f'locality-{variant}-seed{seed}.log')
            assert f'PASS actual_frames=8 patterns=4 recovery=1 fault_probes={5 if seed else 0} seed={seed}'in log and'FAIL'not in log
            rows=[dict((k,int(v))for k,v in re.findall(r'(\w+)=(\d+)',s))for s in log.splitlines()if s.startswith('CASE_PASS')]
            good=[x for x in rows if x['mode']==0]
            assert len(good)==13 and all(x['read_words']==280320 and x['write_words']==384000 and x['painted']==345600 for x in good)
            assert all(x['canvas_runs']==(43200 if variant=='strip'else 345600)for x in good)
            assert all(x['aligned8_runs']==(43200 if variant=='strip'else 0)for x in good)
            outputs.append({'variant':variant,'seed':seed,'full_rasters':13,'fault_probes':5 if seed else 0,'min_cycles':min(x['cycles']for x in good),'mean_cycles':sum(x['cycles']for x in good)/13,'max_cycles':max(x['cycles']for x in good),'per_frame':good})
    for f,h in baseline.items():assert sha(ROOT/f)==h,('baseline changed during comparison',f)
    assert before=={str(p.relative_to(ROOT)):sha(p)for p in files},'source mutation'
    a,b=outputs[0]['per_frame'][0],outputs[2]['per_frame'][0]
    result={'status':'PASS','source_sha256':before,'commands':commands,'runs':outputs,'frozen_baseline_files':len(baseline),'additional_strip_bytes':11520,'total_logical_cache_bytes_strip':13696,'measured_address_locality':{'direct_canvas_runs':a['canvas_runs'],'strip_canvas_runs':b['canvas_runs'],'direct_512word_row_changes':a['row_changes'],'strip_512word_row_changes':b['row_changes'],'strip_aligned8word_canvas_runs':b['aligned8_runs']},'scope':'acceptedwriteaddresslocality andexactfullrasteroutput; scalarcompletionbenches; notactualSDRAMACTPREcommands orBL8writes','not_proven':['targetmemoryfit/Fmax','physicalfps','actualcontrollerburstthroughput','endtoendpacketdisplayintegration']}
    (HERE/'strip-results.json').write_text(json.dumps(result,indent=2)+'\n')
    print('STRIP_COMPARISON_PASS variants=2 seeds=2 full_rasters=52 compared_words=19968000 seeded_fault_probes=10 canvas_runs_direct=345600 strip=43200 aligned8_strip=43200 baseline_files_unchanged='+str(len(baseline)))


if __name__=='__main__':main()
