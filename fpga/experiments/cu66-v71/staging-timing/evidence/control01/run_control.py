"""Run actual typed CSR/async bridge differential with credit-stager binding."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,time
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/staging-timing';b=r/'fpga/experiments/cu66-v71/bus-split';a=argparse.ArgumentParser();a.add_argument('--output',required=True);args=a.parse_args();o=Path(args.output).resolve();o.mkdir(parents=True,exist_ok=False);sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
sources=[b/'cu71_bus_cdc_split.sv',b/'tb_bus_pair.sv',r/'fpga/experiments/cu66-v71/board/source-v007/moonshine_bus_cdc.sv',r/'fpga/experiments/cu66-v71/system/cu71_local_control.sv',r/'fpga/experiments/cu66-v71/direct-system/local-control/dy71_local_control.sv',r/'fpga/experiments/cu66-v71/system/cu71_packet_staging.sv',r/'fpga/experiments/cu66-v71/system/cu71_packet_arbiter.sv',r/'fpga/experiments/cu66-v70/memory/cu70_memory_map.svh',d/'cu71_packet_staging_credit.sv',d/'cu71_local_control_credit.sv',d/'dy71_local_control_credit.sv',Path(__file__).resolve()]
for f in sources:shutil.copyfile(f,o/f.name)
tb=o/'tb_bus_pair.sv';text=tb.read_text();text=text.replace('cu71_local_control_split','cu71_local_control_credit').replace('dy71_local_control_split','dy71_local_control_credit');tb.write_text(text,newline='\n')
pins={str(f):sha(f)for f in sources};(o/'source-freeze.json').write_text(json.dumps({'originals':pins,'compiled':{f.name:sha(o/f.name)for f in sources},'transform':'Only new-side split control module instances select versioned credit controls; all original controls/bridge fixture logic preserved'},indent=2)+'\n')
env=dict(os.environ,PATH='C:/msys64/ucrt64/bin;'+os.environ['PATH']);steps=[]
def run(label,cmd):
 start=time.monotonic()
 with(o/(label+'.log')).open('w')as log:p=subprocess.run(cmd,cwd=o,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=180)
 steps.append(dict(label=label,returncode=p.returncode,seconds=time.monotonic()-start,command=cmd));(o/'execution.json').write_text(json.dumps(steps,indent=2)+'\n');print(label,p.returncode,flush=True);assert p.returncode==0
iv='C:/msys64/ucrt64/bin/iverilog.exe';vvp='C:/msys64/ucrt64/bin/vvp.exe'
for phase in ['0.0','2.3']:
 for dy in [0,1]:
  label=f'control-phase{phase}-dy{dy}';run(label+'-compile',[iv,'-g2012','-I.','-s','tb_bus_pair','-Ptb_bus_pair.PHASE='+phase,'-Ptb_bus_pair.DY='+str(dy),'-o',label+'.vvp']+[f.name for f in sources if f.suffix=='.sv']);run(label,[vvp,label+'.vvp']);assert 'ACTUAL_CSR_BRIDGE_PAIR_PASS'in(o/(label+'.log')).read_text()
assert all(sha(Path(n))==h for n,h in pins.items())
(o/'result.json').write_text(json.dumps({'status':'PASS_ACTUAL_TYPED_CSR_ASYNC_BRIDGE_CREDIT_STAGER_DIFFERENTIAL','runs':4,'profiles':['CU71','DY71'],'phases_ns':[0.0,2.3],'hardware':False,'Vivado':False,'source_freeze_sha256':sha(o/'source-freeze.json')},indent=2)+'\n')
