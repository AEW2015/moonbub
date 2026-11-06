#!/usr/bin/env python3
"""Fixed-admission two-source replay after complete active warm scanout."""
import argparse,hashlib,json,os,re,subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'fpga/experiments/cu66-v76/phases'
NATIVE=ROOT/'experiments/cu66-native-v69'
SPEC=ROOT/'fpga/experiments/cu66-v75/system/sources.json'
OFFSETS=(0,384171,768342,1152513)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fields(line):return {k:int(v)for k,v in re.findall(r'(\w+)=(\d+)',line)}
def main():
 p=argparse.ArgumentParser();p.add_argument('--first-only',action='store_true');p.add_argument('--workers',type=int,choices=(1,2),default=2);a=p.parse_args()
 spec=json.loads(SPEC.read_text());paths=[ROOT/x for x in spec['rtl_sources']]+[AREA/'tb_phases.cpp',SPEC,Path(__file__).resolve(),NATIVE/'index.tsv',ROOT/'fpga/experiments/cu66-v69/hud-partition/hud_gate.hpp',ROOT/'fpga/experiments/cu66-v69/packet/cu66_profile.svh',ROOT/'fpga/experiments/cu66-v69/inverse/cu66_quant_rom.svh',ROOT/'fpga/experiments/cu66-v70/memory/cu70_memory_map.svh',ROOT/'fpga/experiments/cu66-v70/memory/memory_map.hpp',*NATIVE.glob('*.hpp')]
 for line in (NATIVE/'index.tsv').read_text().splitlines()[:2]:paths.append(NATIVE/line.split('\t')[2])
 def pins():return {str(p.relative_to(ROOT)):sha(p)for p in sorted(set(paths))}
 before=pins();commands=[];container=os.environ.get('TASK_CONTAINER','gamebub-cu66-v69-build');AREA.mkdir(exist_ok=True)
 def run(argv,name,timeout):
  path=AREA/name
  with path.open('w')as f:r=subprocess.run(argv,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
  commands.append(dict(argv=argv,log=str(path.relative_to(ROOT)),exit_code=r.returncode,sha256=sha(path)))
  if r.returncode:raise RuntimeError(f'{name}: exit{r.returncode}; inspect retained log')
  return path.read_text()
 mdir='/build/v76-phases'
 run(['docker','exec',container,'verilator','--cc','--exe','--build','-j','1',*spec['verilator_options'],'-DSIMULATION','--top-module','cu75_system_sim','-GUSE_STRIP=1','-GP0_CACHE_LINES=8','--Mdir',mdir,'-CFLAGS','-O2 -std=c++17',*['-I'+str(ROOT/x)for x in spec['include_dirs']],*[str(ROOT/x)for x in spec['rtl_sources']],str(AREA/'tb_phases.cpp')],'build.log',1200)
 records=[]
 jobs=[('burst',0)] if a.first_only else [(mode,off)for mode in ('scalar','burst')for off in OFFSETS]
 def one_job(job):
  mode,off=job
  log=run(['docker','exec',container,mdir+'/Vcu75_system_sim',str(NATIVE/'index.tsv'),mode,str(off)],f'run-{mode}-{off}.log',7200)
  marker=re.search(r'^SYSTEM_PASS (.+)$',log,re.M);assert marker and 'FAIL'not in log
  summary=fields(marker[1]);assert summary['complete_frames']==summary['distinct_complete_presentations']==2 and summary['total_underruns']==summary['black_lines']==0
  rows=[fields(l)for l in log.splitlines()if l.startswith('SYSTEM_FRAME_PASS')];times=[fields(l)for l in log.splitlines()if l.startswith('SYSTEM_TIMING')]
  assert len(rows)==len(times)==2
  wc,wb,reqs=(83040,664320,2640)if mode=='burst'else(101520,812160,21120)
  assert all(r['actual_writes']==664320 and r['actual_write_commands']==wc and r['actual_write_bus_beats']==wb and r['hud_burst']==int(mode=='burst')and r['hud_write_requests']==r['hud_read_requests']==reqs and r['painter_read_commands']==35040 and r['painter_read_words']==280320 and r['painter_write_commands']==48000 and r['painter_write_words']==384000 and r['underruns']==0 for r in rows)
  t=times[1];assert t['fid']==1 and t['generation']==2 and t['planned_admission_cycle']==t['admission_cycle']==20000000+off and t['packet_complete_cycle']+1==t['admission_cycle'] and t['warm_complete_rasters']>=1
  assert t['admission_front_id']==0 and t['admission_front_generation']==1 and t['complete_rasters']>=1 and rows[1]['processor_commit_calls']>=2
  assert t['admission_sample_ps']==t['admission_cycle']*10000-5000
  assert t['packet_complete_cycle']<t['admission_cycle']<t['validated_ready_cycle']<t['rgb_ready_cycle']<=t['commit_ack_cycle']
  assert t['transaction_model_cycles']==t['commit_ack_cycle']-t['packet_complete_cycle']
  assert t['met_30fps_transaction_deadline']==int(t['transaction_model_cycles']<=3333333)and t['met_sub10ms_validated_deadline']==int(t['validated_decode_model_cycles']<1000000)
  record=dict(hud_mode=mode,offset_cycles=off,frames=rows,timings=times,summary=summary,
   P_validated_interval_model_ms=t['validated_decode_model_cycles']*1e-5,P_composition_model_ms=t['composition_model_cycles']*1e-5,P_transaction_model_ms=t['transaction_model_cycles']*1e-5)
  print(f"PHASE_CASE_PASS hud={mode} offset={off} validated_ms={record['P_validated_interval_model_ms']:.5f} transaction_ms={record['P_transaction_model_ms']:.5f}",flush=True)
  return record
 with ThreadPoolExecutor(max_workers=1 if a.first_only else a.workers)as executor:records=list(executor.map(one_job,jobs))
 command_map={Path(c['log']).name:c for c in commands}
 commands=[command_map['build.log']]+[command_map[f'run-{mode}-{off}.log']for mode,off in jobs]
 if not a.first_only:
  for off in OFFSETS:
   x,y=[r for r in records if r['offset_cycles']==off]
   for k in ('packet_complete_cycle','admission_cycle','admission_sample_ps','admission_x','admission_y','admission_de','admission_front_id','admission_front_generation'):assert x['timings'][1][k]==y['timings'][1][k],('crossmodephase',off,k)
 assert before==pins(),'qualified inputs changed'
 grouped={}
 for mode in sorted({r['hud_mode']for r in records}):
  selected=[r for r in records if r['hud_mode']==mode];grouped[mode]={name:{'min':min(r[name]for r in selected),'max':max(r[name]for r in selected)}for name in ('P_validated_interval_model_ms','P_composition_model_ms','P_transaction_model_ms')}
 d=dict(schema='cu76-phase-replay-v1',status='PASS_FUNCTIONAL_EXACT_FRAMEBUFFERS_AND_PHASES',campaign_complete=not a.first_only,performance_status='FAIL_30FPS_OR_SUB10MS_BUDGETS'if any(not r['timings'][1]['met_30fps_transaction_deadline']or not r['timings'][1]['met_sub10ms_validated_deadline']for r in records)else'PASS_MODELED_BUDGETS_ONLY',source_sha256=before,commands=commands,runs=records,ranges=grouped,
  runtime_workers=1 if a.first_only else a.workers,schedule=dict(planned_P_admission_base_cycle=20000000,offset_cycles=list(OFFSETS),packet_complete_lead_cycles=1,admission_cycle_is_tick_end=True,handshake_sample_ps='admission_cycle*10000-5000',warm_exact_complete_rasters_required=1),
  clocks=dict(memory_period_ps=10000,read_sample_phase_degrees=279,pixel_half_period_ps=17029),
  budgets=dict(transaction30fps_max_cycles=3333333,validated_sub10ms_strict_max_exclusive_cycles=1000000),
  scope='Frozen V75RTL actualcommand memory + packet/qmap/base/reference/HUDfunctionalreadback/nativeRGBoracle/liveLCD; fixedP admission after complete warm exact scanout, not bootstrap paced',limitations=['No physical30fps or targetsub10ms/Fmax/fit/CDC proof','NativeHUD CPU/readbackhash/controlCPU execution and liveESP32WiFi/QSPI service unmodeled','Two sources per phase and four synthetic arrival phases are not a1800distinctsource fixedarrivalcampaign','Systemadmissioncycle is tickend; sampledrequesthandshake is halfcycle earlier','Firstcorrectpixel mayinclude matchingblackborders, not input-to-photon latency','CheckedSDRAM commandmodel is not vendor/electricalsignoff'])
 dest=AREA/('first-results.json'if a.first_only else'results.json');dest.write_text(json.dumps(d,indent=2)+'\n')
 print('V76_PHASE_EVIDENCE_PASS campaign_complete='+str(not a.first_only)+' performance='+d['performance_status'])
if __name__=='__main__':main()
