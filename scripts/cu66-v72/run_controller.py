#!/usr/bin/env python3
"""Masked BL8 actual-command/controller regression; no target timing claim."""
import hashlib,json,os,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'fpga/experiments/cu66-v72/memory'
OUT=AREA/'controller'
CONTAINER=os.environ.get('TASK_CONTAINER','gamebub-cu66-v69-build')
SOURCES=[AREA/'cu72_sdram_controller.sv',AREA/'cu72_sdram_model.sv',OUT/'tb_controller.sv']
PINS=SOURCES+[Path(__file__).resolve()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
pins={str(p.relative_to(ROOT)):sha(p)for p in PINS};commands=[];runs=[]
def run(argv,name,timeout=300):
 p=OUT/name
 with p.open('w')as f:r=subprocess.run(argv,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
 commands.append(dict(argv=argv,log=str(p.relative_to(ROOT)),exit_code=r.returncode,sha256=sha(p)))
 if r.returncode:raise RuntimeError(f'{name} exit{r.returncode}; retained log')
 return p.read_text()
for tac in(2,7):
 build=f'/build/v72-controller-tac{tac}'
 common=['-DSIMULATION',*map(str,SOURCES)]
 run(['docker','exec',CONTAINER,'verilator','--binary','--timing','--Wall','-Wno-BLKSEQ','--top-module','tb_controller','-GTAC_NS='+str(tac)+'.0','--Mdir',build,'-j','1',*common],f'build-tac{tac}.log')
 run(['docker','exec',CONTAINER,'iverilog','-g2012',f'-Ptb_controller.TAC_NS={tac}.0','-s','tb_controller','-o',build+'.vvp',*common],f'iverilog-build-tac{tac}.log')
 for seed in(7201,7202):
  pair=[]
  for backend,argv in(('verilator',[build+'/Vtb_controller']),('iverilog',['vvp',build+'.vvp'])):
   log=run(['docker','exec',CONTAINER,*argv,f'+SEED={seed}'],f'{backend}-tac{tac}-{seed}.log')
   match=re.search(r'^CONTROLLER_V72_PASS (.+)$',log,re.M)
   assert match and not any(t in log for t in('FATAL','Error:','FAIL'))
   counts={k:int(v)for k,v in re.findall(r'(\w+)=(\d+)',match[1])}
   assert counts['seed']==seed and counts['writes']==195 and counts['reads']==212 and counts['reset_probes']==9 and counts['reset_edge_probes']==1 and counts['mask_cases']==8
   pair.append(counts);runs.append(dict(backend=backend,tac_ns=tac,**counts));print('PASS',backend,tac,seed,flush=True)
  assert pair[0]==pair[1],'simulators disagree'
assert pins=={str(p.relative_to(ROOT)):sha(p)for p in PINS},'sourceschanged'
result=dict(schema='cu72-controller-results-v1',status='PASS',source_sha256=pins,commands=commands,runs=runs,scope='Actual masked BL8 controller commands and checked32MiB model, read sampling/tAC corners, byte preservation, refresh and reset prefixes',limitations=['Functional command model, not vendor/electrical signoff','No FPGA fit/routed clock/CDC proof','Caller must validate aligned physical bursts before controller admission','No physical30fps or under10ms proof'])
(OUT/'results.json').write_text(json.dumps(result,indent=2)+'\n')
print('CONTROLLER_V72_REGRESSION_PASS runs=8 sources_stable=true')
