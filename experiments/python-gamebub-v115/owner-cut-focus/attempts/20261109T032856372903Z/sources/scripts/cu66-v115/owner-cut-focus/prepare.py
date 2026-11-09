#!/usr/bin/env python3
"""Reversibly package old control cases; never emit a production candidate."""
import hashlib,json,pathlib,sys
sys.dont_write_bytecode=True
R=pathlib.Path(__file__).resolve().parents[3];S=R/'fpga/experiments/cu66-v115-owner-cut-focus';A=R/'experiments/python-gamebub-v115/owner-cut-focus'
SUMMARY=R/'experiments/python-gamebub-v115/refined/spatial/results.json';SELECTED=R/'experiments/python-gamebub-v115/refined/spatial/attempts/20261109T021900879958Z/receipt.json'
SUMMARY_SHA='0d6afa8665e0b806aeb19152a952c689a08dc969414f6798e65a092ad3ecd075';SELECTED_SHA='5dfad8ef50f71ed3605712ef84a91eadb57892e6ffb4ee6b2e7186c88bb37ea5'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
OVERRIDES=[
 ('fpga/experiments/cu66-v115-owner/cs88_pipeline_v91k.sv','4ffe09eb94a4823b7870ab8421c7a0dc5f64758c3dbbd1acb8684c761df26a24','6c5c4bfe3f23801c6910fe117831a2da0f2e7546ad5cded1baf40681e2b0d926'),
 ('fpga/experiments/cu66-v115-final-ingress/br88_packet_ingress_sync_v91h.sv','e5ca00d03ca91050295da961e5793e7fd96bd183d83e668fbcd7a21b1784a2d6','c47f388093ec3fd59aacf95b4cab50735195bbd56cea17a756523b8caba0ea01')]
def prepare():
 assert sha(SUMMARY)==SUMMARY_SHA and sha(SELECTED)==SELECTED_SHA
 selected=json.loads(SUMMARY.read_text());base=json.loads(SELECTED.read_text());assert selected['selected_receipt']==str(SELECTED.relative_to(R)) and selected['status']==base['status']=='PASS_V115_REFINED_SPATIAL_CANONICAL' and base['actual_RTL_run']
 assert len(base['rtl_source_order'])==len(base['source_origins'])==18
 for origin in base['source_origins'].values():assert sha(R/origin['path'])==origin['sha256']
 old=R/'fpga/experiments/cu66-v114-control/tb_control.cpp';assert sha(old)=='2390c119c986b424820a081833481e6dd5812cfa0afbff7a43f70234409b68c8'
 text=old.read_text();before='int main(int argc,char**argv){try{';after='int immutable_control_main(int argc,char**argv){try{';assert text.count(before)==1;derived=text.replace(before,after,1);(S/'immutable_control.hpp').write_text(derived);assert derived.replace(after,before,1)==text
 peer=R/'fpga/experiments/cu66-v115-control-peer/tb_peer.cpp';peer_text=peer.read_text();reference=peer_text[peer_text.index('static void inject('):peer_text.index('static void masked(')]
 own=(S/'tb_owner.cpp').read_text();injected=own[own.index('static void inject('):own.index('static void masked_certificate(')]
 assert injected.rstrip()==reference.replace('static void inject(Bench&b,unsigned peer)','static void inject(ControlBench&b,unsigned peer)',1).rstrip()
 recipe=dict(complete_fail_fixture=dict(original=str(peer.relative_to(R)),original_sha256=sha(peer),body_type_change_only='Bench to ControlBench; exact assignment/check body retained'),original=str(old.relative_to(R)),original_sha256=sha(old),derived=str((S/'immutable_control.hpp').relative_to(R)),derived_sha256=sha(S/'immutable_control.hpp'),edits=[dict(before=before,after=after)],old_check_bodies_modified=0,old_directed_checks=78,old_physical_drain_checks=4,scope='C++ entry name packaging only; old original source, main body, all assertions and exact bench.cpp dependency remain unchanged.')
 (S/'bench-derivation.json').write_text(json.dumps(recipe,indent=2,sort_keys=True)+'\n');A.mkdir(parents=True,exist_ok=True)
 overrides=[];order=list(base['rtl_source_order']);origins={k:dict(v) for k,v in base['source_origins'].items()}
 for path,expected,recipe_expected in OVERRIDES:
  candidate=R/path;rp=candidate.parent/'edit-recipe.json';assert sha(candidate)==expected and sha(rp)==recipe_expected
  edit=json.loads(rp.read_text());original=R/edit['original'];assert sha(original)==edit['original_sha256'] and edit['candidate']==path and edit['candidate_sha256']==expected
  reconstructed=original.read_text()
  for e in edit['edits']:
   assert reconstructed.count(e['before'])==e.get('occurrences',1)
   reconstructed=reconstructed.replace(e['before'],e['after'])
  assert reconstructed==candidate.read_text()
  assert order.count(edit['original'])==1;order[order.index(edit['original'])]=path
  matched=[k for k,v in origins.items() if v['path']==edit['original']];assert len(matched)==1
  origins[matched[0]]=dict(path=path,sha256=expected)
  overrides.append(dict(original=edit['original'],original_sha256=edit['original_sha256'],candidate=path,candidate_sha256=expected,recipe=str(rp.relative_to(R)),recipe_sha256=recipe_expected))
 assert len(order)==len(origins)==18
 manifest=dict(status='PREPARED_NOT_RUN_FINAL18_OWNER_AND_INGRESS',baseline=dict(summary=str(SUMMARY.relative_to(R)),summary_sha256=SUMMARY_SHA,receipt=str(SELECTED.relative_to(R)),receipt_sha256=SELECTED_SHA,rtl_source_order=base['rtl_source_order'],source_origins=base['source_origins']),rtl_source_order=order,source_origins=origins,production_overrides=overrides,adoption_gate='Actual refined routed owner cone confirmed; Root source-reviewed certificate. Focused runtime and final native timing qualification remain required.',production_emitted_by_this_script=False,required_signal='base_kill_authorized',old_control_recipe=recipe,run_authorization='Explicit Root heavy-job grant remains required; preparation launches no job.')
 (A/'preparation.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n');return manifest
if __name__=='__main__':print(prepare()['status'])
