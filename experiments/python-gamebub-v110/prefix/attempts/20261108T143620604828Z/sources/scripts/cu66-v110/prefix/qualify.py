#!/usr/bin/env python3
"""Complete old/new Rice parser and unchanged oracles; opt-in --run, never promotion."""
import argparse,datetime,gzip,hashlib,json,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];SRC=ROOT/'fpga/experiments/cu66-v110-prefix';AREA=ROOT/'experiments/python-gamebub-v110/prefix';IMAGE='gamebub-cu66-v69-tools:20261105';VECTORS=ROOT/'experiments/python-gamebub-v91/rtl-vectors/cases.jsonl.gz'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,j):p.write_text(json.dumps(j,indent=2,sort_keys=True)+'\n')
def memory():
 m={x.split(':')[0]:int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines()};f=next(x for x in Path('/proc/pressure/memory').read_text().splitlines() if x.startswith('full '));return dict(available_bytes=m['MemAvailable'],psi_full_avg10=float(f.split('avg10=')[1].split()[0]))
def verify():
 recipe=json.loads((SRC/'edit-recipe.json').read_text())
 for n,e in recipe['production'].items():
  p=ROOT/e['original'];q=ROOT/e['candidate'];assert sha(p)==e['original_sha256'] and sha(q)==e['candidate_sha256'];s=p.read_text()
  for x in e['edits']:assert s.count(x['before'])==1;s=s.replace(x['before'],x['after'],1)
  assert s==q.read_text()
  for x in reversed(e['edits']):assert s.count(x['after'])==1;s=s.replace(x['after'],x['before'],1)
  assert s==p.read_text();assert p.read_text().split('`ifndef SYNTHESIS',1)[1].rsplit('endmodule',1)[0] in q.read_text()
 a=json.loads((SRC/'verification/adapters.json').read_text())
 for e in a['adapters']:
  p=ROOT/e['source'];q=ROOT/e['path'];assert sha(p)==e['source_sha256'] and sha(q)==e['sha256'];s=p.read_text()
  for before,after in e['renames']:assert s.count(before)==1;s=s.replace(before,after,1)
  assert s==q.read_text()
 p=ROOT/a['historical_original'];assert sha(p)==a['historical_sha256'];s=p.read_text()
 for before,after in a['historical_renames']:assert before in s;s=s.replace(before,after)
 assert s==(SRC/'verification/historical_rice.cpp').read_text()
 p=ROOT/a['bench_original'];assert sha(p)==a['bench_original_sha256'];s=p.read_text()
 for before,after in a['bench_edits']:assert s.count(before)==1;s=s.replace(before,after,1)
 assert s==(SRC/'verification/tb_rice.cpp').read_text();assert json.loads((AREA/'model.json').read_text())['take_rows']==33280
 f=json.loads((SRC/'verification/fixture-adapter.json').read_text());p=ROOT/f['original'];assert sha(p)==f['sha256'];s=p.read_text()
 for e in f['edits']:assert s.count(e['before'])==1;s=s.replace(e['before'],e['after'],1)
 assert s==(SRC/'verification/tb_prefix.cpp').read_text()
 return recipe

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--run',action='store_true');args=ap.parse_args();recipe=verify()
 if not args.run:print('RICE_QUALIFICATION_PREPARED_NOT_RUN_NOT_SELECTED');return
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/stamp;out.mkdir(parents=True);build=Path('/home/lori/gamebub-build/cu66-v69')/('v110-prefix-'+stamp);build.mkdir();mapped='/build/'+build.name
 files=sorted(set([p for p in SRC.rglob('*') if p.is_file()]+[ROOT/e['original'] for e in recipe['production'].values()]+[p for p in Path(__file__).parent.glob('*.py')]+[AREA/'preparation.json',AREA/'model.json',VECTORS,ROOT/'fpga/experiments/cu66-v107-rice/tb_rice.cpp',ROOT/'fpga/experiments/cu66-v91/tb_rice.cpp']))
 r=dict(schema='v110-parallel-prefix-complete-parser-focused-v1',status='FAIL',actual_RTL_run=False,source_sha256={str(p.relative_to(ROOT)):sha(p) for p in files},production=[dict(path=e['candidate'],sha256=e['candidate_sha256']) for e in recipe['production'].values()],commands=[],runs=[],memory_samples=[],strict_warnings=True,warning_suppression=False,assertions_disabled_or_downgraded=False,added_public_cycles=0,selected_for_native=False,scope='Actual qualified V110 unmasked parser versus guarded parallel prefix take/rank simplification. Every public output including invalid data/counters, every raw stored register/reservoir and original golden/queue/parameter/malformed/reset/start/inactive tests retained. Only unused RHS rank-load expressions can differ outside selected write. No pipeline/native/hardware claim.')
 started=time.monotonic()
 def command(argv,name,cap):
  gate=memory();assert gate['available_bytes']>=8*1024**3 and gate['psi_full_avg10']<1,gate
  container='gamebub-v110-prefix-'+stamp.lower()+'-'+str(len(r['commands']));cmd=['docker','run','--rm','--init','--name',container,'--memory','4g','--memory-swap','4g','--cpus','2','--pids-limit','2048','--network','none','--ulimit','core=0','--mount',f'type=bind,src={build},dst={mapped}','-w',mapped,IMAGE,'timeout','--kill-after=5s',str(cap)+'s',*argv]
  e=dict(argv=cmd,resource_before=gate,timeout_seconds=cap);r['commands'].append(e);began=time.monotonic();stop=None;last=-5;pressure_breaches=0
  with (out/name).open('w') as log:
   proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
   while proc.poll() is None:
    elapsed=time.monotonic()-began
    if elapsed-last>=5:
     sample=dict(command=name,elapsed_seconds=elapsed,**memory());r['memory_samples'].append(sample);last=elapsed
     pressure_breaches=pressure_breaches+1 if sample['psi_full_avg10']>=5 else 0
     if sample['available_bytes']<4*1024**3 or pressure_breaches>=2:stop='HOST_MEMORY_GATE'
    if elapsed>cap+20:stop='HOST_TIMEOUT'
    if stop:subprocess.run(['docker','stop','--time','5',container],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15);break
    time.sleep(.5)
   code=proc.wait(timeout=20)
  e.update(exit_code=code,stop_reason=stop,wall_seconds=time.monotonic()-began);assert code==0 and not stop,(name,code,stop)
 try:
  for p in files:q=out/'sources'/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
  for p in (SRC/'verification').iterdir():shutil.copyfile(p,build/p.name)
  cases=requests=0
  with gzip.open(VECTORS,'rt') as src,(build/'vectors.txt').open('w') as dst:
   for line in src:
    c=json.loads(line);dst.write(f"{c['id']} {c['bit_size']} {c['data_hex'] or '-'} {len(c['requests'])}\n")
    for req in c['requests']:dst.write(' '.join(map(str,req))+'\n')
    cases+=1;requests+=len(c['requests'])
  r.update(historical_vector_cases=cases,historical_requests_per_configuration=requests,text_vectors_sha256=sha(build/'vectors.txt'))
  command(['verilator','--version'],'version.log',30)
  command(['verilator','--cc','--exe','--build','-j','1','--assert','-Wall','--public-flat-rw','--output-split','10000','--output-split-cfuncs','500','--language','1800-2017','-CFLAGS','-std=c++17 -O1 -Wall -Wextra -Werror','--top-module','rice_probe','--Mdir',mapped+'/obj',*[mapped+'/'+n for n in ('rice_original.sv','rice_candidate.sv','rice_probe.sv','tb_prefix.cpp')]],'compile.log',300)
  assert '%Warning-' not in (out/'compile.log').read_text();r['binary_sha256']=sha(build/'obj/Vrice_probe')
  for seed in (111101,111102):
   name=f'seed-{seed}.log';command([mapped+'/obj/Vrice_probe',str(seed),mapped+f'/seed-{seed}.jsonl',mapped+'/vectors.txt'],name,180)
   records=[json.loads(line) for line in (out/name).read_text().splitlines()];v=next(x for x in records if 'parameter_cases' in x);extra=records[-1];h=next(x for x in records if x.get('type')=='verdict')
   assert v['status']=='TEST_PASS' and v['prepared_clocks']>100000 and v['parameter_cases']==6096 and h['status']=='TEST_PASS' and h['cases']==cases and h['requests_per_configuration']==requests and h['configurations']==8 and h['directed_checks']>90;assert extra['status']=='TEST_PASS' and extra['cases']==8320 and extra['differing_unused_ranks']>100;r['runs'].append(dict(focused=v,historical=h,unowned=extra))
  assert r['source_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in files};r.update(status='PASS',actual_RTL_run=True,frozen_after_focused_PASS=True)
 except BaseException as e:r['error']=repr(e);raise
 finally:
  for p in build.glob('seed-*.jsonl'):
   with p.open('rb') as source,(out/(p.name+'.gz')).open('wb') as dest:
    with gzip.GzipFile(filename='',fileobj=dest,mode='wb',mtime=0) as z:shutil.copyfileobj(source,z)
  r['wall_seconds']=time.monotonic()-started;r['artifacts_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()};write(out/'results.json',r);write(AREA/'results.json',dict(r,selected_report=str((out/'results.json').relative_to(ROOT)),selected_report_sha256=sha(out/'results.json')));print('RICE_FOCUSED',r['status'],out,flush=True)
if __name__=='__main__':main()
