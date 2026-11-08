#!/usr/bin/env python3
"""Strict complete old/new IDCT proof; source/fixture checks only unless --run."""
import argparse
import datetime
import gzip
import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"outtile"))
from model import verify_recipe
ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/'fpga/experiments/cu66-v108-outtile-kill-collisions'
AREA=ROOT/'experiments/python-gamebub-v108/outtile-kill-collisions'
OLD_AREA=ROOT/'experiments/python-gamebub-v107/idct-reset'
IMAGE='gamebub-cu66-v69-tools:20261105'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def memory():
    m={x.split(':')[0]:int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines()}
    f=next(x for x in Path('/proc/pressure/memory').read_text().splitlines() if x.startswith('full '))
    return dict(available_bytes=m['MemAvailable'],psi_full_avg10=float(f.split('avg10=')[1].split()[0]))
def verify():
    recipe=verify_recipe();a=json.loads((SRC/'adapters.json').read_text())
    prior=ROOT/a["frozen_prior_result"];assert sha(prior)==a["frozen_prior_result_sha256"];prior_record=json.loads(prior.read_text());assert prior_record["status"]=="PASS" and prior_record["actual_RTL_run"] and prior_record["candidate"]["sha256"]==recipe["candidate_sha256"]
    for e in a['adapters']:
        p=ROOT/e['source'];q=ROOT/e['path'];assert sha(p)==e['source_sha256'] and sha(q)==e['sha256'];s=q.read_text()
        if e['candidate_extra_ports']:
            assert s.count(e['candidate_extra_ports'])==1;s=s.replace(e['candidate_extra_ports'],'\n);',1)
            assert s.count(e['candidate_extra_assignments'])==1;s=s.replace(e['candidate_extra_assignments'],'',1)
        assert s.count(e['extra_ports'])==1;s=s.replace(e['extra_ports'],'\n);',1)
        assert s.count(e['extra_assignments'])==1;s=s.replace(e['extra_assignments'],'',1)
        old,new=e['module_rename'];assert s.count(new)==1;s=s.replace(new,old,1);assert s==p.read_text()
    p=ROOT/a['bench_original'];assert sha(p)==a['bench_original_sha256'];s=p.read_text()
    for e in a['bench_edits']:assert s.count(e['before'])==1;s=s.replace(e['before'],e['after'],1)
    assert s==(SRC/'tb_idct.cpp').read_text()
    old_probe=ROOT/a['probe_original'];assert sha(old_probe)==a['probe_original_sha256']
    equal=old_probe.read_text().split('    assign probe_equal=',1)[1]
    assert (SRC/'idct_probe.sv').read_text().split('    assign probe_equal=',1)[1]==equal
    model=json.loads((AREA/'preparation.json').read_text());assert model['status']=='PASS_PREPARATION_MODEL_NOT_RTL' and model['candidate_sha256']==recipe['candidate_sha256']
    for name,h in model['source_sha256'].items():assert sha(ROOT/name)==h
    vectors=OLD_AREA/'vectors.hex.gz';gold=json.loads((OLD_AREA/'model.json').read_text());assert sha(vectors)==gold['vectors']['sha256'] and gold['tiles']==4303
    return recipe,vectors
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--run',action='store_true');args=ap.parse_args();recipe,vectors=verify()
    if not args.run:print('OUTTILE_QUALIFICATION_PREPARED_NOT_RUN');return
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/stamp;out.mkdir(parents=True)
    build=Path('/home/lori/gamebub-build/cu66-v69')/('v108-outtile-kill-'+stamp);build.mkdir();mapped='/build/'+build.name
    files=[p for p in SRC.iterdir() if p.is_file()]+[p for p in Path(__file__).parent.iterdir() if p.is_file()]
    files += [ROOT/recipe['original_path'],ROOT/recipe['candidate_path'],ROOT/"experiments/python-gamebub-v108/outtile/results.json",vectors,OLD_AREA/'model.json',AREA/'preparation.json',ROOT/'fpga/experiments/cu66-v107-idct-reset/adapter.json',ROOT/'fpga/experiments/cu66-v107-idct-reset/tb_idct.cpp',ROOT/'fpga/experiments/cu66-v107-idct-reset/idct_probe.sv']
    r=dict(schema='v108-outtile-kill-collisions-focused-proof-v1',status='FAIL',actual_RTL_run=False,source_sha256={str(p.relative_to(ROOT)):sha(p) for p in files},candidate=dict(path=recipe['candidate_path'],sha256=recipe['candidate_sha256']),commands=[],runs=[],memory_samples=[],strict_warnings=True,assertions_disabled_or_downgraded=False,scope='Complete original actualV107 IDCT body versus fixed-word private-output payload and exact64-bit visibility mask; every original public/invalid/partial-word/control/golden check retained; prepared-only arbitrary-control model is separate; no full pipeline/native/board claim.')
    def command(argv,name,cap):
        gate=memory();assert gate['available_bytes']>=8*1024**3 and gate['psi_full_avg10']<1,gate
        container='gamebub-v108-outtile-kill-'+stamp.lower()+'-'+str(len(r['commands']))
        cmd=['docker','run','--rm','--init','--name',container,'--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--network','none','--ulimit','core=0','--mount',f'type=bind,src={ROOT},dst={ROOT},readonly','--mount',f'type=bind,src={build},dst={mapped}','-w',mapped,IMAGE,'timeout','--kill-after=5s',str(cap)+'s',*argv]
        entry=dict(argv=cmd,resource_before=gate,timeout_seconds=cap);r['commands'].append(entry);start=time.monotonic();stop=None;last=-5
        with (out/name).open('w') as log:
            proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
            while proc.poll() is None:
                elapsed=time.monotonic()-start
                if elapsed-last>=5:
                    sample=dict(elapsed_seconds=elapsed,command=name,**memory());r['memory_samples'].append(sample);last=elapsed
                    if sample['available_bytes']<4*1024**3 or sample['psi_full_avg10']>=5:stop='HOST_MEMORY_GATE'
                if elapsed>cap+20:stop='HOST_TIMEOUT'
                if stop:
                    subprocess.run(['docker','stop','--time','5',container],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15);break
                time.sleep(.5)
            code=proc.wait(timeout=20)
        entry.update(exit_code=code,stop_reason=stop,wall_seconds=time.monotonic()-start);assert code==0 and not stop,name
    try:
        for p in files:
            q=out/'sources'/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
        for name in ('idct_original.sv','idct_candidate.sv','idct_probe.sv','tb_idct.cpp'):shutil.copyfile(SRC/name,build/name)
        raw=gzip.decompress(vectors.read_bytes());assert len(raw.splitlines())==4303;(build/'vectors.hex').write_bytes(raw)
        command(['verilator','--version'],'version.log',30)
        command(['verilator','--cc','--exe','--build','-j','1','--assert','-Wall','--public-flat-rw','--output-split','10000','--output-split-cfuncs','500','--language','1800-2017','--top-module','idct_probe','--Mdir',mapped+'/obj','-CFLAGS','-std=c++17 -O1 -Wall -Wextra -Werror',*[mapped+'/'+n for n in ('idct_original.sv','idct_candidate.sv','idct_probe.sv','tb_idct.cpp')]],'compile.log',300)
        assert '%Warning-' not in (out/'compile.log').read_text()
        command(['sha256sum',mapped+'/obj/Vidct_probe'],'binary.log',30);r['binary_sha256']=(out/'binary.log').read_text().split()[0]
        for seed in (108301,108302):
            trace=build/f'trace-{seed}.jsonl';command([mapped+'/obj/Vidct_probe',mapped+'/vectors.hex',str(seed),mapped+'/'+trace.name],f'seed-{seed}.json',120)
            v=json.loads((out/f'seed-{seed}.json').read_text());assert v['status']=='TEST_PASS' and v['tiles']==4303 and v['directed_abort_reset_cases']==30 and v['abort_state_mask']==1023 and v['states']==1023 and v['idle_noise_edges']==1024 and v['source_owner_checks']>100000 and v['masked_private_word_poisons']>1000 and v['all_cycle_public_word_checks']>=64*v['clock_edges']*3 and v['kill_payload_write_collisions']>=3 and v['exposed_word_commits']>1000 and v['write_boundary_collision_cases']==12 and v['write_boundary_group_mask']==15 and v['write_boundary_guard_mask']==7 and v['write_boundary_matrix_mask']==4095 and v['write_boundary_good_retries']==12 and v['kill_payload_write_collisions']==15
            products=[0]*8;rows=mul=0;boundary={}
            for line in trace.open():
                row=json.loads(line)
                if row['kill']:products=[0]*8
                elif row['mul']:products=[x*y for x,y in zip(row['samples'],row['basis'])];mul+=1
                assert row['products']==products;rows+=1
                if row['kill'] and row['state']==4 and row['k']==7:
                    group=row['group'];guards=row['rst']+2*row['abort'];assert 0<=group<4 and guards in (1,2,3)
                    selected=sum(1<<(r*8+c) for r in range(8) for c in (group*2,group*2+1));assert row['payload_write_mask']==selected and row['written_mask_after']==0 and row['public_zero_after']
                    key=group*3+guards-1;boundary[key]=boundary.get(key,0)+1
            assert rows==v['clock_edges'] and mul==v['multiply_edges']
            assert boundary=={i:1 for i in range(12)}
            r['runs'].append(dict(seed=seed,verdict=v,trace_replay=dict(status='PASS',rows=rows,multiply_edges=mul,raw_sha256=sha(trace),write_boundary_matrix_mask=sum(1<<i for i in boundary),write_boundary_collisions=sum(boundary.values()))))
        assert r['source_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in files};r.update(status='PASS',actual_RTL_run=True,frozen_after_focused_PASS=True)
    except BaseException as e:r['error']=repr(e);raise
    finally:
        for trace in build.glob('trace-*.jsonl'):
            with trace.open('rb') as src,(out/(trace.name+'.gz')).open('wb') as dst:
                with gzip.GzipFile(filename='',fileobj=dst,mode='wb',mtime=0) as z:shutil.copyfileobj(src,z)
        for p in build.iterdir():
            if p.is_file() and not p.name.startswith('trace-') and p.name!='vectors.hex':shutil.copyfile(p,out/p.name)
        r['artifacts_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()};write(out/'results.json',r)
        write(AREA/'results.json',dict(r,selected_report=str((out/'results.json').relative_to(ROOT)),selected_report_sha256=sha(out/'results.json')));print('OUTTILE_KILL_QUALIFICATION',r['status'],flush=True)
if __name__=='__main__':main()
