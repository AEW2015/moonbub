#include "Vingress_capture_probe.h"
#include "Vingress_capture_probe___024root.h"
#include "Vingress_capture_probe__Syms.h"
#include "verilated.h"
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>
#include <deque>
static void need(bool yes,const std::string&why){if(!yes)throw std::runtime_error(why);}
#define OLD(n) r.ingress_capture_probe__DOT__old_dut__DOT__##n
#define NEW(n) r.ingress_capture_probe__DOT__new_dut__DOT__##n
#define BOTH(n,v) do{const auto z=(v);OLD(n)=z;NEW(n)=z;}while(0)
#define CTXO(n) r.ingress_capture_probe__DOT__old_dut__DOT__context_decoder__DOT__##n
#define CTXN(n) r.ingress_capture_probe__DOT__new_dut__DOT__context_decoder__DOT__##n
#define CBOTH(n,v) do{const auto z=(v);CTXO(n)=z;CTXN(n)=z;}while(0)
static uint32_t align_count(uint32_t n){return uint32_t(n*4U+15U)&0xfffffff0U;}
struct Bench {
 Vingress_capture_probe d;std::mt19937 rng;std::ofstream trace;std::array<uint32_t,3>a{};uint32_t p12=0,p123=0;uint64_t edges=0,captures=0,held=0,prepared=0,raw_packets=0,restarts=0;std::array<uint64_t,12> modes{};std::array<uint64_t,3> capture_indices{};
 std::array<std::deque<std::pair<uint64_t,uint32_t>>,3> threshold_queue;
 std::array<uint32_t,3> thresholds{};unsigned threshold_live=0;
 uint64_t threshold_commits=0,threshold_flush_commits=0,commit_abort_retries=0;
 std::deque<std::pair<uint64_t,uint32_t>> capacity_queue;
 uint32_t capacity_upper=0,capacity_lower=0;bool capacity_wrap=false,capacity_live=false;
 uint64_t capacity_commits=0,capacity_flush_commits=0,capacity_abort_retries=0;
 static std::array<uint32_t,3> capacity_bounds(uint32_t prefix){const uint32_t a=((prefix>>4)+2U)&0x0fffffffU;return {((16384U-a)&0x0fffffffU)<<3,((~a)&0x0fffffffU)<<3,uint32_t(a>16384U)};}

