#!/usr/bin/env python3
"""Source-bound V117 two-owner reconstruction focused proof; established Verilator backend."""
import argparse,datetime,gzip,hashlib,importlib.util,json,shutil,subprocess,sys,time
sys.dont_write_bytecode=True
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/'fpga/experiments/cu66-v117-reconstruct-wordbank'
BASESRC=ROOT/'fpga/experiments/cu66-v117-throughput'
BASELINE_SELECTOR=ROOT/'experiments/python-gamebub-v117/throughput/reconstruct/results.json'
BASELINE_RECEIPT=ROOT/'experiments/python-gamebub-v117/throughput/reconstruct/attempts/20261109T111821839417Z/receipt.json'
BASELINE_RECEIPT_SHA256='ab82508fed471cec452db2edf7308933f01921d8dcf7d8f3fe01315d37c3d906'
OLD_RUNNER=ROOT/'scripts/cu66-v117/throughput/qualify_reconstruct.py'
AREA=ROOT/'experiments/python-gamebub-v117/reconstruct-wordbank'
IMAGE='sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def write(p,x):Path(p).write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def rel(p):return str(Path(p).resolve().relative_to(ROOT))
def memory():
 m={s.split(':')[0]:int(s.split()[1])*1024 for s in Path('/proc/meminfo').read_text().splitlines()};f=next(s for s in Path('/proc/pressure/memory').read_text().splitlines() if s.startswith('full '))
 return dict(available_bytes=m['MemAvailable'],psi_full_avg10=float(f.split('avg10=')[1].split()[0]),combined_used_ratio=(m['MemTotal']-m['MemAvailable']+m['SwapTotal']-m['SwapFree'])/(m['MemTotal']+m['SwapTotal']))
