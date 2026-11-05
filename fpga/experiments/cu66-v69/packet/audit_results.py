#!/usr/bin/env python3
"""Recheck retained packet fixtures, source pins and terminal seeded verdicts."""
from pathlib import Path
import hashlib,importlib.util,json,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
s=importlib.util.spec_from_file_location('packet69_explicit_oracle',HERE/'export_fixtures.py');e=importlib.util.module_from_spec(s);sys.modules[s.name]=e;s.loader.exec_module(e)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 manifest=json.loads((HERE/'manifest.json').read_text());q=json.loads((HERE/'results.json').read_text())
 for name,digest in q['source_sha256'].items():assert sha(HERE/name)==digest,name
 for name,digest in manifest['source_sha256'].items():assert sha(ROOT/name)==digest,name
 counts={0:0,1:0,2:0}
 for c in manifest['cases']:
  packet=(HERE/c['packet']['path']).read_bytes();assert len(packet)==c['packet']['bytes']and hashlib.sha256(packet).hexdigest()==c['packet']['sha256'];accepted=True
  try:meta=e.oracle(packet,c['cfg'])
  except(ValueError,IndexError,e.struct.error):accepted=False
  assert accepted==(c['mode']!=0);counts[c['mode']]+=1
  if accepted:
   assert meta.pop('qmap')==(HERE/c['expected']['qmap']['path']).read_bytes();assert meta=={k:v for k,v in c['expected'].items()if k!='qmap'}
 assert counts=={0:23,1:457,2:5}
 log=(HERE/'regression.log').read_text();assert 'TEST_FAIL'not in log
 actual=[json.loads(line.split('TEST_PASS ',1)[1])for line in log.splitlines()if line.startswith('TEST_PASS ')];assert len(actual)==2
 for run in actual:
  assert run['seed']in(6910,6911)and run['valid_frames']==457 and run['structural_rejections']==23 and run['semantic_deferred_and_aborted']==5 and run['qmap_values_checked']==625050 and run['RAM_reads']==8161002 and run['request_stalls']>0 and run['delayed_response_cycles']>0 and run['abort_tests']==3 and not run['physical_timing_proven']
 assert actual==q['runs'];print(json.dumps(dict(seeds=[x['seed']for x in actual],full_valid_fixture_frames=457,structural_rejections=23,semantic_deferred_not_committed=5,qmap_values_checked=sum(x['qmap_values_checked']for x in actual),source_pins=len(q['source_sha256']),stateless_accepted_history=True,canonical_or_HUD_semantic_decoder=False,physical_timing_proven=False)))
if __name__=='__main__':main()