 static uint32_t ceil_count(uint32_t n,unsigned g){const unsigned d=g==0?5:g==1?15:43;return n/d+uint32_t(n%d!=0);}
 Bench(unsigned seed,const char*path):rng(seed),trace(path){need(bool(trace),"trace open");d.clk=0;d.reset=1;d.start=0;d.abort_packet=0;d.packet_bytes=174;d.blocks=1;d.epoch=123;d.word16=0;d.serial_mode=0;d.in_valid=0;d.in_data=0;d.in_last=0;d.out_ready=0;d.meta_ready=0;d.band_end_ready=0;tick(false,-1,0);d.reset=0;}
 void check(){
  need(d.verify_capacity_upper==capacity_upper&&d.verify_capacity_lower==capacity_lower&&bool(d.verify_capacity_wrap)==capacity_wrap,"independent four-edge bound tuple arithmetic/hold");
  need(bool(d.verify_capacity_live)==capacity_live,"independent capacity validity/flush owner");
  if(d.meta_valid){const auto c=capacity_bounds(p123);need(capacity_live&&capacity_upper==c[0]&&capacity_lower==c[1]&&capacity_wrap==bool(c[2]),"actual owned metadata capacity bounds");}

  need(d.meta_threshold1==thresholds[0]&&d.meta_threshold2==thresholds[1]&&d.meta_threshold3==thresholds[2],"independent eight-edge threshold cache arithmetic/hold");
  need(d.verify_threshold_live==threshold_live,"independent threshold validity/flush ownership");need(!d.mismatch,"all original ingress public ports differ including invalid/debug/counters");need(d.verify_a1==a[0]&&d.verify_a2==a[1]&&d.verify_a3==a[2],"actual private count capture/hold");need(d.meta_prefix1==a[0]&&d.meta_prefix12==p12&&d.meta_prefix123==p123,"actual unreset nonblocking prefix pipeline");}
 void tick(bool expected_capture,int capture_index,uint32_t count){
  d.clk=0;d.eval();check();need(bool(d.verify_capture)==expected_capture,"actual production capture eligibility");const uint32_t next12=a[0]+a[1],next123=p12+a[2];
  if(expected_capture&&capture_index>=0){a[unsigned(capture_index)]=align_count(count);++captures;++capture_indices[unsigned(capture_index)];}
  const auto&r=*d.rootp;const bool flush=d.stage_cancel||(d.stage_context_active&&CTXN(done));
  for(unsigned g=0;g<3;++g){
   bool commit=!threshold_queue[g].empty()&&threshold_queue[g].front().first==edges;
   if(commit){thresholds[g]=ceil_count(threshold_queue[g].front().second,g);threshold_queue[g].pop_front();++threshold_commits;if(flush)++threshold_flush_commits;}
   if(flush){threshold_queue[g].clear();threshold_live&=~(1U<<g);}else if(commit)threshold_live|=1U<<g;
   if(expected_capture&&capture_index==int(g)&&!flush)threshold_queue[g].push_back({edges+8,count});
   need(threshold_queue[g].size()<=8,"threshold pipeline finite owner bound");
  }
  const bool cap_commit=!capacity_queue.empty()&&capacity_queue.front().first==edges;
  if(cap_commit){const auto c=capacity_bounds(capacity_queue.front().second);capacity_queue.pop_front();capacity_upper=c[0];capacity_lower=c[1];capacity_wrap=bool(c[2]);++capacity_commits;if(flush)++capacity_flush_commits;}
  if(flush){capacity_queue.clear();capacity_live=false;}else if(cap_commit)capacity_live=true;
  if(expected_capture&&capture_index==2&&!flush)capacity_queue.push_back({edges+4,uint32_t(p12+align_count(count))});
  need(capacity_queue.size()<=4,"capacity pipeline owner bound");
  d.clk=1;d.eval();p12=next12;p123=next123;check();d.clk=0;d.eval();check();
  trace<<edges<<','<<expected_capture<<','<<capture_index<<','<<count<<','<<a[0]<<','<<a[1]<<','<<a[2]<<','<<p12<<','<<p123<<','<<unsigned(d.meta_valid)<<','<<unsigned(d.debug_state)<<','<<unsigned(d.error)<<','<<d.meta_threshold1<<','<<d.meta_threshold2<<','<<d.meta_threshold3<<','<<unsigned(d.verify_threshold_live)<<','<<flush<<','<<d.verify_capacity_upper<<','<<d.verify_capacity_lower<<','<<unsigned(d.verify_capacity_wrap)<<','<<unsigned(d.verify_capacity_live)<<'\n';++edges;need(edges<1000000,"capture finite watchdog");
 }
 void clean(){d.reset=1;d.start=d.abort_packet=d.in_valid=0;tick(false,-1,0);d.reset=0;}
 void prepare(unsigned index,uint32_t count,unsigned mode){auto&r=*d.rootp;d.clk=0;d.eval();d.packet_bytes=174;d.blocks=1;d.epoch=99;d.start=d.reset=d.abort_packet=0;d.in_valid=0;
  BOTH(state,13U);BOTH(fetch_index,index);BOTH(fetch_count,46U);BOTH(fetch_return,2U);BOTH(fetch_kind,mode==10?1U:0U);BOTH(fetch_base,0U);BOTH(size_bytes,1024U);BOTH(context_epoch,99U);BOTH(context_blocks,1U);BOTH(context_active,0U);BOTH(received,0U);BOTH(done,0U);BOTH(error,0U);BOTH(buffer_bytes,index);BOTH(ram_valid,mode==3?0U:1U);BOTH(ram_epoch,mode==1||mode==3?100U:99U);BOTH(ram_addr,mode==2?index+1:index);BOTH(ram_data,count>>24);
  // Synthetic WAIT fixtures describe a prior request at base0+index. This
  // expected address is independent of deliberately foreign ram_addr/epoch.
  BOTH(expected_fetch_addr,uint32_t(index));
  const unsigned start=index-3;for(unsigned byte=0;byte<3;++byte){BOTH(fetch_bytes[start+byte],(count>>(8*byte))&255U);}BOTH(fetch_bytes[index],((count>>24)^255U)&255U);
  if(mode==4)d.reset=1;
  if(mode==5)d.start=1;
  if(mode==6)d.abort_packet=1;
  if(mode==7)d.reset=d.start=d.abort_packet=1;
  if(mode==8||mode==9){BOTH(context_active,1U);CBOTH(state,mode==8?8U:9U);CBOTH(done,mode==8?1U:0U);CBOTH(error,mode==9?3U:0U);CBOTH(out_valid,0U);}
  d.eval();
 }
 void prepared_case(unsigned index,uint32_t count,unsigned mode){clean();prepare(index,count,mode);need(mode!=1&&mode!=2,"foreign-valid requires negative subprocess");const bool capture=mode==0;const unsigned slot=(index-33)/4;tick(capture,capture?int(slot):-1,count);++prepared;++modes[mode];d.reset=d.start=d.abort_packet=0;
  auto&r=*d.rootp;BOTH(state,0U);BOTH(context_active,0U);BOTH(ram_valid,0U);
  for(unsigned quiet=0;quiet<8;++quiet)tick(false,-1,0);
 }
 static std::vector<uint8_t> packet(){std::vector<uint8_t> p(174);p[0]='B';p[1]='R';p[2]='8';p[3]='8';p[4]=1;p[5]=1;p[6]=1;p[10]=1;p[14]=128;uint32_t crc=0xffffffffU;for(unsigned i=0;i<p.size()-4;++i){crc^=p[i];for(unsigned bit=0;bit<8;++bit)crc=(crc>>1)^((crc&1)?0xedb88320U:0);}crc^=0xffffffffU;for(unsigned i=0;i<4;++i)p[p.size()-4+i]=uint8_t(crc>>(8*i));return p;}
 void normal_tick(){d.clk=0;d.eval();const bool cap=d.stage_read_rsp&&d.stage_purpose==0;int slot=-1;if(cap&&(d.stage_rsp_addr==33||d.stage_rsp_addr==37||d.stage_rsp_addr==41))slot=int((d.stage_rsp_addr-33)/4);tick(cap,slot,0);}
 void start_raw(unsigned epoch){d.reset=d.abort_packet=0;d.start=1;d.epoch=epoch;d.blocks=1;d.packet_bytes=174;d.in_valid=0;tick(false,-1,0);d.start=0;const auto p=packet();for(unsigned i=0;i<p.size();++i){d.in_valid=1;d.in_data=p[i];d.in_last=i+1==p.size();d.eval();need(d.in_ready,"RAW receive no extra cycle");normal_tick();}d.in_valid=0;d.in_last=0;}
 void raw(unsigned epoch,int cancel_at){clean();start_raw(epoch);unsigned fetch_edges=0;bool cancelled=false;for(unsigned wait=0;!d.meta_valid;++wait){need(wait<256,"RAW earliest metadata watchdog");d.eval();if(cancel_at>=0&&d.stage_read_rsp&&d.stage_rsp_addr==unsigned(cancel_at)){d.abort_packet=1;tick(false,-1,0);d.abort_packet=0;cancelled=true;++restarts;break;}normal_tick();++fetch_edges;}
  if(cancelled){need(d.debug_state==0&&!d.meta_valid,"capture-edge abort must suppress metadata");return;}
  need(fetch_edges==93,"RAW earliest metadata schedule changed");need(d.meta_raw&&d.meta_blocks==1&&d.meta_epoch==epoch,"RAW metadata owner");need(d.meta_count1==0&&d.meta_count2==0&&d.meta_count3==0,"RAW metadata count zero");for(unsigned hold=0;hold<17;++hold){d.blocks=rng()&131071U;d.epoch=rng();d.packet_bytes=rng();normal_tick();need(d.meta_valid&&d.meta_raw&&d.meta_blocks==1&&d.meta_epoch==epoch,"held metadata ignores mutable external context");++held;}d.meta_ready=1;normal_tick();d.meta_ready=0;need(d.debug_state==6,"RAW metadata acceptance unchanged");++raw_packets;
 }
 void flush_commit_retry(unsigned index,uint32_t n){
  clean();prepare(index,n,0);const unsigned slot=(index-33)/4;tick(true,int(slot),n);
  auto&r=*d.rootp;BOTH(state,0U);BOTH(context_active,0U);BOTH(ram_valid,0U);
  for(unsigned quiet=0;quiet<7;++quiet)tick(false,-1,0);
  d.abort_packet=1;tick(false,-1,0);d.abort_packet=0;need(threshold_live==0,"abort/commit collision retained live owner");
  raw(9000U+index,-1);++commit_abort_retries;
 }
 void capacity_flush_commit_retry(){
  clean();prepare(41U,0xfffffffdU,0);tick(true,2,0xfffffffdU);
  auto&r=*d.rootp;BOTH(state,0U);BOTH(context_active,0U);BOTH(ram_valid,0U);
  for(unsigned quiet=0;quiet<3;++quiet)tick(false,-1,0);
  d.abort_packet=1;tick(false,-1,0);d.abort_packet=0;need(!capacity_live,"capacity commit/abort owner invalidated");
  raw(19001U,-1);++capacity_abort_retries;
 }
 void high_metadata(const std::array<uint32_t,3>&counts){clean();for(unsigned slot=0;slot<3;++slot){prepare(33+4*slot,counts[slot],0);tick(true,int(slot),counts[slot]);
   auto&r=*d.rootp;BOTH(state,0U);BOTH(context_active,0U);BOTH(ram_valid,0U);
   for(unsigned quiet=0;quiet<2;++quiet)tick(false,-1,0);
  }auto&r=*d.rootp;BOTH(state,9U);BOTH(context_active,0U);for(unsigned i=0;i<3;++i)BOTH(counts[i+1],counts[i]);BOTH(raw_mode,0U);BOTH(ram_valid,0U);d.eval(); // settle pipeline on two existing non-metadata prepared edges first
  BOTH(state,0U);for(unsigned quiet=0;quiet<8;++quiet)tick(false,-1,0);BOTH(state,9U);
  for(unsigned hold=0;hold<17;++hold){d.blocks=rng()&131071U;d.epoch=rng();d.packet_bytes=rng();tick(false,-1,0);need(d.meta_valid&&d.meta_count1==counts[0]&&d.meta_count2==counts[1]&&d.meta_count3==counts[2],"high32 owned metadata unchanged");++held;}
 }
};
int main(int argc,char**argv){try{need(argc>=3,"seed trace [negative-mode index] required");unsigned seed=unsigned(std::stoul(argv[1]));Bench b(seed,argv[2]);if(argc==5){unsigned mode=unsigned(std::stoul(argv[3])),index=unsigned(std::stoul(argv[4]));need(mode==1||mode==2,"negative owner type");b.prepare(index,0xa5b6c7d8U,mode);need(!b.d.verify_capture&&!b.d.mismatch,"foreign response must not enable capture");std::cout<<"{\"type\":\"EXPECTED_ASSERTION_ARMED\",\"capture_enable\":false,\"mode\":"<<mode<<",\"index\":"<<index<<"}"<<std::endl;b.d.clk=1;b.d.eval();throw std::runtime_error("foreign response was not rejected by original assertion");}
 const std::array<uint32_t,14> values={0,1,2,3,0x3fffffffU,0x40000000U,0x7fffffffU,0x80000000U,0xa5b6c7d8U,0xbfffffffU,0xfffffff0U,0xfffffffcU,0xfffffffeU,0xffffffffU};
 for(unsigned index:{33U,37U,41U})for(unsigned mode:{0U,3U,4U,5U,6U,7U,8U,9U,10U})for(unsigned sample=0;sample<64;++sample)b.prepared_case(index,sample<values.size()?values[sample]:b.rng(),mode);
 for(unsigned n=0;n<128;++n)b.high_metadata({uint32_t(b.rng()),uint32_t(b.rng()),uint32_t(b.rng())});
 for(unsigned index:{33U,37U,41U})b.flush_commit_retry(index,0xffffffffU-uint32_t(b.rng()%128));
 b.capacity_flush_commit_retry();
 for(int index:{33,37,41}){b.raw(1000U+unsigned(index),index);b.raw(2000U+unsigned(index),-1);}b.raw(7777,-1);
 need(b.prepared==1728&&b.raw_packets==8&&b.restarts==3&&b.held==2312&&b.commit_abort_retries==3&&b.threshold_flush_commits>=3&&b.capacity_abort_retries==1&&b.capacity_flush_commits>=1,"capture coverage totals");b.d.final();std::cout<<"{\"type\":\"prefix_capture_verdict\",\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"edges\":"<<b.edges<<",\"capacity_commits\":"<<b.capacity_commits<<",\"capacity_flush_commits\":"<<b.capacity_flush_commits<<",\"capacity_abort_retries\":"<<b.capacity_abort_retries<<",\"threshold_commits\":"<<b.threshold_commits<<",\"threshold_flush_commits\":"<<b.threshold_flush_commits<<",\"commit_abort_retries\":"<<b.commit_abort_retries<<",\"positive_prepared_cases\":"<<b.prepared<<",\"high32_metadata_owners\":128,\"actual_raw_packets\":"<<b.raw_packets<<",\"capture_edge_abort_restarts\":"<<b.restarts<<",\"held_metadata_edges\":"<<b.held<<",\"captures\":"<<b.captures<<",\"capture_indices\":["<<b.capture_indices[0]<<','<<b.capture_indices[1]<<','<<b.capture_indices[2]<<"],\"expected_negative_subprocesses_separate\":6}\n";return 0;
}catch(const std::exception&e){std::cerr<<"TEST_FAIL "<<e.what()<<'\n';return 1;}}