def verify():
 assert sha(OLD_RUNNER)=='885e31f83aa604bd5b32680eb42c1c7b4a55584af931b7bc610eb8f61b725113'
 spec=importlib.util.spec_from_file_location('v117_frozen_reconstruct_qualification',OLD_RUNNER)
 old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old);old.verify()
 selector=load(BASELINE_SELECTOR);baseline=load(BASELINE_RECEIPT)
 assert selector==dict(status='PASS',actual_RTL_run=True,path=rel(BASELINE_RECEIPT),sha256=BASELINE_RECEIPT_SHA256)
 assert sha(BASELINE_RECEIPT)==BASELINE_RECEIPT_SHA256 and baseline['status']=='PASS' and baseline['actual_RTL_run'] is True
 assert baseline['assertions_disabled_or_downgraded'] is False and baseline['original_oracle_checks_removed']==0
 assert baseline['source_sha256'][rel(BASESRC/'cu66_reconstruct_stream_v91k.sv')]=='5b12193073a8410ad0d05d251c061f7379cd9dba5a9677e5f8f20da4c581be06'
 assert all(c['exit_code']==0 and 'resource_stop' not in c for c in baseline['commands'])
 compiles=[c['argv'] for c in baseline['commands'] if 'verilator' in c['argv'] and '--cc' in c['argv']]
 assert len(compiles)==1 and '--assert' in compiles[0] and '-Wall' in compiles[0] and '-Wno-fatal' not in compiles[0]
 assert '-Werror' in compiles[0][compiles[0].index('-CFLAGS')+1] and compiles[0][compiles[0].index('-j')+1]=='1'
 pins=[BASELINE_SELECTOR,BASELINE_RECEIPT,OLD_RUNNER]
 for name,h in baseline['source_sha256'].items():assert sha(ROOT/name)==h; pins.append(ROOT/name)
 for name,h in baseline['artifact_sha256'].items():assert sha(BASELINE_RECEIPT.parent/name)==h;pins.append(BASELINE_RECEIPT.parent/name)
 assert [q['seed'] for q in baseline['runs']]==[117311,117312]
 for row in baseline['runs']:
  terminal=BASELINE_RECEIPT.parent/('run-'+str(row['seed'])+'.log')
  assert [json.loads(line) for line in terminal.read_text().splitlines()]==[row]
 q=load(SRC/'wordbank-edit-recipe.json');text=(ROOT/q['original']).read_text()
 assert sha(ROOT/q['original'])==q['original_sha256'] and sha(ROOT/q['derived'])==q['derived_sha256']
 assert q['original']==rel(BASESRC/'cu66_reconstruct_stream_v91k.sv') and q['derived']==rel(SRC/'cu66_reconstruct_stream_v91k.sv')
 for e in q['edits']:assert text.count(e['before'])==1;text=text.replace(e['before'],e['after'],1)
 assert text==(ROOT/q['derived']).read_text()
 for e in reversed(q['edits']):assert text.count(e['after'])==1;text=text.replace(e['after'],e['before'],1)
 assert text==(ROOT/q['original']).read_text()
 oldbody=(ROOT/q['original']).read_text();newbody=(ROOT/q['derived']).read_text()
 assert oldbody[oldbody.index('`ifndef SYNTHESIS'):oldbody.rindex('endmodule')] in newbody
 assert (SRC/'tb_reconstruct.cpp').read_bytes()==(BASESRC/'tb_reconstruct.cpp').read_bytes()
 q=load(SRC/'reconstruct-probe-recipe.json');production=(ROOT/q['production']['path']).read_text();adapter=(ROOT/q['adapter']['path']).read_text()
 assert sha(ROOT/q['production']['path'])==q['production']['sha256'] and sha(ROOT/q['adapter']['path'])==q['adapter']['sha256']
 assert q['production']['path']==rel(SRC/'cu66_reconstruct_stream_v91k.sv') and q['adapter']['path']==rel(SRC/'reconstruct_probe.sv')
 adapter=adapter.replace(q['adapter_module'],q['original_module'],1).replace(q['probe_assignment'],'',1)
 at=adapter.index(');');assert adapter[:at]==q['original_before_ports'].rstrip()+q['probe_ports'];adapter=q['original_before_ports']+adapter[at:]
 assert adapter==production
 oldbench=(ROOT/q['geometry_oracle_source']).read_text();newbench=(SRC/'tb_reconstruct.cpp').read_text()
 oracle=oldbench[oldbench.index('static unsigned oracle('):oldbench.index('int main(')]
 assert oracle.strip() in newbench and sha(ROOT/q['geometry_oracle_source'])==q['geometry_oracle_source_sha256']
 return dict(baseline=baseline,pins=pins)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run',action='store_true');ap.add_argument('--root-grant');a=ap.parse_args();qualification=verify()
 if not a.run:print('V117_RECONSTRUCT_WORDBANK_PREPARED_NOT_RUN');return
 assert a.root_grant,'Root heavy-slot grant required'
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/stamp;out.mkdir(parents=True);build=Path('/home/lori/gamebub-build/cu66-v69')/('v117-reconstruct-wordbank-'+stamp);build.mkdir();mapped='/build/'+build.name
 paths=sorted(set(qualification['pins']+[SRC/'cu66_reconstruct_stream_v91k.sv',SRC/'reconstruct_probe.sv',SRC/'tb_reconstruct.cpp',SRC/'wordbank-edit-recipe.json',SRC/'reconstruct-probe-recipe.json',ROOT/'fpga/experiments/cu66-v69/inverse/cu66_reconstruct_tile.sv',Path(__file__).resolve()]))
 r=dict(schema='v117-reconstruction-constant-wordbank-focused-v1',status='FAIL',backend='Verilator 5.020',actual_RTL_run=False,simulation_started=False,root_grant=a.root_grant,image_id=IMAGE,assertions_disabled_or_downgraded=False,original_oracle_checks_removed=0,all_original_assertion_blocks_retained=True,physical_copy_has_only_registered_local_CE=True,logical_copy_immediate_kill_mask_retained=True,old_geometry_domain_retained=32768,all_old_public_private_bench_checks_unchanged=True,exact_cycle_schedule_preserved=True,physical_bank_CE_prediction_exact_preedge=True,timing_gain_claimed=False,baseline_receipt=dict(path=rel(BASELINE_RECEIPT),sha256=BASELINE_RECEIPT_SHA256),baseline_terminal_comparisons=[],source_sha256={rel(p):sha(p)for p in paths},commands=[],runs=[],memory_samples=[],contract='Elaboration-constant64word residual insertion plus exact-edge predicted physical bank CE strobes. Same source schedule and private values as qualified R5b; every old independent semantic/math/owner/error/reset/reference-debt check retained, all terminal fields and cycles compared exactly after actual new RTL execution.',scope='Standalone established Verilator behavioral proof with independent whole-grid canonical oracle; no native route/whole-parent/ESP32/hardware claim.')
 def command(argv,name,cap,rtl=False):
  before=memory();assert before['available_bytes']>=8*1024**3 and before['psi_full_avg10']<1 and before['combined_used_ratio']<.85,before
  container='gamebub-v117-reconstruct-wordbank-'+stamp.lower()+'-'+str(len(r['commands']));cmd=['docker','run','--rm','--init','--name',container,'--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--network','none','--ulimit','core=0','--mount',f'type=bind,src={build},dst={mapped}','-w',mapped,IMAGE,'timeout','--kill-after=5s',str(cap)+'s',*argv]
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
   log=f'run-{seed}.log';command([mapped+'/obj/Vreconstruct_probe',str(seed),mapped+f'/trace-{seed}.jsonl'],log,240,rtl=True);rows=[json.loads(s)for s in(out/log).read_text().splitlines()];assert len(rows)==1 and rows[0]['status']=='TEST_PASS';q=rows[0];assert q['geometry_cases']==32768 and q['full_frames']==3 and q['max_tile_owners']==2 and q['fill_emit_overlap_edges']>0 and q['held_tuple_checks']>0 and q['directed_checks']>=46 and q['private_copy_cancel_cases']==2
   baseline_row=next(row for row in qualification['baseline']['runs'] if row['seed']==seed)
   assert q==baseline_row,dict(seed=seed,actual=q,baseline=baseline_row)
   r['baseline_terminal_comparisons'].append(dict(seed=seed,all_terminal_fields_exact=True,exact_clock_edges=q['clock_edges'],exact_key_frame_cycles=q['key_frame_cycles'],exact_inter_frame_cycles=q['inter_frame_cycles']))
   r['runs'].append(q)
  assert r['source_sha256']=={rel(p):sha(p)for p in paths};assert len(r['baseline_terminal_comparisons'])==2;r['status']='PASS'
 except BaseException as e:r['error']=repr(e);raise
 finally:
  for trace in build.glob('trace-*.jsonl'):
   (out/(trace.name+'.gz')).write_bytes(gzip.compress(trace.read_bytes(),mtime=0))
  r['wall_seconds']=time.monotonic()-began;r['artifact_sha256']={str(p.relative_to(out)):sha(p)for p in out.rglob('*')if p.is_file()and p.name!='receipt.json'};write(out/'receipt.json',r);write(AREA/'results.json',dict(status=r['status'],actual_RTL_run=r['actual_RTL_run'],path=rel(out/'receipt.json'),sha256=sha(out/'receipt.json')));print('V117_RECONSTRUCT_WORDBANK_FOCUSED',r['status'],out,flush=True)
if __name__=='__main__':main()
