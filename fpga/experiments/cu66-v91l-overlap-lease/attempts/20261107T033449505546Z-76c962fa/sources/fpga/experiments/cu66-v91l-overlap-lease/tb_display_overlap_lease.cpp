#include "Vdisplay_overlap_lease.h"
#include "verilated.h"
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string>

static void need(bool ok,const std::string& message){if(!ok)throw std::runtime_error(message);}
struct Bench {
 Vdisplay_overlap_lease d;
 unsigned checks=0,cycles=0;
 void eval(){d.clk=0;d.eval();}
 void tick(unsigned n=1){while(n--){need(++cycles<10000,"finite lease watchdog");eval();Verilated::timeInc(5000);d.clk=1;d.eval();Verilated::timeInc(5000);d.clk=0;d.eval();}}
 void check(bool ok,const std::string& name){need(ok,name);++checks;std::cout<<"{\"type\":\"check\",\"status\":\"PASS\",\"name\":\""<<name<<"\",\"cycle\":"<<cycles<<"}\n";}
 void defaults(){
  d.power_on_reset=0;d.reset=0;d.cancel=0;d.start_valid=0;d.start_epoch=7;d.start_generation=9;d.start_bank=0;
  d.accepted_valid=1;d.accepted_bank=0;d.accepted_fid=0;d.accepted_generation=9;
  d.engine_start_ready=1;d.engine_busy=0;d.engine_draining=0;d.engine_done=0;d.engine_error=0;
  d.reader_busy=0;d.reader_pending=0;d.mux_owner=0;d.external_drained=1;d.candidate_valid=0;d.candidate_bank=2;
  eval();
 }
 void cold(){defaults();d.power_on_reset=1;tick(3);d.power_on_reset=0;tick();check(!d.active&&d.start_ready&&d.effective_drained,"cold_no_owner");}
 void accepted(unsigned bank=0,unsigned fid=0,uint32_t generation=9,uint32_t epoch=7){
  defaults();d.start_bank=bank;d.accepted_bank=bank;d.accepted_fid=fid;d.accepted_generation=generation;
  d.start_generation=generation;d.start_epoch=epoch;d.start_valid=1;eval();
  check(d.start_ready&&d.engine_start&&!d.start_rejected&&!d.effective_drained,"qualified_start_blocks_same_edge_publication");
  d.candidate_valid=1;d.candidate_bank=bank;eval();check(!d.candidate_allowed&&d.alias_fault,"same_edge_start_reserves_bank");
  d.candidate_valid=0;tick();d.start_valid=0;d.engine_busy=1;eval();
  check(d.active&&!d.start_ready&&d.lease_bank==bank&&d.lease_fid==fid&&d.lease_epoch==epoch&&d.lease_generation==generation,"accepted_full_descriptor");
 }
 void finish(){
  d.engine_done=1;d.engine_busy=0;d.engine_draining=0;d.reader_busy=0;d.reader_pending=0;d.mux_owner=0;
  tick();check(d.active&&d.idle_samples==1&&!d.effective_drained,"first_idle_retains_owner");
  tick();check(!d.active&&d.effective_drained,"second_idle_releases_owner");
  d.engine_done=0;tick();check(!d.active&&!d.terminal_seen&&d.start_ready,"released_ready_for_next_source");
 }
 void illegal(unsigned which){
  defaults();
  switch(which){
   case 0:d.accepted_valid=0;break;
   case 1:d.accepted_bank=3;d.start_bank=3;break;
   case 2:d.start_bank=1;break;
   case 3:d.start_epoch=0;break;
   case 4:d.accepted_generation=0;d.start_generation=0;break;
   case 5:d.start_generation=10;break;
   case 6:d.accepted_generation=(uint64_t(1)<<32)|9;break;
   default:throw std::runtime_error("invalid illegal fixture");
  }
  d.start_valid=1;eval();check(d.start_ready&&d.start_rejected&&!d.engine_start,"invalid_descriptor_rejected_without_engine_start");
  tick();check(!d.active&&!d.engine_start,"invalid_descriptor_has_no_lease");
  d.start_valid=0;tick();check(d.effective_drained,"invalid_offer_withdrawn_drains");
 }
 void pending_drain(unsigned kind){
  accepted(1,17,0xffffffffU,0x80000007U);
  d.engine_busy=0;d.reader_busy=1;d.reader_pending=1;d.mux_owner=1;
  if(kind==0)d.cancel=1;else if(kind==1)d.reset=1;else if(kind==2)d.engine_error=0x81;else d.engine_done=1;
  tick();check(d.active&&d.terminal_seen&&!d.effective_drained&&d.idle_samples==0,"terminal_keeps_physical_reader_owner");
  d.cancel=0;d.reset=0;d.engine_done=0;d.engine_error=0;
  const uint8_t expected_error=kind<2?2:kind==2?0x81:0;
  for(unsigned n=0;n<8;++n){
   // These pending states stand for an accepted burst that may not be ignored
   // merely because engine_done, reset, or error was observed upstream.
   d.accepted_generation=uint64_t(0xa55a)<<32|33;d.accepted_bank=2;d.accepted_fid=99;
   tick();check(d.active&&d.terminal_error==expected_error&&d.lease_generation==0xffffffffU&&d.lease_bank==1&&d.lease_fid==17&&d.lease_epoch==0x80000007U,"pending_burst_and_changing_hints_preserve_lease");
  }
  d.reader_pending=0;d.reader_busy=0;d.mux_owner=1;tick();check(d.active&&d.idle_samples==0,"display_mux_held_reply_retains_lease");
  d.mux_owner=0;tick();check(d.active&&d.idle_samples==1,"one_idle_after_pending_not_enough");
  d.reader_pending=1;tick();check(d.active&&d.idle_samples==0,"renewed_pending_restarts_two_idle_fence");
  d.reader_pending=0;tick();check(d.active&&d.idle_samples==1,"drain_restarts_first_idle");
  tick();check(!d.active&&d.effective_drained&&d.terminal_error==expected_error,"terminal_releases_only_after_actual_drain");
  tick();
 }
};
int main(int argc,char** argv){try{
 Verilated::commandArgs(argc,argv);Bench b;b.cold();
 for(unsigned i=0;i<7;++i)b.illegal(i);
 b.accepted(0,0,9,7);
 for(unsigned n=0;n<11;++n){
  b.d.accepted_bank=2;b.d.accepted_fid=123;b.d.accepted_generation=33;b.d.start_bank=2;b.d.start_epoch=55;b.d.start_generation=33;
  b.d.candidate_valid=1;b.d.candidate_bank=0;b.eval();b.check(!b.d.candidate_allowed&&b.d.alias_fault,"active_bank_write_backpressured");
  b.d.candidate_bank=1;b.eval();b.check(b.d.candidate_allowed&&!b.d.alias_fault,"different_candidate_bank_allowed");
  b.tick();b.check(b.d.active&&b.d.lease_bank==0&&b.d.lease_fid==0&&b.d.lease_generation==9&&b.d.lease_epoch==7&&!b.d.effective_drained,"accepted_reference_changes_do_not_retarget_scanout");
 }
 b.d.candidate_valid=0;b.finish();
 for(unsigned kind=0;kind<4;++kind)b.pending_drain(kind);
 b.accepted(2,0,11,9);b.d.engine_done=1;b.d.engine_busy=0;b.d.engine_draining=1;b.tick(4);b.check(b.d.active&&b.d.idle_samples==0,"engine_draining_blocks_release");
 b.d.engine_draining=0;b.d.reader_busy=1;b.d.reader_pending=0;b.d.mux_owner=2;b.tick(4);b.check(b.d.active&&b.d.idle_samples==0,"reference_owned_reader_conservatively_blocks_release");
 b.d.reader_busy=0;b.d.mux_owner=0;b.tick(2);b.check(!b.d.active&&b.d.effective_drained,"all_engine_and_reader_drains_complete");
 b.d.engine_done=0;b.d.external_drained=0;b.eval();b.check(!b.d.effective_drained,"external_scanout_hint_remains_required");b.d.external_drained=1;b.tick();
 need(!b.d.active&&!b.d.engine_busy&&!b.d.reader_pending,"terminal no display lease");
 std::cout<<"{\"type\":\"verdict\",\"status\":\"TEST_PASS\",\"checks\":"<<b.checks<<",\"cycles\":"<<b.cycles<<"}\n";return 0;
}catch(const std::exception& e){std::cerr<<"DISPLAY_LEASE_TEST_FAIL "<<e.what()<<'\n';return 1;}}
