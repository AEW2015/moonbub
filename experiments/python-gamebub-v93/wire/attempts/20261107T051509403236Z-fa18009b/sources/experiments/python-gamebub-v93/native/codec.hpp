#pragma once
// EC93 research profile: frozen AB/BR, arithmetic unary + raw suffix, and
// bounded 32-event Rice groups. HY bypasses every suffix by a fixed rule.
#include "../../python-gamebub-v92/native/codec.hpp"
namespace cu93 {
using namespace cu66;
struct DecodeStats {
  std::array<uint64_t,4> ab_decisions{},ab_renorm{},plain_bits{},group_headers{},arithmetic_inits{};
};
inline View bit_bytes(Reader &r,uint32_t bits) {
  auto data=r.take(size_t((uint64_t(bits)+7)/8));
  if(bits%8)need((data[data.n-1]&((1u<<(8-bits%8))-1))==0,"EC93 bit padding");
  return data;
}
inline void parameters(unsigned context,unsigned k0,unsigned k1) {
  need(context? k0<=19&&k1<=11 : k0<=13&&k1==255,"EC93 Rice parameters");
}
template<class Emit> inline void read_stream(View bytes,unsigned method,unsigned context,unsigned events,Emit emit,DecodeStats *stats) {
  Reader r(bytes);unsigned k0=0,k1=0;
  auto account=[&](uint64_t decisions,uint64_t renorm,uint64_t plain,uint64_t groups,uint64_t inits) {
    if(stats) {stats->ab_decisions[context]=decisions;stats->ab_renorm[context]=renorm;stats->plain_bits[context]=plain;stats->group_headers[context]=groups;stats->arithmetic_inits[context]=inits;}
  };
  if(method<3) {
    k0=r.u8();k1=r.u8();parameters(context,k0,k1);uint32_t first=r.u32();
    uint32_t second=method==2?r.u32():0;View data=bit_bytes(r,first),suffix=bit_bytes(r,second);r.end();
    if(method==1) {
      cu88::RiceReader reader(data,first);
      for(unsigned i=0;i<events;++i) {auto a=reader.read(k0,context?24:14);auto b=context?reader.read(k1,12):0;emit(a,b);}
      reader.end();account(0,0,first,0,0);
    } else {
      cu92::Arithmetic reader(data,first);Bits plain(suffix,second);
      auto rice=[&](unsigned k,unsigned escape,bool level) {
        if(method==0)return reader.rice(k,escape,level);
        unsigned q=0,base=level?48:0;while(q<15&&!reader.bit(base+q))++q;
        unsigned width=q==15?escape:k;uint32_t value=0;
        for(unsigned i=0;i<width;++i)value=value*2+plain.bit();
        return q==15?value:(q<<k)|value;
      };
      for(unsigned i=0;i<events;++i) {auto a=rice(k0,context?24:14,false);auto b=context?rice(k1,12,true):0;emit(a,b);}
      reader.end();need(plain.pos==plain.n,"EC93 HY trailing suffix");account(reader.decisions,reader.renorm,second,0,1);
    }
  } else {
    need(r.u8()==32&&r.u8()==0,"EC93 SG profile");unsigned groups=r.u32();need(groups==(events+31)/32,"EC93 SG count");uint64_t plain=0;
    for(unsigned group=0;group<groups;++group) {
      k0=r.u8();k1=r.u8();parameters(context,k0,k1);uint32_t length=r.u32();View data=bit_bytes(r,length);cu88::RiceReader input(data,length);
      for(unsigned i=group*32;i<std::min(events,(group+1)*32);++i) {auto a=input.read(k0,context?24:14);auto b=context?input.read(k1,12):0;emit(a,b);}
      input.end();plain+=length;
    }
    r.end();account(0,0,plain,groups,0);
  }
}
inline std::vector<int16_t> decode_ec93(View packet,unsigned blocks,unsigned bw=1,DecodeStats *stats=nullptr) {
  need(blocks>=1&&blocks<=65536&&bw==1,"EC93 geometry");checked(packet,48,48+128*size_t(blocks));if(stats)*stats=DecodeStats{};
  Reader r(packet.sub(0,packet.n-4));need(r.magic()=="EC93"&&r.u8()==1,"EC93 profile");unsigned flags=r.u8(),selector=r.u8();
  need(flags<=1&&r.u8()==0,"EC93 flags/reserved");need(r.u32()==blocks&&r.u16()==1&&r.u16()==0,"EC93 binding");
  std::array<uint32_t,4> lengths{};std::array<uint32_t,3> counts{};for(auto &v:lengths)v=r.u32();for(auto &v:counts)v=r.u32();
  size_t total=0;for(auto length:lengths)total+=length;need(r.pos+total==packet.n-4,"EC93 lengths");std::vector<int16_t> values(size_t(blocks)*64);
  if(flags) {
    need(selector==0&&lengths==std::array<uint32_t,4>{128*blocks,0,0,0}&&counts==std::array<uint32_t,3>{0,0,0},"EC93 raw fields");
    for(auto &value:values) {value=int16_t(signed16(r.u16()));need(value>=-2048&&value<=2048,"EC93 raw range");}r.end();return values;
  }
  need(total<128*size_t(blocks),"EC93 coded bound");const unsigned limits[4]={1,6,21,64};
  for(unsigned context=0;context<4;++context) {
    unsigned width=context?limits[context]-limits[context-1]:1;unsigned events=context?counts[context-1]:blocks;
    need(events<=blocks*width,"EC93 event bound");int64_t at=-1;unsigned dc=0;
    read_stream(r.take(lengths[context]),(selector>>(2*context))&3,context,events,[&](uint32_t a,uint32_t b) {
      int value=signed_zig(context?b+1:a);need(value>=-2048&&value<=2048&&(!context||value),"EC93 coefficient range");
      if(!context)values[(dc++)*64]=int16_t(value);
      else {at+=int64_t(a)+1;need(at<int64_t(blocks*width),"EC93 AC position");values[(at/width)*64+cu85::order()[limits[context-1]+at%width]]=int16_t(value);}
    },stats);
  }
  r.end();return values;
}
inline std::vector<int16_t> decode(View packet,unsigned blocks,unsigned bw=1) {return decode_ec93(packet,blocks,bw);}
struct Prepared {
  unsigned blocks=0;std::vector<int16_t> coefficients;cu85::Encoded ab;cu88::Encoded br;
  std::array<std::array<Bytes,4>,4> streams{};std::array<uint32_t,3> counts{};bool source_raw_fallback=false;
  std::array<DecodeStats,4> metrics{};
  std::array<std::array<std::array<uint64_t,2>,24>,2> suffix_histogram{};
};
inline Prepared prepare(const std::vector<int16_t> &values) {
  Prepared p;p.coefficients=values;p.blocks=unsigned(values.size()/64);
  // Frozen coders run exactly once, including their internal validation. If
  // either discards streams for RAW, all EC93 assemblies conservatively use RAW.
  p.ab=cu85::encode(values);p.br=cu88::encode_br88(values);p.source_raw_fallback=p.ab.raw||p.br.raw;
  if(!p.source_raw_fallback) {
    p.streams[0]=cu92::split_streams(p.ab.packet,p.counts);std::array<uint32_t,3> counts{};
    p.streams[1]=cu92::split_streams(p.br.packet,counts);need(counts==p.counts,"EC93 frozen event counts");
  }
  p.metrics[0].ab_decisions=p.ab.decisions;p.metrics[0].ab_renorm=p.ab.renorm;p.metrics[0].arithmetic_inits.fill(1);
  p.metrics[1].plain_bits=p.br.bits;const unsigned limits[4]={1,6,21,64};
  for(unsigned context=0;context<4;++context) {
    std::vector<uint32_t> a,b;
    if(!context) {for(unsigned block=0;block<p.blocks;++block)a.push_back(cu85::mapped(values[block*64]));}
    else {
      int64_t previous=-1;unsigned width=limits[context]-limits[context-1];
      for(unsigned block=0;block<p.blocks;++block)for(unsigned i=limits[context-1];i<limits[context];++i) {
        int value=values[block*64+cu85::order()[i]];if(value) {int64_t at=int64_t(block)*width+i-limits[context-1];a.push_back(uint32_t(at-previous-1));b.push_back(cu85::mapped(value)-1);previous=at;}
      }
      p.counts[context-1]=uint32_t(a.size());
    }
    unsigned k0=cu85::best_k(a,context?19:13,context?24:14),k1=context?cu85::best_k(b,11,12):255;
    cu85::BinaryEncoder prefix;cu88::PlainBits suffix;
    auto hybrid=[&](uint32_t value,unsigned k,unsigned escape,bool level) {
      unsigned q=value>>k,base=level?48:0;for(unsigned i=0;i<std::min(q,15u);++i)prefix.bit(0,base+i);
      unsigned width=q<15?k:escape;if(q<15) {prefix.bit(1,base+q);value&=(1u<<k)-1;}
      for(int i=int(width)-1;i>=0;--i) {unsigned bit=(value>>i)&1;suffix.bit(bit);++p.suffix_histogram[level?1:0][unsigned(i)][bit];}
    };
    for(size_t i=0;i<a.size();++i) {hybrid(a[i],k0,context?24:14,false);if(context)hybrid(b[i],k1,12,true);}
    auto bits=prefix.finish();auto &hy=p.streams[2][context];hy.push_back(uint8_t(k0));hy.push_back(uint8_t(k1));cu85::put32(hy,bits.second);cu85::put32(hy,suffix.size);
    hy.insert(hy.end(),bits.first.begin(),bits.first.end());hy.insert(hy.end(),suffix.data.begin(),suffix.data.end());
    p.metrics[2].ab_decisions[context]=prefix.decisions;p.metrics[2].ab_renorm[context]=prefix.renorm;p.metrics[2].plain_bits[context]=suffix.size;p.metrics[2].arithmetic_inits[context]=1;
    auto &sg=p.streams[3][context];sg.push_back(32);sg.push_back(0);cu85::put32(sg,uint32_t((a.size()+31)/32));
    for(size_t first=0;first<a.size();first+=32) {
      auto last=std::min(a.size(),first+32);std::vector<uint32_t> ga(a.begin()+std::ptrdiff_t(first),a.begin()+std::ptrdiff_t(last)),gb;
      if(context)gb.assign(b.begin()+std::ptrdiff_t(first),b.begin()+std::ptrdiff_t(last));
      unsigned g0=cu85::best_k(ga,context?19:13,context?24:14),g1=context?cu85::best_k(gb,11,12):255;cu88::PlainBits plain;
      for(size_t i=0;i<ga.size();++i) {plain.rice(ga[i],g0,context?24:14);if(context)plain.rice(gb[i],g1,12);}
      sg.push_back(uint8_t(g0));sg.push_back(uint8_t(g1));cu85::put32(sg,plain.size);sg.insert(sg.end(),plain.data.begin(),plain.data.end());
      p.metrics[3].plain_bits[context]+=plain.size;++p.metrics[3].group_headers[context];
    }
  }
  return p;
}
inline unsigned local_selector(const Prepared &p) {
  unsigned selector=0;for(unsigned context=0;context<4;++context) {unsigned method=0;for(unsigned i=1;i<4;++i)if(p.streams[i][context].size()<p.streams[method][context].size())method=i;selector|=method<<(2*context);}return selector;
}
inline Bytes assemble(const Prepared &p,unsigned selector) {
  need(selector<256,"EC93 selector");size_t total=0;for(unsigned i=0;i<4;++i)total+=p.streams[(selector>>(2*i))&3][i].size();
  bool raw=p.source_raw_fallback||total>=128*size_t(p.blocks);Bytes out{'E','C','9','3',1,uint8_t(raw),uint8_t(raw?0:selector),0};
  cu85::put32(out,p.blocks);cu85::put16(out,1);cu85::put16(out,0);
  for(unsigned i=0;i<4;++i)cu85::put32(out,raw?(i?0:128*p.blocks):uint32_t(p.streams[(selector>>(2*i))&3][i].size()));
  for(auto count:p.counts)cu85::put32(out,raw?0:count);
  if(raw)for(auto value:p.coefficients)cu85::put16(out,uint16_t(value));
  else for(unsigned i=0;i<4;++i) {const auto &stream=p.streams[(selector>>(2*i))&3][i];out.insert(out.end(),stream.begin(),stream.end());}
  cu85::put32(out,crc32(out));return out;
}
} // namespace cu93
