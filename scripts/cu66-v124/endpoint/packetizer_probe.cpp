#include <cstdint>
#include <fstream>
#include <iostream>
#include <iterator>
#include <limits>
#include <span>
#include <stdexcept>
#include <string>
#include <vector>

#include "msv1.h"

namespace {
  std::vector<std::uint8_t> read_file(const std::string &path) {
    std::ifstream input {path, std::ios::binary};
    if (!input) throw std::runtime_error {"cannot open input"};
    return {std::istreambuf_iterator<char> {input}, std::istreambuf_iterator<char> {}};
  }

  void write_be16(std::ostream &out, std::size_t value) {
    if (value > std::numeric_limits<std::uint16_t>::max()) throw std::runtime_error {"datagram exceeds u16 framing"};
    out.put(static_cast<char>((value >> 8) & 0xff));
    out.put(static_cast<char>(value & 0xff));
  }

  void packetize(int argc, char **argv) {
    if (argc != 7) throw std::invalid_argument {"packetize INPUT OUTPUT FRAME_ID CAPTURE_US CHUNK_SIZE"};
    const auto frame = read_file(argv[2]);
    const auto frame_id = std::stoull(argv[4]);
    const auto capture_us = std::stoull(argv[5]);
    const auto chunk = std::stoull(argv[6]);
    if (frame_id > std::numeric_limits<std::uint32_t>::max()) throw std::invalid_argument {"frame id out of range"};
    std::ofstream output {argv[3], std::ios::binary};
    if (!output) throw std::runtime_error {"cannot open output"};
    const gamebub::msv1::packetizer_t packetizer {frame, static_cast<std::uint32_t>(frame_id), capture_us,
                                                   static_cast<std::size_t>(chunk)};
    for (std::size_t offset = 0; offset < frame.size(); offset += static_cast<std::size_t>(chunk)) {
      const auto packet = packetizer.packet_at(offset);
      write_be16(output, packet.size());
      output.write(reinterpret_cast<const char *>(packet.data()), static_cast<std::streamsize>(packet.size()));
      if (!output) throw std::runtime_error {"failed writing datagram stream"};
    }
  }

  void expect_invalid(bool condition, const char *name) {
    if (!condition) throw std::runtime_error {std::string {"invalid input unexpectedly accepted: "} + name};
  }

  void bounds() {
    const std::vector<std::uint8_t> empty;
    const auto small = std::vector<std::uint8_t> {1, 2, 3};
    const auto oversized = std::vector<std::uint8_t>(gamebub::msv1::max_frame + 1, 0);
    const auto invalid_ctor = [](std::span<const std::uint8_t> bytes, std::size_t chunk) {
      try { const gamebub::msv1::packetizer_t p {bytes, 1, 1, chunk}; (void)p; }
      catch (const std::invalid_argument &) { return true; }
      return false;
    };
    expect_invalid(invalid_ctor(empty, 1), "empty frame");
    expect_invalid(invalid_ctor(oversized, 1), "oversized frame");
    expect_invalid(invalid_ctor(small, 0), "zero chunk");
    expect_invalid(invalid_ctor(small, gamebub::msv1::max_payload + 1), "oversized chunk");
    const gamebub::msv1::packetizer_t valid {small, 1, 1, 2};
    const auto invalid_offset = [&valid](std::size_t offset) {
      try { (void)valid.packet_at(offset); }
      catch (const std::invalid_argument &) { return true; }
      return false;
    };
    expect_invalid(invalid_offset(1), "unaligned offset");
    expect_invalid(invalid_offset(small.size()), "end offset");
    std::cout << "bounds_probe=PASS cases=6\n";
  }
}

int main(int argc, char **argv) {
  try {
    if (argc >= 2 && std::string {argv[1]} == "--bounds") bounds();
    else if (argc >= 2 && std::string {argv[1]} == "--packetize") packetize(argc, argv);
    else throw std::invalid_argument {"expected --bounds or --packetize"};
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "packetizer_probe: " << error.what() << '\n';
    return 2;
  }
}
