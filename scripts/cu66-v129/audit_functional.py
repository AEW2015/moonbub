#!/usr/bin/env python3
"""Independent V129 evidence audit against immutable V128 raw execution artifacts."""
import argparse,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent/'integration'))
from contract import BASELINE,AREA,composition,contract_candidates,legacy,load,pin,sha,verify

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--integration',type=Path,default=AREA/'integration/results.json');ap.add_argument('--output',type=Path,default=AREA/'audit/full-independent.json');a=ap.parse_args();verify();c=composition();idx=load(a.integration);base=load(BASELINE);m=legacy()
 assert idx['schema']=='v129-functional-composition-v1' and idx['status']=='PASS_V129_FULL_FUNCTIONAL'
 assert idx['all_original_oracles_retained'] and idx['exact_B_public_cycles'] and not idx['assertions_disabled_or_downgraded'] and idx['declared_public_cycle_delta']==0
 assert set(idx['stages'])=={'focused','spatial','peer','parent'} and idx['source_origins']==c['complete_source_origins'] and len(idx['source_origins'])==18
 remap={base['source_origins'][k]['path']:v['path'] for k,v in c['source_origins'].items()};assert idx['rtl_source_order']==[remap.get(p,p) for p in base['rtl_source_order']]
 raws={};closures={}
 for name,meta in idx['stages'].items():
  _,p,r=m.resolve_stage(meta);counts=m.verify_closure(p,r,name);closures[name]=dict(sources=counts[0],artifacts=counts[1]);raws[name]=(p,r)
  if name!='focused':
   assert r['source_origins']==idx['source_origins'];_,bp,br=m.resolve_stage(base['stages'][name]);assert r['rtl_source_order']==[remap.get(p,p) for p in br['rtl_source_order']]
  else:
   assert r['schema']=='v129-focused-aggregate-v1' and not r['aggregate_is_single_whole_composition_binary']
   assert set(r['focused_components'])=={'inherited_v128','parser','scratch'}
   for name2,meta2 in r['focused_components'].items():
    s=ROOT/meta2['selector']['path'];p2=ROOT/meta2['receipt']['path'];assert pin(s)==meta2['selector'] and pin(p2)==meta2['receipt'];sdata=load(s);raw=load(p2)
    assert sdata['status']==raw['status']=='PASS' and raw['actual_RTL_run'] is True and sdata.get('path',sdata.get('selected_report'))==meta2['receipt']['path'] and sdata.get('sha256',sdata.get('selected_report_sha256'))==meta2['receipt']['sha256']
    m.verify_closure(p2,raw,name2)
   for candidate in contract_candidates():assert r['source_sha256'][candidate]==sha(ROOT/candidate)
 checks={}
 for name,fn in [('spatial',m.compare_spatial),('peer',m.compare_peer),('parent',m.compare_parent)]:
  p,r=raws[name];_,bp,br=m.resolve_stage(base['stages'][name]);checks[name]=fn(p,r,bp,br)
 assert {k:len(v) for k,v in checks.items()}==dict(spatial=4,peer=2,parent=4)
 qualified=load(ROOT/'experiments/python-gamebub-v120/handoff.json');assert len(qualified['source_origins'])==18
 for meta in qualified['source_origins'].values():assert sha(ROOT/meta['path'])==meta['sha256']
 result=dict(schema='v129-independent-full-functional-audit-v1',status='PASS_INDEPENDENT_V129_FULL_FUNCTIONAL_AUDIT',integration_index_sha256=sha(a.integration),integration=pin(a.integration),source_B_count=18,source_B_hashes_match_handoff=True,v129_changed_aliases=sorted(c['source_origins']),source_origins=c['complete_source_origins'],source_count=18,source_artifact_closure=closures,exact_comparisons=dict(spatial_stdout_event_and_canonical_streams=4,peer_stdout_event_and_canonical_streams=2,parent_stdout_and_terminal_stream_sets=4),raw_comparison_evidence=checks,baseline_index=pin(BASELINE),all_original_oracles_retained=True,assertions_disabled_or_downgraded=False,declared_public_cycle_delta=0,hardware_contact=False)
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(result['status'],sha(a.output))
if __name__=='__main__':main()
