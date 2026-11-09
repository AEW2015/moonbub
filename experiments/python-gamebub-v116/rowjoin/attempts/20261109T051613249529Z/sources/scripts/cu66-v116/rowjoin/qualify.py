#!/usr/bin/env python3
"""Root-dispatched bounded strict V116 three-slot rowjoin standalone proof."""
import argparse
import datetime
import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path
R=Path(__file__).resolve().parents[3]
S=R/'fpga/experiments/cu66-v116-rowjoin'
A=R/'experiments/python-gamebub-v116/rowjoin'
IMAGE='sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf'
CFLAGS='-std=c++17 -O2 -Wall -Wextra -Werror'
TOP='cu66_row_write_hash_join_v91l'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,q):p.write_text(json.dumps(q,sort_keys=True,indent=2)+'\n')
def rel(p):return str(p.relative_to(R))
def verify():
 q=json.loads((S/'source-manifest.json').read_text())
 for name,h in q['source_sha256'].items():assert sha(R/name)==h,name
 old=R/q['original'];new=S/(TOP+'.sv')
 # Public interface is text-exact; behavioral timing deliberately changes.
 def ports(p):return p.read_text().split('module '+TOP+' (',1)[1].split('\n);',1)[0]
 assert ports(old)==ports(new)
 assert new.read_text().count('logic [63:0] payload [0:2];')==1
 assert '--assert' in Path(__file__).read_text()
 assert ('-'+'Wno-fatal') not in Path(__file__).read_text()
 return q

def memory():
 m={x.split(':')[0]:int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines()}
 f=next(x for x in Path('/proc/pressure/memory').read_text().splitlines()if x.startswith('full '))
 return dict(available_bytes=m['MemAvailable'],PSI_full_avg10=float(f.split('avg10=')[1].split()[0]),combined_used_ratio=(m['MemTotal']-m['MemAvailable']+m['SwapTotal']-m['SwapFree'])/(m['MemTotal']+m['SwapTotal']))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run',action='store_true');args=ap.parse_args();manifest=verify()
 if not args.run:print('V116_ROWJOIN_PREPARED_NOT_RUN',sha(S/(TOP+'.sv')));return
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
 out=A/'attempts'/stamp;out.mkdir(parents=True)
 build=Path('/home/lori/gamebub-build/cu66-v69')/('v116-rowjoin-'+stamp);build.mkdir();mapped='/build/'+build.name
 files=sorted(set([p for p in S.rglob('*')if p.is_file()]+list(Path(__file__).parent.glob('*.py'))+[R/manifest['original']]))
 result=dict(schema='v116-rowjoin-three-slot-independent-standalone-v1',status='FAIL',actual_RTL_run=False,backend='Verilator 5.020',image_id=IMAGE,cflags=CFLAGS,source_sha256={rel(p):sha(p)for p in files},commands=[],runs=[],memory_samples=[],assertions_disabled_or_downgraded=False,original_assertions_retained=True,source_contract='Three eight-byte payload slots, one physical epoch/token/bank/address lease; ordered ACK-qualified metadata-exact byte expansion; warm kill/fault drains physical debt.',intentional_schedule_change=True,invalid_output_view='Raw outputs outside valid select the current owned/next slot; valid stalled tuples remain stable.',scope='Directed/random standalone simulation only; no parent integration, timing, native synthesis, physical SDRAM or FPGA performance claim.')
 began=time.monotonic()
 def receipt():write(out/'receipt.json',result)
 def command(argv,name,cap,rtl_run=False):
  gate=memory();assert gate['available_bytes']>=8*1024**3 and gate['PSI_full_avg10']<1 and gate['combined_used_ratio']<.85,gate
  container='gamebub-v116-rowjoin-'+stamp.lower()+'-'+str(len(result['commands']))
  cmd=['docker','run','--rm','--init','--name',container,'--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--network','none','--ulimit','core=0','--mount',f'type=bind,src={build},dst={mapped}','-w',mapped,IMAGE,'timeout','--kill-after=5s',str(cap)+'s',*argv]
  row=dict(argv=cmd,timeout_seconds=cap,resource_before=gate);result['commands'].append(row)
  if rtl_run:result['actual_RTL_run']=True
  receipt();start=time.monotonic();high=0
  with(out/name).open('w')as log:
   child=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
   while child.poll()is None:
    sample=dict(command=name,elapsed_seconds=time.monotonic()-start,**memory());result['memory_samples'].append(sample);high=high+1 if sample['PSI_full_avg10']>=5 else 0
    if sample['available_bytes']<4*1024**3 or high>=2 or sample['combined_used_ratio']>=.9 or sample['elapsed_seconds']>cap+20:
     row['resource_stop']=sample;subprocess.run(['docker','stop','--time','5',container],capture_output=True,timeout=15);break
    time.sleep(2)
   row.update(exit_code=child.wait(timeout=20),wall_seconds=time.monotonic()-start)
  receipt();assert row['exit_code']==0 and'resource_stop'not in row,name
 try:
  for p in files:
   snap=out/'sources'/p.relative_to(R);snap.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,snap)
  for p in (S/(TOP+'.sv'),S/'tb_rowjoin.cpp'):shutil.copyfile(p,build/p.name)
  command(['verilator','--version'],'version.log',30);assert 'Verilator 5.020' in(out/'version.log').read_text()
  command(['verilator','--cc','--exe','--build','-j','1','--assert','-Wall','--public-flat-rw','--language','1800-2017','-CFLAGS',CFLAGS,'--top-module',TOP,'--Mdir',mapped+'/obj',mapped+'/'+TOP+'.sv',mapped+'/tb_rowjoin.cpp'],'compile.log',600)
  assert '%Warning-'not in(out/'compile.log').read_text();result['binary_sha256']=sha(build/'obj'/('V'+TOP))
  for seed in (116501,116502,116503,116504):
   name=f'run-{seed}.log';command([mapped+'/obj/V'+TOP,str(seed)],name,60,rtl_run=True)
   entries=[json.loads(line)for line in(out/name).read_text().splitlines()];v=entries[-1]
   assert v['status']=='TEST_PASS'and v['directed_checks']==30 and v['exact_bytes']>=4096 and v['triple_overlap_cycles']>0 and v['same_edge_ack_hash_last_fill']>0 and v['wrong_ack_checks']==5
   assert sum(e.get('type')=='directed'and e.get('status')=='PASS'for e in entries)==30
   result['runs'].append(v);receipt()
  assert result['source_sha256']=={rel(p):sha(p)for p in files};result['status']='PASS'
 except BaseException as exc:result['error']=repr(exc);raise
 finally:
  result['wall_seconds']=time.monotonic()-began
  result['artifact_sha256']={str(p.relative_to(out)):sha(p)for p in sorted(out.rglob('*'))if p.is_file()and p.name!='receipt.json'}
  receipt();write(A/'results.json',dict(status=result['status'],path=rel(out/'receipt.json'),sha256=sha(out/'receipt.json')))
  print('V116_ROWJOIN',result['status'],out,flush=True)
if __name__=='__main__':main()
