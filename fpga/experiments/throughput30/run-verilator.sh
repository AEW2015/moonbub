#!/usr/bin/env bash
set -euo pipefail
# Run from any directory, with Verilator 5.x, make, a C++ compiler and timeout.
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
fpga=$(cd -- "$here/../.." && pwd)
build_dir=${BUILD_DIR:-$(mktemp -d)}
mkdir -p "$build_dir"
printf 'Build directory: %s\n' "$build_dir"
verilator --version
verilator --binary --timing --assert -Wno-fatal --top-module tb_moonbub_tile_transpose --Mdir "$build_dir/tile" "$here/tb_moonbub_tile_transpose.sv" "$here/moonbub_tile_transpose.sv"
timeout 120s "$build_dir/tile/Vtb_moonbub_tile_transpose"
verilator --binary --timing --assert -Wno-fatal --top-module tb_tile_full_trace --Mdir "$build_dir/full" "$here/tb_tile_full_trace.sv" "$here/moonbub_tile_transpose.sv"
timeout 180s "$build_dir/full/Vtb_tile_full_trace" "+TRACE_FILE=$fpga/sim/decoded-rgb565.txt"
verilator --binary --timing --assert -Wno-fatal -DSIMULATION --top-module tb_memory_throughput --Mdir "$build_dir/memory" "$here/tb_memory_throughput.sv" "$here/moonbub_tile_transpose.sv" "$fpga/rtl/moonshine_memory.sv" "$fpga/rtl/moonshine_sdram.sv" "$fpga/rtl/moonshine_lcd.sv" "$fpga/sim/sdram_model.sv"
timeout 300s "$build_dir/memory/Vtb_memory_throughput" "+TRACE_FILE=$fpga/sim/decoded-rgb565.txt"
