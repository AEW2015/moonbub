#include "Vphase_predicate_probe.h"
#include "verilated.h"
#include <array>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string>

static void require(bool ok, const std::string &why) {
    if (!ok) throw std::runtime_error(why);
}

struct Vector {
    uint32_t blocks;
    std::array<uint32_t, 4> counts;
    uint32_t written;
    uint16_t block;
    uint8_t index;
    int16_t value;
    uint32_t active_epoch;
    uint32_t coef_epoch;
    uint8_t band;
    uint32_t previous_position;
    bool previous_valid;
    bool raw;
};

static uint32_t next_random(uint32_t &state) {
    state = state * 1664525U + 1013904223U;
    return state;
}

static void check(Vphase_predicate_probe &dut, const Vector &v,
                  uint8_t phase, uint64_t &cases) {
    dut.phase = phase;
    dut.blocks = v.blocks;
    dut.written = v.written;
    dut.coef_block = v.block;
    dut.coef_index = v.index;
    dut.coef_value = static_cast<uint16_t>(v.value);
    dut.active_epoch = v.active_epoch;
    dut.coef_epoch = v.coef_epoch;
    dut.coef_band = v.band;
    dut.previous_position = v.previous_position;
    dut.previous_valid = v.previous_valid;
    dut.raw_mode = v.raw;
    for (unsigned i = 0; i < 4; ++i) dut.counts_flat[i] = v.counts[i];
    dut.eval();
    require(dut.candidate_bad == dut.reference_bad,
            "candidate/reference mismatch phase=" + std::to_string(phase) +
            " blocks=" + std::to_string(v.blocks) +
            " written=" + std::to_string(v.written) +
            " block=" + std::to_string(v.block) +
            " index=" + std::to_string(v.index));
    ++cases;
}

int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    try {
        Vphase_predicate_probe dut;
        uint64_t cases = 0;
        const std::array<uint32_t, 12> edges = {
            0U, 1U, 15U, 16U, 17U, 2047U, 2048U, 65535U,
            65536U, 0x7fffffffU, 0xfffffffeU, 0xffffffffU};
        const std::array<int16_t, 8> values = {
            -32768, -2049, -2048, -1, 0, 1, 2048, 32767};
        const std::array<uint32_t, 8> positions = {
            0U, 1U, 63U, 64U, 127U, 2047U, 0x7fffffffU, 0xffffffffU};

        // Directed Cartesian boundary set spans every 3-bit phase, raw and
        // sparse modes, all semantic value boundaries, and count wrap edges.
        for (unsigned phase = 0; phase < 8; ++phase) {
            for (unsigned mode = 0; mode < 2; ++mode) {
                for (unsigned i = 0; i < edges.size(); ++i) {
                    Vector v{};
                    v.blocks = edges[(i + phase) % edges.size()];
                    v.counts = {edges[i], edges[(i + 1) % edges.size()],
                                edges[(i + 2) % edges.size()], edges[(i + 3) % edges.size()]};
                    v.written = edges[(i + 4) % edges.size()];
                    v.block = static_cast<uint16_t>(edges[(i + 5) % edges.size()]);
                    v.index = static_cast<uint8_t>((i * 9U + phase) & 63U);
                    v.value = values[(i + phase) % values.size()];
                    v.active_epoch = edges[(i + 6) % edges.size()];
                    v.coef_epoch = (i & 1U) ? v.active_epoch : v.active_epoch + 1U;
                    v.band = static_cast<uint8_t>((phase + i) & 3U);
                    v.previous_position = positions[(i + phase) % positions.size()];
                    v.previous_valid = (i & 1U) != 0;
                    v.raw = mode != 0;
                    check(dut, v, static_cast<uint8_t>(phase), cases);
                }
            }
        }

        uint32_t state = 0x113301U;
        for (unsigned n = 0; n < 100000; ++n) {
            Vector v{};
            v.blocks = next_random(state) & 0x1ffffU;
            for (auto &count : v.counts) count = next_random(state);
            v.written = next_random(state);
            v.block = static_cast<uint16_t>(next_random(state));
            v.index = static_cast<uint8_t>(next_random(state) & 63U);
            v.value = static_cast<int16_t>(next_random(state));
            v.active_epoch = next_random(state);
            v.coef_epoch = next_random(state);
            v.band = static_cast<uint8_t>(next_random(state) & 3U);
            v.previous_position = next_random(state);
            v.previous_valid = (next_random(state) & 1U) != 0;
            v.raw = (next_random(state) & 1U) != 0;
            for (unsigned phase = 0; phase < 8; ++phase)
                check(dut, v, static_cast<uint8_t>(phase), cases);
        }
        std::cout << "{\"type\":\"phase_predicate_verdict\",\"status\":\"TEST_PASS\","
                  << "\"phase_encodings\":8,\"random_vectors\":100000,\"comparisons\":"
                  << cases << "}\n";
        return 0;
    } catch (const std::exception &error) {
        std::cerr << "PHASE_PREDICATE_FAIL " << error.what() << '\n';
        return 1;
    }
}
