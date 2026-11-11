#include "Vadmission_pair.h"
#include "verilated.h"
#include <cstdint>
#include <fstream>
#include <iostream>
#include <random>
#include <sstream>
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
  Vadmission_pair d;uint64_t edges=0, checks=0,accepted=0,valid_checks=0,clamp_cases=0;
  auto eval=[&](){d.eval();++checks;need(!d.mismatch,"public output mismatch");};
  auto tick=[&](){d.clk=0;eval();d.clk=1;eval();++edges;d.clk=0;eval();};
  d.clk=0;d.reset=1;d.start=0;d.abort_packet=0;d.cache_write=0;d.cache_index=0;d.cache_data=0;d.lookup_req=0;d.lookup_tile=0;d.lookup_cell=0;
  d.replay_req=0;d.replay_addr=0;d.packet_bytes=uint32_t(bytes.size());d.epoch=0x1527812;d.accepted_ref_valid=0;d.accepted_qcache_valid=0;d.accepted_ref_fid=0;d.accepted_ref_generation=0;d.in_valid=0;d.in_last=0;d.in_data=0;d.receipt_ready=0;tick();d.reset=0;d.start=1;tick();d.start=0;
  for(unsigned i=0;i<9000&&!d.in_ready;++i){tick();}
  need(d.in_ready,"RX start timeout");
  for(size_t i=0;i<bytes.size();++i){
   d.in_valid=1;d.in_data=bytes[i];d.in_last=(i+1==bytes.size());
   if((i%13)==0){d.in_valid=0;tick();d.in_valid=1;}
   d.replay_req=(i%7)==0;d.replay_addr=(i%4)==0?0xffffffffU:uint32_t(rng());tick();
  }
  d.in_valid=0;d.in_last=0;d.receipt_ready=0;
  for(unsigned i=0;i<1000000&&!d.receipt_valid&&!d.error;++i){
   d.replay_req=(i%11)==0;d.replay_addr=(i%5)==0?49152U:uint32_t(rng());tick();
  }
  need(!d.error,"positive vector admission rejected");need(d.receipt_valid,"receipt timeout");
  for(int i=0;i<3;++i){tick();}
  d.receipt_ready=1;tick();d.receipt_ready=0;
  need(d.debug_state==26,"FINISHED expected");
  const uint32_t boundary[]={0,1,uint32_t(bytes.size()-1),uint32_t(bytes.size()),49151,49152,65535,65536,0xffffffffU};
  for(unsigned i=0;i<12000;++i){
   uint32_t a=(i%3==0)?boundary[(i/3)%9]:((i%3==1)?uint32_t(rng()%bytes.size()):uint32_t(rng()));
   d.replay_addr=a;d.replay_req=(i%4)!=0;d.clk=0;eval();
   const bool take=d.replay_req&&d.replay_ready;d.clk=1;eval();++edges;
   need(bool(d.replay_rsp_valid)==take,"replay response valid");
   if(take){++accepted;need(a<bytes.size(),"out of range accepted");need(d.replay_rsp_addr==a&&d.replay_rsp_epoch==d.epoch&&d.replay_data==bytes[a],"response data/address/epoch");++valid_checks;}
   if(a>=49152)++clamp_cases;
   d.clk=0;eval();
  }
  // Existing cancellation priority: a simultaneous replay request may not respond.
  for(unsigned kind=0;kind<3;++kind){
   d.replay_req=1;d.replay_addr=0;d.reset=(kind==0);d.start=(kind==1);d.abort_packet=(kind==2);tick();
   need(!d.replay_rsp_valid,"cancelled replay generated response");d.reset=d.start=d.abort_packet=0;tick();
  }
  need(accepted>1000&&valid_checks==accepted&&clamp_cases>1000,"insufficient coverage");
  std::cout<<"{\"status\":\"PASS\",\"seed\":"<<seed<<",\"edges\":"<<edges<<",\"checks\":"<<checks<<",\"valid_replay\":"<<accepted<<",\"invalid_speculative_addresses\":"<<clamp_cases<<",\"packet_bytes\":"<<bytes.size()<<",\"actual_full_admission_fsm\":true,\"all_nondatabus_outputs_compared\":true,\"invalid_databus_qualified\":true}"<<std::endl;
  return 0;
 }catch(const std::exception&e){std::cerr<<"PAIR_FAIL "<<e.what()<<std::endl;return 1;}
}
