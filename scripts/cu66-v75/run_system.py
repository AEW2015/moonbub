#!/usr/bin/env python3
"""Actual V75 receiver/memory/painter/LCD replay with scalar/burst HUD ablation."""
import argparse,hashlib,json,os,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'fpga/experiments/cu66-v75/system'
NATIVE=ROOT/'experiments/cu66-native-v69'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--frames',type=int,default=2);p.add_argument('--hud-mode',choices=('scalar','burst'),default='burst');a=p.parse_args()
 assert a.frames in (2,4),'bounded verified cohort sizes'
 spec=json.loads((AREA/'sources.json').read_text());suffix='strip-'+a.hud_mode;out=AREA/(('full-'if a.frames==2 else'history-'+str(a.frames)+'-')+suffix);out.mkdir(exist_ok=True)
 paths=[ROOT/x for x in spec['rtl_sources']]+[AREA/'tb_system.cpp',AREA/'sources.json',Path(__file__).resolve(),NATIVE/'index.tsv',ROOT/'fpga/experiments/cu66-v69/hud-partition/hud_gate.hpp',ROOT/'fpga/experiments/cu66-v69/packet/cu66_profile.svh',ROOT/'fpga/experiments/cu66-v69/inverse/cu66_quant_rom.svh',ROOT/'fpga/experiments/cu66-v70/memory/cu70_memory_map.svh',ROOT/'fpga/experiments/cu66-v70/memory/memory_map.hpp',*NATIVE.glob('*.hpp')]
 for line in (NATIVE/'index.tsv').read_text().splitlines()[:a.frames]:paths.append(NATIVE/line.split('\t')[2])
 def pins():return {str(p.relative_to(ROOT)):sha(p)for p in sorted(set(paths))}
 before=pins();commands=[];container=os.environ.get('TASK_CONTAINER','gamebub-cu66-v69-build')
 def run(argv,name,timeout):
  with(out/name).open('w')as f:r=subprocess.run(argv,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
  commands.append(dict(argv=argv,log=str((out/name).relative_to(ROOT)),exit_code=r.returncode,sha256=sha(out/name)))
  if r.returncode:raise RuntimeError(f'{name}: exit{r.returncode}; inspect retained log')
  return(out/name).read_text()
 mdir='/build/v75-system-strip'
 run(['docker','exec',container,'verilator','--cc','--exe','--build','-j','1',*spec['verilator_options'],'-DSIMULATION','--top-module','cu75_system_sim','-GUSE_STRIP=1','-GP0_CACHE_LINES=8','--Mdir',mdir,'-CFLAGS','-O2 -std=c++17',*['-I'+str(ROOT/x)for x in spec['include_dirs']],*[str(ROOT/x)for x in spec['rtl_sources']],str(AREA/'tb_system.cpp')],'build.log',1200)
 log=run(['docker','exec',container,mdir+'/Vcu75_system_sim',str(NATIVE/'index.tsv'),str(a.frames),a.hud_mode],'run.log',7200)
 m=re.search(r'^SYSTEM_PASS (.+)$',log,re.M);assert m and 'FAIL'not in log
 summary={k:int(v)for k,v in re.findall(r'(\w+)=(\d+)',m[1])};assert summary['complete_frames']==a.frames and summary['distinct_complete_presentations']==a.frames and summary['canonical_bytes_per_frame']==518400 and summary['RGB_words_per_frame']==384000 and summary['HUD_functional_readback_words_per_frame']==21120
 timings=[{k:int(v)for k,v in re.findall(r'(\w+)=(\d+)',line)}for line in log.splitlines()if line.startswith('SYSTEM_TIMING')]
 assert len(timings)==a.frames and len({t['fid']for t in timings})==a.frames
 assert all(t['packet_complete_cycle']<=t['admission_cycle']<t['validated_ready_cycle']<t['rgb_ready_cycle']<=t['commit_ack_cycle'] and t['complete_rasters']>0 for t in timings)
 rows=[{k:int(v)for k,v in re.findall(r'(\w+)=(\d+)',line)}for line in log.splitlines()if line.startswith('SYSTEM_FRAME_PASS')]
 wc,wb,reqs=(83040,664320,2640)if a.hud_mode=='burst'else(101520,812160,21120)
 assert len(rows)==a.frames
 assert all(row['actual_writes']==664320 and row['actual_write_commands']==wc and row['actual_write_bus_beats']==wb and row['hud_burst']==int(a.hud_mode=='burst') and row['hud_write_requests']==reqs and row['hud_read_requests']==reqs and row['painter_read_commands']==35040 and row['painter_read_words']==280320 and row['painter_write_commands']==48000 and row['painter_write_words']==384000 for row in rows)
 assert rows[1]['processor_commit_calls']>=2
 assert before==pins(),'systeminputs changed'
 result=dict(status='PASS_FUNCTIONAL_MEMORY_AND_FRAMEBUFFERS',cadence_status='FAIL_UNDERRUNS'if summary['total_underruns']else'NOT_QUALIFIED',hud_mode=a.hud_mode,canonical_layout='tile-major-8x8',p0_cache_lines=8,strip=True,source_sha256=before,commands=commands,frames=rows,timings=timings,summary=summary,clocks=dict(memory_period_ps=10000,read_sample_phase_degrees=279,pixel_half_period_ps=17029),timing_scope='modelcycleevents;immutablepacketstaging;validatedready=WAIT_RGB;RGBreadyafterpaint;nativeHUDCPUiszero-simtime',scope='actualRTLpacket/qmap/base/storedreferences/HUDscalar-or-BL8functionalreadback/portraitpainter/LCDdescriptorandcheckedSDRAMcommandmodel',limitations=['no physical30fps or targetsub10ms proof','no targetFmax/fit/CDCsignoff','nativeHUDCPUexecution/readbackhash/controlCPUtime not simulated','externalpacketBRAM not liveESP32WiFi/QSPI','checkedcommandmodel is not vendor/electricalsignoff','decoder-paced short history, not fixed-arrival30fps qualification','first_correct_pixel can include black borders, not first-game-image or input-to-photon latency'])
 (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
 print(f'SYSTEM_EVIDENCE_PASS frames={a.frames} hud={a.hud_mode} cadence='+result['cadence_status'])
if __name__=='__main__':main()
