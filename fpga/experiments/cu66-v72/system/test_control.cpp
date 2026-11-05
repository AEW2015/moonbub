#include "Vcu72_system_sim.h"
#include "verilated.h"
#include "../../cu66-v70/memory/memory_map.hpp"
#include <algorithm>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <memory>
#include <stdexcept>
#include <vector>
static void need(bool b,const char*s){if(!b)throw std::runtime_error(s);}
struct Event{
 bool start=false,packet_request=false,packet_response=false,prepare=false,aux_request=false,aux_response=false,aux_error=false,command=false;
 uint16_t packet_address=0,aux_data=0;uint64_t packet_generation=0;uint32_t packet_sequence=0;unsigned opcode=0;
};
struct Sim{
 std::unique_ptr<VerilatedContext> c=std::make_unique<VerilatedContext>();Vcu72_system_sim d{c.get()};
 uint64_t next_pixel=17029,cycles=0;bool packet_pending=false;uint16_t address=0;uint64_t generation=0;uint32_t sequence=0;
 std::vector<uint8_t> packet;
 explicit Sim(const char*path){std::ifstream f(path,std::ios::binary);need(bool(f),"packet open");packet={std::istreambuf_iterator<char>(f),{}};need(packet.size()>88&&packet.size()<=49152,"actualpacket");
  d.clk=0;d.read_clk=0;d.pixel_clk=0;d.pixel_reset_n=0;d.rst=1;d.abort_i=0;d.clear_fault=0;d.start_valid=0;d.packet_rsp_valid=0;d.hud_prepare_ready=0;d.hud_result_valid=0;d.hud_drain_valid=0;d.software_command_ready=0;d.software_ack_valid=0;d.hud_aux_req_valid=0;d.hud_aux_rsp_ready=1;d.diag_address=0;d.peek_address=0;d.eval();for(int i=0;i<8;i++)tick();d.rst=0;d.pixel_reset_n=1;for(int i=0;i<100;i++)tick();
 }
 void advance(uint64_t target){while(c->time()<target){uint64_t next=std::min(target,next_pixel);if(d.eventsPending())next=std::min(next,d.nextTimeSlot());need(next>=c->time(),"eventtime");c->timeInc(next-c->time());if(next==next_pixel){d.pixel_clk=!d.pixel_clk;next_pixel+=17029;}d.eval();}}
 Event tick(){need(cycles<1000000,"controlwatchdog");uint64_t t=c->time();
  d.packet_rsp_valid=packet_pending;if(packet_pending){d.packet_rsp_address=address;d.packet_rsp_generation=generation;d.packet_rsp_sequence=sequence;d.packet_rsp_data=packet.at(address);}d.eval();
  advance(t+2750);d.read_clk=1;d.eval();advance(t+5000);d.eval();
  Event e;e.start=d.start_valid&&d.start_ready;e.packet_request=d.packet_req_valid&&d.packet_req_ready;e.packet_response=d.packet_rsp_valid&&d.packet_rsp_ready;e.prepare=d.hud_prepare_valid&&d.hud_prepare_ready;
  e.packet_address=d.packet_req_address;e.packet_generation=d.packet_req_generation;e.packet_sequence=d.packet_req_sequence;
  e.aux_request=d.hud_aux_req_valid&&d.hud_aux_req_ready;e.aux_response=d.hud_aux_rsp_valid&&d.hud_aux_rsp_ready;e.aux_error=d.hud_aux_rsp_error;e.aux_data=d.hud_aux_rsp_data;
  e.command=d.software_command_valid&&d.software_command_ready;e.opcode=d.software_command_opcode;
  d.clk=1;d.eval();advance(t+7750);d.read_clk=0;d.eval();advance(t+10000);d.clk=0;d.eval();cycles++;
  if(e.packet_response)packet_pending=false;
  if(e.packet_request){need(!packet_pending,"multiplepacketrequests");packet_pending=true;address=e.packet_address;generation=e.packet_generation;sequence=e.packet_sequence;}
  return e;
 }
 void aux(bool writing,uint32_t addr,uint16_t data,bool error,uint64_t gen,uint32_t fid){d.hud_aux_generation=gen;d.hud_aux_frame_id=fid;d.hud_aux_req_valid=1;d.hud_aux_req_write=writing;d.hud_aux_req_addr=addr;d.hud_aux_req_data=data;while(!tick().aux_request){}d.hud_aux_req_valid=0;unsigned count=0;for(;;){auto e=tick();if(e.aux_response){need(e.aux_error==error,"auxerror");if(!writing&&!error)need(e.aux_data==data,"auxreadback");return;}need(++count<2000,"auxwait");}}
};
int main(int argc,char**argv){try{need(argc==2,"firstkeypacketargument");Sim s(argv[1]);s.d.packet_req_ready=1;uint32_t before=s.d.model_writes;
 s.aux(true,cu70_map::HUD0_BASE,0xaaaa,true,10,0);need(s.d.model_writes==before,"idlewriteescaped");
 s.d.start_generation=10;s.d.start_packet_bytes=uint32_t(s.packet.size());s.d.start_valid=1;while(!s.tick().start){}s.d.start_valid=0;s.d.hud_prepare_ready=1;while(!s.tick().prepare){}s.d.hud_prepare_ready=0;
 need(s.d.active_generation==10&&s.d.active_frame_id==0&&s.d.active_key,"actualparsedidentity");uint32_t base=s.d.candidate_bank==0?cu70_map::HUD0_BASE:s.d.candidate_bank==1?cu70_map::HUD1_BASE:cu70_map::HUD2_BASE;
 before=s.d.model_writes;s.aux(true,base,0x1234,false,10,0);s.aux(false,base,0x1234,false,10,0);need(s.d.model_writes==before+1,"writecompletioncount");
 s.aux(true,base,0x9876,true,11,0);s.aux(true,base,0x9876,true,10,1);s.aux(true,cu70_map::CANONICAL0_BASE,0x9876,true,10,0);s.aux(true,base,0x9876,true,10,0);s.aux(true,base+2,0x9876,true,10,0);
 need(s.d.model_writes==before+1,"invalidoroutoforderwriteescaped");s.aux(true,base+1,0x5678,false,10,0);s.aux(false,base+1,0x5678,false,10,0);
 s.d.peek_address=base;s.d.eval();need(s.d.peek_data==0x1234,"readonlymodelpeek");s.d.peek_address=base+1;s.d.eval();need(s.d.peek_data==0x5678,"readonlymodelpeek2");need(s.d.write_event_sequence==s.d.model_writes,"actualwriteeventcount");
 s.d.abort_i=1;s.tick();s.d.abort_i=0;s.d.software_command_ready=1;for(;;){auto e=s.tick();if(e.command){need(e.opcode==6,"abortcommand");break;}}
 s.d.software_command_ready=0;s.d.software_ack_valid=1;s.d.software_ack_opcode=6;s.d.software_ack_generation=10;s.d.software_ack_frame_id=0;s.d.software_ack_success=1;s.tick();s.d.software_ack_valid=0;
 for(unsigned n=0;s.d.busy;n++){need(n<10000,"abortdrain");s.tick();}
 need(!s.d.reference_valid&&!s.d.front_valid&&!s.d.lcd_front_valid&&s.d.accepted_count==0&&!s.d.memory_tile_busy&&!s.d.painter_busy,"partialtransactionpublished");
 s.aux(true,base+2,0x7777,true,10,0);need(s.d.model_writes==before+2,"postabortwriteescaped");
 // A falsely claimed full transfer must fail the hardware coverage fence.
 s.d.start_generation=11;s.d.start_valid=1;while(!s.tick().start){}s.d.start_valid=0;s.d.hud_prepare_ready=1;while(!s.tick().prepare){}s.d.hud_prepare_ready=0;
 s.d.hud_drain_generation=11;s.d.hud_drain_frame_id=0;s.d.hud_drain_bank=s.d.candidate_bank;s.d.hud_drain_words=21120;s.d.hud_drain_success=1;
 for(unsigned i=0;i<4;i++)s.d.hud_drain_tag[i]=s.d.expected_hud_tag[i];
 s.d.hud_drain_valid=1;s.tick();s.d.hud_drain_valid=0;need(s.d.error&&s.d.error_code==0x71,"incompletetransferaccepted");
 s.d.software_command_ready=1;for(;;){auto e=s.tick();if(e.command){need(e.opcode==6,"failedtransferabortcommand");break;}}
 s.d.software_command_ready=0;s.d.software_ack_valid=1;s.d.software_ack_opcode=6;s.d.software_ack_generation=11;s.d.software_ack_frame_id=0;s.d.software_ack_success=1;s.tick();s.d.software_ack_valid=0;
 for(unsigned n=0;s.d.busy;n++){need(n<10000,"faultdrain");s.tick();}
 need(!s.d.reference_valid&&!s.d.front_valid&&!s.d.lcd_front_valid&&s.d.accepted_count==0&&s.d.model_writes==before+2,"failedtransferpublished");
 std::cout<<"SYSTEM_CONTROL_PASS actual_keys_parsed=2 completed_HUD_words=2 denied_writes=7 abort_drained=2 early_HUD_drain_rejected=1 accepted_frames=0 actual_writes="<<s.d.model_writes<<" actual_reads="<<s.d.model_reads<<" refreshes="<<s.d.model_refreshes<<" clocks="<<s.cycles<<"\n";
 }catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}
