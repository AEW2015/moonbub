#!/usr/bin/env bash
set -euo pipefail
# Verilator 5.x, C++, make, timeout, and Python with Pillow required.
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
fpga=$(cd -- "$here/../../.." && pwd)
root=$(cd -- "$fpga/.." && pwd)
build=${BUILD_DIR:-$(mktemp -d)}
mkdir -p "$build"
build=$(cd -- "$build" && pwd)
if [[ -e "$build/fixtures" ]]; then printf 'Fixture directory already exists: %s\n' "$build/fixtures" >&2; exit 2; fi
"${PYTHON:-python3}" "$root/experiments/fixture30/generate.py" "$build/fixtures" --frames 7
files=()
for f in "$fpga"/vendor/core_jpeg/src_v/*.v; do
 [[ "$f" == */jpeg_input.v ]] || files+=("$f")
done
verilator --version
verilator --binary --timing --assert -Wno-fatal -DSIMULATION --top-module tb_jpeg720_guarded_directed --Mdir "$build/obj" \
 "$here/tb_jpeg720_guarded_directed.sv" "$here/jpeg_input_guarded.v" "$here/moonshine_memory_burst.sv" "$here/moonshine_sdram_burst.sv" \
 "$here/sdram_model_burst_verilator.sv" "$here/../moonbub_tile_transpose.sv" \
 "$fpga/rtl/moonshine_core.sv" "$fpga/rtl/moonshine_lcd.sv" "${files[@]}"
ulimit -c 0
timeout 180s "$build/obj/Vtb_jpeg720_guarded_directed" "+JPEG_FILE=$build/fixtures/0006.jpg" "+DUMP_FILE=$build/rgb565.txt"
"${CXX:-g++}" -std=c++17 -O2 -I"$fpga/vendor/core_jpeg/c_model" \
 "$root/host/evidence/jpeg-c-model-fixed-color-main.cpp" -o "$build/jpeg-cmodel"
"$build/jpeg-cmodel" "$build/fixtures/0006.jpg" "$build/frame6-cmodel.ppm"
"${PYTHON:-python3}" "$here/compare-frame.py" "$build/frame6-cmodel.ppm" "$build/rgb565.txt" --exact
