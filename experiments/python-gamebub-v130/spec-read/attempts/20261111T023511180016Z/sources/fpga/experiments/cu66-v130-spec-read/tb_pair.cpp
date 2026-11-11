#include "Vadmission_pair.h"
#include "verilated.h"
#include <cstdint>
#include <fstream>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>
static void need(bool b,const char* why){if(!b)throw std::runtime_error(why);}
static std::vector<uint8_t> packet(const char* path){
 std::ifstream in(path);std::string id,hex;unsigned err=1;need(bool(in),"fixture file");
 while(in>>id>>err>>hex){std::string rest;std::getline(in,rest);if(err)continue;
  std::vector<uint8_t> out;for(size_t i=0;i<hex.size();i+=2)out.push_back(uint8_t(std::stoul(hex.substr(i,2),nullptr,16)));return out;}
 throw std::runtime_error("no positive packet");
}
int main(int argc,char**argv){
 try{
  need(argc==3,"usage: fixture seed");auto bytes=packet(argv[1]);unsigned seed=unsigned(std::stoul(argv[2]));std::mt19937 rng(seed);
  Vadmission_pair d;uint64_t edges=0,checks=0,accepted=0,clamp_cases=0,stage_cancel_cases=0,replay_cancel_cases=0,packet_runs=0;
  auto eval=[&](){d.eval();++checks;need(!d.mismatch,"public output mismatch");};
  auto tick=[&](){d.clk=0;eval();d.clk=1;eval();++edges;d.clk=0;eval();};
  d.clk=0;d.reset=0;d.start=0;d.abort_packet=0;d.cache_write=0;d.cache_index=0;d.cache_data=0;d.lookup_req=0;d.lookup_tile=0;d.lookup_cell=0;
  d.replay_req=0;d.replay_addr=0;d.packet_bytes=uint32_t(bytes.size());d.epoch=0x1527812;d.accepted_ref_valid=0;d.accepted_qcache_valid=0;d.accepted_ref_fid=0;d.accepted_ref_generation=0;d.in_valid=0;d.in_last=0;d.in_data=0;d.receipt_ready=0;
  auto start_packet=[&](){
   d.in_valid=0;d.in_last=0;d.receipt_ready=0;d.replay_req=0;d.abort_packet=0;d.start=0;d.reset=1;tick();d.reset=0;++d.epoch;d.start=1;tick();d.start=0;
   for(unsigned i=0;i<9000&&!d.in_ready;++i){tick();}need(d.in_ready,"RX start timeout");
   for(size_t i=0;i<bytes.size();++i){
    d.in_valid=1;d.in_data=bytes[i];d.in_last=(i+1==bytes.size());
    if((i%13)==0){d.in_valid=0;tick();d.in_valid=1;}
    d.replay_req=(i%7)==0;d.replay_addr=(i%4)==0?0xffffffffU:uint32_t(rng());tick();
   }
   d.in_valid=0;d.in_last=0;d.receipt_ready=0;++packet_runs;
  };
  auto until_state=[&](unsigned state){
   for(unsigned i=0;i<1000000&&d.debug_state!=state&&!d.error;++i){
    d.replay_req=(i%11)==0;d.replay_addr=(i%5)==0?49152U:uint32_t(rng());tick();
   }
   need(!d.error,"positive vector admission rejected");need(d.debug_state==state,"state timeout");
  };
  auto finish_packet=[&](){until_state(25);need(d.receipt_valid,"receipt expected");
   for(int i=0;i<3;++i){tick();}d.receipt_ready=1;tick();d.receipt_ready=0;need(d.debug_state==26,"FINISHED expected");};
  auto cancel=[&](unsigned kind){d.reset=(kind==0);d.start=(kind==1);d.abort_packet=(kind==2);tick();
   need(!d.replay_rsp_valid,"cancelled replay generated response");need(!d.stage_read_rsp,"cancelled stage generated response");
   d.reset=d.start=d.abort_packet=0;tick();};
  // Cancel each real stage read both before acceptance and while its response is pending.
  for(unsigned state:{28U,29U})for(unsigned kind=0;kind<3;++kind){
   start_packet();until_state(state);need(state==28?d.stage_read_req:d.stage_read_rsp,"stage request/response expected");
   cancel(kind);++stage_cancel_cases;
  }
  start_packet();finish_packet();
  const uint32_t boundary[]={0,1,uint32_t(bytes.size()-1),uint32_t(bytes.size()),49151,49152,65535,65536,0xffffffffU};
  for(unsigned i=0;i<12000;++i){
   uint32_t a=(i%3==0)?boundary[(i/3)%9]:((i%3==1)?uint32_t(rng()%bytes.size()):uint32_t(rng()));
   d.replay_addr=a;d.replay_req=(i%4)!=0;d.clk=0;eval();
   const bool take=d.replay_req&&d.replay_ready;d.clk=1;eval();++edges;
   need(bool(d.replay_rsp_valid)==take,"replay response valid");
   if(take){++accepted;need(a<bytes.size(),"out of range accepted");need(d.replay_rsp_addr==a&&d.replay_rsp_epoch==d.epoch&&d.replay_data==bytes[a],"response data/address/epoch");}
   if(a>=49152){++clamp_cases;}
   d.clk=0;eval();
  }
  // Check every 16-bit replay address, including 49151/49152, while speculative reads are unowned.
  d.replay_req=0;for(uint32_t a=0;a<65536;++a){d.replay_addr=a;tick();}clamp_cases+=65536;
  for(uint32_t a:{65536U,0x80000000U,0xffffffffU}){d.replay_addr=a;tick();++clamp_cases;}
  // Cancel at the offered read edge and on the following valid-response edge.
  for(unsigned pending=0;pending<2;++pending)for(unsigned kind=0;kind<3;++kind){
   if(pending||kind){start_packet();finish_packet();}
   d.replay_req=1;d.replay_addr=0;d.clk=0;eval();need(d.replay_ready,"ready required");
   if(pending){tick();need(d.replay_rsp_valid,"pending replay response expected");}
   cancel(kind);++replay_cancel_cases;
  }
  // Following every cancellation, the next complete transaction must recover.
  start_packet();finish_packet();d.replay_req=1;d.replay_addr=0;tick();
  need(d.replay_rsp_valid&&d.replay_data==bytes[0]&&d.replay_rsp_epoch==d.epoch,"clean retry data/epoch");
  need(accepted>1000&&stage_cancel_cases==6&&replay_cancel_cases==6&&clamp_cases>65536,"insufficient coverage");
  std::cout<<"{\"status\":\"PASS\",\"seed\":"<<seed<<",\"edges\":"<<edges<<",\"checks\":"<<checks<<",\"valid_replay\":"<<accepted<<",\"invalid_and_exhaustive_spec_addresses\":"<<clamp_cases<<",\"stage_cancel_cases\":"<<stage_cancel_cases<<",\"replay_cancel_cases\":"<<replay_cancel_cases<<",\"packet_runs\":"<<packet_runs<<",\"packet_bytes\":"<<bytes.size()<<",\"actual_full_admission_fsm\":true,\"all_nondatabus_outputs_compared\":true,\"invalid_databus_qualified\":true}"<<std::endl;
  return 0;
 }catch(const std::exception&e){std::cerr<<"PAIR_FAIL "<<e.what()<<std::endl;return 1;}
}
