#include "Vcu71_direct_system_sim.h"
#include "verilated.h"
#include "/mnt/c/mb70/fpga/experiments/cu66-v70/memory/memory_map.hpp"
#include <algorithm>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <memory>
#include <stdexcept>
#include <vector>

namespace control {
static void need(bool b,const char*s){if(!b)throw std::runtime_error(s);}
struct Event{
 bool start=false,packet_request=false,packet_response=false,prepare=false,aux_request=false,aux_response=false,aux_error=false,command=false;
 uint16_t packet_address=0,aux_data=0;uint64_t packet_generation=0;uint32_t packet_sequence=0;unsigned opcode=0;
};
struct Sim{
 std::unique_ptr<VerilatedContext> c=std::make_unique<VerilatedContext>();Vcu71_direct_system_sim d{c.get()};
 uint64_t next_pixel=17029,cycles=0;bool packet_pending=false;uint16_t address=0;uint64_t generation=0;uint32_t sequence=0;
 std::vector<uint8_t> packet;
 explicit Sim(const char*path){std::ifstream f(path,std::ios::binary);need(bool(f),"packet open");packet={std::istreambuf_iterator<char>(f),{}};need(packet.size()>88&&packet.size()<=49152,"actualpacket");
  d.clk=0;d.read_clk=0;d.pixel_clk=0;d.pixel_reset_n=0;d.rst=1;d.abort_i=0;d.clear_fault=0;d.start_valid=0;d.packet_rsp_valid=0;d.hud_prepare_ready=0;d.hud_result_valid=0;d.hud_drain_valid=0;d.software_command_ready=0;d.software_ack_valid=0;d.hud_aux_req_valid=0;d.hud_aux_rsp_ready=1;d.diag_address=0;d.peek_address=0;d.eval();for(int i=0;i<8;i++)tick();d.rst=0;d.pixel_reset_n=1;for(int i=0;i<100;i++)tick();
 }
 void advance(uint64_t target){while(c->time()<target){uint64_t next=std::min(target,next_pixel);if(d.eventsPending())next=std::min(next,d.nextTimeSlot());need(next>=c->time(),"eventtime");c->timeInc(next-c->time());if(next==next_pixel){d.pixel_clk=!d.pixel_clk;next_pixel+=17029;}d.eval();}}
 Event tick(){need(cycles<1000000,"controlwatchdog");uint64_t t=c->time();
  d.packet_rsp_valid=packet_pending;if(packet_pending){d.packet_rsp_address=address;d.packet_rsp_generation=generation;d.packet_rsp_sequence=sequence;d.packet_rsp_data=packet.at(address);}d.eval();
  advance(t+2625);d.read_clk=1;d.eval();advance(t+5000);d.eval();
  Event e;e.start=d.start_valid&&d.start_ready;e.packet_request=d.packet_req_valid&&d.packet_req_ready;e.packet_response=d.packet_rsp_valid&&d.packet_rsp_ready;e.prepare=d.hud_prepare_valid&&d.hud_prepare_ready;
  e.packet_address=d.packet_req_address;e.packet_generation=d.packet_req_generation;e.packet_sequence=d.packet_req_sequence;
  e.aux_request=d.hud_aux_req_valid&&d.hud_aux_req_ready;e.aux_response=d.hud_aux_rsp_valid&&d.hud_aux_rsp_ready;e.aux_error=d.hud_aux_rsp_error;e.aux_data=d.hud_aux_rsp_data;
  e.command=d.software_command_valid&&d.software_command_ready;e.opcode=d.software_command_opcode;
  d.clk=1;d.eval();advance(t+7625);d.read_clk=0;d.eval();advance(t+10000);d.clk=0;d.eval();cycles++;
  if(e.packet_response)packet_pending=false;
  if(e.packet_request){need(!packet_pending,"multiplepacketrequests");packet_pending=true;address=e.packet_address;generation=e.packet_generation;sequence=e.packet_sequence;}
  return e;
 }
 void aux(bool writing,uint32_t addr,uint16_t data,bool error,uint64_t gen,uint32_t fid){d.hud_aux_generation=gen;d.hud_aux_frame_id=fid;d.hud_aux_req_valid=1;d.hud_aux_req_write=writing;d.hud_aux_req_addr=addr;d.hud_aux_req_data=data;while(!tick().aux_request){}d.hud_aux_req_valid=0;unsigned count=0;for(;;){auto e=tick();if(e.aux_response){need(e.aux_error==error,"auxerror");if(!writing&&!error)need(e.aux_data==data,"auxreadback");return;}need(++count<2000,"auxwait");}}
};
int run(int argc,char**argv){try{need(argc==2,"firstkeypacketargument");Sim s(argv[1]);s.d.packet_req_ready=1;uint32_t before=s.d.model_writes;
 s.aux(true,cu70_map::HUD0_BASE,0xaaaa,true,10,0);need(s.d.model_writes==before,"idlewriteescaped");
 s.d.start_generation=10;s.d.start_packet_bytes=uint32_t(s.packet.size());s.d.start_valid=1;while(!s.tick().start){}s.d.start_valid=0;s.d.hud_prepare_ready=1;while(!s.tick().prepare){}s.d.hud_prepare_ready=0;
 need(s.d.active_generation==10&&s.d.active_frame_id==0&&s.d.active_key,"actualparsedidentity");uint32_t base=s.d.candidate_bank==0?cu70_map::HUD0_BASE:s.d.candidate_bank==1?cu70_map::HUD1_BASE:cu70_map::HUD2_BASE;
 before=s.d.model_writes;s.aux(true,base,0x1234,false,10,0);s.aux(false,base,0x1234,false,10,0);need(s.d.model_writes==before+8,"writecompletioncount");
 s.aux(true,base,0x9876,true,11,0);s.aux(true,base,0x9876,true,10,1);s.aux(true,cu70_map::CANONICAL0_BASE,0x9876,true,10,0);s.aux(true,base,0x9876,true,10,0);s.aux(true,base+2,0x9876,true,10,0);
 need(s.d.model_writes==before+8,"invalidoroutoforderwriteescaped");s.aux(true,base+1,0x5678,false,10,0);s.aux(false,base+1,0x5678,false,10,0);
 s.d.peek_address=base;s.d.eval();need(s.d.peek_data==0x1234,"readonlymodelpeek");s.d.peek_address=base+1;s.d.eval();need(s.d.peek_data==0x5678,"readonlymodelpeek2");need(s.d.write_event_sequence==s.d.model_writes,"actualwriteeventcount");
 s.d.abort_i=1;s.tick();s.d.abort_i=0;s.d.software_command_ready=1;for(;;){auto e=s.tick();if(e.command){need(e.opcode==6,"abortcommand");break;}}
 s.d.software_command_ready=0;s.d.software_ack_valid=1;s.d.software_ack_opcode=6;s.d.software_ack_generation=10;s.d.software_ack_frame_id=0;s.d.software_ack_success=1;s.tick();s.d.software_ack_valid=0;
 for(unsigned n=0;s.d.busy;n++){need(n<10000,"abortdrain");s.tick();}
 need(!s.d.reference_valid&&!s.d.front_valid&&!s.d.lcd_front_valid&&s.d.accepted_count==0&&!s.d.memory_tile_busy&&!s.d.cache_prepare_busy,"partialtransactionpublished");
 s.aux(true,base+2,0x7777,true,10,0);need(s.d.model_writes==before+16,"postabortwriteescaped");
 // A falsely claimed full transfer must fail the hardware coverage fence.
 s.d.start_generation=11;s.d.start_valid=1;while(!s.tick().start){}s.d.start_valid=0;s.d.hud_prepare_ready=1;while(!s.tick().prepare){}s.d.hud_prepare_ready=0;
 s.d.hud_drain_generation=11;s.d.hud_drain_frame_id=0;s.d.hud_drain_bank=s.d.candidate_bank;s.d.hud_drain_words=21120;s.d.hud_drain_success=1;
 for(unsigned i=0;i<4;i++)s.d.hud_drain_tag[i]=s.d.expected_hud_tag[i];
 s.d.hud_drain_valid=1;s.tick();s.d.hud_drain_valid=0;need(s.d.error&&s.d.error_code==0x71,"incompletetransferaccepted");
 s.d.software_command_ready=1;for(;;){auto e=s.tick();if(e.command){need(e.opcode==6,"failedtransferabortcommand");break;}}
 s.d.software_command_ready=0;s.d.software_ack_valid=1;s.d.software_ack_opcode=6;s.d.software_ack_generation=11;s.d.software_ack_frame_id=0;s.d.software_ack_success=1;s.tick();s.d.software_ack_valid=0;
 for(unsigned n=0;s.d.busy;n++){need(n<10000,"faultdrain");s.tick();}
 need(!s.d.reference_valid&&!s.d.front_valid&&!s.d.lcd_front_valid&&s.d.accepted_count==0&&s.d.model_writes==before+16,"failedtransferpublished");
 std::cout<<"SYSTEM_CONTROL_PASS actual_keys_parsed=2 completed_HUD_words=2 denied_writes=7 abort_drained=2 early_HUD_drain_rejected=1 accepted_frames=0 actual_writes="<<s.d.model_writes<<" actual_reads="<<s.d.model_reads<<" refreshes="<<s.d.model_refreshes<<" clocks="<<s.cycles<<"\n";
 return 0;}catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}

}

