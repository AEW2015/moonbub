#include "Vvalue_check_probe.h"
#include "verilated.h"
#include <cstdint>
#include <iostream>
#include <stdexcept>
int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);
    Vvalue_check_probe dut;
    unsigned cases = 0;
    for (unsigned bits = 0; bits < 65536; ++bits) {
        const int value = bits < 32768 ? static_cast<int>(bits) : static_cast<int>(bits) - 65536;
        for (unsigned scale = 0; scale < 4; ++scale) {
            dut.in_value = static_cast<uint16_t>(bits);
            dut.in_qscale = scale;
            dut.eval();
            const bool expected = scale == 3 || value < -2048 || value > 2048;
            if (dut.baseline_bad != expected || dut.candidate_bad != expected)
                throw std::runtime_error("signed16 range predicate mismatch");
            ++cases;
        }
    }
    dut.final();
    std::cout << "{\"status\":\"TEST_PASS\",\"vectors\":" << cases << "}\n";
}
