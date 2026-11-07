#include "Vtile_mux_unit.h"
#include "verilated.h"
#include <array>
#include <cstdint>
#include <deque>
#include <functional>
#include <iostream>
#include <optional>
#include <stdexcept>
#include <string>
#include <vector>
#ifndef TEST_REF_LINES
#define TEST_REF_LINES 4
#endif
struct Request {unsigned who;uint32_t epoch,generation;unsigned bank,address;bool error=false;unsigned gap=0;};
struct Pending {Request q;unsigned age=0;bool acked=false,offered=false;unsigned drain=0;};
struct Seen {Request q;uint64_t cycle;};
struct Bench {
 Vtile_mux_unit d;uint64_t cycle=0;unsigned checks=0;
 std::deque<Request> refs,display;std::optional<Pending> pending;std::vector<Seen> accepted,acked;
 uint64_t next_ref_cycle=0;bool hold_port=false,reply_enable=true,hold_ref=false,hold_display=false,wrong=false;
 bool ref_reset=false,ref_cancel=false,display_reset=false,display_cancel=false;
 static std::array<uint32_t,4> payload(const Request&q){return {q.epoch^0x12345678U,q.generation^0xfedcba98U,uint32_t(q.bank*0x1020304U+q.address),q.address^0x87654321U};}
 void need(bool ok,const std::string& label){if(!ok)throw std::runtime_error(label+" cycle="+std::to_string(cycle));++checks;std::cout<<"{\"type\":\"check\",\"status\":\"PASS\",\"label\":\""<<label<<"\",\"cycle\":"<<cycle<<"}\n";}
 void tick(){
  if(cycle>20000)throw std::runtime_error("global finite watchdog");
  d.clk=0;d.reference_reset=ref_reset;d.reference_cancel=ref_cancel;d.display_reset=display_reset;d.display_cancel=display_cancel;
  d.reference_req_valid=!refs.empty()&&cycle>=next_ref_cycle;d.display_req_valid=!display.empty();
  if(!refs.empty()){const auto&q=refs.front();d.reference_req_epoch=q.epoch;d.reference_req_generation=q.generation;d.reference_req_bank=q.bank;d.reference_req_addr=q.address;}
  if(!display.empty()){const auto&q=display.front();d.display_req_epoch=q.epoch;d.display_req_generation=q.generation;d.display_req_bank=q.bank;d.display_req_addr=q.address;}
  d.reference_rsp_ready=!hold_ref;d.display_rsp_ready=!hold_display;
  d.mem_req_ready=!pending&&!hold_port;d.mem_busy=bool(pending);d.mem_rsp_valid=pending&&!pending->acked&&reply_enable&&pending->age>=2;
  d.mem_rsp_epoch=0;d.mem_rsp_generation=0;d.mem_rsp_bank=0;d.mem_rsp_addr=0;d.mem_rsp_error=0;
  for(unsigned i=0;i<4;++i)d.mem_rsp_data[i]=0;
  if(pending){const auto&q=pending->q;d.mem_rsp_epoch=q.epoch;d.mem_rsp_generation=q.generation^(wrong?1U:0U);d.mem_rsp_bank=q.bank;d.mem_rsp_addr=q.address;d.mem_rsp_error=q.error;auto words=payload(q);for(unsigned i=0;i<4;++i)d.mem_rsp_data[i]=q.error?0:words[i];}
  d.eval();
  std::optional<Request> new_request;
  if(d.mem_req_valid&&d.mem_req_ready){
   need(!pending,"single_pending_physical_line");const auto who=unsigned(d.owner);need(who==1||who==2,"physical_owner_legal");auto &queue=who==1?display:refs;need(!queue.empty(),"accepted_offer_exists");const auto q=queue.front();
   need(d.mem_req_epoch==q.epoch&&d.mem_req_generation==q.generation&&d.mem_req_bank==q.bank&&d.mem_req_addr==q.address,"physical_request_identity");
   need(who==1?bool(d.display_req_ready):bool(d.reference_req_ready),"request_ready_routed_only_owner");
   queue.pop_front();new_request=q;accepted.push_back({q,cycle});
   std::cout<<"{\"type\":\"unit_mem_accept\",\"cycle\":"<<cycle<<",\"owner\":"<<who<<",\"epoch\":"<<q.epoch<<",\"generation\":"<<q.generation<<",\"bank\":"<<q.bank<<",\"address\":"<<q.address<<"}\n";
  }
  const bool ack=d.mem_rsp_valid&&d.mem_rsp_ready;
  if(d.mem_rsp_valid){
   if(wrong)need(!d.mem_rsp_ready&&!d.reference_rsp_valid&&!d.display_rsp_valid,"wrong_reply_tag_not_consumed");
   else {
    need(pending.has_value(),"reply_owned");const auto&q=pending->q;need(q.who==unsigned(d.owner),"reply_owner_preserved");
    need(q.who==1?bool(d.display_rsp_valid)&&!d.reference_rsp_valid:bool(d.reference_rsp_valid)&&!d.display_rsp_valid,"reply_only_owner");
    const auto words=payload(q);for(unsigned i=0;i<4;++i)need((q.who==1?d.display_rsp_data[i]:d.reference_rsp_data[i])==(q.error?0:words[i]),"all_reply_payload_words");
    need((q.who==1?d.display_rsp_error:d.reference_rsp_error)==q.error,"reply_error_preserved");
   }
  }
  if(ack){need(pending.has_value(),"ack_has_owner");acked.push_back({pending->q,cycle});if(pending->q.who==2)next_ref_cycle=cycle+pending->q.gap;}
  const bool kill=d.mem_reset||d.mem_cancel;
  const bool offered=d.mem_rsp_valid;
  Verilated::timeInc(5000);d.clk=1;d.eval();++cycle;Verilated::timeInc(5000);d.clk=0;d.eval();
  if(pending){
   if(kill&&!pending->offered&&!offered)pending->q.error=true;
   if(offered)pending->offered=true;
   if(ack){pending->acked=true;pending->drain=2;}
   else if(pending->acked){if(--pending->drain==0)pending.reset();}
   else ++pending->age;
  }
  if(new_request)pending=Pending{*new_request};
 }
 void step(unsigned n=1){for(unsigned i=0;i<n;++i)tick();}
 void until(const std::function<bool()>& f,const std::string& what){for(unsigned n=0;n<600&&!f();++n)tick();need(f(),what);}
 void idle(){until([&]{return refs.empty()&&display.empty()&&!pending&&d.owner==0;},"bounded_terminal_idle");step(3);need(d.owner==0&&!d.grant_reserved,"all_mux_owners_released");}
 void reset(){need(!pending,"reset_without_physical_owner");refs.clear();display.clear();next_ref_cycle=0;accepted.clear();acked.clear();hold_port=false;reply_enable=true;hold_ref=hold_display=wrong=ref_reset=ref_cancel=display_reset=display_cancel=false;d.power_on_reset=1;step(2);d.power_on_reset=0;step();need(d.owner==0,"cold_owner_idle");}
 void ref(uint32_t gen,unsigned address,unsigned gap=0,bool error=false,unsigned bank=0,uint32_t epoch=7){refs.push_back({2,epoch,gen,bank,address,error,gap});}
 void disp(){display.push_back({1,99,100,2,128});}
 void start_one(){until([&]{return accepted.size()==1;},"first_reference_accepted");}
};
int main(int argc,char**argv){try{Verilated::commandArgs(argc,argv);Bench b;
 // Four retired lines retain one source grant, then a waiting display gets a turn.
 b.reset();for(unsigned i=0;i<5;++i)b.ref(10+i,i*16);b.start_one();b.disp();b.idle();
 b.need(b.accepted.size()==6&&b.acked.size()==6,"five_reference_one_display_complete");
 b.need(b.accepted[TEST_REF_LINES==4?4:1].q.who==1,"bounded_four_credit_display_turn");
 if(TEST_REF_LINES==4){b.need(b.d.grant_continuations==3&&b.d.grant_timeouts==1,"four_line_budget_and_partial_next_tile_timeout");}
 // Physical ticket UINT32_MAX wraps to one without narrowing outer identities.
 b.reset();b.ref(0xffffffffU,0);b.ref(1,16);b.ref(2,32);b.ref(3,48);b.start_one();b.disp();b.idle();
 if(TEST_REF_LINES==4)b.need(b.d.grant_continuations==3,"skip_zero_ticket_continuations");
 // A short producer gap retains the reference turn; the same limit bounds no-offer waits.
 b.reset();for(unsigned i=0;i<4;++i)b.ref(100+i,i*16,6);b.start_one();b.disp();b.idle();
 if(TEST_REF_LINES==4)b.need(b.accepted[4].q.who==1&&b.d.grant_timeouts==0,"bounded_short_gap_reservation");
 b.reset();b.ref(10,0);b.start_one();b.disp();b.idle();
 if(TEST_REF_LINES==4)b.need(b.d.grant_timeouts==1&&b.accepted.back().q.who==1,"missing_next_offer_times_out");
 // Each changed continuation field must yield without accidentally accepting it.
 for(unsigned variant=0;variant<5;++variant){
  b.reset();b.ref(10,0);b.ref(variant==0?12:11,variant==1?48:variant==2?64:16,0,false,variant==3?1:0,variant==4?8:7);b.start_one();b.disp();b.idle();
  b.need(b.accepted.size()==3&&b.accepted[1].q.who==1,"mismatch_yields_before_new_reference_request");
  if(TEST_REF_LINES==4)b.need(b.d.grant_mismatches==1,"one_continuation_mismatch_recorded");
 }
 // A legal 16-byte line that does not start a 64-byte tile is standalone.
 b.reset();b.ref(20,16);b.ref(21,32);b.start_one();b.disp();b.idle();b.need(b.accepted[1].q.who==1,"non_tile_start_is_standalone");
 if(TEST_REF_LINES==4)b.need(b.d.grant_groups==0&&b.d.grant_continuations==0,"non_tile_start_never_crosses_tile_budget");
 // The final legal tile ends exactly at the physical canonical aperture limit.
 b.reset();for(unsigned i=0;i<4;++i)b.ref(200+i,518336+i*16);b.start_one();b.disp();b.idle();
 if(TEST_REF_LINES==4)b.need(b.d.grant_groups==1&&b.d.grant_continuations==3&&b.d.grant_timeouts==0,"final_legal_tile_stays_within_aperture");
 // Initial invalid requests retain the lower bridge's rejection contract and never reserve.
 for(unsigned variant=0;variant<4;++variant){
  b.reset();b.ref(variant==0?0:210,variant==1?518400:0,0,true,variant==2?3:0,variant==3?0:7);b.start_one();b.disp();b.idle();
  b.need(b.d.grant_groups==0&&b.d.grant_continuations==0&&b.accepted.back().q.who==1,"invalid_first_metadata_never_reserves");
 }
 // Held and wrong-tag replies retain the owner; an unrelated kill stays isolated.
 b.reset();b.ref(30,0);b.hold_ref=true;b.start_one();b.disp();b.until([&]{return b.pending&&b.pending->age>=2;},"held_response_available");b.step(3);b.need(b.d.owner==2&&b.accepted.size()==1,"held_response_excludes_display");
 b.wrong=true;b.step(3);b.wrong=false;b.display_cancel=true;b.step(2);b.display_cancel=false;b.need(b.d.owner==2,"ungranted_display_cancel_preserves_reference");
 b.ref_cancel=true;b.step(2);b.ref_cancel=false;b.hold_ref=false;b.idle();b.need(b.accepted.back().q.who==1,"held_late_cancel_ack_then_display");
 // Accepted work survives reset until its matching error response and bridge drain.
 b.reset();b.ref(40,0);b.reply_enable=false;b.start_one();b.disp();b.ref_reset=true;b.step(3);b.need(b.d.owner==2&&b.pending.has_value(),"reset_cannot_discard_pending_line");b.reply_enable=true;b.until([&]{return !b.acked.empty();},"reset_reply_acknowledged");b.ref_reset=false;b.idle();
 // Error replies end reservations; next offer needs a fresh RR turn.
 b.reset();b.ref(50,0,0,true);b.ref(51,16);b.start_one();b.disp();b.idle();b.need(b.accepted[1].q.who==1,"error_yields_before_continuation");b.need(b.d.grant_error_yields==1,"error_yield_count");
 // No physical acceptance means a withdrawn offer releases immediately.
 b.reset();b.hold_port=true;b.ref(60,0);b.until([&]{return b.d.owner==2;},"unaccepted_reference_grant");b.refs.clear();b.disp();b.step(2);b.hold_port=false;b.idle();b.need(b.accepted.size()==1&&b.accepted[0].q.who==1,"withdrawn_reference_never_accepted");
 // A matching offer blocked at the lower port is not mistaken for a missing offer.
 b.reset();b.ref(70,0);b.ref(71,16);b.start_one();b.disp();b.until([&]{return !b.acked.empty();},"first_ack_before_lower_stall");b.hold_port=true;b.step(14);b.need(b.accepted.size()==1,"lower_backpressure_preserves_request_credit");b.hold_port=false;b.idle();
 if(TEST_REF_LINES==4)b.need(b.d.grant_continuations==1,"matching_offer_waits_without_gap_timeout");
 std::cout<<"{\"type\":\"verdict\",\"status\":\"TEST_PASS\",\"checks\":"<<b.checks<<",\"cycles\":"<<b.cycle<<",\"reference_lines\":"<<TEST_REF_LINES<<"}\n";return 0;
}catch(const std::exception&e){std::cerr<<"TILE_MUX_TEST_FAIL "<<e.what()<<'\n';return 1;}}