#include "Vcu71_direct_system_sim.h"
#include "verilated.h"
#include "/mnt/c/mb70/experiments/cu66-native-v69/decoder.hpp"
#include "/mnt/c/mb70/fpga/experiments/cu66-v69/hud-partition/hud_gate.hpp"
#include "/mnt/c/mb70/fpga/experiments/cu66-v70/memory/memory_map.hpp"
#include <algorithm>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <memory>
#include <stdexcept>


namespace frames {
static void need(bool b,const std::string&s){if(!b)throw std::runtime_error(s);}
static cu66::Bytes load(const std::filesystem::path&p){std::ifstream f(p,std::ios::binary);need(bool(f),"packet open");return {std::istreambuf_iterator<char>(f),{}};}
template<class W>static void put_tag(W&w,const cu66::Tag&t){for(unsigned i=0;i<4;i++){uint32_t v=0;for(unsigned j=0;j<4;j++)v=(v<<8)|t[4*i+j];w[3-i]=v;}}
static unsigned hud_base(unsigned bank){need(bank<3,"HUD bank bound");return bank==0?cu70_map::HUD0_BASE:bank==1?cu70_map::HUD1_BASE:cu70_map::HUD2_BASE;}
struct Event{
 bool start=false,packet_req=false,packet_rsp=false,prepare=false,result=false,drain=false,aux_req=false,aux_rsp=false,aux_error=false,command=false,ack=false;
 unsigned packet_address=0,packet_sequence=0,aux_data=0,opcode=0,fid=0,rid=0,bank=0,hud_address=0,hud_length=0;
 uint64_t packet_generation=0,generation=0;bool key=false;
};
struct Sim{
 std::unique_ptr<VerilatedContext> c=std::make_unique<VerilatedContext>();Vcu71_direct_system_sim d{c.get()};
 uint64_t next_pixel=17029,cycles=0,generation=0;
 cu66::Bytes packet;cu66_partition::HudGate hud;
 std::shared_ptr<const cu66_partition::HudCache> candidate;
 std::vector<cu66::Patch> readback;std::vector<uint16_t> words;
 std::map<uint64_t,std::shared_ptr<const cu66::Frame>> golds;
 bool packet_pending=false,prepared=false,result_sent=false,drain_sent=false,aux_pending=false,software_pending=false;
 bool software_success=false,drop_ack=false,did_drop_ack=false;
 unsigned packet_address=0,packet_sequence=0,hud_bank=0,word_cursor=0,read_cursor=0,soft_op=0,soft_fid=0,soft_calls=0;
 uint64_t packet_generation=0,soft_gen=0;
 uint64_t good_lines=0,black_lines=0,pixels=0;
 unsigned line_matches=0,line_zeros=0,line_pixels=0,last_rgb_slot=0,last_write_sequence=0;uint64_t line_generation=0;
 explicit Sim(){d.clk=0;d.read_clk=0;d.pixel_clk=0;d.pixel_reset_n=0;d.rst=1;d.abort_i=0;d.clear_fault=0;d.start_valid=0;d.packet_req_ready=1;d.packet_rsp_valid=0;d.hud_prepare_ready=0;d.hud_result_valid=0;d.hud_drain_valid=0;d.software_command_ready=0;d.software_ack_valid=0;d.hud_aux_req_valid=0;d.hud_aux_rsp_ready=1;d.diag_address=0;d.peek_address=0;d.eval();for(int i=0;i<8;i++)tick();d.rst=0;d.pixel_reset_n=1;for(int i=0;i<100;i++)tick();}

