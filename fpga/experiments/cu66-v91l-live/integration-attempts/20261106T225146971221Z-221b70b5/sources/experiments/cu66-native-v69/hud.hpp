#pragma once
#include "bytes.hpp"
#include "generated_constants.hpp"
#include <map>
#include <set>
namespace cu66 {
struct Patch {
  std::array<uint16_t, 4> rect{};
  std::vector<uint16_t> words;
};
inline Bytes word_bytes(const std::vector<uint16_t> &v) {
  Bytes b;
  b.reserve(v.size() * 2);
  for (auto w : v)
    put16(b, uint16_t(w));
  return b;
}
inline Tag patch_tag(const std::vector<uint16_t> &v, unsigned w, unsigned hh) {
  Bytes b;
  put16(b, uint16_t(w));
  put16(b, uint16_t(hh));
  auto raw = word_bytes(v);
  b.insert(b.end(), raw.begin(), raw.end());
  return tag(b);
}
inline Tag hud_tag(const std::vector<Patch> &p) {
  Bytes b;
  put16(b, 720);
  put16(b, 480);
  b.push_back(uint8_t(p.size()));
  for (auto &v : p) {
    for (auto x : v.rect)
      put16(b, x);
    auto raw = word_bytes(v.words);
    b.insert(b.end(), raw.begin(), raw.end());
  }
  return tag(b);
}
inline std::vector<int> huffman(Reader &r, unsigned count, unsigned maximum) {
  need(count && count <= 21120, "HUD symbol count");
  unsigned ns = r.u16(), nb = r.u32();
  need(ns && ns <= std::min(count, maximum + 1) && nb <= 16 * count,
       "HUD Huffman bounds");
  std::vector<std::pair<unsigned, unsigned>> pairs;
  int last = -1;
  for (unsigned i = 0; i < ns; i++) {
    unsigned s = r.u8(), n = r.u8();
    need(s <= maximum && int(s) > last && n >= 1 && n <= 16,
         "HUD Huffman table");
    last = s;
    pairs.push_back({n, s});
  }
  auto raw = r.take((nb + 7) / 8);
  Bits bits(raw, nb);
  if (ns == 1) {
    need(pairs[0].first == 1 && nb == 0, "HUD constant syntax");
    return std::vector<int>(count, pairs[0].second);
  }
  std::sort(pairs.begin(), pairs.end());
  std::map<std::pair<unsigned, unsigned>, unsigned> table;
  unsigned code = 0, prior = 0;
  for (auto pair : pairs) {
    unsigned n = pair.first, s = pair.second;
    code <<= n - prior;
    need(code < (1u << n), "HUD oversubscribed Huffman");
    table[{n, code}] = s;
    code++;
    prior = n;
  }
  need(code == (1u << prior) && nb >= count, "HUD Huffman complete");
  std::vector<int> out;
  out.reserve(count);
  for (unsigned i = 0; i < count; i++) {
    unsigned c = 0;
    bool found = false;
    for (unsigned n = 1; n <= 16; n++) {
      c = c * 2 + bits.bit();
      auto it = table.find({n, c});
      if (it != table.end()) {
        out.push_back(it->second);
        found = true;
        break;
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
inline std::vector<int> channel33(Reader &r, unsigned count, unsigned maximum) {
  unsigned scheme = r.u8(), k = r.u8();
  uint32_t events = r.u32(), size = r.u32(), nb = r.u32();
  need(scheme <= 2 && k <= 14 && events <= count &&
           size <= 6 + 506 + 2 * count && nb <= 16 * count + 1,
       "HS33 channel bounds");
  std::vector<int> symbols;
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
  std::vector<int> out;
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
inline std::vector<uint16_t> byte_planes(View data, unsigned n) {
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
  std::vector<uint16_t> out(n);
  for (unsigned i = 0; i < n; i++)
    out[i] = uint16_t(a[i] | (uint32_t(b[i]) << 8));
  return out;
}
inline std::vector<uint16_t> span_words(View data, unsigned w, unsigned hh) {
  Reader r(data);
  unsigned count = r.u16();
  need(count <= w * hh && count <= (data.n - 2) / 8, "HD25 spans count");
  std::vector<uint16_t> out(w * hh);
  int last_y = -1, last_end = -1;
  for (unsigned i = 0; i < count; i++) {
    unsigned y = r.u16(), x = r.u16(), n = r.u16();
    need(y < hh && n && x + n <= w && int(y) >= last_y &&
             (int(y) != last_y || int(x) - last_end >= 3),
         "HD25 span order");
    std::vector<uint16_t> v(n);
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
inline std::vector<uint16_t>
rice_components(View data, unsigned w, unsigned hh,
                const std::vector<uint16_t> *prediction, bool left) {
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
  std::vector<uint16_t> out(w * hh);
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
        out[y * w + x] = uint16_t(out[y * w + x] | (uint32_t(result) << shift));
      }
    }
    bits.end();
  }
  r.end();
  return out;
}
inline std::pair<std::vector<uint16_t>, size_t>
motion_prediction(const std::vector<uint16_t> &ref, unsigned mode, View data,
                  unsigned w, unsigned hh) {
  std::vector<uint16_t> pred(w * hh);
  if (mode == 1)
    return {ref, 0};
  Reader r(data);
  std::vector<std::pair<int, int>> vectors;
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
inline std::vector<uint16_t>
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
  std::vector<uint16_t> palette(colors);
  for (auto &x : palette)
    x = r.u16();
  for (unsigned i = 1; i < colors; i++)
    need(palette[i] > palette[i - 1], "HUD palette order");
  auto data = r.take(length);
  r.end();
  std::vector<uint16_t> out;
  std::set<unsigned> used;
  if (mode == 0) {
    need(!colors && length == 2 * pixels, "HUD full raw");
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
inline std::vector<uint16_t> decode_patch(View packet, const Patch *reference,
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
  std::vector<uint16_t> out;
  if (hs) {
    need(mode == 0 || mode == 1 || mode == 2 || mode == 3 || mode == 9 ||
             mode == 10 || mode == 11,
         "HS mode");
    unsigned plain = mode & 7;
    std::vector<uint16_t> pred;
    size_t pos = 0;
    if (plain) {
      auto q = motion_prediction(reference->words, plain, data, w, hh);
      pred = std::move(q.first);
      pos = q.second;
    }
    Reader a(data.sub(pos, data.n - pos));
    out.assign(w * hh, 0);
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
            result = int((pred[y * w + x] >> shift) & maximum) + delta;
          need(result >= 0 && result <= int(maximum), "HS reconstructed range");
          out[y * w + x] =
              uint16_t(out[y * w + x] | (uint32_t(result) << shift));
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
inline std::vector<Patch> decode_hud(View packet,
                                     const std::vector<Patch> *reference,
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
  std::vector<Patch> out;
  for (unsigned i = 0; i < 4; i++) {
    auto data = r.take(length[i]);
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
    out.push_back(std::move(p));
  }
  r.end();
  need(hud_tag(out) == ot, "HUD reconstructed envelope tag");
  return out;
}
} // namespace cu66
