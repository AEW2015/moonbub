#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstring>
#include <stdexcept>
#include <string>
#include <vector>
namespace cu66 {
using Bytes = std::vector<uint8_t>;
using Tag = std::array<uint8_t, 16>;
inline void need(bool v, const char *what) {
  if (!v)
    throw std::runtime_error(what);
}
struct View {
  const uint8_t *p = nullptr;
  size_t n = 0;
  View() = default;
  View(const uint8_t *p, size_t n) : p(p), n(n) {}
  View(const Bytes &b) : p(b.data()), n(b.size()) {}
  uint8_t operator[](size_t i) const {
    need(i < n, "truncated input");
    return p[i];
  }
  View sub(size_t i, size_t k) const {
    need(i <= n && k <= n - i, "bounded slice");
    return {p + i, k};
  }
};
struct Reader {
  View v;
  size_t pos = 0;
  explicit Reader(View v) : v(v) {}
  uint8_t u8() { return v[pos++]; }
  uint16_t u16() {
    uint16_t a = u8();
    return uint16_t(a | (uint32_t(u8()) << 8));
  }
  uint32_t u32() {
    uint32_t a = u16();
    return a | uint32_t(u16()) << 16;
  }
  View take(size_t n) {
    auto x = v.sub(pos, n);
    pos += n;
    return x;
  }
  Tag tag() {
    auto a = take(16);
    Tag t;
    std::copy(a.p, a.p + 16, t.begin());
    return t;
  }
  std::string magic() {
    auto a = take(4);
    return {reinterpret_cast<const char *>(a.p), 4};
  }
  void end() const { need(pos == v.n, "trailing bytes"); }
};
inline uint32_t crc32(View a) {
  static const auto table = []() {
    std::array<uint32_t, 256> t{};
    for (unsigned i = 0; i < 256; i++) {
      uint32_t c = i;
      for (int j = 0; j < 8; j++)
        c = (c >> 1) ^ (0xedb88320u & uint32_t(-int(c & 1)));
      t[i] = c;
    }
    return t;
  }();
  uint32_t c = ~0u;
  for (size_t i = 0; i < a.n; i++)
    c = table[(c ^ a.p[i]) & 255] ^ (c >> 8);
  return ~c;
}
inline void checked(View a, size_t lo, size_t hi) {
  need(a.n >= lo && a.n <= hi, "bounded packet");
  Reader r(a.sub(a.n - 4, 4));
  need(crc32(a.sub(0, a.n - 4)) == r.u32(), "CRC mismatch");
}
inline uint32_t rotr(uint32_t x, unsigned n) {
  return (x >> n) | (x << (32 - n));
}
class SHA256 {
  std::array<uint32_t, 8> s{0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
                            0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19};
  std::array<uint8_t, 64> b{};
  size_t used = 0;
  uint64_t total = 0;
  void block() {
    static constexpr uint32_t K[64] = {
        0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1,
        0x923f82a4, 0xab1c5ed5, 0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
        0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786,
        0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
        0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147,
        0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
        0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85, 0xa2bfe8a1, 0xa81a664b,
        0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
        0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a,
        0x5b9cca4f, 0x682e6ff3, 0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
        0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2};
    uint32_t w[64];
    for (int i = 0; i < 16; i++)
      w[i] = uint32_t(b[4 * i]) << 24 | uint32_t(b[4 * i + 1]) << 16 |
             uint32_t(b[4 * i + 2]) << 8 | b[4 * i + 3];
    for (int i = 16; i < 64; i++) {
      auto x = w[i - 15], y = w[i - 2];
      w[i] = w[i - 16] + (rotr(x, 7) ^ rotr(x, 18) ^ (x >> 3)) + w[i - 7] +
             (rotr(y, 17) ^ rotr(y, 19) ^ (y >> 10));
    }
    auto a = s[0], c = s[2], d = s[3], e = s[4], f = s[5], g = s[6], hh = s[7],
         bb = s[1];
    for (int i = 0; i < 64; i++) {
      auto t1 = hh + (rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25)) +
                ((e & f) ^ (~e & g)) + K[i] + w[i];
      auto t2 = (rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22)) +
                ((a & bb) ^ (a & c) ^ (bb & c));
      hh = g;
      g = f;
      f = e;
      e = d + t1;
      d = c;
      c = bb;
      bb = a;
      a = t1 + t2;
    }
    uint32_t t[] = {a, bb, c, d, e, f, g, hh};
    for (int i = 0; i < 8; i++)
      s[i] += t[i];
  }

