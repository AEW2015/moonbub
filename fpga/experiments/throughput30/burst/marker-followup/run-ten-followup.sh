#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
burst=$(cd -- "$here/.." && pwd)
fpga=$(cd -- "$here/../../../.." && pwd)
root=$(cd -- "$fpga/.." && pwd)
build=${BUILD_DIR:-$(mktemp -d)}
mkdir -p "$build"
build=$(cd -- "$build" && pwd)
"${PYTHON:-python3}" "$root/experiments/fixture30/generate.py" "$build/fixtures" --frames 10
mkdir "$build/dumps"
files=()
for f in "$fpga"/vendor/core_jpeg/src_v/*.v; do [[ "$f" == */jpeg_input.v ]] || files+=("$f"); done
verilator --version
verilator --binary --timing --assert -Wno-fatal -DSIMULATION --top-module tb_jpeg720_queue1_burst --Mdir "$build/obj" \
 "$burst/tb_jpeg720_queue1_burst.sv" "$here/jpeg_input_followup.v" "$burst/moonshine_memory_burst.sv" "$burst/moonshine_sdram_burst.sv" \
 "$burst/sdram_model_burst_verilator.sv" "$burst/../moonbub_tile_transpose.sv" "$fpga/rtl/moonshine_core.sv" "$fpga/rtl/moonshine_lcd.sv" "${files[@]}"
ulimit -c 0
timeout 300s "$build/obj/Vtb_jpeg720_queue1_burst" "+FIXTURE_DIR=$build/fixtures" "+DUMP_DIR=$build/dumps" | tee "$build/run.log"
grep -q '^TEST_PASS_JPEG720_TEN_FRAMES ' "$build/run.log"
"${CXX:-g++}" -std=c++17 -O2 -I"$fpga/vendor/core_jpeg/c_model" "$root/host/evidence/jpeg-c-model-fixed-color-main.cpp" -o "$build/jpeg-cmodel"
for ((frame=0; frame<10; frame++)); do
 printf -v stem '%04d' "$frame"
 "$build/jpeg-cmodel" "$build/fixtures/$stem.jpg" "$build/$stem-cmodel.ppm" > "$build/$stem-cmodel.log"
 "${PYTHON:-python3}" "$burst/compare-frame.py" "$build/$stem-cmodel.ppm" "$build/dumps/$stem-rgb565.txt" --exact > "$build/$stem-compare.json"
done
printf 'All ten shared-algorithm C-model pixel comparisons passed. Logs: %s\n' "$build"
