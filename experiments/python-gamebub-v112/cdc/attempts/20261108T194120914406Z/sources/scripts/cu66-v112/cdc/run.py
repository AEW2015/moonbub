#!/usr/bin/env python3
"""Actual existing CDC fabric under proposed clock ratios; behavioral only."""
import datetime,gzip,hashlib,importlib.util,json,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];AREA=ROOT/'experiments/python-gamebub-v112/cdc';OLD=ROOT/'fpga/experiments/cu66-v107-cdc-sync'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):Path(p).write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def module(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
BASE=module(ROOT/'scripts/cu66-v107/cdc.py','cdc_original')
def replay(path):
 result=BASE.replay(path);owned=[0]*5;high=[0]*5;last=-1
 with gzip.open(path,'rt') as f:
  for line in f:
   t,op,ch,*rest=line.strip().split(',');t=int(t);ch=int(ch);assert t>=last;last=t
   if op=='E':owned=[0]*5
   elif op=='W':owned[ch]+=1;high[ch]=max(high[ch],owned[ch]);assert owned[ch]<=9
   else:owned[ch]-=1;assert owned[ch]>=0
 assert not any(owned);assert high==[9]*5,high
 return dict(**result,max_owned_words=high,time_unit='ps',last_event_ps=last)
def main():
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/stamp;out.mkdir(parents=True)
 build=Path('/home/lori/gamebub-build/cu66-v69')/('v112-cdc-ratios-'+stamp);build.mkdir()
 files=[*sorted(OLD.glob('*.sv')),OLD/'reset_contract.py',OLD/'tb_cdc.cpp',ROOT/'fpga/experiments/cu66-v112-cdc/tb_cdc.cpp',ROOT/'scripts/cu66-v107/cdc.py',Path(__file__).resolve()]
 selected=json.loads((ROOT/'experiments/python-gamebub-v107/cdc-sync/results.json').read_text());prior=ROOT/selected['selected_receipt'];assert sha(prior)==selected['sha256'];old_receipt=json.loads(prior.read_text())
 for p in OLD.glob('*.sv'):assert sha(p)==old_receipt['source_sha256'][str(p.relative_to(ROOT))]
 pins={str(p.relative_to(ROOT)):sha(p) for p in files};snap=out/'sources'
 for name in pins:
  target=snap/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,target)
 image=subprocess.check_output(['docker','image','inspect','--format','{{.Id}}','gamebub-cu66-v69-tools:20261105'],text=True).strip()
 r=dict(schema='v112-proposed-clock-cdc-behavioral-v1',status='RUNNING',actual_RTL_run=False,source_sha256=pins,image_content_id=image,external_build=str(build),baseline_receipt=dict(path=str(prior.relative_to(ROOT)),sha256=sha(prior)),DUT_RTL_byte_identical_to_V107=True,original_scoreboard_sha256=sha(OLD/'tb_cdc.cpp'),new_bench_changes='Integer-ps event scheduler and nominal/detuned clock profiles only; original payload/order/accounting/reset/stopped-clock/stall coverage assertions retained; RNG sampling frequency changes accepted workload',profiles={'nominal':dict(half_period_ps=[2500,4000,5000,17029]),'detuned':dict(half_period_ps=[2501,4001,5003,17031])},commands=[],runs=[],physical_CDC_qualified=False,parent_125MHz_qualified=False,hardware_contact=False)
 write(out/'reset-model.json',module(OLD/'reset_contract.py','reset_model').model())
 def cmd(argv,name,cap):
  container='v112-cdc-'+stamp.lower()+'-'+str(len(r['commands']))
  command=['docker','run','--rm','--init','--name',container,'--cpus','2','--memory','8g','--memory-swap','8g','--pids-limit','2048','--network','none','--ulimit','core=0','--mount',f'type=bind,src={snap},dst={snap},readonly','--mount',f'type=bind,src={build},dst={build}','-w',str(build),image,'timeout','--kill-after=5s',str(cap)+'s',*map(str,argv)]
  entry=dict(argv=command,timeout_seconds=cap);r['commands'].append(entry);write(out/'receipt.json',r);start=time.monotonic()
  with (out/name).open('w') as log:p=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=cap+30)
  entry.update(exit_code=p.returncode,wall_seconds=time.monotonic()-start);assert p.returncode==0,name
 try:
  assert BASE.resources()['available_bytes']>=8*1024**3
  cmd(['verilator','--version'],'version.log',30)
  rtl=[snap/str(p.relative_to(ROOT)) for p in sorted(OLD.glob('*.sv'))]
  cmd(['verilator','--cc','--exe','--build','-j','2','--assert','-Wall','--language','1800-2017','--top-module','v107_cdc_fabric','--Mdir',build/'obj','-CFLAGS','-std=c++17 -O2 -Wall -Wextra -Werror',*rtl,snap/'fpga/experiments/cu66-v112-cdc/tb_cdc.cpp'],'compile.log',180)
  assert '%Warning-' not in (out/'compile.log').read_text();binary=build/'obj/Vv107_cdc_fabric';r['binary_sha256']=sha(binary)
  for profile in (0,1):
   for seed in (107001,107002,107003):
    label=f'{profile}-{seed}';trace=build/(label+'.csv');cmd([binary,seed,trace,profile],label+'.log',30)
    assert f'TEST_PASS_CDC seed={seed}' in (out/(label+'.log')).read_text()
    with trace.open('rb') as src,(out/(label+'.csv.gz')).open('wb') as dest:
     with gzip.GzipFile(filename='',mode='wb',fileobj=dest,mtime=0) as z:shutil.copyfileobj(src,z)
    r['runs'].append(dict(profile=profile,seed=seed,replay=replay(out/(label+'.csv.gz'))));write(out/'receipt.json',r)
  assert all(sha(ROOT/n)==h and sha(snap/n)==h for n,h in pins.items())
  r.update(status='PASS_PROPOSED_RATIO_CDC_BEHAVIORAL_ONLY',actual_RTL_run=True,strict_compile_warning_count=0,source_unchanged=True)
 except Exception as e:r.update(status='FAIL',error=repr(e));raise
 finally:
  r['artifact_sha256']={p.name:sha(p) for p in out.iterdir() if p.is_file() and p.name!='receipt.json'};write(out/'receipt.json',r)
  write(AREA/'results.json',dict(schema=r['schema'],status=r['status'],selected_receipt=str((out/'receipt.json').relative_to(ROOT)),selected_sha256=sha(out/'receipt.json'),parent_125MHz_qualified=False,physical_CDC_qualified=False));print(r['status'],out)
if __name__=='__main__':main()
