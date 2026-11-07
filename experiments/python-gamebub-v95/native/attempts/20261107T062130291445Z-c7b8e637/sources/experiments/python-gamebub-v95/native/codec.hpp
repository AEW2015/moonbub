#pragma once
// Exact canonical PIXEL records. Integrity belongs to outer CS95 and semantic root.
#include "../../python-gamebub-v92/native/codec.hpp"
#include <limits>
namespace cu95 {
using namespace cu66;
constexpr size_t MAX_RECORD=138;
inline unsigned width(unsigned n) {unsigned w=0;while((1u<<w)<n)++w;return w;}
struct Writer {Bytes data;unsigned bits=0;void put(unsigned value,unsigned n) {for(unsigned i=n;i;--i) {if(bits%8==0)data.push_back(0);data.back()|=((value>>(i-1))&1)<<(7-bits%8);++bits;}}};
struct BitReader {View data;size_t pos=0;unsigned get(unsigned n) {unsigned v=0;while(n--) {need(pos<data.n*8,"palette truncated bits");v=v*2+((data[pos/8]>>(7-pos%8))&1);++pos;}return v;}void end() {need((pos+7)/8==data.n,"palette trailing body");while(pos<data.n*8)need(get(1)==0,"palette padding");}};
struct Decoded {Bytes pixels,palette;};
inline void palette_ok(const Bytes &p) {need(!p.empty()&&p.size()<=8,"palette count");for(size_t i=1;i<p.size();++i)need(p[i-1]<p[i],"palette ascending unique");}
inline Decoded decode_record(View record,const Bytes &previous={}) {
  need(record.n>=2&&record.n<=MAX_RECORD,"palette record size");Reader r(record);unsigned kind=r.u8(),arg=r.u8();Bytes palette;
  if(kind==3) {need(arg==0&&record.n==66,"palette RAW fields");auto body=r.take(64);return {Bytes(body.p,body.p+64),{}};}
  if(kind==4) {need(arg<=2&&r.u8()==0,"palette reuse fields");palette=previous;palette_ok(palette);kind=arg;}
  else {need(kind<=2&&arg>=1&&arg<=8,"palette kind/count");auto p=r.take(arg);palette=Bytes(p.p,p.p+p.n);palette_ok(palette);}
  Bytes out;unsigned w=width(unsigned(palette.size()));
  auto emit=[&](unsigned i) {need(i<palette.size(),"palette index range");out.push_back(palette[i]);};
  if(kind==0) {BitReader bits{r.take(record.n-r.pos)};while(out.size()<64)emit(bits.get(w));bits.end();}
  else if(kind==2) {BitReader bits{r.take(record.n-r.pos)};w=width(unsigned(palette.size()+1));while(out.size()<64) {unsigned i=bits.get(w);need(i<=palette.size(),"palette escape code");if(i==palette.size())out.push_back(uint8_t(bits.get(8)));else emit(i);}bits.end();}
  else {while(out.size()<64) {unsigned token=r.u8(),op=token>>6,n=(token&63)+1;need(n<=64-out.size(),"palette run overflow");if(op==0) {need(out.size()>=8,"palette TOP origin");while(n--)out.push_back(out[out.size()-8]);}else if(op==1) {need(out.size()%8&&n<=8-out.size()%8,"palette LEFT row");while(n--)out.push_back(out.back());}else if(op==2) {BitReader bits{r.take((n*w+7)/8)};while(n--)emit(bits.get(w));bits.end();}else need(false,"palette reserved token");}}
  r.end();need(out.size()==64,"palette coverage");return {out,palette};
}
inline Bytes packed_body(const Bytes &pixels,const Bytes &palette,bool escape) {
  Writer out;unsigned w=width(unsigned(palette.size()+(escape?1:0)));
  for(auto value:pixels) {auto it=std::lower_bound(palette.begin(),palette.end(),value);unsigned i=unsigned(it-palette.begin());if(it==palette.end()||*it!=value) {if(!escape)return {};out.put(unsigned(palette.size()),w);out.put(value,8);}else out.put(i,w);}return out.data;
}
inline bool contains(const Bytes &pixels,const Bytes &palette) {for(auto value:pixels)if(!std::binary_search(palette.begin(),palette.end(),value))return false;return true;}
inline Bytes predict_body(const Bytes &p,const Bytes &palette) {
  unsigned w=width(unsigned(palette.size()));std::array<unsigned,65> cost{};std::array<unsigned,64> ops{},lens{};
  for(int pos=63;pos>=0;--pos) {unsigned best=10000,opbest=0,lenbest=0;for(unsigned op=0;op<3;++op)for(unsigned n=1;n<=64-unsigned(pos);++n) {
    bool legal=true;if(op==0)legal=pos>=8&&p[pos+n-1]==p[pos+n-1-8];else if(op==1)legal=pos%8&&n<=8-unsigned(pos)%8&&p[pos+n-1]==p[pos-1];
    if(!legal)break;
    unsigned c=1+(op==2?(n*w+7)/8:0)+cost[pos+n];if(c<best) {best=c;opbest=op;lenbest=n;}
  }cost[pos]=best;ops[pos]=opbest;lens[pos]=lenbest;}
  Bytes body;for(unsigned pos=0;pos<64;) {unsigned n=lens[pos],op=ops[pos];body.push_back(uint8_t(op*64+n-1));if(op==2) {Writer b;for(unsigned j=0;j<n;++j)b.put(unsigned(std::lower_bound(palette.begin(),palette.end(),p[pos+j])-palette.begin()),w);body.insert(body.end(),b.data.begin(),b.data.end());}pos+=n;}return body;
}
struct Choice {Bytes record,next;};
inline Choice choose(const Bytes &pixels,unsigned cap,bool escapes,const Bytes &previous) {
  need(pixels.size()==64&&(cap==2||cap==4||cap==8),"palette encode arguments");Choice best{{3,0},{}};best.record.insert(best.record.end(),pixels.begin(),pixels.end());
  std::array<unsigned,256> histogram{};for(auto v:pixels)++histogram[v];Bytes exact;for(unsigned v=0;v<256;++v)if(histogram[v])exact.push_back(uint8_t(v));
  auto candidate=[&](unsigned kind,const Bytes &palette,bool reuse) {Bytes body=kind==1?predict_body(pixels,palette):packed_body(pixels,palette,kind==2);Bytes record;if(reuse)record={4,uint8_t(kind),0};else {record={uint8_t(kind),uint8_t(palette.size())};record.insert(record.end(),palette.begin(),palette.end());}record.insert(record.end(),body.begin(),body.end());if(record.size()<best.record.size())best={record,palette};};
  if(exact.size()<=cap) {candidate(0,exact,false);candidate(1,exact,false);}
  if(escapes) {std::vector<unsigned> ranked;for(unsigned v=0;v<256;++v)if(histogram[v])ranked.push_back(v);std::sort(ranked.begin(),ranked.end(),[&](unsigned a,unsigned b){return histogram[a]!=histogram[b]?histogram[a]>histogram[b]:a<b;});Bytes p;for(unsigned i=0;i<std::min(cap,unsigned(ranked.size()));++i)p.push_back(uint8_t(ranked[i]));std::sort(p.begin(),p.end());candidate(2,p,false);}
  if(!previous.empty()) {if(contains(pixels,previous)) {candidate(0,previous,true);candidate(1,previous,true);}if(escapes)candidate(2,previous,true);}
  return best;
}
inline void be16(Bytes &b,unsigned n) {b.push_back(uint8_t(n>>8));b.push_back(uint8_t(n));}
inline void be32(Bytes &b,unsigned n) {be16(b,n>>16);be16(b,n);}
inline unsigned get16(Reader &r) {unsigned a=r.u8();return a*256+r.u8();}
inline unsigned get32(Reader &r) {unsigned a=get16(r);return a*65536+get16(r);}
struct PlaneDecoded {std::vector<unsigned> positions;std::vector<Bytes> records,pixels;std::vector<int16_t> coefficients;cu92::DecodeStats stats;};
inline PlaneDecoded decode_plane(View packet,const std::vector<unsigned> &active,unsigned plane_tiles) {
  need(packet.n>=12&&packet.n<=12+active.size()*146+48,"palette plane bound");Reader r(packet);unsigned n=get32(r);need(n<=active.size(),"palette count active");PlaneDecoded out;Bytes previous;
  for(unsigned i=0;i<n;++i) {unsigned pos=get16(r),length=get16(r);need(pos<plane_tiles&&std::binary_search(active.begin(),active.end(),pos)&&(!i||out.positions.back()<pos),"palette position/order");auto record=r.take(length);auto decoded=decode_record(record,previous);previous=decoded.palette;out.positions.push_back(pos);out.records.emplace_back(record.p,record.p+record.n);out.pixels.push_back(decoded.pixels);}
  unsigned blocks=get32(r),length=get32(r);need(blocks==active.size()-n,"palette residual count");auto entropy=r.take(length);r.end();if(blocks)out.coefficients=cu92::decode_ec92(entropy,blocks,1,&out.stats);else need(length==0,"palette empty entropy");return out;
}
} // namespace cu95
