#define main inherited_ready_main
#include "tb_ready.cpp"
#undef main
#include "Vready_probe_cs88_admission_v91i2a.h"
#define OLD(n) d.rootp->ready_probe__DOT__old_dut__DOT__##n
#define NEW(n) d.rootp->ready_probe__DOT__new_dut__DOT__##n
#define OLD_ADMISSION(n) d.rootp->__PVT__ready_probe__DOT__old_dut__DOT__admission->n
#define NEW_ADMISSION(n) d.rootp->__PVT__ready_probe__DOT__new_dut__DOT__admission->n
#define BOTH(n,v) do{OLD(n)=(v);NEW(n)=(v);}while(0)
#include "successor_monitor.hpp"
static void require_owner(bool p,const std::string&s){if(!p)throw std::runtime_error(s);}
static void equal(Vready_probe&d){d.eval();require_owner(d.probe_public_equal&&d.probe_internal_equal&&d.probe_scale_equal,"whole producer pair mismatch");}
static void tick_owner(Vready_probe&d){d.clk=0;equal(d);const auto staged=successor_before(d,true);d.clk=1;equal(d);successor_after(d,staged,true);d.clk=0;equal(d);}
int inherited_owner_main(int argc,char**argv){try{
 require_owner(inherited_ready_main(argc,argv)==0,"inherited producer/cache readiness oracles");
 const unsigned seed=unsigned(std::stoul(argv[1]));Driver driver(seed,"/dev/null");auto&d=driver.d;
 d.reset=1;tick_owner(d);d.reset=0;uint64_t cases=0,reject64=0,reject66=0,accept=0;
 const std::array<uint32_t,18> nonces{{0,1,2,3,4,65535,65536,0x7fffffffU,0x80000000U,0xfffffff0U,0xfffffff7U,0xfffffff8U,0xfffffff9U,0xfffffffaU,0xfffffffbU,0xfffffffcU,0xfffffffeU,0xffffffffU}};
 for(uint32_t nonce:nonces)for(unsigned mask=0;mask<8;++mask)for(unsigned ent=0;ent<64;++ent){
  d.reset=1;tick_owner(d);d.reset=0;BOTH(state,2);BOTH(frame_running_owned,1);BOTH(plane,0);BOTH(tile_cursor,0);BOTH(producer_cell_cache,0);BOTH(child_nonce,nonce);BOTH(child_owned,0);
  bool entropy_bad=false;unsigned needed=0;
  for(unsigned p=0;p<3;++p){const bool nonzero=(mask>>p)&1;const uint32_t blocks=nonzero?(p==0?1U:p==1?0x80000000U:0xffffffffU):0U;const unsigned entropy=(ent>>(2*p))&3U;
   OLD_ADMISSION(plane_blocks)[p]=NEW_ADMISSION(plane_blocks)[p]=blocks;
   OLD_ADMISSION(plane_entropy)[p]=NEW_ADMISSION(plane_entropy)[p]=entropy;
   needed+=nonzero;if(nonzero&&entropy!=2)entropy_bad=true;
  }
  equal(d);const bool overflow=uint64_t(nonce)+needed>0xffffffffULL;
  require_owner(bool(NEW(nonce_budget_overflow))==overflow,"independent full32 nonce oracle");tick_owner(d);
  const unsigned reason=entropy_bad?64U:overflow?66U:0U;
  require_owner(d.error==reason&&d.frame_state==(reason?15U:3U),"entropy before nonce exact reason/state");
  require_owner(NEW(producer_cell_cache)==0&&OLD(producer_cell_cache)==0,"redundant cache write changed owner");
  if(reason==64)++reject64;else if(reason==66)++reject66;else ++accept;++cases;
 }
 // The arithmetic domain is all32 bits; deterministic RNG checks compare actual RTL wires without a state or RAM write.
 std::mt19937 random(seed);uint64_t random_cases=0;
 d.reset=1;tick_owner(d);d.reset=0;
 for(unsigned n=0;n<250000;++n){const uint32_t nonce=random();BOTH(child_nonce,nonce);unsigned count=0;
  for(unsigned p=0;p<3;++p){const uint32_t value=(random()&1U)?random():0U;OLD_ADMISSION(plane_blocks)[p]=NEW_ADMISSION(plane_blocks)[p]=value;count+=value!=0;}
  tick_owner(d);require_owner(bool(NEW(nonce_budget_overflow))==(uint64_t(nonce)+count>0xffffffffULL),"random full32 RTL nonce equivalence");++random_cases;
 }
 std::cout<<"{\"type\":\"v119_producer_owner\",\"status\":\"TEST_PASS\",\"cases\":"<<cases<<",\"random_cases\":"<<random_cases<<",\"reason64\":"<<reject64<<",\"reason66\":"<<reject66<<",\"accepted\":"<<accept<<",\"original_oracle_checks_removed\":0}\n";return 0;
 }catch(const std::exception&e){std::cerr<<"V119_OWNER_FAIL "<<e.what()<<'\n';return 1;}}
