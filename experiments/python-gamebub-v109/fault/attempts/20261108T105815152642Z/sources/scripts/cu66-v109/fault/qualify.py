#!/usr/bin/env python3
"""Strict actual V108/new complete inverse and reconstruction proof; --run required."""
import argparse,datetime,gzip,hashlib,json,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];SRC=ROOT/'fpga/experiments/cu66-v109-fault';AREA=ROOT/'experiments/python-gamebub-v109/fault'
IMAGE='gamebub-cu66-v69-tools:20261105'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,j):p.write_text(json.dumps(j,indent=2,sort_keys=True)+'\n')
def memory():
 m={x.split(':')[0]:int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines()};f=next(x for x in Path('/proc/pressure/memory').read_text().splitlines() if x.startswith('full '));return dict(available_bytes=m['MemAvailable'],psi_full_avg10=float(f.split('avg10=')[1].split()[0]))
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--run',action='store_true');args=ap.parse_args()
 recipe=json.loads((SRC/'edit-recipe.json').read_text());model=json.loads((AREA/'model.json').read_text());assert model['status']=='PASS_STRUCTURAL_INDUCTION_AND_CONTROL_MODEL_NOT_RTL'
 for n,h in model['source_sha256'].items():assert sha(ROOT/n)==h
 for e in recipe['production'].values():assert sha(ROOT/e['candidate'])==e['candidate_sha256']
 if not args.run:print('FAULT_QUALIFICATION_PREPARED_NOT_RUN');return
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/stamp;out.mkdir(parents=True)
 build=Path('/home/lori/gamebub-build/cu66-v69')/('v109-fault-'+stamp);build.mkdir();mapped='/build/'+build.name
 card=json.loads((ROOT/recipe['baseline_receipt']).read_text());math=[ROOT/m['path'] for a,m in card['source_origins'].items() if Path(a).name in ('cu66_dequant.sv','cu66_idct8x8.sv','cu66_quant_rom.svh','cu66_reconstruct_tile.sv')]
 assert len(math)==4;boundary=ROOT/'experiments/python-gamebub-v91j/vectors/boundary.tsv'
 files=sorted(set([p for p in SRC.rglob('*') if p.is_file()]+[p for p in Path(__file__).parent.glob('*.py')]+math+[boundary,AREA/'model.json',AREA/'preparation.json',ROOT/recipe['baseline_receipt']]+[ROOT/e['original'] for e in recipe['production'].values()]+[ROOT/'fpga/experiments/cu66-v107-meta-flags/verification'/n for n in ('tb_inverse.cpp','historical_inverse.cpp','locality_probe.sv')]+[ROOT/'fpga/experiments/cu66-v104-control'/n for n in ('tb_control.cpp','control_probe.sv','adapter.json')]))
 r=dict(schema='v109-same-edge-owned-fault-focused-v1',status='FAIL',actual_RTL_run=False,source_sha256={str(p.relative_to(ROOT)):sha(p) for p in files},production=[dict(path=e['candidate'],sha256=e['candidate_sha256']) for e in recipe['production'].values()],substitutions=[dict(alias=e['alias'],original=e['original'],candidate=e['candidate']) for e in recipe['production'].values()],baseline_receipt=dict(path=recipe['baseline_receipt'],sha256=recipe['baseline_receipt_sha256']),commands=[],inverse_runs=[],reconstruction_runs=[],memory_samples=[],strict_warnings=True,assertions_disabled_or_downgraded=False,added_public_cycles=0,limits=['Actual selected V108 complete inverse and reconstruction pair; every public/invalid/debug/counter check remains active.','Producer and top use source-level induction for every error NBA plus control truth table; full canonical pipeline remains a separate required root run.','Verification-only inverse internal preparations are declared; no arbitrary-state/four-state proof or physical timing conclusion.'])
 started=time.monotonic()
 def command(argv,name,cap):
  gate=memory();assert gate['available_bytes']>=6*1024**3 and gate['psi_full_avg10']<1,gate
  container='gamebub-v109-fault-'+stamp.lower()+'-'+str(len(r['commands']))
  cmd=['docker','run','--rm','--init','--name',container,'--memory','4g','--memory-swap','4g','--cpus','2','--pids-limit','2048','--network','none','--ulimit','core=0','--mount',f'type=bind,src={build},dst={mapped}','-w',mapped,IMAGE,'timeout','--kill-after=5s',str(cap)+'s',*argv]
  e=dict(argv=cmd,resource_before=gate,timeout_seconds=cap);r['commands'].append(e);began=time.monotonic();stop=None;last=-5
  with (out/name).open('w') as log:
   proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
   while proc.poll() is None:
    elapsed=time.monotonic()-began
    if elapsed-last>=5:
     sample=dict(command=name,elapsed_seconds=elapsed,**memory());r['memory_samples'].append(sample);last=elapsed
     if sample['available_bytes']<3*1024**3 or sample['psi_full_avg10']>=5:stop='HOST_MEMORY_GATE'
    if elapsed>cap+20:stop='HOST_TIMEOUT'
    if stop:subprocess.run(['docker','stop','--time','5',container],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15);break
    time.sleep(.5)
   code=proc.wait(timeout=20)
  e.update(exit_code=code,stop_reason=stop,wall_seconds=time.monotonic()-began);assert code==0 and not stop,(name,code,stop)
 try:
  for p in files:q=out/'sources'/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
  for p in (SRC/'verification').iterdir():shutil.copyfile(p,build/p.name)
  for p in math+[boundary]:shutil.copyfile(p,build/p.name)
  command(['verilator','--version'],'version.log',30)
  common=['verilator','--cc','--exe','--build','-j','1','--assert','-Wall','--public-flat-rw','--output-split','10000','--output-split-cfuncs','500','--language','1800-2017','-I'+mapped,'-CFLAGS','-std=c++17 -O1 -Wall -Wextra -Werror']
  command(common+['--top-module','locality_probe','--Mdir',mapped+'/inverse-obj',*[mapped+'/'+n for n in ('locality_original.sv','locality_candidate.sv','locality_probe.sv','cu66_dequant.sv','cu66_idct8x8.sv','tb_inverse.cpp')]],'inverse-compile.log',600)
  assert '%Warning-' not in (out/'inverse-compile.log').read_text()
  r['inverse_binary_sha256']=sha(build/'inverse-obj/Vlocality_probe')
  for seed in (109101,109102):
   command([mapped+'/inverse-obj/Vlocality_probe',str(seed),mapped+f'/inverse-{seed}.jsonl',mapped+'/boundary.tsv'],f'inverse-{seed}.log',180)
   v=json.loads((out/f'inverse-{seed}.log').read_text().splitlines()[-1]);assert v['status']=='TEST_PASS' and v['prepared_clocks']>9000 and v['word_count']==128 and v['late_same_edge_write_fail_cases']==2 and v['concurrent_math_cases']==51;r['inverse_runs'].append(v)
  command(common+['--top-module','control_probe','--Mdir',mapped+'/control-obj',*[mapped+'/'+n for n in ('control_original.sv','control_candidate.sv','control_probe.sv','cu66_reconstruct_tile.sv','tb_control.cpp')]],'reconstruction-compile.log',600)
  assert '%Warning-' not in (out/'reconstruction-compile.log').read_text()
  r['reconstruction_binary_sha256']=sha(build/'control-obj/Vcontrol_probe')
  command([mapped+'/control-obj/Vcontrol_probe',mapped+'/reconstruction.jsonl'],'reconstruction.log',180)
  v=json.loads((out/'reconstruction.log').read_text().splitlines()[-1]);assert v['status']=='TEST_PASS' and v['full_frames']==2 and v['directed_checks']==51 and v['half_cycle_public_comparisons']>1000000;r['reconstruction_runs'].append(v)
  assert r['source_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in files};r.update(status='PASS',actual_RTL_run=True,frozen_after_focused_PASS=True)
 except BaseException as e:r['error']=repr(e);raise
 finally:
  for p in build.iterdir():
   if p.is_file():
    if p.suffix=='.jsonl':
     with p.open('rb') as a,(out/(p.name+'.gz')).open('wb') as b:
      with gzip.GzipFile(filename='',fileobj=b,mode='wb',mtime=0) as z:shutil.copyfileobj(a,z)
    else:shutil.copyfile(p,out/p.name)
  r['wall_seconds']=time.monotonic()-started;r['artifact_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()};write(out/'results.json',r);write(AREA/'results.json',dict(r,selected_report=str((out/'results.json').relative_to(ROOT)),selected_report_sha256=sha(out/'results.json')));print('FAULT_FOCUSED',r['status'],out,flush=True)
if __name__=='__main__':main()
