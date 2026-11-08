#include "Vthreshold_math_probe.h"
#include "verilated.h"
#include <array>
#include <cstdint>
#include <deque>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>
static void need(bool v,const std::string&s){if(!v)throw std::runtime_error(s);}
static constexpr std::array<unsigned,3> divisors={5,15,43};
static uint32_t ceil_count(uint32_t n,unsigned d){return n/d+uint32_t(n%d!=0);}
struct Owner {uint64_t due;uint32_t n,b;};
struct Bench {
 Vthreshold_math_probe d;std::array<std::deque<Owner>,3> pending;
 std::array<uint32_t,3> cache{},owner{};unsigned live=0;
 uint64_t edges=0,commits=0,flush_collisions=0,guard_checks=0,accepted=0;
 void check(unsigned b,unsigned selected){
  const std::array<uint32_t,3> out={d.meta_threshold1,d.meta_threshold2,d.meta_threshold3};
  need(out==cache,"actual reciprocal partial-product/register pipeline output");
  need(d.live==live,"actual eight-edge ownership validity");
  for(unsigned g=0;g<3;++g){need(bool((d.bad>>g)&1U)==(uint64_t(owner[g])>uint64_t(b)*divisors[g]),"live full17-bit block threshold predicate");++guard_checks;}
  if(selected<3)need(bool(d.selected_bad)==bool((d.bad>>selected)&1U),"actual descriptor count predicate selection");
 }
 void tick(uint32_t n,unsigned g,bool take,bool flush,unsigned target_b){
  unsigned b=target_b;
  for(const auto&q:pending)if(!q.empty()&&q.front().due==edges)b=q.front().b;
  d.clk=0;d.reset=flush;d.take=take;d.selected=g;d.numerator=n;d.blocks=b;d.eval();check(b,g);
  for(unsigned k=0;k<3;++k){
   const bool commit=!pending[k].empty()&&pending[k].front().due==edges;
   if(commit){owner[k]=pending[k].front().n;cache[k]=ceil_count(owner[k],divisors[k]);pending[k].pop_front();++commits;if(flush)++flush_collisions;}
   if(flush){pending[k].clear();live&=~(1U<<k);}else if(commit)live|=1U<<k;
   if(take&&!flush&&k==g){pending[k].push_back({edges+8,n,target_b});++accepted;}
   need(pending[k].size()<=8,"bounded streaming owner storage");
  }
  d.clk=1;d.eval();d.clk=0;d.eval();check(b,g);++edges;need(edges<5000000,"finite actual arithmetic clock watchdog");
 }
};
int main(int argc,char**argv){try{
 need(argc==2,"seed required");unsigned seed=unsigned(std::stoul(argv[1]));std::mt19937 rng(seed);Bench b;b.tick(0,0,false,true,0);uint64_t boundary=0,random=0,extremes=0;
 for(unsigned g=0;g<3;++g){const unsigned d=divisors[g];
  for(unsigned blocks=0;blocks<131072;++blocks){uint32_t product=blocks*d;for(uint32_t n:{product?product-1:0U,product,product+1,0U,0xffffffffU}){b.tick(n,g,true,false,blocks);++boundary;}}
  for(uint32_t n:{0U,1U,d-1,d,d+1,65535U,65536U,65537U,0x7fffffffU,0x80000000U,0x80000001U,0xfffffffeU,0xffffffffU}){b.tick(n,g,true,false,rng()&131071U);++extremes;}
  for(unsigned n=0;n<100000;++n){b.tick(rng(),g,true,false,rng()&131071U);++random;}
 }
 for(unsigned n=0;n<30000;++n)b.tick(rng(),rng()%3,rng()%4!=0,rng()%97==0,rng()&131071U);
 for(unsigned g=0;g<3;++g){b.tick(0xffffffffU-g,g,true,true,0);b.tick(0xfffffffdU-g,g,true,false,8192);for(unsigned quiet=0;quiet<7;++quiet)b.tick(rng(),g,false,false,rng()&131071U);b.tick(rng(),g,false,true,131071);}
 for(unsigned quiet=0;quiet<9;++quiet)b.tick(rng(),0,false,false,rng()&131071U);
 for(const auto&q:b.pending){need(q.empty(),"pending threshold failed to drain");}need(boundary==1966080&&random==300000&&b.flush_collisions>=3,"actual full-domain/flush coverage");
 std::cout<<"{\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"clock_edges\":"<<b.edges<<",\"full_u17_boundary_cases\":"<<boundary<<",\"random_u32_cases\":"<<random<<",\"extreme_cases\":"<<extremes<<",\"accepted\":"<<b.accepted<<",\"commits\":"<<b.commits<<",\"flush_commit_collisions\":"<<b.flush_collisions<<",\"live_block_guard_checks\":"<<b.guard_checks<<",\"post_capture_edges\":8}\n";return 0;
}catch(const std::exception&e){std::cerr<<"TEST_FAIL "<<e.what()<<'\n';return 1;}}
