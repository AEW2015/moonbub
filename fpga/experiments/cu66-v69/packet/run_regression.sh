#!/usr/bin/env bash
set -euo pipefail
study_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
build_dir=${BUILD_DIR:-/build/packet}
verilator --lint-only -Wall --top-module cu66_packet_control "$study_dir/cu66_packet_control.sv" -I"$study_dir"
verilator --cc --exe --build -j 2 -Wall --top-module cu66_packet_control -I"$study_dir" --Mdir "$build_dir" "$study_dir/cu66_packet_control.sv" "$study_dir/tb_packet.cpp" -CFLAGS '-std=c++17 -O2'
"$build_dir/Vcu66_packet_control" "$study_dir/cases.tsv" 6910
"$build_dir/Vcu66_packet_control" "$study_dir/cases.tsv" 6911
