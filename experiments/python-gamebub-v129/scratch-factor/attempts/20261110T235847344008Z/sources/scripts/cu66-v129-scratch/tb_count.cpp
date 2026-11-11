#include "Vcount_factor_probe.h"
#include "verilated.h"
#include <array>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>

int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    if (argc != 2) return 2;
    try {
        const unsigned seed = unsigned(std::stoul(argv[1]));
        std::mt19937 rng(seed);
        Vcount_factor_probe d;
        uint64_t records=0, checks=0, equal=0, unequal=0, high=0;
        auto run = [&](uint32_t written, const std::array<uint32_t,4> &counts) {
            ++records;
            d.written=written;
            for (unsigned i=0;i<4;++i) d.counts[i]=counts[i];
            for (unsigned phase=0;phase<8;++phase) {
                d.phase=phase; d.eval();
                const bool reference=written==counts[phase&3U];
                if (bool(d.old_equal)!=reference || bool(d.new_equal)!=reference)
                    throw std::runtime_error("count factor mismatch");
                ++checks; reference ? ++equal : ++unequal;
                if ((written^counts[phase&3U])&0xffff0000U) ++high;
            }
        };
        for (uint32_t w:std::array<uint32_t,7>{0,1,2,0x7fffffffU,0x80000000U,0xfffffffeU,0xffffffffU})
            for(unsigned bit=0;bit<32;++bit)
                run(w,{w,w^(uint32_t(1)<<bit),w+uint32_t(1),w-uint32_t(1)});
        for(unsigned i=0;i<30000;++i) {
            const uint32_t w=uint32_t(rng()); std::array<uint32_t,4> c{uint32_t(rng()),uint32_t(rng()),uint32_t(rng()),uint32_t(rng())};
            c[rng()%4]=w; c[rng()%4]=w^(uint32_t(1)<<(rng()%32)); run(w,c);
        }
        if(records!=30224 || checks!=241792 || !equal || !unequal || !high)
            throw std::runtime_error("coverage mismatch");
        std::cout << "{\"type\":\"v129_count_factor_verdict\",\"status\":\"TEST_PASS\",\"seed\":" << seed
                  << ",\"records\":" << records << ",\"phase_checks\":" << checks
                  << ",\"equal\":" << equal << ",\"unequal\":" << unequal
                  << ",\"high_bit_differences\":" << high << ",\"DUT_clocks\":0}\n";
        return 0;
    } catch (const std::exception &e) {
        std::cerr << "V129_COUNT_FAIL " << e.what() << '\n'; return 1;
    }
}
