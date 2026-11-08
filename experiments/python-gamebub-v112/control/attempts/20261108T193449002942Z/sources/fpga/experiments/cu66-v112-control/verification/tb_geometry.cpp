#include "Vgeometry_probe.h"
#include "verilated.h"
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <random>
#include <stdexcept>
static bool hidden(unsigned p,uint32_t t){
 if(p)return t>=1046&&t<=1064;
 static constexpr uint32_t intervals[][2]={{633,651},{723,741},{993,1011},{1083,1101},{4071,4110},{4161,4200},{4251,4290},{4431,4460},{4521,4550}};
 for(const auto &r:intervals)if(t>=r[0]&&t<=r[1])return true;
 return false;
}
int main(int argc,char **argv){
 Verilated::commandArgs(argc,argv);uint32_t seed=argc>1?uint32_t(std::stoul(argv[1])):112301U;
 std::mt19937 random(seed);Vgeometry_probe d;uint64_t checks=0;
 auto one=[&](unsigned p,uint32_t t){
  d.geometry_plane=p;d.geometry_tile=t;d.eval();uint32_t sum=0,mask=0;
  for(unsigned k=0;k<16;++k){const uint32_t x=t+uint32_t(k);bool visible=x<(p?1350U:5400U)&&!hidden(p,x);sum+=visible;mask|=uint32_t(visible)<<k;}
  if(d.mask!=mask||d.count!=sum||d.original_count!=sum)throw std::runtime_error("generic uint32 geometry mismatch p="+std::to_string(p)+" t="+std::to_string(t));
  ++checks;
 };
 try{
  // Every possible 16-bit intermediate. This discharges the count identity
  // independently of geometry and every arbitrary mask, including all sixteen.
  for(uint32_t mask=0;mask<65536;++mask){d.raw_mask=mask;d.eval();unsigned count=0;for(unsigned i=0;i<16;++i)count+=(mask>>i)&1U;if(d.raw_count!=count)throw std::runtime_error("balanced population mismatch");}
  // Full small domain and exact 32-bit wrapping tail for all four plane values.
  // Remaining middle domain [65536,UINT32_MAX-15] cannot intersect a visible
  // tile: t+k neither wraps nor is below either tile-count bound.
  for(unsigned p=0;p<4;++p){for(uint32_t t=0;t<65536;++t)one(p,t);for(uint32_t tail=0;tail<16;++tail)one(p,UINT32_MAX-tail);}
  const auto generic=checks;
  for(unsigned i=0;i<100000;++i)one(random()%4,random());
  std::cout<<"{\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"all_mask_counts\":65536,\"generic_tiles\":"<<generic<<",\"random_tiles\":100000,\"plane_mask\":15,\"uint32_wrap_tested\":true,\"middle_domain_proof\":\"no wrap and every t+k >=65536 > both tile counts\"}\n";
 }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
 return 0;
}
