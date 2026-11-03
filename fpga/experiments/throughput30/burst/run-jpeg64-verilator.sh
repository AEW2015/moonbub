#!/usr/bin/env bash
set -euo pipefail
# Requires Verilator 5.x, make, C++, GNU timeout, Python and Pillow.
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
fpga=$(cd -- "$here/../../.." && pwd)
root=$(cd -- "$fpga/.." && pwd)
build=${BUILD_DIR:-$(mktemp -d)}
mkdir -p "$build"
build=$(cd -- "$build" && pwd)
verilator --version
verilator --binary --timing --assert -Wno-fatal -DSIMULATION --top-module tb_jpeg64_burst --Mdir "$build/obj" \
 "$here/tb_jpeg64_burst.sv" "$here/moonshine_memory_burst.sv" "$here/moonshine_sdram_burst.sv" \
 "$here/sdram_model_burst_verilator.sv" "$here/../moonbub_tile_transpose.sv" \
 "$fpga/rtl/moonshine_core.sv" "$fpga/rtl/moonshine_lcd.sv" "$fpga"/vendor/core_jpeg/src_v/*.v
 timeout 180s "$build/obj/Vtb_jpeg64_burst" "+JPEG_FILE=$fpga/sim/pipeline64-420.jpg" "+DUMP_FILE=$build/jpeg64-rgb565.txt"
"${PYTHON:-python3}" "$here/compare-frame.py" \
 "$fpga/sim/pipeline64-420.jpg" "$build/jpeg64-rgb565.txt"
# Shared-algorithm exact C-model check (not an independent decoder).
"${CXX:-g++}" -std=c++17 -O2 -I"$fpga/vendor/core_jpeg/c_model" \
 "$root/host/evidence/jpeg-c-model-fixed-color-main.cpp" -o "$build/jpeg-cmodel"
"$build/jpeg-cmodel" "$fpga/sim/pipeline64-420.jpg" "$build/jpeg64-cmodel.ppm"
"${PYTHON:-python3}" "$here/compare-frame.py" \
 "$build/jpeg64-cmodel.ppm" "$build/jpeg64-rgb565.txt" --exact
