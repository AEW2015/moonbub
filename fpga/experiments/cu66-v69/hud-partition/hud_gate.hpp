#pragma once
// Native HUD semantic endpoint for the explicitly partial software/FPGA split.
// This is not an ESP32 firmware transport or an RTL HUD decoder.
#include "../../../../experiments/cu66-native-v69/hud.hpp"
#include <memory>
#include <string>
namespace cu66_partition {
using cu66::Bytes;
using cu66::Patch;
using cu66::Tag;
using cu66::View;
constexpr uint32_t NO_REFERENCE = 0xffffffffu;
constexpr uint32_t HUD_WORDS = 21120;
enum class Opcode : uint8_t {
  Prepare = 1,
  Status = 2,
  ReadCandidate = 3,
  AcknowledgeExternalWriteDrain = 4,
  Commit = 5,
  Abort = 6,
  Reset = 7
};
enum class Phase : uint8_t {
  Idle,
  Ready,
  Transferred,
  Committed,
  Aborted,
  Failed
};
enum class Reply : uint8_t {
  Accepted,
  Busy,
  Stale,
  InvalidIdentity,
  DecodeRejected
};
struct HudCache {
  uint64_t generation = 0;
  uint32_t id = 0, reference_id = NO_REFERENCE;
  Tag tag{};
  std::vector<Patch> patches;
};
struct Status {
  Phase phase = Phase::Idle;
  uint64_t generation = 0;
  uint32_t frame_id = 0, reference_id = NO_REFERENCE, words = 0;
  Tag tag{};
  bool decoded_verified = false, external_write_drain_acknowledged = false;
  std::string failure;
};
class HudGate {
  std::shared_ptr<const HudCache> accepted_, candidate_;
  uint64_t latest_generation_ = 0;
  Status status_;
  bool matches(uint64_t gen, uint32_t fid) const {
    return candidate_ && candidate_->generation == gen && candidate_->id == fid;
  }

public:
  const Status &status() const { return status_; }
  bool candidate_ready() const {
    return bool(candidate_) && status_.decoded_verified;
  }
  bool candidate_transferred() const {
    return candidate_ready() && status_.external_write_drain_acknowledged;
  }
  std::shared_ptr<const HudCache> accepted() const { return accepted_; }
  std::shared_ptr<const HudCache> read_candidate(uint64_t generation,
                                                 uint32_t fid) const {
    return matches(generation, fid) ? candidate_ : nullptr;
  }
  Reply prepare(uint64_t generation, uint32_t fid, uint32_t rid, bool key,
                View packet) {
    if (candidate_)
      return Reply::Busy;
    if (generation == 0 || generation <= latest_generation_)
      return Reply::Stale;
    latest_generation_ = generation;
    status_ = {};
    status_.generation = generation;
    status_.frame_id = fid;
    status_.reference_id = rid;
    if (fid == NO_REFERENCE ||
        (key ? (rid != NO_REFERENCE) : (rid == NO_REFERENCE || rid >= fid)) ||
        (accepted_ && fid <= accepted_->id)) {
      status_.phase = Phase::Failed;
      status_.failure = "invalid whole-frame identity";
      return Reply::InvalidIdentity;
    }
    if (!key && (!accepted_ || accepted_->id != rid)) {
      status_.phase = Phase::Failed;
      status_.failure = "missing exact accepted HUD ID";
      return Reply::InvalidIdentity;
    }
    try {
      auto words = cu66::decode_hud(packet, key ? nullptr : &accepted_->patches,
                                    fid, rid);
      // decode_hud already verified the reconstructed envelope tag against
      // words.
      cu66::Reader header(packet.sub(38, 16));
      auto verified_tag = header.tag();
      auto pending = std::make_shared<HudCache>();
      pending->generation = generation;
      pending->id = fid;
      pending->reference_id = rid;
      pending->tag = verified_tag;
      pending->patches = std::move(words);
      candidate_ = pending;
      status_.phase = Phase::Ready;
      status_.words = HUD_WORDS;
      status_.tag = verified_tag;
      status_.decoded_verified = true;
      return Reply::Accepted;
    } catch (const std::exception &e) {
      status_.phase = Phase::Failed;
      status_.failure = e.what();
      return Reply::DecodeRejected;
    }
  }
  // This is an explicit ACK from the external writer/owner, not an internally
  // measured physical DMA fence. The native test sink copies and hashes words.
  bool acknowledge_external_write_drain(uint64_t generation, uint32_t fid,
                                        uint32_t words, Tag readback_tag) {
    if (!matches(generation, fid) || words != HUD_WORDS ||
        readback_tag != candidate_->tag)
      return false;
    status_.phase = Phase::Transferred;
    status_.external_write_drain_acknowledged = true;
    return true;
  }
  // Root authority calls this only for a globally qualified whole-frame commit.
  // Identical retries are idempotent; a delayed older commit cannot replace
  // HUD.
  bool commit(uint64_t generation, uint32_t fid) {
    if (accepted_ && accepted_->generation == generation &&
        accepted_->id == fid)
      return true;
    if (!matches(generation, fid) || !status_.external_write_drain_acknowledged)
      return false;
    accepted_ = candidate_;
    candidate_.reset();
    status_.phase = Phase::Committed;
    return true;
  }
  bool abort(uint64_t generation, uint32_t fid) {
    bool failed = status_.phase == Phase::Failed &&
                  status_.generation == generation && status_.frame_id == fid;
    if (!matches(generation, fid) && !failed)
      return false;
    candidate_.reset();
    status_.phase = Phase::Aborted;
    status_.decoded_verified = false;
    status_.external_write_drain_acknowledged = false;
    status_.words = 0;
    status_.tag = {};
    return true;
  }
  // Reset requires a new root lease generation and externally established
  // quiescence; no real bus/DMA flush can be inferred by this software object.
  bool reset(uint64_t generation, bool all_external_masters_quiescent) {
    if (!all_external_masters_quiescent || !generation ||
        generation <= latest_generation_)
      return false;
    accepted_.reset();
    candidate_.reset();
    latest_generation_ = generation;
    status_ = {};
    status_.generation = generation;
    return true;
  }
};
inline uint32_t logical_words(const HudCache &cache) {
  uint32_t n = 0;
  for (auto &p : cache.patches)
    n += uint32_t(p.words.size());
  return n;
}
inline size_t allocated_word_bytes(const HudCache &cache) {
  size_t n = 0;
  for (auto &p : cache.patches)
    n += p.words.capacity() * sizeof(uint16_t);
  return n;
}
} // namespace cu66_partition
