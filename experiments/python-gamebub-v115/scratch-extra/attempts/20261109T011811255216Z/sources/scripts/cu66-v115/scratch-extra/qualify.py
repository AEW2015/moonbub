#!/usr/bin/env python3
"""Additional actual scratch metadata geometry/replay/poison tests; no parent or throughput claim."""
import argparse,datetime,hashlib,json,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/'fpga/experiments/cu66-v115-scratch-extra';AREA=ROOT/'experiments/python-gamebub-v115/scratch-extra'
IMAGE='sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run',action='store_true');a=ap.parse_args()
 if a.run:
  import importlib.util
  spec=importlib.util.spec_from_file_location('v115_mem',ROOT/'scripts/cu66-v115/scratch/qualify.py');guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard);m=guard.memory();assert m['available_bytes']>=8*1024**3 and m['PSI_full_avg10']<1,m
 paths=[ROOT/'fpga/experiments/cu66-v115-scratch/packed_scratch_v91g2.sv',SRC/'metadata.cpp',Path(__file__).resolve()]
 if not a.run:print('V113_INVERSE_PREPARED_NOT_RUN');return
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/stamp;out.mkdir(parents=True)
 build=Path('/home/lori/gamebub-build/cu66-v69')/('v115-scratch-extra-'+stamp);build.mkdir();mapped='/build/'+build.name
 receipt=dict(schema='v115-extra-metadata-geometry-replay-v1',status='FAIL',backend='Verilator',assertions_disabled_or_downgraded=False,source_sha256={str(p.relative_to(ROOT)):sha(p) for p in paths},commands=[],runs=[])
 for p in paths:
  shutil.copyfile(p,build/p.name);snap=out/'sources'/p.relative_to(ROOT);snap.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,snap)
 def run(argv,name,cap):
  gate=guard.memory();assert gate['available_bytes']>=8*1024**3 and gate['PSI_full_avg10']<1,gate
  container='gamebub-v115-scratch-extra-'+stamp.lower()+'-'+name.split('.')[0]
  cmd=['docker','run','--rm','--init','--name',container,'--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--network','none','--ulimit','core=0','--mount',f'type=bind,src={build},dst={mapped}','-w',mapped,IMAGE,'timeout','--kill-after=5s',str(cap)+'s',*argv]
  receipt['commands'].append(cmd);t=time.monotonic()
  with (out/name).open('w')as f:
   child=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT);high=0
   while child.poll()is None:
    sample=guard.memory();high=high+1 if sample['PSI_full_avg10']>=5 else 0
    receipt.setdefault('memory_samples',[]).append(sample)
    if sample['available_bytes']<4*1024**3 or high>=2 or time.monotonic()-t>cap+20:
     receipt['resource_stop']=sample;subprocess.run(['docker','stop','--time','5',container],capture_output=True,timeout=15);break
    time.sleep(2)
   assert child.wait(timeout=20)==0 and 'resource_stop'not in receipt,name
  receipt.setdefault('wall_seconds',{})[name]=time.monotonic()-t
 try:
  run(['verilator','--version'],'version.log',30)
  run(['verilator','--cc','--exe','--build','-j','1','--assert','-Wall','--public-flat-rw','--output-split','10000','--output-split-cfuncs','500','--language','1800-2017','-CFLAGS','-std=c++17 -O1 -Wall -Wextra -Werror','--top-module','packed_scratch_v91g2','--Mdir',mapped+'/obj',*[mapped+'/'+n for n in ('packed_scratch_v91g2.sv','metadata.cpp')]],'compile.log',600)
  assert '%Warning-' not in (out/'compile.log').read_text()
  for seed in (115451,115452):
   run([mapped+'/obj/Vpacked_scratch_v91g2',str(seed)],f'run-{seed}.log',120)
   result=json.loads((out/f'run-{seed}.log').read_text().splitlines()[-1]);assert result['status']=='TEST_PASS';receipt['runs'].append(result)
  assert receipt['source_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in paths};receipt.update(status='PASS',actual_RTL_run=True,scope='Standalone actual production scratch metadata path; physical-memory requests forbidden. This augments, not replaces, full paired/golden/recovery qualification.')
 except BaseException as e:receipt['error']=repr(e);raise
 finally:
  receipt['artifact_sha256']={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()}
  (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');(AREA/'results.json').write_text(json.dumps(dict(path=str((out/'receipt.json').relative_to(ROOT)),sha256=sha(out/'receipt.json'),status=receipt['status']),indent=2)+'\n');print(receipt['status'],out,flush=True)
if __name__=='__main__':main()
