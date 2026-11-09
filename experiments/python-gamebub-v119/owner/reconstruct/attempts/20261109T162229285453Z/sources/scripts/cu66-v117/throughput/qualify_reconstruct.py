#!/usr/bin/env python3
"""Source-bound V117 two-owner reconstruction focused proof; established Verilator backend."""
import argparse,datetime,gzip,hashlib,json,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/'fpga/experiments/cu66-v117-throughput'
AREA=ROOT/'experiments/python-gamebub-v117/throughput/reconstruct'
IMAGE='sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def write(p,x):Path(p).write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def rel(p):return str(Path(p).resolve().relative_to(ROOT))
def memory():
 m={s.split(':')[0]:int(s.split()[1])*1024 for s in Path('/proc/meminfo').read_text().splitlines()};f=next(s for s in Path('/proc/pressure/memory').read_text().splitlines() if s.startswith('full '))
 return dict(available_bytes=m['MemAvailable'],psi_full_avg10=float(f.split('avg10=')[1].split()[0]),combined_used_ratio=(m['MemTotal']-m['MemAvailable']+m['SwapTotal']-m['SwapFree'])/(m['MemTotal']+m['SwapTotal']))
def verify():
 recipes=[]
 for name in ('reconstruct-edit-recipe.json','reconstruct-storage-copy-recipe.json','reconstruct-storage-bench-recipe.json'):
  q=load(SRC/name);s=(ROOT/q['original']).read_text();assert sha(ROOT/q['original'])==q['original_sha256']
  for e in q['edits']:assert s.count(e['before'])==1;s=s.replace(e['before'],e['after'],1)
  assert s==(ROOT/q['derived']).read_text() and sha(ROOT/q['derived'])==q['derived_sha256']
  for e in reversed(q['edits']):assert s.count(e['after'])==1;s=s.replace(e['after'],e['before'],1)
  assert s==(ROOT/q['original']).read_text();recipes.append(q)
 old=(ROOT/recipes[0]['original']).read_text();assert old[old.index('`ifndef SYNTHESIS'):old.rindex('endmodule')] in (ROOT/recipes[0]['derived']).read_text()
 q=load(SRC/'reconstruct-probe-recipe.json');production=(ROOT/q['production']['path']).read_text();adapter=(ROOT/q['adapter']['path']).read_text()
 assert sha(ROOT/q['production']['path'])==q['production']['sha256'] and sha(ROOT/q['adapter']['path'])==q['adapter']['sha256']
 adapter=adapter.replace(q['adapter_module'],q['original_module'],1).replace(q['probe_assignment'],'',1)
 at=adapter.index(');');assert adapter[:at]==q['original_before_ports'].rstrip()+q['probe_ports'];adapter=q['original_before_ports']+adapter[at:]
 assert adapter==production
 oldbench=(ROOT/q['geometry_oracle_source']).read_text();newbench=(SRC/'tb_reconstruct.cpp').read_text()
 oracle=oldbench[oldbench.index('static unsigned oracle('):oldbench.index('int main(')]
 assert oracle.strip() in newbench and sha(ROOT/q['geometry_oracle_source'])==q['geometry_oracle_source_sha256']
 return recipes

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run',action='store_true');ap.add_argument('--root-grant');a=ap.parse_args();recipes=verify()
 if not a.run:print('V117_RECONSTRUCT_PREPARED_NOT_RUN');return
 assert a.root_grant,'Root heavy-slot grant required'
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/stamp;out.mkdir(parents=True);build=Path('/home/lori/gamebub-build/cu66-v69')/('v117-reconstruct-'+stamp);build.mkdir();mapped='/build/'+build.name
 paths=[SRC/'cu66_reconstruct_stream_v91k.sv',SRC/'reconstruct_probe.sv',SRC/'tb_reconstruct.cpp',SRC/'reconstruct-edit-recipe.json',SRC/'reconstruct-probe-recipe.json',ROOT/'fpga/experiments/cu66-v69/inverse/cu66_reconstruct_tile.sv',ROOT/'fpga/experiments/cu66-v110-fault/cu66_reconstruct_stream_v91k.sv',ROOT/'fpga/experiments/cu66-v103-reconstruct/tb_reconstruct.cpp',Path(__file__).resolve(),SRC/'reconstruct-storage-copy-recipe.json',SRC/'reconstruct-storage-bench-recipe.json',SRC/'initial/cu66_reconstruct_stream_v91k.sv',SRC/'initial/tb_reconstruct.cpp',ROOT/'scripts/cu66-v117/throughput/prepare_storage_copy.py']
 r=dict(schema='v117-two-owner-reconstruction-focused-v1',status='FAIL',backend='Verilator 5.020',actual_RTL_run=False,simulation_started=False,root_grant=a.root_grant,image_id=IMAGE,assertions_disabled_or_downgraded=False,original_oracle_checks_removed=0,all_original_assertion_blocks_retained=True,physical_copy_has_only_registered_local_CE=True,logical_copy_immediate_kill_mask_retained=True,old_geometry_domain_retained=32768,source_sha256={rel(p):sha(p)for p in paths},commands=[],runs=[],memory_samples=[],contract='Exactly two tile owners, independent gather/emission, one real registered whole512bit conversion copy edge. Original semantic clamp/geometry/owner/ref-debt/EOF/cancel/error checks retained and independently exercised; scheduling changes explicitly.',scope='Standalone established Verilator behavioral proof with independent whole-grid canonical oracle; no native route/whole-parent/ESP32/hardware claim.')
 def command(argv,name,cap,rtl=False):
  before=memory();assert before['available_bytes']>=8*1024**3 and before['psi_full_avg10']<1 and before['combined_used_ratio']<.85,before
  container='gamebub-v117-reconstruct-'+stamp.lower()+'-'+str(len(r['commands']));cmd=['docker','run','--rm','--init','--name',container,'--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--network','none','--ulimit','core=0','--mount',f'type=bind,src={build},dst={mapped}','-w',mapped,IMAGE,'timeout','--kill-after=5s',str(cap)+'s',*argv]
  row=dict(argv=cmd,resource_before=before,timeout_seconds=cap);r['commands'].append(row)
  if rtl:r.update(actual_RTL_run=True,simulation_started=True)
  write(out/'receipt.json',r);began=time.monotonic();high=0
  with(out/name).open('w')as log:
   p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
   while p.poll()is None:
    sample=dict(elapsed_seconds=time.monotonic()-began,command=name,**memory());r['memory_samples'].append(sample);high=high+1 if sample['psi_full_avg10']>=5 else 0
    if sample['available_bytes']<4*1024**3 or high>=2 or sample['combined_used_ratio']>=.9 or sample['elapsed_seconds']>cap+20:subprocess.run(['docker','stop','--time','5',container],capture_output=True,timeout=15);row['resource_stop']=sample;break
    time.sleep(2)
   row.update(exit_code=p.wait(timeout=20),wall_seconds=time.monotonic()-began)
  assert row['exit_code']==0 and 'resource_stop'not in row,name
 began=time.monotonic()
 try:
  for p in paths:
   q=out/'sources'/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
  for p in [SRC/'reconstruct_probe.sv',SRC/'tb_reconstruct.cpp',ROOT/'fpga/experiments/cu66-v69/inverse/cu66_reconstruct_tile.sv']:shutil.copyfile(p,build/p.name)
  command(['verilator','--version'],'version.log',30)
  flags=['verilator','--cc','--exe','--build','-j','1','--assert','-Wall','--public-flat-rw','--output-split','10000','--output-split-cfuncs','500','--language','1800-2017','-I'+mapped,'-CFLAGS','-std=c++17 -O2 -Wall -Wextra -Werror','--top-module','reconstruct_probe','--Mdir',mapped+'/obj']
  command(flags+[mapped+'/'+n for n in ('cu66_reconstruct_tile.sv','reconstruct_probe.sv','tb_reconstruct.cpp')],'compile.log',600);assert '%Warning-'not in(out/'compile.log').read_text()
  r['binary_sha256']=sha(build/'obj/Vreconstruct_probe')
  for seed in (117311,117312):
   log=f'run-{seed}.log';command([mapped+'/obj/Vreconstruct_probe',str(seed),mapped+f'/trace-{seed}.jsonl'],log,240,rtl=True);rows=[json.loads(s)for s in(out/log).read_text().splitlines()];assert len(rows)==1 and rows[0]['status']=='TEST_PASS';q=rows[0];assert q['geometry_cases']==32768 and q['full_frames']==3 and q['max_tile_owners']==2 and q['fill_emit_overlap_edges']>0 and q['held_tuple_checks']>0 and q['directed_checks']>=46 and q['private_copy_cancel_cases']==2;r['runs'].append(q)
  assert r['source_sha256']=={rel(p):sha(p)for p in paths};r['status']='PASS'
 except BaseException as e:r['error']=repr(e);raise
 finally:
  for trace in build.glob('trace-*.jsonl'):
   (out/(trace.name+'.gz')).write_bytes(gzip.compress(trace.read_bytes(),mtime=0))
  r['wall_seconds']=time.monotonic()-began;r['artifact_sha256']={str(p.relative_to(out)):sha(p)for p in out.rglob('*')if p.is_file()and p.name!='receipt.json'};write(out/'receipt.json',r);write(AREA/'results.json',dict(status=r['status'],actual_RTL_run=r['actual_RTL_run'],path=rel(out/'receipt.json'),sha256=sha(out/'receipt.json')));print('V117_RECONSTRUCT_FOCUSED',r['status'],out,flush=True)
if __name__=='__main__':main()
