#!/usr/bin/env python3
"""Bounded native mapping/query of frozen exact extracted threshold arithmetic."""
import csv,datetime,hashlib,json,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SRC=ROOT/'fpga/experiments/cu66-v107-count-threshold';FLOW=ROOT/'fpga/experiments/cu66-v107-count-threshold-native';AREA=ROOT/'experiments/python-gamebub-v107/count-threshold/native-unit';BASE=Path('/home/lori/gamebub-build/cu66-v69')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def memory():
 m={x.split(':')[0]:int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines()};f=next(x for x in Path('/proc/pressure/memory').read_text().splitlines() if x.startswith('full '));return dict(available_bytes=m['MemAvailable'],psi_full_avg10=float(f.split('avg10=')[1].split()[0]))
def main():
 recipe=json.loads((SRC/'edit-recipe.json').read_text());probe=SRC/'verification/threshold_math_probe.sv';assert sha(probe)=='70022c313ad91332a49e36daa3034cf055fad26c299d076feeb8e4a59d6cece4';extraction=json.loads((SRC/'verification/math-block.json').read_text());production=ROOT/extraction['production'];s=production.read_text();start=s.index('    // COUNT_THRESHOLD_PIPELINE_BEGIN');end=s.index('    // COUNT_THRESHOLD_PIPELINE_END')+len('    // COUNT_THRESHOLD_PIPELINE_END');block=s[start:end];assert hashlib.sha256(block.encode()).hexdigest()==extraction['extracted_sha256'];assert probe.read_text().count(block)==1
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/stamp;out.mkdir(parents=True);build=BASE/('v107-threshold-unit-'+stamp);build.mkdir();mapped='/build/'+build.name
 files=[SRC/name for name in recipe['production']]+[SRC/'edit-recipe.json',probe,SRC/'verification/math-block.json',*sorted(p for p in FLOW.iterdir() if p.is_file()),Path(__file__).resolve()]
 hashes={str(p.relative_to(ROOT)):sha(p) for p in files}
 for p in files:q=out/'sources'/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
 for p in [probe,*[x for x in FLOW.iterdir() if x.is_file()]]:shutil.copyfile(p,build/p.name)
 gate=memory();assert gate['available_bytes']>=8*1024**3 and gate['psi_full_avg10']<1,gate
 name='gamebub-v107-threshold-unit-'+stamp.lower();cmd=['docker','run','--rm','--init','--name',name,'--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--network','host','--ulimit','core=0','--mount','type=bind,src=/home/lori/acorn-nexys4-ddr/tools,dst=/opt/amd-tools,readonly','--mount','type=bind,src=/home/lori/acorn-nexys4-ddr/cache/vivado.lic,dst=/root/.Xilinx/license.dat,readonly','--mount',f'type=bind,src={build},dst={mapped}','-e','LD_PRELOAD=/lib/x86_64-linux-gnu/libudev.so.1','-e','XILINXD_LICENSE_FILE=/root/.Xilinx/license.dat','-w',mapped,'acorn-nexys4-ddr:2026.1','timeout','--signal=TERM','--kill-after=15s','300s','/opt/amd-tools/2026.1/Vivado/bin/vivado','-mode','batch','-nojournal','-nolog','-notrace','-source','run.tcl','-tclargs',mapped]
 r=dict(schema='v107-frozen-extracted-threshold-native-unit-v1',status='RUNNING',command=cmd,source_sha256=hashes,extracted_block_sha256=extraction['extracted_sha256'],wrapper_sha256=sha(probe),build_external=str(build),part='xc7a100tcsg324-1',synthetic_clock_ns=10,source_unmodified=True,tools_and_license_readonly=True,timeout_seconds=300,cpus=2,max_threads=2,memory_limit_bytes=8*1024**3,memory_samples=[],scope='Exact arithmetic extraction only, synthetic numerator byte plumbing; not whole-ingress, decoder, routed timing, board clock, or hardware proof. Physical sharing/count need not match18 source multiplications.');write(out/'receipt.json',r);began=time.monotonic();last=-5;stop=None;code=None
 print('THRESHOLD_NATIVE_UNIT_STARTED',out.relative_to(ROOT),flush=True)
 try:
  with (out/'tool.log').open('w') as log:
   proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
   while proc.poll() is None:
    elapsed=time.monotonic()-began
    if elapsed-last>=5:
     sample=dict(elapsed_seconds=elapsed,**memory());r['memory_samples'].append(sample);last=elapsed
     if sample['available_bytes']<4*1024**3 or sample['psi_full_avg10']>=5:stop='HOST_MEMORY_GATE'
    if elapsed>340:stop='HOST_TIMEOUT'
    if stop:subprocess.run(['docker','stop','--time','10',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=20);break
    time.sleep(.5)
   code=proc.wait(timeout=30)
  assert code==0 and not stop,(code,stop)
  text=(out/'tool.log').read_text(errors='replace');assert 'V107_THRESHOLD_EXTRACTED_NATIVE_MAPPING_COMPLETE' in text
  def rows(name):return list(csv.DictReader((build/'results'/name).open(),delimiter='\t'))
  dsps=rows('dsp-registers.tsv');ff=rows('ff-control-pins.tsv');dc=rows('dsp-control-pins.tsv');srl=rows('srls.tsv');assert dsps and ff
  metrics=dict(DSP48E1=len(dsps),DSP_register_configs=sorted(set((int(x['AREG']),int(x['BREG']),int(x['MREG']),int(x['PREG'])) for x in dsps)),DSPs_with_neither_MREG_nor_PREG=[x['cell'] for x in dsps if int(x['MREG'])==0 and int(x['PREG'])==0],fabric_FFs=len(set(x['cell'] for x in ff)),data_FFs=len(set(x['cell'] for x in ff if x['role']=='data')),control_FFs=len(set(x['cell'] for x in ff if x['role']=='control')),data_reset_pins=len([x for x in ff if x['role']=='data' and x['pin'] in ('R','S','CLR','PRE')]),data_reset_non_GND=[x for x in ff if x['role']=='data' and x['pin'] in ('R','S','CLR','PRE') and x['driver_types']!='GND'],data_CE_external_ports=[x for x in ff if x['role']=='data' and x['pin']=='CE' and x['input_ports']],data_CE_constants=sorted(set(x['driver_types'] for x in ff if x['role']=='data' and x['pin']=='CE' and x['driver_types'] in ('GND','VCC'))),data_CE_register_drivers=sorted(set(x['drivers'] for x in ff if x['role']=='data' and x['pin']=='CE' and x['sequential_starts'])),DSP_non_GND_resets=[x for x in dc if x['pin'].startswith('RST') and x['driver_types']!='GND'],SRLs=len(srl),SRL_types=sorted(set(x['primitive'] for x in srl)))
  r.update(status='PASS_MEASURED_EXTRACTED_UNIT_MAPPING',metrics=metrics,warnings=[line for line in text.splitlines() if 'WARNING:' in line or 'CRITICAL WARNING:' in line])
 except BaseException as e:r.update(status='FAIL_NATIVE_TOOL_OR_QUERY',error=repr(e));raise
 finally:
  r.update(exit_code=code,stop_reason=stop,wall_seconds=time.monotonic()-began,source_unchanged=hashes=={str(p.relative_to(ROOT)):sha(p) for p in files})
  if not r['source_unchanged']:r['status']='FAIL_SOURCE_DRIFT'
  artifacts={}
  for p in sorted((build/'results').glob('*')):
   if not p.is_file():continue
   artifacts[p.name]=dict(sha256=sha(p),bytes=p.stat().st_size,external_path=str(p))
   if p.suffix in ('.rpt','.tsv','.v','.xdc') and p.stat().st_size<16*1024**2:q=out/'reports'/p.name;q.parent.mkdir(exist_ok=True);shutil.copyfile(p,q)
  r['artifacts']=artifacts;r['retained_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='receipt.json'};write(out/'receipt.json',r);write(AREA/'results.json',dict(status=r['status'],selected_receipt=str((out/'receipt.json').relative_to(ROOT)),sha256=sha(out/'receipt.json')));print('THRESHOLD_NATIVE_UNIT_FINISHED',r['status'],code,flush=True)
 if r['status']!='PASS_MEASURED_EXTRACTED_UNIT_MAPPING':raise SystemExit(1)
if __name__=='__main__':main()
