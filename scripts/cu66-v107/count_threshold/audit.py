#!/usr/bin/env python3
"""Read-only independent receipt/recipe and delayed-capture CSV replay."""
import csv,gzip,hashlib,json
from collections import deque
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];AREA=ROOT/'experiments/python-gamebub-v107/count-threshold';SRC=ROOT/'fpga/experiments/cu66-v107-count-threshold';MASK=(1<<32)-1

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 selected=json.loads((AREA/'results.json').read_text());assert selected['status']=='PASS' and selected['actual_RTL_run'];receipt=ROOT/selected['selected_report'];assert sha(receipt)==selected['selected_report_sha256'];r=json.loads(receipt.read_text());out=receipt.parent
 for rel,h in r['source_sha256'].items():assert sha(ROOT/rel)==h,rel
 for rel,h in r['artifacts_sha256'].items():assert sha(out/rel)==h,rel
 recipe=json.loads((SRC/'edit-recipe.json').read_text())
 for name,e in recipe['production'].items():
  original=ROOT/e['original'];s=original.read_text();assert sha(original)==e['original_sha256'] and sha(SRC/name)==e['candidate_sha256']
  for edit in e['edits']:assert s.count(edit['before'])==1;s=s.replace(edit['before'],edit['after'],1)
  assert s==(SRC/name).read_text()
  for edit in reversed(e['edits']):assert s.count(edit['after'])==1;s=s.replace(edit['after'],edit['before'],1)
  assert s==original.read_text()
 s=(SRC/'br88_packet_ingress_sync_v91h.sv').read_text();i=s.index('    // COUNT_THRESHOLD_PIPELINE_BEGIN');block=s[i:s.index('    // COUNT_THRESHOLD_PIPELINE_END',i)+len('    // COUNT_THRESHOLD_PIPELINE_END')]
 assert block in (SRC/'verification/threshold_math_probe.sv').read_text()
 adapters=json.loads((SRC/'verification/adapters.json').read_text())
 for e in adapters['adapters']:
  s=(ROOT/e['source']).read_text()
  for before,after in e['renames']:assert s.count(before)==1;s=s.replace(before,after,1)
  assert s==(ROOT/e['path']).read_text()
 replay=[]
 for seed in (109101,109102):
  a=[0,0,0];p12=p123=0;cache=[0,0,0];live=0;pending=[deque() for _ in a];commits=flush_commits=rows=0
  with gzip.open(out/f'capture-{seed}.csv.gz','rt') as f:
   for row in csv.reader(f):
    x=list(map(int,row));assert len(x)==17;edge,cap,index,n=x[:4];assert edge==rows
    np12=(a[0]+a[1])&MASK;np123=(p12+a[2])&MASK
    if cap and index>=0:a[index]=(n*4+15)&0xfffffff0
    flush=bool(x[16])
    for g,d in enumerate((5,15,43)):
     due=bool(pending[g] and pending[g][0][0]==edge)
     if due:
      _,owner=pending[g].popleft();cache[g]=owner//d+int(owner%d!=0);commits+=1;flush_commits+=flush
     if flush:pending[g].clear();live&=~(1<<g)
     elif due:live|=1<<g
     if cap and index==g and not flush:pending[g].append((edge+8,n))
     assert len(pending[g])<=8
    p12,p123=np12,np123
    assert x[4:9]==a+[p12,p123],(seed,edge,'prefix')
    assert x[12:16]==cache+[live],(seed,edge,'threshold')
    if x[9]:assert live==7
    rows+=1
  verdict=next(v for v in r['capture_runs'] if v['seed']==seed);assert rows==verdict['edges'] and commits==verdict['threshold_commits'] and flush_commits==verdict['threshold_flush_commits']
  replay.append(dict(seed=seed,rows=rows,commits=commits,flush_commit_collisions=flush_commits))
 for n in r['negative_owner_contract_rejections']:
  log=(out/n['log']).read_text();assert 'stale staging response' in log and 'EXPECTED_ASSERTION_ARMED' in log and '"capture_enable":false' in log
 for command in r['commands']:
  if 'verilator' in command['argv'] and '--build' in command['argv']:
   assert '-Wall' in command['argv'] and '--assert' in command['argv'];assert not any(x.startswith('-Wno-') for x in command['argv'])
  if command['exit_code']!=0:assert command.get('status')=='PASS_EXPECTED_ORIGINAL_ASSERTION_CONTRACT_REJECTION'
 build=Path('/home/lori/gamebub-build/cu66-v69')/('v107-threshold-'+out.name)
 binary={str(p.relative_to(build)):dict(sha256=sha(p),bytes=p.stat().st_size) for p in [build/'math-obj/Vthreshold_math_probe',build/'capture-obj/Vingress_capture_probe',build/'pair-1/Vprefix_probe',build/'pair-0/Vprefix_probe']}
 result=dict(status='PASS',actual_RTL_run=True,receipt=str(receipt.relative_to(ROOT)),receipt_sha256=sha(receipt),auditor_sha256=sha(Path(__file__).resolve()),source_hashes_checked=len(r['source_sha256']),artifact_hashes_checked=len(r['artifacts_sha256']),four_complete_reversible_sources=True,lossless_adapters=len(adapters['adapters']),exact_production_math_block=True,capture_trace_replay=replay,postrun_binary_hashes=binary,scope='Offline audit of actual selected unit proof; no new RTL execution, model/preparation count, parent timing or four-state claim.')
 (AREA/'audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
