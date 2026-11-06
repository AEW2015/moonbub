#!/usr/bin/env python3
"""Independent packed-value mutations and delayed-write drain contract."""
import copy,gzip,hashlib,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];AREA=Path(__file__).resolve().parent

def load(path):
 s=importlib.util.spec_from_file_location('trace_under_test',path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
 trace=load(AREA/'trace.py');report=json.loads((AREA/'results.json').read_text());checks=[]
 for item in report['selected_traces']:
  path=ROOT/item['path']
  with gzip.open(path,'rt') as f:snapshot=json.load(f)
  def initial():
   banks=[bytearray(b'\xff'*2048)for _ in range(3)]
   for mapid,mapping in zip(snapshot['map_roles'][:2],(snapshot['previous'],snapshot['presented'])):
    if mapping is None:continue
    for tile,slot in enumerate(mapping):
     at=tile//4;shift=(tile%4)*2;banks[mapid][at]=(banks[mapid][at]&~(3<<shift))|(slot<<shift)
   return banks
  trace.validate_descriptors(snapshot['events'],initial())
  checks.append(dict(name='selected_packed_descriptor_value_replay',cohort=item['cohort'],fid=item['fid'],status='PASS'))
  for kind in ('descriptor_candidate','descriptor_scanout'):
   mutated=copy.deepcopy(snapshot['events']);entry=next(e for e in mutated if e['kind']==kind);entry['value']=(entry['value']+1)%3
   try:trace.validate_descriptors(mutated,initial())
   except AssertionError:pass
   else:raise AssertionError('descriptor mutation escaped '+kind)
   checks.append(dict(name='reject_'+kind+'_value_mutation',cohort=item['cohort'],fid=item['fid'],status='PASS'))
 # Minimal asynchronous bus oracle: accepted slot0 and scanout slot1 are pinned.
 # A provisional slot2 cannot be leased again until every issued write drains.
 physical=[b'A',b'D',None];accepted=0;presented=1;pending=[(2,b'B')];phase='draining'
 def begin():
  if phase=='draining' or pending:raise ValueError('issued writes must drain')
 try:begin()
 except ValueError:pass
 else:raise AssertionError('undrained slot reuse allowed')
 checks.append(dict(name='abort_blocks_next_epoch_until_write_drain',status='PASS'))
 slot,value=pending.pop(0);assert slot not in (accepted,presented);physical[slot]=value
 assert physical[accepted]==b'A' and physical[presented]==b'D'
 phase='idle';begin();physical[2]=b'C';accepted=2
 assert physical[accepted]==b'C' and physical[presented]==b'D'
 checks.append(dict(name='drain_preserves_live_leases_and_unblocks_new_publication',status='PASS'))
 # Show why merely throwing away an old response tag is insufficient: the bus
 # write itself can already have modified a slot reused by a new generation.
 naive=[b'A',b'D',b'C'];naive[2]=b'B';assert naive[2]!=b'C'
 checks.append(dict(name='counterexample_late_old_write_corrupts_early_reused_slot',status='PASS_COUNTEREXAMPLE'))
 output=dict(schema='cu66-v88-alias-value-drain-tests-v1',status='PASS_PACKED_VALUES_AND_DRAIN_CONTRACT',checks=checks,checks_count=len(checks),
             source_sha256={str(p.relative_to(ROOT)):sha(p)for p in (Path(__file__).resolve(),AREA/'trace.py',AREA/'results.json')},
             scope='Actual selected descriptor-byte replays plus a minimal delayed-write lease oracle; no asynchronous RTL/bus-controller implementation.')
 (AREA/'tests.json').write_text(json.dumps(output,indent=2)+'\n');print(output['status'],len(checks))

if __name__=='__main__':main()
