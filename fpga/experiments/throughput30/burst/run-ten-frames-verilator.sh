#!/usr/bin/env bash
set -euo pipefail
# MODE=strict|queue1; JPEG_DECODER=stock|guarded. Requires Verilator 5.x,
# C++, make, timeout and Python with Pillow; generate fixtures in a NEW build.
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
fpga=$(cd -- "$here/../../.." && pwd)
root=$(cd -- "$fpga/.." && pwd)
build=${BUILD_DIR:-$(mktemp -d)}
mkdir -p "$build"
build=$(cd -- "$build" && pwd)
mode=${MODE:-queue1}
decoder=${JPEG_DECODER:-guarded}
case "$mode" in
 strict) top=tb_jpeg720_multiframe_burst ;;
 queue1) top=tb_jpeg720_queue1_burst ;;
 *) printf 'Unknown MODE %s\n' "$mode" >&2; exit 2 ;;
esac
case "$decoder" in stock|guarded) ;; *) printf 'Unknown JPEG_DECODER %s\n' "$decoder" >&2; exit 2 ;; esac
if [[ -e "$build/fixtures" ]]; then printf 'Fixture directory already exists: %s\n' "$build/fixtures" >&2; exit 2; fi
"${PYTHON:-python3}" "$root/experiments/fixture30/generate.py" "$build/fixtures" --frames 10
mkdir "$build/dumps"
files=()
for f in "$fpga"/vendor/core_jpeg/src_v/*.v; do
 if [[ "$decoder" == guarded && "$f" == */jpeg_input.v ]]; then continue; fi
 files+=("$f")
done
if [[ "$decoder" == guarded ]]; then files+=("$here/jpeg_input_guarded.v"); fi
verilator --version
verilator --binary --timing --assert -Wno-fatal -DSIMULATION --top-module "$top" --Mdir "$build/obj" \
 "$here/$top.sv" "$here/moonshine_memory_burst.sv" "$here/moonshine_sdram_burst.sv" \
 "$here/sdram_model_burst_verilator.sv" "$here/../moonbub_tile_transpose.sv" \
 "$fpga/rtl/moonshine_core.sv" "$fpga/rtl/moonshine_lcd.sv" "${files[@]}"
ulimit -c 0
# FAIL and timeout remain nonzero, including the known strict/stock failure.
timeout 300s "$build/obj/V$top" "+FIXTURE_DIR=$build/fixtures" "+DUMP_DIR=$build/dumps"
"${CXX:-g++}" -std=c++17 -O2 -I"$fpga/vendor/core_jpeg/c_model" \
 "$root/host/evidence/jpeg-c-model-fixed-color-main.cpp" -o "$build/jpeg-cmodel"
for ((frame=0; frame<10; frame++)); do
 printf -v stem '%04d' "$frame"
 "$build/jpeg-cmodel" "$build/fixtures/$stem.jpg" "$build/$stem-cmodel.ppm" > "$build/$stem-cmodel.log"
 # Exact reference is a shared-algorithm C implementation, not independent.
 "${PYTHON:-python3}" "$here/compare-frame.py" "$build/$stem-cmodel.ppm" "$build/dumps/$stem-rgb565.txt" --exact > "$build/$stem-cmodel-comparison.json"
 # Independent Pillow comparison is reported, not silently treated as exact.
 "${PYTHON:-python3}" "$here/compare-frame.py" "$build/fixtures/$stem.jpg" "$build/dumps/$stem-rgb565.txt" > "$build/$stem-pillow-comparison.json"
done
printf 'All 10 shared-algorithm pixel comparisons passed; Pillow metrics in %s\n' "$build"
