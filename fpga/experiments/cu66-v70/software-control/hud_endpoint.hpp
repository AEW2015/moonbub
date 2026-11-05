#pragma once
// Transport-neutral C++17 endpoint. No OS, FPGA, DMA or authentication code.
#include "../../cu66-v69/hud-partition/hud_gate.hpp"
#include <limits>

namespace hc70 {
using cu66::Bytes;
using cu66::Tag;
using cu66::View;
constexpr uint32_t MAX_PAYLOAD = 49152;
constexpr uint32_t STATUS_BYTES = 72;
struct ProtocolError : std::runtime_error {
  using std::runtime_error::runtime_error;
};
inline void require(bool ok, const char *reason) {
  if (!ok)
    throw ProtocolError(reason);
}
struct Message {
  bool response = false;
  uint8_t opcode = 0;
  uint64_t generation = 0;
  uint32_t frame_id = 0, reference_id = 0, argument = 0;
  Bytes payload;
};
inline uint64_t get64(cu66::Reader &r) {
  uint64_t low = r.u32();
  return low | (uint64_t(r.u32()) << 32);
}
inline void put64(Bytes &b, uint64_t n) {
  cu66::put32(b, uint32_t(n));
  cu66::put32(b, uint32_t(n >> 32));
}
inline void validate(const Message &m) {
  require(m.opcode >= 1 && m.opcode <= 7, "unknown opcode");
  require(m.payload.size() <= MAX_PAYLOAD, "payload exceeds49152");
  if (!m.response) {
    if (m.opcode == 3)
      require(m.payload.size() == 8, "READ payload mustbe8bytes");
    if (m.opcode == 4)
      require(m.payload.size() == 20, "ACK payload mustbe20bytes");
    if (m.opcode == 2 || m.opcode >= 5)
      require(m.payload.empty(), "empty command payload required");
    if (m.opcode == 7)
      require(m.argument == 1, "RESET requires caller quiescence assertion");
  }
}
inline Bytes encode(const Message &m) {
  validate(m);
  Bytes out;
  out.reserve(36 + m.payload.size());
  for (char c : std::string(m.response ? "HR70" : "HC70"))
    out.push_back(uint8_t(c));
  out.push_back(1);
  out.push_back(m.opcode);
  cu66::put16(out, 0);
  cu66::put32(out, uint32_t(m.payload.size()));
  put64(out, m.generation);
  cu66::put32(out, m.frame_id);
  cu66::put32(out, m.reference_id);
  cu66::put32(out, m.argument);
  out.insert(out.end(), m.payload.begin(), m.payload.end());
  cu66::put32(out, cu66::crc32(out));
  return out;
}
inline Message decode(View wire) {
  require(wire.n >= 36 && wire.n <= size_t(MAX_PAYLOAD) + 36,
          "frame length outsidebounds");
  cu66::Reader r(wire);
  auto magic = r.magic();
  require(magic == "HC70" || magic == "HR70", "unknown magic");
  require(r.u8() == 1, "unsupported version");
  Message m;
  m.response = magic == "HR70";
  m.opcode = r.u8();
  require(r.u16() == 0, "reserved bits mustbezero");
  auto length = r.u32();
  require(length <= MAX_PAYLOAD && size_t(length) + 36 == wire.n,
          "declared/exact frame length");
  m.generation = get64(r);
  m.frame_id = r.u32();
  m.reference_id = r.u32();
  m.argument = r.u32();
  auto data = r.take(length);
  uint32_t expected = r.u32();
  r.end();
  // No endpoint object is touched before all header/payload CRC bytes pass.
  require(cu66::crc32(wire.sub(0, wire.n - 4)) == expected,
          "header+payload CRC32 mismatch");
  m.payload.assign(data.p, data.p + data.n);
  validate(m);
  return m;
}
enum class Code : uint32_t {
  Ok = 0,
  Busy = 1,
  Stale = 2,
  InvalidIdentity = 3,
  DecodeRejected = 4,
  Rejected = 5
};
inline Code map_reply(cu66_partition::Reply r) {
  switch (r) {
  case cu66_partition::Reply::Accepted:
    return Code::Ok;
  case cu66_partition::Reply::Busy:
    return Code::Busy;
  case cu66_partition::Reply::Stale:
    return Code::Stale;
  case cu66_partition::Reply::InvalidIdentity:
    return Code::InvalidIdentity;
  case cu66_partition::Reply::DecodeRejected:
    return Code::DecodeRejected;
  }
  return Code::Rejected;
}
class HudEndpoint {
  cu66_partition::HudGate gate_;
  bool last_abort_valid_ = false;
  uint64_t last_abort_generation_ = 0;
  uint32_t last_abort_frame_ = 0, last_abort_reference_ = 0;
  bool candidate_matches(const Message &m) const {
    auto c = gate_.read_candidate(m.generation, m.frame_id);
    return c && c->reference_id == m.reference_id;
  }
  bool status_matches(const Message &m) const {
    const auto &s = gate_.status();
    return s.generation == m.generation && s.frame_id == m.frame_id &&
           s.reference_id == m.reference_id;
  }
  Bytes status_payload() const {
    const auto &s = gate_.status();
    auto accepted = gate_.accepted();
    Bytes b;
    b.push_back(uint8_t(s.phase));
    b.push_back(uint8_t((s.decoded_verified ? 1 : 0) |
                        (s.external_write_drain_acknowledged ? 2 : 0) |
                        (gate_.candidate_ready() ? 4 : 0) |
                        (gate_.candidate_transferred() ? 8 : 0) |
                        (accepted ? 16 : 0)));
    cu66::put16(b, 0);
    cu66::put32(b, s.words);
    put64(b, s.generation);
    cu66::put32(b, s.frame_id);
    cu66::put32(b, s.reference_id);
    b.insert(b.end(), s.tag.begin(), s.tag.end());
    put64(b, accepted ? accepted->generation : 0);
    cu66::put32(b, accepted ? accepted->id : 0xffffffffu);
    cu66::put32(b, accepted ? accepted->reference_id : 0xffffffffu);
    Tag tag = accepted ? accepted->tag : Tag{};
    b.insert(b.end(), tag.begin(), tag.end());
    require(b.size() == STATUS_BYTES, "internal status size");
    return b;
  }

public:
  std::shared_ptr<const cu66_partition::HudCache> accepted() const {
    return gate_.accepted();
  }
  Bytes transact(const Bytes &wire) {
    Message m = decode(wire);
    require(!m.response, "endpoint accepts requests only");
    Message out = m;
    out.response = true;
    out.payload.clear();
    Code code = Code::Rejected;
    switch (m.opcode) {
    case 1:
      if (m.argument <= 1)
        code = map_reply(gate_.prepare(m.generation, m.frame_id, m.reference_id,
                                       m.argument == 1, m.payload));
      break;
    case 2:
      if (m.argument == 0)
        code = Code::Ok;
      break;
    case 3:
      if (m.argument == 0 && candidate_matches(m)) {
        cu66::Reader p(m.payload);
        uint32_t offset = p.u32(), count = p.u32();
        if (offset <= cu66_partition::HUD_WORDS &&
            count <= cu66_partition::HUD_WORDS - offset) {
          auto candidate = gate_.read_candidate(m.generation, m.frame_id);
          uint32_t index = 0;
          out.payload.reserve(size_t(count) * 2);
          for (const auto &patch : candidate->patches)
            for (auto word : patch.words) {
              if (index >= offset && index - offset < count)
                cu66::put16(out.payload, word);
              index++;
            }
          require(out.payload.size() == size_t(count) * 2,
                  "internal READ coverage");
          code = Code::Ok;
        }
      }
      break;
    case 4:
      if (m.argument == 1 && candidate_matches(m)) {
        cu66::Reader p(m.payload);
        uint32_t words = p.u32();
        Tag tag = p.tag();
        if (gate_.acknowledge_external_write_drain(m.generation, m.frame_id,
                                                   words, tag))
          code = Code::Ok;
      }
      break;
    case 5:
      if (m.argument == 0) {
        auto accepted = gate_.accepted();
        if (candidate_matches(m) ||
            (accepted && accepted->generation == m.generation &&
             accepted->id == m.frame_id &&
             accepted->reference_id == m.reference_id))
          if (gate_.commit(m.generation, m.frame_id))
            code = Code::Ok;
      }
      break;
    case 6:
      if (m.argument == 0) {
        if (last_abort_valid_ && last_abort_generation_ == m.generation &&
            last_abort_frame_ == m.frame_id &&
            last_abort_reference_ == m.reference_id)
          code = Code::Ok;
        else if (status_matches(m) && gate_.abort(m.generation, m.frame_id)) {
          last_abort_valid_ = true;
          last_abort_generation_ = m.generation;
          last_abort_frame_ = m.frame_id;
          last_abort_reference_ = m.reference_id;
          code = Code::Ok;
        }
      }
      break;
    case 7:
      if (gate_.reset(m.generation, m.argument == 1)) {
        last_abort_valid_ = false;
        code = Code::Ok;
      }
      break;
    default:
      throw ProtocolError("internal opcode");
    }
    out.argument = uint32_t(code);
    if (m.opcode != 3 || code != Code::Ok)
      out.payload = status_payload();
    return encode(out);
  }
};
} // namespace hc70
