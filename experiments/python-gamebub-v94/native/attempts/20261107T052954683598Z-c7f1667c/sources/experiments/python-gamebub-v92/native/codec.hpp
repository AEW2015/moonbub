#pragma once
// EC92 is a research wire profile. It preserves frozen AB38/BR88 event grammar,
// while selecting the coder independently for DC and three AC bands.
#include "../../python-gamebub-v88/entropy/codec.hpp"
#include <memory>
namespace cu92 {
using namespace cu66;
struct DecodeStats {
  std::array<uint64_t,4> ab_decisions{},ab_renorm{},br_bits{};
};
// Instrumented independent decoder, not the encoder's counters. Probability
// contexts and arithmetic state reset on construction for every entropy stream.
struct Arithmetic {
  Bits bits;uint32_t lo=0,hi=65535,code=0;
  std::array<unsigned,88> probabilities{};uint64_t decisions=0,renorm=0;
  Arithmetic(View bytes,uint32_t length):bits(bytes,length) {
    need(length>=18,"EC92 arithmetic minimum");probabilities.fill(128);
    for(unsigned i=0;i<16;++i)code=code*2+bits.bit();
  }
  unsigned bit(unsigned context) {
    need(context<88,"EC92 arithmetic context");unsigned probability=probabilities[context];
    uint32_t part=std::max(1u,std::min(hi-lo,((hi-lo+1)*probability)/256));
    uint32_t boundary=lo+part-1;unsigned value=code>boundary;
    if(value) {lo=boundary+1;probabilities[context]=std::max(1u,probability-std::max(1u,probability/32));}
    else {hi=boundary;probabilities[context]=std::min(255u,probability+std::max(1u,(256-probability)/32));}
    for(;;) {
      uint32_t offset;
      if(hi<32768)offset=0;else if(lo>=32768)offset=32768;
      else if(lo>=16384&&hi<49152)offset=16384;else break;
      lo=(lo-offset)*2;hi=(hi-offset)*2+1;code=(code-offset)*2+bits.bit();++renorm;
    }
    ++decisions;need(lo<=code&&code<=hi,"EC92 arithmetic interval");return value;
  }
  uint32_t rice(unsigned k,unsigned escape,bool level=false) {
    unsigned base=level?48:0,q=0;while(q<15&&!bit(base+q))++q;
    unsigned width=q==15?escape:k;uint32_t value=0;
    for(int i=int(width)-1;i>=0;--i)value=value*2+bit(base+16+std::min(i,23));
    return q==15?value:(q<<k)|value;
  }
  void end() {need(bits.n-bits.pos==2&&!bits.bit()&&!bits.bit(),"EC92 arithmetic termination");}
};
struct StreamReader {
  std::unique_ptr<Arithmetic> arithmetic;std::unique_ptr<cu88::RiceReader> plain;
  StreamReader(bool br,View bytes,uint32_t length) {
    if(br)plain=std::make_unique<cu88::RiceReader>(bytes,length);
    else arithmetic=std::make_unique<Arithmetic>(bytes,length);
  }
  uint32_t rice(unsigned k,unsigned escape,bool level=false) {
    return arithmetic?arithmetic->rice(k,escape,level):plain->read(k,escape);
  }
  void end(unsigned context,DecodeStats *stats) {
    if(arithmetic) {
      arithmetic->end();if(stats) {stats->ab_decisions[context]=arithmetic->decisions;stats->ab_renorm[context]=arithmetic->renorm;}
    } else {plain->end();if(stats)stats->br_bits[context]=plain->bits.pos;}
  }
};
inline std::vector<int16_t> decode_ec92(View packet,unsigned blocks,unsigned bw=1,DecodeStats *stats=nullptr) {
  need(blocks>=1&&blocks<=65536&&bw==1,"EC92 geometry");checked(packet,48,48+128*size_t(blocks));
  if(stats)*stats=DecodeStats{};
  Reader reader(packet.sub(0,packet.n-4));need(reader.magic()=="EC92"&&reader.u8()==1,"EC92 profile");
  unsigned flags=reader.u8(),mask=reader.u8();need(flags<=1&&mask<=15&&reader.u8()==0,"EC92 flags/mask/reserved");
  need(reader.u32()==blocks&&reader.u16()==1&&reader.u16()==0,"EC92 binding");
  std::array<uint32_t,4> lengths{};std::array<uint32_t,3> counts{};
  for(auto &length:lengths)length=reader.u32();
  for(auto &count:counts)count=reader.u32();
  size_t total=0;for(auto length:lengths)total+=length;need(reader.pos+total==packet.n-4,"EC92 lengths");
  std::vector<int16_t> values(size_t(blocks)*64,0);
  if(flags) {
    need(mask==0&&lengths==std::array<uint32_t,4>{128*blocks,0,0,0}&&counts==std::array<uint32_t,3>{0,0,0},"EC92 raw fields");
    for(auto &value:values) {value=int16_t(signed16(reader.u16()));need(value>=-2048&&value<=2048,"EC92 raw range");}
    reader.end();return values;
  }
  need(total<128*size_t(blocks),"EC92 coded/raw canonical bound");
  struct Stream {unsigned k0,k1;uint32_t bits;View data;};std::array<Stream,4> streams;
  for(unsigned i=0;i<4;++i) {
    need(lengths[i]>=((mask>>i)&1?6u:9u),"EC92 stream minimum");Reader stream(reader.take(lengths[i]));
    unsigned k0=stream.u8(),k1=stream.u8();uint32_t bits=stream.u32();
    need((uint64_t(bits)+7)/8==lengths[i]-6,"EC92 exact bit bytes");View data=stream.take(lengths[i]-6);stream.end();
    if(bits%8)need((data[data.n-1]&((1u<<(8-bits%8))-1))==0,"EC92 padding");
    streams[i]={k0,k1,bits,data};
  }
  reader.end();need(streams[0].k0<=13&&streams[0].k1==255,"EC92 DC parameters");
  StreamReader dc(mask&1,streams[0].data,streams[0].bits);
  for(unsigned block=0;block<blocks;++block) {
    int value=signed_zig(dc.rice(streams[0].k0,14));need(value>=-2048&&value<=2048,"EC92 DC range");values[block*64]=int16_t(value);
  }
  dc.end(0,stats);const unsigned limits[4]={1,6,21,64};
  for(unsigned band=0;band<3;++band) {
    const auto &stream=streams[band+1];unsigned width=limits[band+1]-limits[band];
    need(stream.k0<=19&&stream.k1<=11&&counts[band]<=blocks*width,"EC92 AC parameters");
    StreamReader ac((mask>>(band+1))&1,stream.data,stream.bits);int64_t at=-1;
    for(unsigned event=0;event<counts[band];++event) {
      at+=ac.rice(stream.k0,24)+1;need(at<int64_t(blocks*width),"EC92 AC position");
      int value=signed_zig(ac.rice(stream.k1,12,true)+1);need(value&&value>=-2048&&value<=2048,"EC92 AC range");
      values[(at/width)*64+cu85::order()[limits[band]+at%width]]=int16_t(value);
    }
    ac.end(band+1,stats);
  }
  return values;
}
inline std::vector<int16_t> decode(View packet,unsigned blocks,unsigned bw=1) {return decode_ec92(packet,blocks,bw);}
struct Prepared {
  unsigned blocks=0;std::vector<int16_t> coefficients;cu85::Encoded ab;cu88::Encoded br;
  std::array<Bytes,4> ab_streams,br_streams;std::array<uint32_t,3> counts{};bool source_raw_fallback=false;
};
inline std::array<Bytes,4> split_streams(View packet,std::array<uint32_t,3> &counts) {
  Reader reader(packet.sub(6,packet.n-10));reader.u32();reader.u16();reader.u16();
  std::array<uint32_t,4> lengths{};for(auto &length:lengths)length=reader.u32();for(auto &count:counts)count=reader.u32();
  std::array<Bytes,4> streams;for(unsigned i=0;i<4;++i) {View bytes=reader.take(lengths[i]);streams[i]=Bytes(bytes.p,bytes.p+bytes.n);}reader.end();return streams;
}
inline Prepared prepare(const std::vector<int16_t> &values) {
  Prepared prepared;prepared.coefficients=values;prepared.blocks=unsigned(values.size()/64);
  // Exactly one whole-plane encode of each frozen coder. If a frozen coder
  // replaces its streams by RAW, do not fabricate missing stream candidates.
  prepared.ab=cu85::encode(values);prepared.br=cu88::encode_br88(values);
  prepared.source_raw_fallback=prepared.ab.raw||prepared.br.raw;
  if(!prepared.source_raw_fallback) {
    prepared.ab_streams=split_streams(prepared.ab.packet,prepared.counts);std::array<uint32_t,3> br_counts{};
    prepared.br_streams=split_streams(prepared.br.packet,br_counts);need(prepared.counts==br_counts,"EC92 event counts agree");
  }
  return prepared;
}
inline Bytes assemble(const Prepared &prepared,unsigned mask) {
  need(mask<=15,"EC92 mask domain");size_t total=0;
  for(unsigned i=0;i<4;++i)total+=((mask>>i)&1?prepared.br_streams[i]:prepared.ab_streams[i]).size();
  bool raw=prepared.source_raw_fallback||total>=128*size_t(prepared.blocks);
  Bytes out{'E','C','9','2',1,uint8_t(raw),uint8_t(raw?0:mask),0};cu85::put32(out,prepared.blocks);cu85::put16(out,1);cu85::put16(out,0);
  for(unsigned i=0;i<4;++i)cu85::put32(out,raw?(i?0:128*prepared.blocks):uint32_t(((mask>>i)&1?prepared.br_streams[i]:prepared.ab_streams[i]).size()));
  for(auto count:prepared.counts)cu85::put32(out,raw?0:count);
  if(raw)for(auto value:prepared.coefficients)cu85::put16(out,uint16_t(value));
  else for(unsigned i=0;i<4;++i) {const auto &stream=(mask>>i)&1?prepared.br_streams[i]:prepared.ab_streams[i];out.insert(out.end(),stream.begin(),stream.end());}
  cu85::put32(out,crc32(out));return out;
}
} // namespace cu92
