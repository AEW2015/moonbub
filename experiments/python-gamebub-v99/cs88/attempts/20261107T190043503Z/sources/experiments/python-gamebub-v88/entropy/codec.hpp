#pragma once
#include "../../cu66-native-v69/entropy.hpp"
#include "../../python-gamebub-v85/residual/encode.hpp"
namespace cu88 {
using namespace cu66;
struct PlainBits {
  Bytes data;uint32_t size=0;
  void bit(unsigned value) {if(size%8==0)data.push_back(0);data.back()|=uint8_t(value<<(7-size%8));++size;}
  void rice(uint32_t value,unsigned k,unsigned escape) {
    need(value<(1u<<escape),"BR88 encoder domain");unsigned q=value>>k;
    for(unsigned i=0;i<std::min(q,15u);++i)bit(0);
    unsigned width=q<15?k:escape;
    if(q<15) {bit(1);value&=(1u<<k)-1;}
    for(int i=int(width)-1;i>=0;--i)bit((value>>i)&1);
  }
};
struct RiceReader {
  Bits bits;
  explicit RiceReader(View bytes,uint32_t size):bits(bytes,size) {}
  uint32_t read(unsigned k,unsigned escape) {
    unsigned q=0;while(q<15&&!bits.bit())++q;
    unsigned width=q<15?k:escape;uint32_t v=0;
    for(unsigned i=0;i<width;++i)v=(v<<1)|bits.bit();
    return q==15?v:(q<<k)|v;
  }
  void end() {need(bits.pos==bits.n,"BR88 trailing coded bits");}
};
struct Encoded {
  Bytes packet;bool raw=false;
  std::array<uint64_t,4> bits{},values{},events{};
};
inline Encoded encode_br88(const std::vector<int16_t> &a) {
  need(!a.empty()&&a.size()%64==0&&a.size()/64<=65536,"BR88 encoder geometry");
  unsigned blocks=unsigned(a.size()/64);for(auto x:a)need(x>=-2048&&x<=2048,"BR88 encoder range");
  Encoded result;std::array<Bytes,4> streams;std::array<uint32_t,3> counts{};
  std::vector<uint32_t> dc;for(unsigned b=0;b<blocks;++b)dc.push_back(cu85::mapped(a[b*64]));
  unsigned kd=cu85::best_k(dc,13,14);PlainBits writer;
  for(auto value:dc)writer.rice(value,kd,14);
  streams[0].push_back(uint8_t(kd));streams[0].push_back(255);cu85::put32(streams[0],writer.size);
  streams[0].insert(streams[0].end(),writer.data.begin(),writer.data.end());
  result.bits[0]=writer.size;result.values[0]=blocks;
  const unsigned limits[4]={1,6,21,64};
  for(unsigned band=0;band<3;++band) {
    std::vector<uint32_t> runs,levels;int64_t previous=-1;unsigned width=limits[band+1]-limits[band];
    for(unsigned b=0;b<blocks;++b)for(unsigned i=limits[band];i<limits[band+1];++i) {
      int value=a[b*64+cu85::order()[i]];
      if(value) {int64_t pos=int64_t(b)*width+i-limits[band];runs.push_back(uint32_t(pos-previous-1));levels.push_back(cu85::mapped(value)-1);previous=pos;}
    }
    counts[band]=uint32_t(runs.size());unsigned kr=cu85::best_k(runs,19,24),kv=cu85::best_k(levels,11,12);PlainBits bits;
    for(size_t i=0;i<runs.size();++i) {bits.rice(runs[i],kr,24);bits.rice(levels[i],kv,12);}
    auto &stream=streams[band+1];stream.push_back(uint8_t(kr));stream.push_back(uint8_t(kv));cu85::put32(stream,bits.size);
    stream.insert(stream.end(),bits.data.begin(),bits.data.end());result.bits[band+1]=bits.size;result.values[band+1]=2*runs.size();result.events[band+1]=runs.size();
  }
  size_t total=0;for(const auto &stream:streams)total+=stream.size();result.raw=total>=128*blocks;
  Bytes out{'B','R','8','8',1,uint8_t(result.raw)};cu85::put32(out,blocks);cu85::put16(out,1);cu85::put16(out,0);
  for(unsigned i=0;i<4;++i)cu85::put32(out,result.raw?(i?0:128*blocks):uint32_t(streams[i].size()));
  for(auto n:counts)cu85::put32(out,result.raw?0:n);
  if(result.raw) {for(auto value:a)cu85::put16(out,uint16_t(value));result.bits={uint64_t(16)*a.size(),0,0,0};result.values={0,0,0,0};result.events={0,0,0,0};}
  else for(const auto &stream:streams)out.insert(out.end(),stream.begin(),stream.end());
  cu85::put32(out,crc32(out));result.packet=std::move(out);return result;
}
inline std::vector<int16_t> decode_br88(View packet,unsigned blocks,unsigned bw) {
  need(blocks>=1&&blocks<=65536&&bw==1,"BR88 geometry");checked(packet,46,46+128*blocks);
  Reader r(packet.sub(0,packet.n-4));need(r.magic()=="BR88"&&r.u8()==1,"BR88 profile");
  unsigned flags=r.u8();need(flags<=1&&r.u32()==blocks&&r.u16()==1&&r.u16()==0,"BR88 binding");
  std::array<uint32_t,4> lengths{};std::array<uint32_t,3> counts{};
  for(auto &n:lengths)n=r.u32();
  for(auto &n:counts)n=r.u32();
  size_t sum=0;for(auto n:lengths)sum+=n;need(r.pos+sum==packet.n-4,"BR88 lengths");
  std::vector<int16_t> result(size_t(blocks)*64,0);
  if(flags) {
    need(lengths==std::array<uint32_t,4>{128*blocks,0,0,0}&&counts==std::array<uint32_t,3>{0,0,0},"BR88 raw fields");
    for(auto &value:result) {value=int16_t(signed16(r.u16()));need(value>=-2048&&value<=2048,"BR88 raw range");}r.end();return result;
  }
  struct S {unsigned k0,k1;uint32_t bits;View data;};std::array<S,4> streams;
  for(unsigned i=0;i<4;++i) {
    need(lengths[i]>=6,"BR88 stream header");Reader s(r.take(lengths[i]));unsigned k0=s.u8(),k1=s.u8();uint32_t n=s.u32();
    need((uint64_t(n)+7)/8==lengths[i]-6,"BR88 exact bit bytes");auto data=s.take(lengths[i]-6);s.end();
    if(n%8)need((data[data.n-1]&((1u<<(8-n%8))-1))==0,"BR88 padding");
    streams[i]={k0,k1,n,data};
  }
  r.end();need(streams[0].k0<=13&&streams[0].k1==255,"BR88 DC parameters");
  RiceReader dc(streams[0].data,streams[0].bits);
  for(unsigned b=0;b<blocks;++b) {int value=signed_zig(dc.read(streams[0].k0,14));need(value>=-2048&&value<=2048,"BR88 DC range");result[b*64]=int16_t(value);}dc.end();
  const unsigned limits[4]={1,6,21,64};
  for(unsigned band=0;band<3;++band) {
    const auto &stream=streams[band+1];unsigned width=limits[band+1]-limits[band];
    need(stream.k0<=19&&stream.k1<=11&&counts[band]<=blocks*width,"BR88 AC parameters");RiceReader input(stream.data,stream.bits);int64_t at=-1;
    for(unsigned event=0;event<counts[band];++event) {
      at+=input.read(stream.k0,24)+1;need(at<int64_t(blocks*width),"BR88 run range");int value=signed_zig(input.read(stream.k1,12)+1);
      need(value&&value>=-2048&&value<=2048,"BR88 level range");result[(at/width)*64+cu85::order()[limits[band]+at%width]]=int16_t(value);
    }input.end();
  }
  return result;
}
} // namespace cu88
