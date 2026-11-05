#!/usr/bin/env python3
"""Actual receiver/controller/painter/LCD simulation; report deadline failures."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'fpga/experiments/cu66-v73/system'
NATIVE=ROOT/'experiments/cu66-native-v69'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--frames',type=int,default=4);p.add_argument('--strip',action='store_true',default=True);p.add_argument('--p0-cache-lines',type=int,choices=(1,8),default=8);a=p.parse_args()
 spec=json.loads((AREA/'sources.json').read_text());suffix=('strip'if a.strip else'direct')+('-cache1'if a.p0_cache_lines==1 else'');out=AREA/('history-'+str(a.frames)+'-'+suffix);out.mkdir(exist_ok=True)
 paths=[ROOT/x for x in spec['rtl_sources']]+[AREA/'tb_system.cpp',AREA/'sources.json',Path(__file__).resolve(),NATIVE/'index.tsv',
  ROOT/'fpga/experiments/cu66-v69/hud-partition/hud_gate.hpp',
  ROOT/'fpga/experiments/cu66-v69/packet/cu66_profile.svh',ROOT/'fpga/experiments/cu66-v69/inverse/cu66_quant_rom.svh',
  ROOT/'fpga/experiments/cu66-v70/memory/cu70_memory_map.svh',ROOT/'fpga/experiments/cu66-v70/memory/memory_map.hpp',
  *NATIVE.glob('*.hpp')]
 for line in (NATIVE/'index.tsv').read_text().splitlines()[:a.frames]:paths.append(NATIVE/line.split('\t')[2])
 def pins():return {str(p.relative_to(ROOT)):sha(p)for p in sorted(set(paths))}
 before=pins();commands=[];container=os.environ.get('TASK_CONTAINER','gamebub-cu66-v69-build')
 def run(argv,name,timeout):
  with(out/name).open('w')as f:r=subprocess.run(argv,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
  commands.append(dict(argv=argv,log=str((out/name).relative_to(ROOT)),exit_code=r.returncode,sha256=sha(out/name)))
  if r.returncode:raise RuntimeError(f'{name}: exit{r.returncode}; inspect retained log')
  return(out/name).read_text()
 args=['docker','exec',container,'verilator','--cc','--exe','--build','-j','1',*spec['verilator_options'],
  '-DSIMULATION','--top-module','cu73_system_sim',f'-GUSE_STRIP={int(a.strip)}',f'-GP0_CACHE_LINES={a.p0_cache_lines}','--Mdir','/build/v73-system-'+suffix,
  '-CFLAGS','-O2 -std=c++17',*['-I'+str(ROOT/x)for x in spec['include_dirs']],
  *[str(ROOT/x)for x in spec['rtl_sources']],str(AREA/'tb_system.cpp')]
 run(args,'build.log',1200)
 log=run(['docker','exec',container,'/build/v73-system-'+suffix+'/Vcu73_system_sim',str(NATIVE/'index.tsv'),str(a.frames)],'run.log',7200)
 m=re.search(r'^SYSTEM_PASS (.+)$',log,re.M);assert m and 'FAIL'not in log
 summary={k:int(v)for k,v in re.findall(r'(\w+)=(\d+)',m[1])};assert summary['complete_frames']==a.frames and summary['canonical_bytes_per_frame']==518400 and summary['RGB_words_per_frame']==384000 and summary['HUD_functional_readback_words_per_frame']==21120
 timings=[{k:int(v)for k,v in re.findall(r'(\w+)=(\d+)',line)}for line in log.splitlines()if line.startswith('SYSTEM_TIMING')]
 assert len(timings)==a.frames and len({t['fid']for t in timings})==a.frames
 assert all(t['packet_complete_cycle']<=t['admission_cycle']<t['validated_ready_cycle']<t['rgb_ready_cycle']<=t['commit_ack_cycle']for t in timings)
 assert summary['distinct_complete_presentations']==sum(t['complete_rasters']>0 for t in timings)
 rows=[{k:int(v)for k,v in re.findall(r'(\w+)=(\d+)',line)}for line in log.splitlines()if line.startswith('SYSTEM_FRAME_PASS')]
 assert all(row['actual_writes']==664320 and row['actual_write_commands']==133920 and row['actual_write_bus_beats']==1071360 and row['painter_write_commands']==48000 and row['painter_write_words']==384000 for row in rows)
 assert len(rows)==a.frames and (a.frames<2 or rows[1]['processor_commit_calls']>=2)
 assert before==pins(),'systeminputs changed'
 result=dict(status='PASS_FUNCTIONAL_MEMORY_AND_FRAMEBUFFERS',
  cadence_status='FAIL_UNDERRUNS'if summary['total_underruns']else'NOT_QUALIFIED',
  timings=timings,
  timing_scope='modelcycleevents;packetcompleteimmutablebenchstage;WAIT_RGB=validatedready;nativeHUDsoftwareiszero-simtime;notvalidatedtargetlatency',
  scope='actualRTLpacket/qmap/base/storedreferences/HUDfunctionalauxtransfer/portraitpainter/LCDdescriptorwithrealcontrollercommandsandcheckedmodel',
  p0_cache_lines=a.p0_cache_lines,strip=a.strip,source_sha256=before,commands=commands,frames=rows,summary=summary,
  clocks=dict(memory_period_ps=10000,read_sample_phase_degrees=279,pixel_half_period_ps=17029),
  limitations=['nativeHUDsoftwareexecutiontime not simulated','externalpacketBRAM not liveQSPI','simplifiedcommandmodel not vendor/electricalsignoff','no targetFmax/fit/CDCsignoff','underruns remain failures of clean presentation; descriptorchanges are not complete presentedframes','no physical30fps','short chronological history; decoder-paced, not 30fps fixed arrivals','native HUD prepare wall timing is desktop diagnostics and not added to model clock; processor readback/hash/control CPU work also unmodeled'])
 (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
 print('SYSTEM_EVIDENCE_PASS frames='+str(a.frames)+' strip='+str(a.strip)+' cadence='+result['cadence_status'])
if __name__=='__main__':main()
