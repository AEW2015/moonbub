#!/usr/bin/env python3
"""Offline independent replay of all mode events, complete final store and adapters."""
import gzip,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
AREA=ROOT/'experiments/python-gamebub-v105/memory'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def hidden(p,t):
 if p:return 1046<=t<=1064
 return any(lo<=t<=hi for lo,hi in ((633,651),(723,741),(993,1011),(1083,1101),(4071,4110),(4161,4200),(4251,4290),(4431,4460),(4521,4550)))
def main():
 selection=json.loads((AREA/'probe-results.json').read_text());receipt=ROOT/selection['selected_receipt'];r=json.loads(receipt.read_text());assert sha(receipt)==selection['sha256'];assert r['status']=='PASS_ACTUAL_CLOCKED_MODE_EQUIVALENCE'
 out={'schema':'v105-mode-independent-trace-audit-v1','status':'FAIL','receipt':str(receipt.relative_to(ROOT)),'receipt_sha256':sha(receipt),'runs':[],'checks':[],'auditor':{'path':str(Path(__file__).resolve().relative_to(ROOT)),'sha256':sha(Path(__file__))}}
 for field,module,artifact in [('original','mode_original','mode_original.sv'),('candidate','mode_candidate','mode_candidate.sv')]:
  src=ROOT/r[field]['path'];adapter=receipt.parent/artifact
  assert sha(src)==r[field]['sha256'];assert adapter.read_text().replace('module '+module+' (','module cs88_admission_v91i2a (',1)==src.read_text()
  out['checks'].append({'name':field+' full production body after reversing module rename','status':'PASS','sha256':sha(src)})
 recipe=ROOT/'fpga/experiments/cu66-v105-memory/edit-proof.json';proof=json.loads(recipe.read_text());s=(ROOT/proof['original_path']).read_text()
 for edit in proof['edits']:assert s.count(edit['before'])==edit['expected_occurrences'];s=s.replace(edit['before'],edit['after'])
 assert s==(ROOT/proof['candidate_path']).read_text();out['checks'].append({'name':'exact seven-edit production recipe','status':'PASS','path':str(recipe.relative_to(ROOT)),'sha256':sha(recipe)})
 before=(ROOT/proof['original_path']).read_text();after=(ROOT/proof['candidate_path']).read_text()
 assert re.findall(r'tile<=.*?;',before)==re.findall(r'tile<=.*?;',after)
 assert before.split('task automatic residual_tile;',1)[1].split('endtask',1)[0]==after.split('task automatic residual_tile;',1)[1].split('endtask',1)[0]
 assert 'logic [1:0] modes [0:8099];' in after
 out['checks'].append({'name':'all tile assignments, residual task and 8100x2 declaration preserved','status':'PASS'})
 for run in r['runs']:
  seed=run['seed'];p=receipt.parent/f'seed-{seed}.jsonl.gz';assert sha(p)==r['artifacts_sha256'][p.name]
  memory=[((i*131+(i>>3))^seed)&3 for i in range(8100)];held=3;cases=0;reads=0;writes=0;guards=0;finals=0;branches=[0]*5;read_addresses=set();write_addresses=[set() for _ in range(5)]
  with gzip.open(p,'rt') as f:
   for line in f:
    e=json.loads(line)
    if 'final_addr' in e:assert e['final_addr']==finals and e['value']==memory[finals];finals+=1;continue
    assert e['case']==cases and e['equal'];assert 0<=e['addr']<8100
    state,plane,t=e['state'],e['plane'],e['tile'];branch=-1;addr=data=0;base=(0,5400,6750)[plane]
    if not e['guard']:
     if state==31 and e['index']!=8100:branch=0;addr=e['index']&8191;data=1
     elif state==6 and t!=(5400 if plane==0 else 1350):branch=1;addr=(base+t)&8191;data=1 if hidden(plane,t) else 2
     elif state==8 and e['bits'] and e['mixed']:branch=2;addr=(base+t)&8191;data=2 if e['bit'] else 0
     elif state==10 and t!=e['end']:
      if hidden(plane,t) or e['tag']==0:branch=3;addr=(base+t)&8191;data=1 if hidden(plane,t) else 0
      elif e['tag']==1:branch=4;addr=(base+t)&8191;data=2
    read=bool(e['lookup'] and state==26 and not e['guard'])
    assert (e['branch'],e['write_addr'],e['write_data'],bool(e['read']))==(branch,addr,data,read)
    assert not(read and branch>=0)
    if read:held=memory[e['addr']];reads+=1;read_addresses.add(e['addr'])
    if branch>=0:assert addr<8100;memory[addr]=data;writes+=1;branches[branch]+=1;write_addresses[branch].add(addr)
    assert held==e['held'];cases+=1;guards+=bool(e['guard'])
  assert cases==run['cases'] and reads==run['reads'] and writes==run['writes'] and guards==run['guarded_cases'] and branches==run['write_branches'];assert finals==8100 and len(read_addresses)==8100
  assert all(len(write_addresses[i])==8100 for i in [0,1,2,3]);assert len(write_addresses[4])==sum(not hidden(p,t) for p in range(3) for t in range(5400 if p==0 else 1350))
  out['runs'].append({'seed':seed,'events':cases,'read_events':reads,'write_events':writes,'write_branches':branches,'unique_write_addresses_per_branch':list(map(len,write_addresses)),'all_valid_read_addresses':len(read_addresses),'final_store_entries':finals,'trace_sha256':sha(p),'status':'PASS'})
 out['status']='PASS_INDEPENDENT_MODE_REPLAY';(AREA/'trace-audit.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