 unsigned timeline_stage=999,timeline_presented=0;
 uint64_t timeline_visible_generation=0,timeline_raster_generation=0;
 unsigned timeline_raster_lines=0,timeline_raster_black=0;bool timeline_raster=false;
 void timeline_cycle(){
  if(unsigned(d.stage)!=timeline_stage){std::cout<<"DY71_STAGE cycle="<<cycles<<" generation="<<d.active_generation<<" fid="<<d.active_frame_id<<" stage="<<unsigned(d.stage)<<std::endl;timeline_stage=d.stage;}
  if(d.lcd_presented_count!=timeline_presented){std::cout<<"DY71_PRESENTED cycle="<<cycles<<" generation="<<d.lcd_front_generation<<" fid="<<d.lcd_front_frame_id<<" count="<<d.lcd_presented_count<<std::endl;timeline_presented=d.lcd_presented_count;}
 }

 bool fence_last_idle=false;uint64_t fence_idle_changed=0,fence_idle_transitions=0,fence_idle_cycles=0;unsigned fence_pending_logs=0,fence_pulses=0;
 void fence_cycle(){
  if(d.lcd_scanout_drained)fence_idle_cycles++;
  if(bool(d.lcd_scanout_drained)!=fence_last_idle){fence_idle_changed=cycles;fence_idle_transitions++;fence_last_idle=d.lcd_scanout_drained;
   if(d.lcd_pending&&fence_pending_logs<64){std::cout<<"DY71_IDLE_FENCE cycle="<<cycles<<" idle="<<unsigned(d.lcd_scanout_drained)<<" pending="<<unsigned(d.lcd_pending)<<" active_generation="<<d.active_generation<<" front_generation="<<d.lcd_front_generation<<std::endl;fence_pending_logs++;}}
  if(d.lcd_frame_boundary){fence_pulses++;std::cout<<"DY71_FRAME_FENCE cycle="<<cycles<<" idle="<<unsigned(d.lcd_scanout_drained)<<" last_idle_change="<<fence_idle_changed<<" pending="<<unsigned(d.lcd_pending)<<" active_generation="<<d.active_generation<<" front_generation="<<d.lcd_front_generation<<std::endl;}
 }
 struct ProfileSnapshot{uint64_t gen=0;unsigned stage=0,fs=0,ts=0,flags=0,events=0;uint32_t idle=0,lcdidle=0,bgidle=0;unsigned rf=0,as=0,cs=0,bo=0,bs=0,pt=0;uint32_t tid=0,ttag=0,glcd=0,gbg=0;uint64_t tgen=0;};
 static constexpr unsigned PB=24;
 static constexpr const char* profile_names[PB]={"canonical_done_HUD_tail","canonical_done_memory_drain","owner_transition","base_idle_before_good","plane_wait","plane_configure","entropy_scatter_wait","tile_accept","quant_request","quant_wait","dequant_input","dequant_output","idct_compute_pipeline","idct_done_reference_wait","idct_done_other_backpressure","idct_recon_transfer","recon_output","write_both_blocked","write_memory_blocked","write_rows_hash_blocked","write_transfer","hash_final_tail","base_result","unexpected"};
 static constexpr unsigned PO=11;
 static constexpr const char* overlap_names[PO]={"entropy_busy","entropy_output_stall","idct_active","reference_pending","write_pending","hash_busy","sha_round","rows_to_hash_stall","packet_pending","quant_pending","rows_write_busy"};
 static constexpr unsigned overlap_bits[PO]={17,30,26,7,8,18,29,31,20,21,28};
 struct Latency{bool pending=false;uint64_t at=0,count=0,sum=0,max=0;void sample(bool req,bool rsp,uint64_t cycle){if(rsp){need(pending,"profile unowned completion");auto n=cycle-at;count++;sum+=n;max=std::max(max,n);pending=false;}if(req){need(!pending,"profile multiple outstanding");pending=true;at=cycle;}}};
 ProfileSnapshot ps;bool profile_active=false;uint64_t profile_gen=0,profile_start=0,profile_startup=0;
 std::array<uint64_t,12> profile_stage{},profile_stage_reserved{};
 std::array<uint64_t,PB> profile_bin{},profile_bin_reserved{};
 std::array<uint64_t,PO> profile_overlap{},profile_base_overlap{};
 Latency profile_ref,profile_write,profile_idct;
 uint64_t profile_reserved=0,profile_lcd_reserved=0,profile_bg_reserved=0,profile_idct_output=0,profile_entropy_planes=0,profile_entropy_decisions=0,profile_entropy_renorm=0,profile_entropy_reads=0,profile_entropy_stalls=0;
 static bool pf(unsigned f,unsigned bit){return(f>>bit)&1u;}
 unsigned profile_classify()const{
  unsigned f=ps.flags;
  if(pf(f,0)){if(!pf(f,1)||!pf(f,2))return 0;if(!pf(f,3))return 1;return 2;}
  if(ps.fs==0)return 3;if(ps.fs==1)return 4;if(ps.fs==2)return 5;
  if(ps.fs==4)return 21;if(ps.fs==5)return 22;if(ps.fs!=3)return 23;
  switch(ps.ts){case 0:return pf(f,15)?7:6;case 1:return 8;case 2:return 9;case 3:return 10;case 4:return 11;
   case 5:if(!pf(f,9))return 12;if(!pf(f,10)){if(!pf(f,4)&&!pf(f,5)&&!pf(f,6))return 13;return 14;}return 15;
   case 6:return 16;case 7:{bool m=pf(f,11)||pf(f,12),h=pf(f,13)||pf(f,14);if(!m&&!h)return 17;if(!m)return 18;if(!h)return 19;return 20;}default:return 23;}
 }
 void profile_before(){ps={d.active_generation,unsigned(d.stage),unsigned(d.prof_fs),unsigned(d.prof_ts),unsigned(d.prof_flags),unsigned(d.prof_events),d.group_idle,d.group_lcd_idle,d.group_bg_idle};ps.rf=d.prof_ref_flags;ps.as=d.prof_adapter_state;ps.cs=d.prof_controller_state;ps.bo=d.prof_bridge_owner;ps.bs=d.prof_bridge_state;ps.pt=d.prof_physical_flags;ps.tid=d.prof_current_tile;ps.ttag=d.prof_adapter_tile;ps.tgen=d.prof_adapter_generation;ps.glcd=d.group_lcd_count;ps.gbg=d.group_bg_count;}
 template<size_t N>static uint64_t profile_sum(const std::array<uint64_t,N>&a){uint64_t n=0;for(auto x:a)n+=x;return n;}

