#include "hud.hpp"
#include <fstream>
#include <iostream>
#include <sstream>
using namespace cu66;
Bytes readfile(const std::string &path) {
  std::ifstream f(path, std::ios::binary);
  need(bool(f), "HUD fixture open");
  return Bytes(std::istreambuf_iterator<char>(f), {});
}
int main(int argc, char **argv) {
  try {
    need(argc == 2, "test_hud_directed hud-directed.tsv");
    std::string index = argv[1],
                base = index.substr(0, index.find_last_of('/') + 1), line;
    std::ifstream input(index);
    need(bool(input), "HUD index open");
    unsigned cases = 0;
    while (std::getline(input, line)) {
      std::stringstream ss(line);
      std::vector<std::string> p;
      std::string item;
      while (std::getline(ss, item, '\t'))
        p.push_back(item);
      need(p.size() == 9, "HUD index fields");
      unsigned kind = unsigned(std::stoul(p[1]));
      std::array<uint16_t, 4> rect;
      for (unsigned i = 0; i < 4; i++) {
        auto n = std::stoul(p[4 + i]);
        need(n <= 720, "HUD coordinate bound");
        rect[i] = uint16_t(n);
      }
      Patch reference;
      reference.rect = rect;
      const Patch *ref = nullptr;
      if (p[3] != "-") {
        Bytes raw = readfile(base + p[3]);
        need(raw.size() == size_t(rect[2]) * rect[3] * 2, "HUD reference size");
        Reader r(raw);
        while (r.pos < r.v.n)
          reference.words.push_back(r.u16());
        ref = &reference;
      }
      auto packet = readfile(base + p[2]);
      auto words = kind == 1 ? decode_full_patch(packet, rect)
                             : decode_patch(packet, ref, rect[2], rect[3]);
      need(hex(sha256(word_bytes(words))) == p[8],
           "directed native HUD word parity");
      std::cout << "{\"name\":\"" << p[0]
                << "\",\"exact_RGB565_words\":" << words.size() << "}\n";
      cases++;
    }
    std::cout << "{\"native_directed_HUD_cases\":" << cases << "}\n";
    return 0;
  } catch (const std::exception &e) {
    std::cerr << "ERROR: " << e.what() << "\n";
    return 1;
  }
}
