#!/usr/bin/env python3
"""Actual frozen SDRAM command-model replay of a synthetic direct-YUV cache trace."""
import argparse,hashlib,json,os,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];AREA=ROOT/'fpga/experiments/cu66-v76/service';OLD=ROOT/'fpga/experiments/cu66-v74/memory';CTRL=ROOT/'fpga/experiments/cu66-v72/memory';CONTAINER=os.environ.get('TASK_CONTAINER','gamebub-cu66-v69-build')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--quick',action='store_true');a=ap.parse_args()
 spec=[AREA/'tb_service_v76.sv',*[OLD/n for n in ('cu74_word_bridge.sv','cu74_memory_system.sv','cu74_tile_memory.sv')],*[CTRL/n for n in ('cu72_sdram_controller.sv','cu72_sdram_model.sv')]]
 files=spec+[ROOT/'fpga/experiments/cu66-v70/memory/cu70_memory_map.svh',AREA/'trace.mem',AREA/'reference.mem',AREA/'trace.json',ROOT/'scripts/cu66-v76/generate_service_trace.py',Path(__file__).resolve(),ROOT/'experiments/cu66-native-v69/generated_constants.hpp']
 pins={str(p.relative_to(ROOT)):sha(p)for p in files};commands=[];runs=[]
 def run(argv,name,timeout=600):
  p=AREA/name
  with p.open('w')as f:r=subprocess.run(argv,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
  commands.append(dict(argv=argv,log=str(p.relative_to(ROOT)),exit_code=r.returncode,sha256=sha(p)))
  if r.returncode:raise RuntimeError(f'{name}: exit{r.returncode}, retained log')
  return p.read_text()
 for tac in ((2,)if a.quick else(2,7)):
  mdir='/build/v76-service-tac'+str(tac)
  common=['-DSIMULATION','-I'+str(ROOT/'fpga/experiments/cu66-v70/memory'),*map(str,spec)]
  run(['docker','exec',CONTAINER,'verilator','--binary','--timing','--Wall','-Wno-BLKSEQ','--top-module','tb_service_v76',f'-GTAC_NS={tac}.0','--Mdir',mdir,'-j','1',*common],f'{"quick-"if a.quick else""}build-tac{tac}.log')
  cases=[(0,0,0)]if a.quick else[(r,b,0)for r,b in [(0,0),(1,0),(0,1),(1,1),(0,2),(1,2)]]+([(0,0,1),(1,0,1)]if tac==2 else[])
  for route,bg,gap in cases:
   log=run(['docker','exec',CONTAINER,mdir+'/Vtb_service_v76','+TRACE='+str(AREA/'trace.mem'),'+REF='+str(AREA/'reference.mem'),f'+ROUTE={route}',f'+BACKGROUND={bg}',f'+ISSUE_GAP={gap}','+REFBANK=0'],f'{"quick-"if a.quick else""}run-tac{tac}-route{route}-bg{bg}-gap{gap}.log')
   m=re.search(r'^SERVICE_PASS (.+)$',log,re.M);assert m and not re.search(r'(^|\s)(FAIL|FATAL)(\s|:|$)',log,re.M)
   row={k:int(v)for k,v in re.findall(r'(\w+)=(\d+)',m[1])};strips=[{k:int(v)for k,v in re.findall(r'(\w+)=(\d+)',line)}for line in log.splitlines()if line.startswith('SERVICE_STRIP')]
   assert row['strips']==len(strips)==90 and row['bursts']==35040 and row['compared_words']==280320
   assert sum(s['bursts']for s in strips)==35040 and sum(s['late_cycles']>0 for s in strips)==row['deadline_misses']
   assert row['drained_w']==row['released_w'] and row['drained_r']==row['released_r']
   assert row['writes']==row['drained_w']*32 and row['write_commands']==row['drained_w']*4 and row['write_bus_beats']==row['writes']
   row.update(tac_ns=tac,strips_detail=strips,deadline_status='PASS'if row['deadline_misses']==0 else'FAIL',max_service_us=row['max_service_cycles']*.01,elapsed_us=row['measured_cycles']*.01)
   runs.append(row);print(f"SERVICE_RUN_PASS tac={tac} route={route} bg={bg} max_us={row['max_service_us']:.2f} deadline={row['deadline_status']} misses={row['deadline_misses']}",flush=True)
 assert pins=={p:sha(ROOT/p)for p in pins},'qualified inputs changed'
 d=dict(schema='v76-direct-service-results-v1',status='PASS_FUNCTIONAL_SERVICE_REPLAY',scope='Actual frozen RTL/controller/checked SDRAM command model serving synthetic software-cache miss schedules; no RTLcache, YUVconversion, video pixels, descriptor leases or fullstreaming proof',source_sha256=pins,commands=commands,runs=runs,quick=a.quick,clocks=dict(memory_period_ps=10000,read_phase_degrees=279,T_AC_ns=[2]if a.quick else[2,7],clock_flight_ns=4),deadline_ps=147403024,cache_assumption=dict(YUV_lines=720,HUD_lines=192,line_bytes=16,RTL_implemented=False),background=dict(mode0='none',mode1='paced independent absolute writes8100tiles*30/sec and reads7806tiles*30/sec; referenceorder staticSAFE maps, not livepacketdecode; backlogneverdiscarded',mode2='continuous alternating complete write/read tile saturation; not30fps',write_bank=1,reference_bank=0,front_bank=0,admission='actual legal client handshakes; releases absolute; measurement-end backlog recorded then drained'),limitations=['functionalPASS is separate from deadlinePASS/FAIL','setup through actual physical P1writes, excluded from measuredinterval','softwarecache trace assumes instantaneous tags/conversion and separate3072byteHUDLRU; no exact-pixel renderer proof','100MHzassumed model not routedFmax or physicalSDRAMproof','no CPU/ESP32transport/packetdecoder timing','panel8rowdeadline includes allforegroundrequest/service/drain and priorstripbacklog; no fabricatedlatency','end modelcounts include backgroundtaildrain; foregroundelapsed ends at finalstripresponse'])
 (AREA/('quick-results.json'if a.quick else'results.json')).write_text(json.dumps(d,indent=2)+'\n')
 print('V76_SERVICE_EVIDENCE_PASS functional=true deadline_verdicts_retained=true')
if __name__=='__main__':main()
