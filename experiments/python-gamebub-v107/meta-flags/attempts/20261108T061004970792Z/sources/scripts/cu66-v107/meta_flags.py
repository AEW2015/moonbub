#!/usr/bin/env python3
"""Strict clocked132b stage + exact complete inverse paired proof, bounded and retained."""
import datetime,gzip,hashlib,json,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];FPGA=ROOT/'fpga/experiments/cu66-v107-meta-flags';AREA=ROOT/'experiments/python-gamebub-v107/meta-flags';HELP=ROOT/'scripts/cu66-v107/meta_flags'
sys.path.insert(0,str(ROOT/'scripts/cu66-v100'));from run_rtl import resources
CONTAINER='gamebub-cu66-v69-build'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def validate_recipe():
 r=json.loads((FPGA/'edit-recipe.json').read_text())
 for name,entry in r['production'].items():
  p=ROOT/entry['original'];assert sha(p)==entry['original_sha256'];s=p.read_text()
  for e in entry['edits']:assert s.count(e['before'])==e['expected_occurrences']==1;s=s.replace(e['before'],e['after'],1)
  assert s==(FPGA/name).read_text() and sha(FPGA/name)==entry['candidate_sha256']
 for suffix,source in [('original',ROOT/r['production']['cu66_inverse_stream_v91j.sv']['original']),('candidate',FPGA/'cu66_inverse_stream_v91j.sv')]:
  adapted=(FPGA/'verification'/('locality_'+suffix+'.sv')).read_text()
  assert adapted.replace('module locality_'+suffix+' (','module cu66_inverse_stream_v91j (',1)==source.read_text()
 historical=(ROOT/'fpga/experiments/cu66-v91j/tb_inverse.cpp').read_text().replace('Vcu66_inverse_stream_v91j','Vlocality_probe').replace('int main(int argc,char **argv)','int historical_inverse_main(int argc,char **argv)')
 historical=historical.replace('d.clk=1;d.eval();++cycle;','locality_pre(d);d.clk=1;d.eval();locality_post(d);++cycle;',1)
 assert historical==(FPGA/'verification/historical_inverse.cpp').read_text()
 return r

