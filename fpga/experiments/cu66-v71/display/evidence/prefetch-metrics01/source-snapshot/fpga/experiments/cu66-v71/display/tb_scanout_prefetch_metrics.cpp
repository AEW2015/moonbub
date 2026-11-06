#include "Vcu71_scanout_prefetch.h"
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
  Vcu71_scanout_prefetch d;
  std::mt19937 rng;
  bool randomize, starve;
  unsigned fault_mode=0, injected_faults=0;
  bool reset_probe=false;
  uint64_t line_begin=0,max_line_cycles=0,request_begin=0,max_response_cycles=0;
  bool black_line = false;
  uint64_t black_lines = 0;
  uint64_t time = 0, next_mem = 5, next_pixel = 18, mem_edges = 0,
           pixel_edges = 0, pixels = 0;
  bool pending = false;
  unsigned delay = 0, address = 0, received_descriptors = 0, errors = 0;
  uint64_t per_slot[2] = {0, 0};
  bool queued_second = false, queued_stale = false, held_request = false;
  unsigned held_address = 0;
  uint64_t bursts = 0;
  explicit Sim(unsigned seed, bool starvation = false, unsigned faults = 0, bool reset = false)
      : rng(seed), randomize(seed != 0), starve(starvation), fault_mode(faults), reset_probe(reset) {
    d.mem_clk = 0;
    d.pixel_clk = 0;
    d.mem_rst = 1;
    d.pixel_reset_n = 0;
    d.descriptor_valid = 0;
    d.lcd_req_ready = 0;
    d.lcd_busy = 0;
    d.lcd_aborted = 0;
    d.lcd_rsp_valid = 0;
    d.lcd_rsp_error = 0;
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
    bool req = false, rsp = false, desc = false, safe = false, aborted = false;
    unsigned addr = 0;
    if (mp) {
      d.lcd_req_ready = !pending && (!randomize || rng() % 5 != 0);
      d.lcd_busy = pending;
      bool fault_address = address == (0xc00000 + 100*480 + 8);
      d.lcd_aborted = pending && delay == 0 && fault_mode == 2 && fault_address;
      d.lcd_rsp_valid = pending && delay == 0 && !d.lcd_aborted;
      d.lcd_rsp_error = fault_mode == 1 && fault_address;
      if (d.lcd_rsp_valid) {
        need(address >= 0xc00000 && address < 0xd00000, "addressrange");
        unsigned slot = (address - 0xc00000) / 0x80000,
                 offset = (address - 0xc00000) % 0x80000;
        need(offset < 384000, "buffer guard");
        need((address & 7) == 0 && offset + 7 < 384000, "burstguardalignment");
        for (unsigned i = 0; i < 4; i++) {
          unsigned off = offset + 2*i;
          d.lcd_rsp_data[i] = uint32_t(word(slot, off % 480, off / 480)) |
            (uint32_t(word(slot, (off+1) % 480, (off+1) / 480)) << 16);
        }
      }
      d.eval();
      if (check && held_request)
        need(d.lcd_req_valid && d.lcd_req_addr == held_address,
             "burstrequeststability");
      held_request = d.lcd_req_valid && !d.lcd_req_ready;
      held_address = d.lcd_req_addr;
      req = d.lcd_req_valid && d.lcd_req_ready;
      rsp = d.lcd_rsp_valid && d.lcd_rsp_ready;
      aborted = d.lcd_aborted;
      desc = d.descriptor_valid && d.descriptor_ready;
      safe = d.frame_boundary && d.scanout_drained;
      addr = d.lcd_req_addr;
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
      if (rsp || aborted) {
        pending = false;
        max_response_cycles = std::max(max_response_cycles, mem_edges-request_begin);
        if (address % 0x80000 % 480 == 472) max_line_cycles = std::max(max_line_cycles, mem_edges-line_begin+8);
        if (fault_mode && address == (0xc00000 + 100*480 + 8)) injected_faults++;
      }
      if (req) {
        need(!pending, "multiplememoryrequests");
        need((addr & 7) == 0, "requestalignment");
        bursts++;
        request_begin=mem_edges;
        if ((addr-0xc00000) % 0x80000 % 480 == 0) line_begin=mem_edges;
        pending = true;
        address = addr;
        delay = randomize ? (starve ? 80 + rng() % 40 : rng() % 24) : 0;
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
        if (fault_mode && d.front_slot==0 && y==100 && x>=8 && x<16) w=0;
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
    if (reset_probe) {
      d.descriptor_valid=1;d.descriptor_generation=99;d.descriptor_frame_id=99;d.descriptor_slot=0;
      while(!pending) step(false);
      // This test resets both clock domains AND the simulated memory service.
      // It does not certify unilateral pixel reset or external drain behavior.
      d.mem_rst=1;d.pixel_reset_n=0;d.descriptor_valid=0;
      pending=false;held_request=false;
      for(unsigned i=0;i<40;i++)step(false);
      d.mem_rst=0;d.pixel_reset_n=1;held_request=false;pending=false;
      received_descriptors=0;errors=0;bursts=0;pixels=0;per_slot[0]=per_slot[1]=0;
      need(!d.front_valid && !d.pending_valid && d.presented_count==0 && !d.lcd_req_valid,"coordinatedresetclear");
    }
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
    need(errors == (1u+(fault_mode==2)) && received_descriptors == 3, "stalerejected");
    need(d.memory_errors == (fault_mode?1u:0u) && injected_faults == (fault_mode?1u:0u), "memoryerror");
    if (starve)
      need(black_lines > 0 && d.underruns == black_lines,
           "whole-lineblackunderruncount");
    else
      need(d.underruns == 0, "unexpectedunderrun");
    std::cout << "TEST_PASS_BL8_SCANOUT pixel_clocks=" << pixel_edges
              << " memory_clocks=" << mem_edges << " compared_pixels=" << pixels
              << " complete_frames=2 descriptors_presented="
              << d.presented_count << " bursts=" << bursts << " stale_rejections=" << errors
              << " max_response_cycles=" << max_response_cycles << " max_line_cycles_from_first_request=" << max_line_cycles
              << " injected_faults=" << injected_faults << " coordinated_reset_probe=" << reset_probe
              << " black_lines=" << black_lines << " underruns=" << d.underruns
              << std::endl;
  }
};
int main(int argc, char **argv) {
  try {
    unsigned seed = argc > 1 ? unsigned(std::stoul(argv[1])) : 0;
    std::string mode=argc>2?argv[2]:"";
    Sim sim(seed,mode=="--starve",mode=="--memory-error"?1:mode=="--abort"?2:0,mode=="--reset");
    sim.run();
    std::cout << "PASS seed=" << seed << " asynchronous_clocks_ns=10,36"
              << std::endl;
  } catch (const std::exception &e) {
    std::cerr << "FAIL " << e.what() << std::endl;
    return 1;
  }
}
