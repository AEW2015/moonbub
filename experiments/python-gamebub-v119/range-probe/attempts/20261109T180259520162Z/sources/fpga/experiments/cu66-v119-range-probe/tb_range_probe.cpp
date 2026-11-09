#include "Vrange_probe.h"
#include "verilated.h"

#include <cstdint>
#include <cstdlib>
#include <iostream>

static std::int32_t signed16(std::uint32_t raw) {
    return raw < 0x8000U ? static_cast<std::int32_t>(raw)
                         : static_cast<std::int32_t>(raw) - 0x10000;
}

static bool oracle(std::uint32_t raw) {
    const std::int32_t value = signed16(raw);
    return value >= -2048 && value <= 2048;
}

static void check(Vrange_probe& dut, std::uint32_t raw, bool expected) {
    dut.raw = raw;
    dut.eval();
    const bool actual = dut.in_range != 0U;
    if (actual != expected) {
        std::cerr << "Mismatch raw=0x" << std::hex << raw << std::dec
                  << " signed=" << signed16(raw)
                  << " expected=" << expected << " actual=" << actual << '\n';
        std::exit(EXIT_FAILURE);
    }
}

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);
    Vrange_probe dut;
    for (std::uint32_t raw = 0; raw <= 0xffffU; ++raw) {
        check(dut, raw, oracle(raw));
    }

    struct Endpoint {
        std::uint16_t raw;
        bool accepted;
    };
    constexpr Endpoint endpoints[] = {
        {0x8000U, false}, {0xf7ffU, false}, {0xf800U, true},
        {0xffffU, true},  {0x0000U, true}, {0x07ffU, true},
        {0x0800U, true},  {0x0801U, false}, {0x7fffU, false},
    };
    for (const Endpoint& endpoint : endpoints) {
        check(dut, endpoint.raw, endpoint.accepted);
    }
    dut.final();
    std::cout << "TEST_PASS patterns=65536 endpoint_checks=9 mismatches=0\n";
    return EXIT_SUCCESS;
}
