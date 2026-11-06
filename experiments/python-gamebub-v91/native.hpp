#pragma once
#include "../python-gamebub-v88/entropy/codec.hpp"

namespace cu91 {
using namespace cu66;

// Host-native realization of the bounded reader. This is neither embedded
// firmware nor a hardware timing model. Byte assembly is endian-independent.
struct WordRice {
  View bytes;
  uint32_t size, pos = 0;
  size_t next = 0;
  uint64_t reservoir = 0;
  unsigned available = 0;
  WordRice(View input, uint32_t bits) : bytes(input), size(bits) {
    need((uint64_t(bits) + 7) / 8 == input.n, "word exact bits");
    if (bits % 8)
      need((input[input.n - 1] & ((1u << (8 - bits % 8)) - 1)) == 0,
           "word padding");
  }
  void ensure(unsigned n) {
    need(n <= 32 && n <= size - pos, "word truncated bits");
    while (available < n) {
      unsigned count = unsigned(std::min(size_t(4), bytes.n - next));
      need(count != 0, "word refill EOF");
      uint32_t value = 0;
      for (unsigned i = 0; i < count; ++i)
        value = (value << 8) | bytes[next++];
      unsigned bits = count * 8;
      if (next == bytes.n && size % 8) {
        unsigned padding = 8 - size % 8;
        bits -= padding;
        value >>= padding;
      }
      reservoir = (reservoir << bits) | value;
      available += bits;
      need(available <= 63, "word reservoir bound");
    }
  }
  uint32_t take(unsigned n) {
    if (!n) return 0;
    ensure(n);
    available -= n;
    uint32_t out = uint32_t(reservoir >> available);
    reservoir &= (uint64_t(1) << available) - 1;
    pos += n;
    return out;
  }
  uint32_t read(unsigned k, unsigned escape) {
    need(k <= 19 && escape <= 24, "word Rice widths");
    unsigned window = std::min(15u, size - pos);
    need(window != 0, "word empty symbol");
    ensure(window);
    uint32_t prefix = uint32_t(reservoir >> (available - window));
    unsigned q = prefix ? unsigned(__builtin_clz(prefix)) - (32 - window) : window;
    need(prefix || window == 15, "word truncated prefix");
    take(q == 15 ? 15 : q + 1);
    uint32_t suffix = take(q == 15 ? escape : k);
    return q == 15 ? suffix : (q << k) | suffix;
  }
  void end() const { need(pos == size, "word trailing bits"); }
};

inline std::vector<int16_t> decode(View packet, unsigned blocks) {
  need(blocks >= 1 && blocks <= 65536, "word geometry");
  checked(packet, 46, 46 + size_t(128) * blocks);
  Reader r(packet.sub(0, packet.n - 4));
  need(r.magic() == "BR88" && r.u8() == 1, "word profile");
  unsigned flags = r.u8();
  need(flags <= 1 && r.u32() == blocks && r.u16() == 1 && r.u16() == 0,
       "word binding");
  std::array<uint32_t, 4> lengths{};
  std::array<uint32_t, 3> counts{};
  for (auto &x : lengths) x = r.u32();
  for (auto &x : counts) x = r.u32();
  uint64_t total = 0;
  for (auto x : lengths) total += x;
  need(total == packet.n - 46, "word lengths");
  std::vector<int16_t> result(size_t(blocks) * 64, 0);
  if (flags) {
    need(lengths == std::array<uint32_t,4>{128*blocks,0,0,0} &&
         counts == std::array<uint32_t,3>{0,0,0}, "word raw fields");
    for (auto &v : result) {
      int x = signed16(r.u16());
      need(x >= -2048 && x <= 2048, "word raw range");
      v = int16_t(x);
    }
    r.end();
    return result;
  }
  struct Stream { unsigned k0, k1; uint32_t bits; View data; };
  std::array<Stream,4> ss;
  for (unsigned i=0;i<4;++i) {
    need(lengths[i]>=6,"word stream header");
    Reader s(r.take(lengths[i]));
    unsigned k0=s.u8(),k1=s.u8(); uint32_t bits=s.u32();
    ss[i]={k0,k1,bits,s.take(lengths[i]-6)};
    s.end();
  }
  r.end();
  need(ss[0].k0<=13 && ss[0].k1==255,"word DC parameters");
  WordRice dc(ss[0].data,ss[0].bits);
  for (unsigned b=0;b<blocks;++b) {
    int v=signed_zig(dc.read(ss[0].k0,14));
    need(v>=-2048 && v<=2048,"word DC range"); result[b*64]=int16_t(v);
  }
  dc.end();
  const unsigned limits[4]={1,6,21,64};
  for (unsigned band=0;band<3;++band) {
    const auto &s=ss[band+1]; unsigned width=limits[band+1]-limits[band];
    need(s.k0<=19 && s.k1<=11 && counts[band]<=blocks*width,"word AC parameters");
    WordRice input(s.data,s.bits); int64_t at=-1;
    for (unsigned event=0;event<counts[band];++event) {
      at+=input.read(s.k0,24)+1;
      need(at<int64_t(blocks*width),"word run range");
      int v=signed_zig(input.read(s.k1,12)+1);
      need(v && v>=-2048 && v<=2048,"word level range");
      result[size_t(at/width)*64+cu85::order()[limits[band]+at%width]]=int16_t(v);
    }
    input.end();
  }
  return result;
}
} // namespace cu91