 static constexpr unsigned PR=7,PA=7;
 static constexpr const char* ref_names[PR]={"not_offered","admission_valid_not_ready","accepted_inflight","return_held","return_transfer","request_transfer","other"};
 std::array<uint64_t,PR> reference_bins{},reference_reserved{},reference_lcd_reserved{},reference_bg_reserved{},reference_write_pending{},reference_maxrun{};
 std::array<std::array<uint64_t,PA>,PR> reference_adapter{};
 std::array<std::array<uint64_t,16>,PR> reference_controller{};
 uint64_t admission_previous_write=0,admission_other=0,physical_lcd=0,physical_bg=0,physical_read=0,physical_write=0;unsigned reference_last=PR;uint64_t reference_run=0;
 struct RefExample{uint64_t cycle,generation;uint32_t current,adapter;unsigned state,flags;};std::vector<RefExample>reference_examples;
 void profile_ref_reset(){reference_bins={};reference_reserved={};reference_lcd_reserved={};reference_bg_reserved={};reference_write_pending={};reference_maxrun={};reference_adapter={};reference_controller={};admission_previous_write=admission_other=physical_lcd=physical_bg=physical_read=physical_write=0;reference_last=PR;reference_run=0;reference_examples.clear();}
 void profile_ref_gap(){if(reference_last<PR)reference_maxrun[reference_last]=std::max(reference_maxrun[reference_last],reference_run);reference_last=PR;reference_run=0;}
 unsigned profile_ref_class()const{
  auto f=ps.rf;
  if(pf(f,3)&&!pf(f,5))return 6;
  if((pf(f,3)&&!pf(f,4))||(pf(f,12)&&!pf(f,13))||(pf(f,7)&&!pf(f,8)))return 3;
  if(pf(f,3)&&pf(f,4)&&pf(f,5))return 4;
  if(pf(f,2))return 2;
  if(pf(f,0))return pf(f,1)?5:1;
  return 0;
 }
 void profile_physical_sample(){
  uint32_t l=uint32_t(d.group_lcd_count-ps.glcd),b=uint32_t(d.group_bg_count-ps.gbg);bool accepted=ps.pt&1;
  need(l<=1&&b<=1&&l+b==unsigned(accepted),"profile physical/group acceptance conservation");
  if(accepted){need((ps.bo==2)==bool(l),"profile physical owner/class identity");physical_lcd+=l;physical_bg+=b;if(ps.pt&2)physical_write++;else physical_read++;}
 }
 void profile_reference_sample(unsigned bin,uint32_t idle,uint32_t li,uint32_t bi){
  if(bin!=13){profile_ref_gap();return;}
  unsigned sub=profile_ref_class();need(sub<PR&&ps.as<4&&ps.cs<15,"profile unknown reference/controller phase");reference_bins[sub]++;reference_reserved[sub]+=idle;reference_lcd_reserved[sub]+=li;reference_bg_reserved[sub]+=bi;if(pf(ps.rf,15))reference_write_pending[sub]++;
  unsigned adapter=ps.as==0?0:(pf(ps.rf,14)?ps.as:3+ps.as);reference_adapter[sub][adapter]++;reference_controller[sub][ps.cs]++;
  if(reference_last!=sub){profile_ref_gap();reference_last=sub;reference_run=1;}else reference_run++;
  if(sub==1){
   if(ps.as!=0&&pf(ps.rf,14)&&pf(ps.rf,15)){need(ps.tgen==profile_gen&&ps.ttag!=ps.tid,"profile admission writeback identity not previous tile");admission_previous_write++;}
   else admission_other++;
   if(reference_run==1&&reference_examples.size()<8)reference_examples.push_back({cycles-1,ps.tgen,ps.tid,ps.ttag,ps.as,ps.rf});
  }
 }
 void profile_ref_assert(){
  profile_ref_gap();need(profile_sum(reference_bins)==profile_bin[13],"profile reference subdivision conservation");need(reference_bins[6]==0,"profile reference phase other/mismatch inaccessible");
  need(profile_sum(reference_reserved)==profile_bin_reserved[13],"profile reference reserved conservation");need(admission_previous_write+admission_other==reference_bins[1],"profile admission identity partition");
  for(unsigned i=0;i<PR;i++){need(profile_sum(reference_adapter[i])==reference_bins[i]&&profile_sum(reference_controller[i])==reference_bins[i],"profile adapter/controller crossbin conservation");need(reference_reserved[i]<=reference_bins[i]&&reference_write_pending[i]<=reference_bins[i],"profile reference overlap bound");need(reference_reserved[i]==reference_lcd_reserved[i]+reference_bg_reserved[i],"profile reference reserved class conservation");}
 }
 void profile_ref_print(){
  auto named=[&](const char*name,const auto&a){std::cout<<",\""<<name<<"\":{";for(unsigned i=0;i<PR;i++)std::cout<<(i?",":"")<<"\""<<ref_names[i]<<"\":"<<a[i];std::cout<<"}";};
  named("reference_block_bins",reference_bins);named("reference_block_reserved",reference_reserved);named("reference_block_LCD_reserved",reference_lcd_reserved);named("reference_block_BG_reserved",reference_bg_reserved);named("reference_block_write_pending",reference_write_pending);named("reference_block_max_run",reference_maxrun);
  auto matrix=[&](const char*name,const auto&a){std::cout<<",\""<<name<<"\":[";for(unsigned i=0;i<PR;i++){std::cout<<(i?",":"")<<"[";for(unsigned k=0;k<a[i].size();k++)std::cout<<(k?",":"")<<a[i][k];std::cout<<"]";}std::cout<<"]";};matrix("reference_adapter_matrix",reference_adapter);matrix("reference_controller_state_matrix",reference_controller);
  std::cout<<",\"admission_previous_write_cycles\":"<<admission_previous_write<<",\"admission_other_cycles\":"<<admission_other<<",\"physical_accepted\":{\"LCD\":"<<physical_lcd<<",\"BG\":"<<physical_bg<<",\"read\":"<<physical_read<<",\"write\":"<<physical_write<<"},\"admission_examples\":[";
  for(unsigned i=0;i<reference_examples.size();i++){auto e=reference_examples[i];std::cout<<(i?",":"")<<"{\"cycle\":"<<e.cycle<<",\"generation\":"<<e.generation<<",\"current_tile_tag\":"<<e.current<<",\"adapter_tile_tag\":"<<e.adapter<<",\"adapter_state\":"<<e.state<<",\"raw_reference_flags\":"<<e.flags<<"}";}std::cout<<"]";
 }
 void profile_print(){
  profile_ref_assert();
  auto base=profile_stage[5];need(profile_sum(profile_bin)==base,"profile BASE bin conservation");need(profile_bin[23]==0,"profile inaccessible or unexpected BASE phase");
  need(profile_sum(profile_stage)+profile_startup==cycles-profile_start,"profile transaction clock conservation");
  need(profile_sum(profile_stage_reserved)<=profile_reserved,"profile reservation phase conservation");
  need(profile_sum(profile_bin_reserved)==profile_stage_reserved[5],"profile BASE reservation conservation");
  need(profile_reserved==profile_lcd_reserved+profile_bg_reserved,"profile reserved class conservation");
  for(unsigned i=0;i<PB;i++)need(profile_bin_reserved[i]<=profile_bin[i],"profile reserved bin exceeds phase");
  for(unsigned i=0;i<PO;i++){need(profile_base_overlap[i]<=base,"profile overlap exceeds BASE");need(profile_overlap[i]<=profile_sum(profile_stage),"profile overlap exceeds transaction");}
  need(!profile_ref.pending&&!profile_write.pending&&!profile_idct.pending,"profile pending operation at committed end");
  need(profile_ref.sum==profile_overlap[3],"profile reference latency/pending conservation");need(profile_write.sum==profile_overlap[4],"profile write latency/pending conservation");
  need(profile_idct.sum==profile_overlap[2]+profile_idct_output,"profile IDCT compute/output latency conservation");
  need(profile_overlap[6]==uint64_t(d.prof_hash_rounds),"profile SHA round conservation");
  need(profile_write.count==d.prof_base_tiles&&profile_idct.count==d.prof_base_tiles,"profile canonical tile count conservation");
  std::cout<<"DY71_PROFILE_JSON {\"generation\":"<<profile_gen<<",\"frame_id\":"<<d.active_frame_id<<",\"transaction_cycles\":"<<cycles-profile_start<<",\"startup_cycles\":"<<profile_startup<<",\"BASE_cycles\":"<<base;
  std::cout<<",\"stages\":[";for(unsigned i=0;i<12;i++)std::cout<<(i?",":"")<<profile_stage[i];std::cout<<"],\"reserved_by_stage\":[";for(unsigned i=0;i<12;i++)std::cout<<(i?",":"")<<profile_stage_reserved[i];std::cout<<"]";
  auto named=[&](const char*key,const auto&a,const auto&names){std::cout<<",\""<<key<<"\":{";for(unsigned i=0;i<a.size();i++)std::cout<<(i?",":"")<<"\""<<names[i]<<"\":"<<a[i];std::cout<<"}";};
  named("BASE_bins",profile_bin,profile_names);named("BASE_reserved",profile_bin_reserved,profile_names);named("overlap_total",profile_overlap,overlap_names);named("BASE_overlap",profile_base_overlap,overlap_names);
  auto latency=[&](const char*name,const Latency&l){std::cout<<",\""<<name<<"\":{\"count\":"<<l.count<<",\"sum_cycles\":"<<l.sum<<",\"max_cycles\":"<<l.max<<"}";};latency("reference_latency",profile_ref);latency("canonical_write_latency",profile_write);latency("idct_input_to_consumed_output_latency",profile_idct);
  profile_ref_print();
  std::cout<<",\"reserved_cycles\":"<<profile_reserved<<",\"LCD_reserved_cycles\":"<<profile_lcd_reserved<<",\"BG_reserved_cycles\":"<<profile_bg_reserved;
  std::cout<<",\"receiver_clock\":"<<d.prof_clock<<",\"base_at\":"<<d.prof_base_at<<",\"hud_at\":"<<d.prof_hud_at<<",\"prepared_at\":"<<d.prof_prepared_at<<",\"base_cycle_counter\":"<<d.prof_base_cycles<<",\"tiles\":"<<d.prof_base_tiles<<",\"hash_rounds\":"<<d.prof_hash_rounds<<",\"hash_blocks\":"<<d.prof_hash_blocks;
  std::cout<<",\"entropy\":{\"planes\":"<<profile_entropy_planes<<",\"decisions\":"<<profile_entropy_decisions<<",\"renormalizations\":"<<profile_entropy_renorm<<",\"memory_reads\":"<<profile_entropy_reads<<",\"output_stall_cycles\":"<<profile_entropy_stalls<<"},\"conservation\":\"PASS\"}"<<std::endl;
 }
 void profile_after(){
  uint32_t idle=uint32_t(d.group_idle-ps.idle),li=uint32_t(d.group_lcd_idle-ps.lcdidle),bi=uint32_t(d.group_bg_idle-ps.bgidle);need(idle<=1&&li<=1&&bi<=1&&idle==li+bi,"profile reservation counter step");
  if(d.active_generation!=profile_gen&&d.stage!=0){need(!profile_active,"profile generation replaced live observation");profile_active=true;profile_gen=d.active_generation;profile_start=cycles-1;profile_startup=1;profile_stage={};profile_stage_reserved={};profile_bin={};profile_bin_reserved={};profile_overlap={};profile_base_overlap={};profile_ref={};profile_write={};profile_idct={};profile_reserved=idle;profile_lcd_reserved=li;profile_bg_reserved=bi;profile_idct_output=0;profile_entropy_planes=profile_entropy_decisions=profile_entropy_renorm=profile_entropy_reads=profile_entropy_stalls=0;profile_ref_reset();profile_physical_sample();return;}
  if(!profile_active)return;
  profile_physical_sample();
  need(ps.gen==profile_gen&&ps.stage>0&&ps.stage<12,"profile lost active generation/phase");profile_stage[ps.stage]++;profile_stage_reserved[ps.stage]+=idle;profile_reserved+=idle;profile_lcd_reserved+=li;profile_bg_reserved+=bi;
  for(unsigned i=0;i<PO;i++)if(pf(ps.flags,overlap_bits[i])){profile_overlap[i]++;if(ps.stage==5)profile_base_overlap[i]++;}
  if(pf(ps.flags,9))profile_idct_output++;
  if(ps.stage==5){unsigned bin=profile_classify();profile_bin[bin]++;profile_bin_reserved[bin]+=idle;profile_reference_sample(bin,idle,li,bi);}else profile_ref_gap();
  auto ev=[&](unsigned bit){return(ps.events>>bit)&1u;};profile_ref.sample(ev(0),ev(1),cycles-1);profile_write.sample(ev(2),ev(3),cycles-1);profile_idct.sample(ev(4),ev(5),cycles-1);
  if(ev(8)){profile_entropy_planes++;profile_entropy_decisions+=d.prof_entropy_decisions;profile_entropy_renorm+=d.prof_entropy_renorm;profile_entropy_reads+=d.prof_entropy_reads;profile_entropy_stalls+=d.prof_entropy_stalls;}
  if(d.stage==0){profile_print();profile_active=false;}
 }

