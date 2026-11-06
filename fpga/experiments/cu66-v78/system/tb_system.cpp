#include "Vcu78_system_sim.h"
#include "verilated.h"
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
#include <memory>
#include <set>
#include <stdexcept>

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
struct Sim{
 std::unique_ptr<VerilatedContext> c=[](){auto p=std::make_unique<VerilatedContext>();p->threads(1);return p;}();Vcu78_system_sim d{c.get()};
 uint64_t next_pixel=17029,cycles=0,generation=0;
 cu66::Bytes packet;cu66_partition::HudGate hud;
 std::shared_ptr<const cu66_partition::HudCache> candidate;
 std::vector<cu66::Patch> readback;std::vector<uint16_t> words;
 std::map<uint64_t,std::shared_ptr<const cu66::Frame>> golds;
 bool packet_pending=false,prepared=false,result_sent=false,drain_sent=false,aux_pending=false,software_pending=false;
 bool software_success=false,drop_ack=false,did_drop_ack=false;
 bool hud_burst=true;unsigned aux_step=0,hud_write_requests=0,hud_read_requests=0;
 unsigned packet_address=0,packet_sequence=0,hud_bank=0,word_cursor=0,read_cursor=0,soft_op=0,soft_fid=0,soft_calls=0;
 uint64_t packet_generation=0,soft_gen=0;
 std::map<uint64_t,Timing> timings;
 uint64_t good_lines=0,black_lines=0,pixels=0,raster_generation=0,raster_start_ps=0;
 bool raster_good=false;unsigned raster_lines=0;
 unsigned line_matches=0,line_zeros=0,line_pixels=0,last_write_sequence=0;
 uint64_t input_base=0;bool fixed_arrivals=false;unsigned max_input_queue=0,negative_cases=0;uint64_t line_generation=0;
 explicit Sim(bool fixed):fixed_arrivals(fixed){d.clk=0;d.read_clk=0;d.pixel_clk=0;d.pixel_reset_n=0;d.rst=1;d.abort_i=0;d.clear_fault=0;d.start_valid=0;d.packet_req_ready=1;d.packet_rsp_valid=0;d.hud_prepare_ready=0;d.hud_result_valid=0;d.hud_drain_valid=0;d.software_command_ready=0;d.software_ack_valid=0;d.hud_aux_req_valid=0;d.hud_aux_rsp_ready=1;d.hud_aux_req_burst=0;d.hud_aux_req_read_burst=0;d.hud_aux_req_byte_enable=0;for(unsigned i=0;i<4;i++)d.hud_aux_req_burst_data[i]=0;d.diag_address=0;d.peek_address=0;d.eval();for(int i=0;i<8;i++)tick();d.rst=0;d.pixel_reset_n=1;for(int i=0;i<100;i++)tick();}
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
   if(y==799&&raster_good&&raster_lines==800){auto &tm=timings[raster_generation];tm.complete_rasters++;if(!tm.first_complete_raster_end_ps){tm.first_complete_raster_start_ps=raster_start_ps;tm.first_complete_raster_end_ps=c->time();}}
  }
 }
 void advance(uint64_t target){while(c->time()<target){uint64_t n=std::min(target,next_pixel);if(d.eventsPending())n=std::min(n,d.nextTimeSlot());need(n>=c->time(),"simulation event in past");c->timeInc(n-c->time());bool rising=false;if(n==next_pixel){d.pixel_clk=!d.pixel_clk;rising=d.pixel_clk;next_pixel+=17029;}d.eval();if(d.write_event_sequence!=last_write_sequence){last_write_sequence=d.write_event_sequence;unsigned a=d.write_event_address;need(a<cu70_map::RGB0_BASE,"unexpected RGB/diagnostic/packet framebuffer write");if(d.lcd_front_valid){unsigned fb=cu70_map::canonical_base(d.lcd_front_bank),fh=hud_base(d.lcd_front_bank);need(!(a>=fb&&a<fb+259200)&&!(a>=fh&&a<fh+21120),"write into active canonical/HUD front");}}if(rising)pixel_check();}}
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
 Event tick(){need(cycles<300000000,"system watchdog");drive();d.eval();uint64_t t=c->time();advance(t+2750);d.read_clk=1;d.eval();advance(t+5000);d.eval();
  Event e;e.start=d.start_valid&&d.start_ready;e.packet_req=d.packet_req_valid&&d.packet_req_ready;e.packet_rsp=d.packet_rsp_valid&&d.packet_rsp_ready;e.prepare=d.hud_prepare_valid&&d.hud_prepare_ready;e.result=d.hud_result_valid&&d.hud_result_ready;e.drain=d.hud_drain_valid&&d.hud_drain_ready;e.aux_req=d.hud_aux_req_valid&&d.hud_aux_req_ready;e.aux_rsp=d.hud_aux_rsp_valid&&d.hud_aux_rsp_ready;e.aux_data=d.hud_aux_rsp_data;for(unsigned i=0;i<8;i++)e.aux_words[i]=uint16_t(d.hud_aux_rsp_burst_data[i/2]>>(16*(i%2)));e.aux_error=d.hud_aux_rsp_error;e.command=d.software_command_valid&&d.software_command_ready;e.ack=d.software_ack_valid&&d.software_ack_ready;
  e.packet_address=d.packet_req_address;e.packet_generation=d.packet_req_generation;e.packet_sequence=d.packet_req_sequence;e.generation=d.active_generation;e.fid=d.active_frame_id;e.rid=d.active_reference_id;e.key=d.active_key;e.bank=d.candidate_bank;e.hud_address=d.hud_address;e.hud_length=d.hud_bytes;e.opcode=d.software_command_opcode;
  d.clk=1;d.eval();advance(t+7750);d.read_clk=0;d.eval();advance(t+10000);d.clk=0;d.eval();cycles++;
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
   if(e.start)tm.admission=cycles;
   // Frozen receiver WAIT_RGB (6) is reached only after checked base, HUD and write fences.
   if(d.validated_ready&&!tm.validated_ready)tm.validated_ready=cycles;
   if(d.done&&!tm.commit_ack)tm.commit_ack=cycles;
  }
  if(d.lcd_presented)timings[d.lcd_front_generation].descriptor_presented=cycles;
  return e;
 }
 uint16_t peek(unsigned address){need(address<(1u<<24)&&cu70_map::allowed(address),"peek map");d.peek_address=address;d.eval();return d.peek_data;}
 void verify(std::shared_ptr<const cu66::Frame>gold){
  need(d.reference_valid&&d.reference_frame_id==gold->id,"stored accepted reference identity");unsigned base=cu70_map::canonical_base(d.reference_bank);
  std::array<cu66::Bytes,3> p;for(unsigned a=0;a<3;a++){unsigned n=a?86400:345600,off=a==0?0:a==1?172800:216000;p[a].resize(n);for(unsigned i=0;i<n/2;i++){unsigned pitch=a?180:360, row=i/pitch,col=i%pitch;unsigned phys=((row>>3)*(a?45:90)+(col>>2))*32+(row&7)*4+(col&3);auto w=peek(base+off+phys);p[a][i*2]=uint8_t(w);p[a][i*2+1]=uint8_t(w>>8);}need(p[a]==gold->planes[a],"full command-memory canonical plane mismatch");}
  need(cu66::canonical_tag(p)==gold->canonical_tag,"canonical memory full tag");

 }
 std::array<uint32_t,9> profile(){return {d.p0_cache_hits,d.p0_cache_misses,d.p0_row_reads,d.p0_wait_cycles,d.p0_service_cycles,d.p1_cache_hits,d.p1_cache_misses,d.p0_read_wait_cycles,d.p0_read_service_cycles};}
 void run(cu66::Bytes bytes,std::shared_ptr<const cu66::Frame>gold,unsigned ordinal,bool lost_ack=false){
  if(!ordinal)input_base=cycles;uint64_t release=fixed_arrivals?input_base+uint64_t(ordinal)*100000000/30:cycles;while(cycles<release)tick();if(fixed_arrivals)max_input_queue=std::max(max_input_queue,unsigned((cycles-release)*30/100000000+1));
  generation++;packet=std::move(bytes);golds[generation]=gold;timings[generation].packet_complete=release;timings[generation].fid=gold->id;while(!d.start_ready)tick();prepared=result_sent=drain_sent=false;aux_pending=false;candidate=nullptr;word_cursor=read_cursor=0;hud_write_requests=hud_read_requests=0;soft_calls=0;drop_ack=lost_ack;did_drop_ack=false;
  auto profile_before=profile();
  uint64_t begin=cycles;unsigned old=d.accepted_count,wr0=d.model_writes,rd0=d.model_reads,a0=d.model_acts,p0=d.model_pres,ref0=d.model_refreshes,u0=d.lcd_underruns,wc0=d.model_write_commands,wb0=d.model_write_bus_beats;
  d.start_generation=generation;d.start_packet_bytes=packet.size();d.start_valid=1;while(!tick().start){}d.start_valid=0;
  while(!d.done){need(cycles-begin<100000000,"full frame transaction timeout stage="+std::to_string(d.stage));tick();need(!d.error&&!d.lcd_error,"system error stage="+std::to_string(d.stage)+" reason="+std::to_string(d.error_code));}
  need(timings[generation].validated_ready>timings[generation].admission,"ordered actual decoder validation event");
  need(d.accepted_count==old+1&&hud.accepted()&&hud.accepted()->id==gold->id,"global commit exactly once");if(lost_ack)need(soft_calls>=2,"lost commit acknowledgment not reconciled");verify(gold);
  std::cout<<"SYSTEM_FRAME_PASS fid="<<gold->id<<" key="<<gold->key<<" generation="<<generation<<" cycles="<<cycles-begin<<" origin_to_ack_cycles="<<cycles-release<<" actual_writes="<<d.model_writes-wr0<<" actual_write_commands="<<d.model_write_commands-wc0<<" actual_write_bus_beats="<<d.model_write_bus_beats-wb0<<" hud_burst="<<hud_burst<<" hud_write_requests="<<hud_write_requests<<" hud_read_requests="<<hud_read_requests<<" actual_read_bursts="<<d.model_reads-rd0<<" ACT="<<d.model_acts-a0<<" PRE="<<d.model_pres-p0<<" REF="<<d.model_refreshes-ref0<<" underruns="<<d.lcd_underruns-u0<<" processor_commit_calls="<<soft_calls;auto profile_after=profile();const char* names[]={"p0_cache_hits","p0_cache_misses","p0_row_reads","p0_wait_cycles","p0_service_cycles","p1_cache_hits","p1_cache_misses","p0_read_wait_cycles","p0_read_service_cycles"};for(unsigned i=0;i<9;i++)std::cout<<" "<<names[i]<<"="<<profile_after[i]-profile_before[i];std::cout<<std::endl;
 }
};
int main(int argc,char**argv){try{need(argc>=3,"native index frame_count");std::filesystem::path index=argv[1];unsigned limit=unsigned(std::stoul(argv[2]));bool fixed=argc>=4&&std::string(argv[3])=="fixed30";Sim s(fixed);cu66::Decoder decoder;std::ifstream f(index);need(bool(f),"index open");std::string line;unsigned frames=0;std::set<unsigned> attempted_source_ids;
 while(frames<limit&&std::getline(f,line)){std::stringstream row(line);std::string chain,ordinal,path;std::getline(row,chain,'\t');std::getline(row,ordinal,'\t');std::getline(row,path,'\t');need(chain=="0","single chronological first cohort");auto bytes=load(index.parent_path()/path);auto gold=decoder.receive(bytes);need(attempted_source_ids.insert(gold->id).second,"duplicate attempted source frame ID");s.run(bytes,gold,frames,frames==1);frames++;}
 uint64_t begin=s.cycles;while(s.cycles-begin<3500000)s.tick();need(s.d.front_valid&&s.d.lcd_front_valid&&s.d.front_frame_id==s.d.reference_frame_id&&s.d.lcd_front_frame_id==s.d.reference_frame_id,"final presentation acknowledgment");
 unsigned distinct_complete=0;std::set<unsigned> completed_source_ids;
 for(const auto &item:s.timings){auto &tm=item.second;if(tm.complete_rasters){need(completed_source_ids.insert(tm.fid).second,"duplicate source frame ID in distinct presentation count");distinct_complete++;}
  std::cout<<"SYSTEM_TIMING generation="<<item.first<<" fid="<<tm.fid<<" packet_complete_cycle="<<tm.packet_complete<<" admission_cycle="<<tm.admission<<" validated_ready_cycle="<<tm.validated_ready<<" commit_ack_cycle="<<tm.commit_ack<<" descriptor_presented_cycle="<<tm.descriptor_presented<<" queue_cycles="<<tm.admission-tm.packet_complete<<" validated_decode_model_cycles="<<tm.validated_ready-tm.packet_complete<<" post_validated_ack_model_cycles="<<tm.commit_ack-tm.validated_ready<<" met_serial_30fps_budget="<<((tm.commit_ack-tm.packet_complete)*30<=100000000)<<" met_validated_under10ms="<<(tm.validated_ready-tm.packet_complete<1000000)<<" first_correct_pixel_ps="<<tm.first_correct_pixel_ps<<" last_correct_pixel_ps="<<tm.last_correct_pixel_ps<<" first_complete_raster_start_ps="<<tm.first_complete_raster_start_ps<<" first_complete_raster_end_ps="<<tm.first_complete_raster_end_ps<<" complete_rasters="<<tm.complete_rasters<<" native_hud_prepare_wall_ns="<<tm.native_hud_wall_ns<<std::endl;
 }
 std::cout<<"SYSTEM_PASS distinct_complete_presentations="<<distinct_complete<<" complete_frames="<<frames<<" canonical_bytes_per_frame=518400 RGB_DDR_words_written_per_frame=0 HUD_functional_readback_words_per_frame=21120 clean_lines="<<s.good_lines<<" black_lines="<<s.black_lines<<" observed_pixels="<<s.pixels<<" total_underruns="<<s.d.lcd_underruns<<" cycles="<<s.cycles<<" max_input_queue="<<s.max_input_queue<<" physical_fps_proven=0"<<std::endl;
 }catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<std::endl;return 1;}}
