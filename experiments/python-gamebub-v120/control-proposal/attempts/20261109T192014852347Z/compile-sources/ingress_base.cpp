#include "Vingress_probe.h"
#include "Vingress_probe___024root.h"
#include "verilated.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <optional>
#include <random>
#include <stdexcept>
#include <string>
#include <tuple>
#include <vector>
static void need(bool ok,const std::string& why){if(!ok)throw std::runtime_error(why);}
#include "writer_scoreboard.hpp"
struct PacketCase{std::string id;unsigned blocks;std::vector<uint8_t> packet,dense;};
static std::vector<uint8_t> bytes(const std::string&s){need(s.size()%2==0,"hexsize");std::vector<uint8_t>o;for(size_t i=0;i<s.size();i+=2)o.push_back(uint8_t(std::stoul(s.substr(i,2),nullptr,16)));return o;}
static uint32_t little(const std::vector<uint8_t>&p,unsigned a){return uint32_t(p[a])|(uint32_t(p[a+1])<<8)|(uint32_t(p[a+2])<<16)|(uint32_t(p[a+3])<<24);}
static void set32(std::vector<uint8_t>&p,unsigned at,uint32_t value){for(unsigned j=0;j<4;++j)p[at+j]=uint8_t(value>>(8*j));}
static void crc(std::vector<uint8_t>&p){uint32_t x=0xffffffffU;for(unsigned i=0;i<p.size()-4;++i){x^=p[i];for(unsigned j=0;j<8;++j)x=(x>>1)^((x&1)?0xedb88320U:0);}set32(p,unsigned(p.size()-4),x^0xffffffffU);}
struct Coef{unsigned band,block,index;int16_t value;};
// Independent dense-to-sparse value/order oracle, unchanged from the historical
// packet checker; it does not inspect implementation descriptor/cache registers.
static std::vector<Coef> golden(const PacketCase&c){std::vector<Coef>o;std::array<unsigned,64>order{};unsigned rank=0;for(unsigned diag=0;diag<15;++diag)for(unsigned step=0;step<8;++step){int row=diag%2?int(step):7-int(step),col=int(diag)-row;if(col>=0&&col<8)order[rank++]=unsigned(row*8+col);}need(rank==64,"zigzag permutation");const bool raw=c.packet[5]==1;for(unsigned band=0;band<(raw?1U:4U);++band)for(unsigned block=0;block<c.blocks;++block)for(unsigned z=0;z<(raw?64U:band==0?1U:64U);++z){unsigned i=raw?z:order[z];if(!raw&&band&&(z==0||(z<6?1U:z<21?2U:3U)!=band))continue;unsigned at=(block*64+i)*2;int16_t v=int16_t(unsigned(c.dense[at])|(unsigned(c.dense[at+1])<<8));if(raw||band==0||v)o.push_back({band,block,i,v});}return o;}
struct Run{
 Vingress_probe d;std::mt19937 rng;uint64_t edges=0,requests=0,responses=0,canceled_reads=0,outputs=0,packets=0,cancels=0,held=0;uint32_t next_epoch=1000;bool pending=false;uint32_t expected_addr=0,expected_epoch=0;std::array<uint64_t,4>kinds{};unsigned boundary_mask=0,selection_desc=0,selection_ctx=0,word_hold=0;
 const std::vector<uint8_t>*image=nullptr;
 using Tuple=std::tuple<unsigned,unsigned,unsigned,int16_t,uint32_t>;
 std::optional<Tuple> hold_output;
 explicit Run(unsigned seed):rng(seed){d.clk=0;d.reset=1;d.start=d.abort_packet=d.in_valid=0;d.out_ready=d.meta_ready=d.band_end_ready=0;d.packet_bytes=174;d.blocks=1;d.epoch=1;d.word16=d.serial_mode=0;d.in_data=d.in_last=0;tick();d.reset=0;}
 Tuple tuple(){return {d.out_band,d.out_block,d.out_index,int16_t(d.out_coefficient),d.out_epoch};}
 void tick(){d.clk=0;d.eval();const bool kill=d.stage_cancel,req=d.stage_read_req,rsp=d.stage_read_rsp;
  if(!kill&&hold_output)need(d.out_valid&&tuple()==*hold_output,"held output tuple changed");
  hold_output=!kill&&d.out_valid&&!d.out_ready?std::optional<Tuple>(tuple()):std::nullopt;
  const uint32_t addr=d.stage_read_addr,epoch=d.stage_req_epoch;
  if(rsp){need(pending&&!kill,"response lacks real request owner");need(d.stage_rsp_addr==expected_addr&&d.stage_rsp_epoch==expected_epoch&&d.probe_expected_addr==expected_addr,"response address/epoch owner mismatch");need(image&&expected_addr<image->size()&&d.stage_read_data==image->at(expected_addr),"synchronous read differs from admitted packet");++responses;unsigned kind=d.stage_purpose;need(kind<4,"purpose range");++kinds[kind];if(kind==0&&d.probe_fetch_index==41)boundary_mask|=1;if(kind==0&&d.probe_fetch_index==42)boundary_mask|=2;if(kind==0&&d.probe_fetch_index==45)boundary_mask|=4;if(kind==1&&d.probe_fetch_index==6)boundary_mask|=8;}
  if(kill&&pending)++canceled_reads;
  ControlPrivateStep private_step(d);d.clk=1;d.eval();d.clk=0;d.eval();private_step.finish(d);
  if(kill||rsp)pending=false;
  if(req){need(!pending,"more than one actual synchronous read owner");pending=true;expected_addr=addr;expected_epoch=epoch;++requests;need(d.probe_expected_addr==addr,"request-edge address capture differs");}
  need(++edges<120000000,"finite whole-ingress watchdog");
 }
 void clean(){d.reset=1;d.start=d.abort_packet=d.in_valid=0;tick();d.reset=0;}
 void noise(){d.packet_bytes=rng();d.blocks=rng()&131071U;d.epoch=rng();d.word16=rng()&1;d.serial_mode=rng()&1;}
 bool run(const PacketCase&c,unsigned mode,unsigned profile,int target=-1,int index=-1,unsigned action=0,unsigned expected_error=0,bool reset_first=true){if(reset_first)clean();image=&c.packet;const auto gold=golden(c);const uint32_t epoch=++next_epoch;
  d.start=1;d.packet_bytes=c.packet.size();d.blocks=c.blocks;d.epoch=epoch;d.word16=mode&1;d.serial_mode=(mode>>1)&1;d.in_valid=0;d.out_ready=d.meta_ready=d.band_end_ready=0;tick();d.start=0;unsigned at=0,out=0,ends=0,hold=0;
  bool metadata=false;std::optional<std::array<uint32_t,16>> hold_meta;
  for(unsigned n=0;!d.done&&!d.error;++n){need(n<5000000,"per-packet finite watchdog");noise();d.in_valid=at<c.packet.size()&&(!profile||rng()%4!=0);if(d.in_valid){d.in_data=c.packet[at];d.in_last=at+1==c.packet.size();}d.out_ready=!profile||rng()%4!=0;d.band_end_ready=!profile||rng()%4!=0;d.meta_ready=hold>=17;d.clk=0;d.eval();
   bool target_hit=target>=0&&target<4&&d.stage_purpose==unsigned(target)&&d.probe_fetch_index==unsigned(index)&&(action<3?d.stage_read_req:d.stage_read_rsp);
   if(target==4)target_hit=d.debug_state==14&&!d.probe_selection_context;
   if(target==5)target_hit=d.debug_state==14&&d.probe_selection_context;
   if(target==6)target_hit=d.debug_state==5&&d.stage_word_valid;
   if(target>=7&&target<=9)target_hit=d.probe_length_pipe==(1U<<unsigned(target-7));
   if(target==10)target_hit=d.probe_length_live&&d.stage_purpose==0&&d.probe_fetch_index<42;
   if(target>=11&&target<=14)target_hit=writer_initial_kind(d)==target-11;
   if(target_hit){unsigned op=action%3;if(op==0)d.abort_packet=1;else if(op==1)d.reset=1;else{d.start=1;d.packet_bytes=c.packet.size();d.blocks=c.blocks;d.epoch=++next_epoch;d.word16=mode&1;d.serial_mode=(mode>>1)&1;}d.eval();need(!d.out_valid&&!d.stage_read_req&&!d.stage_read_rsp&&!d.meta_valid&&!d.stage_word_valid,"same-edge cancel fence");tick();d.abort_packet=d.reset=d.start=0;d.in_valid=0;tick();need(!pending&&!d.stage_read_rsp&&!d.out_valid,"cancel retained synchronous read/output owner");++cancels;if(target==4)++selection_desc;if(target==5)++selection_ctx;if(target==6)++word_hold;return false;}
   bool input=d.in_valid&&d.in_ready,output=d.out_valid&&d.out_ready,end=d.band_end_valid&&d.band_end_ready;
   if(d.meta_valid){std::array<uint32_t,16>m={uint32_t(d.meta_blocks),d.meta_count1,d.meta_count2,d.meta_count3,d.meta_epoch,d.meta_prefix1,d.meta_prefix12,d.meta_prefix123,d.meta_threshold1,d.meta_threshold2,d.meta_threshold3,d.meta_capacity_upper,d.meta_capacity_lower,uint32_t(d.meta_capacity_wrap),uint32_t(d.meta_raw),epoch};need(d.meta_blocks==c.blocks&&d.meta_epoch==epoch&&d.meta_raw==(c.packet[5]==1),"metadata owner");need(d.meta_count1==little(c.packet,30)&&d.meta_count2==little(c.packet,34)&&d.meta_count3==little(c.packet,38),"metadata counts");if(hold_meta)need(m==*hold_meta,"held complete metadata tuple changed");if(!d.meta_ready)hold_meta=m;else hold_meta.reset();if(hold<17){++hold;++held;}metadata=true;}
   if(output){need(out<gold.size(),"extra coefficient");const auto&g=gold[out];need(d.out_band==g.band&&d.out_block==g.block&&d.out_index==g.index&&int16_t(d.out_coefficient)==g.value&&d.out_epoch==epoch,"dense-derived coefficient tuple/order mismatch "+c.id);++out;++outputs;}
   if(end){need(d.band_end_band==ends&&d.band_end_epoch==epoch,"band-end order/epoch");++ends;}
   tick();if(input)++at;
  }
  if(expected_error){need(d.error==expected_error&&!d.done&&!metadata&&out==0,"malformed packet terminal contract");return true;}
  need(!d.error&&d.done&&metadata&&out==gold.size()&&ends==(c.packet[5]==1?1U:4U)&&at==c.packet.size()&&!pending,"packet completion/content count "+c.id);need(d.count_inputs==c.packet.size()&&d.count_stage_writes==c.packet.size()&&d.count_outputs==gold.size(),"actual ingress public counters");++packets;return true;
 }
};
int inherited_ingress_main(int argc,char**argv){try{need(argc==3,"usage seed packet-vectors");unsigned seed=std::stoul(argv[1]);std::ifstream in(argv[2]);need(bool(in),"vector input open");std::vector<PacketCase>cs;std::string p,d,s;for(PacketCase c;in>>c.id>>c.blocks>>p>>d>>s;){c.packet=bytes(p);c.dense=bytes(d);cs.push_back(c);}need(cs.size()==20,"full historical packet corpus");Run w(seed);
 for(const auto&c:cs)for(unsigned mode=0;mode<4;++mode)for(unsigned profile=0;profile<2;++profile)w.run(c,mode,profile);
 auto raw=std::find_if(cs.begin(),cs.end(),[](const auto&c){return c.packet[5]==1;});auto sparse=std::find_if(cs.begin(),cs.end(),[](const auto&c){return c.packet[5]==0;});need(raw!=cs.end()&&sparse!=cs.end(),"raw/sparse fixtures");
 for(const auto&target:std::array<std::pair<int,int>,9>{{{0,41},{0,42},{0,45},{1,6},{2,0},{3,1},{4,0},{5,0},{6,0}}})for(unsigned action=0;action<6;++action){const auto&c=target.first==3?*raw:*sparse;need(!w.run(c,action%4,1,target.first,target.second,action),"cancel point not reached");need(w.run(c,action%4,1,-1,-1,0,0,false),"clean non-reset retry failed");}
 unsigned malformed=0;
 for(unsigned kind=0;kind<4;++kind){auto c=*sparse;c.id+="-malformed-"+std::to_string(kind);if(kind==0)c.packet.back()^=1;else if(kind==1){auto n=little(c.packet,14);set32(c.packet,14,5);set32(c.packet,26,little(c.packet,26)+n-5);crc(c.packet);}else if(kind==2){set32(c.packet,44,0xffffffffU);crc(c.packet);}else{c.packet[42]=255;crc(c.packet);}w.run(c,0,1,-1,-1,0,kind==0?3:4);++malformed;need(w.run(*sparse,0,1,-1,-1,0,0,false),"post-malformed retry failed");}
 need(w.boundary_mask==15&&w.cancels==54&&w.selection_desc==6&&w.selection_ctx==6&&w.word_hold==6,"all added/boundary cancel phases covered");need(w.requests==w.responses+w.canceled_reads,"actual synchronous read owner conservation");
 const unsigned initial_cancel_retries=w.cancels,initial_successful_packets=w.packets;
 unsigned refined_cancel_checks=0,refined_length_checks=0;
 for(const auto&target:std::array<std::pair<int,int>,5>{{{0,29},{7,0},{8,0},{9,0},{10,0}}})for(unsigned action=0;action<6;++action){
  need(!w.run(*sparse,action%4,1,target.first,target.second,action),"refined pipeline cancel point not reached");
  need(w.run(*sparse,action%4,1,-1,-1,0,0,false),"refined pipeline non-reset retry failed");++refined_cancel_checks;
 }
 const uint32_t remaining=uint32_t(sparse->packet.size()-46);
 const std::array<std::array<uint32_t,4>,10> length_cases{{
  {{0xffffffffU,0xffffffffU,0xffffffffU,0xffffffffU}},
  {{0x40000000U,0x40000000U,0x40000000U,0x40000000U}},
  {{0x80000000U,0x80000000U,0x80000000U,0x80000000U}},
  {{0xffffffffU,remaining+1U,0,0}},
  {{0xffffffffU,0xffffffffU,remaining+2U,0}},
  {{remaining,0,0,0}},{{0,remaining,0,0}},
  {{remaining+1U,0,0,0}},{{remaining-1U,0,0,0}},
  {{0,0,0,0x01000000U}}
 }};
 for(unsigned i=0;i<length_cases.size();++i){auto c=*sparse;c.id+="-refined-length-"+std::to_string(i);for(unsigned j=0;j<4;++j)set32(c.packet,14+4*j,length_cases[i][j]);crc(c.packet);
  w.run(c,0,1,-1,-1,0,4);++refined_length_checks;need(w.run(*sparse,0,1,-1,-1,0,0,false),"refined length-reject clean retry failed");
 }
 // CRC has the original first-cause priority even when length arithmetic is bad.
 {auto c=*sparse;c.id+="-refined-crc-priority";set32(c.packet,26,0xffffffffU);crc(c.packet);c.packet.back()^=1;w.run(c,0,1,-1,-1,0,3);++refined_length_checks;need(w.run(*sparse,0,1,-1,-1,0,0,false),"refined CRC clean retry failed");}
 need(initial_cancel_retries==54&&initial_successful_packets==218&&refined_cancel_checks==30&&refined_length_checks==11,"refined additive coverage incomplete");
 need(w.requests==w.responses+w.canceled_reads,"refined complete synchronous read conservation");
 need(w.d.probe_public_pair_checks==w.edges,"exact public pair checker did not execute every clock");

 std::cout<<"{\"type\":\"ingress_verdict\",\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"corpus_profiles\":160,\"successful_packets\":"<<w.packets<<",\"cancel_retries\":"<<w.cancels<<",\"new_descriptor_cancel_checks\":"<<w.selection_desc<<",\"new_context_cancel_checks\":"<<w.selection_ctx<<",\"word_tuple_cancel_checks\":"<<w.word_hold<<",\"malformed_checks\":"<<malformed<<",\"requests\":"<<w.requests<<",\"responses\":"<<w.responses<<",\"canceled_read_owners\":"<<w.canceled_reads<<",\"coefficients\":"<<w.outputs<<",\"refined_cancel_checks\":"<<refined_cancel_checks<<",\"refined_length_checks\":"<<refined_length_checks<<",\"initial_cancel_retries\":"<<initial_cancel_retries<<",\"initial_successful_packets\":"<<initial_successful_packets<<",\"public_cycle_pair_checks\":"<<w.d.probe_public_pair_checks<<",\"clock_edges\":"<<w.edges<<"}\n";return 0;
}catch(const std::exception&e){std::cerr<<"INGRESS_V115_FAIL "<<e.what()<<'\n';return 1;}}
