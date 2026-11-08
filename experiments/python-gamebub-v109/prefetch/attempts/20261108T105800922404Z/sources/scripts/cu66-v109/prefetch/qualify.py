#!/usr/bin/env python3
"""Exact-cycle complete scratch/four-body qualification; opt-in RTL execution."""
import argparse,datetime,gzip,hashlib,json,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];SRC=ROOT/'fpga/experiments/cu66-v109-prefetch';AREA=ROOT/'experiments/python-gamebub-v109/prefetch';IMAGE='gamebub-cu66-v69-tools:20261105'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def memory():
 m={x.split(':')[0]:int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines()};f=next(x for x in Path('/proc/pressure/memory').read_text().splitlines() if x.startswith('full '));return dict(available_bytes=m['MemAvailable'],psi_full_avg10=float(f.split('avg10=')[1].split()[0]))
def verify():
 recipe=json.loads((SRC/'edit-recipe.json').read_text())
 for n,e in recipe['production'].items():
  old=ROOT/e['original'];new=SRC/n;assert sha(old)==e['original_sha256'] and sha(new)==e['candidate_sha256'];text=old.read_text()
  for edit in e['edits']:assert text.count(edit['before'])==1;text=text.replace(edit['before'],edit['after'],1)
  assert text==new.read_text()
 for e in json.loads((SRC/'verification/adapters.json').read_text())['adapters']:
  old=ROOT/e['source'];new=ROOT/e['path'];assert sha(old)==e['source_sha256'] and sha(new)==e['sha256'];text=old.read_text()
  for before,after in e['renames']:assert text.count(before)==1;text=text.replace(before,after,1)
  assert text==new.read_text()
 for n in ('tb_scratch.cpp','historical_hazards.cpp'):assert (SRC/'verification'/n).read_bytes()==(ROOT/'fpga/experiments/cu66-v106-scratch'/n).read_bytes()
 for n in ('tb_prefix.cpp','prefix_probe.sv'):assert (SRC/'verification'/n).read_bytes()==(ROOT/'fpga/experiments/cu66-v108-capacity/verification'/n).read_bytes()
 return recipe

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--run',action='store_true');args=ap.parse_args();recipe=verify()
 if not args.run:print('PREFETCH_QUALIFICATION_PREPARED_NOT_RUN');return
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/stamp;out.mkdir(parents=True);build=Path('/home/lori/gamebub-build/cu66-v69')/('v109-prefetch-'+stamp);build.mkdir();mapped='/build/'+build.name
 deps=[ROOT/p for p in ('fpga/experiments/cu66-v107-rice/br88_rice_elastic.sv','fpga/experiments/cu66-v106-context/br88_context.sv','fpga/experiments/cu66-v91d/br88_packet_ingress.sv')];vectors=ROOT/'experiments/python-gamebub-v91e/vectors/coefficients.jsonl.gz'
 files=[p for p in SRC.rglob('*') if p.is_file()]+[ROOT/e['original'] for e in recipe['production'].values()]+deps+[vectors]+[p for p in Path(__file__).parent.iterdir() if p.is_file() and p.suffix=='.py']
 files += [ROOT/'fpga/experiments/cu66-v108-capacity'/n for n in ('br88_pipeline_v91h.sv','br88_packet_ingress_v91h.sv','br88_packet_ingress_sync_v91h.sv')]
 r=dict(schema='v109-prefetch-focused-qualification-v1',status='FAIL',actual_RTL_run=False,source_sha256={str(p.relative_to(ROOT)):sha(p) for p in files},production=[dict(path=str((SRC/n).relative_to(ROOT)),sha256=e['candidate_sha256']) for n,e in recipe['production'].items()],commands=[],scratch_runs=[],runs=[],strict_warnings=True,scope='Complete production scratch and four-body exact every-cycle public/debug/counter/memory request comparison with unchanged independent dense/golden/hazard oracles; SYNC=0 and1. No full-pixel/native/timing/board claim.')
 def command(argv,name,cap):
  gate=memory();assert gate['available_bytes']>=8*1024**3 and gate['psi_full_avg10']<1,gate
  container='gamebub-v109-prefetch-'+stamp.lower()+'-'+str(len(r['commands']));cmd=['docker','run','--rm','--init','--name',container,'--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--network','none','--ulimit','core=0','--mount',f'type=bind,src={ROOT},dst={ROOT},readonly','--mount',f'type=bind,src={build},dst={mapped}','-w',mapped,IMAGE,'timeout','--kill-after=5s',str(cap)+'s',*argv];entry=dict(argv=cmd,resource_before=gate,timeout_seconds=cap);r['commands'].append(entry);start=time.monotonic();stop=None
  with (out/name).open('w') as log:
   proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
   while proc.poll() is None:
    gate=memory()
    if gate['available_bytes']<4*1024**3 or gate['psi_full_avg10']>=5:stop='HOST_MEMORY_GATE'
    if time.monotonic()-start>cap+20:stop='HOST_TIMEOUT'
    if stop:subprocess.run(['docker','stop','--time','5',container],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15);break
    time.sleep(.5)
   code=proc.wait(timeout=20)
  entry.update(exit_code=code,stop_reason=stop,wall_seconds=time.monotonic()-start);write(out/'progress.json',r);assert code==0 and not stop,name
 try:
  for p in files:q=out/'sources'/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
  for p in (SRC/'verification').iterdir():
   if p.is_file():shutil.copyfile(p,build/p.name)
  for p in deps:shutil.copyfile(p,build/p.name)
  cases=[json.loads(line) for line in gzip.decompress(vectors.read_bytes()).splitlines()];(build/'vectors.txt').write_text(''.join(' '.join(map(str,(x['id'],x['blocks'],x['packet_hex'],x['dense_hex'],x['packed_hex'])))+'\n' for x in cases))
  command(['verilator','--version'],'version.log',30);cflags='-std=c++17 -O1 -Wall -Wextra -Werror';flags=['verilator','--cc','--exe','--build','-j','1','--assert','-Wall','--output-split','10000','--output-split-cfuncs','500','--language','1800-2017','-CFLAGS',cflags]
  command([*flags,'--top-module','scratch_probe','--Mdir',mapped+'/scratch-obj',*[mapped+'/'+n for n in ('observed_original.sv','observed_candidate.sv','scratch_probe.sv','tb_scratch.cpp')]],'scratch-compile.log',600);assert '%Warning-' not in (out/'scratch-compile.log').read_text()
  for seed in (109301,109302):
   log=f'scratch-{seed}.jsonl';command([mapped+'/scratch-obj/Vscratch_probe',str(seed),mapped+f'/scratch-{seed}.jsonl'],log,180);v=json.loads((out/log).read_text().splitlines()[-1]);assert v['status']=='TEST_PASS' and v['full_transactions']==72 and v['corrupt_response_cases']==128 and v['read_owner_cases']==4 and v['bank_mask']==15 and v['offset_mask']==65535;r['scratch_runs'].append(v)
  sv=[mapped+'/'+kind+'_'+variant+'.sv' for kind in ('ingress','packet','scratch','pipeline') for variant in ('original','candidate')]+[mapped+'/prefix_probe.sv']+[mapped+'/'+p.name for p in deps]
  for sync in (1,0):
   command([*flags,'--top-module','prefix_probe','-GSYNC_STAGING='+str(sync),'--Mdir',mapped+'/pair-'+str(sync),'-CFLAGS',cflags+' -DSYNC_STAGING='+str(sync),*sv,mapped+'/tb_prefix.cpp'],f'pair-{sync}-compile.log',600);assert '%Warning-' not in (out/f'pair-{sync}-compile.log').read_text()
   for seed in (109301,109302):
    log=f'pair-{sync}-{seed}.jsonl';command([mapped+f'/pair-{sync}/Vprefix_probe',mapped+'/vectors.txt',str(seed)],log,180);records=[json.loads(line) for line in (out/log).read_text().splitlines()];v=records[-1];history=next(x for x in records if x.get('type')=='verdict');assert v['status']==history['status']=='TEST_PASS' and history['packets']==len(cases) and history['configurations']==2;r['runs'].append(dict(sync_staging=sync,seed=seed,pair=v,historical=history))
  assert r['source_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in files};r.update(status='PASS',actual_RTL_run=True,frozen_after_focused_PASS=True)
 except BaseException as e:r['error']=repr(e);raise
 finally:
  for p in build.glob('scratch-*.jsonl'):
   with p.open('rb') as source,gzip.open(out/(p.name+'.gz'),'wb') as dest:shutil.copyfileobj(source,dest)
  r['artifacts_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()};write(out/'results.json',r);write(AREA/'results.json',dict(r,selected_report=str((out/'results.json').relative_to(ROOT)),selected_report_sha256=sha(out/'results.json')));print('PREFETCH_QUALIFICATION',r['status'],flush=True)
if __name__=='__main__':main()
