#include "clock_adapter.hpp"
#include "tb_bank.cpp"
int main(int argc,char**argv){try{
 need(inherited_bank_main(argc,argv)==0,"inherited complete scratch value/owner/request/corrupt/boundary suite");
 const unsigned seed=unsigned(std::stoul(argv[1]));std::ofstream trace(std::string(argv[2])+"-prepare.jsonl");need(bool(trace),"prepare trace open");unsigned pending_cancel=0,wrong_tags=0,retries=0;
 for(unsigned phase=0;phase<3;++phase)for(unsigned reset=0;reset<2;++reset)for(unsigned raw=0;raw<2;++raw){
  ProbeBench b(seed+pending_cancel+3000,trace);auto p=packet(3,raw!=0,seed+pending_cancel);
  b.d.adapter_enabled=false;b.d.begin_blocks=p.blocks;b.d.begin_raw=p.raw;b.d.begin_epoch=1;b.d.begin_overlap=1;b.d.begin_prefetch=1;b.d.begin_tile_overlap=!p.raw;
  b.d.begin_count1=p.records[1].size();b.d.begin_count2=p.records[2].size();b.d.begin_count3=p.records[3].size();b.d.begin_valid=1;b.d.clk=0;b.d.eval();need(b.d.begin_ready,"pending-case begin not ready");
  b.d.candidate_only_edge();b.d.begin_valid=0;for(unsigned k=0;k<phase;++k)b.d.candidate_only_edge();
  need(b.d.verify_preparing&&b.d.busy&&!b.d.mem_req_valid&&!b.d.dense_valid&&!b.d.debug_outstanding&&b.d.active_epoch==1,"pending descriptor gained physical or committed epoch effects");
  b.d.abort_valid=1;b.d.abort_epoch=0;b.d.eval();need(!b.d.verify_prepare_cancel&&b.d.verify_preparing,"stale active-epoch abort canceled pending descriptor");++wrong_tags;
  b.d.abort_valid=!reset;b.d.abort_epoch=b.d.active_epoch;b.d.reset=reset;b.d.candidate_only_edge();b.d.abort_valid=0;b.d.reset=0;b.d.clk=0;b.d.eval();
  need(b.d.begin_ready&&!b.d.busy&&!b.d.error&&!b.d.mem_req_valid&&!b.d.debug_outstanding,"pending cancel/reset did not release uncommitted descriptor");++pending_cancel;
  // This NEW candidate-only case has no corresponding old admitted epoch.
  // Same tag retry runs the real transaction with all independent dense,
  // request/response owner and cache-position goldens; old paired cases above
  // retain their complete original comparisons outside declared warm-up.
  b.ingest(p,6);b.finish();++retries;
  b.abort_and_drain(false);
  b.d.begin_valid=1;b.d.begin_epoch=b.epoch;b.tick();b.d.begin_valid=0;
  for(unsigned k=0;!b.d.error;++k){need(k<5,"committed epoch reject watchdog");b.tick();}
  need(b.d.error==2&&!b.pending&&!b.d.debug_outstanding,"committed epoch replay accepted");
  b.abort_and_drain(false);b.ingest(p,6);b.finish();++retries;
 }
 need(pending_cancel==12&&wrong_tags==12&&retries==24,"new pending-stage/retry coverage");
 need(PrepareStats::transactions>250&&PrepareStats::extra_edges==3*PrepareStats::transactions&&PrepareStats::poisoned==PrepareStats::transactions&&PrepareStats::preedge_comparisons==PrepareStats::transactions,"fixed prepare edge/capture/poison conservation");
 std::cout<<"{\"type\":\"v115_scratch_prepare_verdict\",\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"full_transactions\":72,\"corrupt_response_cases\":128,\"read_owner_cases\":4,\"dc_line_boundary_transactions\":48,\"pending_cancel_cases\":"<<pending_cancel<<",\"stale_pending_abort_checks\":"<<wrong_tags<<",\"complete_retry_transactions\":"<<retries<<",\"paired_accepted_descriptors\":"<<PrepareStats::transactions<<",\"paired_candidate_extra_edges\":"<<PrepareStats::extra_edges<<",\"poisoned_tuples\":"<<PrepareStats::poisoned<<",\"original_oracles_removed\":0,\"old_public_cycle_equivalence\":false}\n";return 0;
}catch(const std::exception&e){std::cerr<<"V115_SCRATCH_FAIL "<<e.what()<<'\n';return 1;}}
