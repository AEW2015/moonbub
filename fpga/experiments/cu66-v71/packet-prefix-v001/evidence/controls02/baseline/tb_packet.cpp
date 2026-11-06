#include "Vcu71_packet_prefix.h"
#include "verilated.h"
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <random>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
static std::string active_case;
static uint64_t active_cycle = 0;
static unsigned active_state = 0, active_error = 0;
static void need(bool x, const std::string &why) {
  if (!x)
    throw std::runtime_error(why);
}
static std::vector<std::string> split(const std::string &s) {
  std::stringstream ss(s);
  std::vector<std::string> out;
  std::string x;
  while (std::getline(ss, x, '\t'))
    out.push_back(x);
  return out;
}
static std::vector<uint8_t> readfile(const std::string &path) {
  std::ifstream f(path, std::ios::binary);
  need(bool(f), "open " + path);
  return {std::istreambuf_iterator<char>(f), {}};
}
template <class W> static std::string taghex(const W &w) {
  static const char *h = "0123456789abcdef";
  std::string s;
  for (unsigned i = 0; i < 16; i++) {
    unsigned b = (w[3 - i / 4] >> (8 * (3 - i % 4))) & 255;
    s += h[b >> 4];
    s += h[b & 15];
  }
  return s;
}
template <class W> static void settag(W &w, const std::string &s) {
  need(s.size() == 32, "tag hex length");
  for (unsigned j = 0; j < 4; j++)
    w[j] = 0;
  for (unsigned i = 0; i < 16; i++)
    w[3 - i / 4] |= uint32_t(std::stoul(s.substr(2 * i, 2), nullptr, 16))
                    << (8 * (3 - i % 4));
}
struct Case {
  std::string name, path, meta;
  unsigned mode, last_valid, last_id, ref_valid, ref_id;
  std::string ref_tag;
};
struct Expected {
  unsigned key, id, rid, bs, hud_addr, hud_bytes;
  std::string rt, ot, hrt, hot, qmap;
  std::array<std::array<unsigned, 5>, 3> planes;
};
static Expected expected(const std::string &path) {
  std::ifstream file(path);
  std::string line;
  std::getline(file, line);
  auto p = split(line);
  need(p.size() == 26, "metadata expected fields");
  Expected e{};
  e.key = std::stoul(p[0]);
  e.id = std::stoul(p[1]);
  e.rid = std::stoul(p[2]);
  e.rt = p[3];
  e.ot = p[4];
  e.bs = std::stoul(p[5]);
  e.hud_addr = std::stoul(p[6]);
  e.hud_bytes = std::stoul(p[7]);
  e.hrt = p[8];
  e.hot = p[9];
  e.qmap = p[10];
  for (unsigned i = 0; i < 3; i++)
    for (unsigned j = 0; j < 5; j++)
      e.planes[i][j] = std::stoul(p[11 + 5 * i + j]);
  return e;
}
struct Simulation {
  Vcu71_packet_prefix d;
  std::mt19937 rng;
  std::vector<uint8_t> packet;
  bool pending = false, held = false;
  unsigned address = 0, delay = 0, held_addr = 0;
  uint64_t cycles = 0, requests = 0, request_stalls = 0, response_waits = 0;
  bool force_not_ready = false;
  explicit Simulation(unsigned seed) : rng(seed) {
    d.rst = 1;
    d.abort_i = 0;
    d.cfg_valid = 0;
    d.metadata_ready = 0;
    d.qmap_req_valid = 0;
    d.qmap_req_index = 0;
    d.commit_valid = 0;
    tick();
    tick();
    d.rst = 0;
    tick();
  }
  void tick() {
    if (pending && delay)
      delay--;
    d.clk = 0;
    d.rd_req_ready = !force_not_ready && ((rng() % 4) != 0);
    d.rd_rsp_valid = pending && delay == 0;
    d.rd_rsp_data = pending ? packet.at(address) : 0;
    d.eval();
    if (held && !d.abort_i && !d.rst)
      need(d.rd_req_valid && d.rd_req_addr == held_addr,
           "request changed while stalled");
    bool req = d.rd_req_valid && d.rd_req_ready,
         rsp = d.rd_rsp_valid && d.rd_rsp_ready;
    unsigned next_address = d.rd_req_addr;
    if (d.rd_req_valid && !d.rd_req_ready)
      request_stalls++;
    if (pending && !d.rd_rsp_valid)
      response_waits++;
    held = d.rd_req_valid && !d.rd_req_ready;
    held_addr = d.rd_req_addr;
    if (req) {
      need(!pending || rsp, "multiple RAM requests outstanding");
      need(next_address < packet.size(), "RAM read outside immutable packet");
    }
    d.clk = 1;
    d.eval();
    cycles++;
    active_cycle = cycles;
    active_state = d.debug_state;
    active_error = d.error_code;
    if (rsp)
      pending = false;
    if (req) {
      pending = true;
      address = next_address;
      delay = 1 + rng() % 7;
      requests++;
    }
    if (pending && !d.rst)
      need(d.busy && !d.cfg_ready, "lease released before RAM response drain");
  }
  void configure(const Case &c, const std::string &base) {
    need(!pending && d.cfg_ready, "start before local lease ready");
    packet = readfile(base + c.path);
    d.cfg_packet_bytes = packet.size();
    d.cfg_last_valid = c.last_valid;
    d.cfg_last_frame_id = c.last_id;
    d.cfg_reference_valid = c.ref_valid;
    d.cfg_reference_id = c.ref_id;
    settag(d.cfg_reference_tag, c.ref_tag);
    d.metadata_ready = 0;
    d.commit_valid = 0;
    d.qmap_req_valid = 0;
    d.abort_i = 0;
    d.cfg_valid = 1;
    tick();
    d.cfg_valid = 0;
  }
  void compare_meta(const Expected &e) {
    need(d.metadata_key == e.key && d.metadata_frame_id == e.id &&
             d.metadata_reference_id == e.rid,
         "frame identity metadata");
    need(taghex(d.metadata_reference_tag) == e.rt &&
             taghex(d.metadata_output_tag) == e.ot,
         "canonical tag metadata packing");
    need(d.metadata_block_size == e.bs && d.metadata_hud_addr == e.hud_addr &&
             d.metadata_hud_bytes == e.hud_bytes,
         "block/HUD metadata");
    need(taghex(d.metadata_hud_reference_tag) == e.hrt &&
             taghex(d.metadata_hud_output_tag) == e.hot,
         "HUD tag metadata");
    for (unsigned i = 0; i < 3; i++) {
      need(d.metadata_plane_addr[i] == e.planes[i][0] &&
               d.metadata_plane_bytes[i] == e.planes[i][1] &&
               d.metadata_plane_dispatch[i] == e.planes[i][2] &&
               d.metadata_plane_blocks[i] == e.planes[i][3] &&
               d.metadata_plane_blocks_w[i] == e.planes[i][4],
           "plane address/config metadata axis" + std::to_string(i));
    }
  }
  bool await_parse(unsigned mode) {
    uint64_t watchdog = cycles + packet.size() * 40 + 10000;
    for (;;) {
      need(cycles < watchdog,
           "packet watchdog state" + std::to_string(d.debug_state));
      if (d.done && d.error) {
        std::cout << "EXACT_REJECT " << active_case << " " << unsigned(d.error_code) << "\n";
        need(mode == 0, "unexpected structural reject code" +
                            std::to_string(d.error_code));
        need(!pending && !d.busy && d.cfg_ready, "error failed local drain");
        return false;
      }
      if (d.metadata_valid) {
        need(mode != 0, "malformed structural packet accepted");
        need(!d.error && !pending && d.busy && !d.cfg_ready,
             "metadata before full parse/drain");
        return true;
      }
      tick();
    }
  }
  void check_qmap(const std::string &base, const Expected &e) {
    auto q = readfile(base + e.qmap);
    need(q.size() == 1350, "qmap oracle shape");
    d.qmap_req_valid = 1;
    for (unsigned i = 0; i < q.size(); i++) {
      d.qmap_req_index = i;
      d.clk = 0;
      d.eval();
      need(d.qmap_req_ready, "qmap lookup not ready");
      tick();
      need(d.qmap_rsp_valid && d.qmap_rsp_index == i && d.qmap_rsp_code == q[i],
           "one-cycle qmap result");
    }
    d.qmap_req_valid = 0;
    tick();
    need(!d.qmap_rsp_valid, "qmap response valid persisted without request");
    d.qmap_req_valid = 1;
    d.qmap_req_index = 1350;
    d.clk = 0;
    d.eval();
    need(!d.qmap_req_ready, "out-of-range qmap query accepted");
    tick();
    need(!d.qmap_rsp_valid, "invalid qmap query produced response");
    d.qmap_req_valid = 0;
    d.qmap_req_index = 0;
  }
  void abort_and_drain() {
    d.abort_i = 1;
    tick();
    d.abort_i = 0;
    d.eval();
    uint64_t stop = cycles + 100;
    while (d.busy) {
      need(cycles < stop, "abort drain watchdog");
      need(!d.cfg_ready, "cfg ready before abort drain");
      tick();
    }
    need(d.aborted && !pending && d.cfg_ready && !d.error,
         "abort did not drain/release local lease");
  }
  void run(const Case &c, const std::string &base) {
    configure(c, base);
    if (!await_parse(c.mode))
      return;
    auto e = expected(base + c.meta);
    compare_meta(e);
    need(!d.qmap_req_ready, "qmap exposed before metadata handshake");
    need(d.memory_reads == packet.size(),
         "valid scan must read each byte exactly once");
    unsigned stall = rng() % 32;
    for (unsigned n = 0; n < stall; n++) {
      tick();
      need(d.metadata_valid && !d.done && d.busy && !d.cfg_ready,
           "metadata not held under backpressure");
      compare_meta(e);
    }
    d.commit_valid = 1;
    tick();
    need(d.metadata_valid && !d.commit_ready && d.busy && !d.done,
         "early commit bypassed metadata handshake");
    d.commit_valid = 0;
    d.metadata_ready = 1;
    tick();
    d.metadata_ready = 0;
    need(!d.metadata_valid && d.commit_ready && d.busy && !d.cfg_ready,
         "metadata handshake released lease before commit");
    check_qmap(base, e);
    for (unsigned n = 0; n < 3; n++) {
      tick();
      need(d.busy && d.commit_ready && !d.cfg_ready && !d.done,
           "WAIT_COMMIT not held");
    }
    if (c.mode == 2) {
      abort_and_drain();
      return;
    }
    d.commit_valid = 1;
    tick();
    d.commit_valid = 0;
    need(d.done && !d.busy && d.cfg_ready && !d.error && !d.aborted && !pending,
         "valid commit did not release local lease");
  }
  void test_aborts(const Case &first, const std::string &base) {
    // Abort a held request before it is accepted: no phantom response is owed.
    force_not_ready = true;
    configure(first, base);
    for (unsigned n = 0; n < 3; n++)
      tick();
    need(d.rd_req_valid && !pending, "held-request abort setup");
    abort_and_drain();
    force_not_ready = false;
    // Abort an accepted request while RAM delays its response; busy must hold.
    configure(first, base);
    uint64_t stop = cycles + 100;
    while (!pending) {
      need(cycles < stop, "pending abort setup");
      tick();
    }
    delay = 16;
    abort_and_drain();
    // An uncommitted metadata offer cannot change owner snapshots or replay
    // law.
    configure(first, base);
    need(await_parse(1), "metadata abort setup");
    abort_and_drain();
    // The same frame still parses with the same caller-owned snapshot after
    // abort.
    run(first, base);
  }
};
int main(int argc, char **argv) {
  try {
    Verilated::commandArgs(argc, argv);
    need(argc == 3, "tb_packet cases.tsv seed");
    std::string index = argv[1],
                base = index.substr(0, index.find_last_of('/') + 1);
    unsigned seed = std::stoul(argv[2]);
    std::ifstream file(index);
    need(bool(file), "case index open");
    std::vector<Case> cases;
    std::string line;
    while (std::getline(file, line)) {
      auto p = split(line);
      need(p.size() == 9, "case9fields");
      cases.push_back({p[0], p[1], p[8], unsigned(std::stoul(p[2])),
                       unsigned(std::stoul(p[3])), unsigned(std::stoul(p[4])),
                       unsigned(std::stoul(p[5])), unsigned(std::stoul(p[6])),
                       p[7]});
    }
    Simulation sim(seed);
    unsigned valid = 0, rejected = 0, deferred = 0;
    for (auto &c : cases) {
      active_case = c.name;
      sim.run(c, base);
      if (c.mode == 1)
        valid++;
      else if (c.mode == 2)
        deferred++;
      else
        rejected++;
      if ((valid % 24) == 0 && c.mode == 1)
        std::cout << "{\"seed\":" << seed << ",\"valid_frames\":" << valid
                  << ",\"cycles\":" << sim.cycles << "}\n";
    }
    active_case = "directed_abort_and_retry";
    sim.test_aborts(cases.front(), base);
    need(valid == 12 && rejected == 23 && deferred == 5,
         "all required fixtures completed");
    std::cout << "TEST_PASS {\"seed\":" << seed << ",\"valid_frames\":" << valid
              << ",\"structural_rejections\":" << rejected
              << ",\"semantic_deferred_and_aborted\":" << deferred
              << ",\"qmap_values_checked\":" << (valid + deferred + 1) * 1350
              << ",\"cycles\":" << sim.cycles
              << ",\"RAM_reads\":" << sim.requests
              << ",\"request_stalls\":" << sim.request_stalls
              << ",\"delayed_response_cycles\":" << sim.response_waits
              << ",\"abort_tests\":3,\"physical_timing_proven\":false}\n";
    return 0;
  } catch (const std::exception &e) {
    std::cerr << "TEST_FAIL case=" << active_case << " cycle=" << active_cycle
              << " state=" << active_state << " error=" << active_error << " "
              << e.what() << "\n";
    return 1;
  }
}
