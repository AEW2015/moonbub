#!/usr/bin/env python3
"""Strict isolated capacity proof. Source verification only unless --run is explicit."""
import argparse
import datetime
import gzip
import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/'fpga/experiments/cu66-v108-capacity'
AREA=ROOT/'experiments/python-gamebub-v108/capacity'
IMAGE='gamebub-cu66-v69-tools:20261105'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def memory():
    m={x.split(':')[0]:int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines()}
    f=next(x for x in Path('/proc/pressure/memory').read_text().splitlines() if x.startswith('full '))
    return dict(available_bytes=m['MemAvailable'],psi_full_avg10=float(f.split('avg10=')[1].split()[0]))
def verify():
    recipe=json.loads((SRC/'edit-recipe.json').read_text())
    for name,f in recipe['production'].items():
        old=ROOT/f['original'];new=SRC/name
        assert sha(old)==f['original_sha256'] and sha(new)==f['candidate_sha256']
        text=old.read_text()
        for e in f['edits']:
            assert text.count(e['before'])==1
            text=text.replace(e['before'],e['after'],1)
        assert text==new.read_text()
    for a in json.loads((SRC/'verification/adapters.json').read_text())['adapters']:
        old=ROOT/a['source'];new=ROOT/a['path']
        assert sha(old)==a['source_sha256'] and sha(new)==a['sha256']
        text=old.read_text()
        for before,after in a['renames']:
            assert text.count(before)==1
            text=text.replace(before,after,1)
        assert text==new.read_text()
    assert (SRC/'verification/tb_math.cpp').read_bytes()==(Path(__file__).parent/'tb_math.cpp').read_bytes()
    return recipe
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--run',action='store_true');args=ap.parse_args();recipe=verify()
    if not args.run:
        print('CAPACITY_QUALIFICATION_PREPARED_NOT_RUN');return
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=AREA/'attempts'/stamp;out.mkdir(parents=True)
    build=Path('/home/lori/gamebub-build/cu66-v69')/('v108-capacity-'+stamp);build.mkdir()
    mapped='/build/'+build.name
    deps=[ROOT/p for p in ('fpga/experiments/cu66-v107-rice/br88_rice_elastic.sv','fpga/experiments/cu66-v106-context/br88_context.sv','fpga/experiments/cu66-v91d/br88_packet_ingress.sv')]
    vectors=ROOT/'experiments/python-gamebub-v91e/vectors/coefficients.jsonl.gz'
    files=[p for p in SRC.rglob('*') if p.is_file()]+[ROOT/f['original'] for f in recipe['production'].values()]+deps+[vectors,ROOT/'fpga/experiments/cu66-v91h/tb_pipeline.cpp']
    files += [p for p in Path(__file__).parent.iterdir() if p.is_file()]
    files += [ROOT/'fpga/experiments/cu66-v107-count-threshold/verification'/n for n in ('tb_capture.cpp','tb_prefix.cpp')]
    r=dict(schema='v108-capacity-focused-qualification-v1',status='FAIL',actual_RTL_run=False,source_sha256={str(p.relative_to(ROOT)):sha(p) for p in files},production=[dict(path=str((SRC/n).relative_to(ROOT)),sha256=e['candidate_sha256']) for n,e in recipe['production'].items()],commands=[],math_runs=[],capture_runs=[],runs=[],memory_samples=[],strict_warnings=True,compiler_optimization='-O1 uniform across control/candidate/oracle',scope='Exact extracted production capacity pipeline/predicate, actual complete synchronous ingress capture and paired four-body cycle/public/golden proof in both SYNC modes. No full-pixel/native/timing or board claim.')
    def command(argv,name,cap,rejection=False):
        gate=memory();assert gate['available_bytes']>=8*1024**3 and gate['psi_full_avg10']<1,gate
        container='gamebub-v108-capacity-'+stamp.lower()+'-'+str(len(r['commands']))
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
        entry.update(exit_code=code,stop_reason=stop,wall_seconds=time.monotonic()-start)
        if rejection:
            text=(out/name).read_text()
            assert code==134 and not stop and 'stale staging response' in text and 'EXPECTED_ASSERTION_ARMED' in text and '"capture_enable":false' in text,name
            entry['status']='PASS_EXPECTED_ORIGINAL_ASSERTION_CONTRACT_REJECTION'
        else:assert code==0 and not stop,name
    try:
        for p in files:
            q=out/'sources'/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
        for p in (SRC/'verification').iterdir():
            if p.is_file():shutil.copyfile(p,build/p.name)
        for p in deps:shutil.copyfile(p,build/p.name)
        cases=[json.loads(line) for line in gzip.decompress(vectors.read_bytes()).splitlines()]
        (build/'vectors.txt').write_text(''.join(' '.join(map(str,(x['id'],x['blocks'],x['packet_hex'],x['dense_hex'],x['packed_hex'])))+'\n' for x in cases))
        command(['verilator','--version'],'version.log',30)
        cflags='-std=c++17 -O1 -Wall -Wextra -Werror'
        flags=['verilator','--cc','--exe','--build','-j','1','--assert','-Wall','--output-split','10000','--output-split-cfuncs','500','--language','1800-2017','-CFLAGS',cflags]
        command([*flags,'--top-module','capacity_math_probe','--Mdir',mapped+'/math-obj',mapped+'/capacity_math_probe.sv',mapped+'/tb_math.cpp'],'math-compile.log',180)
        assert '%Warning-' not in (out/'math-compile.log').read_text()
        for seed in (108201,108202):
            log=f'math-{seed}.json';command([mapped+'/math-obj/Vcapacity_math_probe',str(seed)],log,120);v=json.loads((out/log).read_text().splitlines()[-1])
            assert v['status']=='TEST_PASS' and v['full_u17_block_grid_cases']==2097152 and v['raw_full_u17_cases']==131072 and v['random_u32_cases']==300000 and v['post_capture_edges']==4 and v['flush_commit_collisions']>=4;r['math_runs'].append(v)
        command([*flags,'--public-flat-rw','--top-module','ingress_capture_probe','--Mdir',mapped+'/capture-obj',mapped+'/ingress_original.sv',mapped+'/ingress_candidate.sv',mapped+'/ingress_capture_probe.sv',mapped+'/br88_context.sv',mapped+'/br88_rice_elastic.sv',mapped+'/tb_capture.cpp'],'capture-compile.log',600)
        assert '%Warning-' not in (out/'capture-compile.log').read_text()
        for seed in (108201,108202):
            log=f'capture-{seed}.json';command([mapped+'/capture-obj/Vingress_capture_probe',str(seed),mapped+f'/capture-{seed}.csv'],log,120);v=json.loads((out/log).read_text().splitlines()[-1])
            assert v['status']=='TEST_PASS' and v['positive_prepared_cases']==1728 and v['actual_raw_packets']==8 and v['high32_metadata_owners']==128 and v['capture_edge_abort_restarts']==3 and v['held_metadata_edges']==2312 and v['commit_abort_retries']==3 and v['threshold_flush_commits']>=3 and v['capacity_abort_retries']==1 and v['capacity_flush_commits']>=1;r['capture_runs'].append(v)
        r['negative_owner_contract_rejections']=[]
        for mode in (1,2):
            for index in (33,37,41):
                log=f'capture-negative-{mode}-{index}.log';command([mapped+'/capture-obj/Vingress_capture_probe','108201',mapped+f'/negative-{mode}-{index}.csv',str(mode),str(index)],log,30,True)
                r['negative_owner_contract_rejections'].append(dict(mode=mode,index=index,log=log,status='PASS_EXPECTED_ORIGINAL_ASSERTION_REJECTION',capture_enable=False,post_rejection_recovery_claim=False))
        sv=[mapped+'/'+kind+'_'+variant+'.sv' for kind in ('ingress','packet','scratch','pipeline') for variant in ('original','candidate')]+[mapped+'/prefix_probe.sv']+[mapped+'/'+p.name for p in deps]
        for sync in (1,0):
            command([*flags,'--top-module','prefix_probe','-GSYNC_STAGING='+str(sync),'--Mdir',mapped+'/pair-'+str(sync),'-CFLAGS',cflags+' -DSYNC_STAGING='+str(sync),*sv,mapped+'/tb_prefix.cpp'],f'pair-{sync}-compile.log',600)
            assert '%Warning-' not in (out/f'pair-{sync}-compile.log').read_text()
            for seed in (108201,108202):
                log=f'pair-{sync}-{seed}.jsonl';command([mapped+f'/pair-{sync}/Vprefix_probe',mapped+'/vectors.txt',str(seed)],log,180)
                records=[json.loads(line) for line in (out/log).read_text().splitlines()];v=records[-1];history=next(x for x in records if x.get('type')=='verdict')
                assert v['status']==history['status']=='TEST_PASS' and history['packets']==len(cases) and history['configurations']==2;r['runs'].append(dict(sync_staging=sync,seed=seed,pair=v,historical=history))
        assert r['source_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in files}
        r.update(status='PASS',actual_RTL_run=True,frozen_after_focused_PASS=True)
    except BaseException as e:r['error']=repr(e);raise
    finally:
        for trace in build.glob('*.csv'):
            with trace.open('rb') as src,(out/(trace.name+'.gz')).open('wb') as dst:
                with gzip.GzipFile(filename='',fileobj=dst,mode='wb',mtime=0) as z:shutil.copyfileobj(src,z)
        for p in build.iterdir():
            if p.is_file() and p.suffix!='.csv':shutil.copyfile(p,out/p.name)
        r['artifacts_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
        write(out/'results.json',r);write(AREA/'results.json',dict(r,selected_report=str((out/'results.json').relative_to(ROOT)),selected_report_sha256=sha(out/'results.json')))
        print('CAPACITY_QUALIFICATION',r['status'],flush=True)
if __name__=='__main__':main()
