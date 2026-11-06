#include "Vcu75_system_sim.h"
#include "verilated.h"
#include "../../cu66-v70/memory/memory_map.hpp"
#include <algorithm>
#include <array>
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
 uint16_t packet_address=0,aux_data=0;uint64_t packet_generation=0;uint32_t packet_sequence=0;unsigned opcode=0;std::array<uint16_t,8> aux_wide{};
};
struct Sim{
 std::unique_ptr<VerilatedContext> c=[](){auto v=std::make_unique<VerilatedContext>();v->threads(1);return v;}();Vcu75_system_sim d{c.get()};
 uint64_t next_pixel=17029,cycles=0;bool packet_pending=false;uint16_t address=0;uint64_t generation=0;uint32_t sequence=0;
 std::vector<uint8_t> packet;
 explicit Sim(const char*path){std::ifstream f(path,std::ios::binary);need(bool(f),"packet open");packet={std::istreambuf_iterator<char>(f),{}};need(packet.size()>88&&packet.size()<=49152,"actualpacket");
  d.clk=0;d.read_clk=0;d.pixel_clk=0;d.pixel_reset_n=0;d.rst=1;d.abort_i=0;d.clear_fault=0;d.start_valid=0;d.packet_rsp_valid=0;d.hud_prepare_ready=0;d.hud_result_valid=0;d.hud_drain_valid=0;d.software_command_ready=0;d.software_ack_valid=0;d.hud_aux_req_valid=0;d.hud_aux_req_burst=0;d.hud_aux_req_read_burst=0;d.hud_aux_req_byte_enable=0;for(unsigned i=0;i<4;i++)d.hud_aux_req_burst_data[i]=0;d.hud_aux_rsp_ready=1;d.diag_address=0;d.peek_address=0;d.eval();for(int i=0;i<8;i++)tick();d.rst=0;d.pixel_reset_n=1;for(int i=0;i<100;i++)tick();
 }
 void advance(uint64_t target){while(c->time()<target){uint64_t next=std::min(target,next_pixel);if(d.eventsPending())next=std::min(next,d.nextTimeSlot());need(next>=c->time(),"eventtime");c->timeInc(next-c->time());if(next==next_pixel){d.pixel_clk=!d.pixel_clk;next_pixel+=17029;}d.eval();}}
 Event tick(){need(cycles<1000000,"controlwatchdog");uint64_t t=c->time();
  d.packet_rsp_valid=packet_pending;if(packet_pending){d.packet_rsp_address=address;d.packet_rsp_generation=generation;d.packet_rsp_sequence=sequence;d.packet_rsp_data=packet.at(address);}d.eval();
  advance(t+2750);d.read_clk=1;d.eval();advance(t+5000);d.eval();
  Event e;e.start=d.start_valid&&d.start_ready;e.packet_request=d.packet_req_valid&&d.packet_req_ready;e.packet_response=d.packet_rsp_valid&&d.packet_rsp_ready;e.prepare=d.hud_prepare_valid&&d.hud_prepare_ready;
  e.packet_address=d.packet_req_address;e.packet_generation=d.packet_req_generation;e.packet_sequence=d.packet_req_sequence;
  e.aux_request=d.hud_aux_req_valid&&d.hud_aux_req_ready;e.aux_response=d.hud_aux_rsp_valid&&d.hud_aux_rsp_ready;e.aux_error=d.hud_aux_rsp_error;e.aux_data=d.hud_aux_rsp_data;for(unsigned i=0;i<8;i++)e.aux_wide[i]=uint16_t(d.hud_aux_rsp_burst_data[i/2]>>((i%2)*16));
  e.command=d.software_command_valid&&d.software_command_ready;e.opcode=d.software_command_opcode;
  d.clk=1;d.eval();advance(t+7750);d.read_clk=0;d.eval();advance(t+10000);d.clk=0;d.eval();cycles++;
  if(e.packet_response)packet_pending=false;
  if(e.packet_request){need(!packet_pending,"multiplepacketrequests");packet_pending=true;address=e.packet_address;generation=e.packet_generation;sequence=e.packet_sequence;}
  return e;
 }
 void aux(bool writing,uint32_t addr,uint16_t data,bool error,uint64_t gen,uint32_t fid){d.hud_aux_req_burst=0;d.hud_aux_req_read_burst=0;d.hud_aux_req_byte_enable=0;d.hud_aux_generation=gen;d.hud_aux_frame_id=fid;d.hud_aux_req_valid=1;d.hud_aux_req_write=writing;d.hud_aux_req_addr=addr;d.hud_aux_req_data=data;while(!tick().aux_request){}d.hud_aux_req_valid=0;unsigned count=0;for(;;){auto e=tick();if(e.aux_response){need(e.aux_error==error,"auxerror");if(!writing&&!error)need(e.aux_data==data,"auxreadback");return;}need(++count<2000,"auxwait");}}
 void prepare(uint64_t gen){d.packet_req_ready=1;d.start_generation=gen;d.start_packet_bytes=uint32_t(packet.size());d.start_valid=1;while(!tick().start){}d.start_valid=0;d.hud_prepare_ready=1;while(!tick().prepare){}d.hud_prepare_ready=0;need(d.active_generation==gen&&d.active_frame_id==0&&d.active_key,"parsedburstidentity");d.packet_req_ready=0;}
 uint32_t base(){return d.candidate_bank==0?cu70_map::HUD0_BASE:d.candidate_bank==1?cu70_map::HUD1_BASE:cu70_map::HUD2_BASE;}
 void abort_frame(uint64_t gen,bool initiate=true){
  if(initiate){d.abort_i=1;tick();d.abort_i=0;}
  d.hud_aux_rsp_ready=1;d.hud_aux_req_valid=0;d.software_command_ready=1;
  for(unsigned n=0;;n++){need(n<10000,"burstabortcommandwait");auto e=tick();if(e.command){need(e.opcode==6,"burstabortcommand");break;}}
  d.software_command_ready=0;d.software_ack_valid=1;d.software_ack_opcode=6;d.software_ack_generation=gen;d.software_ack_frame_id=0;d.software_ack_success=1;
  for(unsigned n=0;!d.software_ack_ready;n++){need(n<10000,"burstabortackwait");tick();}tick();d.software_ack_valid=0;
  for(unsigned n=0;d.busy;n++){need(n<10000,"burstabortdrain");tick();}
  need(!d.reference_valid&&!d.front_valid&&!d.lcd_front_valid&&d.accepted_count==0&&!d.memory_tile_busy&&!d.memory_aux_busy&&!d.painter_busy,"burstpartialpublished");
 }
 void payload(const std::array<uint16_t,8>& v){for(unsigned i=0;i<4;i++)d.hud_aux_req_burst_data[i]=uint32_t(v[i*2])|(uint32_t(v[i*2+1])<<16);}
 void raw_request(bool writing,uint32_t addr,uint64_t gen,uint32_t fid,bool wb,bool rb,uint16_t mask,const std::array<uint16_t,8>& v){
  d.hud_aux_generation=gen;d.hud_aux_frame_id=fid;d.hud_aux_req_write=writing;d.hud_aux_req_addr=addr;d.hud_aux_req_data=v[0];d.hud_aux_req_burst=wb;d.hud_aux_req_read_burst=rb;d.hud_aux_req_byte_enable=mask;payload(v);d.hud_aux_req_valid=1;for(unsigned n=0;;n++){need(n<2000,"rawrequestwait");if(tick().aux_request)break;}d.hud_aux_req_valid=0;
 }
 Event response(bool error){for(unsigned n=0;;n++){need(n<2000,"rawresponsewait");auto e=tick();if(e.aux_response){need(e.aux_error==error,"rawresponseerror");return e;}}}
 Event wide(bool writing,uint32_t addr,uint64_t gen,const std::array<uint16_t,8>& v,bool hold=false,bool mutate=false){
  d.hud_aux_rsp_ready=!hold;raw_request(writing,addr,gen,0,writing,!writing,writing?0xffff:0,v);
  if(mutate){d.hud_aux_generation=gen+100;d.hud_aux_frame_id=99;d.hud_aux_req_addr=0xffffff;d.hud_aux_req_write=!writing;d.hud_aux_req_burst=!writing;d.hud_aux_req_read_burst=writing;d.hud_aux_req_byte_enable=0x5555;std::array<uint16_t,8> poison{};poison.fill(0xdead);payload(poison);}
  if(hold){for(unsigned n=0;!d.hud_aux_rsp_valid;n++){need(n<2000,"heldresponsewait");tick();}std::array<uint32_t,4> snapshot{};for(unsigned i=0;i<4;i++)snapshot[i]=d.hud_aux_rsp_burst_data[i];bool err=d.hud_aux_rsp_error;uint16_t scalar=d.hud_aux_rsp_data;
   for(unsigned n=0;n<23;n++){tick();need(d.hud_aux_rsp_valid&&d.hud_aux_rsp_error==err&&d.hud_aux_rsp_data==scalar,"heldresponsescalar");for(unsigned i=0;i<4;i++)need(snapshot[i]==d.hud_aux_rsp_burst_data[i],"heldresponsewide");}d.hud_aux_rsp_ready=1;
  }
  auto e=response(false);if(!writing){need(e.aux_wide==v,"wideactualreadback");need(e.aux_data==v[0],"widescalarcompatibility");}return e;
 }

};

