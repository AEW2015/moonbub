#include "decoder.hpp"
#include <fstream>
#include <iostream>
#include <sstream>
using namespace cu66;
Bytes readfile(const std::string &path) {
  std::ifstream f(path, std::ios::binary);
  need(bool(f), "fixture open");
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
std::string fingerprint(const std::shared_ptr<const Frame> &f) {
  if (!f)
    return "empty";
  Bytes b;
  put32(b, f->id);
  put32(b, f->reference_id);
  b.push_back(f->key);
  b.insert(b.end(), f->canonical_tag.begin(), f->canonical_tag.end());
  for (auto &p : f->planes)
    b.insert(b.end(), p.begin(), p.end());
  for (auto &p : f->hud) {
    for (auto x : p.rect)
      put16(b, x);
    auto x = word_bytes(p.words);
    b.insert(b.end(), x.begin(), x.end());
  }
  auto d = word_bytes(f->display);
  b.insert(b.end(), d.begin(), d.end());
  return hex(sha256(b));
}
template <class F> void fails(F &&f) {
  bool failed = false;
  try {
    f();
  } catch (const std::runtime_error &) {
    failed = true;
  }
  need(failed, "malformed operation accepted");
}
int main(int argc, char **argv) {
  try {
    need(argc == 2, "test_native fixture directory");
    std::string dir = argv[1];
    if (dir.back() != '/')
      dir += '/';
    const std::string abc = "abc", digits = "123456789";
    need(hex(sha256(
             {reinterpret_cast<const uint8_t *>(abc.data()), abc.size()})) ==
             "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
         "SHA256 known answer");
    need(crc32({reinterpret_cast<const uint8_t *>(digits.data()),
                digits.size()}) == 0xcbf43926u,
         "CRC32 known answer");
    std::ifstream index(dir + "index.tsv");
    std::string line;
    std::vector<Bytes> packets;
    while (packets.size() < 25 && std::getline(index, line)) {
      auto row = split(line, '\t');
      packets.push_back(readfile(dir + row[2]));
    }
    need(packets.size() == 25, "fixture keys");
    Decoder decoder;
    auto key = decoder.receive(packets[0]);
    auto prior = decoder.state();
    auto signature = fingerprint(prior);
    fails([&] { decoder.receive(packets[0]); });
    need(decoder.state() == prior && fingerprint(decoder.state()) == signature,
         "replay atomicity");
    Decoder missing;
    fails([&] { missing.receive(packets[1]); });
    need(!missing.state(), "missing reference atomicity");
    std::ifstream negative(dir + "negative.tsv");
    unsigned rejected = 0;
    while (std::getline(negative, line)) {
      auto row = split(line, '\t');
      need(row.size() == 2, "negative fields");
      auto bad = readfile(dir + row[1]);
      fails([&] { decoder.receive(bad); });
      need(decoder.state() == prior &&
               fingerprint(decoder.state()) == signature,
           "negative candidate changed published state");
      std::cout << "{\"rejected\":\"" << row[0]
                << "\",\"published_state_unchanged\":true}\n";
      rejected++;
    }
    need(rejected >= 20, "negative cases exercised");
    auto p = decoder.receive(packets[1]);
    need(p->id == 1 && prior->id == 0 && fingerprint(prior) == signature,
         "old returned object ownership");
    auto recovered = decoder.receive(packets[24]);
    need(recovered->key && recovered->id == 24, "independent key recovery");
    Capabilities unsupported;
    unsupported.zero_motion_only = false;
    fails([&] { Decoder x(unsupported); });
    std::cout << "{\"known_answer_tests\":2,\"malformed_or_unsupported_packets_"
                 "rejected\":"
              << rejected
              << ",\"late_failure_atomic_state\":true,\"key_recovery\":true,"
                 "\"owned_const_publication\":true}\n";
    return 0;
  } catch (const std::exception &e) {
    std::cerr << "ERROR: " << e.what() << "\n";
    return 1;
  }
}
