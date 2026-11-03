#!/usr/bin/env bash
set -euo pipefail
# Standalone functional full-trace model, not a physical design or timing test.
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
fpga=$(cd -- "$here/../../.." && pwd)
build=${BUILD_DIR:-$(mktemp -d)}
mkdir -p "$build"
verilator --version
verilator --binary --timing --assert -Wno-fatal -DSIMULATION --top-module tb_burst_memory_throughput --Mdir "$build" "$here/tb_burst_memory_throughput_verilator.sv" "$here/moonshine_memory_burst.sv" "$here/moonshine_sdram_burst.sv" "$fpga/rtl/moonshine_lcd.sv" "$here/../moonbub_tile_transpose.sv" "$here/sdram_model_burst_verilator.sv"
timeout 180s "$build/Vtb_burst_memory_throughput" "+TRACE_FILE=$fpga/sim/decoded-rgb565.txt" "$@"
