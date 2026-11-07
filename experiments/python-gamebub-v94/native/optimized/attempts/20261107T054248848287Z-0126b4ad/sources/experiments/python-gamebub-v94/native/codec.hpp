#pragma once
// Independent bounded byte-rANS research implementation; equations use L=2^23.
// No cache, trained model, or tANS implementation is claimed.
#include "../../python-gamebub-v92/native/codec.hpp"
namespace cu94 {
using namespace cu66;
constexpr uint32_t L=1u<<23;
struct DecodeStats {
  std::array<uint64_t,4> ab_decisions{},ab_renorm{},literal_bits{},ans_symbols{},ans_renorm_bytes{},model_tables{},model_entries{},ans_lanes{};
};
using Model=std::array<uint16_t,16>;
inline Model normalize(const std::array<uint64_t,16> &hist,unsigned scale) {
  need(scale>=8&&scale<=10,"EC94 scale");Model result{};uint64_t total=0;unsigned used=0;
  for(auto n:hist) {total+=n;used+=n!=0;}
  unsigned mass=1u<<scale;if(!total) {result.fill(uint16_t(mass/16));return result;}
  unsigned remain=mass-used,assigned=used;std::array<uint64_t,16> remainders{};
  for(unsigned i=0;i<16;++i)if(hist[i]) {uint64_t product=uint64_t(remain)*hist[i];result[i]=uint16_t(1+product/total);assigned+=unsigned(product/total);remainders[i]=product%total;}
  std::array<unsigned,16> order{};for(unsigned i=0;i<16;++i)order[i]=i;
  std::stable_sort(order.begin(),order.end(),[&](unsigned a,unsigned b){return remainders[a]>remainders[b];});
  for(unsigned i=0;i<mass-assigned;++i)++result[order[i]];
  return result;
}
inline View bit_bytes(Reader &r,uint32_t bits) {
  auto data=r.take(size_t((uint64_t(bits)+7)/8));if(bits%8)need((data[data.n-1]&((1u<<(8-bits%8))-1))==0,"EC94 literal padding");return data;
}
inline void parameters(unsigned context,unsigned k0,unsigned k1) {need(context?k0<=19&&k1<=11:k0<=13&&k1==255,"EC94 Rice parameters");}
template<class Emit> inline void read_stream(View bytes,unsigned method,unsigned context,unsigned events,Emit emit,DecodeStats *stats=nullptr) {
  need(method<4&&context<4,"EC94 context method");Reader r(bytes);unsigned k0=r.u8(),k1=r.u8();parameters(context,k0,k1);
  if(method<2) {
    uint32_t bits=r.u32();View data=bit_bytes(r,bits);r.end();
    if(method==0) {cu92::Arithmetic input(data,bits);for(unsigned i=0;i<events;++i) {auto a=input.rice(k0,context?24:14),b=context?input.rice(k1,12,true):0;emit(a,b);}input.end();if(stats) {stats->ab_decisions[context]=input.decisions;stats->ab_renorm[context]=input.renorm;}}
    else {cu88::RiceReader input(data,bits);for(unsigned i=0;i<events;++i) {auto a=input.read(k0,context?24:14),b=context?input.read(k1,12):0;emit(a,b);}input.end();if(stats)stats->literal_bits[context]=bits;}
    return;
  }
  unsigned scale=r.u8();need(scale>=8&&scale<=10&&r.u8()==0,"EC94 scale/table mode");uint32_t model_id=r.u32(),ans_bytes=r.u32(),literal_bits=r.u32(),symbols=r.u32();
  unsigned lanes=method==2?2:4,models=context?2:1;need(symbols==uint64_t(events)*(context?2:1),"EC94 symbol count");
  need(ans_bytes>=4*lanes&&uint64_t(ans_bytes)<=4*lanes+uint64_t(symbols)*2,"EC94 ANS byte bound");
  auto tables=r.take(models*32);need(crc32(tables)==model_id,"EC94 model id");Reader table_reader(tables);
  std::array<Model,2> freq{};std::array<std::array<unsigned,16>,2> cdf{};
  std::array<std::array<uint8_t,1024>,2> lookup{};unsigned mass=1u<<scale;
  for(unsigned m=0;m<models;++m) {unsigned sum=0;for(unsigned q=0;q<16;++q) {freq[m][q]=table_reader.u16();cdf[m][q]=sum;need(sum+freq[m][q]<=mass,"EC94 model sum");for(unsigned slot=sum;slot<sum+freq[m][q];++slot)lookup[m][slot]=uint8_t(q);sum+=freq[m][q];}need(sum==mass,"EC94 model sum");}
  Reader ans(r.take(ans_bytes));View literals=bit_bytes(r,literal_bits);r.end();Bits plain(literals,literal_bits);std::array<uint32_t,4> states{};
  for(unsigned lane=0;lane<lanes;++lane) {states[lane]=ans.u32();need(states[lane]>=L&&states[lane]<(1u<<31),"EC94 initial state");}
  uint64_t renorm=0;unsigned field=0;
  auto value=[&](unsigned k,unsigned escape,unsigned model) {
    auto &state=states[field++%lanes];unsigned slot=state&(mass-1),q=lookup[model][slot];unsigned frequency=freq[model][q];need(frequency!=0,"EC94 zero frequency");
    state=frequency*(state>>scale)+slot-cdf[model][q];unsigned count=0;while(state<L) {need(count<2,"EC94 renormalization bound");state=state*256+ans.u8();++count;++renorm;}
    unsigned width=q==15?escape:k;uint32_t result=0;for(unsigned i=0;i<width;++i)result=result*2+plain.bit();return q==15?result:(q<<k)|result;
  };
  for(unsigned i=0;i<events;++i) {auto a=value(k0,context?24:14,0),b=context?value(k1,12,1):0;emit(a,b);}
  ans.end();need(plain.pos==plain.n,"EC94 trailing literal bits");for(unsigned lane=0;lane<lanes;++lane)need(states[lane]==L,"EC94 terminal state");
  if(stats) {stats->literal_bits[context]=literal_bits;stats->ans_symbols[context]=symbols;stats->ans_renorm_bytes[context]=renorm;stats->model_tables[context]=models;stats->model_entries[context]=models*16;stats->ans_lanes[context]=lanes;}
}
inline std::vector<int16_t> decode_ec94(View packet,unsigned blocks,unsigned bw=1,DecodeStats *stats=nullptr) {
  need(blocks>=1&&blocks<=65536&&bw==1,"EC94 geometry");checked(packet,48,48+128*size_t(blocks));if(stats)*stats=DecodeStats{};
  Reader r(packet.sub(0,packet.n-4));need(r.magic()=="EC94"&&r.u8()==1,"EC94 profile");unsigned flags=r.u8(),selector=r.u8();need(flags<=1&&r.u8()==0,"EC94 flags/reserved");need(r.u32()==blocks&&r.u16()==1&&r.u16()==0,"EC94 binding");
  std::array<uint32_t,4> lengths{};std::array<uint32_t,3> counts{};for(auto &v:lengths)v=r.u32();for(auto &v:counts)v=r.u32();size_t total=0;for(auto v:lengths)total+=v;need(r.pos+total==packet.n-4,"EC94 lengths");std::vector<int16_t> values(size_t(blocks)*64);
  if(flags) {need(selector==0&&lengths==std::array<uint32_t,4>{128*blocks,0,0,0}&&counts==std::array<uint32_t,3>{0,0,0},"EC94 raw fields");for(auto &v:values) {v=int16_t(signed16(r.u16()));need(v>=-2048&&v<=2048,"EC94 raw range");}r.end();return values;}
  need(total<128*size_t(blocks),"EC94 coded bound");const unsigned limits[4]={1,6,21,64};
  for(unsigned context=0;context<4;++context) {unsigned width=context?limits[context]-limits[context-1]:1,events=context?counts[context-1]:blocks;need(events<=blocks*width,"EC94 event bound");int64_t at=-1;unsigned dc=0;
    read_stream(r.take(lengths[context]),(selector>>(2*context))&3,context,events,[&](uint32_t a,uint32_t b) {int v=signed_zig(context?b+1:a);need(v>=-2048&&v<=2048&&(!context||v),"EC94 coefficient range");if(!context)values[(dc++)*64]=int16_t(v);else {at+=int64_t(a)+1;need(at<int64_t(blocks*width),"EC94 AC position");values[(at/width)*64+cu85::order()[limits[context-1]+at%width]]=int16_t(v);}},stats);
  }r.end();return values;
}
inline std::vector<int16_t> decode(View packet,unsigned blocks,unsigned bw=1) {return decode_ec94(packet,blocks,bw);}
inline Bytes encode_stream(const std::vector<uint32_t> &a,const std::vector<uint32_t> &b,unsigned context,unsigned lanes,unsigned scale,DecodeStats &stats) {
  unsigned k0=cu85::best_k(a,context?19:13,context?24:14),k1=context?cu85::best_k(b,11,12):255,models=context?2:1;
  std::vector<unsigned> categories;categories.reserve(a.size()*models);cu88::PlainBits plain;std::array<std::array<uint64_t,16>,2> hist{};
  auto field=[&](uint32_t v,unsigned k,unsigned escape,unsigned model) {unsigned q=std::min(v>>k,15u);categories.push_back(q);++hist[model][q];unsigned width=q==15?escape:k;if(q<15)v&=(1u<<k)-1;for(int i=int(width)-1;i>=0;--i)plain.bit((v>>i)&1);};
  for(size_t i=0;i<a.size();++i) {field(a[i],k0,context?24:14,0);if(context)field(b[i],k1,12,1);}
  std::array<Model,2> freq{};std::array<std::array<unsigned,16>,2> cdf{};Bytes tables;
  for(unsigned m=0;m<models;++m) {freq[m]=normalize(hist[m],scale);unsigned sum=0;for(unsigned q=0;q<16;++q) {cdf[m][q]=sum;sum+=freq[m][q];cu85::put16(tables,freq[m][q]);}}
  std::array<uint32_t,4> states{};states.fill(L);Bytes emitted;
  for(size_t i=categories.size();i-->0;) {unsigned model=context?unsigned(i%2):0,q=categories[i],f=freq[model][q];auto &state=states[i%lanes];unsigned renorm=0;uint64_t threshold=uint64_t((L>>scale)<<8)*f;
    while(state>=threshold) {need(renorm<2,"EC94 encoder renormalization bound");emitted.push_back(uint8_t(state));state>>=8;++renorm;}
    state=((state/f)<<scale)+(state%f)+cdf[model][q];need(state>=L&&state<(1u<<31),"EC94 encoded state bound");
  }
  Bytes out{uint8_t(k0),uint8_t(k1),uint8_t(scale),0};cu85::put32(out,crc32(tables));cu85::put32(out,uint32_t(lanes*4+emitted.size()));cu85::put32(out,plain.size);cu85::put32(out,uint32_t(categories.size()));out.insert(out.end(),tables.begin(),tables.end());for(unsigned lane=0;lane<lanes;++lane)cu85::put32(out,states[lane]);out.insert(out.end(),emitted.rbegin(),emitted.rend());out.insert(out.end(),plain.data.begin(),plain.data.end());
  stats.literal_bits[context]=plain.size;stats.ans_symbols[context]=categories.size();stats.ans_renorm_bytes[context]=emitted.size();stats.model_tables[context]=models;stats.model_entries[context]=16*models;stats.ans_lanes[context]=lanes;return out;
}
struct Prepared {
  unsigned blocks=0;std::vector<int16_t> coefficients;cu85::Encoded ab;cu88::Encoded br;std::array<std::array<Bytes,4>,8> streams{};std::array<uint32_t,3> counts{};bool source_raw_fallback=false;std::array<DecodeStats,8> metrics{};
};
inline Prepared prepare(const std::vector<int16_t> &values) {
  Prepared p;p.coefficients=values;p.blocks=unsigned(values.size()/64);p.ab=cu85::encode(values);p.br=cu88::encode_br88(values);p.source_raw_fallback=p.ab.raw||p.br.raw;
  if(!p.source_raw_fallback) {p.streams[0]=cu92::split_streams(p.ab.packet,p.counts);std::array<uint32_t,3> counts{};p.streams[1]=cu92::split_streams(p.br.packet,counts);need(counts==p.counts,"EC94 frozen counts");}
  p.metrics[0].ab_decisions=p.ab.decisions;p.metrics[0].ab_renorm=p.ab.renorm;p.metrics[1].literal_bits=p.br.bits;const unsigned limits[4]={1,6,21,64};
  for(unsigned context=0;context<4;++context) {std::vector<uint32_t> a,b;if(!context) {for(unsigned block=0;block<p.blocks;++block)a.push_back(cu85::mapped(values[block*64]));}else {int64_t previous=-1;unsigned width=limits[context]-limits[context-1];for(unsigned block=0;block<p.blocks;++block)for(unsigned i=limits[context-1];i<limits[context];++i) {int v=values[block*64+cu85::order()[i]];if(v) {int64_t at=int64_t(block)*width+i-limits[context-1];a.push_back(uint32_t(at-previous-1));b.push_back(cu85::mapped(v)-1);previous=at;}}p.counts[context-1]=uint32_t(a.size());}
    for(unsigned method=2;method<8;++method)p.streams[method][context]=encode_stream(a,b,context,method<5?2:4,8+(method-2)%3,p.metrics[method]);
  }return p;
}
using Choices=std::array<unsigned,4>;
inline unsigned wire_method(unsigned alternative) {need(alternative<8,"EC94 alternative");return alternative<2?alternative:alternative<5?2:3;}
inline unsigned wire_selector(const Choices &choices) {unsigned result=0;for(unsigned c=0;c<4;++c)result|=wire_method(choices[c])<<(2*c);return result;}
inline Choices local_choices(const Prepared &p) {Choices result{};for(unsigned c=0;c<4;++c)for(unsigned m=1;m<8;++m)if(p.streams[m][c].size()<p.streams[result[c]][c].size())result[c]=m;return result;}
inline unsigned local_selector(const Prepared &p) {return wire_selector(local_choices(p));}
inline Bytes assemble(const Prepared &p,const Choices &choices) {
  unsigned selector=wire_selector(choices);size_t total=0;for(unsigned c=0;c<4;++c)total+=p.streams[choices[c]][c].size();bool raw=p.source_raw_fallback||total>=128*size_t(p.blocks);Bytes out{'E','C','9','4',1,uint8_t(raw),uint8_t(raw?0:selector),0};cu85::put32(out,p.blocks);cu85::put16(out,1);cu85::put16(out,0);for(unsigned c=0;c<4;++c)cu85::put32(out,raw?(c?0:128*p.blocks):uint32_t(p.streams[choices[c]][c].size()));for(auto count:p.counts)cu85::put32(out,raw?0:count);
  if(raw)for(auto value:p.coefficients)cu85::put16(out,uint16_t(value));else for(unsigned c=0;c<4;++c)out.insert(out.end(),p.streams[choices[c]][c].begin(),p.streams[choices[c]][c].end());cu85::put32(out,crc32(out));return out;
}
inline Bytes assemble(const Prepared &p,unsigned selector,unsigned scale=8) {need(selector<256&&scale>=8&&scale<=10,"EC94 selector/scale");Choices choices{};for(unsigned c=0;c<4;++c) {unsigned method=(selector>>(2*c))&3;choices[c]=method<2?method:(method==2?2:5)+scale-8;}return assemble(p,choices);}
} // namespace cu94
