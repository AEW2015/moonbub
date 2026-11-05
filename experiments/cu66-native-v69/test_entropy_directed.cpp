#include "entropy.hpp"
#include <fstream>
#include <iostream>
#include <sstream>
using namespace cu66;
int main(int argc, char **argv) {
  try {
    need(argc == 2, "test_entropy_directed entropy-directed.tsv");
    std::string index = argv[1],
                base = index.substr(0, index.find_last_of('/') + 1), line;
    std::ifstream input(index);
    need(bool(input), "directed index open");
    unsigned valid = 0, rejected = 0;
    while (std::getline(input, line)) {
      std::stringstream ss(line);
      std::vector<std::string> parts;
      std::string item;
      while (std::getline(ss, item, '\t'))
        parts.push_back(item);
      need(parts.size() == 7, "directed fields");
      std::ifstream file(base + parts[1], std::ios::binary);
      need(bool(file), "directed fixture open");
      Bytes packet(std::istreambuf_iterator<char>(file), {});
      unsigned blocks = unsigned(std::stoul(parts[2])),
               bw = unsigned(std::stoul(parts[3])),
               dispatch = unsigned(std::stoul(parts[4]));
      bool invalid = parts[5] == "1", failed = false;
      std::vector<int16_t> coeff;
      try {
        need(dispatch == 5 || dispatch == 6, "dispatch capability");
        need(dispatch != 6 || bw == 1, "compact geometry capability");
        coeff = decode_ab38(packet, blocks, bw);
      } catch (const std::runtime_error &) {
        failed = true;
      }
      need(failed == invalid, "directed accept/reject mismatch");
      if (failed)
        rejected++;
      else {
        Bytes raw;
        for (auto c : coeff)
          put16(raw, uint16_t(c));
        need(hex(sha256(raw)) == parts[6], "directed exact coefficient values");
        valid++;
      }
      std::cout << "{\"name\":\"" << parts[0]
                << "\",\"rejected\":" << (failed ? "true" : "false") << "}\n";
    }
    std::cout << "{\"directed_valid_entropy_packets\":" << valid
              << ",\"directed_rejected_entropy_packets\":" << rejected << "}\n";
    return 0;
  } catch (const std::exception &e) {
    std::cerr << "ERROR: " << e.what() << "\n";
    return 1;
  }
}
