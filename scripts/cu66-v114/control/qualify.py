#!/usr/bin/env python3
"""Focused actual18-body V114 reservation/command/cancel/drain proof, Verilator."""
import argparse,datetime,gzip,hashlib,json,pathlib,shutil,subprocess,time
R=pathlib.Path(__file__).resolve().parents[3];S=R/'fpga/experiments/cu66-v114-control';A=R/'experiments/python-gamebub-v114/control'
BASE=R/'experiments/python-gamebub-v113/native/20261108T213919828839Z/receipt.json';GOLD=R/'experiments/python-gamebub-v113/spatial/attempts/20261108T212355592057Z/receipt.json';IMAGE='sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,j):p.write_text(json.dumps(j,indent=2,sort_keys=True)+'\n')
def memory():
 m={x.split(':')[0]:int(x.split()[1])*1024 for x in pathlib.Path('/proc/meminfo').read_text().splitlines()};p=next(x for x in pathlib.Path('/proc/pressure/memory').read_text().splitlines()if x.startswith('full '));return dict(available_bytes=m['MemAvailable'],psi_full_avg10=float(p.split('avg10=')[1].split()[0]))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run',action='store_true');a=ap.parse_args();card=json.loads(BASE.read_text())['source_contract'];g=json.loads(GOLD.read_text());aliases=card['source_order']['rtl_read_order_aliases']+[x for x in card['source_origins']if x.endswith('.svh')];assert len(aliases)==18
 sources=[]
 for alias in aliases:
  m=card['source_origins'][alias];p=R/m['path'];assert sha(p)==m['sha256'];sources.append(S/'cs88_pipeline_v91k.sv'if p.name=='cs88_pipeline_v91k.sv'else p)
 bench=R/'fpga/experiments/cu66-v107-elastic/verification/bench.cpp';pack=R/'fpga/experiments/cu66-v112-control/packaging.json';recipe=json.loads((S/'edit-recipe.json').read_text());assert sha(S/'cs88_pipeline_v91k.sv')==recipe['candidate_sha256']
 files=sorted(set(sources+[bench,S/'tb_control.cpp',S/'edit-recipe.json',S/'production.diff',pathlib.Path(__file__).resolve(),pathlib.Path(__file__).parent/'prepare.py',BASE,GOLD,pack]+[R/m['source']for m in g['inputs'].values()]))
 if not a.run:print('V114_CONTROL_PREPARED_NOT_RUN');return
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=A/'attempts'/stamp;out.mkdir(parents=True);build=pathlib.Path('/home/lori/gamebub-build/cu66-v69')/('v114-control-'+stamp);build.mkdir();mapped='/build/'+build.name
 r=dict(schema='v114-actual-full-top-reservation-focused-v1',status='FAIL',actual_RTL_run=False,backend='Verilator',strict_warnings=True,assertions_disabled_or_downgraded=False,old_bench_checks_removed=0,source_sha256={str(p.relative_to(R)):sha(p)for p in files},rtl_source_order=[str(p.relative_to(R))for p in sources],commands=[],runs=[],memory_samples=[],scope='Actual18-body top; accepted-command/cache/peer-fault tests, explicit adversarial prepared raw child fault/sequence fixtures, and unchanged canonical/memory/reference oracles on real accepted drain cancellation')
 def command(argv,name,cap):
  gate=memory();assert gate['available_bytes']>=8*1024**3 and gate['psi_full_avg10']<1,gate;container='gamebub-v114-control-'+stamp.lower()+'-'+str(len(r['commands']));cmd=['docker','run','--rm','--init','--name',container,'--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--network','none','--ulimit','core=0','--mount',f'type=bind,src={out},dst={out},readonly','--mount',f'type=bind,src={build},dst={mapped}','-w',mapped,IMAGE,'timeout','--kill-after=5s',str(cap)+'s',*argv];c=dict(argv=cmd,timeout_seconds=cap,resource_before=gate);r['commands'].append(c);t=time.monotonic()
  with(out/name).open('w')as f:
   p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT);hi=0
   while p.poll()is None:
    m=dict(command=name,elapsed_seconds=time.monotonic()-t,**memory());r['memory_samples'].append(m);hi=hi+1 if m['psi_full_avg10']>=5 else 0
    if m['available_bytes']<4*1024**3 or hi>=2 or m['elapsed_seconds']>cap+20:subprocess.run(['docker','stop','--timeout','5',container],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15);c['resource_stop']=m;break
    time.sleep(2)
   c.update(exit_code=p.wait(timeout=20),wall_seconds=time.monotonic()-t)
  assert c['exit_code']==0 and 'resource_stop'not in c,name
 try:
  for p in files:
   q=out/'sources'/p.relative_to(R);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
  snap=lambda p:str(out/'sources'/p.relative_to(R))
  shutil.copyfile(bench,build/'bench.cpp')
  for name,m in g['inputs'].items():
   p=R/m['source'];assert sha(p)==m['sha256'];b=gzip.decompress(p.read_bytes())if p.suffix=='.gz'else p.read_bytes();(build/name).write_bytes(b);assert sha(build/name)==m['expanded_sha256']
  packaging=json.loads(pack.read_text());admission=next(p for p in sources if p.name=='cs88_admission_v91i2a.sv');data=admission.read_bytes();assert sha(admission)==packaging['production_sha256'];offs=[0]+packaging['split_byte_offsets']+[len(data)];frags=[]
  for i,m in enumerate(packaging['fragments']):p=build/m['filename'];p.write_bytes(data[offs[i]:offs[i+1]]);assert sha(p)==m['sha256'];frags.append(p)
  assert b''.join(p.read_bytes()for p in frags)==data
  compiled=[mapped+'/'+frags[0].name if p==admission else snap(p)for p in sources if p.suffix=='.sv']+[mapped+'/'+p.name for p in frags[1:]]
  command(['verilator','--version'],'version.log',30)
  command(['verilator','--cc','--exe','--build','-j','1','--assert','-Wall','--public-flat-rw','--output-split','10000','--output-split-cfuncs','1000','--language','1800-2017','--top-module','cs88_pipeline_v91k','--Mdir',mapped+'/obj','-I'+str(out/'sources/fpga/experiments/cu66-v69/inverse'),'-CFLAGS','-std=c++17 -O1 -Wall -Wextra -Werror -DELASTIC=1 -I'+mapped,*compiled,snap(S/'tb_control.cpp')],'compile.log',900)
  assert '%Warning-'not in(out/'compile.log').read_text();r['binary_sha256']=sha(build/'obj/Vcs88_pipeline_v91k')
  for seed in (114101,114102):
   command([mapped+'/obj/Vcs88_pipeline_v91k',mapped+'/cases.tsv',mapped+'/transform_tiles.tsv',mapped+'/canonical_goldens.tsv',str(seed),mapped+f'/control-{seed}.jsonl'],f'control-{seed}.log',240);v=json.loads((out/f'control-{seed}.log').read_text().splitlines()[-1]);assert v['status']=='TEST_PASS'and v['real_physical_drain_checks']==4 and v['backdoor_fault_tests_declared']==7;r['runs'].append(v)
  assert r['source_sha256']=={str(p.relative_to(R)):sha(p)for p in files};r.update(status='PASS',actual_RTL_run=True,frozen_after_focused_PASS=True)
 except BaseException as e:r['error']=repr(e);raise
 finally:
  for p in build.glob('control-*.jsonl'):(out/(p.name+'.gz')).write_bytes(gzip.compress(p.read_bytes(),mtime=0))
  r['artifact_sha256']={str(p.relative_to(out)):sha(p)for p in sorted(out.rglob('*'))if p.is_file()};write(out/'results.json',r);write(A/'results.json',dict(r,selected_report=str((out/'results.json').relative_to(R)),selected_report_sha256=sha(out/'results.json')));print('V114_CONTROL',r['status'],out,flush=True)
if __name__=='__main__':main()
