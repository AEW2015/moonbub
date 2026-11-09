#!/usr/bin/env python3
"""Source-bound V118 owned residual pipeline and four-beat reconstruction proof; established Verilator backend."""
import argparse,datetime,gzip,hashlib,importlib.util,json,shutil,subprocess,sys,time
sys.dont_write_bytecode=True
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/'fpga/experiments/cu66-v118-reconstruct'
BASESRC=ROOT/'fpga/experiments/cu66-v117-reconstruct-wordbank'
BASELINE_SELECTOR=ROOT/'experiments/python-gamebub-v117/reconstruct-wordbank/results.json'
BASELINE_RECEIPT=ROOT/'experiments/python-gamebub-v117/reconstruct-wordbank/attempts/20261109T125304434518Z/receipt.json'
OLD_RUNNER=ROOT/'scripts/cu66-v117/reconstruct_wordbank/qualify.py'
AREA=ROOT/'experiments/python-gamebub-v118/reconstruct'
IMAGE='sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def write(p,x):Path(p).write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def rel(p):return str(Path(p).resolve().relative_to(ROOT))
def memory():
 m={s.split(':')[0]:int(s.split()[1])*1024 for s in Path('/proc/meminfo').read_text().splitlines()};f=next(s for s in Path('/proc/pressure/memory').read_text().splitlines() if s.startswith('full '))
 return dict(available_bytes=m['MemAvailable'],psi_full_avg10=float(f.split('avg10=')[1].split()[0]),combined_used_ratio=(m['MemTotal']-m['MemAvailable']+m['SwapTotal']-m['SwapFree'])/(m['MemTotal']+m['SwapTotal']))
