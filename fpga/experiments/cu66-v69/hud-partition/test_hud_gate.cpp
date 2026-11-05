#include "hud_gate.hpp"
#include <chrono>
#include <fstream>
#include <iostream>
#include <sstream>
#include <type_traits>
using namespace cu66;
using namespace cu66_partition;
Bytes readfile(const std::string &path) {
  std::ifstream f(path, std::ios::binary);
  need(bool(f), "HUD gate fixture open");
  return Bytes(std::istreambuf_iterator<char>(f), {});
}
std::vector<std::string> split(const std::string &s) {
  std::stringstream ss(s);
  std::vector<std::string> v;
  std::string x;
  while (std::getline(ss, x, '\t'))
    v.push_back(x);
  return v;
}
std::string cache_hash(const std::shared_ptr<const HudCache> &cache) {
  if (!cache)
    return "empty";
  SHA256 h;
  for (auto &p : cache->patches) {
    auto b = word_bytes(p.words);
    h.update(b);
  }
  return hex(h.finish());
}
struct Slice {
  uint32_t id, rid;
  bool key;
  View hud;
};
Slice slice(const Bytes &packet) {
  Reader r(View(packet).sub(0, 76));
  need(r.magic() == "CU66" && r.u8() == 1, "CU66 seed profile");
  bool key = r.u8() & 1;
  need(r.u16() == 25, "seed epoch");
  auto fid = r.u32(), rid = r.u32();
  r.take(52);
  unsigned nb = r.u32(), nh = r.u32();
  return {fid, rid, key, View(packet).sub(76 + nb, nh)};
}
Tag transfer_to_test_sink(const std::shared_ptr<const HudCache> &cache) {
  std::vector<Patch> external;
  for (auto &p : cache->patches) {
    Patch copy;
    copy.rect = p.rect;
    copy.words = p.words;
    external.push_back(std::move(copy));
  }
  need(cu66::hud_tag(external) == cache->tag, "native test sink readback tag");
  return cu66::hud_tag(external);
}
void publish(HudGate &gate, uint64_t gen, uint32_t fid) {
  auto candidate = gate.read_candidate(gen, fid);
  need(bool(candidate), "missing candidate");
  auto readback = transfer_to_test_sink(candidate);
  need(gate.acknowledge_external_write_drain(gen, fid, HUD_WORDS, readback),
       "correct transfer ACK");
  need(gate.commit(gen, fid), "qualified root commit");
}
int main(int argc, char **argv) {
  try {
    need(argc == 2, "test_hud_gate native fixture directory");
    std::string base = argv[1];
    if (base.back() != '/')
      base += '/';
    std::ifstream input(base + "index.tsv");
    std::string line;
    HudGate gate;
    uint64_t gen = 0;
    int prior_case = -1;
    unsigned frames = 0, keys = 0;
    size_t max_one_capacity = 0, max_joint_capacity = 0;
    double decode_ms = 0;
    Bytes first_key, next, recovery;
    while (std::getline(input, line)) {
      auto fields = split(line);
      need(fields.size() == 6, "native index fields");
      int caseid = std::stoi(fields[0]);
      if (caseid != prior_case) {
        need(gate.reset(++gen, true), "new case quiescent reset");
        prior_case = caseid;
      }
      auto packet = readfile(base + fields[2]);
      auto info = slice(packet);
      if (caseid == 0 && info.id == 0)
        first_key = packet;
      if (caseid == 0 && info.id == 1)
        next = packet;
      if (caseid == 0 && info.id == 24)
        recovery = packet;
      auto previous = gate.accepted();
      auto before = cache_hash(previous);
      auto active = ++gen;
      auto began = std::chrono::steady_clock::now();
      auto reply = gate.prepare(active, info.id, info.rid, info.key, info.hud);
      auto ended = std::chrono::steady_clock::now();
      decode_ms +=
          std::chrono::duration<double, std::milli>(ended - began).count();
      need(reply == Reply::Accepted, "stored HUD prepare rejected");
      auto candidate = gate.read_candidate(active, info.id);
      static_assert(
          std::is_const_v<typename decltype(candidate)::element_type>);
      need(candidate && logical_words(*candidate) == HUD_WORDS &&
               cache_hash(candidate) == fields[4],
           "native HUD semantic output");
      // The decoded candidate owns its words; no compressed-input alias
      // remains.
      std::fill(packet.begin(), packet.end(), uint8_t(0));
      need(cache_hash(candidate) == fields[4], "candidate aliases wire input");
      need(gate.candidate_ready() && gate.status().decoded_verified &&
               !gate.status().external_write_drain_acknowledged &&
               gate.status().phase == Phase::Ready,
           "ready status contract");
      need(gate.accepted() == previous && cache_hash(previous) == before,
           "prepare changed accepted cache");
      need(gate.prepare(active + 1, info.id, info.rid, info.key, info.hud) ==
               Reply::Busy,
           "busy candidate replaced");
      need(!gate.read_candidate(active + 1, info.id) &&
               !gate.abort(active + 1, info.id) &&
               !gate.commit(active + 1, info.id),
           "stale command affected candidate");
      need(!gate.commit(active, info.id),
           "commit before external drain accepted");
      auto tag = candidate->tag;
      Tag wrong = tag;
      wrong[0] ^= 1;
      need(!gate.acknowledge_external_write_drain(active, info.id,
                                                  HUD_WORDS - 1, tag) &&
               !gate.acknowledge_external_write_drain(active, info.id,
                                                      HUD_WORDS, wrong),
           "bad external drain ACK accepted");
      max_one_capacity =
          std::max(max_one_capacity, allocated_word_bytes(*candidate));
      max_joint_capacity =
          std::max(max_joint_capacity,
                   allocated_word_bytes(*candidate) +
                       (previous ? allocated_word_bytes(*previous) : 0));
      publish(gate, active, info.id);
      need(gate.accepted() == candidate &&
               cache_hash(gate.accepted()) == fields[4] &&
               cache_hash(previous) == before,
           "commit/previous-cache immutability");
      need(gate.commit(active, info.id) && !gate.abort(active, info.id) &&
               !gate.candidate_ready() && !gate.candidate_transferred(),
           "commit retry/late abort contract");
      need(gate.prepare(active, info.id, info.rid, info.key, info.hud) ==
               Reply::Stale,
           "generation reuse accepted");
      frames++;
      keys += info.key;
    }
    need(frames == 457 && keys == 20, "whole retained HUD history");
    // Failure/abort tests start from a real accepted key0 HUD cache each time.
    unsigned rejected = 0, base_failure_rollbacks = 0;
    std::ifstream bads(base + "negative.tsv");
    while (std::getline(bads, line)) {
      auto f = split(line);
      if (f[0] != "HUD_crc" && f[0] != "late_HUD_output_tag" &&
          f[0] != "actual_legacy_coefficient_packet" &&
          f[0] != "actual_nonzero_motion_CU66" &&
          f[0] != "hidden_nonzero_coefficient_resealed" &&
          f[0] != "output_wrong")
        continue;
      HudGate test;
      auto seed = slice(first_key);
      need(test.prepare(1, seed.id, seed.rid, seed.key, seed.hud) ==
               Reply::Accepted,
           "rollback seed");
      publish(test, 1, 0);
      auto old = test.accepted();
      auto hash = cache_hash(old);
      auto packet = readfile(base + f[1]);
      auto inf = slice(packet);
      auto reply = test.prepare(2, inf.id, inf.rid, inf.key, inf.hud);
      if (f[0] == "HUD_crc" || f[0] == "late_HUD_output_tag") {
        need(reply == Reply::DecodeRejected &&
                 !test.read_candidate(2, inf.id) &&
                 !test.status().decoded_verified && !test.candidate_ready(),
             "malformed HUD became ready");
        rejected++;
      } else {
        need(reply == Reply::Accepted && test.status().decoded_verified,
             "valid HUD under failed base rejected unexpectedly");
        need(!test.commit(2, inf.id),
             "base failed but HUD committed without drain/root gate");
        auto readback = transfer_to_test_sink(test.read_candidate(2, inf.id));
        need(test.acknowledge_external_write_drain(2, inf.id, HUD_WORDS,
                                                   readback),
             "provisional external transfer ACK");
        need(test.status().phase == Phase::Transferred &&
                 test.candidate_transferred(),
             "base-failure rollback was not exercised after transfer");
        base_failure_rollbacks++;
      }
      need(test.abort(2, inf.id) && test.accepted() == old &&
               cache_hash(old) == hash,
           "candidate failure/abort changed previous HUD");
      auto rec = slice(recovery);
      need(test.prepare(3, rec.id, rec.rid, rec.key, rec.hud) ==
               Reply::Accepted,
           "independent key recovery prepare");
      publish(test, 3, rec.id);
      need(test.accepted()->id == 24 && cache_hash(old) == hash,
           "key recovery/old ownership");
    }
    // Identity/config and reset fences are enforced without touching accepted
    // data.
    HudGate test;
    auto key = slice(first_key), p = slice(next);
    need(test.prepare(1, p.id, p.rid, p.key, p.hud) == Reply::InvalidIdentity,
         "missing prior HUD accepted");
    need(test.prepare(2, key.id, key.rid, key.key, key.hud) == Reply::Accepted,
         "fresh key after failure");
    publish(test, 2, 0);
    auto saved = test.accepted();
    need(!test.reset(3, false) && test.accepted() == saved,
         "nonquiescent reset changed cache");
    need(test.reset(3, true) && !test.accepted() && !test.read_candidate(2, 0),
         "quiescent reset failed");
    need(test.prepare(2, key.id, key.rid, key.key, key.hud) == Reply::Stale,
         "old generation crossed reset");
    std::cout << "TEST_PASS {\"frames\":" << frames << ",\"keys\":" << keys
              << ",\"logical_words_per_cache\":" << HUD_WORDS
              << ",\"logical_bytes_per_cache\":" << HUD_WORDS * 2
              << ",\"maximum_one_cache_word_capacity_bytes\":"
              << max_one_capacity
              << ",\"maximum_previous_plus_candidate_word_capacity_bytes\":"
              << max_joint_capacity << ",\"sizeof_HudGate\":" << sizeof(HudGate)
              << ",\"sizeof_HudCache\":" << sizeof(HudCache)
              << ",\"sizeof_Patch\":" << sizeof(Patch)
              << ",\"HUD_decode_rejections\":" << rejected
              << ",\"base_failed_valid_HUD_rollbacks\":"
              << base_failure_rollbacks
              << ",\"mean_native_prepare_ms\":" << decode_ms / frames
              << ",\"software_endpoint_is_Linux_host\":true,\"physical_DMA_or_"
                 "FPGA_HUD_decoder_proven\":false}\n";
    return 0;
  } catch (const std::exception &e) {
    std::cerr << "TEST_FAIL " << e.what() << "\n";
    return 1;
  }
}
