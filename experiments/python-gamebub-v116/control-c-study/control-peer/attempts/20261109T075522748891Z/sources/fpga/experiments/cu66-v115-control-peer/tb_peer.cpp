// Verification-only prepared peer fault states; every request, replay and retry
// uses the actual full component and the unchanged independent data/owner oracle.
#include "bench_peer_base.hpp"
#define P(n) b.d.rootp->cs88_pipeline_v91k__DOT__##n
#define S(n) b.d.rootp->cs88_pipeline_v91k__DOT__coefficients__DOT__child__DOT__scratch__DOT__##n
#define C(n) b.d.rootp->cs88_pipeline_v91k__DOT__coefficients__DOT__child__DOT__##n
static void inject(Bench&b,unsigned peer){
 // Prepare the COMPLETE actual fail(reason) task poststate, including every
 // logical flush effect. Physical reference/scratch ledgers are not assigned.
 if(peer==2){const bool was_fault=P(transform__DOT__fault_o);
  P(transform__DOT__error)=5;P(transform__DOT__fault_o)=1;P(transform__DOT__fault_pending_o)=!P(inverse_fault_ack)&&!was_fault;
  P(transform__DOT__running)=0;P(transform__DOT__done)=0;P(transform__DOT__bank_state)[0]=0;P(transform__DOT__bank_state)[1]=0;
  P(transform__DOT__fill_index)=0;P(transform__DOT__math_state)=0;P(transform__DOT__accept_state)=0;
  P(transform__DOT__result_state)[0]=0;P(transform__DOT__result_state)[1]=0;P(transform__DOT__emit_index)=0;
 }else{const bool was_fault=P(reconstruction__DOT__fault_o);
  P(reconstruction__DOT__error)=3;P(reconstruction__DOT__fault_o)=1;P(reconstruction__DOT__fault_pending_o)=!P(reconstruction_fault_ack)&&!was_fault;
  P(reconstruction__DOT__running)=0;P(reconstruction__DOT__done)=0;P(reconstruction__DOT__state)=0;P(reconstruction__DOT__discard_ref)=1;
 }
 b.d.eval();
 if(peer==2)need(!P(transform__DOT__running)&&!P(transform__DOT__done)&&!b.d.inverse_owned_banks&&!P(transform__DOT__fill_index)&&!P(transform__DOT__math_state)&&!P(transform__DOT__accept_state)&&!P(transform__DOT__result_state)[0]&&!P(transform__DOT__result_state)[1]&&!P(transform__DOT__emit_index),"prepared inverse fail task poststate differs");
 else need(!P(reconstruction__DOT__running)&&!P(reconstruction__DOT__done)&&!P(reconstruction__DOT__state)&&P(reconstruction__DOT__discard_ref),"prepared reconstruction fail task poststate differs");
}
static void masked(Bench&b){need(!b.d.in_ready&&!b.d.mem_req_valid&&!b.d.ref_req_valid&&!b.d.out_valid&&!b.d.coefficient_valid&&!b.d.coefficient_ready&&!b.d.residual_valid&&!b.d.residual_ready,"peer fault leaked public transfer eligibility");}
int main(int argc,char**argv){try{
 need(argc==7,"peer usage cases transforms canonical seed events canonical-output");
 auto cases=load(argv[1]);load_tiles(argv[2]);const Case*good=nullptr;for(const auto&c:cases)if(!c.error&&!c.dense[0].empty()&&!c.qvalid){good=&c;break;}need(good,"peer good fixture missing");
 Bench b(unsigned(std::stoul(argv[4])),argv[5],argv[3],argv[6]);unsigned checks=0,retries=0,accepted_writes=0,accepted_reads=0,replay_checks=0,local_cancel_edges=0,parent_checks=0,parent_retries=0,parent_stage_mask=0,parent_aborts=0,parent_resets=0,original_local_cancel_edges=0;bool local_cancel_scope=false;uint32_t expected_cancel_queued=0,expected_cancel_pending=0;
 b.before_edge=[&](){local_cancel_scope=!b.d.reset&&!b.d.abort_packet&&P(base_abort)&&P(base_kill_valid)&&P(base_kill_owner)==P(owner_sequence);
  if(local_cancel_scope){need(!b.d.queue_push&&!b.d.queue_pop&&!b.d.stage_write&&!b.d.frame_read_req,"private kill issued refill traffic");need(unsigned(b.d.queue_count)+unsigned(b.d.queue_pending)<=2,"private cancel owner bound");expected_cancel_queued=b.d.queue_cancel_queued+b.d.queue_count;expected_cancel_pending=b.d.queue_cancel_pending+b.d.queue_pending;masked(b);++local_cancel_edges;}};
 b.after_edge=[&](){if(local_cancel_scope){need(b.d.queue_cancel_queued==expected_cancel_queued&&b.d.queue_cancel_pending==expected_cancel_pending,"independent private cancel owner accounting");need(!b.d.queue_count&&!b.d.queue_pending&&!b.d.queue_active,"private kill retained canceled queue owners");}};
 auto start=[&](unsigned profile){b.prepare(*good,profile,false);b.preload(*good);b.begin(*good);};
 auto canonical_retry=[&](){b.hold_response=false;b.hold_reference_response=false;b.d.start=0;b.settle();need(!b.pending&&!b.reference_pending&&!b.d.ref_pending&&b.d.start_ready,"peer drain did not return reservation");start(0);b.record=true;b.feed_until();b.finish(*good);b.settle();};
 auto retry=[&](){canonical_retry();++retries;};
 for(unsigned peer:{2U,4U})for(unsigned phase:{0U,1U,3U}){
  start(1);b.feed_until(11);const bool write=phase==0;
  for(unsigned k=0;!(b.pending&&b.pending->req.write==write);++k){need(k<3000000,"accepted scratch request setup watchdog");b.tick();}
  b.hold_response=true;need(b.d.dbg_scratch_outstanding,"accepted scratch request lacks physical RTL ledger");const auto owner=b.pending->req;const auto acks=b.acks;const auto commands=P(count_command_accepts);const auto sequence=P(owner_sequence);
  if(write)++accepted_writes;else ++accepted_reads;
  while(b.cycle<b.pending->due)b.tick();
  b.d.in_valid=b.d.in_last=0;need(!P(base_kill_valid),"preexisting peer kill");inject(b,peer);const unsigned cause=peer==2?0xc5:0xe3;need(b.d.error==cause,"immediate peer cause");masked(b);
  if(phase==0)b.hold_response=false;
  b.d.start=1;b.d.epoch=++b.next_epoch;b.tick();b.d.start=0;
  need(P(count_command_accepts)==commands&&P(owner_sequence)==sequence,"fault admitted replacement command");
  need(P(base_kill_valid)&&P(base_kill_owner)==sequence&&P(base_abort),"peer kill was not registered for same owner");
  if(phase!=0)need(b.pending&&b.pending->req==owner&&b.d.dbg_scratch_outstanding&&!b.d.start_ready,"peer fault forgot actual accepted scratch debt");
  inject(b,peer==2?4:2);need(b.d.error==cause,"later peer changed first cause");
  if(phase==1)b.hold_response=false;
  b.tick();need(b.d.error==cause,"local kill changed terminal cause");
  if(phase==3){need(b.pending&&b.pending->req==owner&&b.d.dbg_scratch_outstanding&&!b.d.start_ready,"local kill retired unacknowledged owner");b.tick();need(b.pending&&b.pending->req==owner&&b.d.dbg_scratch_outstanding,"late scratch debt vanished");b.hold_response=false;b.tick();}
  need(!b.pending&&!b.d.dbg_scratch_outstanding&&b.acks==acks+1,"matching scratch reply did not retire exactly one real owner");
  std::cout<<"{\"type\":\"peer_case\",\"status\":\"PASS\",\"peer\":"<<peer<<",\"reply_phase\":"<<phase<<",\"write\":"<<write<<",\"request_epoch\":"<<owner.epoch<<",\"request_address\":"<<owner.addr<<",\"first_cause\":"<<cause<<"}\n";++checks;retry();
 }
 for(unsigned peer:{2U,4U}){
  start(0);b.feed_until(16);for(unsigned k=0;!(b.d.queue_count==1&&b.d.queue_pending);++k){need(k<100,"queued replay setup watchdog");b.tick();}
  need(b.local_read.has_value(),"queue pending lacks independent synchronous replay owner");const auto commands=P(count_command_accepts);inject(b,peer);masked(b);b.tick();need(P(base_kill_valid)&&P(base_abort),"replay peer kill not registered");b.tick();
  need(P(count_command_accepts)==commands,"replay fault admitted hidden command");b.settle();need(b.d.queue_count==0&&!b.d.queue_pending&&!b.d.frame_read_req&&!b.d.frame_read_rsp,"peer kill retained private refill ownership");
  std::cout<<"{\"type\":\"peer_replay_case\",\"status\":\"PASS\",\"peer\":"<<peer<<"}\n";++checks;++replay_checks;retry();
 }
 original_local_cancel_edges=local_cancel_edges;need(original_local_cancel_edges==8,"original peer cancel-edge count changed");
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
 std::cout<<"{\"type\":\"peer_verdict\",\"status\":\"TEST_PASS\",\"seed\":"<<argv[4]<<",\"directed_checks\":"<<checks<<",\"canonical_retries\":"<<retries<<",\"accepted_write_checks\":"<<accepted_writes<<",\"accepted_read_checks\":"<<accepted_reads<<",\"queued_replay_checks\":"<<replay_checks<<",\"prepared_child_fault_injections\":14,\"local_cancel_edges\":"<<original_local_cancel_edges<<",\"all_local_cancel_edges\":"<<local_cancel_edges<<",\"parent_private_cancel_edges\":"<<(local_cancel_edges-original_local_cancel_edges)<<",\"parent_pending_cancel_cases\":"<<parent_checks<<",\"parent_canonical_retries\":"<<parent_retries<<",\"total_canonical_retries\":"<<(retries+parent_retries)<<",\"parent_stage_mask\":"<<parent_stage_mask<<",\"parent_abort_cases\":"<<parent_aborts<<",\"parent_reset_cases\":"<<parent_resets<<",\"canonical_case_id\":\""<<good->id<<"\",\"clock_edges\":"<<b.cycle<<",\"original_oracle_checks_removed\":0,\"peer_private_cancel_assumptions_corrected\":1}\n";return 0;
}catch(const std::exception&e){std::cerr<<"IV115_CONTROL_PEER_FAIL "<<e.what()<<'\n';return 1;}}
