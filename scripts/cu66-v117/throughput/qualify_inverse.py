#!/usr/bin/env python3
"""Source-bound V117 inverse focused proof; established Verilator backend."""
import argparse,datetime,hashlib,json,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/'fpga/experiments/cu66-v117-throughput'
AREA=ROOT/'experiments/python-gamebub-v117/throughput/inverse'
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
 for name in ('inverse-edit-recipe.json','inverse-bench-recipe.json'):
  q=load(SRC/name);s=(ROOT/q['original']).read_text();assert sha(ROOT/q['original'])==q['original_sha256']
  for e in q['edits']:assert s.count(e['before'])==1;s=s.replace(e['before'],e['after'],1)
  assert s==(ROOT/q['derived']).read_text() and sha(ROOT/q['derived'])==q['derived_sha256']
  for e in reversed(q['edits']):assert s.count(e['after'])==1;s=s.replace(e['after'],e['before'],1)
  assert s==(ROOT/q['original']).read_text();recipes.append(q)
 old=(ROOT/recipes[0]['original']).read_text();assert old[old.index('`ifndef SYNTHESIS'):old.rindex('endmodule')] in (ROOT/recipes[0]['derived']).read_text()
 assert recipes[1]['old_semantic_checks_removed']==0 and recipes[1]['original_E_plus_2_commit_ledger_retained']
 return recipes

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run',action='store_true');ap.add_argument('--root-grant');a=ap.parse_args();recipes=verify()
 if not a.run:print('V117_INVERSE_PREPARED_NOT_RUN');return
 assert a.root_grant,'Root heavy-slot grant required'
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/stamp;out.mkdir(parents=True);build=Path('/home/lori/gamebub-build/cu66-v69')/('v117-inverse-'+stamp);build.mkdir();mapped='/build/'+build.name
 paths=[SRC/'cu66_inverse_stream_v91j.sv',SRC/'tb_inverse.cpp',SRC/'inverse-edit-recipe.json',SRC/'inverse-bench-recipe.json',ROOT/'fpga/experiments/cu66-v115-inverse/cu66_dequant.sv',ROOT/'fpga/experiments/cu66-v115-inverse/cu66_idct8x8.sv',ROOT/'fpga/experiments/cu66-v69/inverse/cu66_quant_rom.svh',ROOT/'experiments/python-gamebub-v91j/vectors/boundary.tsv',Path(__file__).resolve(),*[ROOT/q['original']for q in recipes]]
 r=dict(schema='v117-true-II1-inverse-focused-v1',status='FAIL',backend='Verilator 5.020',actual_RTL_run=False,simulation_started=False,root_grant=a.root_grant,image_id=IMAGE,assertions_disabled_or_downgraded=False,original_oracle_checks_removed=0,original_E_plus_2_commit_ledger_retained=True,all_original_assertion_blocks_retained=True,source_sha256={rel(p):sha(p)for p in paths},commands=[],runs=[],memory_samples=[],contract='Two complete accepted tuple stages, registered validation, E+2 payload commit, independent accepted and committed bank/index/token frontiers. Actual consecutive II1 capture required; math and output semantic ordering unchanged.',scope='Standalone established Verilator behavioral proof, no native route/whole-parent/ESP32/hardware claim.')
 def command(argv,name,cap,rtl=False):
  before=memory();assert before['available_bytes']>=8*1024**3 and before['psi_full_avg10']<1 and before['combined_used_ratio']<.85,before
  container='gamebub-v117-inverse-'+stamp.lower()+'-'+str(len(r['commands']));cmd=['docker','run','--rm','--init','--name',container,'--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--network','none','--ulimit','core=0','--mount',f'type=bind,src={build},dst={mapped}','-w',mapped,IMAGE,'timeout','--kill-after=5s',str(cap)+'s',*argv]
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
  for p in [SRC/'cu66_inverse_stream_v91j.sv',SRC/'tb_inverse.cpp',*paths[4:8]]:shutil.copyfile(p,build/p.name)
  command(['verilator','--version'],'version.log',30)
  flags=['verilator','--cc','--exe','--build','-j','1','--assert','-Wall','--public-flat-rw','--output-split','10000','--output-split-cfuncs','500','--language','1800-2017','-I'+mapped,'-CFLAGS','-std=c++17 -O2 -Wall -Wextra -Werror','--top-module','cu66_inverse_stream_v91j','--Mdir',mapped+'/obj']
  command(flags+[mapped+'/'+n for n in ('cu66_dequant.sv','cu66_idct8x8.sv','cu66_inverse_stream_v91j.sv','tb_inverse.cpp')],'compile.log',600);assert '%Warning-'not in(out/'compile.log').read_text()
  r['binary_sha256']=sha(build/'obj/Vcu66_inverse_stream_v91j')
  for seed in (117301,117302):
   log=f'run-{seed}.log';command([mapped+'/obj/Vcu66_inverse_stream_v91j',mapped+'/boundary.tsv',str(seed)],log,240,rtl=True);rows=[json.loads(s)for s in(out/log).read_text().splitlines()];assert len(rows)==1 and rows[0]['status']=='TEST_PASS';q=rows[0];assert q['max_consecutive_accepts']>=64 and q['first_tile_acceptance_cycles']==64 and q['commit_latency_edges']==2;r['runs'].append(q)
  assert r['source_sha256']=={rel(p):sha(p)for p in paths};r['status']='PASS'
 except BaseException as e:r['error']=repr(e);raise
 finally:
  r['wall_seconds']=time.monotonic()-began;r['artifact_sha256']={str(p.relative_to(out)):sha(p)for p in out.rglob('*')if p.is_file()and p.name!='receipt.json'};write(out/'receipt.json',r);write(AREA/'results.json',dict(status=r['status'],actual_RTL_run=r['actual_RTL_run'],path=rel(out/'receipt.json'),sha256=sha(out/'receipt.json')));print('V117_INVERSE_FOCUSED',r['status'],out,flush=True)
if __name__=='__main__':main()
