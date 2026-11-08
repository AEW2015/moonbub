#!/usr/bin/env python3
"""Strict public-cycle dequant payload-reset comparison and integer oracle."""
import datetime,gzip,hashlib,json,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SRC=ROOT/'fpga/experiments/cu66-v107-payload-reset';AREA=ROOT/'experiments/python-gamebub-v107/payload-reset';CONTAINER='gamebub-cu66-v69-build'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def memory():
 m={x.split(':')[0]:int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines()};f=next(x for x in Path('/proc/pressure/memory').read_text().splitlines() if x.startswith('full '));return dict(available_bytes=m['MemAvailable'],psi_full_avg10=float(f.split('avg10=')[1].split()[0]))
def main():
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/stamp;out.mkdir(parents=True);build=Path('/home/lori/gamebub-build/cu66-v69')/('v107-dequant-reset-'+stamp);build.mkdir();mapped='/build/'+build.name
 files=[*sorted(x for x in SRC.glob('*') if x.is_file()),ROOT/'fpga/experiments/cu66-v69/inverse/cu66_dequant.sv',ROOT/'fpga/experiments/cu66-v69/inverse/cu66_quant_rom.svh',ROOT/'experiments/cu66-native-v69/generated_constants.hpp',Path(__file__).resolve()]
 r=dict(schema='v107-dequant-private-payload-reset-v1',status='FAIL',actual_RTL_run=False,source_sha256={str(p.relative_to(ROOT)):sha(p) for p in files},commands=[],runs=[],full_public_outputs_compared_including_invalid=True,private_payload_allowed_differ_only_before_owned_use=True,scope='Behavioral two-state full public-cycle equality and independent integer/partial-output oracle; no full pipeline or timing claim.')
 def command(argv,name,timeout):
  gate=memory();assert gate['available_bytes']>=8*1024**3 and gate['psi_full_avg10']<1,gate
  e=dict(argv=argv,resource_before=gate,timeout_seconds=timeout);r['commands'].append(e);start=time.monotonic()
  with (out/name).open('w') as log:result=subprocess.run(argv,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=timeout+15)
  e.update(exit_code=result.returncode,wall_seconds=time.monotonic()-start);assert result.returncode==0,name
 try:
  recipe=json.loads((SRC/'edit-recipe.json').read_text());a=(ROOT/recipe['baseline']).read_text();s=a
  for e in reversed(recipe['changes']):assert s[e['start']:e['end']]==e['old'];s=s[:e['start']]+e['new']+s[e['end']:]
  assert s==(SRC/'cu66_dequant.sv').read_text()
  for v,body in [('original',a),('candidate',s)]:assert (SRC/f'dequant_{v}.sv').read_text().replace('module dequant_'+v+' (','module cu66_dequant (',1)==body
  for p in files:dst=out/'sources'/p.relative_to(ROOT);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dst)
  cp=lambda p:str(out/'sources'/p.relative_to(ROOT))
  command(['docker','exec',CONTAINER,'verilator','--version'],'version.log',30)
  command(['docker','exec',CONTAINER,'timeout','--kill-after=5s','180s','verilator','--cc','--exe','--build','-j','2','--assert','-Wall','--language','1800-2017','--top-module','dequant_probe','--Mdir',mapped,'-I'+cp(ROOT/'fpga/experiments/cu66-v69/inverse'),'-CFLAGS','-std=c++17 -O2 -Wall -Wextra -Werror -I'+cp(ROOT/'experiments/cu66-native-v69'),*[cp(SRC/name) for name in ('dequant_original.sv','dequant_candidate.sv','dequant_probe.sv','tb_dequant.cpp')]],'compile.log',180)
  assert '%Warning-' not in (out/'compile.log').read_text();r['binary_sha256']=sha(build/'Vdequant_probe')
  for seed in (107901,107902,107903):
   trace=out/f'{seed}.csv';log=f'{seed}.jsonl';command(['docker','exec',CONTAINER,'timeout','--kill-after=5s','60s',mapped+'/Vdequant_probe',str(seed),str(trace)],log,60)
   verdict=json.loads((out/log).read_text());assert verdict['status']=='TEST_PASS' and verdict['accepted']==verdict['retired']+verdict['discarded'];r['runs'].append(verdict)
   with trace.open('rb') as src,(out/f'{seed}.csv.gz').open('wb') as dst:
    with gzip.GzipFile(filename='',mode='wb',fileobj=dst,mtime=0) as z:shutil.copyfileobj(src,z)
   trace.unlink()
  assert r['source_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in files}
  r['status']='PASS';r['actual_RTL_run']=True;r['candidate']=dict(path=str((SRC/'cu66_dequant.sv').relative_to(ROOT)),sha256=sha(SRC/'cu66_dequant.sv'))
 except BaseException as e:r.update(error_class=type(e).__name__,error=str(e));raise
 finally:
  r['artifacts_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()};write(out/'results.json',r);write(AREA/'results.json',dict(r,selected_report=str((out/'results.json').relative_to(ROOT))));print('V107_DEQUANT_RESET',r['status'],out.relative_to(ROOT),flush=True)
if __name__=='__main__':main()
