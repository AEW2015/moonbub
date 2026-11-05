#include "decoder.hpp"
#include <fstream>
#include <iostream>
#include <random>
#include <sstream>
using namespace cu66;
Bytes readfile(const std::string &path) {
  std::ifstream f(path, std::ios::binary);
  need(bool(f), "fuzz fixture open");
  return Bytes(std::istreambuf_iterator<char>(f), {});
}
uint32_t field(const Bytes &b, size_t p) {
  Reader r(View(b).sub(p, 4));
  return r.u32();
}
void reseal(Bytes &b, size_t start, size_t length) {
  need(length >= 4 && start + length <= b.size(), "fuzz reseal bounds");
  auto c = crc32(View(b).sub(start, length - 4));
  for (unsigned i = 0; i < 4; i++)
    b[start + length - 4 + i] = uint8_t(c >> (8 * i));
}
std::string signature(const Frame &f) {
  SHA256 h;
  for (auto &p : f.planes)
    h.update(p);
  for (auto &p : f.hud) {
    auto b = word_bytes(p.words);
    h.update(b);
  }
  auto display = word_bytes(f.display);
  h.update(display);
  return hex(h.finish());
}
int main(int argc, char **argv) {
  try {
    need(argc == 2, "fuzz_native fixture directory");
    std::string dir = argv[1];
    if (dir.back() != '/')
      dir += '/';
    std::ifstream index(dir + "index.tsv");
    std::string line;
    std::vector<Bytes> packets;
    while (packets.size() < 2 && std::getline(index, line)) {
      std::stringstream ss(line);
      std::string skip, path;
      std::getline(ss, skip, '\t');
      std::getline(ss, skip, '\t');
      std::getline(ss, path, '\t');
      packets.push_back(readfile(dir + path));
    }
    need(packets.size() == 2, "fuzz seed packets");
    Decoder base;
    base.receive(packets[0]);
    auto prior = base.state();
    auto before = signature(*prior);
    Decoder expected = base;
    auto valid = expected.receive(packets[1]);
    auto target = signature(*valid);
    std::mt19937 rng(6903);
    unsigned accepted = 0, rejected = 0;
    for (unsigned trial = 0; trial < 512; trial++) {
      Bytes b = packets[1];
      unsigned mode = trial % 8;
      size_t inner = 76, nb = field(b, 68), hud = inner + nb, nh = field(b, 72),
             first = inner + 60 + field(b, inner + 40) + field(b, inner + 44),
             plane = field(b, inner + 48);
      auto flip = [&](size_t start, size_t length) {
        need(length > 0, "fuzz mutation region");
        size_t p = start + rng() % length;
        b[p] ^= uint8_t(1u << (rng() % 8));
      };
      if (mode == 0)
        flip(0, b.size());
      else if (mode == 1) {
        flip(0, 76);
        reseal(b, 0, b.size());
      } else if (mode == 2) {
        flip(inner + 60, nb - 64);
        reseal(b, inner, nb);
        reseal(b, 0, b.size());
      } else if (mode == 3) {
        flip(first + 1, plane - 5);
        reseal(b, first + 1, plane - 1);
        reseal(b, inner, nb);
        reseal(b, 0, b.size());
      } else if (mode == 4) {
        flip(hud, nh - 4);
        reseal(b, hud, nh);
        reseal(b, 0, b.size());
      } else if (mode == 5) {
        size_t patch = hud + 106, n = field(b, hud + 54);
        flip(patch, n - 4);
        reseal(b, patch, n);
        reseal(b, hud, nh);
        reseal(b, 0, b.size());
      } else if (mode == 6) {
        size_t count = 1 + rng() % std::min<size_t>(64, b.size() - 4);
        b.resize(b.size() - count);
        reseal(b, 0, b.size());
      } else {
        flip(inner + 60, 338);
        reseal(b, inner, nb);
        reseal(b, 0, b.size());
      }
      Decoder fork = base;
      bool failed = false;
      try {
        auto out = fork.receive(b);
        need(out->id == 1 && out->reference_id == 0 &&
                 signature(*out) == target,
             "accepted mutation changed bound canonical/HUD/display");
        accepted++;
      } catch (const std::runtime_error &) {
        failed = true;
        rejected++;
      }
      if (failed)
        need(fork.state() == prior, "fuzz failure published candidate");
      need(base.state() == prior && signature(*prior) == before,
           "fuzz changed source/reference");
    }
    std::cout << "{\"seed\":6903,\"mutation_trials\":512,\"rejected\":"
              << rejected << ",\"accepted_bound_identical\":" << accepted
              << ",\"source_and_failed_publications_unchanged\":true}\n";
    return 0;
  } catch (const std::exception &e) {
    std::cerr << "ERROR: " << e.what() << "\n";
    return 1;
  }
}
