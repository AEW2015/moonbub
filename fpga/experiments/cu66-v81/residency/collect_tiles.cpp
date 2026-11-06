// Separate native-only oracle collector. Frozen decoder and fixtures are read-only.
#include "../../../../experiments/cu66-native-v69/decoder.hpp"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <set>
#include <sstream>
using namespace cu66;
static Bytes load(const std::filesystem::path &p) {
  std::ifstream f(p, std::ios::binary); need(bool(f), "fixture open");
  return {std::istreambuf_iterator<char>(f), {}};
}
static std::vector<std::string> split(const std::string &s) {
  std::vector<std::string> v; std::stringstream in(s); std::string x;
  while (std::getline(in, x, '\t')) v.push_back(x);
  return v;
}
int main(int argc, char **argv) { try {
  need(argc == 3, "index and binary tile-fingerprint output prefix required");
  std::filesystem::path index = argv[1]; std::ifstream input(index);
  std::ofstream fingerprints;
  need(bool(input), "oracle input open");
  Decoder decoder; int prior_cohort = -1; unsigned frames = 0, keys = 0;
  std::array<unsigned, 4> counts{}; std::string line;
  std::set<std::pair<int, unsigned>> seen;
  while (std::getline(input, line)) {
    auto f = split(line); need(f.size() == 6, "six index fields");
    int cohort = std::stoi(f[0]); unsigned fid = unsigned(std::stoul(f[1]));
    need(cohort >= 0 && cohort < 4, "cohort bound");
    if (cohort != prior_cohort) {
      need(cohort == prior_cohort + 1, "ordered independent histories");
      if (fingerprints.is_open()) {
        fingerprints.flush(); need(bool(fingerprints), "fingerprint cohort output complete");
        fingerprints.close();
      }
      fingerprints.open(std::string(argv[2]) + std::to_string(cohort) + ".bin", std::ios::binary);
      need(bool(fingerprints), "oracle fingerprint output open");
      decoder = Decoder(); prior_cohort = cohort;
    }
    auto previous = decoder.state(); auto packet = load(index.parent_path() / f[2]);
    auto packet_hash = hex(sha256(packet));
    need(packet_hash == std::filesystem::path(f[2]).stem().string(), "packet SHA256");
    auto current = decoder.receive(packet);
    need(current->id == fid && seen.emplace(cohort, fid).second, "unique fixture");
    SHA256 canonical; for (const auto &p : current->planes) canonical.update(p);
    need(hex(canonical.finish()) == f[3], "full golden canonical SHA256");
    Bytes hud; for (const auto &p : current->hud) {
      auto b = word_bytes(p.words); hud.insert(hud.end(), b.begin(), b.end());
    }
    need(hex(sha256(hud)) == f[4], "golden HUD SHA256");
    need(hex(sha256(word_bytes(current->display))) == f[5], "golden display SHA256");
    std::cout << "{\"cohort\":" << cohort << ",\"ordinal\":" << counts[cohort]
      << ",\"fid\":" << fid << ",\"key\":" << (current->key ? "true" : "false")
      << ",\"comparable\":" << (previous ? "true" : "false")
      << ",\"previous_fid\":" << (previous ? std::to_string(previous->id) : "null")
      << ",\"packet_sha256\":\"" << packet_hash << "\",\"canonical_sha256\":\"" << f[3]
      << "\",\"hud_sha256\":\"" << f[4] << "\",\"display_sha256\":\"" << f[5]
      << "\",\"canonical_tag\":\"" << hex(current->canonical_tag) << "\",\"planes\":[";
    for (unsigned plane = 0; plane < 3; ++plane) {
      unsigned width = plane ? 360 : 720, tiles = plane ? 1350 : 5400;
      const auto *hidden = plane == 0 ? SAFE0 : plane == 1 ? SAFE1 : SAFE2;
      unsigned same_visible = 0, same_hidden = 0, hidden_count = 0;
      Bytes mask((tiles + 7) / 8, 0);
      for (unsigned tile = 0; tile < tiles; ++tile) {
        Bytes bytes; bytes.reserve(64); bool equal = bool(previous);
        unsigned y = (tile / (width / 8)) * 8, x = (tile % (width / 8)) * 8;
        hidden_count += hidden[tile] != 0;
        for (unsigned yy = 0; yy < 8; ++yy) for (unsigned xx = 0; xx < 8; ++xx) {
          unsigned at = (y + yy) * width + x + xx;
          uint8_t value = current->planes[plane][at]; bytes.push_back(value);
          if (previous && value != previous->planes[plane][at]) equal = false;
          if (hidden[tile]) need(value == 128, "fixed hidden canonical byte");
        }
        auto digest = sha256(bytes);
        fingerprints.write(reinterpret_cast<const char *>(digest.data()), digest.size());
        if (equal) {
          mask[tile / 8] |= uint8_t(1u << (tile % 8));
          if (hidden[tile]) ++same_hidden; else ++same_visible;
        }
      }
      need(hidden_count == (plane == 0 ? 256u : 19u), "hidden tile coverage");
      std::cout << (plane ? "," : "") << "{\"plane\":" << plane << ",\"tiles\":" << tiles
        << ",\"hidden_tiles\":" << hidden_count << ",\"same_visible\":" << same_visible
        << ",\"same_hidden\":" << same_hidden << ",\"same_mask_u8_lsb_hex\":\"" << hex(mask) << "\"}";
    }
    std::cout << "]}" << std::endl; ++frames; ++counts[cohort]; keys += current->key;
  }
  fingerprints.flush(); need(bool(fingerprints), "fingerprint output complete");
  need(frames == 457 && keys == 20 && counts == std::array<unsigned, 4>{119,119,119,100}, "complete corpus");
  std::cout << "RESIDENCY_NATIVE_ORACLE_PASS frames=" << frames << " keys=" << keys
    << " deltas=" << frames - keys << " packet_canonical_hud_display=1 exact_tile_bytes=1" << std::endl;
} catch (const std::exception &e) { std::cerr << "FAIL " << e.what() << std::endl; return 1; } }