def verify():
 spec=importlib.util.spec_from_file_location('v117_frozen_reconstruct_qualification',OLD_RUNNER)
 old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old);old.verify()
 selector=load(BASELINE_SELECTOR);baseline=load(BASELINE_RECEIPT)
 assert selector==dict(status='PASS',actual_RTL_run=True,path=rel(BASELINE_RECEIPT),sha256=sha(BASELINE_RECEIPT))
 assert baseline['status']=='PASS' and baseline['actual_RTL_run'] is True
 pins=[BASELINE_SELECTOR,BASELINE_RECEIPT,OLD_RUNNER]
 for name,h in baseline['source_sha256'].items():assert sha(ROOT/name)==h;pins.append(ROOT/name)
 for name,h in baseline['artifact_sha256'].items():assert sha(BASELINE_RECEIPT.parent/name)==h;pins.append(BASELINE_RECEIPT.parent/name)
 q=load(SRC/'edit-recipe.json');text=(ROOT/q['original']).read_text()
 assert sha(ROOT/q['original'])==q['original_sha256'] and sha(ROOT/q['derived'])==q['derived_sha256']
 for e in q['edits']:assert text.count(e['before'])==1;text=text.replace(e['before'],e['after'],1)
 text=text.replace('endmodule\n',q['appended_assertions']+'endmodule\n')
 assert text==(SRC/'cu66_reconstruct_stream_v91k.sv').read_text()
 production=(SRC/'cu66_reconstruct_stream_v91k.sv').read_text()
 adapter=(SRC/'reconstruct_probe.sv').read_text().replace('module reconstruct_probe (','module cu66_reconstruct_stream_v91k (',1)
 ports='    output logic [63:0] count_output_stalls,count_ref_wait,\n    input logic [1:0] probe_plane,\n    input logic [12:0] probe_tile,\n    output logic [10:0] probe_cell\n);\n    assign probe_cell=quant_cell(probe_plane,probe_tile);'
 assert adapter.count(ports)==1
 assert adapter.replace(ports,'    output logic [63:0] count_output_stalls,count_ref_wait\n);',1)==production
 # All original complete independent pixel/geometry/reference oracles remain.
 oldbench=(BASESRC/'tb_reconstruct.cpp').read_text();newbench=(SRC/'tb_reconstruct.cpp').read_text()
 assert oldbench[oldbench.index('static unsigned oracle('):oldbench.index('class Bench{')] in newbench
 for name in ('wrong_ref_','input_corruption_','bad_mode_','missing_reference','partial_eof','held_final_byte','fixture_reference_drain'):
  assert name in newbench
 return dict(baseline=baseline,pins=pins)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run',action='store_true');ap.add_argument('--root-grant');a=ap.parse_args();qualification=verify()
 if not a.run:print('V118_RECONSTRUCT_PREPARED_NOT_RUN');return
 assert a.root_grant,'Root heavy-slot grant required'
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/stamp;out.mkdir(parents=True);build=Path('/home/lori/gamebub-build/cu66-v69')/('v118-reconstruct-'+stamp);build.mkdir();mapped='/build/'+build.name
 paths=sorted(set(qualification['pins']+[SRC/'cu66_reconstruct_stream_v91k.sv',SRC/'reconstruct_probe.sv',SRC/'tb_reconstruct.cpp',SRC/'edit-recipe.json',ROOT/'fpga/experiments/cu66-v69/inverse/cu66_reconstruct_tile.sv',Path(__file__).resolve()]))
 r=dict(schema='v118-reconstruction-owned-residual-fourbeat-focused-v1',status='FAIL',backend='Verilator 5.020',actual_RTL_run=False,simulation_started=False,root_grant=a.root_grant,image_id=IMAGE,assertions_disabled_or_downgraded=False,original_oracle_checks_removed=0,old_geometry_domain_retained=32768,exact_cycle_schedule_preserved=False,residual_accept_to_commit_edges=2,canonical_copy_beats=4,canonical_copy_bits_per_beat=128,additional_tile_payload_buffers=0,immediate_kill_masks_retained=True,physical_reference_debt_survives_cancel_reset=True,timing_gain_claimed=False,baseline_receipt=dict(path=rel(BASELINE_RECEIPT),sha256=sha(BASELINE_RECEIPT)),baseline_terminal_comparisons=[],source_sha256={rel(p):sha(p)for p in paths},commands=[],runs=[],memory_samples=[],contract='Two-stage immutable tuple capture/validation followed by ordered commit at E+2; four128-bit physical canonical copy edges using held engine response. All independent whole-grid pixel, owner, geometry, fault, reset and physical reference-debt checks retained. Atomic-copy-only expectations replaced by stricter every-lane/unchanged-byte ledger plus cancellation on allfour beats. Cycle schedule explicitly changes; no old-cycle equality claim.',scope='Standalone established Verilator behavioral proof with independent whole-grid canonical oracle; no native route/whole-parent/ESP32/hardware claim.')

 def command(argv,name,cap,rtl=False):
  before=memory();assert before['available_bytes']>=8*1024**3 and before['psi_full_avg10']<1 and before['combined_used_ratio']<.85,before
  container='gamebub-v118-reconstruct-'+stamp.lower()+'-'+str(len(r['commands']));cmd=['docker','run','--rm','--init','--name',container,'--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--network','none','--ulimit','core=0','--mount',f'type=bind,src={build},dst={mapped}','-w',mapped,IMAGE,'timeout','--kill-after=5s',str(cap)+'s',*argv]
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
  for seed in (118311,118312):
   log=f'run-{seed}.log';command([mapped+'/obj/Vreconstruct_probe',str(seed),mapped+f'/trace-{seed}.jsonl'],log,240,rtl=True);rows=[json.loads(s)for s in(out/log).read_text().splitlines()];assert len(rows)==1 and rows[0]['status']=='TEST_PASS';q=rows[0];assert q['geometry_cases']==32768 and q['full_frames']==3 and q['max_tile_owners']==2 and q['fill_emit_overlap_edges']>0 and q['held_tuple_checks']>0 and q['directed_checks']>=56 and q['private_copy_cancel_cases']==8 and q['pipeline_fault_cases']==4 and q['physical_copy_bits']==128*q['physical_copy_edges'] and all(q['copy_lane'+str(i)+'_edges']>0 for i in range(4))
   r['baseline_terminal_comparisons'].append(dict(seed=seed,semantic_oracles_executed=True,exact_cycle_equality_required=False,clock_edges=q['clock_edges'],key_frame_cycles=q['key_frame_cycles'],inter_frame_cycles=q['inter_frame_cycles']))
   r['runs'].append(q)
  assert r['source_sha256']=={rel(p):sha(p)for p in paths};assert len(r['baseline_terminal_comparisons'])==2;r['status']='PASS'
 except BaseException as e:r['error']=repr(e);raise
 finally:
  for trace in build.glob('trace-*.jsonl'):
   (out/(trace.name+'.gz')).write_bytes(gzip.compress(trace.read_bytes(),mtime=0))
  r['wall_seconds']=time.monotonic()-began;r['artifact_sha256']={str(p.relative_to(out)):sha(p)for p in out.rglob('*')if p.is_file()and p.name!='receipt.json'};write(out/'receipt.json',r);write(AREA/'results.json',dict(status=r['status'],actual_RTL_run=r['actual_RTL_run'],path=rel(out/'receipt.json'),sha256=sha(out/'receipt.json')));print('V118_RECONSTRUCT_FOCUSED',r['status'],out,flush=True)
if __name__=='__main__':main()
