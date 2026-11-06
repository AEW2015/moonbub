from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,time
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/bus-split'
p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();o=Path(a.output).resolve();o.mkdir(parents=True,exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
sources=list(d.glob('*.sv'))+[r/'fpga/experiments/cu66-v71/board/source-v007/moonshine_bus_cdc.sv',r/'fpga/experiments/cu66-v71/board/source-v007/moonshine_qspi_endpoint.sv',r/'fpga/experiments/cu66-v71/system/cu71_local_control.sv',r/'fpga/experiments/cu66-v71/direct-system/local-control/dy71_local_control.sv',r/'fpga/experiments/cu66-v71/system/cu71_packet_staging.sv',r/'fpga/experiments/cu66-v71/system/cu71_packet_arbiter.sv',r/'fpga/experiments/cu66-v70/memory/cu70_memory_map.svh',Path(__file__)]
for f in sources:shutil.copy2(f,o/f.name)
pins={str(f):sha(f)for f in sources};(o/'source-freeze.json').write_text(json.dumps(dict(originals=pins,compiled={f.name:sha(o/f.name)for f in sources},scope='Actual original/split typed controls, bridge phase/queue/read/reset comparisons and unchanged physical QSPI wire endpoint simulation; no hardware'),indent=2)+'\n')
steps=[]
env=dict(os.environ,PATH='C:/msys64/ucrt64/bin;'+os.environ['PATH'])
def run(label,cmd):
 start=time.monotonic()
 with(o/(label+'.log')).open('wb')as out:q=subprocess.run(cmd,cwd=o,env=env,stdout=out,stderr=subprocess.STDOUT,timeout=300)
 steps.append(dict(label=label,command=cmd,returncode=q.returncode,seconds=time.monotonic()-start));(o/'execution.json').write_text(json.dumps(steps,indent=2)+'\n');print(label,q.returncode,flush=True);assert q.returncode==0,label
iv='C:/msys64/ucrt64/bin/iverilog.exe';vvp='C:/msys64/ucrt64/bin/vvp.exe';sv=[f.name for f in sources if f.suffix=='.sv'];results=[]
for top in('tb_bus_pair','tb_qspi_split'):
 for phase in('0.0','2.3'):
  for dy in((0,1)if top=='tb_bus_pair'else(0,)):
   label=top+'-phase'+phase+'-dy'+str(dy);cmd=[iv,'-g2012','-I.','-s',top,'-P'+top+('.PHASE='if top=='tb_bus_pair'else'.START_PHASE_NS=')+phase,'-o',label+'.vvp']
   if top=='tb_bus_pair':cmd+=['-P'+top+'.DY='+str(dy)]
   run(label+'-compile',cmd+sv);run(label,[vvp,label+'.vvp']);log=(o/(label+'.log')).read_text();assert('ACTUAL_CSR_BRIDGE_PAIR_PASS'in log if top=='tb_bus_pair'else'QSPI_CDC_PASS'in log);results.append(dict(label=label,report=log))
assert all(sha(Path(f))==h for f,h in pins.items())
(o/'result.json').write_text(json.dumps(dict(status='PASS_ACTUAL_OLD_SPLIT_BRIDGE_CSR_AND_UNCHANGED_QSPI_WIRE_SUITE',runs=results,source_freeze_sha256=sha(o/'source-freeze.json'),hardware=False,physical_timing=False,changed_latency=False),indent=2)+'\n')
