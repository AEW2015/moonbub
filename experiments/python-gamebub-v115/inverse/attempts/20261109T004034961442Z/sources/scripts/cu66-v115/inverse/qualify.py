#!/usr/bin/env python3
"""Standalone established Verilator IV115.1 helper/inverse verification, not Vivado integration."""
import argparse,datetime,hashlib,json,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];SRC=ROOT/'fpga/experiments/cu66-v115-inverse';AREA=ROOT/'experiments/python-gamebub-v115/inverse'
IMAGE='sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def write(p,x):Path(p).write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def rel(p):return str(Path(p).resolve().relative_to(ROOT))
def memory():
 m={s.split(':')[0]:int(s.split()[1])*1024 for s in Path('/proc/meminfo').read_text().splitlines()};f=next(s for s in Path('/proc/pressure/memory').read_text().splitlines()if s.startswith('full '));return dict(available_bytes=m['MemAvailable'],psi_full_avg10=float(f.split('avg10=')[1].split()[0]))
def verify():
 q=load(SRC/'edit-recipe.json')
 for e in q['recipes']:
  s=(ROOT/e['original']).read_text();assert sha(ROOT/e['original'])==e['original_sha256']
  for x in e['edits']:assert s.count(x['before'])==1;s=s.replace(x['before'],x['after'],1)
  assert s==(ROOT/e['derived']).read_text()and sha(ROOT/e['derived'])==e['derived_sha256']
  for x in reversed(e['edits']):assert s.count(x['after'])==1;s=s.replace(x['after'],x['before'],1)
  assert s==(ROOT/e['original']).read_text()
 return q

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run',action='store_true');a=ap.parse_args();recipe=verify()
 if not a.run:print('V115_INVERSE_PREPARED_NOT_RUN');return
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/stamp;out.mkdir(parents=True);build=Path('/home/lori/gamebub-build/cu66-v69')/('v115-inverse-'+stamp);build.mkdir();mapped='/build/'+build.name
 paths=[SRC/'cu66_idct8x8.sv',SRC/'cu66_dequant.sv',SRC/'edit-recipe.json',SRC/'helpers_probe.sv',SRC/'tb_helpers.cpp',ROOT/'fpga/experiments/cu66-v113-inverse/cu66_inverse_stream_v91j.sv',ROOT/'fpga/experiments/cu66-v113-inverse/tb_inverse.cpp',ROOT/'fpga/experiments/cu66-v69/inverse/cu66_quant_rom.svh',ROOT/'experiments/python-gamebub-v91j/vectors/boundary.tsv',ROOT/'scripts/cu66-v115/inverse/prepare.py',Path(__file__).resolve(),*[ROOT/e['original']for e in recipe['recipes']]]
 r=dict(schema='v115-IV115.1-helper-inverse-proof-v1',status='FAIL',backend='Verilator',actual_RTL_run=False,assertions_disabled_or_downgraded=False,source_sha256={rel(p):sha(p)for p in paths},commands=[],runs=[],helper_runs=[],memory_samples=[],contract=recipe['contract'],new_private_states={'dequant_PREPARE':3,'IDCT_PREPARE':10},scope='Standalone inferred RTL behavioral proof. No Vivado-integrated simulator backend claim, native route, whole-parent, ESP32 or hardware execution.')
 def command(argv,name,cap):
  before=memory();assert before['available_bytes']>=8*1024**3 and before['psi_full_avg10']<1,before;container='gamebub-v115-inverse-'+stamp.lower()+'-'+str(len(r['commands']));cmd=['docker','run','--rm','--init','--name',container,'--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--network','none','--ulimit','core=0','--mount',f'type=bind,src={build},dst={mapped}','-w',mapped,IMAGE,'timeout','--kill-after=5s',str(cap)+'s',*argv];row=dict(argv=cmd,resource_before=before);r['commands'].append(row);started=time.monotonic();hi=0
  with(out/name).open('w')as log:
   child=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
   while child.poll()is None:
    sample=dict(elapsed_seconds=time.monotonic()-started,command=name,**memory());r['memory_samples'].append(sample);hi=hi+1 if sample['psi_full_avg10']>=5 else 0
    if sample['available_bytes']<4*1024**3 or hi>=2 or sample['elapsed_seconds']>cap+20:subprocess.run(['docker','stop','--time','5',container],capture_output=True,timeout=15);row['resource_stop']=sample;break
    time.sleep(2)
   row.update(exit_code=child.wait(timeout=20),wall_seconds=time.monotonic()-started)
  assert row['exit_code']==0 and 'resource_stop'not in row,name
 try:
  for p in paths:
   snap=out/'sources'/p.relative_to(ROOT);snap.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,snap)
  for p in paths[:2]+[SRC/'helpers_probe.sv',SRC/'tb_helpers.cpp',ROOT/'fpga/experiments/cu66-v113-inverse/cu66_inverse_stream_v91j.sv',ROOT/'fpga/experiments/cu66-v113-inverse/tb_inverse.cpp',ROOT/'fpga/experiments/cu66-v69/inverse/cu66_quant_rom.svh',ROOT/'experiments/python-gamebub-v91j/vectors/boundary.tsv']:shutil.copyfile(p,build/p.name)
  command(['verilator','--version'],'version.log',30)
  flags=['verilator','--cc','--exe','--build','-j','1','--assert','-Wall','--public-flat-rw','--output-split','10000','--output-split-cfuncs','500','--language','1800-2017','-I'+mapped,'-CFLAGS','-std=c++17 -O1 -Wall -Wextra -Werror']
  for top,bench,extra,collection in [('cu66_inverse_stream_v91j','tb_inverse.cpp',['cu66_inverse_stream_v91j.sv'],'runs'),('helpers_probe','tb_helpers.cpp',['helpers_probe.sv'],'helper_runs')]:
   log='compile-'+top+'.log';command(flags+['--top-module',top,'--Mdir',mapped+'/obj-'+top,*[mapped+'/'+n for n in ['cu66_dequant.sv','cu66_idct8x8.sv',*extra,bench]]],log,600);assert '%Warning-'not in(out/log).read_text()
   r.setdefault('binary_sha256',{})[top]=sha(build/('obj-'+top)/('V'+top))
   for seed in [115101,115102]:
    name=f'{top}-{seed}.log';command([mapped+'/obj-'+top+'/V'+top,mapped+'/boundary.tsv',str(seed)],name,180);rows=[json.loads(s)for s in(out/name).read_text().splitlines()];assert len(rows)==1 and rows[0]['status']=='TEST_PASS';v=rows[0]
    if top=='helpers_probe':assert v['exhaustive_signed20_domain_checks']==1048576 and v['cancel_phase_checks']==v['clean_retries']==30 and v['new_preparation_states_executed']
    r[collection].append(v)
  assert r['source_sha256']=={rel(p):sha(p)for p in paths};r.update(status='PASS',actual_RTL_run=True)
 except BaseException as e:r['error']=repr(e);raise
 finally:
  r['artifact_sha256']={str(p.relative_to(out)):sha(p)for p in out.rglob('*')if p.is_file()};write(out/'receipt.json',r);write(AREA/'results.json',dict(status=r['status'],path=rel(out/'receipt.json'),sha256=sha(out/'receipt.json')));print('V115_INVERSE_FOCUSED',r['status'],out,flush=True)
if __name__=='__main__':main()
