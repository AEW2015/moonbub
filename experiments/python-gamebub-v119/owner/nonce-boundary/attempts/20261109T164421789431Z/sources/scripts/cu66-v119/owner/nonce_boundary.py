#!/usr/bin/env python3
"""Source-bound reuse of a qualified actual Verilator model for additional nonce boundaries."""
import argparse,datetime,hashlib,json,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
AREA=ROOT/'experiments/python-gamebub-v119/owner/nonce-boundary'
SELECTOR=ROOT/'experiments/python-gamebub-v119/owner/producer/results.json'
BENCH=ROOT/'fpga/experiments/cu66-v119-owner/nonce-boundary-verification/tb_boundary.cpp'
IMAGE='sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def rel(p):return str(Path(p).resolve().relative_to(ROOT))
def write(p,x):Path(p).write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def memory():
 m={s.split(':')[0]:int(s.split()[1])*1024 for s in Path('/proc/meminfo').read_text().splitlines()};p=next(s for s in Path('/proc/pressure/memory').read_text().splitlines()if s.startswith('full '))
 return dict(available_bytes=m['MemAvailable'],psi_full_avg10=float(p.split('avg10=')[1].split()[0]),combined_used_ratio=(m['MemTotal']-m['MemAvailable']+m['SwapTotal']-m['SwapFree'])/(m['MemTotal']+m['SwapTotal']))
