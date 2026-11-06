// V82 instrumented fork of frozen V69 decoder; observes quantized c[64] before IDCT.
#pragma once
#include "../../cu66-native-v69/entropy.hpp"
#include "../../cu66-native-v69/hud.hpp"
#include <memory>
namespace cu66 {
struct InstrumentedCapabilities {
  bool arithmetic_dispatch_5_6 = true;
  bool zero_motion_only = true;
  unsigned width = 720, height = 480, epoch = 25;
};
struct InstrumentedFrame {
  uint32_t id = 0, reference_id = 0xffffffffu;
  bool key = false;
  Tag canonical_tag{};
  std::array<Bytes, 3> planes;
  std::array<Bytes, 3> zero_coefficients;
  std::vector<Patch> hud;
  std::vector<uint16_t> display;
};
class InstrumentedDecoder {
  InstrumentedCapabilities caps_;
  std::shared_ptr<const InstrumentedFrame> state_;

public:
  explicit InstrumentedDecoder(InstrumentedCapabilities caps = {}) : caps_(caps) {
    need(caps.arithmetic_dispatch_5_6 && caps.zero_motion_only &&
             caps.width == 720 && caps.height == 480 && caps.epoch == 25,
         "explicit implemented native capabilities");
  }
  const InstrumentedCapabilities &capabilities() const { return caps_; }
  std::shared_ptr<const InstrumentedFrame> state() const { return state_; }
  std::shared_ptr<const InstrumentedFrame> receive(const Bytes &packet);
};
inline Tag instrumented_canonical_tag(const std::array<Bytes, 3> &p) {
  SHA256 h;
  const uint8_t geometry[] = {0xd0, 0x02, 0xe0, 0x01};
  h.update({geometry, 4});
  for (auto &v : p)
    h.update(v);
  auto full = h.finish();
  Tag out;
  std::copy(full.begin(), full.begin() + 16, out.begin());
  return out;
}
inline std::vector<uint16_t> instrumented_render(const std::array<Bytes, 3> &p,
                                    const std::vector<Patch> &hud) {
  std::vector<uint16_t> out(720 * 480);
  auto up = [&p](unsigned a, unsigned y, unsigned x) {
    auto &w = p[a];
    unsigned yy = y / 2, xx = x / 2, xx1 = std::min(xx + 1, 359u),
             yy1 = std::min(yy + 1, 239u);
    int top = w[yy * 360 + xx];
    if (x & 1)
      top = (top + w[yy * 360 + xx1] + 1) / 2;
    if (y & 1) {
      int bottom = w[yy1 * 360 + xx];
      if (x & 1)
        bottom = (bottom + w[yy1 * 360 + xx1] + 1) / 2;
      top = (top + bottom + 1) / 2;
    }
    return top - 128;
  };
  for (unsigned y = 0; y < 480; y++)
    for (unsigned x = 0; x < 720; x++) {
      int Y = p[0][y * 720 + x], cb = up(1, y, x), cr = up(2, y, x);
      int r = clamp(Y + int(floor_shift(359 * cr + 128, 8)), 0, 255),
          g = clamp(Y - int(floor_shift(88 * cb + 183 * cr + 128, 8)), 0, 255),
          b = clamp(Y + int(floor_shift(454 * cb + 128, 8)), 0, 255);
      out[y * 720 + x] = uint16_t((r >> 3) << 11 | (g >> 2) << 5 | (b >> 3));
    }
  for (auto &v : hud)
    for (unsigned y = 0; y < v.rect[3]; y++)
      for (unsigned x = 0; x < v.rect[2]; x++)
        out[(v.rect[1] + y) * 720 + v.rect[0] + x] = v.words[y * v.rect[2] + x];
  return out;
}
inline std::shared_ptr<const InstrumentedFrame> InstrumentedDecoder::receive(const Bytes &packet) {
  View v(packet);
  checked(v, 88, 49152);
  Reader r(v.sub(0, v.n - 4));
  need(r.magic() == "CU66" && r.u8() == 1, "configured CU66 profile");
  unsigned flags = r.u8();
  need((flags == 2 || flags == 3) && r.u16() == 25, "CU66 flags/epoch");
  bool key = flags & 1;
  uint32_t fid = r.u32(), rid = r.u32();
  need(fid != 0xffffffffu && r.u16() == 720 && r.u16() == 480,
       "CU66 frame/geometry");
  auto profile = r.tag();
  need(std::equal(profile.begin(), profile.end(), PROFILE),
       "CU66 profile domain");
  Tag rt = r.tag(), ot = r.tag();
  unsigned nb = r.u32(), nh = r.u32();
  need(!zero(ot) && r.pos + size_t(nb) + nh == r.v.n && nb >= 67 && nh >= 110,
       "CU66 exact lengths/output");
  need(!state_ || fid > state_->id, "CU66 monotonic frame");
  if (key)
    need(rid == 0xffffffffu && zero(rt), "CU66 independent identity");
  else
    need(state_ && rid == state_->id && rid < fid &&
             rt == state_->canonical_tag,
         "CU66 cached reference binding");
  auto inner = r.take(nb), hud = r.take(nh);
  r.end();
  checked(inner, 67, 49152);
  Reader q(inner.sub(0, inner.n - 4));
  need(q.magic() == "GU66" && q.u8() == 1 && q.u8() == unsigned(key) &&
           q.u32() == 25 && q.u32() == fid && q.u32() == rid &&
           q.u16() == 720 && q.u16() == 480,
       "GU66 identity binding");
  unsigned bs = q.u8(), limit = q.u8();
  need((bs == 16 || bs == 32) && limit == 18 && q.tag() == rt,
       "GU66 geometry/reference binding");
  unsigned nq = q.u32(), nv = q.u32();
  std::array<unsigned, 3> length;
  for (auto &x : length)
    x = q.u32();
  need(nq == 338 &&
           q.pos + size_t(nq) + nv + length[0] + length[1] + length[2] == q.v.n,
       "GU66 body lengths");
  auto mapped = q.take(nq);
  std::array<uint8_t, 1350> qmap{};
  for (unsigned i = 0; i < 1352; i++) {
    unsigned code = (mapped[i / 4] >> (6 - 2 * (i % 4))) & 3;
    if (i >= 1350)
      need(code == 0, "qmap padding");
    else {
      need(code <= 2, "qmap code");
      qmap[i] = uint8_t(code);
    }
  }
  auto motion = q.take(nv);
  if (key)
    need(nv == 0, "key motion absent");
  else
    need(nv == 3 && motion[0] == 0 && motion[1] == 0 && motion[2] == 0,
         "capability zero-motion canonical map only");
  auto candidate = std::make_shared<InstrumentedFrame>();
  candidate->id = fid;
  candidate->reference_id = rid;
  candidate->key = key;
  for (unsigned axis = 0; axis < 3; axis++) {
    unsigned w = axis ? 360 : 720, hh = axis ? 240 : 480, bw = w / 8,
             blocks = bw * (hh / 8);
    need(length[axis] >= 47 && length[axis] <= 128 * blocks + 256,
         "bounded plane bytes");
    Reader a(q.take(length[axis]));
    unsigned dispatch = a.u8();
    need(dispatch == 5 || dispatch == 6, "capability AB38 dispatch5/6 only");
    const uint8_t *safe = axis == 0 ? SAFE0 : axis == 1 ? SAFE1 : SAFE2;
    unsigned visible = 0;
    for (unsigned b = 0; b < blocks; b++)
      visible += !safe[b];
    unsigned encoded = dispatch == 6 ? visible : blocks;
    auto coeff =
        decode_ab38(a.take(a.v.n - a.pos), encoded, dispatch == 6 ? 1 : bw);
    a.end();
    auto &output = candidate->planes[axis];
    output.resize(w * hh);
    unsigned cursor = 0;
    for (unsigned b = 0; b < blocks; b++) {
      unsigned by = b / bw, bx = b % bw;
      std::array<int16_t, 64> c{};
      if (dispatch != 6 || !safe[b]) {
        std::copy(coeff.begin() + cursor * 64,
                  coeff.begin() + (cursor + 1) * 64, c.begin());
        cursor++;
      }
      if (safe[b])
        need(std::all_of(c.begin(), c.end(), [](int x) { return x == 0; }),
             "canonical hidden coefficients");
      candidate->zero_coefficients[axis].push_back(
          std::all_of(c.begin(), c.end(), [](int x) { return x == 0; }) ? 1 : 0);
      unsigned scale = qmap[(axis ? by : by / 2) * 45 + (axis ? bx : bx / 2)];
      const auto &table = QTABLES[axis ? 1 : 0][scale];
      int64_t a64[8][8], mid[8][8];
      for (unsigned y = 0; y < 8; y++)
        for (unsigned x = 0; x < 8; x++)
          a64[y][x] = int64_t(c[y * 8 + x]) * table[y][x];
      for (unsigned y = 0; y < 8; y++)
        for (unsigned x = 0; x < 8; x++) {
          int64_t sum = 0;
          for (unsigned k = 0; k < 8; k++)
            sum += a64[y][k] * DCT[k][x];
          mid[y][x] = floor_shift(sum + 8192, 14);
        }
      for (unsigned y = 0; y < 8; y++)
        for (unsigned x = 0; x < 8; x++) {
          int64_t sum = 0;
          for (unsigned k = 0; k < 8; k++)
            sum += DCT[k][y] * mid[k][x];
          auto residual = floor_shift(sum + 8192, 14);
          unsigned index = (by * 8 + y) * w + bx * 8 + x;
          int prediction = key ? 128 : state_->planes[axis][index];
          output[index] =
              safe[b] ? 128
                      : uint8_t(std::max<int64_t>(
                            0, std::min<int64_t>(255, residual + prediction)));
        }
    }
    need(cursor == encoded, "coefficient tile coverage");
  }
  q.end();
  candidate->canonical_tag = instrumented_canonical_tag(candidate->planes);
  need(candidate->canonical_tag == ot, "canonical CU66 output tag");
  candidate->hud = decode_hud(hud, key ? nullptr : &state_->hud, fid, rid);
  candidate->display = instrumented_render(candidate->planes, candidate->hud);
  state_ = candidate;
  return state_;
}
} // namespace cu66
