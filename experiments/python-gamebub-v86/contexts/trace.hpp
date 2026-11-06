#pragma once
#include "../../cu66-native-v69/entropy.hpp"
#include <memory>
namespace cu86 {
using namespace cu66;
// Primitive-operation observations. No field is an elapsed-clock measurement.
struct Work {
  uint32_t decisions=0, renorm=0, stream_bytes=0, rice_values=0, events=0,
           raw_bytes=0, header_bytes=0, crc_bytes=0, emits=0, raw_bits=0, prob_init=0;
};
struct ObservedArithmetic {
  View data;
  uint32_t n=0, pos=0, lo=0, hi=65535, code=0;
  std::array<unsigned,88> probability{};
  Work *work;
  ObservedArithmetic(View d, uint32_t bits, Work *w):data(d),n(bits),work(w) {
    need(n>=18 && d.n==(n+7)/8,"trace arithmetic bit bytes");
    if(n%8) need(!(d[d.n-1]&((1u<<(8-n%8))-1)),"trace arithmetic padding");
    probability.fill(128);
    for(unsigned i=0;i<16;++i) code=code*2+raw();
  }
  unsigned raw() {
    need(pos<n,"trace bit bound");
    if(pos%8==0) ++work->stream_bytes;
    ++work->raw_bits;
    auto out=(data[pos/8]>>(7-pos%8))&1;
    ++pos; return out;
  }
  unsigned read(unsigned context) {
    need(context<88,"trace arithmetic context"); ++work->decisions;
    auto pr=probability[context];
    uint32_t part=((hi-lo+1)*pr)/256;
    part=std::max(1u,std::min(hi-lo,part));
    auto boundary=lo+part-1;
    unsigned value=code>boundary;
    if(value) {lo=boundary+1;probability[context]=std::max(1u,pr-std::max(1u,pr/32));}
    else {hi=boundary;probability[context]=std::min(255u,pr+std::max(1u,(256-pr)/32));}
    for(;;) {
      uint32_t off;
      if(hi<32768) off=0;
      else if(lo>=32768) off=32768;
      else if(lo>=16384 && hi<49152) off=16384;
      else break;
      ++work->renorm; lo=(lo-off)*2;hi=(hi-off)*2+1;code=(code-off)*2+raw();
    }
    need(lo<=code && code<=hi,"trace arithmetic interval");return value;
  }
  uint32_t rice(unsigned k,unsigned escape,bool level=false) {
    ++work->rice_values;unsigned base=level?48:0,q=0;
    while(q<15) {if(read(base+q)) break;++q;}
    unsigned width=q==15?escape:k;uint32_t out=0;
    for(int bit=int(width)-1;bit>=0;--bit) out=out*2+read(base+16+std::min(bit,23));
    return q==15?out:(q<<k)|out;
  }
  void end() {need(n-pos==2 && raw()==0 && raw()==0,"trace arithmetic termination");}
};
struct Decoded {
  std::vector<int16_t> coefficients;
  std::vector<Work> work;
  std::vector<std::array<Work,4>> context_work;
  unsigned encoded_bytes=0;
  bool raw=false;
};
inline Decoded decode_interleaved(View packet,unsigned blocks,unsigned bw) {
  need(blocks && bw && blocks%bw==0,"trace geometry");
  checked(packet,46,46+128*blocks);
  Reader r(packet.sub(0,packet.n-4));
  need(r.magic()=="AB38" && r.u8()==1,"trace profile");
  unsigned flags=r.u8();
  need(flags<=1 && r.u32()==blocks && r.u16()==bw && r.u16()==0,"trace geometry binding");
  std::array<uint32_t,4> length{};for(auto &v:length) v=r.u32();
  std::array<uint32_t,3> counts{};for(auto &v:counts) v=r.u32();
  size_t sum=0;for(auto v:length)sum+=v;
  need(r.pos+sum==packet.n-4,"trace lengths");
  Decoded out;out.coefficients.resize(size_t(blocks)*64);out.work.resize(blocks);out.context_work.resize(blocks);
  out.encoded_bytes=unsigned(packet.n);out.raw=bool(flags);
  // CRC_READ scans the whole packet including the trailer; the first 42 header
  // bytes are captured during that scan, so they are not additional fetches.
  out.work[0].crc_bytes=unsigned(packet.n);
  if(flags) {
    need(length==std::array<uint32_t,4>{128*blocks,0,0,0} && counts==std::array<uint32_t,3>{0,0,0},"trace raw fields");
    for(unsigned b=0;b<blocks;++b) {
      for(unsigned i=0;i<64;++i) {
        int value=signed16(r.u16());need(value>=-2048 && value<=2048,"trace raw range");
        out.coefficients[b*64+i]=int16_t(value);
      }
      out.work[b].raw_bytes=128;
    }
    r.end();return out;
  }
  struct Stream {unsigned k0,k1;View data;uint32_t bits;};
  std::array<Stream,4> stream{};
  for(unsigned i=0;i<4;++i) {
    need(length[i]>=9,"trace stream bound");Reader q(r.take(length[i]));
    auto k0=q.u8(),k1=q.u8();auto bits=q.u32();
    stream[i]={k0,k1,q.take(q.v.n-q.pos),bits};
    out.work[0].header_bytes+=6;
    // PAD_READ always fetches the final byte, even with byte-aligned bits.
    ++out.work[0].header_bytes;
  }
  r.end();
  for(unsigned i=0;i<4;++i)out.context_work[0][i].prob_init=88;
  need(stream[0].k0<=13 && stream[0].k1==255,"trace DC parameters");
  const unsigned width[3]={5,15,43},low[3]={1,6,21};
  std::array<std::unique_ptr<ObservedArithmetic>,4> arithmetic;
  for(unsigned i=0;i<4;++i) arithmetic[i]=std::make_unique<ObservedArithmetic>(stream[i].data,stream[i].bits,&out.context_work[0][i]);
  std::array<int64_t,3> pending_index{-1,-1,-1};
  std::array<int,3> pending_value{};
  auto pending_left=counts;
  std::array<bool,4> finished{};
  auto event=[&](unsigned band) {
    auto &a=*arithmetic[band+1];
    if(!pending_left[band]) {
      pending_index[band]=int64_t(blocks)*width[band];pending_value[band]=0;
      need(!finished[band+1],"trace duplicate stream finish");a.end();finished[band+1]=true;
    } else {
      pending_index[band]+=int64_t(a.rice(stream[band+1].k0,24))+1;
      need(pending_index[band]<int64_t(blocks)*width[band],"trace run bound");
      pending_value[band]=signed_zig(a.rice(stream[band+1].k1,12,true)+1);
      need(pending_value[band] && pending_value[band]>=-2048 && pending_value[band]<=2048,"trace level bound");
      --pending_left[band];++a.work->events;
    }
  };
  for(unsigned band=0;band<3;++band) {
    need(stream[band+1].k0<=19 && stream[band+1].k1<=11 && counts[band]<=blocks*width[band],"trace AC parameters");
    event(band);
  }
  std::array<unsigned,64> order{};for(unsigned i=0;i<64;++i)order[i]=i;
  std::stable_sort(order.begin(),order.end(),[](unsigned a,unsigned b) {
    unsigned sa=a/8+a%8,sb=b/8+b%8;
    if(sa!=sb)return sa<sb;
    return sa%2?a/8<b/8:a/8>b/8;
  });
  int previous=0;
  for(unsigned b=0;b<blocks;++b) {
    for(unsigned i=0;i<4;++i)arithmetic[i]->work=&out.context_work[b][i];
    if(b%bw==0)previous=0;
    previous+=signed_zig(arithmetic[0]->rice(stream[0].k0,14));
    need(previous>=-2048 && previous<=2048,"trace DC bound");
    out.coefficients[b*64]=int16_t(previous);
    if(b+1==blocks){arithmetic[0]->end();finished[0]=true;}
    for(unsigned band=0;band<3;++band) {
      while(pending_index[band]<int64_t(b+1)*width[band]) {
        need(pending_index[band]>=int64_t(b)*width[band],"trace stale event");
        auto zig=low[band]+unsigned(pending_index[band]-int64_t(b)*width[band]);
        out.coefficients[b*64+order[zig]]=int16_t(pending_value[band]);
        event(band);
      }
    }
  }
  need(std::all_of(finished.begin(),finished.end(),[](bool v){return v;}),"trace stream completion");
  need(std::all_of(pending_left.begin(),pending_left.end(),[](unsigned v){return !v;}),"trace event completion");
  return out;
}
} // namespace cu86
