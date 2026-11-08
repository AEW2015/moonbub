#!/usr/bin/env python3
import argparse,datetime,gzip,hashlib,json,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];SRC=ROOT/'fpga/experiments/cu66-v109-request';AREA=ROOT/'experiments/python-gamebub-v109/request';IMAGE='gamebub-cu66-v69-tools:20261105'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def mem():
 m={x.split(':')[0]:int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines()};f=next(x for x in Path('/proc/pressure/memory').read_text().splitlines() if x.startswith('full '));return dict(available_bytes=m['MemAvailable'],psi_full_avg10=float(f.split('avg10=')[1].split()[0]))
def verify():
 recipe=json.loads((SRC/'edit-recipe.json').read_text())
 for n,e in recipe['production'].items():
  old=ROOT/e['original'];new=SRC/n;assert sha(old)==e['original_sha256'] and sha(new)==e['candidate_sha256'];t=old.read_text()
  for x in e['edits']:assert t.count(x['before'])==1;t=t.replace(x['before'],x['after'],1)
  assert t==new.read_text()
 a=json.loads((SRC/'verification/adapters.json').read_text())
 for x in a['adapters']:
  old=ROOT/x['source'];new=ROOT/x['path'];assert sha(old)==x['source_sha256'] and sha(new)==x['sha256'];t=old.read_text()
  for before,after in x['renames']:assert t.count(before)==1;t=t.replace(before,after,1)
  assert t==new.read_text()
 for name,h in a['inherited_frozen_fixture_files'].items():
  frozen=ROOT/'fpga/experiments/cu66-v109-fetch/verification'/name
  assert sha(frozen)==h and (SRC/'verification'/name).read_bytes()==frozen.read_bytes()
 fixture=ROOT/a['fixture_source'];assert sha(fixture)==a['fixture_source_sha256'];t=fixture.read_text()
 for before,after in a['fixture_edits']:assert t.count(before)==1;t=t.replace(before,after,1)
 assert t==(SRC/'verification/tb_fetch.cpp').read_text() and sha(SRC/'verification/tb_fetch.cpp')==a['fixture_sha256']
 return recipe

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run',action='store_true');args=ap.parse_args();recipe=verify()
 if not args.run:print('REQUEST_SOURCE_VERIFIED_NOT_RUN');return
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/stamp;out.mkdir(parents=True);build=Path('/home/lori/gamebub-build/cu66-v69')/('v109-request-'+stamp);build.mkdir();mapped='/build/'+build.name
 deps=[ROOT/'fpga/experiments/cu66-v106-context/br88_context.sv',ROOT/'fpga/experiments/cu66-v107-rice/br88_rice_elastic.sv'];vectors=ROOT/'experiments/python-gamebub-v91e/vectors/coefficients.jsonl.gz';files=[p for p in SRC.rglob('*') if p.is_file()]+deps+[vectors]+[ROOT/e['original'] for e in recipe['production'].values()]+[p for p in Path(__file__).parent.iterdir() if p.suffix=='.py']
 r=dict(schema='v109-request-focused-qualification-v1',status='FAIL',actual_RTL_run=False,source_sha256={str(p.relative_to(ROOT)):sha(p) for p in files},production=[dict(path=str((SRC/n).relative_to(ROOT)),sha256=e['candidate_sha256']) for n,e in recipe['production'].items()],commands=[],capture_runs=[],whole_ingress_runs=[],negative_owner_contract_rejections=[],strict_warnings=True,scope='Complete original/new actual synchronous ingress every public port including invalid/debug/counters; unchanged capture oracle except coherent synthetic prior-request field, original negative assertions, independent whole-packet sparse/raw goldens and actual request/response address scoreboard. No native/timing/board claim.')
 def cmd(argv,name,cap,negative=False):
  gate=mem();assert gate['available_bytes']>=8*1024**3 and gate['psi_full_avg10']<1,gate
  container='gamebub-v109-request-'+stamp.lower()+'-'+str(len(r['commands']));command=['docker','run','--rm','--init','--name',container,'--memory','4g','--memory-swap','4g','--cpus','2','--pids-limit','2048','--network','none','--ulimit','core=0','--mount',f'type=bind,src={ROOT},dst={ROOT},readonly','--mount',f'type=bind,src={build},dst={mapped}','-w',mapped,IMAGE,'timeout','--kill-after=5s',str(cap)+'s',*argv];entry=dict(argv=command,resource_before=gate,timeout_seconds=cap);r['commands'].append(entry);start=time.monotonic();stop=None
  with (out/name).open('w') as log:
   proc=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
   while proc.poll() is None:
    gate=mem()
    if gate['available_bytes']<4*1024**3 or gate['psi_full_avg10']>=5:stop='HOST_MEMORY_GATE'
    if time.monotonic()-start>cap+20:stop='HOST_TIMEOUT'
    if stop:subprocess.run(['docker','stop','--time','5',container],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15);break
    time.sleep(.5)
   code=proc.wait(timeout=20)
  entry.update(exit_code=code,stop_reason=stop,wall_seconds=time.monotonic()-start);write(out/'progress.json',r)
  if negative:
   t=(out/name).read_text();assert code==134 and not stop and 'stale staging response' in t and 'EXPECTED_ASSERTION_ARMED' in t and '"capture_enable":false' in t,name;entry['status']='PASS_EXPECTED_ORIGINAL_ASSERTION_REJECTION'
  else:assert code==0 and not stop,name
 try:
  for p in files:q=out/'sources'/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
  for p in (SRC/'verification').iterdir():
   if p.is_file():shutil.copyfile(p,build/p.name)
  for p in deps:shutil.copyfile(p,build/p.name)
  cases=[json.loads(x) for x in gzip.decompress(vectors.read_bytes()).splitlines()];(build/'vectors.txt').write_text(''.join(' '.join(map(str,(x['id'],x['blocks'],x['packet_hex'],x['dense_hex'],x['packed_hex'])))+'\n' for x in cases))
  cmd(['verilator','--version'],'version.log',30);flags=['verilator','--cc','--exe','--build','-j','1','--assert','-Wall','--public-flat-rw','--output-split','10000','--output-split-cfuncs','500','--language','1800-2017','-CFLAGS','-std=c++17 -O1 -Wall -Wextra -Werror','--top-module','ingress_capture_probe','--Mdir',mapped+'/obj']
  cmd([*flags,*[mapped+'/'+n for n in ('ingress_original.sv','ingress_candidate.sv','ingress_capture_probe.sv','br88_context.sv','br88_rice_elastic.sv','tb_fetch.cpp')]],'compile.log',600);assert '%Warning-' not in (out/'compile.log').read_text()
  for seed in (109601,109602):
   name=f'capture-{seed}.json';cmd([mapped+'/obj/Vingress_capture_probe',str(seed),mapped+f'/capture-{seed}.csv'],name,120);v=json.loads((out/name).read_text().splitlines()[-1]);assert v['status']=='TEST_PASS' and v['positive_prepared_cases']==1728 and v['actual_raw_packets']==8 and v['high32_metadata_owners']==128 and v['capture_edge_abort_restarts']==3 and v['held_metadata_edges']==2312;r['capture_runs'].append(v)
  for mode in (1,2):
   for index in (33,37,41):
    name=f'negative-{mode}-{index}.log';cmd([mapped+'/obj/Vingress_capture_probe','109601',mapped+'/negative.csv',str(mode),str(index)],name,30,True);r['negative_owner_contract_rejections'].append(dict(mode=mode,index=index,status='PASS_EXPECTED_ORIGINAL_ASSERTION_REJECTION'))
  for seed in (109601,109602):
   name=f'whole-{seed}.json';cmd([mapped+'/obj/Vingress_capture_probe',str(seed),mapped+'/unused.csv',mapped+'/vectors.txt'],name,240);v=json.loads((out/name).read_text().splitlines()[-1]);assert v['status']=='TEST_PASS' and v['packets']==76 and v['cancel_retries']==36 and v['prepared_actual_requests']==8 and v['boundary_mask']==15 and all(v['purpose_responses']);r['whole_ingress_runs'].append(v)
  assert r['source_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in files};r.update(status='PASS',actual_RTL_run=True,frozen_after_focused_PASS=True)
 except BaseException as e:r['error']=repr(e);raise
 finally:
  for p in build.glob('*.csv'):
   with p.open('rb') as source,gzip.open(out/(p.name+'.gz'),'wb') as dest:shutil.copyfileobj(source,dest)
  r['artifacts_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()};write(out/'results.json',r);write(AREA/'results.json',dict(r,selected_report=str((out/'results.json').relative_to(ROOT)),selected_report_sha256=sha(out/'results.json')));print('REQUEST_QUALIFICATION',r['status'],flush=True)
if __name__=='__main__':main()
