#!/usr/bin/env bash
set -euo pipefail
# Requires Verilator 5.x, make, C++, GNU timeout, Python and Pillow.
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
fpga=$(cd -- "$here/../../.." && pwd)
root=$(cd -- "$fpga/.." && pwd)
build=${BUILD_DIR:-$(mktemp -d)}
mkdir -p "$build"
build=$(cd -- "$build" && pwd)
fixture="$root/host/fixtures/pattern-720x480-420-q65.jpg"
verilator --version
verilator --binary --timing --assert -Wno-fatal -DSIMULATION --top-module tb_jpeg720_burst --Mdir "$build/obj" \
 "$here/tb_jpeg720_burst.sv" "$here/moonshine_memory_burst.sv" "$here/moonshine_sdram_burst.sv" \
 "$here/sdram_model_burst_verilator.sv" "$here/../moonbub_tile_transpose.sv" \
 "$fpga/rtl/moonshine_core.sv" "$fpga/rtl/moonshine_lcd.sv" "$fpga"/vendor/core_jpeg/src_v/*.v
 timeout 300s "$build/obj/Vtb_jpeg720_burst" "+JPEG_FILE=$fixture" "+DUMP_FILE=$build/jpeg720-rgb565.txt"
"${PYTHON:-python3}" "$here/compare-frame.py" "$fixture" "$build/jpeg720-rgb565.txt"
# Shared-algorithm C model; not an independent JPEG implementation.
"${CXX:-g++}" -std=c++17 -O2 -I"$fpga/vendor/core_jpeg/c_model" \
 "$root/host/evidence/jpeg-c-model-fixed-color-main.cpp" -o "$build/jpeg-cmodel"
"$build/jpeg-cmodel" "$fixture" "$build/jpeg720-cmodel.ppm"
"${PYTHON:-python3}" "$here/compare-frame.py" "$build/jpeg720-cmodel.ppm" "$build/jpeg720-rgb565.txt" --exact
