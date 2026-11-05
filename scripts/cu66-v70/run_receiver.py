#!/usr/bin/env python3
"""Qualify full-packet receiver/control RTL with transactional external RAM."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'fpga/experiments/cu66-v70/receiver'
NATIVE=ROOT/'experiments/cu66-native-v69'
REL=[
 'fpga/experiments/cu66-v70/receiver/cu70_receiver.sv',
 'fpga/experiments/cu66-v69/packet/cu66_packet_control.sv',
 'fpga/experiments/cu66-v69/banks/cu66_frame_bank_control.sv',
 'fpga/experiments/cu66-v69/integration/cu66_base_pipeline.sv',
 *['fpga/experiments/cu66-v69/inverse/'+s for s in
   ('cu66_expand_tiles.sv','cu66_dequant.sv','cu66_idct8x8.sv','cu66_reconstruct_tile.sv')],
 'fpga/experiments/cu66-v69/entropy/cu66_ab38_decoder.sv',
 'fpga/experiments/cu66-v69/rows/cu66_tile_rows.sv',
 'fpga/experiments/cu66-v69/rows/cu66_rows_sha256.sv',
 'fpga/experiments/cu66-v69/hash/cu66_sha256_bytes.sv']

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--seed',type=int,default=7001)
 p.add_argument('--per-chain',type=int,default=9999);a=p.parse_args()
 container=os.environ.get('TASK_CONTAINER','gamebub-cu66-v69-build')
 deps=[ROOT/x for x in REL]+[AREA/'tb_receiver.cpp',Path(__file__).resolve(),NATIVE/'index.tsv',
  ROOT/'fpga/experiments/cu66-v69/packet/cu66_profile.svh',
  ROOT/'fpga/experiments/cu66-v69/inverse/cu66_quant_rom.svh',
  ROOT/'fpga/experiments/cu66-v69/hud-partition/hud_gate.hpp',
  ROOT/'fpga/experiments/cu66-v70/memory/memory_map.hpp',
  *NATIVE.glob('*.hpp'),*(NATIVE/'fixtures').glob('*.cu66')]
 def pins():return {str(x.relative_to(ROOT)):sha(x)for x in sorted(set(deps))}
 before=pins();commands=[]
 def run(argv,name,timeout=1200):
  dest=AREA/name
  with dest.open('w')as f:r=subprocess.run(argv,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
  commands.append({'argv':argv,'exit_code':r.returncode,'log':str(dest.relative_to(ROOT)),'log_sha256':sha(dest)})
  if r.returncode:raise RuntimeError(f'{name}: exit{r.returncode}; inspect retained log')
  return dest.read_text()
 run(['docker','exec',container,'verilator','--cc','--exe','--build','-j','2',
  '--Wall','-Wno-PINCONNECTEMPTY','--top-module','cu70_receiver','--Mdir','/build/v70-receiver',
  '-CFLAGS','-O2 -std=c++17','-I'+str(ROOT/'fpga/experiments/cu66-v69/inverse'),
  '-I'+str(ROOT/'fpga/experiments/cu66-v69/packet'),*[str(ROOT/x)for x in REL],str(AREA/'tb_receiver.cpp')],
  'build.log',600)
 log=run(['docker','exec',container,'/build/v70-receiver/Vcu70_receiver',str(NATIVE/'index.tsv'),
  str(a.seed),str(a.per_chain)],f'seed{a.seed}.log',3600)
 terminal=re.search(r'^PASS actual_frames=(\d+) fault_and_control_modes=7 seed=(\d+) clocks=(\d+) '
  r'memory_backend=transactional_RAM painter=completion_model scanout=descriptor_model$',log,re.M)
 assert terminal and int(terminal[2])==a.seed and 'FAIL'not in log
 expected=min(a.per_chain,120)+min(a.per_chain,120)+min(a.per_chain,120)+min(a.per_chain,97)
 # The retained index, not guessed cohort lengths, determines the full gate.
 cohorts={}
 for line in (NATIVE/'index.tsv').read_text().splitlines():
  c=line.split('\t',1)[0];cohorts[c]=cohorts.get(c,0)+1
 expected=sum(min(a.per_chain,n)for n in cohorts.values());assert int(terminal[1])==expected
 rows=[dict((k,int(v))for k,v in re.findall(r'(\w+)=(\d+)',line))for line in log.splitlines()if line.startswith('FRAME_PASS')]
 assert len(rows)==expected+21
 corpus=rows[:expected];assert all(x['mode']==0 and x['tiles']==8100 and x['error']==0 for x in corpus)
 for mode in range(1,8):assert len([x for x in rows if x['mode']==mode])==1
 assert next(x for x in rows if x['mode']==5)['stale']>=4
 assert next(x for x in rows if x['mode']==7)['commits']>=2
 assert before==pins(),'inputs changed during qualification'
 result={'status':'PASS','scope':'actual full-packet parser/qmap/base/owner RTL with stored RTL-output references and actual native HUD endpoint; transactional RAM and painter/scanout completion models',
  'actual_corpus_frames':expected,'keys':sum(x['key']for x in corpus),'tiles_per_frame':8100,
  'corpus_min_cycles':min(x['clocks']for x in corpus),'corpus_max_cycles':max(x['clocks']for x in corpus),
  'corpus_mean_cycles':sum(x['clocks']for x in corpus)/expected,'control_modes':7,'rows':rows,
  'source_sha256':before,'commands':commands,
  'not_proven':['actual SDRAM commands in this run','RTL painter/pixels in this run','processor service time','physical FPS','target fit/timing/CDC']}
 (AREA/'results.json').write_text(json.dumps(result,indent=2)+'\n')
 print(f'RECEIVER_PASS actual_corpus_frames={expected} modes=7 source_pins={len(before)}')
if __name__=='__main__':main()
