#include "decoder.hpp"
#include <chrono>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
using namespace cu66;
Bytes load(const std::string &path) {
  std::ifstream f(path, std::ios::binary);
  need(bool(f), "worker fixture open");
  return Bytes(std::istreambuf_iterator<char>(f), {});
}
int main() {
  try {
    std::cout << std::setprecision(17);
    Decoder decoder, saved;
    Bytes packet;
    bool prepared = false, trial_ready = false;
    std::string line;
    while (std::getline(std::cin, line)) {
      std::stringstream ss(line);
      std::string command;
      ss >> command;
      if (command == "RESET") {
        decoder = Decoder();
        prepared = trial_ready = false;
        std::cout << "{\"reset\":true}" << std::endl;
      } else if (command == "PREPARE") {
        std::string path;
        ss >> path;
        packet = load(path);
        prepared = true;
        trial_ready = false;
        std::cout << "{\"prepared_bytes\":" << packet.size() << "}"
                  << std::endl;
      } else if (command == "TRIAL") {
        need(prepared, "worker not prepared");
        Decoder fork = decoder;
        auto begin = std::chrono::steady_clock::now();
        auto out = fork.receive(packet);
        auto end = std::chrono::steady_clock::now();
        double ms =
            std::chrono::duration<double, std::milli>(end - begin).count();
        saved = fork;
        trial_ready = true;
        SHA256 y;
        for (auto &p : out->planes)
          y.update(p);
        Bytes words;
        for (auto &p : out->hud) {
          auto raw = word_bytes(p.words);
          words.insert(words.end(), raw.begin(), raw.end());
        }
        auto display = word_bytes(out->display);
        std::cout << "{\"id\":" << out->id
                  << ",\"key\":" << (out->key ? "true" : "false")
                  << ",\"receive_and_render_ms\":" << ms
                  << ",\"canonical_tag\":\"" << hex(out->canonical_tag)
                  << "\",\"canonical_yuv_u8_sha256\":\"" << hex(y.finish())
                  << "\",\"hud_words_u16le_sha256\":\"" << hex(sha256(words))
                  << "\",\"display_rgb565_u16le_sha256\":\""
                  << hex(sha256(display)) << "\"}" << std::endl;
      } else if (command == "COMMIT") {
        need(trial_ready, "worker no candidate");
        decoder = saved;
        prepared = trial_ready = false;
        std::cout << "{\"committed\":" << decoder.state()->id << "}"
                  << std::endl;
      } else if (command == "QUIT") {
        std::cout << "{\"quit\":true}" << std::endl;
        return 0;
      } else
        need(false, "worker unknown command");
    }
    return 0;
  } catch (const std::exception &e) {
    std::cerr << "ERROR: " << e.what() << "\n";
    return 1;
  }
}