 void pixel_check(){
  if(!d.data_enable||!d.lcd_front_valid)return;
  auto f=golds.find(d.lcd_front_generation);need(f!=golds.end(),"scanout generation lacks scoreboard");
  unsigned x=d.physical_x,y=d.physical_y;need(x<480&&y<800,"physical raster bounds");
  if(x==0&&y==0){timeline_raster=true;timeline_raster_generation=d.lcd_front_generation;timeline_raster_lines=timeline_raster_black=0;}
  if(timeline_raster)need(d.lcd_front_generation==timeline_raster_generation,"generation changed inside tracked raster");
  if(x==0&&y==40&&timeline_visible_generation!=d.lcd_front_generation){timeline_visible_generation=d.lcd_front_generation;std::cout<<"DY71_FIRST_CANVAS cycle="<<cycles<<" generation="<<d.lcd_front_generation<<" fid="<<d.lcd_front_frame_id<<std::endl;}

  uint16_t expected=0;if(y>=40&&y<760)expected=f->second->display[x*720+y-40];
  uint16_t actual=uint16_t(((d.red>>3)<<11)|((d.green>>2)<<5)|(d.blue>>3));
  if(x==0){line_matches=line_zeros=line_pixels=0;line_generation=d.lcd_front_generation;}
  need(line_generation==d.lcd_front_generation,"generation changed inside active line");
  line_matches+=actual==expected;line_zeros+=actual==0;line_pixels++;pixels++;
  if(x==479){need(line_pixels==480,"partial scanout line");need(line_matches==480||line_zeros==480,"corrupted/mixed scanout line");if(line_matches==480)good_lines++;else black_lines++;
   if(timeline_raster){timeline_raster_lines++;timeline_raster_black+=line_matches!=480;if(y==799){need(timeline_raster_lines==800,"tracked incomplete raster");std::cout<<"DY71_RASTER cycle="<<cycles<<" generation="<<timeline_raster_generation<<" fid="<<d.lcd_front_frame_id<<" lines="<<timeline_raster_lines<<" black_lines="<<timeline_raster_black<<std::endl;timeline_raster=false;}}
}
 }
 void advance(uint64_t target){while(c->time()<target){uint64_t n=std::min(target,next_pixel);if(d.eventsPending())n=std::min(n,d.nextTimeSlot());need(n>=c->time(),"simulation event in past");c->timeInc(n-c->time());bool rising=false;if(n==next_pixel){d.pixel_clk=!d.pixel_clk;rising=d.pixel_clk;next_pixel+=17029;}d.eval();if(rising)pixel_check();}}
 void drive(){
  d.packet_rsp_valid=packet_pending;if(packet_pending){d.packet_rsp_address=packet_address;d.packet_rsp_generation=packet_generation;d.packet_rsp_sequence=packet_sequence;d.packet_rsp_data=packet.at(packet_address);}
  d.hud_prepare_ready=!prepared;d.hud_result_valid=prepared&&!result_sent;d.hud_result_generation=generation;d.hud_result_frame_id=d.active_frame_id;d.hud_result_reference_id=d.active_reference_id;d.hud_result_success=bool(candidate);d.hud_result_words=21120;put_tag(d.hud_result_tag,candidate?candidate->tag:cu66::Tag{});
  d.hud_aux_generation=generation;d.hud_aux_frame_id=d.active_frame_id;
  bool transfer=prepared&&result_sent&&candidate;
  d.hud_aux_req_valid=transfer&&!aux_pending&&(word_cursor<words.size()||read_cursor<words.size());
  d.hud_aux_req_write=word_cursor<words.size();
  d.hud_aux_req_addr=hud_base(hud_bank)+(d.hud_aux_req_write?word_cursor:read_cursor);
  d.hud_aux_req_data=d.hud_aux_req_write&&word_cursor<words.size()?words[word_cursor]:0;
  d.hud_drain_valid=transfer&&!drain_sent&&!aux_pending&&word_cursor==21120&&read_cursor==21120;
  d.hud_drain_generation=generation;d.hud_drain_frame_id=d.active_frame_id;d.hud_drain_bank=hud_bank;d.hud_drain_words=21120;d.hud_drain_success=1;
  if(d.hud_drain_valid)put_tag(d.hud_drain_tag,cu66::hud_tag(readback));
  d.software_command_ready=!software_pending;d.software_ack_valid=software_pending;d.software_ack_opcode=soft_op;d.software_ack_generation=soft_gen;d.software_ack_frame_id=soft_fid;d.software_ack_success=software_success;
 }
 Event tick(){need(cycles<300000000,"system watchdog");drive();d.eval();uint64_t t=c->time();advance(t+2625);d.read_clk=1;d.eval();advance(t+5000);d.eval();
  Event e;e.start=d.start_valid&&d.start_ready;e.packet_req=d.packet_req_valid&&d.packet_req_ready;e.packet_rsp=d.packet_rsp_valid&&d.packet_rsp_ready;e.prepare=d.hud_prepare_valid&&d.hud_prepare_ready;e.result=d.hud_result_valid&&d.hud_result_ready;e.drain=d.hud_drain_valid&&d.hud_drain_ready;e.aux_req=d.hud_aux_req_valid&&d.hud_aux_req_ready;e.aux_rsp=d.hud_aux_rsp_valid&&d.hud_aux_rsp_ready;e.aux_data=d.hud_aux_rsp_data;e.aux_error=d.hud_aux_rsp_error;e.command=d.software_command_valid&&d.software_command_ready;e.ack=d.software_ack_valid&&d.software_ack_ready;
  e.packet_address=d.packet_req_address;e.packet_generation=d.packet_req_generation;e.packet_sequence=d.packet_req_sequence;e.generation=d.active_generation;e.fid=d.active_frame_id;e.rid=d.active_reference_id;e.key=d.active_key;e.bank=d.candidate_bank;e.hud_address=d.hud_address;e.hud_length=d.hud_bytes;e.opcode=d.software_command_opcode;
  profile_before();
  d.clk=1;d.eval();advance(t+7625);d.read_clk=0;d.eval();advance(t+10000);d.clk=0;d.eval();cycles++;timeline_cycle();fence_cycle();profile_after();
  if(e.packet_rsp)packet_pending=false;
  if(e.packet_req){need(!packet_pending,"multiple packet requests");packet_pending=true;packet_address=e.packet_address;packet_generation=e.packet_generation;packet_sequence=e.packet_sequence;need(packet_address<packet.size(),"packet address outside immutable stage");}
  if(e.prepare){auto r=hud.prepare(e.generation,e.fid,e.rid,e.key,cu66::View(packet).sub(e.hud_address,e.hud_length));need(r==cu66_partition::Reply::Accepted,"actual HUD semantic preparation rejected");candidate=hud.read_candidate(e.generation,e.fid);need(candidate!=nullptr,"owned HUD candidate");prepared=true;hud_bank=e.bank;words.clear();for(auto&p:candidate->patches)words.insert(words.end(),p.words.begin(),p.words.end());need(words.size()==21120,"exact HUD words");readback=candidate->patches;for(auto&p:readback)std::fill(p.words.begin(),p.words.end(),0);}
  if(e.result)result_sent=true;
  if(e.aux_req){need(!aux_pending,"multiple HUD memory transactions");aux_pending=true;}
  if(e.aux_rsp){need(aux_pending&&!e.aux_error,"actual HUD memory transaction error");aux_pending=false;if(word_cursor<21120)word_cursor++;else{unsigned at=0;for(auto&p:readback){if(read_cursor<at+p.words.size()){p.words[read_cursor-at]=uint16_t(e.aux_data);break;}at+=p.words.size();}read_cursor++;}}
  if(e.drain){need(cu66::hud_tag(readback)==candidate->tag,"actual functional HUD readback tag");need(hud.acknowledge_external_write_drain(e.generation,e.fid,21120,cu66::hud_tag(readback)),"HUD semantic transfer fence");drain_sent=true;}
  if(e.ack)software_pending=false;
  if(e.command){need(!software_pending,"multiple software decisions");soft_op=e.opcode;soft_gen=e.generation;soft_fid=e.fid;need(e.opcode==5,"unexpected abort in positive full system run");software_success=hud.commit(e.generation,e.fid);need(software_success,"root commit disagrees with processor state");soft_calls++;if(drop_ack&&!did_drop_ack)did_drop_ack=true;else software_pending=true;}
  return e;
 }
 uint16_t peek(unsigned address){need(address<(1u<<24)&&cu70_map::allowed(address),"peek map");d.peek_address=address;d.eval();return d.peek_data;}
 void verify(std::shared_ptr<const cu66::Frame>gold){
  need(d.reference_valid&&d.reference_frame_id==gold->id,"stored accepted reference identity");unsigned base=cu70_map::canonical_base(d.reference_bank);
  std::array<cu66::Bytes,3> p;for(unsigned a=0;a<3;a++){unsigned n=a?86400:345600,off=a==0?0:a==1?172800:216000;p[a].resize(n);for(unsigned i=0;i<n/2;i++){unsigned width=a?360:720,x=(i*2)%width,y=(i*2)/width;unsigned addr=base+off+((y/8)*(width/8)+x/8)*32+(y%8)*4+(x%8)/2;auto w=peek(addr);p[a][i*2]=uint8_t(w);p[a][i*2+1]=uint8_t(w>>8);}need(p[a]==gold->planes[a],"full command-memory canonical plane mismatch");}
  need(cu66::canonical_tag(p)==gold->canonical_tag,"canonical memory full tag");
  need(d.rgb_completed_writes==0,"DY71 emitted RGB burst write");
  need(d.profile_magic==0x44593731&&d.profile_abi==0x10000&&d.profile_capabilities==15,"DY71 profile identity");

 }
 void run(cu66::Bytes bytes,std::shared_ptr<const cu66::Frame>gold,bool lost_ack=false){
  while(!d.start_ready)tick();generation++;packet=std::move(bytes);golds[generation]=gold;prepared=result_sent=drain_sent=false;aux_pending=false;candidate=nullptr;word_cursor=read_cursor=0;soft_calls=0;drop_ack=lost_ack;did_drop_ack=false;
  uint64_t begin=cycles;unsigned old=d.accepted_count,wr0=d.model_writes,rd0=d.model_reads,a0=d.model_acts,p0=d.model_pres,ref0=d.model_refreshes,u0=d.lcd_underruns;
  d.start_generation=generation;d.start_packet_bytes=packet.size();d.start_valid=1;while(!tick().start){}d.start_valid=0;
  while(!d.done){need(cycles-begin<100000000,"full frame transaction timeout stage="+std::to_string(d.stage));tick();need(!d.error&&!d.lcd_error&&!d.cache_prepare_fault,"system error stage="+std::to_string(d.stage)+" reason="+std::to_string(d.error_code)+" painter="+std::to_string(d.error_code));}
  need(d.accepted_count==old+1&&hud.accepted()&&hud.accepted()->id==gold->id,"global commit exactly once");if(lost_ack)need(soft_calls>=2,"lost commit acknowledgment not reconciled");verify(gold);
  std::cout<<"SYSTEM_FRAME_PASS fid="<<gold->id<<" key="<<gold->key<<" generation="<<generation<<" cycles="<<cycles-begin<<" ack_cycle="<<cycles<<" actual_writes="<<d.model_writes-wr0<<" actual_read_bursts="<<d.model_reads-rd0<<" ACT="<<d.model_acts-a0<<" PRE="<<d.model_pres-p0<<" REF="<<d.model_refreshes-ref0<<" underruns="<<d.lcd_underruns-u0<<" cache_prepare_cycles="<<d.cache_prepare_cycles<<" processor_commit_calls="<<soft_calls<<" group_LCD="<<d.group_lcd_count<<" group_BG="<<d.group_bg_count<<" reserved_idle="<<d.group_idle<<" LCD_idle="<<d.group_lcd_idle<<" BG_idle="<<d.group_bg_idle<<" LCD_timer_expiry="<<d.group_lcd_expiry<<" BG_timer_expiry="<<d.group_bg_expiry<<" LCD_maxwait="<<d.group_lcd_wait<<" BG_maxwait="<<d.group_bg_wait<<std::endl;
 }
};
int run(int argc,char**argv){try{need(argc>=3,"native index frame_count");std::filesystem::path index=argv[1];unsigned limit=unsigned(std::stoul(argv[2]));Sim s;cu66::Decoder decoder;std::ifstream f(index);need(bool(f),"index open");std::string line;unsigned frames=0;
 while(frames<limit&&std::getline(f,line)){std::stringstream row(line);std::string chain,ordinal,path;std::getline(row,chain,'\t');std::getline(row,ordinal,'\t');std::getline(row,path,'\t');need(chain=="0","single chronological first cohort");auto bytes=load(index.parent_path()/path);auto gold=decoder.receive(bytes);s.run(bytes,gold,frames==1);frames++;}
 uint64_t begin=s.cycles;while(s.cycles-begin<3500000)s.tick();need(s.d.front_valid&&s.d.lcd_front_valid&&s.d.front_frame_id==s.d.reference_frame_id&&s.d.lcd_front_frame_id==s.d.reference_frame_id,"final presentation acknowledgment");
 std::cout<<"DY71_FENCE_SUMMARY pulses="<<s.fence_pulses<<" idle_transitions="<<s.fence_idle_transitions<<" idle_cycles="<<s.fence_idle_cycles<<" pending_transition_logs="<<s.fence_pending_logs<<std::endl;
 std::cout<<"SYSTEM_PASS complete_frames="<<frames<<" canonical_bytes_per_frame=518400 RGB_reads_or_writes=0 HUD_functional_readback_words_per_frame=21120 clean_lines="<<s.good_lines<<" black_lines="<<s.black_lines<<" observed_pixels="<<s.pixels<<" total_underruns="<<s.d.lcd_underruns<<" cycles="<<s.cycles<<" group_LCD="<<s.d.group_lcd_count<<" group_BG="<<s.d.group_bg_count<<" reserved_idle="<<s.d.group_idle<<" LCD_maxwait="<<s.d.group_lcd_wait<<" BG_maxwait="<<s.d.group_bg_wait<<" physical_fps_proven=0"<<std::endl;
 return 0;}catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<std::endl;return 1;}}

}
int main(int argc,char**argv){
 if(argc>1&&std::string(argv[1])=="--control")return control::run(argc-1,argv+1);
 if(argc>1&&std::string(argv[1])=="--frames")return frames::run(argc-1,argv+1);
 return 2;
}
