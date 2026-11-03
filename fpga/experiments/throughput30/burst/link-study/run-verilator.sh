#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
burst=$(cd -- "$here/.." && pwd)
fpga=$(cd -- "$burst/../../.." && pwd)
root=$(cd -- "$fpga/.." && pwd)
build=${BUILD_DIR:-$(mktemp -d)}
mkdir -p "$build"; build=$(cd -- "$build" && pwd)
rate=${RATE_BPS:-8000000}
if [[ -e "$build/fixtures" || -e "$build/dumps" ]]; then echo 'fixture/dump destination exists' >&2; exit 2; fi
"${PYTHON:-python3}" "$root/experiments/fixture30/generate.py" "$build/fixtures" --frames 10
mkdir "$build/dumps"
files=()
for f in "$fpga"/vendor/core_jpeg/src_v/*.v; do [[ "$f" == */jpeg_input.v ]] || files+=("$f"); done
verilator --version
verilator --binary --timing --assert -Wno-fatal -DSIMULATION --top-module tb_jpeg720_link_burst --Mdir "$build/obj" \
 "$here/tb_jpeg720_link_burst.sv" "$burst/moonshine_memory_burst.sv" "$burst/moonshine_sdram_burst.sv" \
 "$burst/sdram_model_burst_verilator.sv" "$burst/jpeg_input_guarded.v" "$burst/../moonbub_tile_transpose.sv" \
 "$fpga/rtl/moonshine_core.sv" "$fpga/rtl/moonshine_lcd.sv" "${files[@]}"
ulimit -c 0
timeout 300s "$build/obj/Vtb_jpeg720_link_burst" "+FIXTURE_DIR=$build/fixtures" "+DUMP_DIR=$build/dumps" "+RATE_BPS=$rate" | tee "$build/run.log"
grep -q '^TEST_PASS_JPEG720_LINK_TEN_FRAMES ' "$build/run.log"
"${CXX:-g++}" -std=c++17 -O2 -I"$fpga/vendor/core_jpeg/c_model" "$root/host/evidence/jpeg-c-model-fixed-color-main.cpp" -o "$build/jpeg-cmodel"
for ((frame=0;frame<10;frame++)); do
 printf -v stem '%04d' "$frame"
 "$build/jpeg-cmodel" "$build/fixtures/$stem.jpg" "$build/$stem.ppm" > "$build/$stem-cmodel.log"
 "${PYTHON:-python3}" "$burst/compare-frame.py" "$build/$stem.ppm" "$build/dumps/$stem-rgb565.txt" --exact > "$build/$stem-comparison.json"
done
printf 'Ten outputs matched related C-model decoder; artifacts: %s\n' "$build"
