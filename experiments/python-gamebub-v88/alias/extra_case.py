#!/usr/bin/env python3
"""Rebuild actual C0f3 to exercise old-resident nonCOPY store restoration."""
import datetime,gzip,hashlib,importlib.util,json,sys,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];AREA=Path(__file__).resolve().parent
def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'extra-case-attempts'/(stamp+'-'+uuid.uuid4().hex[:8]);out.mkdir(parents=True)
 modules={name:load('v88_extra_'+name,ROOT/path)for name,path in {
 'native':'experiments/python-gamebub-v82/native/data.py','layout':'experiments/python-gamebub-v87/alias/prototype.py',
 'tree':'scripts/cu66-v82/prototype_commitment.py','residency':'fpga/experiments/cu66-v81/residency/model.py',
 'workload':'experiments/python-gamebub-v83/workload.py','credits':'experiments/python-gamebub-v84/credits.py',
 'coupled':'experiments/python-gamebub-v87/coupled/model.py','context':'experiments/python-gamebub-v86/contexts/data.py',
 'runner':'scripts/cu66-v87/prototype_coupled.py','scheduler':'experiments/python-gamebub-v83/scheduler.py',
 'audit':'experiments/python-gamebub-v83/audit.py','trace':'experiments/python-gamebub-v88/alias/trace.py'}.items()}
 pins={str(Path(m.__file__).relative_to(ROOT)):sha(Path(m.__file__))for m in modules.values()};pins[str(Path(__file__).relative_to(ROOT))]=sha(Path(__file__))
 slots=modules['layout'].TileSlots();tree=modules['tree'].CommitmentTree(granularity=16);banks=modules['residency'].Residency(8100)
 for f in modules['native'].iter_frames():
  frame=dict(f,generation=f['ordinal']+1);plan=tree.plan(frame,frame['copy_ref_mask'])
  candidatebank=0 if banks.reference is None else(banks.reference+1)%3
  elided=[not frame['key'] and bool(frame['same_mask'][t]) and bool(banks.masks[t]&(1<<candidatebank))for t in range(8100)]
  previous=slots.accepted;presented=slots.presented;slots.begin(frame['tiles'],frame['copy_ref_mask'])
  candidate=list(slots.candidate)
  if frame['cohort']==0 and frame['fid']==3:break
  slots.commit(frame['fid'],modules['layout'].digest(frame['tiles']));slots.present()
  banks.begin(frame['fid'],frame['packet_sha256'],candidatebank,frame['key'],frame['tiles'],frame['same_mask']);banks.step();banks.commit(authenticated=True);banks.present();tree.commit(plan)
 assert sum(not frame['copy_ref_mask'][t] and elided[t]for t in range(8100))==294
 observation=next(o for o in modules['context'].iter_frames()if(o['cohort'],o['fid'],o['cap'])==(0,3,65536))
 packet=next(r for r in map(json.loads,(ROOT/'experiments/python-gamebub-v86/wire-attempts/20261106T135235884295Z-2a73a26a/frames.jsonl').read_text().splitlines())if(r['cohort'],r['fid'],r['configuration'])==(0,3,'copy_group_cap65536'))
 base=modules['workload'].build(frame,elided,plan,inverse_cycles=64,reconstruct_cycles=64,read_gap=18,write_gap=16,group_slots=4)
 credited=modules['credits'].augment(base,[0]*8100,ref_slots=8,inverse_slots=8,coefficient_slots=8)
 metadata=sum(packet['components'][k]for k in('header','mode_body','qmap','chunk_directory'))
 work=modules['coupled'].couple(credited,observation['shared_work'],observation['context_work'],modules['runner'].LOW,wire_bytes=packet['wire_bytes'],metadata_bytes=metadata,dequant_cycles=64)
 config=next(c for c in modules['runner'].CONFIGS if c['name']=='low_lanes2')
 caps=dict(memory=1,inverse=1,reconstruct=1,hash=1,tree_r=1,tree_w=1,map_r=1,map_w=1,fetch=1,arithmetic=2,emit=1,dequant=1)
 result=modules['scheduler'].schedule(work['jobs'],caps,None,retain_timeline=True)
 checked=modules['audit'].verify(work['jobs'],result['timeline'],caps,None,work['groups'],4)
 old=json.loads((ROOT/'experiments/python-gamebub-v87/coupled/verification.json').read_text())
 found=[]
 for n in old['artifact_sha256']:
  if n.endswith('/rows.jsonl')and'/attempts/'in n:
   found.extend(r for r in map(json.loads,(ROOT/n).read_text().splitlines())if(r['cohort'],r['fid'],r['configuration'])==(0,3,'low_lanes2'))
 assert len(found)==1 and found[0]['finish_cycles']==result['finish_cycles']
 witness=out/'witness-c0-f3-low_lanes2.json.gz'
 with gzip.open(witness,'wt')as stream:json.dump(dict(config=config,capacities=caps,workload=work,result=result,audit=checked),stream,separators=(',',':'))
 dirty={t for g in plan['recomputed_groups']for t in g['tile_indices']};trace=modules['trace']
 events=trace.commands(frame,previous,candidate,presented,dirty,map_roles=(0,0,1));accounts={p:trace.account(events,p)for p in('onchip','cached','uncached')}
 path=out/'c0-f3-trace.json.gz'
 with gzip.open(path,'wt')as stream:json.dump(dict(frame={k:frame[k]for k in('cohort','fid','key','canonical_sha256')},previous=previous,presented=presented,candidate=candidate,map_roles=(0,0,1),hidden=list(frame['hidden_mask']),copy=list(frame['copy_ref_mask']),dirty=sorted(dirty),old_elided=elided,events=events,accounts=accounts),stream,separators=(',',':'))
 assert pins=={n:sha(ROOT/n)for n in pins}
 report=dict(schema='cu66-v88-restored-store-case-v1',status='PASS_FROZEN_REBUILD_AND_ADDED_STORE_CASE',cohort=0,fid=3,added_nonCOPY_store_tiles=294,frozen_low2_finish_cycles=result['finish_cycles'],canonical_sha256=frame['canonical_sha256'],source_sha256=pins,original_witness=str(witness.relative_to(ROOT)),original_witness_sha256=sha(witness),trace=str(path.relative_to(ROOT)),trace_sha256=sha(path))
 (out/'results.json').write_text(json.dumps(report,indent=2)+'\n');(AREA/'extra-case.json').write_text(json.dumps(dict(report,selected_report=str((out/'results.json').relative_to(ROOT))),indent=2)+'\n');print(report['status'],result['finish_cycles'])
if __name__=='__main__':main()
