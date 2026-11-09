// All frozen V114 control checks run first; new certificate cases are additive.
#include "immutable_control.hpp"
#define P(n) b.d.rootp->cs88_pipeline_v91k__DOT__##n
static void inject(ControlBench&b,unsigned peer){
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

static void masked_certificate(ControlBench&b){need(!b.d.in_ready&&!b.d.out_valid&&!b.d.mem_req_valid&&!b.d.ref_req_valid&&!b.d.coefficient_valid&&!b.d.coefficient_ready&&!b.d.residual_valid&&!b.d.residual_ready,"certificate public mask");}
static void certified_birth(ControlBench&b,unsigned sequence){
 need(P(base_kill_valid)&&P(base_kill_authorized)&&P(base_kill_owner)==sequence&&P(owner_sequence)==sequence,"real kill birth lacks coherent certificate/tag");
 need(P(base_abort),"real certified kill did not drive actual original child boundary");masked_certificate(b);
 std::cout<<"{\"type\":\"certified_birth\",\"cycle\":"<<b.cycle<<",\"sequence\":"<<sequence<<",\"raw_valid\":"<<unsigned(P(base_kill_valid))<<",\"authorized\":"<<unsigned(P(base_kill_authorized))<<",\"tag\":"<<P(base_kill_owner)<<",\"actual_child_abort\":"<<unsigned(P(base_abort))<<"}\n";
}
static void consumed(ControlBench&b){
 b.tick();need(!P(base_kill_valid)&&P(base_kill_authorized)&&!P(base_abort),"one-edge private pulse did not consume/hold authorization");
 std::cout<<"{\"type\":\"certified_consume\",\"cycle\":"<<b.cycle<<",\"sequence\":"<<P(owner_sequence)<<",\"raw_valid\":"<<unsigned(P(base_kill_valid))<<",\"authorized\":"<<unsigned(P(base_kill_authorized))<<",\"actual_child_abort\":"<<unsigned(P(base_abort))<<"}\n";
}
static void fresh_delivery(ControlBench&b){
 b.offer();need(!P(base_kill_authorized)&&!P(base_kill_valid),"new command retained old authorization");b.poison();b.tick();need(P(owner_delivered)&&!P(base_abort),"fresh command did not deliver cleanly");
}
int main(int argc,char**argv){try{
 // This invokes all original 78 cases and four real physical-debt cases with
 // the same original main body and byte-identical original bench.cpp.
 const int frozen=immutable_control_main(argc,argv);need(frozen==0,"frozen control suite failed");
 ControlBench b(std::string(argv[5])+".certificate");unsigned peer_cases=0,peer_births=0,peer_consumes=0,stale_cases=0,no_owner_cases=0,cache_cases=0,reset_cases=0,wrap_cases=0,fresh_retries=0;
 for(unsigned repeat=0;repeat<2;++repeat)for(unsigned peer:{2U,4U}){
  fresh_delivery(b);need(!P(base_kill_authorized)&&!P(base_kill_valid),"peer setup not fresh");const auto owner=P(owner_sequence);inject(b,peer);masked_certificate(b);b.tick();certified_birth(b,owner);++peer_births;consumed(b);++peer_consumes;
  b.abort();fresh_delivery(b);++fresh_retries;b.abort();++peer_cases;
 }
 // Preserve the same retired-tag injection, with new pre-edge checks to ensure
 // the old post-edge check cannot pass merely because valid defaults to zero.
 b.offer();need(!P(base_kill_authorized),"stale fixture inherited a certificate");P(base_kill_valid)=1;P(base_kill_owner)=P(owner_sequence)-1;b.d.eval();need(!P(base_abort),"retired private kill was not filtered before delivery");b.poison();b.tick();need(P(owner_delivered)&&!P(base_abort)&&!P(base_kill_authorized),"retired kill changed new owner delivery");b.abort();fresh_delivery(b);++fresh_retries;b.abort();++stale_cases;
 // An idle/no-owner abort may legitimately issue one real matching kill.
 b.d.reset=1;b.tick();b.d.reset=0;b.tick();b.settle();need(!P(owner_open)&&!P(base_kill_authorized),"idle abort setup");const auto idle_owner=P(owner_sequence);b.d.abort_packet=1;b.tick();certified_birth(b,idle_owner);b.d.abort_packet=0;consumed(b);b.settle();++no_owner_cases;
 // Repeating abort without a new command does not synthesize another birth.
 b.d.abort_packet=1;for(unsigned k=0;k<4;++k){b.tick();need(!P(base_kill_valid),"held/repeated abort duplicated private pulse");}b.d.abort_packet=0;b.tick();b.settle();fresh_delivery(b);++fresh_retries;b.abort();++no_owner_cases;
 // Reset after a real birth clears pending authorization and permits retry.
 fresh_delivery(b);inject(b,2);b.tick();certified_birth(b,P(owner_sequence));b.d.reset=1;masked_certificate(b);b.tick();need(!P(base_kill_valid)&&!P(base_kill_authorized)&&P(owner_sequence)==0,"reset retained certified pulse");b.d.reset=0;b.tick();b.settle();fresh_delivery(b);++fresh_retries;b.abort();++reset_cases;
 // Partial cache preload has no frame owner but must certify its abort and
 // return reservation only via the original cancel/rearm path.
 b.d.reset=1;b.tick();b.d.reset=0;b.tick();b.settle();b.d.cache_valid=1;b.d.cache_last=0;b.d.cache_ref_fid=91;b.d.cache_ref_generation=92;
 for(unsigned k=0;k<7;++k){need(b.d.cache_ready,"cache setup not reserved");b.d.cache_data=k%3;b.tick();}b.d.cache_valid=0;need(P(cache_owned)&&!b.d.start_ready&&!P(base_kill_authorized),"cache owner setup");const auto cache_owner=P(owner_sequence);b.d.abort_packet=1;b.tick();certified_birth(b,cache_owner);b.d.abort_packet=0;consumed(b);b.settle();need(!P(cache_owned),"cache abort retained owner");fresh_delivery(b);++fresh_retries;b.abort();++cache_cases;
 // Frontier fixture mirrors the existing old test and additionally checks the
 // certificate of an actual ff-owner pulse and drained reset clearance.
 b.d.reset=1;b.tick();b.d.reset=0;b.tick();b.settle();P(owner_sequence)=0xfffffffeU;fresh_delivery(b);need(P(owner_sequence)==0xffffffffU,"frontier command did not reach ff");b.d.abort_packet=1;b.tick();certified_birth(b,0xffffffffU);b.d.abort_packet=0;consumed(b);for(unsigned k=0;k<10;++k)b.tick();need(!b.d.start_ready,"certificate bypassed owner wrap guard");b.d.reset=1;b.tick();need(!P(base_kill_authorized),"frontier reset retained certificate");b.d.reset=0;b.tick();b.settle();fresh_delivery(b);++fresh_retries;b.abort();++wrap_cases;
 need(peer_cases==4&&peer_births==4&&peer_consumes==4&&stale_cases==1&&no_owner_cases==2&&cache_cases==1&&reset_cases==1&&wrap_cases==1&&fresh_retries==9,"certificate coverage not complete");
 std::cout<<"{\"type\":\"owner_certificate_verdict\",\"status\":\"TEST_PASS\",\"seed\":"<<argv[4]<<",\"frozen_directed_checks\":78,\"frozen_physical_drain_checks\":4,\"real_peer_cases\":"<<peer_cases<<",\"real_peer_births\":"<<peer_births<<",\"real_peer_consumes\":"<<peer_consumes<<",\"stale_private_injections\":"<<stale_cases<<",\"no_owner_abort_cases\":"<<no_owner_cases<<",\"cache_abort_cases\":"<<cache_cases<<",\"reset_pending_cases\":"<<reset_cases<<",\"wrap_cases\":"<<wrap_cases<<",\"fresh_command_retries\":"<<fresh_retries<<",\"new_canonical_retry_claim\":false,\"old_assertions_removed\":0}\n";return 0;
}catch(const std::exception&e){std::cerr<<"OWNER_CERTIFICATE_FAIL "<<e.what()<<'\n';return 1;}}
