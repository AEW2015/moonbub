#define main inherited_admission_main
#include "tb_admission.cpp"
#undef main
int main(int argc,char**argv){try{
 require(inherited_admission_main(argc,argv)==0,"inherited complete admission suite");Vadmission_probe d;d.clk=0;d.reset=1;d.start=d.abort_packet=d.cache_write=d.lookup_req=d.replay_req=d.in_valid=d.in_last=d.receipt_ready=0;d.packet_bytes=256;d.epoch=119;
 auto tick=[&](){d.clk=0;d.eval();require(!d.mismatch,"all admission fields low");d.clk=1;d.eval();require(!d.mismatch,"all admission fields high");d.clk=0;d.eval();require(!d.mismatch,"all admission fields falling");};
 tick();d.reset=0;uint64_t cases=0;
 const std::array<uint32_t,15> lengths{{0U,1U,2U,975U,976U,977U,65535U,0x7fffffffU,0x80000000U,0xffffff7fU,0xffffff80U,0xffffff81U,0xfffffffeU,0xffffffffU,128U}};
 for(uint32_t length:lengths)for(unsigned which=0;which<2;++which)for(unsigned trailing=0;trailing<2;++trailing){
  const uint32_t end=uint32_t(128U+length);const std::array<uint32_t,9> cursors{{0U,127U,128U,end-1U,end,end+1U,0x7fffffffU,0x80000000U,0xffffffffU}};
  for(uint32_t cursor:cursors){d.reset=1;tick();d.reset=0;
   QBOTH(coord_valid,0U);QBOTH(state,which?12U:8U);QBOTH(mode_bytes,length);QBOTH(q_start,end);QBOTH(mode_cursor,cursor);QBOTH(bits_left,0U);QBOTH(bit_cache,trailing?1U:0U);QBOTH(key_frame,0U);QBOTH(size_bytes,256U);QBOTH(snapshot_valid,0U);
   d.eval();require(!d.mismatch,"coherent mode bound preparation");tick();
   const bool reject=which?(cursor!=end||trailing):(cursor>=end);
   require(d.error==(reject?8U:0U),"independent full32 mode bound first reason");++cases;
  }
 }
 std::cout<<"{\"type\":\"v119_mode_bound\",\"status\":\"TEST_PASS\",\"cases\":"<<cases<<",\"original_oracle_checks_removed\":0}\n";return 0;
 }catch(const std::exception&e){std::cerr<<"V119_MODE_BOUND_FAIL "<<e.what()<<'\n';return 1;}}
