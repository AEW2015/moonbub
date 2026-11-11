#!/usr/bin/env python3
"""Freeze and run actual paired ingress RTL with all 67 public outputs compared."""
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
AREA = ROOT/'experiments/python-gamebub-v129/header-index'
IMAGE = 'sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf'
FILES = [HERE/x for x in ('prepare.py','run.py','manifest.json','header_index_baseline.sv','header_index_pair.sv','tb_pair.cpp','br88_packet_ingress_sync_v91h.sv')] + [
    ROOT/'fpga/experiments/cu66-v128-raw/br88_packet_ingress_sync_v91h.sv',
    ROOT/'fpga/experiments/cu66-v113-geometry/br88_context.sv',
    ROOT/'fpga/experiments/cu66-v129-parser/br88_rice_elastic.sv']

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p): return str(p.relative_to(ROOT))
def write(p,d): p.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
def memory():
    m={x.split(':')[0]:int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines()}
    line=next(x for x in Path('/proc/pressure/memory').read_text().splitlines() if x.startswith('full '))
    return dict(available=m['MemAvailable'],psi=float(line.split('avg10=')[1].split()[0]),
                combined=(m['MemTotal']-m['MemAvailable']+m['SwapTotal']-m['SwapFree'])/(m['MemTotal']+m['SwapTotal']))

def main():
    before=memory();assert before['available']>=8*1024**3 and before['psi']<1 and before['combined']<.85, before
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=AREA/'attempts'/stamp;out.mkdir(parents=True); snap=out/'sources';snap.mkdir()
    hashes={rel(p):sha(p) for p in FILES}
    for p in FILES:
        dest=snap/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest);assert sha(dest)==hashes[rel(p)]
    freeze=dict(schema='header-index-frozen-v1',source_sha256=hashes,resource_launch=before)
    write(out/'freeze.json',freeze)
    name='gamebub-v129-header-index-'+stamp.lower()
    src='/src/fpga/experiments/cu66-v129-header-index/'
    args=['verilator','--cc','--exe','--build','-j','1','--assert','-Wall','--language','1800-2017',
          '--top-module','header_index_pair','--Mdir','/work/obj','-CFLAGS','-std=c++17 -O2 -Wall -Wextra -Werror',
          src+'header_index_baseline.sv',src+'br88_packet_ingress_sync_v91h.sv',src+'header_index_pair.sv',
          '/src/fpga/experiments/cu66-v113-geometry/br88_context.sv',
          '/src/fpga/experiments/cu66-v129-parser/br88_rice_elastic.sv',src+'tb_pair.cpp']
    cmd=['docker','run','--rm','--init','--name',name,'--network','none','--memory','8g','--memory-swap','8g',
         '--cpus','2','--pids-limit','2048','--mount',f'type=bind,src={snap},dst=/src,readonly',
         '--mount',f'type=bind,src={out},dst=/work',IMAGE,'timeout','--kill-after=5s','900s',*args]
    result=dict(status='FAIL',actual_RTL_run=False,source_sha256=hashes,freeze_sha256=sha(out/'freeze.json'),
                commands=[cmd],memory_samples=[],scope='Finite paired actual ingress RTL; no route, full composition, or hardware proof.')
    write(out/'receipt.json',result)
    try:
        with (out/'compile.log').open('w') as log:
            p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT);high=0;start=time.monotonic()
            while p.poll() is None:
                sample=memory();result['memory_samples'].append(sample);high=high+1 if sample['psi']>=5 else 0
                if sample['available']<4*1024**3 or high>=2 or sample['combined']>=.90 or time.monotonic()-start>920:
                    subprocess.run(['docker','stop','--time','5',name],capture_output=True,timeout=15);raise RuntimeError('resource or wall stop')
                time.sleep(2)
            assert p.wait()==0,'compile failed'
        assert '%Warning-' not in (out/'compile.log').read_text()
        sim=['docker','run','--rm','--init','--network','none','--cpus','2','--memory','8g','--memory-swap','8g',
             '--pids-limit','2048','--mount',f'type=bind,src={out},dst=/work',IMAGE,'timeout','120s','/work/obj/Vheader_index_pair']
        result['commands'].append(sim);r=subprocess.run(sim,text=True,capture_output=True,timeout=130)
        (out/'simulation.log').write_text(r.stdout+r.stderr);result['actual_RTL_run']=True;assert r.returncode==0,'simulation failed'
        verdict=json.loads(r.stdout);assert verdict['status']=='TEST_PASS' and verdict['fetch_purpose_mask']==15 and verdict['race_cases']==4
        assert all(sha(p)==hashes[rel(p)] and sha(snap/p.relative_to(ROOT))==hashes[rel(p)] for p in FILES)
        result.update(status='PASS',verdict=verdict,source_snapshot_unchanged=True,binary_sha256=sha(out/'obj/Vheader_index_pair'))
    except BaseException as e:
        result['failure']=repr(e);raise
    finally:
        result['artifacts']={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file() and p.name!='receipt.json'}
        write(out/'receipt.json',result);print(result['status'],rel(out/'receipt.json'),flush=True)

if __name__=='__main__':main()
