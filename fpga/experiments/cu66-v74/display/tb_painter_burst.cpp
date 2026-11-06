#include "../../../../experiments/cu66-native-v69/decoder.hpp"
#include "Vcu74_painter_burst.h"
#include "verilated.h"
#include <array>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <random>
#include <sstream>

static void need(bool b, const std::string &s) {
  if (!b)
    throw std::runtime_error(s);
}
static cu66::Bytes load(const std::filesystem::path &p) {
  std::ifstream f(p, std::ios::binary);
  need(bool(f), "fixture open");
  return {std::istreambuf_iterator<char>(f), {}};
}
static constexpr unsigned YB = 0x80000, UB = YB + 172800, VB = YB + 216000,
                          HB = 0x100000, RB = 0xc00000;
struct Sim {
  Vcu74_painter_burst d;
  std::mt19937 rng;
  bool randomized;
  uint64_t clocks = 0;
  unsigned delay = 0;
  bool pending = false, pending_write = false;
  unsigned address = 0;
  std::array<uint16_t, 8> value{};
  unsigned write_transactions = 0;
  unsigned reads = 0, read_transactions = 0, writes = 0, mode = 0;
  std::vector<uint16_t> mem = std::vector<uint16_t>(1u << 24);
  std::vector<uint8_t> seen = std::vector<uint8_t>(384000);
  std::vector<uint16_t> expected;
  bool request_held = false;
  unsigned held_address = 0;
  uint16_t held_data = 0;
  bool held_write = false;
  std::array<uint16_t, 8> held_burst_data{};
  uint16_t held_mask = 0;
  bool held_burst = false, held_read_burst = false;
  explicit Sim(unsigned seed) : rng(seed), randomized(seed != 0) {
    d.clk = 0;
    d.rst = 1;
    d.abort_i = 0;
    d.start_valid = 0;
    d.aux_req_ready = 0;
    d.aux_rsp_valid = 0;
    d.aux_rsp_error = 0;
    d.result_ready = 0;
    step();
    step();
    d.rst = 0;
    step();
  }
  struct E {
    bool start, request, response, result;
    bool write;
    unsigned addr;
    uint16_t data;
    bool burst = false, read_burst = false;
    uint16_t mask = 0;
    std::array<uint16_t, 8> words{};
  };
  E step() {
    d.clk = 0;
    d.eval();
    if (request_held && !d.abort_i && !d.error) {
      need(d.aux_req_valid && d.aux_req_addr == held_address &&
               bool(d.aux_req_write) == held_write &&
               d.aux_req_data == held_data && d.aux_req_burst == held_burst &&
               d.aux_req_byte_enable == held_mask && d.aux_req_read_burst == held_read_burst,
           "request changed while stalled");
    }
    if (request_held && !d.abort_i && !d.error)
      for (unsigned i = 0; i < 8; i++)
        need(uint16_t(d.aux_req_burst_data[i / 2] >> (16 * (i % 2))) ==
                 held_burst_data[i],
             "burst data changed while stalled");
    E e{bool(d.start_valid && d.start_ready),
        bool(d.aux_req_valid && d.aux_req_ready),
        bool(d.aux_rsp_valid && d.aux_rsp_ready),
        bool(d.result_valid && d.result_ready),
        bool(d.aux_req_write),
        d.aux_req_addr,
        uint16_t(d.aux_req_data)};
    e.burst = d.aux_req_burst;
    e.read_burst = d.aux_req_read_burst;
    e.mask = d.aux_req_byte_enable;
    for (unsigned i = 0; i < 8; i++)
      e.words[i] = uint16_t(d.aux_req_burst_data[i / 2] >> (16 * (i % 2)));
    request_held =
        d.aux_req_valid && !d.aux_req_ready && !d.abort_i && !d.error;
    held_address = d.aux_req_addr;
    held_write = d.aux_req_write;
    held_data = d.aux_req_data;
    held_burst = d.aux_req_burst;
    held_read_burst = d.aux_req_read_burst;
    held_mask = d.aux_req_byte_enable;
    held_burst_data = e.words;
    d.clk = 1;
    d.eval();
    clocks++;
    need(clocks < 3000000000ull, "global watchdog");
    return e;
  }
  bool readable(unsigned a) {
    return (a >= YB && a < YB + 259200) || (a >= HB && a < HB + 21120);
  }
  void drive() {
    d.aux_req_ready = !pending && (!randomized || rng() % 4 != 0);
    d.aux_rsp_valid = pending && delay == 0;
    d.aux_rsp_data = pending ? value[0] : 0;
    for (unsigned i = 0; i < 4; i++)
      d.aux_rsp_burst_data[i] = uint32_t(value[i * 2]) | uint32_t(value[i * 2 + 1]) << 16;
    d.aux_rsp_error = pending && ((mode == 3 && !pending_write) ||
                                  (mode == 4 && pending_write));
    d.result_ready = 0;
  }
  void service(E e) {
    if (pending && delay)
      delay--;
    if (e.response) {
      if (pending_write) {
        write_transactions++;
        for (unsigned i = 0; i < 8; i++) {
          unsigned at = address + i - RB;
          need(at < 384000, "burst outside RGB allocation");
          need(!seen[at], "duplicate burst output word");
          seen[at] = 1;
          mem[address + i] = value[i];
          need(value[i] == expected[at],
               "burst RGB mismatch physicalword=" + std::to_string(at));
          writes++;
        }
      } else {
        reads += 8;
        read_transactions++;
      }
      pending = false;
    }
    if (e.request) {
      need(!pending, "multiple outstanding painteroperations");
      if (e.write) {
        need(e.addr >= RB && e.addr + 7 < RB + 384000 && e.addr % 8 == 0,
             "BL8 RGB address guard");
        need(e.burst && e.mask == 65535, "complete RGB burst payload");
      } else
        need(readable(e.addr) && readable(e.addr + 7) && e.addr % 8 == 0 &&
                 e.read_burst && !e.burst && e.mask == 0,
             "aligned canonical/HUD wide read guard");
      pending = true;
      pending_write = e.write;
      address = e.addr;
      value = e.words;
      if (!e.write) for (unsigned i = 0; i < 8; i++) value[i] = mem.at(e.addr + i);
      delay = randomized ? 1 + rng() % 8 : 0;
    }
  }
  void prepare(const cu66::Frame &f) {
    for (unsigned a = 0; a < 3; a++) {
      unsigned base = a == 0 ? YB : a == 1 ? UB : VB;
      unsigned width = a ? 360 : 720, height = a ? 240 : 480;
      for (unsigned row = 0; row < height; row++)
        for (unsigned col = 0; col < width; col += 2) {
          // Independent pixel-coordinate mapping into 8x8 packed tiles.
          unsigned tile = (row / 8) * (width / 8) + col / 8;
          unsigned word = tile * 32 + (row % 8) * 4 + (col % 8) / 2;
          unsigned pixel = row * width + col;
          mem[base + word] = uint16_t(f.planes[a][pixel] |
                                  unsigned(f.planes[a][pixel + 1]) << 8);
        }
    }
    unsigned hud = 0;
    for (auto &p : f.hud)
      for (auto w : p.words)
        mem[HB + hud++] = w;
    need(hud == 21120, "HUDwords");
    auto display = cu66::render(f.planes, f.hud);
    expected.assign(384000, 0);
    for (unsigned y = 0; y < 480; y++)
      for (unsigned x = 0; x < 720; x++)
        expected[(x + 40) * 480 + y] = display[y * 720 + x];
    for (unsigned i = 0; i < 384000; i++)
      mem[RB + i] = 0x7bad;
    seen.assign(384000, 0);
    reads = read_transactions = writes = write_transactions = 0;
  }
  void reject_start(unsigned kind) {
    need(d.start_ready && !pending, "invalid start readiness");
    d.generation = 72;
    d.frame_id = 0;
    d.y_base = YB;
    d.u_base = UB;
    d.v_base = VB;
    d.hud_base = HB;
    d.rgb_base = RB;
    switch (kind) {
    case 0:
      d.generation = 0;
      break;
    case 1:
      d.frame_id = 0xffffffff;
      break;
    case 2:
      d.rgb_base = RB + 1;
      break;
    case 3:
      d.y_base = 0xffffff;
      break;
    case 4:
      d.u_base = 0xffffff;
      break;
    case 5:
      d.v_base = 0xffffff;
      break;
    case 6:
      d.hud_base = 0xffffff;
      break;
    case 7:
      d.rgb_base = 0xfffff8;
      break;
    case 8:
      d.rgb_base = YB;
      break;
    case 9:
      d.v_base = UB;
      break;
    default:
      throw std::runtime_error("unknown invalid start probe");
    }
    d.start_valid = 1;
    need(step().start, "invalid start handshake");
    d.start_valid = 0;
    unsigned waits = 0;
    do {
      need(!d.aux_req_valid && !d.result_valid && !pending,
           "invalid start issued memory/result");
      step();
      need(++waits < 80, "invalid start drain timeout");
    } while (d.busy);
    need(d.error && d.error_code == 1 && d.memory_reads == 0 &&
             d.memory_writes == 0 && d.memory_write_words == 0,
         "invalid start not rejected without work");
    std::cout << "START_REJECT_PASS kind=" << kind << std::endl;
  }
  void run(const cu66::Frame &f, const std::string &name, unsigned fault = 0) {
    need(d.start_ready && !pending, "start lease readiness");
    mode = fault;
    prepare(f);
    d.generation = 70;
    d.frame_id = f.id;
    d.y_base = YB;
    d.u_base = UB;
    d.v_base = VB;
    d.hud_base = HB;
    d.rgb_base = RB;
    d.start_valid = 1;
    need(step().start, "start accepted");
    d.start_valid = 0;
    auto started = clocks;
    bool stopped = false, abort_started = false;
    unsigned result_stall = 0, gap_after_read = 0;
    bool last_read_hud = false;
    while (!stopped) {
      need(clocks - started < 20000000, "frame watchdog");
      drive();
      if ((mode == 1 && pending && !pending_write && delay > 2) ||
          (mode == 2 && pending && pending_write && delay > 2) ||
          (mode == 5 && pending && pending_write && d.painted_pixels > 2000 &&
           delay > 2)) {
        d.abort_i = 1;
        abort_started = true;
      }
      if ((mode == 6 && gap_after_read == 3 && !last_read_hud) ||
          (mode == 7 && gap_after_read == 3 && last_read_hud) ||
          (mode == 8 && pending && !pending_write && address >= HB && address < HB+21120 && delay > 2)) {
        d.abort_i = 1;
        abort_started = true;
      }
      d.clk = 0;
      d.eval();
      if (d.result_valid) {
        need(fault == 0 && !pending,
             "result beforecompletionorforinvalidframe");
        need(d.result_generation == 70 && d.result_frame_id == f.id,
             "resultidentity");
        if (result_stall++ > 7)
          d.result_ready = 1;
      }
      auto e = step();
      if (e.response && !pending_write) {
        gap_after_read = 1;
        last_read_hud = address >= HB && address < HB + 21120;
      } else if (gap_after_read) gap_after_read++;
      service(e);
      d.abort_i = 0;
      if (e.result)
        stopped = true;
      else if ((abort_started || d.error) && !d.busy) {
        need(!pending, "lease freedbeforememorydrained");
        stopped = true;
      }
    }
    if (fault == 0) {
      need(!d.error && d.memory_reads == 35040 && d.memory_read_words == 280320 && d.memory_writes == 48000 &&
               d.memory_write_words == 384000 && d.painted_pixels == 345600,
           "fullframecounters");
      need(reads == 280320 && read_transactions == 35040 && writes == 384000 && write_transactions == 48000,
           "modelcounters");
      for (unsigned i = 0; i < 384000; i++)
        need(seen[i] && mem[RB + i] == expected[i], "physicalreadback");
    } else if (fault == 3 || fault == 4)
      need(d.error && d.error_code == 2, "memoryerrornotrejected");
    else
      need(abort_started && !d.error, "abortprobe");
    std::cout << "CASE_PASS name=" << name << " mode=" << fault
              << " cycles=" << clocks - started << " read_commands=" << read_transactions << " read_words=" << reads
              << " write_commands=" << write_transactions
              << " write_words=" << writes << " painted=" << d.painted_pixels
              << " error=" << unsigned(d.error_code) << std::endl;
    for (unsigned i = 0; i < 3; i++) {
      drive();
      service(step());
    }
    need(d.start_ready, "restartready");
  }
};
static cu66::Frame pattern(unsigned kind) {
  cu66::Frame f;
  f.id = 100 + kind;
  for (unsigned a = 0; a < 3; a++) {
    unsigned w = a ? 360 : 720, h = a ? 240 : 480;
    f.planes[a].resize(w * h);
    for (unsigned y = 0; y < h; y++)
      for (unsigned x = 0; x < w; x++) {
        unsigned v = (x * 37 + y * 61 + kind * 53 + a * 127) & 255;
        if (kind == 1)
          v = ((x ^ y) & 1) ? 0 : 255;
        if (kind == 2)
          v = (a == 0 ? 0 : a == 1 ? 255 : 0);
        if (kind == 3)
          v = (a == 0 ? 255 : a == 1 ? 0 : 255);
        f.planes[a][y * w + x] = uint8_t(v);
      }
  }
  for (unsigned r = 0; r < 4; r++) {
    cu66::Patch p;
    for (unsigned i = 0; i < 4; i++)
      p.rect[i] = cu66::RECTS[r][i];
    for (unsigned i = 0; i < unsigned(p.rect[2]) * p.rect[3]; i++)
      p.words.push_back(uint16_t((i * 313 + r * 0x173b + kind * 79) & 65535));
    f.hud.push_back(p);
  }
  return f;
}
int main(int argc, char **argv) {
  try {
    need(argc >= 3, "index.tsv seed");
    unsigned seed = unsigned(std::stoul(argv[2]));
    Sim sim(seed);
    for (unsigned kind = 0; kind < 10; kind++)
      sim.reject_start(kind);
    std::filesystem::path index = argv[1];
    std::ifstream file(index);
    need(bool(file), "indexopen");
    unsigned previous = ~0u, count = 0, actual = 0;
    cu66::Decoder decoder;
    std::string line;
    while (std::getline(file, line)) {
      std::stringstream s(line);
      std::string chain, n, path;
      std::getline(s, chain, '\t');
      std::getline(s, n, '\t');
      std::getline(s, path, '\t');
      unsigned c = unsigned(std::stoul(chain));
      if (c != previous) {
        previous = c;
        count = 0;
        decoder = cu66::Decoder();
      }
      if (count++ >= 2)
        continue;
      auto f = decoder.receive(load(index.parent_path() / path));
      sim.run(*f, "actual" + chain + "_" + n);
      actual++;
    }
    need(actual == 8, "actual key/P coverage");
    for (unsigned k = 0; k < 4; k++)
      sim.run(pattern(k), "pattern" + std::to_string(k));
    if (seed) {
      for (unsigned mode = 1; mode <= 8; mode++)
        sim.run(pattern(0), "fault", mode);
    }
    sim.run(pattern(0), "recovery");
    std::cout << "PASS actual_frames=8 patterns=4 recovery=1 fault_probes="
              << (seed ? 8 : 0) << " seed=" << seed << std::endl;
  } catch (const std::exception &e) {
    std::cerr << "FAIL " << e.what() << std::endl;
    return 1;
  }
}
