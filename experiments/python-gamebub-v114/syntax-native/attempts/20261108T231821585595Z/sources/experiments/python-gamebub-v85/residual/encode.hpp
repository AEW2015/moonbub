#pragma once
#include "../../cu66-native-v69/entropy.hpp"
#include <limits>
namespace cu85 {
using namespace cu66;
inline void put16(Bytes &out, uint16_t x) { out.push_back(uint8_t(x));out.push_back(uint8_t(x>>8)); }
inline void put32(Bytes &out, uint32_t x) { put16(out,uint16_t(x));put16(out,uint16_t(x>>16)); }
inline uint32_t mapped(int value) { return value<0?uint32_t(-value*2-1):uint32_t(value*2); }
struct BinaryEncoder {
  uint32_t low=0,high=65535,pending=0;
  std::array<unsigned,88> p{};
  Bytes bits;
  uint64_t decisions=0,renorm=0;
  BinaryEncoder() {p.fill(128);}
  void emit(unsigned bit) {
    bits.push_back(uint8_t(bit));
    while(pending) {bits.push_back(uint8_t(1-bit));--pending;}
  }
  void bit(unsigned value,unsigned context) {
    need(value<=1 && context<88,"encoder bit/context");
    unsigned probability=p[context];uint32_t width=high-low+1;
    uint32_t part=std::max(1u,std::min(high-low,(width*probability)>>8));
    uint32_t split=low+part-1;
    if(value) {low=split+1;probability-=std::max(1u,probability>>5);}
    else {high=split;probability+=std::max(1u,(256-probability)>>5);}
    p[context]=std::min(255u,std::max(1u,probability));
    for(;;) {
      if(high<32768) emit(0);
      else if(low>=32768) {emit(1);low-=32768;high-=32768;}
      else if(low>=16384 && high<49152) {++pending;low-=16384;high-=16384;}
      else break;
      low*=2;high=high*2+1;++renorm;
    }
    ++decisions;
  }
  void rice(uint32_t value,unsigned k,unsigned escape,bool level=false) {
    need(value<(1u<<escape),"encoder Rice domain");
    unsigned quotient=value>>k,base=level?48:0;
    for(unsigned i=0;i<std::min(quotient,15u);++i)bit(0,base+i);
    unsigned width;
    if(quotient<15) {bit(1,base+quotient);value&=(1u<<k)-1;width=k;}
    else width=escape;
    for(int i=int(width)-1;i>=0;--i)bit((value>>i)&1,base+16+std::min(i,23));
  }
  std::pair<Bytes,uint32_t> finish() {
    ++pending;emit(low>=16384);
    for(unsigned i=0;i<16;++i)bits.push_back(0);
    uint32_t length=uint32_t(bits.size());Bytes out((length+7)/8,0);
    for(unsigned i=0;i<length;++i)out[i/8]|=uint8_t(bits[i]<<(7-i%8));
    return {out,length};
  }
};
inline unsigned best_k(const std::vector<uint32_t> &v,unsigned maximum,unsigned escape) {
  unsigned best=0;uint64_t best_cost=std::numeric_limits<uint64_t>::max();
  for(unsigned k=0;k<=maximum;++k) {
    uint64_t cost=0;
    for(auto x:v)cost+=(x>>k)<15?(x>>k)+1+k:15+escape;
    if(cost<best_cost) {best=k;best_cost=cost;}
  }
  return best;
}
inline const std::array<unsigned,64> &order() {
  static const auto value=[] {
    std::array<unsigned,64> a{};for(unsigned i=0;i<64;++i)a[i]=i;
    std::stable_sort(a.begin(),a.end(),[](unsigned x,unsigned y) {
      unsigned sx=x/8+x%8,sy=y/8+y%8;
      return sx!=sy?sx<sy:sx%2?x/8<y/8:x/8>y/8;
    });return a;
  }();return value;
}
struct Encoded {
  Bytes packet;
  std::array<uint64_t,4> decisions{},renorm{};
  bool raw=false;
};
inline Encoded encode(const std::vector<int16_t> &a) {
  need(!a.empty() && a.size()%64==0 && a.size()/64<=65536,"encoder geometry");
  const unsigned blocks=unsigned(a.size()/64);
  for(auto x:a)need(x>=-2048 && x<=2048,"encoder coefficient domain");
  Encoded result;std::array<Bytes,4> streams;std::array<uint32_t,3> counts{};
  std::vector<uint32_t> dc;dc.reserve(blocks);
  // This residual-only component explicitly resets DC prediction per tile.
  for(unsigned b=0;b<blocks;++b)dc.push_back(mapped(a[b*64]));
  unsigned kd=best_k(dc,13,14);BinaryEncoder coder;
  for(auto v:dc)coder.rice(v,kd,14);
  auto finished=coder.finish();streams[0].push_back(uint8_t(kd));streams[0].push_back(255);
  put32(streams[0],finished.second);streams[0].insert(streams[0].end(),finished.first.begin(),finished.first.end());
  result.decisions[0]=coder.decisions;result.renorm[0]=coder.renorm;
  const unsigned limits[4]={1,6,21,64};
  for(unsigned band=0;band<3;++band) {
    std::vector<uint32_t> runs,levels;int64_t previous=-1;
    unsigned width=limits[band+1]-limits[band];
    for(unsigned b=0;b<blocks;++b)for(unsigned i=limits[band];i<limits[band+1];++i) {
      int value=a[b*64+order()[i]];
      if(value) {
        int64_t position=int64_t(b)*width+i-limits[band];
        runs.push_back(uint32_t(position-previous-1));levels.push_back(mapped(value)-1);previous=position;
      }
    }
    counts[band]=uint32_t(runs.size());unsigned kr=best_k(runs,19,24),kv=best_k(levels,11,12);
    BinaryEncoder ac;
    for(size_t i=0;i<runs.size();++i) {ac.rice(runs[i],kr,24);ac.rice(levels[i],kv,12,true);}
    auto bits=ac.finish();auto &s=streams[band+1];s.push_back(uint8_t(kr));s.push_back(uint8_t(kv));put32(s,bits.second);
    s.insert(s.end(),bits.first.begin(),bits.first.end());result.decisions[band+1]=ac.decisions;result.renorm[band+1]=ac.renorm;
  }
  size_t total=0;for(const auto &s:streams)total+=s.size();result.raw=total>=128*blocks;
  Bytes out{'A','B','3','8',1,uint8_t(result.raw)};put32(out,blocks);put16(out,1);put16(out,0);
  for(unsigned i=0;i<4;++i)put32(out,result.raw?(i==0?128*blocks:0):uint32_t(streams[i].size()));
  for(auto count:counts)put32(out,result.raw?0:count);
  if(result.raw)for(auto value:a)put16(out,uint16_t(value));
  else for(const auto &s:streams)out.insert(out.end(),s.begin(),s.end());
  put32(out,crc32(out));result.packet=std::move(out);
  need(decode_ab38(result.packet,blocks,1)==a,"independent generated chunk coefficient parity");
  return result;
}
} // namespace cu85
