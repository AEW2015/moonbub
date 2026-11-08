#include "Vcapacity_math_probe.h"
#include "verilated.h"
#include <array>
#include <cstdint>
#include <deque>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>
static void need(bool v,const std::string&s){if(!v)throw std::runtime_error(s);}
static uint32_t aligned(uint32_t n){return uint32_t((n<<2)+15U)&0xfffffff0U;}
static std::array<uint32_t,3> bounds(uint32_t p){const uint32_t a=((p>>4)+2U)&0x0fffffffU;return {((16384U-a)&0x0fffffffU)<<3,((~a)&0x0fffffffU)<<3,uint32_t(a>16384U)};}
struct Owner{uint64_t due;uint32_t prefix;};
struct Bench{
 Vcapacity_math_probe d;std::deque<Owner> pending;
 std::array<uint32_t,3> cache{};uint32_t owner=0;bool live=false,known=false;
 uint64_t edges=0,commits=0,collisions=0,predicates=0,accepted=0;
 void check(){
  need(d.meta_capacity_upper==cache[0]&&d.meta_capacity_lower==cache[1]&&unsigned(d.meta_capacity_wrap)==cache[2],"exact extracted pipeline cached tuple/hold");
  need(bool(d.live)==live,"four-edge owner validity/flush");
  need(d.plan_prefix12==uint32_t(d.prefix12_units<<4),"complete aligned prefix passthrough");
  if(known){
   const uint32_t literal_plan=d.raw?uint32_t(32U+128U*d.blocks):uint32_t(32U+((2U*d.blocks+15U)&0xfffffff0U)+owner);
   need(bool(d.bad)==(literal_plan>262144U),"literal original wrapped32-bit plan capacity against live u17 blocks");++predicates;
  }
 }
 void tick(uint32_t p12_units,uint32_t c3,bool take,bool flush,unsigned blocks,bool raw){
  d.clk=0;d.reset=flush;d.take=take;d.prefix12_units=p12_units&0x0fffffffU;d.count3=c3;d.blocks=blocks;d.raw=raw;d.eval();check();
  const bool commit=!pending.empty()&&pending.front().due==edges;
  if(commit){owner=pending.front().prefix;pending.pop_front();cache=bounds(owner);known=true;++commits;if(flush)++collisions;}
  if(flush){pending.clear();live=false;}else if(commit)live=true;
  if(take&&!flush){pending.push_back({edges+4,uint32_t((p12_units<<4)+aligned(c3))});++accepted;}
  need(pending.size()<=4,"bounded pipeline owner storage");
  d.clk=1;d.eval();d.clk=0;d.eval();check();++edges;need(edges<4000000,"finite clock watchdog");
 }
 void settle(uint32_t p){tick(p>>4,0,true,false,0,false);for(unsigned q=0;q<4;++q)tick(0,0,false,false,0,false);need(owner==p&&live,"settled model owner");}
};
int main(int argc,char**argv){try{
 need(argc==2,"seed required");const unsigned seed=unsigned(std::stoul(argv[1]));std::mt19937 rng(seed);Bench b;b.tick(0,0,false,true,0,false);
 uint64_t grid=0,raw=0,random=0;
 for(uint32_t p:{0U,16U,32U,64U,262080U,262096U,262112U,262128U,262144U,262160U,0x7ffffff0U,0x80000000U,0xffffffa0U,0xffffffc0U,0xffffffe0U,0xfffffff0U}){
  b.settle(p);for(unsigned n=0;n<131072;++n){b.tick(rng(),rng(),false,false,n,false);++grid;}
 }
 b.settle(0);for(unsigned n=0;n<131072;++n){b.tick(rng(),rng(),false,false,n,true);++raw;}
 for(unsigned n=0;n<300000;++n){b.tick(rng(),rng(),true,false,rng()&131071U,rng()&1U);++random;}
 for(unsigned n=0;n<30000;++n)b.tick(rng(),rng(),rng()%4!=0,rng()%97==0,rng()&131071U,rng()&1U);
 for(unsigned n=0;n<4;++n){b.tick(0,0,false,true,0,false);b.tick(rng(),rng(),true,false,0,false);for(unsigned q=0;q<3;++q)b.tick(rng(),rng(),false,false,0,false);b.tick(rng(),rng(),true,true,131071,true);}
 for(unsigned q=0;q<5;++q)b.tick(rng(),rng(),false,false,rng()&131071U,false);
 need(b.pending.empty()&&grid==2097152&&raw==131072&&random==300000&&b.collisions>=4,"finite full-domain and collision coverage");
 std::cout<<"{\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"clock_edges\":"<<b.edges<<",\"full_u17_block_grid_cases\":"<<grid<<",\"raw_full_u17_cases\":"<<raw<<",\"random_u32_cases\":"<<random<<",\"accepted\":"<<b.accepted<<",\"commits\":"<<b.commits<<",\"flush_commit_collisions\":"<<b.collisions<<",\"literal_predicate_checks\":"<<b.predicates<<",\"post_capture_edges\":4}\n";return 0;
 }catch(const std::exception&e){std::cerr<<"TEST_FAIL "<<e.what()<<'\n';return 1;}}