def prepare():
 if not SELECTOR.exists():raise SystemExit('PREREQUISITES_NOT_READY: qualified producer selector')
 q=load(SELECTOR);assert q['status']=='PASS'and q['actual_RTL_run']is True
 p=ROOT/q['path'];assert sha(p)==q['sha256'];d=load(p);assert d['status']=='PASS'and d['actual_RTL_run']is True
 for n,h in d['source_sha256'].items():assert sha(ROOT/n)==h,n
 for n,h in d.get('artifact_sha256',d.get('artifacts_sha256',{})).items():assert sha(p.parent/n)==h,n
 commands=d['commands'];compile_rows=[x['argv']for x in commands if 'verilator'in x['argv']and'--cc'in x['argv']]
 assert len(compile_rows)==1
 c=compile_rows[0];assert '--assert'in c and '-Wall'in c and '-Wno-fatal'not in c and '-Werror'in c[c.index('-CFLAGS')+1]
 assert IMAGE in c and d.get('assertions_disabled_or_downgraded')is False
 stamp=p.parent.name;datetime.datetime.strptime(stamp,'%Y%m%dT%H%M%S%fZ')
 build=Path('/home/lori/gamebub-build/cu66-v69')/('v119-owner-producer-'+stamp);obj=build/'ready-obj'
 assert c[c.index('--Mdir')+1]=='/build/'+build.name+'/ready-obj'
 assert sha(obj/'Vready_probe')==d['binary_sha256']
 archive=obj/'Vready_probe__ALL.a';assert archive.is_file()
 listing=subprocess.check_output(['ar','t',str(archive)],text=True).splitlines();assert listing and not any('tb_'in x for x in listing)
 assets=sorted([*obj.glob('*.h'),archive,*obj.glob('verilated*.o')]);assert len(assets)>5
 assert {p.name for p in assets}>={'Vready_probe.h','Vready_probe___024root.h','Vready_probe_cs88_admission_v91i2a.h','verilated.o','verilated_threads.o'}
 for name in ('tb_ready.cpp','tb_owner.cpp','ready_original.sv','ready_candidate.sv','ready_probe.sv'):
  current=ROOT/'fpga/experiments/cu66-v119-owner/producer-verification'/name;assert sha(build/name)==sha(current)==d['source_sha256'][rel(current)]
 return q,p,d,build,assets

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run',action='store_true');ap.add_argument('--root-grant');args=ap.parse_args();q,parent,d,parentbuild,assets=prepare()
 if not args.run:print('V119_NONCE_BOUNDARY_PREPARED_NOT_RUN');return
 assert args.root_grant,'Root heavy-slot grant required'
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/stamp;out.mkdir(parents=True);build=Path('/home/lori/gamebub-build/cu66-v69')/('v119-nonce-boundary-'+stamp);build.mkdir();(build/'model').mkdir();mapped='/build/'+build.name
 paths=sorted(set([BENCH,SELECTOR,parent,Path(__file__).resolve(),ROOT/'fpga/experiments/cu66-v119-owner/producer-verification/tb_ready.cpp',*[ROOT/n for n in d['source_sha256']]]))
 r=dict(schema='v119-source-bound-reused-model-nonce-boundary-v1',status='FAIL',actual_RTL_run=False,backend='Verilator 5.020 model, strict C++ auxiliary',image_id=IMAGE,root_grant=args.root_grant,model_reused=True,fresh_candidate_model_claim=False,assertions_disabled_or_downgraded=False,primary_producer_receipt=dict(path=rel(parent),sha256=sha(parent)),primary_producer_selector=dict(path=rel(SELECTOR),sha256=sha(SELECTOR)),primary_model_binary_sha256=d['binary_sha256'],primary_archive_members=subprocess.check_output(['ar','t',str(parentbuild/'ready-obj/Vready_probe__ALL.a')],text=True).splitlines(),source_sha256={rel(p):sha(p)for p in paths},model_artifacts={str(p):dict(sha256=sha(p),bytes=p.stat().st_size)for p in assets},commands=[],runs=[],memory_samples=[],scope='Additional prepared CHECK_ENTROPY nonce FC/FD/FE/FF/needed0..3/entropy priority and real reset/abort edges on the exact qualified producer model. Original full producer proof remains separate. No fabricated physical lease or frame/clock claim.')
 began=time.monotonic()
 def command(argv,name,cap,simulation=False):
  gate=memory();assert gate['available_bytes']>=8*1024**3 and gate['psi_full_avg10']<1 and gate['combined_used_ratio']<.85,gate
  cmd=['docker','run','--rm','--init','--name','gamebub-v119-nonce-boundary-'+stamp.lower()+'-'+str(len(r['commands'])),'--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--network','none','--ulimit','core=0','--mount',f'type=bind,src={build},dst={mapped}','-w',mapped,IMAGE,'timeout','--kill-after=5s',str(cap)+'s',*argv]
  row=dict(argv=cmd,timeout_seconds=cap,resource_before=gate);r['commands'].append(row)
  if simulation:r['actual_RTL_run']=True
  write(out/'receipt.json',r);start=time.monotonic();high=0
  with(out/name).open('w')as log:
   p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
   while p.poll()is None:
    sample=dict(elapsed_seconds=time.monotonic()-start,**memory());r['memory_samples'].append(sample);high=high+1 if sample['psi_full_avg10']>=5 else 0
    if sample['available_bytes']<4*1024**3 or high>=2 or sample['combined_used_ratio']>=.9 or sample['elapsed_seconds']>cap+20:
     subprocess.run(['docker','stop','--time','5',cmd[cmd.index('--name')+1]],capture_output=True,timeout=15);row['resource_stop']=sample;break
    time.sleep(1)
   row.update(exit_code=p.wait(timeout=20),wall_seconds=time.monotonic()-start)
  assert row['exit_code']==0 and 'resource_stop'not in row,name
 try:
  for p in paths:
   target=out/'sources'/p.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
  for p in assets:shutil.copyfile(p,build/'model'/p.name)
  shutil.copyfile(BENCH,build/'tb_boundary.cpp');shutil.copyfile(ROOT/'fpga/experiments/cu66-v119-owner/producer-verification/tb_ready.cpp',build/'tb_ready.cpp')
  command(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror','-I'+mapped+'/model','-I'+mapped,'-isystem','/usr/share/verilator/include','-isystem','/usr/share/verilator/include/vltstd',mapped+'/tb_boundary.cpp',mapped+'/model/Vready_probe__ALL.a',*[mapped+'/model/'+p.name for p in assets if p.suffix=='.o'],'-pthread','-latomic','-o',mapped+'/nonce-boundary'],'compile.log',300)
  r['auxiliary_binary_sha256']=sha(build/'nonce-boundary')
  for seed in (119661,119662):
   log=f'run-{seed}.log';command([mapped+'/nonce-boundary',str(seed)],log,120,simulation=True);rows=[json.loads(l)for l in(out/log).read_text().splitlines()];assert len(rows)==1;v=rows[0];assert v['status']=='TEST_PASS'and v['cases']==2048 and v['fd_cases']==512 and v['reset_abort_cases']==3 and v['physical_request_accepts']==0 and v['model_reused']is True
   r['runs'].append(v)
  assert r['source_sha256']=={rel(p):sha(p)for p in paths}
  for name,meta in r['model_artifacts'].items():assert sha(Path(name))==meta['sha256']
  r['status']='PASS'
 except BaseException as e:r['error']=repr(e);raise
 finally:
  r['wall_seconds']=time.monotonic()-began;r['artifact_sha256']={str(p.relative_to(out)):sha(p)for p in out.rglob('*')if p.is_file()and p.name!='receipt.json'};write(out/'receipt.json',r);write(AREA/'results.json',dict(status=r['status'],actual_RTL_run=r['actual_RTL_run'],path=rel(out/'receipt.json'),sha256=sha(out/'receipt.json')));print('V119_NONCE_BOUNDARY',r['status'],out,flush=True)
if __name__=='__main__':main()
