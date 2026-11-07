#include "../../cu66-native-v69/decoder.hpp"
#include <chrono>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
using namespace cu66;

static Bytes load(const std::string &path) {
  std::ifstream f(path, std::ios::binary);
  need(bool(f), "packet open");
  return Bytes(std::istreambuf_iterator<char>(f), {});
}
static std::vector<std::string> split(const std::string &line) {
  std::vector<std::string> out;
  std::stringstream stream(line);
  std::string part;
  while (std::getline(stream, part, '\t')) out.push_back(part);
  return out;
}
static Bytes canonical(const Frame &f) {
  Bytes b;
  for (const auto &p : f.planes) b.insert(b.end(), p.begin(), p.end());
  return b;
}
static Bytes hud_bytes(const Frame &f) {
  Bytes b;
  put16(b, 720); put16(b, 480); b.push_back(uint8_t(f.hud.size()));
  for (const auto &p : f.hud) {
    for (auto r : p.rect) put16(b, r);
    auto words = word_bytes(p.words);
    b.insert(b.end(), words.begin(), words.end());
  }
  return b;
}
static std::string fingerprint(const std::shared_ptr<const Frame> &f) {
  if (!f) return "empty";
  Bytes b;
  put32(b, f->id); put32(b, f->reference_id); b.push_back(f->key);
  b.insert(b.end(), f->canonical_tag.begin(), f->canonical_tag.end());
  auto y = canonical(*f), h = hud_bytes(*f), d = word_bytes(f->display);
  b.insert(b.end(), y.begin(), y.end());
  b.insert(b.end(), h.begin(), h.end());
  b.insert(b.end(), d.begin(), d.end());
  return hex(sha256(b));
}
static void repair_crc(Bytes &b) {
  need(b.size() >= 4, "mutation CRC bounds");
  auto crc = crc32(View(b).sub(0, b.size() - 4));
  for (unsigned i = 0; i < 4; ++i) b[b.size() - 4 + i] = uint8_t(crc >> (8*i));
}
static void reject(Decoder &decoder, const Bytes &bad, const char *name) {
  const auto old = decoder.state();
  const auto before = fingerprint(old);
  bool rejected = false;
  try { decoder.receive(bad); } catch (const std::runtime_error &) { rejected = true; }
  need(rejected, name);
  need(decoder.state() == old && fingerprint(old) == before,
       "malformed packet changed published state");
}
static unsigned adversarial(Decoder &decoder, const Bytes &packet) {
  need(packet.size() >= 88, "fresh packet outer header");
  auto bad = packet;
  bad.back() ^= 1;
  reject(decoder, bad, "CRC corruption accepted");
  bad = packet; bad.resize(bad.size() - 1);
  reject(decoder, bad, "truncation accepted");
  bad = packet; bad[0] = 'C'; bad[1] = 'S'; bad[2] = '8'; bad[3] = '8'; repair_crc(bad);
  reject(decoder, bad, "unsupported CS88 wrapper accepted");
  bad = packet; bad[4] = 2; repair_crc(bad);
  reject(decoder, bad, "unsupported CU66 version accepted");
  bad = packet; bad[5] = 0x80; repair_crc(bad);
  reject(decoder, bad, "unsupported flags accepted");
  bad = packet; bad[6] = 26; bad[7] = 0; repair_crc(bad);
  reject(decoder, bad, "unsupported epoch accepted");
  bad = packet; bad[36] ^= 1; repair_crc(bad);
  reject(decoder, bad, "reference identity corruption accepted");
  // Output-tag mutation reaches reconstruction before failing the canonical tag.
  bad = packet; bad[52] ^= 1; repair_crc(bad);
  reject(decoder, bad, "late canonical output corruption accepted");
  // Preserve the outer CRC so invalid HUD is tested after valid base decode.
  bad = packet; bad[bad.size() - 5] ^= 1; repair_crc(bad);
  reject(decoder, bad, "late HUD corruption accepted");
  if ((packet[5] & 1) == 0) {
    Decoder missing;
    reject(missing, packet, "dependent frame without reference accepted");
    return 10;
  }
  return 9;
}
static void dump(const std::string &path, const Bytes &b) {
  std::ofstream out(path, std::ios::binary);
  need(bool(out), "output open");
  out.write(reinterpret_cast<const char *>(b.data()), b.size());
  need(bool(out), "output write");
}
int main(int argc, char **argv) {
  try {
    need(argc == 2, "usage: native_decoder causal_manifest.tsv");
    const std::string abc = "abc", digits = "123456789";
    need(hex(sha256({reinterpret_cast<const uint8_t *>(abc.data()), abc.size()})) ==
      "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad", "SHA256 KAT");
    need(crc32({reinterpret_cast<const uint8_t *>(digits.data()), digits.size()}) == 0xcbf43926u,
      "CRC32 KAT");
    std::ifstream manifest(argv[1]);
    need(bool(manifest), "manifest open");
    std::cout << std::setprecision(17);
    Decoder decoder;
    std::string clip, line;
    std::shared_ptr<const Frame> first;
    std::string first_signature;
    unsigned total = 0, rejects = 0;
    while (std::getline(manifest, line)) {
      auto row = split(line);
      need(row.size() == 8, "manifest fields");
      if (row[0] != clip) {
        decoder = Decoder(); clip = row[0]; first.reset();
      }
      const auto packet = load(row[2]); // Input I/O excluded from receive timing.
      unsigned rejected = adversarial(decoder, packet);
      const auto prior = decoder.state();
      const auto signature = fingerprint(prior);
      const auto begin = std::chrono::steady_clock::now();
      const auto frame = decoder.receive(packet);
      const auto end = std::chrono::steady_clock::now();
      const double ms = std::chrono::duration<double, std::milli>(end - begin).count();
      // Goldens, serialization, hashing, adversarial checks and I/O are untimed.
      auto y = canonical(*frame), h = hud_bytes(*frame), d = word_bytes(frame->display);
      const auto ys = hex(sha256(y)), hs = hex(sha256(h)), ds = hex(sha256(d));
      need(std::to_string(frame->id) == row[1], "frame id parity");
      need(ys == row[3], "canonical golden parity");
      need(hs == row[4], "HUD golden parity");
      need(ds == row[5], "RGB565 golden parity");
      need(row[6] == "-" || hex(frame->canonical_tag) == row[6], "canonical tag parity");
      need(prior != frame && fingerprint(prior) == signature, "prior publication mutated");
      if (first) need(fingerprint(first) == first_signature, "retained publication mutated");
      else { first = frame; first_signature = fingerprint(first); }
      reject(decoder, packet, "replay accepted"); ++rejected;
      if (row[7] != "-") {
        dump(row[7] + ".rgb565", d);
      }
      std::cout << "{\"clip_id\":\"" << clip << "\",\"frame_id\":" << frame->id
        << ",\"key\":" << (frame->key ? "true" : "false")
        << ",\"packet_bytes\":" << packet.size()
        << ",\"receive_to_published_rgb565_ms\":" << ms
        << ",\"canonical_sha256\":\"" << ys << "\",\"hud_sha256\":\"" << hs
        << "\",\"rgb565_sha256\":\"" << ds << "\",\"canonical_tag\":\""
        << hex(frame->canonical_tag) << "\",\"rejections\":" << rejected
        << ",\"rejected_published_state_unchanged\":true,\"post_reject_valid_same_context\":true,\"immutable_publication\":true}"
        << std::endl;
      ++total; rejects += rejected;
    }
    need(total > 0, "empty causal manifest");
    std::cerr << "{\"accepted\":" << total << ",\"rejected\":" << rejects
      << ",\"known_answer_tests\":2,\"pass\":true}\n";
    return 0;
  } catch (const std::exception &e) {
    std::cerr << "ERROR: " << e.what() << "\n"; return 1;
  }
}
