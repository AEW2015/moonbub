#pragma once
#include "bytes.hpp"
namespace cu66 {
struct Arithmetic {
  Bits bits;
  uint32_t lo = 0, hi = 65535, code = 0;
  std::array<unsigned, 88> p{};
  Arithmetic(View a, uint32_t n) : bits(a, n) {
    need(n >= 18, "arithmetic minimum");
    p.fill(128);
    for (int i = 0; i < 16; i++)
      code = code * 2 + bits.bit();
  }
  unsigned read(unsigned c) {
    need(c < p.size(), "arithmetic context");
    auto pr = p[c];
    uint32_t part = ((hi - lo + 1) * pr) / 256;
    part = std::max(1u, std::min(hi - lo, part));
    auto boundary = lo + part - 1;
    unsigned value = code > boundary;
    if (value) {
      lo = boundary + 1;
      p[c] = std::max(1u, pr - std::max(1u, pr / 32));
    } else {
      hi = boundary;
      p[c] = std::min(255u, pr + std::max(1u, (256 - pr) / 32));
    }
    for (;;) {
      uint32_t off;
      if (hi < 32768)
        off = 0;
      else if (lo >= 32768)
        off = 32768;
      else if (lo >= 16384 && hi < 49152)
        off = 16384;
      else
        break;
      lo = (lo - off) * 2;
      hi = (hi - off) * 2 + 1;
      code = (code - off) * 2 + bits.bit();
    }
    need(lo <= code && code <= hi, "arithmetic interval");
    return value;
  }
  uint32_t rice(unsigned k, unsigned escape, bool level = false) {
    unsigned base = level ? 48 : 0, q = 0;
    while (q < 15) {
      if (read(base + q))
        break;
      q++;
    }
    unsigned width = q == 15 ? escape : k;
    uint32_t v = 0;
    for (int i = int(width) - 1; i >= 0; i--)
      v = v * 2 + read(base + 16 + std::min(i, 23));
    return q == 15 ? v : (q << k) | v;
  }
  void end() {
    need(bits.n - bits.pos == 2 && !bits.bit() && !bits.bit(),
         "arithmetic termination");
  }
};
inline std::vector<int16_t> decode_ab38(View packet, unsigned blocks,
                                        unsigned bw) {
  need(blocks >= 1 && blocks <= 65536 && bw >= 1 && bw <= 256 &&
           blocks % bw == 0,
       "AB geometry");
  checked(packet, 46, 46 + 128 * blocks);
  Reader r(packet.sub(0, packet.n - 4));
  need(r.magic() == "AB38" && r.u8() == 1, "AB profile");
  unsigned flags = r.u8();
  need(flags <= 1 && r.u32() == blocks && r.u16() == bw && r.u16() == 0,
       "AB binding");
  std::array<uint32_t, 4> len;
  for (auto &x : len)
    x = r.u32();
  std::array<uint32_t, 3> counts;
  for (auto &x : counts)
    x = r.u32();
  size_t sum = 0;
  for (auto x : len)
    sum += x;
  need(r.pos + sum == packet.n - 4, "AB lengths");
  std::vector<int16_t> out(size_t(blocks) * 64, 0);
  if (flags) {
    need(len == std::array<uint32_t, 4>{128 * blocks, 0, 0, 0} &&
             counts == std::array<uint32_t, 3>{0, 0, 0},
         "AB raw fields");
    for (auto &x : out) {
      x = int16_t(signed16(r.u16()));
      need(x >= -2048 && x <= 2048, "AB raw range");
    }
    r.end();
    return out;
  }
  struct Stream {
    unsigned k0, k1;
    View data;
    uint32_t bits;
  };
  std::array<Stream, 4> ss;
  for (int i = 0; i < 4; i++) {
    need(len[i] >= 9, "AB stream bound");
    Reader q(r.take(len[i]));
    auto k0 = q.u8(), k1 = q.u8();
    auto n = q.u32();
    ss[i] = {k0, k1, q.take(q.v.n - q.pos), n};
  }
  r.end();
  need(ss[0].k0 <= 13 && ss[0].k1 == 255, "AB DC parameters");
  std::vector<int16_t> zig(out.size());
  Arithmetic dc(ss[0].data, ss[0].bits);
  int previous = 0;
  for (unsigned b = 0; b < blocks; b++) {
    if (b % bw == 0)
      previous = 0;
    previous += signed_zig(dc.rice(ss[0].k0, 14));
    need(previous >= -2048 && previous <= 2048, "AB DC range");
    zig[b * 64] = int16_t(previous);
  }
  dc.end();
  const unsigned limits[4] = {1, 6, 21, 64};
  for (int band = 0; band < 3; band++) {
    auto s = ss[band + 1];
    unsigned lo = limits[band], hi = limits[band + 1], width = hi - lo;
    need(s.k0 <= 19 && s.k1 <= 11 && counts[band] <= blocks * width,
         "AB AC parameters");
    Arithmetic ac(s.data, s.bits);
    int64_t index = -1;
    for (unsigned n = 0; n < counts[band]; n++) {
      index += ac.rice(s.k0, 24) + 1;
      need(index < int64_t(blocks * width), "AB run range");
      int value = signed_zig(ac.rice(s.k1, 12, true) + 1);
      need(value && value >= -2048 && value <= 2048, "AB level range");
      zig[(index / width) * 64 + lo + index % width] = int16_t(value);
    }
    ac.end();
  }
  std::array<unsigned, 64> order{};
  for (unsigned i = 0; i < 64; i++)
    order[i] = i;
  std::stable_sort(order.begin(), order.end(), [](unsigned a, unsigned b) {
    unsigned sa = a / 8 + a % 8, sb = b / 8 + b % 8;
    if (sa != sb)
      return sa < sb;
    return sa % 2 ? a / 8 < b / 8 : a / 8 > b / 8;
  });
  for (unsigned b = 0; b < blocks; b++)
    for (int i = 0; i < 64; i++)
      out[b * 64 + order[i]] = zig[b * 64 + i];
  return out;
}
} // namespace cu66
