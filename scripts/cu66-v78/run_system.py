#!/usr/bin/env python3
"""Actual FPGA decode -> canonical commit -> continuous direct native scanout."""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];AREA=ROOT/'fpga/experiments/cu66-v78/system';NATIVE=ROOT/'experiments/cu66-native-v69'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--frames',type=int,choices=(2,4,30),default=2);p.add_argument('--mode',choices=('paced','fixed30'),default='paced');p.add_argument('--tac',type=int,choices=(2,7),default=2);a=p.parse_args();out=AREA/f'frames{a.frames}-{a.mode}-tac{a.tac}';out.mkdir(exist_ok=True)
 spec=json.loads((AREA/'sources.json').read_text());paths=[ROOT/p for p in spec['rtl_sources']]+[AREA/'tb_system.cpp',AREA/'sources.json',Path(__file__).resolve(),NATIVE/'index.tsv',ROOT/'fpga/experiments/cu66-v69/hud-partition/hud_gate.hpp',ROOT/'fpga/experiments/cu66-v70/memory/cu70_memory_map.svh',ROOT/'fpga/experiments/cu66-v70/memory/memory_map.hpp',ROOT/'fpga/experiments/cu66-v69/packet/cu66_profile.svh',ROOT/'fpga/experiments/cu66-v69/inverse/cu66_quant_rom.svh',*NATIVE.glob('*.hpp')]
 for l in (NATIVE/'index.tsv').read_text().splitlines()[:a.frames]:paths.append(NATIVE/l.split('\t')[2])
 pins={str(p.relative_to(ROOT)):sha(p)for p in sorted(set(paths))};cmds=[]
 def run(argv,name,timeout):
  with(out/name).open('w')as f:r=subprocess.run(argv,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
  cmds.append(dict(argv=argv,log=str((out/name).relative_to(ROOT)),exit_code=r.returncode,sha256=sha(out/name)))
  if r.returncode:raise RuntimeError(f'{name}: exit{r.returncode}; retained log')
  return(out/name).read_text()
 mdir=f'/build/v78-system-tac{a.tac}'
 run(['docker','exec','gamebub-cu66-v69-build','verilator','--cc','--exe','--build','-j','1',*spec['verilator_options'],'-DSIMULATION',f'-GTAC_NS={a.tac}.0','--top-module','cu78_system_sim','--Mdir',mdir,'-CFLAGS','-O2 -std=c++17',*['-I'+str(ROOT/p)for p in spec['include_dirs']],*[str(ROOT/p)for p in spec['rtl_sources']],str(AREA/'tb_system.cpp')],'build.log',1200)
 log=run(['docker','exec','gamebub-cu66-v69-build',mdir+'/Vcu78_system_sim',str(NATIVE/'index.tsv'),str(a.frames),a.mode],'run.log',7200)
 fields=lambda l:{k:int(v)for k,v in re.findall(r'(\w+)=(\d+)',l)}
 end=re.search(r'^SYSTEM_PASS (.+)$',log,re.M);assert end and 'FAIL'not in log
 summary=fields(end[1]);rows=[fields(l)for l in log.splitlines()if l.startswith('SYSTEM_FRAME_PASS')];times=[fields(l)for l in log.splitlines()if l.startswith('SYSTEM_TIMING')]
 assert len(rows)==len(times)==a.frames and summary['complete_frames']==summary['distinct_complete_presentations']==a.frames and summary['black_lines']==summary['total_underruns']==0
 assert all(r['actual_writes']==280320 and r['actual_write_commands']==35040 and r['actual_write_bus_beats']==280320 and r['hud_write_requests']==r['hud_read_requests']==2640 for r in rows)
 assert all(t['packet_complete_cycle']<=t['admission_cycle']<t['validated_ready_cycle']<=t['commit_ack_cycle'] and t['complete_rasters']>0 for t in times)
 assert rows[1]['processor_commit_calls']>=2
 assert pins=={p:sha(ROOT/p)for p in pins},'qualified sources changed'
 d=dict(schema='cu78-actual-decode-direct-system-v1',status='PASS_ACTUAL_DECODE_CANONICAL_AND_NATIVE_DISPLAY',frames=rows,timings=times,summary=summary,source_sha256=pins,commands=cmds,arrival_mode=a.mode,tac_ns=a.tac,clocks=dict(memory_period_ps=10000,read_phase_degrees=279,pixel_half_period_ps=17029),performance=dict(serial_30fps_all_pass=all(t['met_serial_30fps_budget']for t in times),validated_under10ms_all_pass=all(t['met_validated_under10ms']for t in times),validated_model_ms=[t['validated_decode_model_cycles']*1e-5 for t in times],origin_to_ack_model_ms=[(t['commit_ack_cycle']-t['packet_complete_cycle'])*1e-5 for t in times]),scope='Actual packet/parser/qmap/inverse/hash FPGA decode, hardware-produced stored references/canonical planes, native semantic HUD through real transfer/readback, canonical commit+CPU ACK retry, continuous direct cache/converter/nativeLCD; no canonical seeding or golden-reference injection',limitations=['NativeHUDCPU/hash/control execution is zero-simtime','No liveESP32WiFi/QSPI or targetFmax/fit/CDC/electrical proof','Finite fixture replay not1800-source/60s or18000-source600s qualification','fixed30 uses immutable modeled releases and records queuing, not validated ESP32 queue capacity','No physical30fps or strict validatedtargetunder10ms proof'])
 (out/'results.json').write_text(json.dumps(d,indent=2)+'\n');print(f'V78_SYSTEM_PASS frames={a.frames} mode={a.mode} serial30={d["performance"]["serial_30fps_all_pass"]} sub10={d["performance"]["validated_under10ms_all_pass"]}')
if __name__=='__main__':main()
