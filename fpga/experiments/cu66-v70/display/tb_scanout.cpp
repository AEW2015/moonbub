#include "Vcu70_scanout.h"
#include "verilated.h"
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>

static void need(bool b, const std::string &s) {
  if (!b)
    throw std::runtime_error(s);
}
static uint16_t word(unsigned slot, unsigned x, unsigned y) {
  unsigned v = (x * 47 + y * 133 + slot * 0x53ab) ^ ((x ^ y) << 7);
  return uint16_t(v | 1u);
}
struct Sim {
  Vcu70_scanout d;
  std::mt19937 rng;
  bool randomize, starve;
  bool black_line = false;
  uint64_t black_lines = 0;
  uint64_t time = 0, next_mem = 5, next_pixel = 18, mem_edges = 0,
           pixel_edges = 0, pixels = 0;
  bool pending = false;
  unsigned delay = 0, address = 0, received_descriptors = 0, errors = 0;
  uint64_t per_slot[2] = {0, 0};
  bool queued_second = false, queued_stale = false, held_request = false;
  unsigned held_address = 0;
  explicit Sim(unsigned seed, bool starvation = false)
      : rng(seed), randomize(seed != 0), starve(starvation) {
    d.mem_clk = 0;
    d.pixel_clk = 0;
    d.mem_rst = 1;
    d.pixel_reset_n = 0;
    d.descriptor_valid = 0;
    d.aux_req_ready = 0;
    d.aux_rsp_valid = 0;
    d.aux_rsp_error = 0;
    for (unsigned i = 0; i < 20; i++)
      step(false);
    d.mem_rst = 0;
    d.pixel_reset_n = 1;
  }
  void step(bool check = true) {
    uint64_t at = std::min(next_mem, next_pixel);
    bool me = at == next_mem, pe = at == next_pixel, mp = me && !d.mem_clk,
         pp = pe && !d.pixel_clk;
    time = at;
    bool req = false, rsp = false, desc = false, safe = false;
    unsigned addr = 0;
    if (mp) {
      d.aux_req_ready = !pending && (!randomize || rng() % 5 != 0);
      d.aux_rsp_valid = pending && delay == 0;
      d.aux_rsp_error = 0;
      if (d.aux_rsp_valid) {
        need(address >= 0xc00000 && address < 0xd00000, "addressrange");
        unsigned slot = (address - 0xc00000) / 0x80000,
                 offset = (address - 0xc00000) % 0x80000;
        need(offset < 384000, "buffer guard");
        d.aux_rsp_data = word(slot, offset % 480, offset / 480);
      }
      d.eval();
      if (check && held_request)
        need(d.aux_req_valid && d.aux_req_addr == held_address,
             "scalarrequeststability");
      held_request = d.aux_req_valid && !d.aux_req_ready;
      held_address = d.aux_req_addr;
      req = d.aux_req_valid && d.aux_req_ready;
      rsp = d.aux_rsp_valid && d.aux_rsp_ready;
      desc = d.descriptor_valid && d.descriptor_ready;
      safe = d.frame_boundary && d.scanout_drained;
      addr = d.aux_req_addr;
    }
    if (me) {
      d.mem_clk = !d.mem_clk;
      next_mem += 5;
    }
    if (pe) {
      d.pixel_clk = !d.pixel_clk;
      next_pixel += 18;
    }
    d.eval();
    if (mp) {
      mem_edges++;
      if (pending && delay)
        delay--;
      if (rsp)
        pending = false;
      if (req) {
        need(!pending, "multiplememoryrequests");
        need(!d.aux_req_write, "LCDwriteunexpected");
        pending = true;
        address = addr;
        delay = randomize ? (starve ? 1 + rng() % 3 : rng() % 2) : 0;
      }
      if (desc) {
        received_descriptors++;
        d.descriptor_valid = 0;
      }
      if (check && d.presented)
        need(safe, "descriptorswitchoutsidesafeboundary");
      if (d.error)
        errors++;
    }
    if (pp) {
      pixel_edges++;
      if (check && d.data_enable && d.front_valid) {
        unsigned x = d.physical_x, y = d.physical_y;
        need(x < 480 && y < 800, "rastercoords");
        uint16_t w = y >= 40 && y < 760 ? word(d.front_slot, x, y) : 0;
        if (x == 0) {
          black_line = starve && y >= 40 && y < 760 && d.red == 0 &&
                       d.green == 0 && d.blue == 0;
          if (black_line)
            black_lines++;
        }
        if (black_line)
          w = 0;
        unsigned r = (w >> 11) & 31, g = (w >> 5) & 63, b = w & 31;
        need(d.red == ((r << 3) | (r >> 2)) &&
                 d.green == ((g << 2) | (g >> 4)) &&
                 d.blue == ((b << 3) | (b >> 2)),
             "RGBscanoutmismatch x=" + std::to_string(x) + " y=" +
                 std::to_string(y) + " slot=" + std::to_string(d.front_slot));
        pixels++;
        per_slot[d.front_slot]++;
        if (d.front_slot == 0 && x == 200 && y == 300 && !queued_second) {
          need(!d.pending_valid, "pendingunexpected");
          d.descriptor_valid = 1;
          d.descriptor_generation = 2;
          d.descriptor_frame_id = 11;
          d.descriptor_slot = 1;
          queued_second = true;
        }
        if (d.front_slot == 1 && x == 200 && y == 300 && !queued_stale) {
          d.descriptor_valid = 1;
          d.descriptor_generation = 1;
          d.descriptor_frame_id = 9;
          d.descriptor_slot = 0;
          queued_stale = true;
        }
      }
    }
    need(mem_edges < 10000000, "scanoutwatchdog");
  }
  void run() {
    d.descriptor_valid = 1;
    d.descriptor_generation = 1;
    d.descriptor_frame_id = 10;
    d.descriptor_slot = 0;
    while (per_slot[1] < 384000)
      step();
    need(per_slot[0] == 384000 && per_slot[1] == 384000, "fullframepixcounts");
    need(d.presented_count == 2 && d.front_generation == 2 &&
             d.front_frame_id == 11 && d.front_slot == 1,
         "descriptorhistory");
    need(errors == 1 && received_descriptors == 3, "stalerejected");
    need(d.memory_errors == 0, "memoryerror");
    if (starve)
      need(black_lines > 0 && d.underruns == black_lines,
           "whole-lineblackunderruncount");
    else
      need(d.underruns == 0, "unexpectedunderrun");
    std::cout << "TEST_PASS_SCANOUT pixel_clocks=" << pixel_edges
              << " memory_clocks=" << mem_edges << " compared_pixels=" << pixels
              << " complete_frames=2 descriptors_presented="
              << d.presented_count << " stale_rejections=" << errors
              << " black_lines=" << black_lines << " underruns=" << d.underruns
              << std::endl;
  }
};
int main(int argc, char **argv) {
  try {
    unsigned seed = argc > 1 ? unsigned(std::stoul(argv[1])) : 0;
    Sim sim(seed, argc > 2 && std::string(argv[2]) == "--starve");
    sim.run();
    std::cout << "PASS seed=" << seed << " asynchronous_clocks_ns=10,36"
              << std::endl;
  } catch (const std::exception &e) {
    std::cerr << "FAIL " << e.what() << std::endl;
    return 1;
  }
}
