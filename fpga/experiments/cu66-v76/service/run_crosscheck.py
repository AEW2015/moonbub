#!/usr/bin/env python3
"""Independent Icarus replay of the near-deadline paced LCD service case."""
import hashlib,json,re,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
src=[H/'tb_service_v76.sv',*[R/'fpga/experiments/cu66-v74/memory'/n for n in ('cu74_word_bridge.sv','cu74_memory_system.sv','cu74_tile_memory.sv')],*[R/'fpga/experiments/cu66-v72/memory'/n for n in ('cu72_sdram_controller.sv','cu72_sdram_model.sv')]]
files=src+[H/'trace.mem',H/'reference.mem',Path(__file__).resolve(),R/'fpga/experiments/cu66-v70/memory/cu70_memory_map.svh'];pins={str(p.relative_to(R)):sha(p)for p in files};cs=[]
def run(argv,name):
 with(H/name).open('w')as f:p=subprocess.run(argv,cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=600)
 cs.append(dict(argv=argv,log=str((H/name).relative_to(R)),exit_code=p.returncode,sha256=sha(H/name)))
 assert p.returncode==0,(name,p.returncode)
 return(H/name).read_text()
vvp='/build/v76-service-iverilog.vvp'
run(['docker','exec','gamebub-cu66-v69-build','iverilog','-g2012','-Ptb_service_v76.TAC_NS=2.0','-s','tb_service_v76','-o',vvp,'-DSIMULATION','-I'+str(R/'fpga/experiments/cu66-v70/memory'),*map(str,src)],'iverilog-build.log')
log=run(['docker','exec','gamebub-cu66-v69-build','vvp',vvp,'+TRACE='+str(H/'trace.mem'),'+REF='+str(H/'reference.mem'),'+ROUTE=1','+BACKGROUND=1','+ISSUE_GAP=0','+REFBANK=0'],'iverilog-paced-lcd.log')
assert 'FAIL'not in log and 'FATAL'not in log
m=re.search(r'^SERVICE_PASS (.+)$',log,re.M);assert m
row={k:int(v)for k,v in re.findall(r'(\w+)=(\d+)',m[1])};assert row['compared_words']==280320 and row['strips']==90
old=(H/'run-tac2-route1-bg1-gap0.log').read_text();m2=re.search(r'^SERVICE_PASS (.+)$',old,re.M);other={k:int(v)for k,v in re.findall(r'(\w+)=(\d+)',m2[1])}
assert row==other,[(k,v,other.get(k))for k,v in row.items()if v!=other.get(k)]
assert pins=={p:sha(R/p)for p in pins}
d=dict(status='PASS_CROSS_SIMULATOR_SERVICE',scope='One tAC2 continuousissue sharedfront pacedLCDcase; functionalPASSseparatefromdeadlineFAIL',source_sha256=pins,commands=cs,iverilog=row,verilator_reference_sha256=sha(H/'run-tac2-route1-bg1-gap0.log'),all_summary_counters_identical=True)
(H/'crosscheck-results.json').write_text(json.dumps(d,indent=2)+'\n');print('V76_SERVICE_CROSSCHECK_PASS counters_identical=true')
