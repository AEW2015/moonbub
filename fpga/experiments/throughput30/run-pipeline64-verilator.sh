#!/usr/bin/env bash
set -euo pipefail
# Verilator 5.x, make, C++ compiler and GNU timeout are required.
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
fpga=$(cd -- "$here/../.." && pwd)
build_dir=${BUILD_DIR:-$(mktemp -d)}
mkdir -p "$build_dir"
printf 'Build directory: %s\n' "$build_dir"
verilator --version
verilator --binary --timing --assert -Wno-fatal -DSIMULATION \
  --top-module tb_pipeline64 --Mdir "$build_dir" \
  "$fpga/sim/tb_pipeline64.sv" "$fpga/rtl/moonshine_core.sv" \
  "$fpga/rtl/moonshine_memory.sv" "$fpga/rtl/moonshine_sdram.sv" \
  "$fpga/sim/sdram_model.sv" "$fpga"/vendor/core_jpeg/src_v/*.v
(cd "$fpga/sim" && timeout 180s "$build_dir/Vtb_pipeline64")
