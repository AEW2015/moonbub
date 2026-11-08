#pragma once
#include "bounded.hpp"
#include "bytes.hpp"
#include "generated_constants.hpp"
#include <map>
#include <set>
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
inline cu66_port::Vector<uint8_t> huffman(Reader &r, unsigned count, unsigned maximum) {
  need(count && count <= 21120 && maximum <= 255, "HUD symbol count");
  unsigned ns = r.u16(), nb = r.u32();
  need(ns && ns <= std::min(count, maximum + 1) && nb <= 16 * count,
       "HUD Huffman bounds");
  // Bounded canonical tables: 648 bytes at most, no heap/map nodes.
  std::array<uint8_t,256> lengths{};
  std::array<uint16_t,17> counts{};
  int last = -1;
  for (unsigned i = 0; i < ns; i++) {
    unsigned s = r.u8(), n = r.u8();
    need(s <= maximum && int(s) > last && n >= 1 && n <= 16,
         "HUD Huffman table");
    last = s;lengths[s]=uint8_t(n);++counts[n];
  }
  auto raw = r.take((nb + 7) / 8);
  Bits bits(raw, nb);
  if (ns == 1) {
    need(lengths[unsigned(last)] == 1 && nb == 0, "HUD constant syntax");
    return cu66_port::Vector<uint8_t>(count, uint8_t(last));
  }
  std::array<uint32_t,17> first_code{};
  std::array<uint16_t,17> first_symbol{};
  std::array<uint8_t,256> symbols{};
  unsigned code=0,offset=0;
  for(unsigned n=1;n<=16;++n){
    code=(code+counts[n-1])<<1;first_code[n]=code;first_symbol[n]=uint16_t(offset);
    need(code+counts[n] <= (1u<<n), "HUD oversubscribed Huffman");
    for(unsigned s=0;s<=maximum;++s)if(lengths[s]==n)symbols[offset++]=uint8_t(s);
  }
  need(code+counts[16] == (1u<<16) && nb >= count, "HUD Huffman complete");
  cu66_port::Vector<uint8_t> out;
  out.reserve(count);
  for (unsigned i = 0; i < count; i++) {
    unsigned c = 0;
    bool found = false;
    for (unsigned n = 1; n <= 16; n++) {
      c = c * 2 + bits.bit();
      const unsigned first=first_code[n];
      if(c>=first && c-first<counts[n]){
        out.push_back(symbols[first_symbol[n]+c-first]);
        found=true;break;
      }
    }
    need(found, "HUD unknown Huffman code");
  }
  bits.end();
  return out;
}
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
inline cu66_port::Vector<uint8_t> channel33(Reader &r, unsigned count, unsigned maximum) {
  unsigned scheme = r.u8(), k = r.u8();
  uint32_t events = r.u32(), size = r.u32(), nb = r.u32();
  need(scheme <= 2 && k <= 14 && events <= count &&
           size <= 6 + 506 + 2 * count && nb <= 16 * count + 1,
       "HS33 channel bounds");
  cu66_port::Vector<uint8_t> symbols;
  if (events) {
    Reader h(r.take(size));
    symbols = huffman(h, events, maximum);
    h.end();
  } else
    need(scheme == 1 && !size, "HS33 empty symbols");
  Bits bits(r.take((nb + 7) / 8), nb);
  if (scheme == 0) {
    need(!k && !nb && events == count, "HS33 plain syntax");
    return symbols;
  }
  cu66_port::Vector<uint8_t> out;
  out.reserve(count);
  if (scheme == 1) {
    for (int s : symbols) {
      need(s != 0, "HS33 nonzero symbol");
      auto gap = plain_rice(bits, k, count - unsigned(out.size()));
      out.insert(out.end(), gap, 0);
      need(out.size() < count, "HS33 expansion");
      out.push_back(s);
    }
    auto gap = plain_rice(bits, k, count - unsigned(out.size()));
    out.insert(out.end(), gap, 0);
  } else {
    need(events > 0, "HS33 repeat events");
    int last = -1;
    for (int s : symbols) {
      need(s != last && out.size() < count, "HS33 repeat order");
      last = s;
      auto n = plain_rice(bits, k, count - unsigned(out.size()) - 1) + 1;
      out.insert(out.end(), n, s);
    }
  }
  need(out.size() == count, "HS33 exact expansion");
  bits.end();
  return out;
}
inline cu66_port::Vector<uint16_t> byte_planes(View data, unsigned n) {
  Reader r(data);
  unsigned lo = r.u32(), hi = r.u32();
  need(size_t(lo) + hi + 8 == data.n, "HD25 planes lengths");
  auto unpack = [n](View input) {
    need(input.n && input.n <= n + (n + 127) / 128, "HD25 byte RLE bound");
    Reader a(input);
    Bytes out;
    out.reserve(n);
    while (a.pos < a.v.n) {
      unsigned t = a.u8(), count;
      uint8_t value = 0;
      if (t < 128) {
        count = t + 1;
        auto raw = a.take(count);
        need(out.size() + count <= n, "HD25 literal overflow");
        out.insert(out.end(), raw.p, raw.p + count);
        continue;
      }
      count = (t & 63) + 1;
      if (t >= 192) {
        value = a.u8();
        need(value != 0, "HD25 repeat zero");
      }
      need(out.size() + count <= n, "HD25 RLE overflow");
      out.insert(out.end(), count, value);
    }
    need(out.size() == n, "HD25 RLE coverage");
    return out;
  };
  auto a = unpack(r.take(lo)), b = unpack(r.take(hi));
  r.end();
  cu66_port::Vector<uint16_t> out(n);
  for (unsigned i = 0; i < n; i++)
    out[i] = uint16_t(a[i] | (uint32_t(b[i]) << 8));
  return out;
}
inline cu66_port::Vector<uint16_t> span_words(View data, unsigned w, unsigned hh) {
  Reader r(data);
  unsigned count = r.u16();
  need(count <= w * hh && count <= (data.n - 2) / 8, "HD25 spans count");
  cu66_port::Vector<uint16_t> out(w * hh);
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
      out[y * w + x + j] = v[j];
    }
    last_y = y;
    last_end = x + n;
  }
  r.end();
  return out;
}
inline cu66_port::Vector<uint16_t>
rice_components(View data, unsigned w, unsigned hh,
                const cu66_port::Vector<uint16_t> *prediction, bool left) {
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
  cu66_port::Vector<uint16_t> out(w * hh);
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
  return out;
}
inline std::pair<cu66_port::Vector<uint16_t>, size_t>
motion_prediction(const cu66_port::Vector<uint16_t> &ref, unsigned mode, View data,
                  unsigned w, unsigned hh) {
  cu66_port::Vector<uint16_t> pred(w * hh);
  if (mode == 1)
    return {ref, 0};
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
  return {pred, r.pos};
}
inline cu66_port::Vector<uint16_t>
decode_full_patch(View packet, const std::array<uint16_t, 4> &rect) {
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
  cu66_port::Vector<uint16_t> out;
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
inline cu66_port::Vector<uint16_t> decode_patch(View packet, const Patch *reference,
                                          unsigned expected_w,
                                          unsigned expected_h) {
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
  cu66_port::Vector<uint16_t> out;
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
      auto q = motion_prediction(reference->words, plain, data, w, hh);
      out = std::move(q.first);
      prediction = &out;
      owned_prediction = true;
      pos = q.second;
    }
    Reader a(data.sub(pos, data.n - pos));
    if (!owned_prediction) out.assign(w * hh, 0);
    for (int c = 0; c < 3; c++) {
      unsigned maximum = c == 1 ? 63 : 31, shift = c == 0 ? 11 : c == 1 ? 5 : 0;
      auto mapped =
          magic == "HS33"
              ? channel33(a, w * hh, (mode & 8) ? 4 * maximum : 2 * maximum)
              : huffman(a, w * hh, (mode & 8) ? 4 * maximum : 2 * maximum);
      for (unsigned y = 0; y < hh; y++) {
        int rowdelta = 0, resultsum = 0;
        for (unsigned x = 0; x < w; x++) {
          int delta = signed_zig(mapped[y * w + x]);
          if (mode & 8) {
            rowdelta += delta;
            delta = rowdelta;
          }
          int result;
          if (!plain) {
            resultsum += delta;
            result = resultsum;
          } else
            result = int(((*prediction)[y * w + x] >> shift) & maximum) + delta;
          need(result >= 0 && result <= int(maximum), "HS reconstructed range");
          out[y * w + x] =
              uint16_t((out[y * w + x] & ~(uint32_t(maximum) << shift)) | (uint32_t(result) << shift));
        }
      }
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
      out = span_words(data, w, hh);
      for (unsigned i = 0; i < out.size(); i++)
        out[i] ^= (*base)[i];
      break;
    case 3:
      out = byte_planes(data, w * hh);
      for (unsigned i = 0; i < out.size(); i++)
        out[i] ^= (*base)[i];
      break;
    case 6:
    case 7:
      out = byte_planes(data, w * hh);
      if (mode == 7)
        for (unsigned y = 0; y < hh; y++)
          for (unsigned x = 1; x < w; x++)
            out[y * w + x] ^= out[y * w + x - 1];
      break;
    case 8:
    case 9:
      out = rice_components(data, w, hh, base, mode == 9);
      break;
    case 4:
    case 5: {
      auto q = motion_prediction(*base, mode == 4 ? 2 : 3, data, w, hh);
      auto residual = data.sub(q.second, data.n - q.second);
      need(residual.n > 0, "HD25 missing residual");
      unsigned grammar = residual[0];
      auto body = residual.sub(1, residual.n - 1);
      if (grammar == 0)
        out = span_words(body, w, hh);
      else if (grammar == 1)
        out = byte_planes(body, w * hh);
      else if (grammar == 2) {
        out = rice_components(body, w, hh, &q.first, false);
        for (unsigned i = 0; i < out.size(); i++)
          out[i] ^= q.first[i];
      } else
        need(false, "HD25 residual grammar");
      for (unsigned i = 0; i < out.size(); i++)
        out[i] ^= q.first[i];
      break;
    }
    }
  }
  need(out.size() == w * hh && patch_tag(out, w, hh) == ot,
       "HUD patch output tag");
  return out;
}
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
  for (unsigned i : order) {
    auto data = components[i];
    Patch p;
    p.rect = rects[i];
    if (kind[i] == 1)
      p.words = decode_full_patch(data, p.rect);
    else {
      need(data.n >= 4, "patch magic");
      Reader q(data);
      auto pm = q.magic();
      need((kind[i] == 2 && pm == "HD25") || (kind[i] == 3 && pm == "HS32") ||
               (kind[i] == 4 && pm == "HS33"),
           "HUD type/body binding");
      p.words = decode_patch(data, reference ? &(*reference)[i] : nullptr,
                             p.rect[2], p.rect[3]);
    }
    out[i] = std::move(p);
  }
  need(hud_tag(out) == ot, "HUD reconstructed envelope tag");
  return out;
}
} // namespace cu66
