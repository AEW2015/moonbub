#pragma once
#include "bounded.hpp"
#include "bytes.hpp"
#include "generated_constants.hpp"
#include <map>
#include <set>
void v58_component_begin(unsigned);
namespace cu66 {
struct Patch {
  std::array<uint16_t, 4> rect{};
  cu66_port::Vector<uint16_t> words;
};
inline Bytes word_bytes(const cu66_port::Vector<uint16_t> &v) {
  Bytes b;
  b.reserve(v.size() * 2);
  for (auto w : v)
    put16(b, uint16_t(w));
  return b;
}
inline void hash_u16(SHA256& h,uint16_t v){uint8_t b[2]={uint8_t(v),uint8_t(v>>8)};h.update(View(b,2));}
inline Tag finish_tag(SHA256& h){auto full=h.finish();Tag t;std::copy(full.begin(),full.begin()+16,t.begin());return t;}
inline Tag patch_tag(const cu66_port::Vector<uint16_t>&v,unsigned w,unsigned hh){
 SHA256 h;hash_u16(h,uint16_t(w));hash_u16(h,uint16_t(hh));for(auto a:v)hash_u16(h,a);return finish_tag(h);
}
inline Tag hud_tag(const cu66_port::Vector<Patch>&p){
 SHA256 h;hash_u16(h,720);hash_u16(h,480);uint8_t count=uint8_t(p.size());h.update(View(&count,1));
 for(const auto&v:p){for(auto x:v.rect)hash_u16(h,x);for(auto a:v.words)hash_u16(h,a);}return finish_tag(h);
}
// Fixed canonical tables and borrowed bitstream only: no count-sized scratch.
struct HuffmanSymbols {
  unsigned count=0,consumed=0,constant=0;bool singleton=false;
  std::array<uint16_t,17> counts{};std::array<uint32_t,17> first_code{};
  std::array<uint16_t,17> first_symbol{};std::array<uint8_t,256> symbols{};
  Bits bits{View{},0};
  void init(Reader&r,unsigned wanted,unsigned maximum){
    need(wanted&&wanted<=21120&&maximum<=255,"HUD symbol count");
    count=wanted;consumed=0;singleton=false;counts.fill(0);first_code.fill(0);first_symbol.fill(0);symbols.fill(0);
    unsigned ns=r.u16(),nb=r.u32();need(ns&&ns<=std::min(count,maximum+1)&&nb<=16*count,"HUD Huffman bounds");
    std::array<uint8_t,256> lengths{};int last=-1;
    for(unsigned i=0;i<ns;++i){unsigned value=r.u8(),length=r.u8();need(value<=maximum&&int(value)>last&&length>=1&&length<=16,"HUD Huffman table");last=value;lengths[value]=uint8_t(length);++counts[length];}
    bits=Bits(r.take((nb+7)/8),nb);
    if(ns==1){need(lengths[unsigned(last)]==1&&nb==0,"HUD constant syntax");singleton=true;constant=unsigned(last);return;}
    unsigned code=0,offset=0;
    for(unsigned n=1;n<=16;++n){code=(code+counts[n-1])<<1;first_code[n]=code;first_symbol[n]=uint16_t(offset);need(code+counts[n]<=(1u<<n),"HUD oversubscribed Huffman");for(unsigned v=0;v<=maximum;++v)if(lengths[v]==n)symbols[offset++]=uint8_t(v);}
    need(code+counts[16]==(1u<<16)&&nb>=count,"HUD Huffman complete");
  }
  uint8_t next(){
    need(consumed<count,"HUD symbol count");if(singleton){++consumed;return uint8_t(constant);}
    unsigned code=0;for(unsigned n=1;n<=16;++n){code=code*2+bits.bit();const unsigned first=first_code[n];if(code>=first&&code-first<counts[n]){++consumed;return symbols[first_symbol[n]+code-first];}}
    need(false,"HUD unknown Huffman code");return 0;
  }
  void end(){need(consumed==count,"HUD symbol coverage");bits.end();}
};
template<class Emit>inline void huffman_emit(Reader&r,unsigned count,unsigned maximum,Emit emit){HuffmanSymbols symbols;symbols.init(r,count,maximum);for(unsigned i=0;i<count;++i)emit(symbols.next());symbols.end();}
inline cu66_port::Vector<uint8_t> huffman(Reader&r,unsigned count,unsigned maximum){HuffmanSymbols symbols;symbols.init(r,count,maximum);cu66_port::Vector<uint8_t> out;out.reserve(count);for(unsigned i=0;i<count;++i)out.push_back(symbols.next());symbols.end();return out;}
inline uint32_t plain_rice(Bits &bits, unsigned k, unsigned remaining) {
  uint32_t q = 0;
  while (!bits.bit()) {
    q++;
    need(q <= (remaining >> k), "HUD Rice unary bound");
  }
  uint32_t v = (q << k) | bits.get(k);
  need(v <= remaining, "HUD Rice bound");
  return v;
}
template<class Emit>
inline void channel33_emit(Reader &r,unsigned count,unsigned maximum,Emit emit) {
  unsigned scheme=r.u8(),k=r.u8();
  uint32_t events=r.u32(),size=r.u32(),nb=r.u32();
  need(scheme<=2&&k<=14&&events<=count&&size<=6+506+2*count&&nb<=16*count+1,"HS33 channel bounds");
  HuffmanSymbols symbols;
  if(events){Reader h(r.take(size));symbols.init(h,events,maximum);h.end();}
  else need(scheme==1&&!size,"HS33 empty symbols");
  Bits bits(r.take((nb+7)/8),nb);unsigned produced=0;
  auto put=[&](unsigned v){need(produced<count,"HS33 expansion");emit(uint8_t(v));++produced;};
  if(scheme==0){need(!k&&!nb&&events==count,"HS33 plain syntax");for(unsigned i=0;i<events;++i)put(symbols.next());}
  else if(scheme==1){
    for(unsigned i=0;i<events;++i){auto v=symbols.next();need(v!=0,"HS33 nonzero symbol");auto gap=plain_rice(bits,k,count-produced);while(gap--)put(0);put(v);}
    auto gap=plain_rice(bits,k,count-produced);while(gap--)put(0);
  }else{
    need(events>0,"HS33 repeat events");int last=-1;
    for(unsigned i=0;i<events;++i){auto v=symbols.next();need(v!=last&&produced<count,"HS33 repeat order");last=v;auto n=plain_rice(bits,k,count-produced-1)+1;while(n--)put(v);}
  }
  need(produced==count,"HS33 exact expansion");if(events)symbols.end();bits.end();
}
inline cu66_port::Vector<uint8_t> channel33(Reader&r,unsigned count,unsigned maximum){
  cu66_port::Vector<uint8_t> out;out.reserve(count);
  channel33_emit(r,count,maximum,[&](uint8_t v){out.push_back(v);});return out;
}
inline void byte_planes_into(View data,unsigned n,cu66_port::Vector<uint16_t>&out,bool xor_values){
  Reader r(data);unsigned lo=r.u32(),hi=r.u32();need(size_t(lo)+hi+8==data.n,"HD25 planes lengths");
  out.resize(n);if(!xor_values)std::fill(out.begin(),out.end(),0);
  auto unpack=[&](View input,unsigned shift){
    need(input.n&&input.n<=n+(n+127)/128,"HD25 byte RLE bound");Reader a(input);unsigned pos=0;
    auto put=[&](uint8_t v){need(pos<n,"HD25 RLE overflow");const uint16_t value=uint16_t(uint16_t(v)<<shift);if(xor_values)out[pos]^=value;else out[pos]=uint16_t((out[pos]&~uint16_t(255u<<shift))|value);++pos;};
    while(a.pos<a.v.n){unsigned t=a.u8(),count;uint8_t value=0;
      if(t<128){count=t+1;auto raw=a.take(count);need(pos+count<=n,"HD25 literal overflow");for(unsigned i=0;i<count;++i)put(raw[i]);continue;}
      count=(t&63)+1;if(t>=192){value=a.u8();need(value!=0,"HD25 repeat zero");}need(pos+count<=n,"HD25 RLE overflow");while(count--)put(value);
    }need(pos==n,"HD25 RLE coverage");
  };
  unpack(r.take(lo),0);unpack(r.take(hi),8);r.end();
}
inline cu66_port::Vector<uint16_t> byte_planes(View data,unsigned n){cu66_port::Vector<uint16_t> out;byte_planes_into(data,n,out,false);return out;}
inline void span_words_into(View data,unsigned w,unsigned hh,cu66_port::Vector<uint16_t>&out,bool xor_values) {
  Reader r(data);
  unsigned count = r.u16();
  need(count <= w * hh && count <= (data.n - 2) / 8, "HD25 spans count");
  out.resize(w*hh);if(!xor_values)std::fill(out.begin(),out.end(),0);
  int last_y = -1, last_end = -1;
  for (unsigned i = 0; i < count; i++) {
    unsigned y = r.u16(), x = r.u16(), n = r.u16();
    need(y < hh && n && x + n <= w && int(y) >= last_y &&
             (int(y) != last_y || int(x) - last_end >= 3),
         "HD25 span order");
    cu66_port::Vector<uint16_t> v(n);
    for (auto &a : v)
      a = r.u16();
    need(v.front() && v.back(), "HD25 span endpoints");
    int last_nz = -1;
    for (unsigned j = 0; j < n; j++) {
      if (v[j]) {
        need(last_nz < 0 || int(j) - last_nz < 4, "HD25 span zero gap");
        last_nz = j;
      }
      if(xor_values)out[y*w+x+j]^=v[j];else out[y*w+x+j]=v[j];
    }
    last_y = y;
    last_end = x + n;
  }
  r.end();
}
inline cu66_port::Vector<uint16_t> span_words(View data,unsigned w,unsigned hh){cu66_port::Vector<uint16_t> out;span_words_into(data,w,hh,out,false);return out;}
inline void rice_components_into(View data,unsigned w,unsigned hh,const cu66_port::Vector<uint16_t>*prediction,bool left,cu66_port::Vector<uint16_t>&out) {
  Reader r(data);
  unsigned ks[3];
  for (auto &k : ks) {
    k = r.u8();
    need(k <= 5, "HD25 component Rice k");
  }
  uint32_t counts[3];
  for (auto &n : counts) {
    n = r.u32();
    need(n >= w * hh && n <= 127 * w * hh, "HD25 component Rice count");
  }
  out.resize(w*hh);
  for (int c = 0; c < 3; c++) {
    unsigned maximum = c == 1 ? 63 : 31, shift = c == 0 ? 11 : c == 1 ? 5 : 0;
    Bits bits(r.take((counts[c] + 7) / 8), counts[c]);
    for (unsigned y = 0; y < hh; y++) {
      int cumulative = 0;
      for (unsigned x = 0; x < w; x++) {
        int delta = signed_zig(plain_rice(bits, ks[c], 2 * maximum));
        int result;
        if (left) {
          cumulative += delta;
          result = cumulative;
        } else {
          need(prediction, "HD25 component prediction");
          result = int((*prediction)[y * w + x] >> shift & maximum) + delta;
        }
        need(result >= 0 && result <= int(maximum), "HD25 component range");
        out[y * w + x] = uint16_t((out[y * w + x] & ~(uint32_t(maximum) << shift)) | (uint32_t(result) << shift));
      }
    }
    bits.end();
  }
  r.end();
}
inline cu66_port::Vector<uint16_t> rice_components(View data,unsigned w,unsigned hh,const cu66_port::Vector<uint16_t>*prediction,bool left){cu66_port::Vector<uint16_t> out;rice_components_into(data,w,hh,prediction,left,out);return out;}
inline size_t motion_prediction_into(const cu66_port::Vector<uint16_t>&ref,unsigned mode,View data,unsigned w,unsigned hh,cu66_port::Vector<uint16_t>&pred) {
  pred.resize(w*hh);
  if(mode==1){pred.assign(ref.begin(),ref.end());return 0;}
  Reader r(data);
  cu66_port::Vector<std::pair<int, int>> vectors;
  if (mode == 2) {
    int dx = signed8(r.u8()), dy = signed8(r.u8());
    need(std::abs(dx) <= 4 && std::abs(dy) <= 4, "HUD global motion");
    vectors.push_back({dx, dy});
  } else {
    need(mode == 3, "HUD motion mode");
    unsigned tw = r.u8(), th = r.u8(), radius = r.u8(), field = r.u8(),
             n = r.u16();
    unsigned count = ((w + 15) / 16) * ((hh + 7) / 8), size = r.u32();
    need(tw == 16 && th == 8 && radius == 4 && field <= 1 && n == count &&
             size && size <= 4 * count,
         "HUD tiled motion header");
    Reader q(r.take(size));
    if (field == 0) {
      need(size == 2 * count, "HUD raw motion bytes");
      for (unsigned i = 0; i < count; i++)
        vectors.push_back({signed8(q.u8()), signed8(q.u8())});
    } else {
      need(size % 4 == 0, "HUD motion run bytes");
      while (q.pos < q.v.n) {
        unsigned n = q.u16();
        int dx = signed8(q.u8()), dy = signed8(q.u8());
        need(n && vectors.size() + n <= count &&
                 (vectors.empty() || vectors.back() != std::make_pair(dx, dy)),
             "HUD motion runs");
        vectors.insert(vectors.end(), n, {dx, dy});
      }
    }
    q.end();
    need(vectors.size() == count, "HUD motion coverage");
    for (auto v : vectors)
      need(std::abs(v.first) <= 4 && std::abs(v.second) <= 4,
           "HUD tiled vector bound");
  }
  for (unsigned y = 0; y < hh; y++)
    for (unsigned x = 0; x < w; x++) {
      auto v = vectors[mode == 2 ? 0 : (y / 8) * ((w + 15) / 16) + x / 16];
      pred[y * w + x] = ref[clamp(int(y) + v.second, 0, hh - 1) * w +
                            clamp(int(x) + v.first, 0, w - 1)];
    }
  return r.pos;
}
inline std::pair<cu66_port::Vector<uint16_t>,size_t> motion_prediction(const cu66_port::Vector<uint16_t>&ref,unsigned mode,View data,unsigned w,unsigned hh){cu66_port::Vector<uint16_t> out;auto pos=motion_prediction_into(ref,mode,data,w,hh,out);return {std::move(out),pos};}
inline cu66_port::Vector<uint16_t>
decode_full_patch_into(View packet,const std::array<uint16_t,4>&rect,cu66_port::Vector<uint16_t> out) {
  checked(packet, 30, 50000);
  Reader r(packet.sub(0, packet.n - 4));
  auto magic = r.magic();
  unsigned version = r.u8(), mode = r.u8();
  std::array<uint16_t, 4> actual;
  for (auto &x : actual)
    x = r.u16();
  unsigned colors = r.u16(), pixels = r.u32(), length = r.u32();
  unsigned w = rect[2], hh = rect[3];
  need((magic == "HP01" || magic == "HR01") && actual == rect && version == 1 &&
           pixels == w * hh && colors <= std::min(256u, pixels) &&
           r.pos + 2 * colors + length == r.v.n,
       "full HUD geometry");
  cu66_port::Vector<uint16_t> palette(colors);
  for (auto &x : palette)
    x = r.u16();
  for (unsigned i = 1; i < colors; i++)
    need(palette[i] > palette[i - 1], "HUD palette order");
  auto data = r.take(length);
  r.end();
  out.clear();
  cu66_port::Set<unsigned> used;
  if (mode == 0) {
    need(!colors && length == 2 * pixels, "HUD full raw");
    out.reserve(pixels);
    Reader a(data);
    for (unsigned i = 0; i < pixels; i++)
      out.push_back(a.u16());
    return out;
  }
  if (magic == "HP01") {
    unsigned expected = colors <= 2    ? 1
                        : colors <= 4  ? 2
                        : colors <= 16 ? 4
                                       : 8;
    need(colors && mode == expected, "HP01 palette mode");
    Bits bits(data, pixels * mode);
    out.reserve(pixels);
    for (unsigned i = 0; i < pixels; i++) {
      auto idx = bits.get(mode);
      need(idx < colors, "HP01 index");
      used.insert(idx);
      out.push_back(palette[idx]);
    }
    bits.end();
  } else {
    need(magic == "HR01" && (mode == 1 || mode == 2) &&
             length <= hh * (2 + 3 * w),
         "HR01 mode/bounds");
    need(mode == 2 ? colors > 0 : colors == 0, "HR01 palette presence");
    out.reserve(pixels);
    Reader a(data);
    for (unsigned y = 0; y < hh; y++) {
      unsigned n = a.u16();
      need(n && n <= 3 * w, "HR01 row bytes");
      Reader row(a.take(n));
      unsigned count = 0;
      while (row.pos < row.v.n) {
        unsigned t = row.u8(), run = (t & 127) + 1;
        need(count + run <= w, "HR01 row overflow");
        if (t & 128) {
          unsigned val = mode == 2 ? row.u8() : row.u16();
          for (unsigned i = 0; i < run; i++) {
            if (mode == 2) {
              need(val < colors, "HR01 index");
              used.insert(val);
              out.push_back(palette[val]);
            } else
              out.push_back(uint16_t(val));
          }
        } else
          for (unsigned i = 0; i < run; i++) {
            unsigned val = mode == 2 ? row.u8() : row.u16();
            if (mode == 2) {
              need(val < colors, "HR01 literal index");
              used.insert(val);
              out.push_back(palette[val]);
            } else
              out.push_back(uint16_t(val));
          }
        count += run;
      }
      need(count == w, "HR01 row coverage");
    }
    a.end();
  }
  if (colors)
    need(used.size() == colors, "HUD unused palette");
  return out;
}
inline cu66_port::Vector<uint16_t> decode_full_patch(View packet,const std::array<uint16_t,4>&rect){return decode_full_patch_into(packet,rect,cu66_port::Vector<uint16_t>{});}
inline cu66_port::Vector<uint16_t> decode_patch_into(View packet,const Patch*reference,unsigned expected_w,unsigned expected_h,cu66_port::Vector<uint16_t> out) {
  checked(packet, 50, 42290);
  Reader r(packet.sub(0, packet.n - 4));
  auto magic = r.magic();
  unsigned version = r.u8(), mode = r.u8(), w = r.u16(), hh = r.u16(),
           size = r.u32();
  Tag rt = r.tag(), ot = r.tag();
  need(version == 1 && w == expected_w && hh == expected_h && w && hh &&
           w * hh <= 21120 && size == r.v.n - r.pos,
       "HUD patch header");
  auto data = r.take(size);
  r.end();
  bool hs = magic == "HS32" || magic == "HS33";
  bool independent =
      hs ? (mode & 7) == 0 : (mode == 0 || mode == 6 || mode == 7 || mode == 9);
  if (independent)
    need(zero(rt), "HUD independent tag");
  else
    need(reference && reference->words.size() == w * hh &&
             patch_tag(reference->words, w, hh) == rt,
         "HUD patch reference");
  out.clear();
  if (hs) {
    need(mode == 0 || mode == 1 || mode == 2 || mode == 3 || mode == 9 ||
             mode == 10 || mode == 11,
         "HS mode");
    unsigned plain = mode & 7;
    bool owned_prediction = false;
    // Plain co-located prediction is immutable accepted state; avoid a copy.
    const cu66_port::Vector<uint16_t>* prediction = nullptr;
    size_t pos = 0;
    if (plain == 1) {
      prediction = &reference->words;
    } else if (plain) {
      pos=motion_prediction_into(reference->words,plain,data,w,hh,out);
      prediction=&out;owned_prediction=true;
    }
    Reader a(data.sub(pos, data.n - pos));
    if (!owned_prediction) out.assign(w * hh, 0);
    for (int c = 0; c < 3; c++) {
      unsigned maximum = c == 1 ? 63 : 31, shift = c == 0 ? 11 : c == 1 ? 5 : 0;
      unsigned position=0;int rowdelta=0,resultsum=0;
      auto emit=[&](uint8_t symbol){
        need(position<w*hh,"HS expansion");const unsigned x=position%w;if(!x){rowdelta=0;resultsum=0;}
        int delta=signed_zig(symbol);if(mode&8){rowdelta+=delta;delta=rowdelta;}
        int result;if(!plain){resultsum+=delta;result=resultsum;}else result=int(((*prediction)[position]>>shift)&maximum)+delta;
        need(result>=0&&result<=int(maximum),"HS reconstructed range");out[position]=uint16_t((out[position]&~(uint32_t(maximum)<<shift))|(uint32_t(result)<<shift));++position;
      };
      if(magic=="HS33")channel33_emit(a,w*hh,(mode&8)?4*maximum:2*maximum,emit);
      else huffman_emit(a,w*hh,(mode&8)?4*maximum:2*maximum,emit);
      need(position==w*hh,"HS exact channel pixels");
    }
    a.end();
  } else {
    need(magic == "HD25" && mode <= 9, "HD25 profile");
    const auto *base = reference ? &reference->words : nullptr;
    switch (mode) {
    case 0: {
      need(data.n == 2 * w * hh, "HD25 raw size");
      out.reserve(w * hh);
      Reader a(data);
      for (unsigned i = 0; i < w * hh; i++)
        out.push_back(a.u16());
      break;
    }
    case 1:
      need(!data.n, "HD25 copy bytes");
      out = *base;
      break;
    case 2:
      out.assign(base->begin(),base->end());span_words_into(data,w,hh,out,true);
      break;
    case 3:
      out.assign(base->begin(),base->end());byte_planes_into(data,w*hh,out,true);
      break;
    case 6:
    case 7:
      byte_planes_into(data,w*hh,out,false);
      if (mode == 7)
        for (unsigned y = 0; y < hh; y++)
          for (unsigned x = 1; x < w; x++)
            out[y * w + x] ^= out[y * w + x - 1];
      break;
    case 8:
    case 9:
      rice_components_into(data,w,hh,base,mode==9,out);
      break;
    case 4:
    case 5: {
      auto consumed=motion_prediction_into(*base,mode==4?2:3,data,w,hh,out);
      auto residual=data.sub(consumed,data.n-consumed);need(residual.n>0,"HD25 missing residual");
      unsigned grammar=residual[0];auto body=residual.sub(1,residual.n-1);
      if(grammar==0)span_words_into(body,w,hh,out,true);
      else if(grammar==1)byte_planes_into(body,w*hh,out,true);
      // The old grammar2 XORed prediction twice. In-place component decoding
      // produces that same absolute result; each channel reads its old bits
      // before replacing only that channel. Accepted storage is never written.
      else if(grammar==2)rice_components_into(body,w,hh,&out,false,out);
      else need(false,"HD25 residual grammar");
      break;
    }
    }
  }
  need(out.size() == w * hh && patch_tag(out, w, hh) == ot,
       "HUD patch output tag");
  return out;
}
inline cu66_port::Vector<uint16_t> decode_patch(View packet,const Patch*reference,unsigned w,unsigned hh){return decode_patch_into(packet,reference,w,hh,cu66_port::Vector<uint16_t>{});}
inline cu66_port::Vector<Patch> decode_hud(View packet,
                                     const cu66_port::Vector<Patch> *reference,
                                     uint32_t fid, uint32_t rid) {
  checked(packet, 110, 49152);
  Reader r(packet.sub(0, packet.n - 4));
  auto magic = r.magic();
  need(magic == "HU25" || magic == "HX32" || magic == "HX33",
       "HUD envelope profile");
  unsigned ver = r.u8(), count = r.u8();
  need(ver == 1 && count == 4 && r.u32() == 25 && r.u32() == fid &&
           r.u32() == rid && r.u16() == 720 && r.u16() == 480,
       "HUD envelope identity");
  Tag rt = r.tag(), ot = r.tag();
  need(!zero(ot), "HUD output identity");
  if (rid == 0xffffffffu)
    need(zero(rt), "HUD independent reference");
  else
    need(reference && hud_tag(*reference) == rt, "HUD envelope prior tag");
  std::array<uint32_t, 4> length;
  for (auto &x : length)
    x = r.u32();
  std::array<uint8_t, 4> kind;
  for (auto &x : kind)
    x = r.u8();
  std::array<std::array<uint16_t, 4>, 4> rects;
  for (unsigned i = 0; i < 4; i++)
    for (unsigned j = 0; j < 4; j++) {
      rects[i][j] = r.u16();
      need(rects[i][j] == RECTS[i][j], "fixed HUD rectangles");
    }
  size_t total = 0;
  for (unsigned i = 0; i < 4; i++) {
    need(length[i] && length[i] <= 49152 && kind[i] >= 1 &&
             kind[i] <= (magic == "HU25"   ? 2
                         : magic == "HX32" ? 3
                                           : 4),
         "HUD patch kind/length");
    total += length[i];
  }
  need(r.pos + total == r.v.n, "HUD exact component lengths");
  // Validate component boundaries before changing candidate allocation order.
  // Predictions always borrow the accepted patch at the canonical index.
  std::array<View, 4> components;
  for (unsigned i = 0; i < 4; i++) {
    components[i] = r.take(length[i]);
  }
  r.end();
  cu66_port::Vector<Patch> out;
  out.resize(4);
  // Allocate the largest fixed output patches before small decode temporaries
  // fragment suitable blocks. Final order, reference indices and tags stay fixed.
  constexpr std::array<unsigned, 4> order{{2, 3, 0, 1}};
  // Private candidate output storage is planned before component temporaries.
  for(unsigned i:order){out[i].rect=rects[i];out[i].words.reserve(size_t(rects[i][2])*rects[i][3]);}
  for (unsigned i : order) {
    ::v58_component_begin(i);
    auto data = components[i];
    Patch p;
    p.rect = rects[i];
    if (kind[i] == 1)
      p.words = decode_full_patch_into(data,p.rect,std::move(out[i].words));
    else {
      need(data.n >= 4, "patch magic");
      Reader q(data);
      auto pm = q.magic();
      need((kind[i] == 2 && pm == "HD25") || (kind[i] == 3 && pm == "HS32") ||
               (kind[i] == 4 && pm == "HS33"),
           "HUD type/body binding");
      p.words = decode_patch_into(data,reference?&(*reference)[i]:nullptr,p.rect[2],p.rect[3],std::move(out[i].words));
    }
    out[i] = std::move(p);
  }
  need(hud_tag(out) == ot, "HUD reconstructed envelope tag");
  return out;
}
} // namespace cu66
