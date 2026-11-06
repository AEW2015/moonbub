#include "Vcu80_system_sim.h"
#include "verilated.h"
#include "monitor.hpp"
#include "../../../../experiments/cu66-native-v69/decoder.hpp"
#include "../../cu66-v69/hud-partition/hud_gate.hpp"
#include "../../cu66-v70/memory/memory_map.hpp"
#include <algorithm>
#include <array>
#include <chrono>
#include <limits>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <numeric>
#include <memory>
#include <set>
#include <sstream>
#include <stdexcept>

static void need(bool b,const char*s){if(!b)throw std::runtime_error(s);}
static void need(bool b,const std::string&s){if(!b)throw std::runtime_error(s);}
static cu66::Bytes load(const std::filesystem::path&p){std::ifstream f(p,std::ios::binary);need(bool(f),"packet open");return {std::istreambuf_iterator<char>(f),{}};}
template<class W>static void put_tag(W&w,const cu66::Tag&t){for(unsigned i=0;i<4;i++){uint32_t v=0;for(unsigned j=0;j<4;j++)v=(v<<8)|t[4*i+j];w[3-i]=v;}}
static unsigned hud_base(unsigned bank){need(bank<3,"HUD bank bound");return bank==0?cu70_map::HUD0_BASE:bank==1?cu70_map::HUD1_BASE:cu70_map::HUD2_BASE;}
struct Event{
 bool start=false,packet_req=false,packet_rsp=false,prepare=false,result=false,drain=false,aux_req=false,aux_rsp=false,aux_error=false,command=false,ack=false;
 std::array<uint16_t,8> aux_words{};
 unsigned packet_address=0,packet_sequence=0,aux_data=0,opcode=0,fid=0,rid=0,bank=0,hud_address=0,hud_length=0;
 uint64_t packet_generation=0,generation=0;bool key=false;
};
struct Timing {
 uint64_t packet_complete=0,admission=0,validated_ready=0,commit_ack=0,descriptor_presented=0;
 uint64_t first_correct_pixel_ps=0,last_correct_pixel_ps=0,first_complete_raster_start_ps=0,first_complete_raster_end_ps=0,complete_rasters=0,native_hud_wall_ns=0;
 unsigned fid=0;
};
struct PrefetchEvents {uint64_t done=0,aborted=0,done_cycle=0,aborted_cycle=0;};
struct PrefetchStats {
 uint64_t epoch=0;uint32_t commands=0,beats=0,filled=0,lookups=0,retired=0,unused=0;
 bool operator==(const PrefetchStats&o)const{return epoch==o.epoch&&commands==o.commands&&beats==o.beats&&filled==o.filled&&lookups==o.lookups&&retired==o.retired&&unused==o.unused;}
};
struct Sim{
 std::unique_ptr<VerilatedContext> c=[](){auto p=std::make_unique<VerilatedContext>();p->threads(1);return p;}();Vcu80_system_sim d{c.get()};
 uint64_t next_pixel=17029,cycles=0,generation=0;
 cu66::Bytes packet;cu66_partition::HudGate hud;
 std::shared_ptr<const cu66_partition::HudCache> candidate;
 std::vector<cu66::Patch> readback;std::vector<uint16_t> words;
 std::map<uint64_t,std::shared_ptr<const cu66::Frame>> golds;
 bool packet_pending=false,prepared=false,result_sent=false,drain_sent=false,aux_pending=false,software_pending=false;
 bool software_success=false,drop_ack=false,did_drop_ack=false;
 std::ofstream trace;std::set<uint64_t> trace_generations;uint64_t trace_rows=0;
 std::array<uint64_t,4> command_reads{},command_writes{};std::array<uint64_t,4> tile_events{};std::array<uint8_t,8100> tile_masks{};uint64_t fill_events=0;
 bool profiling=false;std::array<uint64_t,8> occupancy_bins{};std::array<uint64_t,16> stage_bins{};
 bool hud_burst=true;unsigned aux_step=0,hud_write_requests=0,hud_read_requests=0;
 unsigned packet_address=0,packet_sequence=0,hud_bank=0,word_cursor=0,read_cursor=0,soft_op=0,soft_fid=0,soft_calls=0;
 uint64_t packet_generation=0,soft_gen=0;
 std::map<uint64_t,Timing> timings;std::map<uint64_t,PrefetchEvents> prefetch_events;
 uint64_t good_lines=0,black_lines=0,pixels=0,raster_generation=0,raster_start_ps=0;
 bool raster_good=false;unsigned raster_lines=0;
 unsigned line_matches=0,line_zeros=0,line_pixels=0,last_write_sequence=0;
 uint64_t input_base=0;bool fixed_arrivals=false,prefetch_enabled=false;unsigned prefetch_mode=0;uint64_t line_generation=0;CampaignMonitor monitor;
 explicit Sim(bool fixed,unsigned count,unsigned mode):fixed_arrivals(fixed),prefetch_enabled(mode>0),prefetch_mode(mode),monitor(count){d.clk=0;d.read_clk=0;d.pixel_clk=0;d.pixel_reset_n=0;d.rst=1;d.abort_i=0;d.clear_fault=0;d.start_valid=0;d.packet_req_ready=1;d.packet_rsp_valid=0;d.hud_prepare_ready=0;d.hud_result_valid=0;d.hud_drain_valid=0;d.software_command_ready=0;d.software_ack_valid=0;d.hud_aux_req_valid=0;d.hud_aux_rsp_ready=1;d.hud_aux_req_burst=0;d.hud_aux_req_read_burst=0;d.hud_aux_req_byte_enable=0;for(unsigned i=0;i<4;i++)d.hud_aux_req_burst_data[i]=0;d.diag_address=0;d.peek_address=0;eval();for(int i=0;i<8;i++)tick();d.rst=0;d.pixel_reset_n=1;for(int i=0;i<100;i++)tick();input_base=cycles;monitor.configure_releases(count,input_base,fixed);monitor.queue(cycles);}
 void configure_trace(const std::string&path,const std::string&selected){
  if(path=="-")return;std::stringstream list(selected);std::string item;while(std::getline(list,item,',')){auto gen=std::stoull(item);need(gen>0,"trace generation bound");trace_generations.insert(gen);}need(!trace_generations.empty()&&trace_generations.size()<=4,"trace requires one to four selected source generations");trace.open(path);need(bool(trace),"trace file open");trace<<"cycle,ps,frame_generation,event,owner_generation,client,write,address,bank,plane,tile_index\n";
 }
 void trace_event(const char*event,uint64_t owner,unsigned client,unsigned write,unsigned address,unsigned bank,unsigned plane,unsigned index){
  if(!trace.is_open()||!trace_generations.count(generation))return;
  need(trace_rows<2000000,"bounded trace event limit");trace<<cycles+1<<','<<c->time()<<','<<generation<<','<<event<<','<<owner<<','<<client<<','<<write<<','<<address<<','<<bank<<','<<plane<<','<<index<<'\n';trace_rows++;need(bool(trace),"trace write failed");
 }
 void observe_tile_event(unsigned kind,uint64_t owner,unsigned bank,unsigned plane,unsigned index){
  if(!profiling)return;need(owner==generation,"receiver tile event generation mismatch");need(plane<3&&index<(plane==0?5400u:1350u),"receiver tile event coordinate bounds");need(bank==(kind<2?unsigned(d.reference_bank):unsigned(d.candidate_bank)),"receiver tile event bank mismatch");
  auto&mask=tile_masks[(plane==0?0:plane==1?5400:6750)+index];unsigned bit=1u<<kind;need(!(mask&bit),"duplicate receiver tile event");if(kind==1)need(mask&1,"reference response precedes request");if(kind==3)need(mask&4,"tile write completion precedes request");mask|=bit;tile_events[kind]++;
 }
 void trace_before_edge(){
  if(d.trace_command_valid){unsigned client=d.trace_command_client;need(client<4,"trace command client bound");if(profiling)(d.trace_command_write?command_writes:command_reads)[client]++;trace_event("command",0,client,d.trace_command_write,d.trace_command_address,0,0,0);}
  const unsigned events=d.trace_tile_events;
  if(events&1)observe_tile_event(0,d.trace_ref_req_generation,d.trace_ref_req_bank,d.trace_ref_req_plane,d.trace_ref_req_index);
  if(events&2)observe_tile_event(1,d.trace_ref_rsp_generation,d.trace_ref_rsp_bank,d.trace_ref_rsp_plane,d.trace_ref_rsp_index);
  if(events&4)observe_tile_event(2,d.trace_write_req_generation,d.trace_write_req_bank,d.trace_write_req_plane,d.trace_write_req_index);
  if(events&8)observe_tile_event(3,d.trace_write_done_generation,d.trace_write_done_bank,d.trace_write_done_plane,d.trace_write_done_index);
  if(events&1)trace_event("ref_request",d.trace_ref_req_generation,0,0,0,d.trace_ref_req_bank,d.trace_ref_req_plane,d.trace_ref_req_index);
  if(events&2)trace_event("ref_response",d.trace_ref_rsp_generation,0,0,0,d.trace_ref_rsp_bank,d.trace_ref_rsp_plane,d.trace_ref_rsp_index);
  if(events&4)trace_event("tile_write_request",d.trace_write_req_generation,0,1,0,d.trace_write_req_bank,d.trace_write_req_plane,d.trace_write_req_index);
  if(events&8)trace_event("tile_write_done",d.trace_write_done_generation,0,1,0,d.trace_write_done_bank,d.trace_write_done_plane,d.trace_write_done_index);
 }
 void observe_prefetch_events(){
  // The core completion outputs are one-memory-cycle pulses. Sample exactly once
  // after each memory rising edge; repeated d.eval() calls must not count them again.
  if(!d.prefetch_epoch_done&&!d.prefetch_epoch_aborted)return;
  need(d.prefetch_epoch_generation!=0,"prefetch event lacks epoch identity");auto&events=prefetch_events[d.prefetch_epoch_generation];
  if(d.prefetch_epoch_done){events.done++;if(!events.done_cycle)events.done_cycle=cycles+1;trace_event("prefetch_epoch_done",d.prefetch_epoch_generation,3,0,0,0,0,0);}
  if(d.prefetch_epoch_aborted){events.aborted++;if(!events.aborted_cycle)events.aborted_cycle=cycles+1;trace_event("prefetch_epoch_aborted",d.prefetch_epoch_generation,3,0,0,0,0,0);}
 }
 void eval(){d.eval();monitor.observe(d,c->time());if(d.prefetch_fault)throw std::runtime_error("prefetch fault code="+std::to_string(d.prefetch_fault_code)+" phase="+monitor.phase+" ps="+std::to_string(c->time()));}
 void pixel_check(){
  if(!d.data_enable||!d.lcd_front_valid)return;
  auto f=golds.find(d.lcd_front_generation);need(f!=golds.end(),"scanout generation lacks scoreboard");
  unsigned x=d.physical_x,y=d.physical_y;need(x<480&&y<800,"physical raster bounds");
  uint16_t expected=0;if(y>=40&&y<760)expected=f->second->display[x*720+y-40];
  uint16_t actual=uint16_t(((d.red>>3)<<11)|((d.green>>2)<<5)|(d.blue>>3));
  if(x==0&&y==0){raster_generation=d.lcd_front_generation;raster_start_ps=c->time();raster_good=true;raster_lines=0;}
  if(actual==expected){auto &tm=timings[d.lcd_front_generation];if(!tm.first_correct_pixel_ps)tm.first_correct_pixel_ps=c->time();tm.last_correct_pixel_ps=c->time();}
  if(x==0){need(y==raster_lines,"skipped or repeated physical raster row");line_matches=line_zeros=line_pixels=0;line_generation=d.lcd_front_generation;}
  need(x==line_pixels,"skipped or repeated physical raster column");
  need(line_generation==d.lcd_front_generation,"generation changed inside active line");
  line_matches+=actual==expected;line_zeros+=actual==0;line_pixels++;pixels++;
  if(x==479){need(line_pixels==480,"partial scanout line");need(line_matches==480||line_zeros==480,"corrupted/mixed scanout line");if(line_matches==480)good_lines++;else black_lines++;
   raster_good=raster_good&&line_matches==480&&raster_generation==d.lcd_front_generation;raster_lines++;
   if(y==799&&raster_good&&raster_lines==800){auto &tm=timings[raster_generation];tm.complete_rasters++;monitor.complete(raster_generation);if(!tm.first_complete_raster_end_ps){tm.first_complete_raster_start_ps=raster_start_ps;tm.first_complete_raster_end_ps=c->time();}}
  }
 }
 void advance(uint64_t target){while(c->time()<target){uint64_t n=std::min(target,next_pixel);if(d.eventsPending())n=std::min(n,d.nextTimeSlot());need(n>=c->time(),"simulation event in past");c->timeInc(n-c->time());bool rising=false;if(n==next_pixel){d.pixel_clk=!d.pixel_clk;rising=d.pixel_clk;next_pixel+=17029;}eval();if(d.write_event_sequence!=last_write_sequence){last_write_sequence=d.write_event_sequence;unsigned a=d.write_event_address;need(a<cu70_map::RGB0_BASE,"unexpected RGB/diagnostic/packet framebuffer write");if(d.lcd_front_valid){unsigned fb=cu70_map::canonical_base(d.lcd_front_bank),fh=hud_base(d.lcd_front_bank);need(!(a>=fb&&a<fb+259200)&&!(a>=fh&&a<fh+21120),"write into active canonical/HUD front");}}if(rising)pixel_check();}}
 void drive(){
  d.packet_rsp_valid=packet_pending;if(packet_pending){d.packet_rsp_address=packet_address;d.packet_rsp_generation=packet_generation;d.packet_rsp_sequence=packet_sequence;d.packet_rsp_data=packet.at(packet_address);}
  d.hud_prepare_ready=!prepared;d.hud_result_valid=prepared&&!result_sent;d.hud_result_generation=generation;d.hud_result_frame_id=d.active_frame_id;d.hud_result_reference_id=d.active_reference_id;d.hud_result_success=bool(candidate);d.hud_result_words=21120;put_tag(d.hud_result_tag,candidate?candidate->tag:cu66::Tag{});
  d.hud_aux_generation=generation;d.hud_aux_frame_id=d.active_frame_id;
  bool transfer=prepared&&result_sent&&candidate;
  d.hud_aux_req_valid=transfer&&!aux_pending&&(word_cursor<words.size()||read_cursor<words.size());
  d.hud_aux_req_write=word_cursor<words.size();
  d.hud_aux_req_addr=hud_base(hud_bank)+(d.hud_aux_req_write?word_cursor:read_cursor);
  d.hud_aux_req_data=d.hud_aux_req_write&&word_cursor<words.size()?words[word_cursor]:0;
  d.hud_aux_req_burst=hud_burst&&d.hud_aux_req_write;d.hud_aux_req_read_burst=hud_burst&&!d.hud_aux_req_write;
  d.hud_aux_req_byte_enable=d.hud_aux_req_burst?65535:0;
  for(unsigned i=0;i<4;i++){unsigned at=word_cursor+2*i;d.hud_aux_req_burst_data[i]=hud_burst&&d.hud_aux_req_write&&at+1<words.size()?uint32_t(words[at])|(uint32_t(words[at+1])<<16):0;}
  d.hud_drain_valid=transfer&&!drain_sent&&!aux_pending&&word_cursor==21120&&read_cursor==21120;
  d.hud_drain_generation=generation;d.hud_drain_frame_id=d.active_frame_id;d.hud_drain_bank=hud_bank;d.hud_drain_words=21120;d.hud_drain_success=1;
  if(d.hud_drain_valid)put_tag(d.hud_drain_tag,cu66::hud_tag(readback));
  d.software_command_ready=!software_pending;d.software_ack_valid=software_pending;d.software_ack_opcode=soft_op;d.software_ack_generation=soft_gen;d.software_ack_frame_id=soft_fid;d.software_ack_success=software_success;
 }
 Event tick(){if(profiling){occupancy_bins[(d.stage==5?4:0)+(d.memory_tile_busy?2:0)+(d.memory_aux_busy?1:0)]++;need(d.stage<stage_bins.size(),"stage histogram bound");stage_bins[d.stage]++;}drive();eval();uint64_t t=c->time();advance(t+2750);d.read_clk=1;eval();advance(t+5000);eval();
  Event e;e.start=d.start_valid&&d.start_ready;e.packet_req=d.packet_req_valid&&d.packet_req_ready;e.packet_rsp=d.packet_rsp_valid&&d.packet_rsp_ready;e.prepare=d.hud_prepare_valid&&d.hud_prepare_ready;e.result=d.hud_result_valid&&d.hud_result_ready;e.drain=d.hud_drain_valid&&d.hud_drain_ready;e.aux_req=d.hud_aux_req_valid&&d.hud_aux_req_ready;e.aux_rsp=d.hud_aux_rsp_valid&&d.hud_aux_rsp_ready;e.aux_data=d.hud_aux_rsp_data;for(unsigned i=0;i<8;i++)e.aux_words[i]=uint16_t(d.hud_aux_rsp_burst_data[i/2]>>(16*(i%2)));e.aux_error=d.hud_aux_rsp_error;e.command=d.software_command_valid&&d.software_command_ready;e.ack=d.software_ack_valid&&d.software_ack_ready;
  e.packet_address=d.packet_req_address;e.packet_generation=d.packet_req_generation;e.packet_sequence=d.packet_req_sequence;e.generation=d.active_generation;e.fid=d.active_frame_id;e.rid=d.active_reference_id;e.key=d.active_key;e.bank=d.candidate_bank;e.hud_address=d.hud_address;e.hud_length=d.hud_bytes;e.opcode=d.software_command_opcode;
  trace_before_edge();const auto fills_before=d.prefetch_tiles_filled;const auto epoch_before=d.prefetch_epoch_generation;
  d.clk=1;eval();observe_prefetch_events();
  if(d.prefetch_tiles_filled>fills_before&&d.prefetch_epoch_generation==epoch_before){need(d.prefetch_tiles_filled==fills_before+1,"nonsequential prefetch fill counter");if(profiling)fill_events++;unsigned ordinal=d.prefetch_tiles_filled-1;unsigned plane=ordinal<5400?0:ordinal<6750?1:2,index=ordinal-(plane==0?0:plane==1?5400:6750);trace_event("prefetch_fill",d.prefetch_epoch_generation,3,0,0,d.reference_bank,plane,index);}
  advance(t+7750);d.read_clk=0;eval();advance(t+10000);d.clk=0;eval();cycles++;
  if(e.packet_rsp)packet_pending=false;
  if(e.packet_req){need(!packet_pending,"multiple packet requests");packet_pending=true;packet_address=e.packet_address;packet_generation=e.packet_generation;packet_sequence=e.packet_sequence;need(packet_address<packet.size(),"packet address outside immutable stage");}
  if(e.prepare){auto native_begin=std::chrono::steady_clock::now();auto r=hud.prepare(e.generation,e.fid,e.rid,e.key,cu66::View(packet).sub(e.hud_address,e.hud_length));need(r==cu66_partition::Reply::Accepted,"actual HUD semantic preparation rejected");candidate=hud.read_candidate(e.generation,e.fid);need(candidate!=nullptr,"owned HUD candidate");prepared=true;hud_bank=e.bank;words.clear();for(auto&p:candidate->patches)words.insert(words.end(),p.words.begin(),p.words.end());need(words.size()==21120,"exact HUD words");readback=candidate->patches;for(auto&p:readback)std::fill(p.words.begin(),p.words.end(),0);timings[generation].native_hud_wall_ns+=std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now()-native_begin).count();}
  if(e.result)result_sent=true;
  if(e.aux_req){need(!aux_pending,"multiple HUD memory transactions");aux_pending=true;aux_step=hud_burst?8:1;if(word_cursor<21120)hud_write_requests++;else hud_read_requests++;}
  if(e.aux_rsp){need(aux_pending&&!e.aux_error,"actual HUD memory transaction error");aux_pending=false;if(word_cursor<21120)word_cursor+=aux_step;else{for(unsigned i=0;i<aux_step;i++){unsigned at=0;for(auto&p:readback){if(read_cursor+i<at+p.words.size()){p.words[read_cursor+i-at]=hud_burst?e.aux_words[i]:uint16_t(e.aux_data);break;}at+=p.words.size();}}read_cursor+=aux_step;}}
  if(e.drain){need(cu66::hud_tag(readback)==candidate->tag,"actual functional HUD readback tag");need(hud.acknowledge_external_write_drain(e.generation,e.fid,21120,cu66::hud_tag(readback)),"HUD semantic transfer fence");drain_sent=true;}
  if(e.ack)software_pending=false;
  if(e.command){need(!software_pending,"multiple software decisions");soft_op=e.opcode;soft_gen=e.generation;soft_fid=e.fid;need(e.opcode==5||e.opcode==6,"unexpected software command");software_success=e.opcode==5?hud.commit(e.generation,e.fid):hud.abort(e.generation,e.fid);need(software_success,"root commit disagrees with processor state");soft_calls++;if(drop_ack&&!did_drop_ack)did_drop_ack=true;else software_pending=true;}
  if(generation){auto &tm=timings[generation];
   if(e.start){tm.admission=cycles;monitor.admitted++;}
   // Frozen receiver WAIT_RGB (6) is reached only after checked base, HUD and write fences.
   if(d.validated_ready&&!tm.validated_ready)tm.validated_ready=cycles;
   if(d.done&&!tm.commit_ack){tm.commit_ack=cycles;monitor.commit(generation,cycles,tm.complete_rasters!=0);std::cout<<"SYSTEM_RASTER_DEADLINE generation="<<generation<<" fid="<<tm.fid<<" commit_ack_cycle="<<cycles<<" due_cycle="<<cycles+CampaignMonitor::raster_deadline_cycles<<" bound_cycles="<<CampaignMonitor::raster_deadline_cycles<<" functional_liveness_only=1"<<std::endl;}
  }
  if(d.lcd_presented)timings[d.lcd_front_generation].descriptor_presented=cycles;
  monitor.observe(d,c->time());return e;
 }
 uint16_t peek(unsigned address){need(address<(1u<<24)&&cu70_map::allowed(address),"peek map");d.peek_address=address;eval();return d.peek_data;}
 void verify(std::shared_ptr<const cu66::Frame>gold){
  need(d.reference_valid&&d.reference_frame_id==gold->id,"stored accepted reference identity");unsigned base=cu70_map::canonical_base(d.reference_bank);
  std::array<cu66::Bytes,3> p;for(unsigned a=0;a<3;a++){unsigned n=a?86400:345600,off=a==0?0:a==1?172800:216000;p[a].resize(n);for(unsigned i=0;i<n/2;i++){unsigned pitch=a?180:360, row=i/pitch,col=i%pitch;unsigned phys=((row>>3)*(a?45:90)+(col>>2))*32+(row&7)*4+(col&3);auto w=peek(base+off+phys);p[a][i*2]=uint8_t(w);p[a][i*2+1]=uint8_t(w>>8);}need(p[a]==gold->planes[a],"full command-memory canonical plane mismatch");}
  need(cu66::canonical_tag(p)==gold->canonical_tag,"canonical memory full tag");

 }
 PrefetchStats prefetch_stats()const{return {d.prefetch_epoch_generation,d.prefetch_read_commands,d.prefetch_read_beats,d.prefetch_tiles_filled,d.prefetch_lookups,d.prefetch_tiles_retired,d.prefetch_unused_retired};}
 void verify_prefetch(const PrefetchStats&before,const cu66::Frame&gold){
  const auto after=prefetch_stats();const auto found=prefetch_events.find(after.epoch);const auto events=found==prefetch_events.end()?PrefetchEvents{}:found->second;
  if(!prefetch_enabled){need(after==PrefetchStats{}&&!d.prefetch_busy&&prefetch_events.empty()&&!d.prefetch_epoch_done&&!d.prefetch_epoch_aborted,"baseline prefetch diagnostics must remain zero");}
  else if(gold.key){need(after==before&&!d.prefetch_busy&&!prefetch_events.count(generation),"key frame launched or mutated a prefetch epoch");}
  else {need(after.epoch==generation,"delta prefetch epoch identity mismatch");need(!d.prefetch_busy&&events.done==1&&events.aborted==0&&events.done_cycle>0&&events.done_cycle<timings.at(generation).commit_ack,"delta prefetch epoch did not finish cleanly before ACK");need(after.commands==32400&&after.beats==259200&&after.filled==8100&&after.lookups==7806&&after.retired==8100&&after.unused==294,"delta prefetch logical walk/read/retirement accounting mismatch");}
  std::cout<<"SYSTEM_PREFETCH generation="<<generation<<" fid="<<gold.id<<" key="<<gold.key<<" enabled="<<prefetch_enabled<<" epoch_generation="<<after.epoch<<" busy="<<unsigned(d.prefetch_busy)<<" fault="<<unsigned(d.prefetch_fault)<<" epoch_done_events="<<events.done<<" epoch_aborted_events="<<events.aborted<<" epoch_done_cycle="<<events.done_cycle<<" epoch_aborted_cycle="<<events.aborted_cycle<<" epoch_done_level="<<unsigned(d.prefetch_epoch_done)<<" epoch_aborted_level="<<unsigned(d.prefetch_epoch_aborted)<<" read_commands="<<after.commands<<" read_beats="<<after.beats<<" tiles_filled="<<after.filled<<" lookups="<<after.lookups<<" tiles_retired="<<after.retired<<" unused_retired="<<after.unused<<" new_epoch="<<(after.epoch!=before.epoch)<<std::endl;
 }
 std::array<uint32_t,3> stream_profile()const{return {d.stream_candidate_wait_cycles,d.stream_idle_candidate_wait_cycles,d.stream_write_accepts};}
 std::array<uint32_t,9> profile(){return {d.p0_cache_hits,d.p0_cache_misses,d.p0_row_reads,d.p0_wait_cycles,d.p0_service_cycles,d.p1_cache_hits,d.p1_cache_misses,d.p0_read_wait_cycles,d.p0_read_service_cycles};}
 void run(cu66::Bytes bytes,std::shared_ptr<const cu66::Frame>gold,unsigned ordinal,bool lost_ack=false){
  monitor.phase="release_wait";if(!fixed_arrivals)monitor.releases.at(ordinal)=cycles;uint64_t release=monitor.releases.at(ordinal);while(cycles<release)tick();monitor.queue(cycles);
  generation++;packet=std::move(bytes);golds[generation]=gold;timings[generation].packet_complete=release;timings[generation].fid=gold->id;monitor.phase="readiness_wait";uint64_t readiness_begin=cycles;while(!d.start_ready){need(cycles-readiness_begin<100000000,"start readiness timeout");tick();}prepared=result_sent=drain_sent=false;aux_pending=false;candidate=nullptr;word_cursor=read_cursor=0;hud_write_requests=hud_read_requests=0;soft_calls=0;drop_ack=lost_ack;did_drop_ack=false;
  monitor.phase="transaction";auto profile_before=profile();auto prefetch_before=prefetch_stats();auto stream_before=stream_profile();
  occupancy_bins.fill(0);stage_bins.fill(0);command_reads.fill(0);command_writes.fill(0);tile_events.fill(0);tile_masks.fill(0);fill_events=0;profiling=true;uint64_t begin=cycles;unsigned old=d.accepted_count,wr0=d.model_writes,rd0=d.model_reads,a0=d.model_acts,p0=d.model_pres,ref0=d.model_refreshes,u0=d.lcd_underruns,wc0=d.model_write_commands,wb0=d.model_write_bus_beats;
  d.start_generation=generation;d.start_packet_bytes=packet.size();d.start_valid=1;while(!tick().start){need(cycles-begin<100000000,"start admission timeout");}d.start_valid=0;
  while(!d.done){if(cycles-begin>=100000000)throw std::runtime_error("full frame transaction timeout stage="+std::to_string(d.stage));tick();if(d.error||d.lcd_error)throw std::runtime_error("system error stage="+std::to_string(d.stage)+" reason="+std::to_string(d.error_code));}
  profiling=false;need(std::accumulate(occupancy_bins.begin(),occupancy_bins.end(),uint64_t(0))==cycles-begin,"occupancy bins partition transaction cycles");
  need(timings[generation].validated_ready>timings[generation].admission,"ordered actual decoder validation event");
  need(d.accepted_count==old+1&&hud.accepted()&&hud.accepted()->id==gold->id,"global commit exactly once");if(lost_ack)need(soft_calls>=2,"lost commit acknowledgment not reconciled");verify(gold);verify_prefetch(prefetch_before,*gold);
  for(auto mask:tile_masks)need((mask&12)==12&&((mask&3)==0||(mask&3)==3),"per-tile request/response/write pairing mismatch");
  need(tile_events[0]==tile_events[1]&&tile_events[2]==8100&&tile_events[3]==8100,"receiver tile event accounting mismatch");need(tile_events[0]==(gold->key?0u:7806u),"receiver reference lookup count mismatch");need(std::accumulate(command_writes.begin(),command_writes.end(),uint64_t(0))==35040,"actual per-client BL8 write command accounting mismatch");need(command_reads[3]<=(prefetch_enabled&&!gold->key?32400u:0u),"actual prefetch physical commands exceed logical requests");need(fill_events==(prefetch_enabled&&!gold->key?8100u:0u),"observed prefetch fill accounting mismatch");
  const auto stream_after=stream_profile();std::array<uint32_t,3> stream_delta{};for(unsigned i=0;i<3;i++)stream_delta[i]=stream_after[i]-stream_before[i];if(prefetch_mode==0)need(stream_after==std::array<uint32_t,3>{},"baseline stream diagnostics must remain zero");
  std::cout<<"SYSTEM_STREAM generation="<<generation<<" fid="<<gold->id<<" mode="<<prefetch_mode<<" candidate_wait_cycles="<<stream_delta[0]<<" idle_candidate_wait_cycles="<<stream_delta[1]<<" write_accepts="<<stream_delta[2]<<std::endl;
  std::cout<<"SYSTEM_COMMANDS generation="<<generation<<" fid="<<gold->id;for(unsigned i=0;i<4;i++)std::cout<<" client"<<i<<"_reads="<<command_reads[i]<<" client"<<i<<"_writes="<<command_writes[i];std::cout<<" ref_requests="<<tile_events[0]<<" ref_responses="<<tile_events[1]<<" tile_write_requests="<<tile_events[2]<<" tile_write_done="<<tile_events[3]<<" prefetch_fill_events="<<fill_events<<std::endl;
  std::cout<<"SYSTEM_FRAME_PASS fid="<<gold->id<<" key="<<gold->key<<" generation="<<generation<<" cycles="<<cycles-begin<<" origin_to_ack_cycles="<<cycles-release<<" actual_writes="<<d.model_writes-wr0<<" actual_write_commands="<<d.model_write_commands-wc0<<" actual_write_bus_beats="<<d.model_write_bus_beats-wb0<<" hud_burst="<<hud_burst<<" hud_write_requests="<<hud_write_requests<<" hud_read_requests="<<hud_read_requests<<" actual_read_bursts="<<d.model_reads-rd0<<" ACT="<<d.model_acts-a0<<" PRE="<<d.model_pres-p0<<" REF="<<d.model_refreshes-ref0<<" underruns="<<d.lcd_underruns-u0<<" processor_commit_calls="<<soft_calls;auto profile_after=profile();const char* names[]={"p0_cache_hits","p0_cache_misses","p0_row_reads","p0_wait_cycles","p0_service_cycles","p1_cache_hits","p1_cache_misses","p0_read_wait_cycles","p0_read_service_cycles"};for(unsigned i=0;i<9;i++)std::cout<<" "<<names[i]<<"="<<profile_after[i]-profile_before[i];for(unsigned i=0;i<8;i++)std::cout<<" base"<<(i>>2)<<"_tile"<<((i>>1)&1)<<"_aux"<<(i&1)<<"_cycles="<<occupancy_bins[i];for(unsigned i=0;i<16;i++)std::cout<<" stage"<<i<<"_cycles="<<stage_bins[i];std::cout<<std::endl;
 }
};
int main(int argc,char**argv){try{need(argc>=6,"native index frame_count arrival_mode cohort prefetch_enable");std::filesystem::path index=argv[1];unsigned limit=unsigned(std::stoul(argv[2]));bool fixed=std::string(argv[3])=="fixed30";unsigned cohort=unsigned(std::stoul(argv[4]));need(cohort<4,"cohort range");unsigned prefetch=unsigned(std::stoul(argv[5]));need(prefetch<=2,"prefetch range");
 std::ifstream f(index);need(bool(f),"index open");std::string line;std::vector<std::string> paths;
 while(std::getline(f,line)){std::stringstream row(line);std::string chain,ordinal,path;std::getline(row,chain,'\t');std::getline(row,ordinal,'\t');std::getline(row,path,'\t');if(unsigned(std::stoul(chain))==cohort){need(unsigned(std::stoul(ordinal))==paths.size(),"cohort chronology");paths.push_back(path);}}
 need(limit>0&&limit<=paths.size(),"requested frame count outside finite cohort");Sim s(fixed,limit,prefetch);if(argc>=8)s.configure_trace(argv[6],argv[7]);cu66::Decoder decoder;unsigned frames=0;std::set<unsigned> attempted_source_ids;
 for(;frames<limit;frames++){auto bytes=load(index.parent_path()/paths[frames]);auto gold=decoder.receive(bytes);need(attempted_source_ids.insert(gold->id).second,"duplicate attempted source frame ID");s.run(bytes,gold,frames,frames==1);}
 // Every ACK creates its own bounded raster obligation. Monitoring continues through the tail.
 s.monitor.phase="final_tail";uint64_t tail_begin=s.cycles;while(!s.monitor.raster_due.empty()||s.cycles-tail_begin<3500000)s.tick();
 need(s.d.front_valid&&s.d.lcd_front_valid&&s.d.front_frame_id==s.d.reference_frame_id&&s.d.lcd_front_frame_id==s.d.reference_frame_id,"final presentation acknowledgment");
 unsigned distinct_complete=0;std::set<unsigned> completed_source_ids;
 for(const auto &item:s.timings){auto &tm=item.second;need(tm.complete_rasters>0,"requested source lacks a complete correct physical raster");if(tm.complete_rasters){need(completed_source_ids.insert(tm.fid).second,"duplicate source frame ID in distinct presentation count");distinct_complete++;}
  std::cout<<"SYSTEM_TIMING generation="<<item.first<<" fid="<<tm.fid<<" packet_complete_cycle="<<tm.packet_complete<<" admission_cycle="<<tm.admission<<" validated_ready_cycle="<<tm.validated_ready<<" commit_ack_cycle="<<tm.commit_ack<<" descriptor_presented_cycle="<<tm.descriptor_presented<<" queue_cycles="<<tm.admission-tm.packet_complete<<" validated_decode_model_cycles="<<tm.validated_ready-tm.packet_complete<<" post_validated_ack_model_cycles="<<tm.commit_ack-tm.validated_ready<<" met_serial_30fps_budget="<<((tm.commit_ack-tm.packet_complete)*30<=100000000)<<" met_validated_under10ms="<<(tm.validated_ready-tm.packet_complete<1000000)<<" first_correct_pixel_ps="<<tm.first_correct_pixel_ps<<" last_correct_pixel_ps="<<tm.last_correct_pixel_ps<<" first_complete_raster_start_ps="<<tm.first_complete_raster_start_ps<<" first_complete_raster_end_ps="<<tm.first_complete_raster_end_ps<<" complete_rasters="<<tm.complete_rasters<<" native_hud_prepare_wall_ns="<<tm.native_hud_wall_ns<<std::endl;
 }
 need(distinct_complete==limit&&completed_source_ids==attempted_source_ids,"every requested source fully presented");s.monitor.observe(s.d,s.c->time());need(s.monitor.waiting==0&&s.monitor.in_service==0&&s.monitor.total==0,"terminal input queue not empty");
 std::cout<<"SYSTEM_PASS cohort="<<cohort<<" distinct_complete_presentations="<<distinct_complete<<" complete_frames="<<frames<<" canonical_bytes_per_frame=518400 RGB_DDR_words_written_per_frame=0 HUD_functional_readback_words_per_frame=21120 clean_lines="<<s.good_lines<<" black_lines="<<s.black_lines<<" observed_pixels="<<s.pixels<<" total_underruns="<<s.d.lcd_underruns<<" lcd_memory_errors="<<s.d.lcd_memory_errors<<" sticky_lcd_error="<<s.monitor.saw_lcd_error<<" sticky_memory_error="<<s.monitor.saw_memory_error<<" sticky_underrun="<<s.monitor.saw_underrun<<" health_observations="<<s.monitor.observations<<" cycles="<<s.cycles<<" max_input_queue="<<s.monitor.max_waiting<<" max_waiting_released_unadmitted="<<s.monitor.max_waiting<<" max_in_service="<<s.monitor.max_in_service<<" max_total_released_unacked="<<s.monitor.max_total<<" raster_deadline_cycles="<<CampaignMonitor::raster_deadline_cycles<<" global_watchdog_cycles="<<s.monitor.watchdog_cycles<<" trace_rows="<<s.trace_rows<<" physical_fps_proven=0"<<std::endl;
 }catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<std::endl;return 1;}}
