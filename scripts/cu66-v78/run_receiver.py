#!/usr/bin/env python3
"""Bounded actual parser/base/direct-owner regression with transactional endpoints."""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];AREA=ROOT/'fpga/experiments/cu66-v78/receiver';NATIVE=ROOT/'experiments/cu66-native-v69'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--seed',type=int,default=7801);ap.add_argument('--per-chain',type=int,default=2);a=ap.parse_args()
 rel=json.loads((AREA/'sources.json').read_text());paths=[ROOT/p for p in rel]+[AREA/'tb_receiver.cpp',AREA/'sources.json',Path(__file__).resolve(),ROOT/'fpga/experiments/cu66-v69/packet/cu66_profile.svh',ROOT/'fpga/experiments/cu66-v69/inverse/cu66_quant_rom.svh',ROOT/'fpga/experiments/cu66-v69/hud-partition/hud_gate.hpp',ROOT/'fpga/experiments/cu66-v70/memory/memory_map.hpp',NATIVE/'index.tsv',*NATIVE.glob('*.hpp'),*(NATIVE/'fixtures').glob('*.cu66')]
 pins={str(p.relative_to(ROOT)):sha(p)for p in paths};commands=[]
 def run(argv,name,timeout):
  with(AREA/name).open('w')as f:p=subprocess.run(argv,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
  commands.append(dict(argv=argv,log=str((AREA/name).relative_to(ROOT)),exit_code=p.returncode,sha256=sha(AREA/name)))
  if p.returncode:raise RuntimeError(f'{name}:exit{p.returncode}, retainedlog')
  return(AREA/name).read_text()
 run(['docker','exec','gamebub-cu66-v69-build','verilator','--cc','--exe','--build','-j','1','--Wall','-Wno-PINCONNECTEMPTY','--top-module','cu78_receiver','--Mdir','/build/v78-receiver','-CFLAGS','-O2 -std=c++17','-I'+str(ROOT/'fpga/experiments/cu66-v69/inverse'),'-I'+str(ROOT/'fpga/experiments/cu66-v69/packet'),*[str(ROOT/p)for p in rel],str(AREA/'tb_receiver.cpp')],'build.log',1200)
 log=run(['docker','exec','gamebub-cu66-v69-build','/build/v78-receiver/Vcu78_receiver',str(NATIVE/'index.tsv'),str(a.seed),str(a.per_chain)],f'run-{a.seed}.log',3600)
 assert re.search(r'^PASS actual_frames=\d+ fault_and_control_modes=7',log,re.M)and'FAIL'not in log
 rows=[{k:int(v)for k,v in re.findall(r'(\w+)=(\d+)',l)}for l in log.splitlines()if l.startswith('FRAME_PASS')]
 cohorts={}
 for l in(NATIVE/'index.tsv').read_text().splitlines():cohorts[l.split('\t')[0]]=cohorts.get(l.split('\t')[0],0)+1
 expected=sum(min(a.per_chain,n)for n in cohorts.values());assert len(rows)==expected+24
 assert all(r['tiles']==8100 and r['error']==0 and r['validated_checks']>0 for r in rows[:expected])
 for mode in range(1,9):assert len([r for r in rows if r['mode']==mode])==1
 assert next(r for r in rows if r['mode']==6)['display_guard_checks']==14
 assert next(r for r in rows if r['mode']==7)['commits']>=2
 assert next(r for r in rows if r['mode']==5)['stale']>=4
 assert next(r for r in rows if r['mode']==8)['pending_lease_checks']==37
 assert pins=={p:sha(ROOT/p)for p in pins},'inputs changed'
 d=dict(schema='cu78-receiver-regression-v1',status='PASS_ACTUAL_PACKET_BASE_DIRECT_OWNER',source_sha256=pins,commands=commands,seed=a.seed,actual_corpus_frames=expected,frame_cases=rows,scope='Actual RTL parser/qmap/base/hash/three-bank owner with stored RTL-output references and native semantic HUD endpoint; transactional RAM and controlled presentation ACK endpoint',limitations=['Not actual SDRAM controller or display/CDC test','Endpoint software HUD execution is not FPGA timing','No physical30fps/targetunder10ms/fit/Fmax/route proof','Controlled presentation endpoint is not the continuous direct scanout implementation'])
 (AREA/'results.json').write_text(json.dumps(d,indent=2)+'\n');print('V78_RECEIVER_EVIDENCE_PASS corpus='+str(expected)+' fault_control_modes=7 pending_lease_control=1')
if __name__=='__main__':main()
