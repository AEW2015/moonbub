#include "Vpacked_scratch_v91g2.h"
#include "verilated.h"
#include <array>
#include <cstdint>
#include <iostream>
#include <random>
#include <stdexcept>
static void need(bool v,const char*m){if(!v)throw std::runtime_error(m);}
struct Case{uint32_t blocks;bool raw;uint32_t c1,c2,c3;unsigned error;};
struct Bench{
 Vpacked_scratch_v91g2 d;std::mt19937 rng;unsigned captures=0,poisons=0,ticks=0;
 explicit Bench(unsigned seed):rng(seed){d.clk=0;d.reset=1;d.begin_valid=0;d.begin_blocks=1;d.begin_raw=0;d.begin_serial_clear=0;d.begin_overlap=1;d.begin_prefetch=1;d.begin_tile_overlap=0;d.begin_count1=d.begin_count2=d.begin_count3=d.begin_epoch=0;d.begin_prefix1=d.begin_prefix12=d.begin_prefix123=0;d.begin_threshold1=d.begin_threshold2=d.begin_threshold3=0;d.begin_capacity_upper=d.begin_capacity_lower=0;d.begin_capacity_wrap=0;d.coef_valid=0;d.coef_band=0;d.coef_block=0;d.coef_index=0;d.coef_value=0;d.coef_epoch=0;d.band_end_valid=0;d.band_end_band=0;d.band_end_epoch=0;d.seal_valid=0;d.seal_epoch=0;d.abort_valid=0;d.abort_epoch=0;d.dense_ready=1;d.mem_req_ready=1;d.mem_rsp_valid=0;d.mem_rsp_epoch=0;d.mem_rsp_error=0;for(unsigned j=0;j<4;++j)d.mem_rsp_data[j]=0;tick();d.reset=0;}
 void tick(){need(++ticks<1000,"metadata test watchdog");d.clk=0;d.eval();need(!d.mem_req_valid&&!d.debug_outstanding&&!d.dense_valid,"metadata-only test issued physical/data work");d.clk=1;d.eval();d.clk=0;d.eval();need(!d.mem_req_valid&&!d.debug_outstanding&&!d.dense_valid,"metadata-only test gained physical/data work");}
 void parent_abort(){d.abort_epoch=d.active_epoch;d.abort_valid=1;tick();d.abort_valid=0;d.eval();need(d.begin_ready&&!d.busy&&!d.error,"actual parent tag failed to release descriptor");}
 void prepare(const Case&c,uint32_t tag,unsigned expected){
  auto align=[](uint32_t n){return (n+15U)&~15U;};auto ceildiv=[](uint32_t n,uint32_t k){return n/k+uint32_t(n%k!=0);};
  d.begin_blocks=c.blocks;d.begin_raw=c.raw;d.begin_count1=c.c1;d.begin_count2=c.c2;d.begin_count3=c.c3;d.begin_epoch=tag;
  d.begin_prefix1=align(c.c1*4U);d.begin_prefix12=d.begin_prefix1+align(c.c2*4U);d.begin_prefix123=d.begin_prefix12+align(c.c3*4U);
  d.begin_threshold1=ceildiv(c.c1,5);d.begin_threshold2=ceildiv(c.c2,15);d.begin_threshold3=ceildiv(c.c3,43);
  const uint32_t a=((d.begin_prefix123>>4)+2U)&0x0fffffffU;
  d.begin_capacity_upper=((16384U-a)&0x0fffffffU)<<3;d.begin_capacity_lower=((~a)&0x0fffffffU)<<3;d.begin_capacity_wrap=a>16384U;
  const uint32_t wanted=c.raw?32U+c.blocks*128U:32U+align(c.blocks*2U)+d.begin_prefix123;
  const auto prior_used=d.used_bytes;d.begin_valid=1;d.eval();need(d.begin_ready,"metadata slot not ready");tick();++captures;d.begin_valid=0;
  need(d.active_epoch==tag&&d.busy&&!d.error&&!d.coef_ready,"reservation did not capture actual parent tag");
  d.begin_blocks=rng()&0x1ffffU;d.begin_raw^=1;d.begin_epoch=rng();d.begin_count1=rng();d.begin_count2=rng();d.begin_count3=rng();d.begin_prefix1=rng();d.begin_prefix12=rng();d.begin_prefix123=rng();d.begin_threshold1=rng();d.begin_threshold2=rng();d.begin_threshold3=rng();d.begin_capacity_upper=rng();d.begin_capacity_lower=rng();d.begin_capacity_wrap^=1;++poisons;
  for(unsigned edge=0;edge<3;++edge){tick();need(d.active_epoch==tag,"live metadata poisoned owner tag");if(edge<2)need(d.busy&&!d.error&&!d.coef_ready&&!d.begin_ready,"descriptor committed before third edge");}
  need(d.error==expected,"metadata error/first-cause mismatch");
  if(expected)need(!d.busy&&!d.coef_ready&&d.used_bytes==prior_used,"rejected descriptor changed allocation or eligibility");
  else need(d.busy&&d.coef_ready&&d.used_bytes==wanted,"valid descriptor geometry changed");
 }
};
int main(int argc,char**argv){try{need(argc==2,"metadata usage seed");unsigned seed=std::stoul(argv[1]);unsigned invalid=0,valid=0,priority=0;uint64_t captures=0,poisoned=0;
 const std::array<Case,12> bad{{{0,false,0,0,0,1},{8193,false,0,0,0,1},{131071,false,0,0,0,1},{2048,true,0,0,0,1},{1,true,1,0,0,1},{1,true,0,1,0,1},{1,true,0,0,1,1},{1,false,6,0,0,1},{1,false,0,16,0,1},{1,false,0,0,44,1},{8192,false,0,0,65536,1},{8192,false,0xffffffffU,0,0,1}}};
 for(const auto&c:bad){Bench b(seed+invalid);b.prepare(c,7,c.error);b.parent_abort();b.prepare({1,false,0,0,0,0},7,0);b.parent_abort();captures+=b.captures;poisoned+=b.poisons;++invalid;}
 for(const auto&c:std::array<Case,3>{{{1,false,0,0,0,0},{8192,false,0,0,0,0},{2047,true,0,0,0,0}}}){Bench b(seed+valid+500);b.prepare(c,9,0);b.parent_abort();captures+=b.captures;poisoned+=b.poisons;++valid;}
 {Bench b(seed+900);b.prepare({1,false,0,0,0,0},9,0);b.parent_abort();for(unsigned tag:{9U,8U})for(unsigned blocks:{1U,0U}){b.prepare({blocks,false,0,0,0,0},tag,2);b.parent_abort();++priority;}b.prepare({0,false,0,0,0,1},10,1);b.parent_abort();b.prepare({1,false,0,0,0,0},10,0);b.parent_abort();captures+=b.captures;poisoned+=b.poisons;}
 need(invalid==12&&valid==3&&priority==4&&captures==poisoned,"metadata coverage/conservation");
 std::cout<<"{\"type\":\"metadata_verdict\",\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"invalid_geometry_cases\":"<<invalid<<",\"valid_boundaries\":"<<valid<<",\"replay_priority_cases\":"<<priority<<",\"accepted_poisoned_descriptors\":"<<captures<<",\"physical_requests\":0}\n";return 0;
}catch(const std::exception&e){std::cerr<<"METADATA_FAIL "<<e.what()<<'\n';return 1;}}
