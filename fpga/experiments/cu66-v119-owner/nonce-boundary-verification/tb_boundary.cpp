#define main retained_ready_entry_not_run
#include "tb_ready.cpp"
#undef main
#include "Vready_probe_cs88_admission_v91i2a.h"
#define OLD(n) d.rootp->ready_probe__DOT__old_dut__DOT__##n
#define NEW(n) d.rootp->ready_probe__DOT__new_dut__DOT__##n
#define OLD_ADMISSION(n) d.rootp->__PVT__ready_probe__DOT__old_dut__DOT__admission->n
#define NEW_ADMISSION(n) d.rootp->__PVT__ready_probe__DOT__new_dut__DOT__admission->n
#define BOTH(n,v) do{OLD(n)=(v);NEW(n)=(v);}while(0)
static void require_boundary(bool value,const std::string&message){if(!value)throw std::runtime_error(message);}
static void equal_boundary(Vready_probe&d){d.eval();require_boundary(d.probe_public_equal&&d.probe_internal_equal&&d.probe_scale_equal,"every retained producer public/private/raw-scale field");}
static void edge_boundary(Vready_probe&d,uint64_t&edges){d.clk=0;equal_boundary(d);require_boundary(!d.mem_req_valid&&!d.frame_read_req,"predicate fixture created physical request");d.clk=1;equal_boundary(d);d.clk=0;equal_boundary(d);++edges;}
int main(int argc,char**argv){try{
 require_boundary(argc==2,"usage: nonce-boundary seed");const unsigned seed=unsigned(std::stoul(argv[1]));Driver driver(seed,"/dev/null");auto&d=driver.d;
 uint64_t cases=0,reason64=0,reason66=0,accepted=0,both_bad_priority=0,edges=0,cancel_cases=0,fd_cases=0;
 d.reset=1;edge_boundary(d,edges);d.reset=0;
 for(uint32_t nonce:{0xfffffffcU,0xfffffffdU,0xfffffffeU,0xffffffffU})for(unsigned mask=0;mask<8;++mask)for(unsigned entropies=0;entropies<64;++entropies){
  d.reset=1;edge_boundary(d,edges);d.reset=0;
  // Verification-only complete CHECK_ENTROPY poststate. No physical lease,
  // queue owner, RAM byte or accepted request is fabricated.
  BOTH(state,2U);BOTH(frame_running_owned,1U);BOTH(plane,0U);BOTH(tile_cursor,0U);BOTH(producer_cell_cache,0U);BOTH(child_nonce,nonce);BOTH(child_owned,0U);
  unsigned needed=0;bool entropy_bad=false;
  for(unsigned p=0;p<3;++p){const bool live=(mask>>p)&1U;const uint32_t blocks=live?(p==0?1U:p==1?0x80000000U:0xffffffffU):0U;const unsigned entropy=(entropies>>(2U*p))&3U;
   OLD_ADMISSION(plane_blocks)[p]=NEW_ADMISSION(plane_blocks)[p]=blocks;
   OLD_ADMISSION(plane_entropy)[p]=NEW_ADMISSION(plane_entropy)[p]=entropy;
   needed+=live;entropy_bad=entropy_bad||(live&&entropy!=2U);
  }
  equal_boundary(d);const bool overflow=uint64_t(nonce)+uint64_t(needed)>0xffffffffULL;
  require_boundary(bool(NEW(nonce_budget_overflow))==overflow,"actual retained RTL full32 boundary expression");
  edge_boundary(d,edges);const unsigned reason=entropy_bad?64U:overflow?66U:0U;
  require_boundary(d.error==reason&&d.frame_state==(reason?15U:3U),"entropy-before-overflow reason and state");
  require_boundary(NEW(child_nonce)==nonce&&OLD(child_nonce)==nonce,"CHECK changed declaration-owned nonce");
  require_boundary(NEW(producer_cell_cache)==0U&&OLD(producer_cell_cache)==0U,"CHECK redundant cache write differs");
  if(reason==64U)++reason64;else if(reason==66U)++reason66;else ++accepted;
  if(entropy_bad&&overflow)++both_bad_priority;
  if(nonce==0xfffffffdU)++fd_cases;
  ++cases;
 }
 // External reset/abort retain their original priority over a bad budget and
 // do not clear the existing declaration-initialized nonce lifetime.
 for(unsigned flags=1;flags<4;++flags){
  d.reset=1;edge_boundary(d,edges);d.reset=0;
  BOTH(state,2U);BOTH(frame_running_owned,1U);BOTH(plane,0U);BOTH(tile_cursor,0U);BOTH(producer_cell_cache,0U);BOTH(child_nonce,0xffffffffU);BOTH(child_owned,0U);
  for(unsigned p=0;p<3;++p){OLD_ADMISSION(plane_blocks)[p]=NEW_ADMISSION(plane_blocks)[p]=1U;OLD_ADMISSION(plane_entropy)[p]=NEW_ADMISSION(plane_entropy)[p]=3U;}
  d.reset=flags&1U;d.abort_packet=(flags>>1U)&1U;edge_boundary(d,edges);
  require_boundary(!d.error&&d.frame_state==0U&&NEW(child_nonce)==0xffffffffU&&OLD(child_nonce)==0xffffffffU,"reset/abort priority or nonce warm lifetime");d.reset=d.abort_packet=0;++cancel_cases;
 }
 std::cout<<"{\"type\":\"v119_nonce_boundary_auxiliary\",\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"cases\":"<<cases<<",\"fd_cases\":"<<fd_cases<<",\"reason64\":"<<reason64<<",\"reason66\":"<<reason66<<",\"accepted\":"<<accepted<<",\"both_bad_priority64\":"<<both_bad_priority<<",\"reset_abort_cases\":"<<cancel_cases<<",\"clock_edges\":"<<edges<<",\"model_reused\":true,\"natural_frame_claim\":false,\"physical_request_accepts\":0}\n";
 return 0;
}catch(const std::exception&e){std::cerr<<"V119_NONCE_BOUNDARY_FAIL "<<e.what()<<'\n';return 1;}}
