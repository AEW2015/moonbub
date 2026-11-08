#include "decoder.hpp"
#include <chrono>
#include <fstream>
#include <iostream>
#include <numeric>
#include <sstream>
using namespace cu66;
Bytes readfile(const std::string &path) {
  std::ifstream f(path, std::ios::binary);
  need(bool(f), "fixture file open");
  return Bytes(std::istreambuf_iterator<char>(f), {});
}
std::vector<std::string> split(const std::string &s, char sep) {
  std::vector<std::string> v;
  std::stringstream ss(s);
  std::string x;
  while (std::getline(ss, x, sep))
    v.push_back(x);
  return v;
}
std::string state_hash(const std::shared_ptr<const Frame> &f) {
  if (!f)
    return "empty";
  SHA256 h;
  for (auto &p : f->planes)
    h.update(p);
  for (auto &p : f->hud) {
    auto b = word_bytes(p.words);
    h.update(b);
  }
  auto d = word_bytes(f->display);
  h.update(d);
  return hex(h.finish());
}
int main(int argc, char **argv) {
  try {
    need(argc >= 2, "usage native_decoder index.tsv [rounds=3]");
    std::ifstream input(argv[1]);
    need(bool(input), "index open");
    std::string base = argv[1];
    base = base.substr(0, base.find_last_of('/') + 1);
    auto requested_reps = argc > 2 ? std::stoull(argv[2]) : 3;
    need(requested_reps <= 20, "repeat bound");
    unsigned reps = unsigned(requested_reps);
    need(reps && reps <= 20, "repeat bound");
    Decoder decoder;
    int lastcase = -1;
    unsigned frames = 0, keys = 0;
    double total = 0;
    std::string line;
    while (std::getline(input, line)) {
      auto parts = split(line, '\t');
      need(parts.size() == 6, "index6fields");
      int caseid = std::stoi(parts[0]);
      auto requested_fid = std::stoull(parts[1]);
      need(requested_fid < 0xffffffffu, "frame ID range");
      unsigned fid = unsigned(requested_fid);
      if (caseid != lastcase) {
        decoder = Decoder();
        lastcase = caseid;
      }
      auto packet = readfile(base + parts[2]);
      std::vector<double> times;
      Decoder accepted;
      std::shared_ptr<const Frame> out;
      for (unsigned rep = 0; rep < reps; rep++) {
        Decoder fork = decoder;
        auto start = std::chrono::steady_clock::now();
        out = fork.receive(packet);
        auto end = std::chrono::steady_clock::now();
        times.push_back(
            std::chrono::duration<double, std::milli>(end - start).count());
        accepted = fork;
      }
      need(out->id == fid, "fixture frame ID");
      SHA256 y;
      for (auto &p : out->planes)
        y.update(p);
      need(hex(y.finish()) == parts[3], "golden canonical planes");
      Bytes words;
      for (auto &p : out->hud) {
        auto b = word_bytes(p.words);
        words.insert(words.end(), b.begin(), b.end());
      }
      need(hex(sha256(words)) == parts[4], "golden HUD words");
      auto display = word_bytes(out->display);
      need(hex(sha256(display)) == parts[5], "golden RGB565 display");
      decoder = accepted;
      auto sorted = times;
      std::sort(sorted.begin(), sorted.end());
      double median = sorted[sorted.size() / 2];
      total += median;
      frames++;
      keys += out->key;
      std::cout << "{\"case\":" << caseid << ",\"id\":" << fid
                << ",\"native_receive_ms\":[";
      for (unsigned i = 0; i < times.size(); i++)
        std::cout << (i ? "," : "") << times[i];
      std::cout << "],\"median_ms\":" << median << ",\"state_sha256\":\""
                << state_hash(out) << "\"}\n";
    }
    std::cout << "{\"frames\":" << frames << ",\"keys\":" << keys
              << ",\"mean_median_native_receive_ms\":" << total / frames
              << ",\"physical_30fps_proven\":false,\"native_decoder\":true,"
                 "\"zero_motion_only\":true}\n";
    return 0;
  } catch (const std::exception &e) {
    std::cerr << "ERROR: " << e.what() << "\n";
    return 1;
  }
}
