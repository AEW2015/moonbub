#!/usr/bin/env python3
"""Actual SDRAM/decoder rejection, partial-write abort, front retention and retry."""
import hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'fpga/experiments/cu66-v78/system'
NATIVE=ROOT/'experiments/cu66-native-v69'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=AREA/'faults';out.mkdir(exist_ok=True)
 spec=json.loads((AREA/'sources.json').read_text())
 files=[ROOT/p for p in spec['rtl_sources']]+[AREA/'sources.json',AREA/'tb_system.cpp',AREA/'tb_system_fault.cpp',Path(__file__).resolve(),NATIVE/'index.tsv',*NATIVE.glob('*.hpp'),ROOT/'fpga/experiments/cu66-v69/hud-partition/hud_gate.hpp',ROOT/'fpga/experiments/cu66-v70/memory/cu70_memory_map.svh',ROOT/'fpga/experiments/cu66-v70/memory/memory_map.hpp',ROOT/'fpga/experiments/cu66-v69/packet/cu66_profile.svh',ROOT/'fpga/experiments/cu66-v69/inverse/cu66_quant_rom.svh']
 files += [NATIVE/l.split('\t')[2] for l in (NATIVE/'index.tsv').read_text().splitlines()[:2]]
 pins={str(p.relative_to(ROOT)):sha(p)for p in sorted(set(files))};commands=[]
 def run(argv,name,timeout):
  with(out/name).open('w')as f:r=subprocess.run(argv,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
  commands.append(dict(argv=argv,log=str((out/name).relative_to(ROOT)),exit_code=r.returncode,sha256=sha(out/name)))
  if r.returncode:raise RuntimeError(f'{name} exit{r.returncode}; retained log')
  return(out/name).read_text()
 mdir='/build/v78-system-fault'
 run(['docker','exec','gamebub-cu66-v69-build','verilator','--cc','--exe','--build','-j','1',*spec['verilator_options'],'-DSIMULATION','-GTAC_NS=2.0','--top-module','cu78_system_sim','--Mdir',mdir,'-CFLAGS','-O2 -std=c++17',*['-I'+str(ROOT/p)for p in spec['include_dirs']],*[str(ROOT/p)for p in spec['rtl_sources']],str(AREA/'tb_system_fault.cpp')],'build.log',1200)
 log=run(['docker','exec','gamebub-cu66-v69-build',mdir+'/Vcu78_system_sim',str(NATIVE/'index.tsv')],'run.log',2400)
 fields=lambda line:{k:int(v)for k,v in re.findall(r'(\w+)=(\d+)',line)}
 rows=[dict(kind=re.search(r'kind=(\w+)',l)[1],**fields(l))for l in log.splitlines()if l.startswith('SYSTEM_FAULT_PASS ')]
 end=re.search(r'^SYSTEM_FAULT_CAMPAIGN_PASS (.+)$',log,re.M)
 assert end and 'FAIL'not in log and len(rows)==2
 summary=fields(end[1]);assert summary['rejected']==summary['accepted']==2 and summary['no_per_source_reset']==1 and summary['underruns']==summary['black_lines']==0
 assert rows[0]['kind']=='bad_crc' and rows[0]['physical_write_words']==0 and rows[0]['error']>0
 assert rows[1]['kind']=='partial_write_abort' and rows[1]['physical_write_words']>0 and rows[1]['canonical_write_words_observed']>=64 and rows[1]['active_tile_at_abort']==1 and rows[1]['processor_abort_calls']>0
 assert pins=={p:sha(ROOT/p)for p in pins},'source changed'
 (out/'results.json').write_text(json.dumps(dict(schema='cu78-system-fault-v1',status='PASS_REJECT_ABORT_RETAIN_AND_RECOVER',cases=rows,summary=summary,source_sha256=pins,commands=commands,limitations=['Two directed cases, not complete system fault coverage','Native HUD CPU endpoint has zero simulated cost','No live transport, target timing/CDC or physical proof','Fatal scanout/cache recovery remains unqualified']),indent=2)+'\n')
 print('V78_SYSTEM_FAULT_PASS rejected=2 accepted=2')
if __name__=='__main__':main()
