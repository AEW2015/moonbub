#include "Vcu70_receiver.h"
#include "verilated.h"
#include "../../../../experiments/cu66-native-v69/decoder.hpp"
#include "../../cu66-v69/hud-partition/hud_gate.hpp"
#include "../memory/memory_map.hpp"
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <random>
#include <sstream>

static void need(bool b,const std::string&s){if(!b)throw std::runtime_error(s);}
static cu66::Bytes load(const std::filesystem::path&p){std::ifstream f(p,std::ios::binary);need(bool(f),"fixture open");return {std::istreambuf_iterator<char>(f),{}};}
static unsigned hb(unsigned b){need(b<3,"HUD bank");return b==0?cu70_map::HUD0_BASE:b==1?cu70_map::HUD1_BASE:cu70_map::HUD2_BASE;}
template<class W>static cu66::Tag tag_from(const W&w){cu66::Tag t{};for(unsigned i=0;i<16;i++)t[i]=uint8_t(w[3-i/4]>>(24-8*(i%4)));return t;}
template<class W>static void tag_to(W&w,const cu66::Tag&t){for(unsigned i=0;i<4;i++){uint32_t v=0;for(unsigned j=0;j<4;j++)v=(v<<8)|t[i*4+j];w[3-i]=v;}}
struct Event{
 bool start,packet_request,packet_response,read_request,read_response,write_request,write_response,hud_prepare,hud_result,hud_drain,command,ack,paint,paint_result,presentation;
 uint64_t generation;unsigned fid,rid,bank;
 unsigned packet_address,packet_sequence,read_bank,read_plane,read_index,write_bank,write_plane,write_index;
 uint64_t packet_generation,read_generation,write_generation;
 std::array<uint32_t,16> write_pixels;
 unsigned hud_address,hud_length,command_opcode;bool key,rgb;
};
struct Sim{
 Vcu70_receiver d;std::mt19937 rng;bool randomize;uint64_t clocks=0,generation=0;
 std::vector<uint16_t> mem=std::vector<uint16_t>(1u<<24,0xa55a);
 cu66_partition::HudGate hud;cu66::Bytes packet;std::shared_ptr<const cu66::Frame> expected;
 unsigned mode=0,ordinal=0;uint64_t started=0;
 bool pp=false,rp=false,wp=false,hu=false,hu_result_sent=false,hu_drain_sent=false,sp=false,ap=false,dp=false;
 unsigned pd=0,rd=0,wd=0,hu_delay=0,hu_cursor=0,soft_delay=0,paint_delay=0,display_delay=0;
 unsigned pa=0,ps=0,rb=0,ra=0,ri=0,wb=0,wa=0,wi=0,soft_op=0,display_fid=0,display_slot=0;
 uint64_t pg=0,rg=0,wg=0,soft_gen=0,display_gen=0,last_abort_gen=0;
 unsigned last_abort_fid=0;
 std::array<uint32_t,16> wbuf{};
 std::shared_ptr<const cu66_partition::HudCache> candidate;
 bool hu_success=false,soft_success=false,dropped_ack=false,abort_started=false,stale_packet_sent=false,stale_other_sent=false;
 bool fake_packet=false,fake_other=false;unsigned commits_this_frame=0,aborts_this_frame=0;
 std::vector<unsigned> hud_rect_offsets;
 explicit Sim(unsigned seed):rng(seed),randomize(seed!=0){reset();}
 unsigned delay(unsigned max=5){return randomize?1+rng()%max:0;}
 void reset(){d.clk=0;d.rst=1;d.abort_i=0;d.clear_fault=0;d.start_valid=0;d.packet_rsp_valid=0;d.ref_rsp_valid=0;d.write_done_valid=0;d.hud_result_valid=0;d.hud_drain_valid=0;d.software_ack_valid=0;d.paint_result_valid=0;d.vblank=0;d.packet_req_ready=0;d.ref_req_ready=0;d.write_ready=0;d.hud_prepare_ready=0;d.software_command_ready=0;d.paint_start_ready=0;d.presentation_ready=0;d.memory_drained=1;d.painter_drained=1;d.scanout_drained=1;d.diag_address=0;step(false);step(false);d.rst=0;step(false);hud=cu66_partition::HudGate();pp=rp=wp=hu=sp=ap=dp=false;candidate=nullptr;}
 Event step(bool check=true){d.clk=0;d.eval();Event e{};
 e.start=d.start_valid&&d.start_ready;e.packet_request=d.packet_req_valid&&d.packet_req_ready;e.packet_response=d.packet_rsp_valid&&d.packet_rsp_ready;
 e.read_request=d.ref_req_valid&&d.ref_req_ready;e.read_response=d.ref_rsp_valid&&d.ref_rsp_ready;e.write_request=d.write_valid&&d.write_ready;e.write_response=d.write_done_valid&&d.write_done_ready;
 e.hud_prepare=d.hud_prepare_valid&&d.hud_prepare_ready;e.hud_result=d.hud_result_valid&&d.hud_result_ready;e.hud_drain=d.hud_drain_valid&&d.hud_drain_ready;
 e.command=d.software_command_valid&&d.software_command_ready;e.ack=d.software_ack_valid&&d.software_ack_ready;e.paint=d.paint_start_valid&&d.paint_start_ready;e.paint_result=d.paint_result_valid&&d.paint_result_ready;e.presentation=d.presentation_valid&&d.presentation_ready;
 e.generation=d.active_generation;e.fid=d.active_frame_id;e.rid=d.active_reference_id;e.bank=d.candidate_bank;e.key=d.active_key;
 e.packet_address=d.packet_req_address;e.packet_generation=d.packet_req_generation;e.packet_sequence=d.packet_req_sequence;
 e.read_bank=d.ref_req_bank;e.read_plane=d.ref_req_plane;e.read_index=d.ref_req_index;e.read_generation=d.ref_req_generation;
 e.write_bank=d.write_bank;e.write_plane=d.write_plane;e.write_index=d.write_index;e.write_generation=d.write_generation;
 for(unsigned i=0;i<16;i++)e.write_pixels[i]=d.write_pixels[i];
 e.hud_address=d.hud_address;e.hud_length=d.hud_bytes;e.command_opcode=d.software_command_opcode;e.rgb=d.paint_rgb_slot;
 if(check){
  need(!(e.write_request&&d.reference_valid&&e.write_bank==d.reference_bank),"candidate overwrote accepted reference");
  need(!(e.write_request&&d.front_valid&&e.write_bank==d.front_bank),"candidate overwrote front canonical bank");
  if(e.write_request&&expected){unsigned a=ordinal<5400?0:ordinal<6750?1:2,b=ordinal-(a==0?0:a==1?5400:6750),width=a?360:720;need(e.write_plane==a&&e.write_index==b&&e.fid==expected->id,"tile order/frame identity");for(unsigned i=0;i<64;i++){unsigned at=(b/(width/8)*8+i/8)*width+(b%(width/8))*8+i%8;need(uint8_t(e.write_pixels[i/4]>>(8*(i%4)))==expected->planes[a][at],"canonical RTL output mismatch");}ordinal++;}
 }
 d.clk=1;d.eval();clocks++;need(clocks<10000000000ull,"global watchdog");return e;
 }
 unsigned word_address(unsigned bank,unsigned plane,unsigned tile,unsigned row,unsigned pair){need(bank<3&&plane<3,"canonical geometry");unsigned width=plane?360:720,base=cu70_map::canonical_base(bank)+(plane==0?0:plane==1?172800:216000);unsigned bwidth=width/8;unsigned at=base+(tile/bwidth*8+row)*(width/2)+(tile%bwidth)*4+pair;need(cu70_map::allowed(at),"mapped canonical address");return at;}
 void drive(){
  d.packet_req_ready=!pp&&(!randomize||rng()%5!=0);d.packet_rsp_valid=pp&&pd==0;fake_packet=false;
  d.packet_rsp_generation=pg;d.packet_rsp_sequence=ps;d.packet_rsp_address=pa;d.packet_rsp_data=d.packet_rsp_valid?packet.at(pa):0;
  if(mode==5&&d.packet_rsp_valid&&!stale_packet_sent){fake_packet=true;d.packet_rsp_sequence=ps+1;d.packet_rsp_data^=0xff;}
  d.ref_req_ready=!rp&&(!randomize||rng()%5!=0);d.ref_rsp_valid=rp&&rd==0;d.ref_rsp_generation=rg;d.ref_rsp_bank=rb;d.ref_rsp_plane=ra;d.ref_rsp_index=ri;d.ref_rsp_error=0;
  if(d.ref_rsp_valid)for(unsigned w=0;w<16;w++){unsigned row=w/2,pair=(w%2)*2;uint32_t lo=mem.at(word_address(rb,ra,ri,row,pair)),hi=mem.at(word_address(rb,ra,ri,row,pair+1));d.ref_rsp_pixels[w]=lo|(hi<<16);}
  d.write_ready=!wp&&(!randomize||rng()%5!=0);d.write_done_valid=wp&&wd==0;d.write_done_generation=wg;d.write_done_bank=wb;d.write_done_plane=wa;d.write_done_index=wi;d.write_done_error=mode==4;
  d.hud_prepare_ready=!hu;d.hud_result_valid=hu&&!hu_result_sent&&hu_delay==0;d.hud_result_generation=generation;d.hud_result_frame_id=d.active_frame_id;d.hud_result_reference_id=d.active_reference_id;d.hud_result_success=hu_success;d.hud_result_words=21120;tag_to(d.hud_result_tag,candidate?candidate->tag:cu66::Tag{});
  d.hud_drain_valid=hu&&hu_success&&candidate&&hu_result_sent&&!hu_drain_sent&&hu_cursor==21120;d.hud_drain_generation=generation;d.hud_drain_frame_id=d.active_frame_id;d.hud_drain_bank=d.candidate_bank;d.hud_drain_success=mode!=3;d.hud_drain_words=21120;tag_to(d.hud_drain_tag,candidate?candidate->tag:cu66::Tag{});
  d.software_command_ready=!sp;d.software_ack_valid=sp&&soft_delay==0;d.software_ack_opcode=soft_op;d.software_ack_generation=soft_gen;d.software_ack_frame_id=d.active_frame_id;d.software_ack_success=soft_success;
  d.paint_start_ready=!ap;d.paint_result_valid=ap&&paint_delay==0;d.paint_result_generation=generation;d.paint_result_frame_id=d.active_frame_id;d.paint_result_success=mode!=6;
  d.presentation_ready=!dp;d.vblank=dp&&display_delay==0;d.presented_generation=display_gen;d.presented_frame_id=display_fid;d.presented_rgb_slot=display_slot;d.scanout_drained=1;
  d.memory_drained=!rp&&!wp&&(!hu||hu_cursor==21120||!hu_success);d.painter_drained=!ap;
  fake_other=false;
  if(mode==5&&stale_packet_sent&&!stale_other_sent&&d.stage==5){fake_other=true;d.hud_result_valid=1;d.hud_result_generation=generation-1;d.hud_drain_valid=1;d.hud_drain_generation=generation-1;d.software_ack_valid=1;d.software_ack_generation=generation-1;d.software_ack_opcode=5;}
 }
 void service(const Event&e){
  if(pp&&pd)pd--;if(rp&&rd)rd--;if(wp&&wd)wd--;if(hu_delay)hu_delay--;if(sp&&soft_delay)soft_delay--;if(ap&&paint_delay)paint_delay--;if(dp&&display_delay)display_delay--;
  if(e.packet_response){if(fake_packet)stale_packet_sent=true;else pp=false;}
  if(e.packet_request){need(!pp,"multiple packet reads");pp=true;pd=delay();pa=e.packet_address;pg=e.packet_generation;ps=e.packet_sequence;need(pa<packet.size(),"packet address bound");}
  if(e.read_response)rp=false;
  if(e.read_request){need(!rp,"multiple reference reads");rp=true;rd=delay(9);rb=e.read_bank;ra=e.read_plane;ri=e.read_index;rg=e.read_generation;}
  if(e.write_response){if(mode!=4)for(unsigned row=0;row<8;row++)for(unsigned pair=0;pair<4;pair++){unsigned i=row*8+pair*2;mem.at(word_address(wb,wa,wi,row,pair))=uint16_t(wbuf[i/4]>>(8*(i%4)));}wp=false;}
  if(e.write_request){need(!wp,"multiple writes");wp=true;wd=mode==2?5:delay(11);wb=e.write_bank;wa=e.write_plane;wi=e.write_index;wg=e.write_generation;wbuf=e.write_pixels;}
  if(e.hud_prepare){hu=true;hu_delay=delay(8);hu_result_sent=false;hu_drain_sent=false;hu_cursor=0;candidate=nullptr;auto reply=hud.prepare(e.generation,e.fid,e.rid,e.key,cu66::View(packet).sub(e.hud_address,e.hud_length));hu_success=reply==cu66_partition::Reply::Accepted;candidate=hud.read_candidate(e.generation,e.fid);if(!hu_success)hu_cursor=21120;}
  if(e.hud_result&&!fake_other)hu_result_sent=true;
  if(hu&&hu_success&&hu_result_sent&&hu_cursor<21120&&(!randomize||rng()%3!=0)){
   unsigned at=0;for(auto&p:candidate->patches){if(hu_cursor<at+p.words.size()){mem.at(hb(d.candidate_bank)+hu_cursor)=p.words[hu_cursor-at];break;}at+=p.words.size();}hu_cursor++;
  }
  if(e.hud_drain&&!fake_other){hu_drain_sent=true;if(mode!=3){auto copy=candidate->patches;unsigned at=0;for(auto&p:copy)for(auto&w:p.words)w=mem.at(hb(d.candidate_bank)+at++);need(cu66::hud_tag(copy)==candidate->tag,"actual HUD memory readback tag");need(hud.acknowledge_external_write_drain(generation,candidate->id,21120,cu66::hud_tag(copy)),"HUD transfer ACK");}}
  if(fake_other)stale_other_sent=true;
  if(e.ack&&!fake_other)sp=false;
  if(e.command){need(!sp,"multiple software commands");soft_op=e.command_opcode;soft_gen=e.generation;soft_delay=delay(7);if(soft_op==5){commits_this_frame++;soft_success=hud.commit(e.generation,e.fid);if(mode==7&&!dropped_ack){dropped_ack=true;sp=false;}else sp=true;}else{aborts_this_frame++;if(last_abort_gen==e.generation&&last_abort_fid==e.fid)soft_success=true;else{soft_success=hud.abort(e.generation,e.fid);if(soft_success){last_abort_gen=e.generation;last_abort_fid=e.fid;}}sp=true;}}
  if(e.paint){need(!ap,"multiple painter starts");ap=true;paint_delay=delay(9);}
  if(e.paint_result)ap=false;
  if(d.vblank)dp=false;
  if(e.presentation){need(!dp,"multiple descriptors");dp=true;display_gen=d.presentation_generation;display_fid=d.presentation_frame_id;display_slot=d.presentation_rgb_slot;display_delay=delay(13);}
 }
 void idle(unsigned n=3){for(unsigned i=0;i<n;i++){drive();auto e=step(false);service(e);}}
 std::array<cu66::Bytes,3> read_canonical(unsigned bank){std::array<cu66::Bytes,3> p;for(unsigned a=0;a<3;a++){unsigned n=a?86400:345600,base=cu70_map::canonical_base(bank)+(a==0?0:a==1?172800:216000);p[a].resize(n);for(unsigned i=0;i<n;i++)p[a][i]=uint8_t(mem.at(base+i/2)>>(8*(i%2)));}return p;}
 void run(cu66::Bytes input,std::shared_ptr<const cu66::Frame>gold,unsigned fault=0){
  idle();need(d.start_ready,"receiver not ready");packet=std::move(input);expected=gold;mode=fault;generation++;ordinal=0;candidate=nullptr;hu=false;hu_cursor=21120;commits_this_frame=aborts_this_frame=0;dropped_ack=false;abort_started=false;stale_packet_sent=stale_other_sent=false;
  bool old_ref=d.reference_valid;unsigned old_id=d.reference_frame_id,old_bank=d.reference_bank,old_count=d.accepted_count;auto old_hud=hud.accepted();auto old_tag=tag_from(d.reference_tag);uint64_t stale0=d.stale_completions;
  if(mode==1)packet.back()^=1;
  d.start_generation=generation;d.start_packet_bytes=packet.size();d.start_valid=1;need(step().start,"start handshake");d.start_valid=0;started=clocks;bool finished=false;unsigned error_seen=0;
  while(!finished){need(clocks-started<30000000,"transaction watchdog stage="+std::to_string(d.stage)+" error="+std::to_string(d.error_code));drive();
   if(mode==2&&!abort_started&&wp&&wd>0){d.abort_i=1;abort_started=true;}
   auto e=step(mode!=1);service(e);d.abort_i=0;if(d.error)error_seen=d.error_code;
   if(mode==7&&d.accepted_count!=old_count&&!d.done)need(!d.start_ready,"new dependent frame admitted before HUD reconciliation");
   if(d.done||d.aborted||(!d.busy&&d.error))finished=true;
  }
  bool success=fault==0||fault==5||fault==7;
  if(success){need(d.done&&d.accepted_count==old_count+1&&d.reference_valid,"successful global commit");need(gold&&ordinal==8100&&d.reference_frame_id==gold->id,"complete canonical frame");auto actual=read_canonical(d.reference_bank);need(cu66::canonical_tag(actual)==gold->canonical_tag&&tag_from(d.reference_tag)==gold->canonical_tag,"stored RTL reference tag");need(hud.accepted()&&hud.accepted()->id==gold->id&&hud.accepted()->tag==cu66::hud_tag(gold->hud),"accepted software HUD joins same frame");if(mode==5)need(d.stale_completions-stale0>=4,"stale notification count");if(mode==7)need(commits_this_frame>=2,"lost commit ACK not retried");}
  else{need(d.accepted_count==old_count&&d.reference_valid==old_ref&&d.reference_frame_id==old_id&&d.reference_bank==old_bank&&tag_from(d.reference_tag)==old_tag,"failed candidate changed accepted reference");need(hud.accepted()==old_hud,"failed candidate changed accepted HUD");if(mode==2)need(abort_started,"write abort probe not reached");else need(error_seen!=0,"fault missing");}
  for(unsigned i=0;i<200&&dp;i++)idle(1);
  if(success)need(d.front_valid&&d.front_frame_id==gold->id,"presentation descriptor ACK failed");
  std::cout<<"FRAME_PASS fid="<<(gold?gold->id:0xffffffffu)<<" key="<<(gold?gold->key:0)<<" mode="<<mode<<" clocks="<<clocks-started<<" tiles="<<ordinal<<" error="<<error_seen<<" commits="<<commits_this_frame<<" abort_commands="<<aborts_this_frame<<" stale="<<d.stale_completions-stale0<<" reference_bank="<<unsigned(d.reference_bank)<<std::endl;
 }
};
int main(int argc,char**argv){try{need(argc>=4,"index seed per_chain");std::filesystem::path index=argv[1];unsigned seed=unsigned(std::stoul(argv[2])),limit=unsigned(std::stoul(argv[3]));Sim sim(seed);std::ifstream f(index);need(bool(f),"index open");std::string line;unsigned chain=~0u,n=0,frames=0;cu66::Decoder decoder;cu66::Bytes first,second,recovery;std::shared_ptr<const cu66::Frame> first_gold,second_gold,recovery_gold;
 while(std::getline(f,line)){std::stringstream s(line);std::string a,b,path;std::getline(s,a,'\t');std::getline(s,b,'\t');std::getline(s,path,'\t');unsigned c=unsigned(std::stoul(a));if(c!=chain){chain=c;n=0;decoder=cu66::Decoder();sim.reset();}if(c==0&&std::stoul(b)==24){recovery=load(index.parent_path()/path);cu66::Decoder independent;recovery_gold=independent.receive(recovery);need(recovery_gold->key&&recovery_gold->id==24,"recovery key24");}if(n++>=limit)continue;auto p=load(index.parent_path()/path);auto gold=decoder.receive(p);sim.run(p,gold);if(frames==0){first=p;first_gold=gold;}if(frames==1){second=p;second_gold=gold;}frames++;}
 need(frames>=2,"key/P coverage");for(unsigned mode=1;mode<=7;mode++){sim.reset();sim.run(first,first_gold);if(mode==5||mode==7)sim.run(second,second_gold,mode);else sim.run(second,mode==1?nullptr:second_gold,mode);sim.run(recovery,recovery_gold);}
 std::cout<<"PASS actual_frames="<<frames<<" fault_and_control_modes=7 seed="<<seed<<" clocks="<<sim.clocks<<" memory_backend=transactional_RAM painter=completion_model scanout=descriptor_model"<<std::endl;
 }catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<std::endl;return 1;}}
