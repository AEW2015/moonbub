#include "codec.hpp"
#include <iostream>
#include <random>
using namespace cu66;
int main() {try {
  unsigned checks=0;std::mt19937 random(940063);
  for(unsigned family=0;family<6;++family) {
    unsigned blocks=family==4?1:64;std::vector<int16_t> values(blocks*64);
    for(size_t i=0;i<values.size();++i) {if(family==1&&i%11==0)values[i]=int16_t((int(i)%5-2)*1024);if(family==2&&random()%17==0)values[i]=int16_t(int(random()%4097)-2048);if(family==3)values[i]=i%64==0?int16_t(i%128?2048:-2048):int16_t(i%127==0?1:0);if(family>=4)values[i]=int16_t(int(random()%4097)-2048);}
    auto optimized=cu94opt::prepare(values);auto frozen=cu94::prepare(values);const auto &p=optimized.base;
    for(unsigned c=0;c<4;++c) {
      need(p.streams[4][c]==frozen.streams[4][c],"frozen anchor equality");++checks;
      need(p.streams[2][c].size()<=p.streams[4][c].size(),"actual anchor guard");++checks;
      need(optimized.searches[c][0].tried==(c?20:14)&&optimized.searches[c][1].tried==(c?12:0),"complete k search");++checks;
      need(optimized.rate_k0[c]==p.streams[2][c][0]&&optimized.rate_k1[c]==p.streams[2][c][1],"chosen parameters");++checks;
    }
    auto choices=cu94opt::candidates(optimized);std::array<Bytes,3> packets{};for(unsigned i=0;i<3;++i) {packets[i]=cu94::assemble(p,choices[i]);need(cu94::decode(packets[i],blocks)==values,"native optimized parity");++checks;}
    need(packets[1].size()<=packets[0].size()&&packets[2].size()<=packets[1].size(),"packet no regression");++checks;
    need(packets[0]==cu94::assemble(frozen,170,10),"frozen anchor packet equality");++checks;
  }
  // Every legal explicit parameter must round-trip, including rare escapes.
  for(unsigned context=0;context<2;++context) {
    std::vector<uint32_t> a(96),b(context?96:0);a.back()=context?0xffffff:0x3fff;if(context)b.back()=0xfff;
    for(unsigned k0=0;k0<=(context?19u:13u);++k0)for(unsigned k1=0;k1<(context?12u:1u);++k1) {cu94::DecodeStats stats;auto stream=cu94opt::encode_explicit(a,b,context,k0,context?k1:255,stats);size_t i=0;cu94::read_stream(stream,2,context,unsigned(a.size()),[&](uint32_t x,uint32_t y) {need(x==a[i]&&(!context||y==b[i]),"explicit Rice parameters");++i;});need(i==a.size(),"explicit event count");++checks;}
  }
  for(unsigned escape: {12u,14u,24u}) {auto result=cu94opt::search({},escape==24?19:escape-1,escape);need(result.k==0&&result.score==0,"empty lower-k tie");++checks;}
  std::cout<<"{\"status\":\"PASS\",\"families\":6,\"explicit_parameter_pairs\":254,\"checks\":"<<checks<<"}\n";
}catch(const std::exception &error) {std::cerr<<"EC94OPT_TEST_FAIL "<<error.what()<<'\n';return 1;}}
