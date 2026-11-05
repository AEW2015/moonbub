#!/usr/bin/env python3
import hashlib,json,os,re,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parents[3];C=os.environ.get('TASK_CONTAINER','gamebub-cu66-v69-build')
S=['tb_memory.sv','cu70_tile_memory.sv','cu70_word_bridge.sv','cu70_memory_system.sv','cu70_sdram_controller.sv','cu70_sdram_model.sv']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
pins={n:sha(H/n)for n in S+['cu70_memory_sim.sv','cu70_memory_map.svh','memory_map.hpp','memory-map.json','generate_map.py','run_regression.py']}
commands=[]
def run(argv,name,timeout=300):
 with (H/name).open('w')as out:p=subprocess.run(argv,cwd=ROOT,stdout=out,stderr=subprocess.STDOUT,timeout=timeout)
 commands.append(dict(argv=argv,log=name,exit_code=p.returncode,sha256=sha(H/name)))
 if p.returncode:raise RuntimeError(f'{name}:exit{p.returncode}; see retainedlog')
 return (H/name).read_text()
run(['docker','exec',C,'verilator','--binary','--timing','--Wall','-Wno-BLKSEQ','--top-module','tb_memory','-DSIMULATION','--Mdir','/build/v70-memory','-j','2','-I'+str(H),*[str(H/n)for n in S]],'build.log')
run(['docker','exec',C,'iverilog','-g2012','-DSIMULATION','-I'+str(H),'-s','tb_memory','-o','/build/v70-memory-iverilog.vvp',*[str(H/n)for n in S]],'iverilog-build.log')
results=[]
for seed in (7001,7002,7003):
 for backend,cmd in [('verilator',['/build/v70-memory/Vtb_memory']),('iverilog',['vvp','/build/v70-memory-iverilog.vvp'])]:
  text=run(['docker','exec',C,*cmd,f'+SEED={seed}'],f'{backend}-{seed}.log')
  m=re.search(r'^MEMORY_PASS (.+)$',text,re.M)
  assert m and not any(x in text for x in ('FATAL','Error:','FAIL')),text[-3000:]
  row={k:int(v)for k,v in re.findall(r'(\w+)=(\d+)',m[1])};assert row['seed']==seed and row['tiles']>=227 and row['aborts']==43 and row['REF']>4
  results.append(dict(backend=backend,**row));print('PASS',backend,seed,row['cycles'],flush=True)
 for key in ('checks','tiles','aux','aborts','cycles','writes','reads','ACT','PRE','REF','cache_hits','cache_misses','max_aux_wait'):
  assert results[-1][key]==results[-2][key],(seed,key)
# Read-data tAC slow corner through both actualcontroller/simulation backends.
run(['docker','exec',C,'verilator','--binary','--timing','--Wall','-Wno-BLKSEQ','--top-module','tb_memory','-GTAC_NS=7.0','-DSIMULATION','--Mdir','/build/v70-memory-tac7','-j','2','-I'+str(H),*[str(H/n)for n in S]],'build-tac7.log')
run(['docker','exec',C,'iverilog','-g2012','-DSIMULATION','-Ptb_memory.TAC_NS=7.0','-I'+str(H),'-s','tb_memory','-o','/build/v70-memory-tac7-iverilog.vvp',*[str(H/n)for n in S]],'iverilog-build-tac7.log')
for backend,cmd in [('verilator',['/build/v70-memory-tac7/Vtb_memory']),('iverilog',['vvp','/build/v70-memory-tac7-iverilog.vvp'])]:
 text=run(['docker','exec',C,*cmd,'+SEED=7001'],f'{backend}-tac7.log')
 m=re.search(r'^MEMORY_PASS (.+)$',text,re.M);assert m and not any(x in text for x in ('FATAL','Error:','FAIL'))
 row={k:int(v)for k,v in re.findall(r'(\w+)=(\d+)',m[1])}
 for key,value in row.items():assert value==results[0][key],('tac7',backend,key,value,results[0][key])
 results.append(dict(backend=backend,tac_ns=7,**row));print('PASS',backend,'tac7',row['cycles'],flush=True)
assert pins=={n:sha(H/n)for n in pins},'source changed duringregression'
result=dict(schema='cu70-memory-component-results-v1',status='PASS',scope='actualconservativeSDRAMcontroller+checked32MiBfunctionalcommandmodel+packed-u8tile+scalarauxcache; noelectrical/timing/fit/wholepipelineclaim',source_sha256=pins,commands=commands,runs=results,limitations=['boundedfunctionalmodel,notvendortimingsignoff','SIMULATIONpadbranch,notODDR/IOBUFtiming','100MHzclockisbenchconfiguration,notroutedFmax','partialcanonicalabortsuppressessuccessanddrainsacceptedword;upstreammustcoordinatecancel','maincomponentcasesarenotfull457frameorcontinuousLCDqualification'])
(H/'results.json').write_text(json.dumps(result,indent=2)+'\n');print('MEMORY_REGRESSION_PASS runs=8 bothsimulators=3seeds plus_tac7_corner source_stable=true')
