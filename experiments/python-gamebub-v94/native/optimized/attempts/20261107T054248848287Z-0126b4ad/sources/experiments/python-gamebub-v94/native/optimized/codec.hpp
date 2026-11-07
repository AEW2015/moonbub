#pragma once
// Rate-score Rice parameter search; the wire profile remains frozen EC94.
#include "../codec.hpp"
#include <chrono>
#include <cmath>
namespace cu94opt {
using namespace cu94;
using Clock=std::chrono::steady_clock;
inline uint64_t nanoseconds(Clock::time_point start) {return uint64_t(std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now()-start).count());}
struct Search {unsigned k=0,tried=0;double score=0;};
inline Search search(const std::vector<uint32_t> &values,unsigned maximum,unsigned escape) {
  Search result;result.score=std::numeric_limits<double>::infinity();
  for(unsigned k=0;k<=maximum;++k) {
    std::array<uint64_t,16> hist{};uint64_t literal_bits=0;
    for(uint32_t value:values) {unsigned q=std::min(value>>k,15u);++hist[q];literal_bits+=q==15?escape:k;}
    auto frequency=normalize(hist,10);double score=double(literal_bits);
    for(unsigned q=0;q<16;++q)if(hist[q])score+=double(hist[q])*std::log2(1024.0/frequency[q]);
    if(score<result.score) {result.k=k;result.score=score;}
    ++result.tried;
  }return result;
}
// Adapted from this repository's frozen native/codec.hpp encode_stream, with
// explicit Rice parameters; state equations, table normalization and grammar
// are identical. No external implementation source was copied.
inline Bytes encode_explicit(const std::vector<uint32_t> &a,const std::vector<uint32_t> &b,unsigned context,unsigned k0,unsigned k1,DecodeStats &stats) {
  cu94::parameters(context,k0,k1);constexpr unsigned lanes=2,scale=10;unsigned models=context?2:1;
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
  cu94::Prepared base;
  std::array<std::array<Search,2>,4> searches{};
  std::array<bool,4> anchor_used{};
  std::array<unsigned,4> anchor_k0{},anchor_k1{},rate_k0{},rate_k1{};
  std::array<size_t,4> proposed_bytes{};
  uint64_t search_ns=0;
};
inline Prepared prepare(const std::vector<int16_t> &values) {
  Prepared result;auto &p=result.base;p.coefficients=values;p.blocks=unsigned(values.size()/64);
  p.ab=cu85::encode(values);p.br=cu88::encode_br88(values);p.source_raw_fallback=p.ab.raw||p.br.raw;
  if(!p.source_raw_fallback) {p.streams[0]=cu92::split_streams(p.ab.packet,p.counts);std::array<uint32_t,3> counts{};p.streams[1]=cu92::split_streams(p.br.packet,counts);need(counts==p.counts,"EC94opt frozen counts");}
  p.metrics[0].ab_decisions=p.ab.decisions;p.metrics[0].ab_renorm=p.ab.renorm;p.metrics[1].literal_bits=p.br.bits;
  const unsigned limits[4]={1,6,21,64};
  for(unsigned context=0;context<4;++context) {
    std::vector<uint32_t> a,b;
    if(!context) {for(unsigned block=0;block<p.blocks;++block)a.push_back(cu85::mapped(values[block*64]));}
    else {int64_t previous=-1;unsigned width=limits[context]-limits[context-1];for(unsigned block=0;block<p.blocks;++block)for(unsigned i=limits[context-1];i<limits[context];++i) {int value=values[block*64+cu85::order()[i]];if(value) {int64_t at=int64_t(block)*width+i-limits[context-1];a.push_back(uint32_t(at-previous-1));b.push_back(cu85::mapped(value)-1);previous=at;}}p.counts[context-1]=uint32_t(a.size());}
    // Base slot 4 is the frozen N2S10 anchor. Slot 2 is rate search guarded
    // by actual byte length, so cu94 assembly sees both as two-lane rANS.
    p.streams[4][context]=cu94::encode_stream(a,b,context,2,10,p.metrics[4]);
    result.anchor_k0[context]=p.streams[4][context][0];result.anchor_k1[context]=p.streams[4][context][1];
    auto started=Clock::now();auto &searches=result.searches[context];searches[0]=search(a,context?19:13,context?24:14);if(context)searches[1]=search(b,11,12);else searches[1].k=255;result.search_ns+=nanoseconds(started);
    auto proposed=encode_explicit(a,b,context,searches[0].k,searches[1].k,p.metrics[2]);result.proposed_bytes[context]=proposed.size();
    result.anchor_used[context]=p.streams[4][context].size()<=proposed.size();
    if(result.anchor_used[context]) {p.streams[2][context]=p.streams[4][context];p.metrics[2].ab_decisions[context]=p.metrics[4].ab_decisions[context];p.metrics[2].ab_renorm[context]=p.metrics[4].ab_renorm[context];p.metrics[2].literal_bits[context]=p.metrics[4].literal_bits[context];p.metrics[2].ans_symbols[context]=p.metrics[4].ans_symbols[context];p.metrics[2].ans_renorm_bytes[context]=p.metrics[4].ans_renorm_bytes[context];p.metrics[2].model_tables[context]=p.metrics[4].model_tables[context];p.metrics[2].model_entries[context]=p.metrics[4].model_entries[context];p.metrics[2].ans_lanes[context]=p.metrics[4].ans_lanes[context];}
    else p.streams[2][context]=std::move(proposed);
    result.rate_k0[context]=p.streams[2][context][0];result.rate_k1[context]=p.streams[2][context][1];
    need(p.streams[2][context].size()<=p.streams[4][context].size(),"EC94opt anchor bound");
  }return result;
}
inline Choices local_choices(const Prepared &p) {Choices choices{};for(unsigned c=0;c<4;++c)for(unsigned m=1;m<=2;++m)if(p.base.streams[m][c].size()<p.base.streams[choices[c]][c].size())choices[c]=m;return choices;}
inline std::array<Choices,3> candidates(const Prepared &p) {std::array<Choices,3> result{};result[0].fill(4);result[1].fill(2);result[2]=local_choices(p);return result;}
inline unsigned report_method(unsigned slot) {return slot==4?2:slot==2?3:slot;}
} // namespace cu94opt
