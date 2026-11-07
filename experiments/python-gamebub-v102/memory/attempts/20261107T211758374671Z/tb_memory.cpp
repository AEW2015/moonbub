#include "Vmemory_probe.h"
#include "Vmemory_probe___024root.h"
#include "verilated.h"
#include <array>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <random>
#include <stdexcept>
#include <vector>
#define OLD(n) r.memory_probe__DOT__old_dut__DOT__##n
#define NEW(n) r.memory_probe__DOT__new_dut__DOT__##n
#define BOTH(n,v) do { OLD(n)=(v); NEW(n)=(v); } while(0)
static void need(bool v,const char* why){if(!v)throw std::runtime_error(why);}
int main(int argc,char**argv){
 try {
  need(argc==3,"seed and trace required"); unsigned seed=unsigned(std::stoul(argv[1]));
  std::mt19937 rng(seed); Vmemory_probe d; auto&r=*d.rootp; std::ofstream trace(argv[2]);
  std::vector<uint8_t> mem(49152); for(unsigned i=0;i<mem.size();++i){mem[i]=uint8_t((i*131U)^(i>>5)^seed);OLD(memory)[i]=mem[i];NEW(memory)[i]=mem[i];}
  d.clk=0;d.reset=1;d.start=0;d.abort_packet=0;d.cache_write=0;d.cache_index=0;d.cache_data=0;d.replay_req=0;d.replay_addr=0;d.lookup_req=0;d.lookup_tile=0;d.lookup_cell=0;d.packet_bytes=49152;d.epoch=seed;d.accepted_ref_valid=0;d.accepted_qcache_valid=0;d.accepted_ref_fid=0;d.accepted_ref_generation=0;d.in_valid=0;d.in_last=0;d.in_data=0;d.receipt_ready=0;d.probe_force_collision=0;
  d.eval();d.clk=1;d.eval();d.clk=0;d.eval();d.reset=0;
  BOTH(ram_data,0xA5);BOTH(ram_addr,0x87654321U);BOTH(ram_epoch,0x12345678U);
  uint8_t expected_data=0xA5;uint32_t expected_addr=0x87654321U,expected_epoch=0x12345678U;
  unsigned cases=0,edges=1,reads=0,writes=0,collisions=0,suppressed=0,forced=0;
  auto run=[&](unsigned state,unsigned address,unsigned fetch,unsigned received,unsigned guards,bool input,bool replay,bool collision){
   d.clk=0;d.probe_force_collision=collision;d.reset=(guards&1)!=0;d.start=(guards&2)!=0;d.abort_packet=(guards&4)!=0;
   d.in_valid=input;d.replay_req=replay;d.replay_addr=address;d.in_data=uint8_t(rng());d.in_last=received==49151;d.epoch=rng();
   BOTH(state,uint8_t(state));BOTH(received,received);BOTH(fetch_addr,fetch);BOTH(receipt_epoch,uint32_t(rng()));BOTH(size_bytes,49152U);
   d.eval();need(d.probe_outputs_equal,"pre-edge public mismatch");need(d.probe_ram_equal,"pre-edge RAM metadata mismatch");
   bool wr=d.stage_write;bool rd=d.stage_read_req||(d.replay_req&&d.replay_ready);uint32_t addr=d.stage_read_req?fetch:address;
   uint32_t epoch=OLD(receipt_epoch);unsigned wi=received&65535U,ri=addr&65535U;
   need(!wr||wi<mem.size(),"write address out of contract");need(!rd||ri<mem.size(),"read address out of contract");
   if(rd){expected_data=mem[ri];expected_addr=addr;expected_epoch=epoch;++reads;}
   if(wr){if(rd&&wi==ri)++collisions;mem[wi]=d.in_data;++writes;}
   if(replay&&!d.replay_ready&&!d.stage_read_req)++suppressed;
   if(collision)++forced;
   d.clk=1;d.eval();++edges;need(d.probe_outputs_equal,"post-edge public mismatch");need(d.probe_ram_equal,"post-edge RAM metadata mismatch");
   need(d.replay_data==expected_data&&d.stage_read_data==expected_data,"independent read/hold/read-first byte oracle");
   need(d.replay_rsp_addr==expected_addr&&d.stage_rsp_addr==expected_addr,"independent address priority/hold oracle");
   need(d.replay_rsp_epoch==expected_epoch&&d.stage_rsp_epoch==expected_epoch,"independent epoch/hold oracle");
   need(OLD(memory)[wi]==mem[wi]&&NEW(memory)[wi]==mem[wi],"write oracle");
   trace<<"{\"case\":"<<cases<<",\"state\":"<<state<<",\"guards\":"<<guards<<",\"forced_collision\":"<<(collision?1:0)<<",\"write\":"<<(wr?1:0)<<",\"read\":"<<(rd?1:0)<<",\"write_addr\":"<<wi<<",\"write_data\":"<<unsigned(d.in_data)<<",\"read_addr\":"<<addr<<",\"prepared_epoch\":"<<epoch<<",\"data\":"<<unsigned(d.replay_data)<<",\"latched_addr\":"<<d.replay_rsp_addr<<",\"latched_epoch\":"<<d.replay_rsp_epoch<<",\"equal\":true}\n";
   ++cases;d.clk=0;d.eval();
  };
  std::array<unsigned,8> a={0,1,15,16,255,256,49150,49151};
  for(unsigned state: {0U,1U,26U,27U,28U})for(unsigned guard=0;guard<8;++guard)for(unsigned x:a)for(unsigned flags=0;flags<4;++flags)
   run(state,x,x^1U,x,guard,(flags&1)!=0,(flags&2)!=0,false);
  // Illegal replay requests must be rejected without disturbing the held RAM response.
  for(unsigned x:{49152U,65535U,65536U,0xffffffffU})for(unsigned guard=0;guard<8;++guard)run(26,x,0,0,guard,false,true,false);
  // Verification-only forced enables make same-edge read/write reachable to test the RAM primitive contract.
  for(unsigned x:a)for(unsigned i=0;i<4;++i)run(0,x,x,x,0,true,true,true);
  for(unsigned i=0;i<8192;++i){unsigned x=rng()%49152U;unsigned states[5]={0,1,26,27,28};run(states[rng()%5],x,rng()%49152U,rng()%49152U,rng()%8U,(rng()&1)!=0,(rng()&1)!=0,false);}
  need(cases==9536,"case completeness");need(collisions==32&&forced==32,"directed real same-edge collisions");
  for(unsigned i=0;i<mem.size();++i)need(OLD(memory)[i]==mem[i]&&NEW(memory)[i]==mem[i],"final complete memory equality");
  std::cout<<"{\"type\":\"verdict\",\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"cases\":"<<cases<<",\"clock_edges\":"<<edges<<",\"reads\":"<<reads<<",\"writes\":"<<writes<<",\"same_address_read_first_collisions\":"<<collisions<<",\"verification_forced_collision_cases\":"<<forced<<",\"suppressed_replay_cases\":"<<suppressed<<",\"final_memory_bytes\":"<<mem.size()<<"}\n";
  d.final();return 0;
 }catch(const std::exception&e){std::cerr<<"TEST_FAIL "<<e.what()<<'\n';return 1;}
}
