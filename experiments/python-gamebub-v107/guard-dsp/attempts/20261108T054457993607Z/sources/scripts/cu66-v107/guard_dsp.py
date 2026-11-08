#!/usr/bin/env python3
"""Strict extracted-expression proof; complete production recipes, not full-module proof."""
import argparse,datetime,gzip,hashlib,json,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SRC=ROOT/'fpga/experiments/cu66-v107-guard-dsp';AREA=ROOT/'experiments/python-gamebub-v107/guard-dsp'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def memory():
 m={x.split(':')[0]:int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines()};f=next(x for x in Path('/proc/pressure/memory').read_text().splitlines() if x.startswith('full '));return dict(available_bytes=m['MemAvailable'],psi_full_avg10=float(f.split('avg10=')[1].split()[0]))
def verify():
 recipe=json.loads((SRC/'edit-recipe.json').read_text());unit=(SRC/'guard_probe.sv').read_text()
 for entry in recipe['files']:
  old=ROOT/entry['original'];new=ROOT/entry['candidate'];assert sha(old)==entry['original_sha256'] and sha(new)==entry['candidate_sha256'];s=old.read_text()
  for e in entry['edits']:assert s.count(e['before'])==e['expected_occurrences']==1;s=s.replace(e['before'],e['after'],1)
  assert s==new.read_text();rev=s
  for e in reversed(entry['edits']):assert rev.count(e['after'])==1;rev=rev.replace(e['after'],e['before'],1)
  assert rev==old.read_text()
  for line in s.splitlines():
   if f'logic [31:0] {entry["signal"]};' in line or line.startswith(f'    assign {entry["signal"]}='):assert line+'\n' in unit
  assert f'assign {"scratch" if entry["signal"]=="begin_limit43" else "ingress"}_original={entry["exact_expression"]};' in unit
 return recipe

def model():
 import random
 rng=random.Random(107943);digest=hashlib.sha256();rows=0
 for x in range(1<<17):
  product=x*43;expanded=(x<<5)+(x<<3)+(x<<1)+x;assert product==expanded and product<1<<23
  for count in (0,(product-1)&0xffffffff,product,product+1,0x7fffffff,0x80000000,0xfffffffe,0xffffffff,rng.getrandbits(32)):
   assert (count>product)==(count>expanded);digest.update(x.to_bytes(3,'little')+count.to_bytes(4,'little')+bytes([count>product]));rows+=1
 return dict(status='PASS',all17bit_operands=131072,comparison_rows=rows,full32_counts=True,mathematical_product_max=(131071*43),digest_sha256=digest.hexdigest(),scope='Exact finite17-bit products and sampled full32 count comparisons; attribute-only alias arithmetic unchanged, not full-controller or timing proof.')
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--prepare-only',action='store_true');args=ap.parse_args();AREA.mkdir(parents=True,exist_ok=True);recipe=verify();m=model();write(AREA/'model.json',m)
 if args.prepare_only:print('PASS_SOURCE_RECIPES_AND_FINITE_MODEL_NO_RTL_RUN');return
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/stamp;out.mkdir(parents=True);build=Path('/home/lori/gamebub-build/cu66-v69')/('v107-guard-'+stamp);build.mkdir();mapped='/build/'+build.name
 files=[*sorted(p for p in SRC.iterdir() if p.is_file()),*[ROOT/e['original'] for e in recipe['files']],Path(__file__).resolve()]
 r=dict(schema='v107-local-control-dsp-expression-v1',status='FAIL',actual_RTL_run=False,source_sha256={str(p.relative_to(ROOT)):sha(p) for p in files},commands=[],model=m,scope='Actual extracted standalone combinational expressions only; two complete production source recipes preserved; no full-module/canonical/native mapping/timing claim.',production_files=[dict(path=e['candidate'],sha256=e['candidate_sha256']) for e in recipe['files']])
 def command(argv,name,cap):
  gate=memory();assert gate['available_bytes']>=8*1024**3 and gate['psi_full_avg10']<1,gate;r['commands'].append(e:=dict(argv=argv,timeout_seconds=cap,resource_before=gate));start=time.monotonic()
  with (out/name).open('w') as log:p=subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT,timeout=cap+15,cwd=ROOT)
  e.update(exit_code=p.returncode,wall_seconds=time.monotonic()-start);assert p.returncode==0,name
 try:
  for p in files:dest=out/'sources'/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
  cp=lambda name:str(out/'sources'/SRC.relative_to(ROOT)/name)
  command(['docker','exec','gamebub-cu66-v69-build','verilator','--version'],'version.log',30)
  command(['docker','exec','gamebub-cu66-v69-build','timeout','--kill-after=5s','120s','verilator','--cc','--exe','--build','-j','2','--assert','-Wall','--language','1800-2017','--top-module','guard_probe','--Mdir',mapped,'-CFLAGS','-std=c++17 -O2 -Wall -Wextra -Werror',cp('guard_probe.sv'),cp('tb_guard.cpp')],'compile.log',120);assert '%Warning-' not in (out/'compile.log').read_text();r['binary_sha256']=sha(build/'Vguard_probe')
  command(['docker','exec','gamebub-cu66-v69-build','timeout','--kill-after=5s','60s',mapped+'/Vguard_probe',str(out/'trace.csv')],'run.json',60);v=json.loads((out/'run.json').read_text());assert v['status']=='TEST_PASS' and v['rows']==1179648;r['verdict']=v
  with (out/'trace.csv').open('rb') as src,(out/'trace.csv.gz').open('wb') as dst:
   with gzip.GzipFile(filename='',fileobj=dst,mode='wb',mtime=0) as z:shutil.copyfileobj(src,z)
  (out/'trace.csv').unlink();assert r['source_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in files};r.update(status='PASS',actual_RTL_run=True)
 except BaseException as e:r.update(error=repr(e));raise
 finally:
  r['artifacts_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()};write(out/'results.json',r);write(AREA/'results.json',dict(r,selected_report=str((out/'results.json').relative_to(ROOT))));print('V107_GUARD_DSP',r['status'],flush=True)
if __name__=='__main__':main()