struct BurstStats{unsigned denied=0,keys=0,completed_words=0,held_responses=0,payload_mutations=0,aborts=0,early_drain=0,actual_writes=0,actual_reads=0,write_commands=0,write_beats=0;uint64_t cycles=0;};
static uint16_t pattern(unsigned i){return uint16_t((i*73u)^0x45a5u);}
static std::array<uint16_t,8> block(unsigned start){std::array<uint16_t,8> v{};for(unsigned i=0;i<8;i++)v[i]=pattern(start+i);return v;}
static BurstStats burst_suite(const char*path){
 std::cout<<"HUD_BURST_STAGE begin"<<std::endl;Sim s(path);BurstStats st;auto reject=[&](bool wr,uint32_t a,uint64_t gen,uint32_t fid,bool wb,bool rb,uint16_t mask){unsigned w=s.d.model_writes,r=s.d.model_reads,wc=s.d.model_write_commands,beats=s.d.model_write_bus_beats;auto v=block(0);s.raw_request(wr,a,gen,fid,wb,rb,mask,v);s.response(true);need(s.d.model_writes==w&&s.d.model_reads==r&&s.d.model_write_commands==wc&&s.d.model_write_bus_beats==beats,"deniedburstissuedphysicalcommand");st.denied++;};
 reject(true,cu70_map::HUD0_BASE,20,0,true,false,0xffff); // no active candidate
 s.prepare(20);st.keys++;unsigned base=s.base();std::cout<<"HUD_BURST_STAGE prepared"<<std::endl;
 reject(true,base,21,0,true,false,0xffff);reject(true,base,20,1,true,false,0xffff);
 unsigned other=base==cu70_map::HUD0_BASE?cu70_map::HUD1_BASE:cu70_map::HUD0_BASE;
 reject(true,other,20,0,true,false,0xffff);reject(true,base+1,20,0,true,false,0xffff);
 reject(false,base+1,20,0,false,true,0);reject(false,base+21116,20,0,false,true,0);
 reject(false,base+21120,20,0,false,true,0);reject(true,base+8,20,0,true,false,0xffff);
 reject(true,base,20,0,true,false,0x00ff);reject(true,base,20,0,true,true,0xffff);
 reject(true,base,20,0,false,true,0);reject(false,base,20,0,true,false,0xffff);
 reject(false,base,20,0,false,true,0xffff);reject(false,base,20,0,false,false,1);
 reject(true,base,20,0,false,false,0xffff);
 // Accepted payload survives producer mutation and a held completion. Every
 // remaining word is transferred through actual full-write requests.
 s.wide(true,base,20,block(0),true,true);st.held_responses++;st.payload_mutations++;
 need(s.d.model_writes==8&&s.d.model_write_commands==1&&s.d.model_write_bus_beats==8,"firstfullwriteexactcounts");
 reject(true,base,20,0,true,false,0xffff);reject(true,base+16,20,0,true,false,0xffff);
 for(unsigned at=8;at<21120;at+=8)s.wide(true,base+at,20,block(at));
 std::cout<<"HUD_UPLOAD_COUNTS words="<<s.d.model_writes<<" commands="<<s.d.model_write_commands<<" beats="<<s.d.model_write_bus_beats<<std::endl;need(s.d.model_writes==21120&&s.d.model_write_commands==2640&&s.d.model_write_bus_beats==21120,"completeburstuploadcounts");st.completed_words=21120;std::cout<<"HUD_BURST_STAGE uploaded"<<std::endl;
 reject(true,base+21112,20,0,true,false,0xffff);reject(true,base+21120,20,0,true,false,0xffff);
 // Both a cache-miss and immediately repeated cache-hit snapshot are held.
 s.wide(false,base,20,block(0),true,true);st.held_responses++;st.payload_mutations++;
 unsigned rd=s.d.model_reads;s.wide(false,base,20,block(0),true,true);st.held_responses++;st.payload_mutations++;
 need(s.d.model_reads==rd,"widecachehitissuedread");
 for(unsigned at=8;at<21120;at+=8)s.wide(false,base+at,20,block(at));
 need(s.d.model_reads==2640,"fullburstreadbackcommands");std::cout<<"HUD_BURST_STAGE readback"<<std::endl;s.abort_frame(20);st.aborts++;
 reject(true,base,20,0,true,false,0xffff);
 // Interrupt an accepted physical burst after its first actual word. A false
 // full-drain claim must fail, while the accepted BL8 still drains all beats.
 s.prepare(21);st.keys++;base=s.base();std::cout<<"HUD_BURST_STAGE abort-probe"<<std::endl;unsigned w=s.d.model_writes,wc=s.d.model_write_commands,beats=s.d.model_write_bus_beats;
 s.d.hud_aux_rsp_ready=0;s.raw_request(true,base,21,0,true,false,0xffff,block(0));
 for(unsigned n=0;s.d.model_writes==w;n++){need(n<2000,"physicalburstfirstbeatwait");s.tick();}
 need(s.d.model_writes==w+1,"firstbeatobservable");
 s.d.hud_drain_generation=21;s.d.hud_drain_frame_id=0;s.d.hud_drain_bank=s.d.candidate_bank;s.d.hud_drain_words=21120;s.d.hud_drain_success=1;for(unsigned i=0;i<4;i++)s.d.hud_drain_tag[i]=s.d.expected_hud_tag[i];s.d.hud_drain_valid=1;s.tick();s.d.hud_drain_valid=0;
 need(s.d.error&&s.d.error_code==0x71,"outstandingburstdrainclaimaccepted");st.early_drain++;
 s.abort_frame(21,false);st.aborts++;
 need(s.d.model_writes==w+8&&s.d.model_write_commands==wc+1&&s.d.model_write_bus_beats==beats+8,"acceptedburstnotdrainedexactly");
 for(unsigned i=0;i<8;i++){s.d.peek_address=base+i;s.d.eval();need(s.d.peek_data==pattern(i),"partialabortpayloadmismatch");}
 st.completed_words+=8;st.actual_writes=s.d.model_writes;st.actual_reads=s.d.model_reads;st.write_commands=s.d.model_write_commands;st.write_beats=s.d.model_write_bus_beats;st.cycles=s.cycles;return st;
}
struct LegacyStats{unsigned writes,reads;uint64_t cycles;};
static LegacyStats legacy_suite(const char*path){Sim s(path);s.d.packet_req_ready=1;uint32_t before=s.d.model_writes;
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
 std::cout<<"LEGACY_CONTROL_PASS keys=2 words=2 denied_writes=7 abort_drained=2 early_drain=1 cycles="<<s.cycles<<std::endl;
 return LegacyStats{s.d.model_writes,s.d.model_reads,s.cycles};
}
int main(int argc,char**argv){try{need(argc==2,"firstkeypacketargument");auto legacy=legacy_suite(argv[1]);auto b=burst_suite(argv[1]);

 std::cout<<"SYSTEM_CONTROL_PASS actual_keys_parsed="<<2+b.keys<<" completed_HUD_words="<<2+b.completed_words<<" legacy_denied_writes=7 denied_burst_requests="<<b.denied<<" abort_drained="<<2+b.aborts<<" early_HUD_drain_rejected="<<1+b.early_drain<<" accepted_frames=0 actual_writes="<<legacy.writes+b.actual_writes<<" actual_reads="<<legacy.reads+b.actual_reads<<" held_wide_responses="<<b.held_responses<<" accepted_payload_mutations="<<b.payload_mutations<<" burst_write_commands="<<b.write_commands<<" burst_write_bus_beats="<<b.write_beats<<" legacy_clocks="<<legacy.cycles<<" burst_clocks="<<b.cycles<<"\n";
 }catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}