def main():
 started=time.monotonic();recipe=validate_recipe();stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/stamp;out.mkdir(parents=True);build=Path('/home/lori/gamebub-build/cu66-v69')/('v107-meta-flags-'+stamp);build.mkdir();mapped='/build/'+build.name
 math=[ROOT/'fpga/experiments/cu66-v69/inverse/cu66_dequant.sv',ROOT/'fpga/experiments/cu66-v106-idct-area/cu66_idct8x8.sv',ROOT/'fpga/experiments/cu66-v69/inverse/cu66_quant_rom.svh'];boundary=ROOT/'experiments/python-gamebub-v91j/vectors/boundary.tsv'
 files=sorted([p for p in FPGA.rglob('*') if p.is_file()]+[p for p in HELP.glob('*.py')]+[Path(__file__).resolve(),boundary,*math]+[ROOT/e['original'] for e in recipe['production'].values()]+[ROOT/'fpga/experiments/cu66-v106-locality/tb_locality.cpp',ROOT/'fpga/experiments/cu66-v107-elastic/tb_elastic.cpp',ROOT/'fpga/experiments/cu66-v91j/tb_inverse.cpp'])
 r=dict(schema='v107-token-static-flags-focused-v1',status='RUNNING',actual_RTL_run=False,source_sha256={str(p.relative_to(ROOT)):sha(p) for p in files},production={n:dict(path=str((FPGA/n).relative_to(ROOT)),sha256=sha(FPGA/n)) for n in recipe['production']},commands=[],stage_runs=[],inverse_runs=[],strict_warnings=True,warning_suppression=False,assertions_disabled_or_downgraded=False,added_public_cycles=0,independent_static_domains=dict(helper_plane_tile=32768,metadata_plane_tile_qcell=67108864,scale_value=262144),limits=['Actual132-bit stage token/flag conservation plus complete old/new inverse public/state/store comparison and independent malformed/store/math checks; no new full-pipeline execution claimed.','Explicitly prepared inverse owner/fault cases supplement reachable interface-driven historical tests; no arbitrary-internal-state/four-state proof.','Only unowned stage flag/payload data are unconstrained across flush; no public inverse/invalid/debug output comparison is masked.','No native mapping/route,hardware frequency or frame-rate qualification.'])
 write(out/'results.json',r);print('META_FLAGS_STARTED',out.relative_to(ROOT),flush=True)
 def command(args,name,timeout):
  gate=resources();argv=['docker','exec','-e','OMP_NUM_THREADS=1','-w',mapped,CONTAINER,'timeout','--kill-after=5s',str(timeout)+'s',*args];entry=dict(argv=argv,timeout_seconds=timeout,resource_gate=gate);r['commands'].append(entry);t=time.monotonic()
  with (build/name).open('w') as log:p=subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT,timeout=timeout+15)
  entry.update(exit_code=p.returncode,wall_seconds=time.monotonic()-t);assert p.returncode==0,(name,p.returncode)
 try:
  for p in files:q=out/'sources'/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
  for p in (FPGA/'verification').iterdir():
   if p.is_file():shutil.copyfile(p,build/p.name)
  shutil.copyfile(FPGA/'cu66_coefficient_elastic.sv',build/'cu66_coefficient_elastic.sv')
  for p in math:shutil.copyfile(p,build/p.name)
  shutil.copyfile(boundary,build/'boundary.tsv')
  command(['verilator','--version'],'tool.log',30)
  command(['verilator','--cc','--exe','--build','-j','2','--assert','-Wall','--top-module','meta_stage_probe','--Mdir',mapped+'/stage-obj','-CFLAGS','-std=c++17 -O2 -Wall -Wextra -Werror',mapped+'/meta_stage_probe.sv',mapped+'/cu66_coefficient_elastic.sv',mapped+'/tb_stage.cpp'],'stage-compile.log',300)
  assert '%Warning-' not in (build/'stage-compile.log').read_text()
  command(['sha256sum',mapped+'/stage-obj/Vmeta_stage_probe'],'stage-binary.log',30)
  for i,seed in enumerate((108001,108002)):
   command([mapped+'/stage-obj/Vmeta_stage_probe',str(seed),mapped+f'/stage-{seed}.jsonl','1' if i==0 else '0'],f'stage-{seed}.log',300)
   verdict=json.loads((build/f'stage-{seed}.log').read_text().splitlines()[-1]);assert verdict['status']=='TEST_PASS' and verdict['flag_checks']>100000
   if i==0:assert verdict['helper_cases']==32768 and verdict['metadata_cases']==67108864 and verdict['domain_cases']==262144
   r['stage_runs'].append(verdict)
  command(['verilator','--cc','--exe','--build','-j','2','--assert','-Wall','--public-flat-rw','--top-module','locality_probe','--Mdir',mapped+'/inverse-obj','-CFLAGS','-std=c++17 -O2 -Wall -Wextra -Werror',mapped+'/locality_original.sv',mapped+'/locality_candidate.sv',mapped+'/locality_probe.sv',mapped+'/cu66_dequant.sv',mapped+'/cu66_idct8x8.sv','-I'+mapped,mapped+'/tb_inverse.cpp'],'inverse-compile.log',300)
  assert '%Warning-' not in (build/'inverse-compile.log').read_text()
  command(['sha256sum',mapped+'/inverse-obj/Vlocality_probe'],'inverse-binary.log',30)
  for seed in (108001,108002):
   command([mapped+'/inverse-obj/Vlocality_probe',str(seed),mapped+f'/inverse-{seed}.jsonl',mapped+'/boundary.tsv'],f'inverse-{seed}.log',180)
   verdict=json.loads((build/f'inverse-{seed}.log').read_text().splitlines()[-1]);assert verdict['status']=='TEST_PASS' and verdict['prepared_clocks']>9000 and verdict['word_count']==128 and verdict['late_same_edge_write_fail_cases']==2 and verdict['concurrent_math_cases']==51;r['inverse_runs'].append(verdict)
  assert r['source_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in files};r.update(status='PASS',actual_RTL_run=True,frozen_after_focused_PASS=True)
 except BaseException as e:r.update(status='FAIL',error_class=type(e).__name__,error=str(e));raise
 finally:
  for p in build.iterdir():
   if not p.is_file():continue
   if p.suffix=='.jsonl':
    assert p.stat().st_size<512*1024**2,(p,p.stat().st_size)
    with p.open('rb') as src,(out/(p.name+'.gz')).open('wb') as dst:
     with gzip.GzipFile(filename='',mode='wb',fileobj=dst,mtime=0) as z:shutil.copyfileobj(src,z)
   else:shutil.copyfile(p,out/p.name)
  r.update(wall_seconds=time.monotonic()-started,artifacts_sha256={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='results.json'});write(out/'results.json',r)
  selected=dict(r,selected_report=str((out/'results.json').relative_to(ROOT)),selected_report_sha256=sha(out/'results.json'));write(AREA/'results.json',selected);print('META_FLAGS_FINISHED',r['status'],out.relative_to(ROOT),flush=True)
if __name__=='__main__':main()
