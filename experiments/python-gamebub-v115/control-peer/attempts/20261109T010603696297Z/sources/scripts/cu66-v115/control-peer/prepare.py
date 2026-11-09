#!/usr/bin/env python3
"""Derive additive V115 real-parent pending abort/reset checks; no shared oracle edits."""
from pathlib import Path
import hashlib,json,shutil
R=Path(__file__).resolve().parents[3];S=R/'fpga/experiments/cu66-v115-control-peer';OLD=R/'fpga/experiments/cu66-v114-control-peer'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def main():
 S.mkdir(parents=True,exist_ok=True)
 old=OLD/'tb_peer.cpp';assert sha(old)=='8ba00ccca185a6cae7ce265b55a05d4f40686f3e0269bac76c400ce68507cc2b';text=old.read_text();edits=[]
 def edit(before,after):
  nonlocal text
  assert text.count(before)==1,(before[:100],text.count(before));text=text.replace(before,after,1);edits.append(dict(before=before,after=after))
 edit('#define P(n) b.d.rootp->cs88_pipeline_v91k__DOT__##n',r'''#define P(n) b.d.rootp->cs88_pipeline_v91k__DOT__##n
#define S(n) b.d.rootp->cs88_pipeline_v91k__DOT__coefficients__DOT__child__DOT__scratch__DOT__##n
#define C(n) b.d.rootp->cs88_pipeline_v91k__DOT__coefficients__DOT__child__DOT__##n''')
 edit('unsigned checks=0,retries=0,accepted_writes=0,accepted_reads=0,replay_checks=0,local_cancel_edges=0;', 'unsigned checks=0,retries=0,accepted_writes=0,accepted_reads=0,replay_checks=0,local_cancel_edges=0,parent_checks=0,parent_retries=0,parent_stage_mask=0,parent_aborts=0,parent_resets=0,original_local_cancel_edges=0;')
 edit(''' auto retry=[&](){b.hold_response=false;b.hold_reference_response=false;b.d.start=0;b.settle();need(!b.pending&&!b.reference_pending&&!b.d.ref_pending&&b.d.start_ready,"peer drain did not return reservation");start(0);b.feed_until();b.finish(*good);b.settle();++retries;};''',''' auto canonical_retry=[&](){b.hold_response=false;b.hold_reference_response=false;b.d.start=0;b.settle();need(!b.pending&&!b.reference_pending&&!b.d.ref_pending&&b.d.start_ready,"peer drain did not return reservation");start(0);b.record=true;b.feed_until();b.finish(*good);b.settle();};
 auto retry=[&](){canonical_retry();++retries;};''')
 marker=' std::cout<<"{\\"type\\":\\"peer_verdict\\"'
 at=text.index(marker)
 added=r''' original_local_cancel_edges=local_cancel_edges;need(original_local_cancel_edges==8,"original peer cancel-edge count changed");
 // Actual top-level reset/abort drives the unchanged real parent's store_abort
 // and abort_epoch(store_epoch) wiring. No child tag or owner is assigned here.
 for(bool reset:{false,true})for(unsigned stage=0;stage<3;++stage){
  start(0);size_t at=0;bool offered=false;
  auto input_tick=[&](){
   if(!offered&&at<good->packet.size())offered=true;
   b.d.in_valid=offered;b.d.in_data=at<good->packet.size()?good->packet[at]:0;b.d.in_last=at+1==good->packet.size();
   b.d.clk=0;b.d.eval();const bool take=b.d.in_valid&&b.d.in_ready;b.tick();if(take){++at;offered=false;}
  };
  for(unsigned k=0;!(S(state)==30&&!S(prepare_mature));++k){need(k<3000000,"real parent scratch reservation watchdog");need(!b.d.error&&!b.d.done,"frame terminated before scratch reservation");input_tick();}
  const auto reserved=S(queued_epoch),last=S(last_epoch);const bool seen=S(epoch_seen);const auto requests=b.requests,acks=b.acks,reference_requests=b.observed_ref_requests,reference_acks=b.observed_ref_acks;
  need(S(active_epoch)==reserved&&C(store_epoch)==reserved,"real parent does not see reserved scratch tag");
  for(unsigned n=0;n<stage;++n)input_tick();
  need(S(state)==(stage==2?31U:30U)&&bool(S(prepare_mature))==(stage!=0),"requested real scratch preparation edge absent");
  need(S(last_epoch)==last&&bool(S(epoch_seen))==seen,"uncommitted scratch reservation advanced anti-replay epoch");
  need(!b.pending&&!b.reference_pending&&!b.d.dbg_scratch_outstanding&&!b.d.ref_pending&&!b.d.mem_req_valid&&!b.d.ref_req_valid&&!b.d.out_valid,"pending scratch reservation acquired physical/output owner");
  if(reset)b.d.reset=1;else b.d.abort_packet=1;b.d.in_valid=b.d.in_last=0;b.d.eval();
  need(S(cancel),"actual parent abort/reset did not cancel reserved scratch owner");
  if(!reset)need(C(store_abort)&&C(store_epoch)==reserved,"actual parent store_abort/tag wiring differs");
  masked(b);b.tick();b.d.reset=b.d.abort_packet=0;
  need(S(state)==0&&!S(prepare_mature)&&S(last_epoch)==last&&bool(S(epoch_seen))==seen,"reserved owner survived or advanced on public kill");
  b.settle();need(!b.pending&&!b.reference_pending&&!b.d.dbg_scratch_outstanding&&!b.d.ref_pending&&b.d.start_ready,"public pending kill did not quiesce");
  need(b.requests==requests&&b.acks==acks&&b.observed_ref_requests==reference_requests&&b.observed_ref_acks==reference_acks,"pending kill created or retired hidden physical request");
  ++parent_checks;parent_stage_mask|=1U<<stage;if(reset)++parent_resets;else ++parent_aborts;
  std::cout<<"{\"type\":\"parent_pending_case\",\"status\":\"PASS\",\"reset\":"<<reset<<",\"stage\":"<<stage<<",\"reserved_epoch\":"<<reserved<<",\"last_admitted_epoch\":"<<last<<",\"parent_abort_tag_read_only\":true}\n";
  canonical_retry();++parent_retries;
 }
 need(checks==8&&retries==8&&parent_checks==6&&parent_retries==6&&parent_stage_mask==7&&parent_aborts==3&&parent_resets==3,"peer/public-parent campaign coverage incomplete");
'''
 edit(text[at:at+len(marker)],added+marker)
 edit(r'local_cancel_edges\":"<<local_cancel_edges<<",\"clock_edges\":',r'local_cancel_edges\":"<<original_local_cancel_edges<<",\"all_local_cancel_edges\":"<<local_cancel_edges<<",\"parent_private_cancel_edges\":"<<(local_cancel_edges-original_local_cancel_edges)<<",\"parent_pending_cancel_cases\":"<<parent_checks<<",\"parent_canonical_retries\":"<<parent_retries<<",\"total_canonical_retries\":"<<(retries+parent_retries)<<",\"parent_stage_mask\":"<<parent_stage_mask<<",\"parent_abort_cases\":"<<parent_aborts<<",\"parent_reset_cases\":"<<parent_resets<<",\"canonical_case_id\":\""<<good->id<<"\",\"clock_edges\":')
 edit('IV114_CONTROL_PEER_FAIL','IV115_CONTROL_PEER_FAIL')
 p=S/'tb_peer.cpp'
 if p.exists():assert p.read_text()==text,'Refuse silent candidate bench overwrite'
 else:p.write_text(text)
 back=text
 for e in reversed(edits):assert back.count(e['after'])==1;back=back.replace(e['after'],e['before'],1)
 assert back==old.read_text()
 base=OLD/'bench_peer_base.hpp';derived=S/'bench_peer_base.hpp';shutil.copyfile(base,derived);assert sha(base)==sha(derived)=='e56c4eb4a7a479c123baae06a7ad137b7c90e637735ccb6890c62f2df87c59dc'
 d=dict(schema='v115-additive-real-parent-peer-cancel-derivation-v1',original=str(old.relative_to(R)),original_sha256=sha(old),derived=str(p.relative_to(R)),derived_sha256=sha(p),edits=edits,reverse_verified=True,original_peer_case_assertions_retained=True,canonical_recording_enabled_for_complete_retries=True,shared_API_oracle_changed=False,private_cancel_header=dict(original=str(base.relative_to(R)),original_sha256=sha(base),copy=str(derived.relative_to(R)),copy_sha256=sha(derived),inherited_derivation=str((OLD/'derivation.json').relative_to(R)),inherited_derivation_sha256=sha(OLD/'derivation.json')))
 write(S/'derivation.json',d)
 old_contract=json.loads((OLD/'fault-injection-contract.json').read_text());old_body=old.read_text()[old.read_text().index('static void inject('):old.read_text().index('static void masked(')];body=text[text.index('static void inject('):text.index('static void masked(')];assert body==old_body
 old_contract.update(schema='v115-inherited-complete-actual-fail-task-poststates-v1',cpp=str(p.relative_to(R)),cpp_sha256=sha(p),injection_body_sha256=hashlib.sha256(body.encode()).hexdigest(),inherited_contract=dict(path=str((OLD/'fault-injection-contract.json').relative_to(R)),sha256=sha(OLD/'fault-injection-contract.json')))
 write(S/'fault-injection-contract.json',old_contract)
 print('V115_PEER_ADDITIVE_PREPARED',sha(p))
if __name__=='__main__':main()
