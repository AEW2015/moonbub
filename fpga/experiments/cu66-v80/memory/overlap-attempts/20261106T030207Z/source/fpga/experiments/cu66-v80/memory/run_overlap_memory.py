#!/usr/bin/env python3
"""Controlled mode0/mode1 overlap tests; preserve each attempt's exact sources."""
from pathlib import Path
import hashlib,json,subprocess,time
root=Path(__file__).resolve().parents[4];area=root/'fpga/experiments/cu66-v80/memory'
base=['docker','exec','gamebub-cu66-v69-build']
sources=[area/'tb_overlap_memory_v80.sv',area/'cu80_overlap_memory_system.sv']+[root/'fpga/experiments/cu66-v74/memory'/s for s in ('cu74_word_bridge.sv','cu74_tile_memory.sv')]+[root/'fpga/experiments/cu66-v72/memory'/s for s in ('cu72_sdram_controller.sv','cu72_sdram_model.sv')]
all_sources=sources+[root/'fpga/experiments/cu66-v70/memory/cu70_memory_map.svh',Path(__file__).resolve()]
attempt=area/'overlap-attempts'/time.strftime('%Y%m%dT%H%M%SZ',time.gmtime());attempt.mkdir(parents=True)
for source in all_sources:
 target=attempt/'source'/source.relative_to(root);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source.read_bytes())
manifest={'source_hashes':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in all_sources},'commands':[],'runs':[],'performance_claim':False}
def run(cmd,name):
 with (attempt/name).open('w') as f:p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=300)
 manifest['commands'].append({'argv':cmd,'log':name,'exit_code':p.returncode})
 (attempt/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 if p.returncode:print((attempt/name).read_text());raise SystemExit(p.returncode)
 return (attempt/name).read_text()
for release in (0,1):
 for tac in (2,7):
  build=f'/build/v80-integration/overlap-release{release}-tac{tac}'
  subprocess.run(base+['mkdir','-p',build],check=True)
  cmd=base+['verilator','--binary','--timing','--Wall','-Wno-BLKSEQ','--top-module','tb_overlap_memory_v80',f'-GTAC_NS={tac}.0',f'-GRELEASE_ON_SNAPSHOT={release}', '--Mdir',build,'-j','1','-DSIMULATION',f'-I{root}/fpga/experiments/cu66-v70/memory',*map(str,sources)]
  run(cmd,f'build-release{release}-tac{tac}.log')
  log=run(base+[build+'/Vtb_overlap_memory_v80'],f'run-release{release}-tac{tac}.log')
  print(log);manifest['runs'].append({'release':release,'tAC_ns':tac,'status':'pass','log':f'run-release{release}-tac{tac}.log'})
manifest['status']='pass';(attempt/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('OVERLAP_ATTEMPT',attempt.relative_to(root))
