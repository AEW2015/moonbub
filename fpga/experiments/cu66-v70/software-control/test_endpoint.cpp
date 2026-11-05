#include "hud_endpoint.hpp"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>

using cu66::Bytes;
using cu66::Tag;
using cu66::View;
using hc70::Message;
static void need(bool b, const std::string &s) {
  if (!b)
    throw std::runtime_error(s);
}
static Bytes load(const std::filesystem::path &p) {
  std::ifstream f(p, std::ios::binary);
  need(bool(f), "openinput");
  return {std::istreambuf_iterator<char>(f), {}};
}
static void save(const std::filesystem::path &p, const Bytes &b) {
  std::ofstream f(p, std::ios::binary);
  need(bool(f), "openoutput");
  f.write(reinterpret_cast<const char *>(b.data()), std::streamsize(b.size()));
  need(bool(f), "writeoutput");
}
static std::vector<std::string> split(const std::string &s) {
  std::stringstream r(s);
  std::string x;
  std::vector<std::string> out;
  while (std::getline(r, x, '\t'))
    out.push_back(x);
  return out;
}
struct Slice {
  uint32_t id, rid;
  bool key;
  Bytes hud;
};
static Slice slice(const Bytes &p) {
  cu66::Reader r(View(p).sub(8, 8));
  uint32_t id = r.u32(), rid = r.u32();
  cu66::Reader n(View(p).sub(68, 8));
  unsigned base = n.u32(), length = n.u32();
  auto v = View(p).sub(76 + base, length);
  return {id, rid, bool(p.at(5) & 1), Bytes(v.p, v.p + v.n)};
}
static Message request(uint8_t op, uint64_t gen, uint32_t fid = 0,
                       uint32_t rid = 0xffffffffu, uint32_t arg = 0,
                       Bytes payload = {}) {
  return {false, op, gen, fid, rid, arg, std::move(payload)};
}
static Tag source_tag(const Slice &s) {
  cu66::Reader r(View(s.hud).sub(38, 16));
  return r.tag();
}
static Tag sink_tag(const Bytes &raw) {
  cu66::Reader r(raw);
  std::vector<cu66::Patch> p;
  for (unsigned n = 0; n < 4; n++) {
    cu66::Patch x;
    for (unsigned i = 0; i < 4; i++)
      x.rect[i] = cu66::RECTS[n][i];
    for (unsigned i = 0; i < unsigned(x.rect[2]) * x.rect[3]; i++)
      x.words.push_back(r.u16());
    p.push_back(std::move(x));
  }
  r.end();
  return cu66::hud_tag(p);
}
static std::string raw_hash(const Bytes &raw) {
  cu66::SHA256 h;
  h.update(raw);
  return cu66::hex(h.finish());
}
struct Tester {
  hc70::HudEndpoint endpoint;
  uint64_t generation = 0, commands = 0;
  unsigned malformed = 0;
  std::filesystem::path artifacts;
  bool record = false;
  Message call(const Message &m, hc70::Code expected = hc70::Code::Ok) {
    auto wire = hc70::encode(m);
    auto reply_wire = endpoint.transact(wire);
    auto response = hc70::decode(reply_wire);
    need(response.response && response.opcode == m.opcode &&
             response.generation == m.generation &&
             response.frame_id == m.frame_id &&
             response.reference_id == m.reference_id,
         "responseidentity");
    need(response.argument == uint32_t(expected),
         "resultopcode=" + std::to_string(m.opcode) +
             " expected=" + std::to_string(uint32_t(expected)) +
             " got=" + std::to_string(response.argument));
    commands++;
    if (record) {
      save(artifacts / ("request-op" + std::to_string(m.opcode) + ".bin"),
           wire);
      save(artifacts / ("response-op" + std::to_string(m.opcode) + ".bin"),
           reply_wire);
    }
    std::fill(wire.begin(), wire.end(), uint8_t(0));
    return response;
  }
  Bytes status() { return call(request(2, generation)).payload; }
  void reset() {
    call(request(7, ++generation, 0, 0xffffffffu, 1));
    need(!endpoint.accepted(), "resetnotempty");
  }
  Bytes read(const Slice &s, uint64_t gen) {
    Bytes p;
    cu66::put32(p, 0);
    cu66::put32(p, 21120);
    auto reply = call(request(3, gen, s.id, s.rid, 0, p));
    need(reply.payload.size() == 42240, "READwholewordsize");
    need(sink_tag(reply.payload) == source_tag(s), "actualREADsinktag");
    return reply.payload;
  }
  void ack_commit(const Slice &s, uint64_t gen, const Bytes &raw) {
    Bytes p;
    cu66::put32(p, 21120);
    auto tag = sink_tag(raw);
    p.insert(p.end(), tag.begin(), tag.end());
    call(request(4, gen, s.id, s.rid, 1, p));
    auto command = request(5, gen, s.id, s.rid);
    auto reply = call(command);
    auto retry = call(command);
    need(hc70::encode(reply) == hc70::encode(retry), "lostCOMMITreplyretry");
    auto a = endpoint.accepted();
    need(a && a->id == s.id && a->generation == gen && a->tag == tag,
         "committedactualHUD");
  }
  void malformed_frame(const Bytes &wire) {
    auto before = status();
    auto accepted = endpoint.accepted();
    bool rejected = false;
    try {
      endpoint.transact(wire);
    } catch (const hc70::ProtocolError &) {
      rejected = true;
    }
    need(rejected, "malformedwireaccepted");
    need(status() == before && endpoint.accepted() == accepted,
         "parsefailuremutatedstate");
    malformed++;
  }
  void bad_frames(const Slice &s) {
    auto m =
        request(1, generation + 100000, s.id, s.rid, s.key ? 1u : 0u, s.hud);
    auto valid = hc70::encode(m);
    auto renew = [](Bytes &b) {
      b.resize(b.size() - 4);
      cu66::put32(b, cu66::crc32(b));
    };
    for (unsigned offset : {0u, 4u, 5u, 6u}) {
      auto b = valid;
      b[offset] = offset == 0 ? 'X' : offset == 4 ? 2 : offset == 5 ? 8 : 1;
      renew(b);
      malformed_frame(b);
    }
    auto b = valid;
    b[8] = 0xff;
    b[9] = 0xff;
    b[10] = 0xff;
    b[11] = 0x7f;
    renew(b);
    malformed_frame(b);
    b = valid;
    b.resize(12);
    malformed_frame(b);
    b = valid;
    b.pop_back();
    malformed_frame(b);
    b = valid;
    b.push_back(0);
    malformed_frame(b);
    for (unsigned offset : {12u, 32u}) {
      b = valid;
      b[offset] ^= 1;
      malformed_frame(b);
    }
    b = valid;
    b.back() ^= 1;
    malformed_frame(b);
    m.response = true;
    malformed_frame(hc70::encode(m));
    b = hc70::encode(request(7, generation + 100000, 0, 0xffffffffu, 1));
    b[28] = 0;
    renew(b);
    malformed_frame(b);
  }
};
int main(int argc, char **argv) {
  try {
    if (argc == 4 && std::string(argv[1]) == "--codec") {
      auto raw = load(argv[2]);
      try {
        save(argv[3], hc70::encode(hc70::decode(raw)));
        std::cout << "CODEC_ROUNDTRIP_PASS bytes=" << raw.size() << std::endl;
        return 0;
      } catch (const hc70::ProtocolError &e) {
        std::cerr << "CODEC_REJECT " << e.what() << std::endl;
        return 2;
      }
    }
    need(argc == 3, "test_endpoint native_directory artifact_directory");
    std::filesystem::path native = argv[1];
    Tester t;
    t.artifacts = argv[2];
    std::filesystem::create_directories(t.artifacts);
    std::ifstream index(native / "index.tsv");
    need(bool(index), "indexopen");
    std::string line;
    int previous = -1;
    unsigned frames = 0, keys = 0;
    Slice first{}, second{}, recovery{};
    while (std::getline(index, line)) {
      auto f = split(line);
      need(f.size() == 6, "indexfields");
      int cohort = std::stoi(f[0]);
      if (cohort != previous) {
        t.reset();
        previous = cohort;
      }
      auto s = slice(load(native / f[2]));
      if (cohort == 0 && s.id == 0)
        first = s;
      if (cohort == 0 && s.id == 1)
        second = s;
      if (cohort == 0 && s.id == 24)
        recovery = s;
      auto prior = t.endpoint.accepted();
      auto gen = ++t.generation;
      t.record = frames == 0;
      t.call(request(1, gen, s.id, s.rid, s.key ? 1u : 0u, s.hud));
      auto st = t.status();
      need(st.size() == 72 && st[0] == 1 && (st[1] & 12) == 4,
           "preparedstatus");
      need(t.endpoint.accepted() == prior, "prepareadvancedaccepted");
      auto raw = t.read(s, gen);
      need(raw_hash(raw) == f[4], "exactsourceHUDwords");
      t.ack_commit(s, gen, raw);
      t.record = false;
      if (frames == 0)
        t.bad_frames(second);
      frames++;
      keys += s.key;
    }
    need(frames == 457 && keys == 20, "corpuscoverage");
    t.reset();
    auto gen = ++t.generation;
    t.call(request(1, gen, first.id, first.rid, 1, first.hud));
    auto raw = t.read(first, gen);
    t.ack_commit(first, gen, raw);
    gen = ++t.generation;
    t.call(request(1, gen, second.id, second.rid, 0, second.hud));
    auto accepted = t.endpoint.accepted();
    t.call(request(5, gen, second.id, second.rid), hc70::Code::Rejected);
    t.call(request(1, gen + 1, second.id, second.rid, 0, second.hud),
           hc70::Code::Busy);
    Bytes ack;
    cu66::put32(ack, 21120);
    auto tag = source_tag(second);
    ack.insert(ack.end(), tag.begin(), tag.end());
    t.call(request(4, gen, second.id, second.rid, 0, ack),
           hc70::Code::Rejected);
    t.call(request(4, gen, second.id, second.rid + 1, 1, ack),
           hc70::Code::Rejected);
    auto abort = request(6, gen, second.id, second.rid);
    t.call(abort);
    t.call(abort);
    need(t.endpoint.accepted() == accepted, "lostABORTreplychangedaccepted");
    auto newgen = ++t.generation;
    t.call(request(1, newgen, second.id, second.rid, 0, second.hud));
    t.call(abort);
    raw = t.read(second, newgen);
    t.ack_commit(second, newgen, raw);
    t.call(request(1, gen, second.id, second.rid, 0, second.hud),
           hc70::Code::Stale);
    accepted = t.endpoint.accepted();
    auto bad = recovery;
    bad.hud.back() ^= 1;
    gen = ++t.generation;
    t.call(request(1, gen, bad.id, bad.rid, 1, bad.hud),
           hc70::Code::DecodeRejected);
    need(t.endpoint.accepted() == accepted, "nestedHUfailurechangedaccepted");
    t.call(request(6, gen, bad.id, bad.rid));
    t.call(request(6, gen, bad.id, bad.rid));
    t.call(request(7, 1, 0, 0xffffffffu, 1), hc70::Code::Rejected);
    need(t.endpoint.accepted() == accepted, "staleresetchangedaccepted");
    gen = ++t.generation;
    t.call(request(1, gen, recovery.id, recovery.rid, 2, recovery.hud),
           hc70::Code::Rejected);
    need(t.endpoint.accepted() == accepted, "badkeypolicychangedaccepted");
    t.call(request(1, gen, recovery.id, recovery.rid, 1, recovery.hud));
    raw = t.read(recovery, gen);
    t.ack_commit(recovery, gen, raw);
    // Read bounds are checked before slicing; no overflow may wrap into a
    // cache.
    gen = ++t.generation;
    t.call(request(1, gen, recovery.id, recovery.rid, 1, recovery.hud),
           hc70::Code::InvalidIdentity);
    t.call(request(6, gen, recovery.id, recovery.rid));
    t.reset();
    gen = ++t.generation;
    t.call(request(1, gen, first.id, first.rid, 1, first.hud));
    for (auto range : std::vector<std::pair<uint32_t, uint32_t>>{
             {21121, 0}, {21120, 1}, {1, 0xffffffffu}}) {
      Bytes p;
      cu66::put32(p, range.first);
      cu66::put32(p, range.second);
      t.call(request(3, gen, first.id, first.rid, 0, p), hc70::Code::Rejected);
    }
    t.call(request(6, gen, first.id, first.rid));
    t.call(request(6, gen, first.id, first.rid));
    std::cout << "TEST_PASS_ENDPOINT {\"actual_HUD_frames\":" << frames
              << ",\"keys\":" << keys << ",\"commands\":" << t.commands
              << ",\"malformed_no_state_change\":" << t.malformed
              << ",\"words_transferred_per_actual_frame\":21120,\"commit_"
                 "retry\":true,\"abort_retry\":true,\"old_abort_does_not_"
                 "discard_new_candidate\":true,\"native_endpoint_only\":true}"
              << std::endl;
  } catch (const std::exception &e) {
    std::cerr << "TEST_FAIL " << e.what() << std::endl;
    return 1;
  }
}
