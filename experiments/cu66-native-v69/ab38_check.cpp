#include "entropy.hpp"
#include <chrono>
#include <fstream>
#include <iostream>
#include <sstream>
using namespace cu66;
int main(int argc, char **argv) {
  try {
    need(argc == 2, "ab38_check planes.tsv");
    std::string index = argv[1];
    auto base = index.substr(0, index.find_last_of('/') + 1);
    std::ifstream input(index);
    need(bool(input), "AB index open");
    std::string line;
    unsigned planes = 0;
    uint64_t tiles = 0;
    double ms = 0;
    while (std::getline(input, line)) {
      std::stringstream ss(line);
      std::string path, n, bw, expected;
      need(bool(std::getline(ss, path, '\t')) &&
               bool(std::getline(ss, n, '\t')) &&
               bool(std::getline(ss, bw, '\t')) &&
               bool(std::getline(ss, expected)),
           "AB index fields");
      unsigned blocks = unsigned(std::stoul(n)),
               width = unsigned(std::stoul(bw));
      std::ifstream file(base + path, std::ios::binary);
      need(bool(file), "AB fixture open");
      Bytes packet(std::istreambuf_iterator<char>(file), {});
      auto start = std::chrono::steady_clock::now();
      auto coeff = decode_ab38(packet, blocks, width);
      auto end = std::chrono::steady_clock::now();
      Bytes raw;
      raw.reserve(coeff.size() * 2);
      for (auto c : coeff)
        put16(raw, uint16_t(c));
      need(hex(sha256(raw)) == expected,
           "exact encoded-order coefficient fixture");
      planes++;
      tiles += blocks;
      ms += std::chrono::duration<double, std::milli>(end - start).count();
    }
    std::cout << "{\"arithmetic_planes\":" << planes
              << ",\"exact_coefficient_tiles\":" << tiles
              << ",\"total_native_entropy_ms\":" << ms << "}\n";
    return 0;
  } catch (const std::exception &e) {
    std::cerr << "ERROR: " << e.what() << "\n";
    return 1;
  }
}