public:
  void update(View x) {
    total += x.n;
    for (size_t i = 0; i < x.n; i++) {
      b[used++] = x.p[i];
      if (used == 64) {
        block();
        used = 0;
      }
    }
  }
  std::array<uint8_t, 32> finish() {
    uint64_t bits = total * 8;
    b[used++] = 128;
    if (used > 56) {
      std::fill(b.begin() + used, b.end(), 0);
      block();
      used = 0;
    }
    std::fill(b.begin() + used, b.begin() + 56, 0);
    for (int i = 0; i < 8; i++)
      b[63 - i] = uint8_t(bits >> (8 * i));
    block();
    std::array<uint8_t, 32> out{};
    for (int i = 0; i < 8; i++)
      for (int j = 0; j < 4; j++)
        out[4 * i + j] = uint8_t(s[i] >> (24 - 8 * j));
    return out;
  }
};
inline std::array<uint8_t, 32> sha256(View v) {
  SHA256 h;
  h.update(v);
  return h.finish();
}
inline Tag tag(View v) {
  auto full = sha256(v);
  Tag t;
  std::copy(full.begin(), full.begin() + 16, t.begin());
  return t;
}
template <class C> std::string hex(const C &c) {
  static const char *d = "0123456789abcdef";
  std::string s;
  for (auto b : c) {
    s += d[uint8_t(b) >> 4];
    s += d[uint8_t(b) & 15];
  }
  return s;
}
inline bool zero(Tag t) {
  return std::all_of(t.begin(), t.end(), [](uint8_t b) { return b == 0; });
}
inline void put16(Bytes &b, uint16_t v) {
  b.push_back(uint8_t(v));
  b.push_back(uint8_t(v >> 8));
}
inline void put32(Bytes &b, uint32_t v) {
  put16(b, uint16_t(v));
  put16(b, uint16_t(v >> 16));
}
struct Bits {
  View v;
  size_t n, pos = 0;
  Bits(View v, size_t n) : v(v), n(n) {
    need(v.n == (n + 7) / 8, "exact bit bytes");
    if (n % 8)
      need(!(v[v.n - 1] & ((1u << (8 - n % 8)) - 1)), "nonzero bit padding");
  }
  unsigned bit() {
    need(pos < n, "truncated bits");
    unsigned q = (v[pos / 8] >> (7 - pos % 8)) & 1;
    pos++;
    return q;
  }
  uint32_t get(unsigned count) {
    need(count <= 32, "bit width");
    uint32_t v = 0;
    while (count--)
      v = v * 2 + bit();
    return v;
  }
  void end() { need(pos == n, "trailing bits"); }
};
inline int signed8(uint8_t v) { return v < 128 ? int(v) : int(v) - 256; }
inline int signed16(uint16_t v) { return v < 32768 ? int(v) : int(v) - 65536; }
inline int signed_zig(uint32_t v) {
  return v & 1 ? -int(v / 2) - 1 : int(v / 2);
}
inline int clamp(int x, int a, int b) { return std::max(a, std::min(b, x)); }
inline int64_t floor_shift(int64_t x, unsigned n) {
  return x >= 0 ? x >> n
                : -int64_t((uint64_t(-x) + (uint64_t(1) << n) - 1) >> n);
}
} // namespace cu66
