#include "Vprefix_math_probe.h"
#include "verilated.h"
#include <array>
#include <cstdint>
#include <iostream>
#include <random>
#include <stdexcept>
static void need(bool yes,const char*why){if(!yes)throw std::runtime_error(why);}
int main(){try{
 Vprefix_math_probe d;std::mt19937 rng(108043);uint64_t rows=0,edges=0,holds=0;
 auto tick=[&](){d.clk=0;d.eval();d.clk=1;d.eval();d.clk=0;d.eval();++edges;};
 auto aligned=[](uint32_t count){return uint32_t(count*4U+15U)&0xfffffff0U;};
 const std::array<uint32_t,20> points={0,1,2,3,4,7,8,15,16,17,0x1ffffU,0x3ffffffcU,0x3fffffffU,0x40000000U,0x7fffffffU,0x80000000U,0xbfffffffU,0xfffffff0U,0xfffffffcU,0xffffffffU};
 for(unsigned n=0;n<108000;++n){
  std::array<uint32_t,3> c{};if(n<8000){c={points[n/400],points[(n/20)%20],points[n%20]};}else for(auto&v:c)v=rng();
  d.begin_count1=c[0];d.begin_count2=c[1];d.begin_count3=c[2];d.begin_blocks=rng()&131071U;
  // Poison cached high bytes. Correct capture must forward current ram_data.
  for(unsigned i=0;i<3;++i)d.prior_header[i]=(c[i]&0x00ffffffU)|((rng()&255U)<<24);
  for(unsigned i=0;i<3;++i){d.prefix_header_capture=0;tick();d.prefix_header_capture=1;d.fetch_index=33+4*i;d.ram_data=c[i]>>24;tick();}
  d.prefix_header_capture=0;tick();tick();
  const uint32_t a=aligned(c[0]),b=aligned(c[1]),z=aligned(c[2]);
  auto check=[&](){
   need(d.meta_prefix1==a&&d.meta_prefix12==uint32_t(a+b)&&d.meta_prefix123==uint32_t(a+b+z),"forwarded full32 prefix");
   const uint32_t base=32U+((uint32_t(d.begin_blocks)*2U+15U)&0xfffffff0U);
   need(d.old_plan2==uint32_t(base+a)&&d.old_plan3==uint32_t(base+a+b)&&d.old_used==uint32_t(base+a+b+z),"independent old full32 sums");
   need(d.old_plan2==d.new_plan2&&d.old_plan3==d.new_plan3&&d.old_used==d.new_used,"exact old/new full32 plan");
  };
  check();
  for(unsigned hold=0;hold<4;++hold){d.begin_blocks=rng()&131071U;d.ram_data=rng()&255U;d.fetch_index=33+4*(rng()%3);d.prefix_header_capture=0;tick();check();++holds;}
  ++rows;
 }
 need(rows==108000,"finite proof rows");std::cout<<"{\"type\":\"prefix_math_verdict\",\"status\":\"TEST_PASS\",\"rows\":"<<rows<<",\"edges\":"<<edges<<",\"held_edges\":"<<holds<<",\"seed\":108043}\n";d.final();return 0;
}catch(const std::exception&e){std::cerr<<"TEST_FAIL "<<e.what()<<'\n';return 1;}}
