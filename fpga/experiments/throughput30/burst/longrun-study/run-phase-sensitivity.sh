#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
burst=$(cd -- "$here/.." && pwd)
fpga=$(cd -- "$here/../../../.." && pwd)
root=$(cd -- "$fpga/.." && pwd)
build=${BUILD_DIR:-$(mktemp -d)}
mkdir -p "$build"; build=$(cd -- "$build" && pwd)
[[ ! -e "$build/fixtures" ]] || { echo 'fixture destination exists' >&2; exit 2; }
"${PYTHON:-python3}" "$here/generate-jpegs.py" "$build/fixtures" --frames 10
files=()
for f in "$fpga"/vendor/core_jpeg/src_v/*.v; do [[ "$f" == */jpeg_input.v ]] || files+=("$f"); done
verilator --version
verilator --binary --timing --assert -Wno-fatal -DSIMULATION --top-module tb_jpeg720_phase_sensitivity --Mdir "$build/obj" \
 "$here/tb_jpeg720_phase_sensitivity.sv" "$burst/marker-audit/jpeg_input_candidate.v" \
 "$burst/moonshine_memory_burst.sv" "$burst/moonshine_sdram_burst.sv" "$burst/sdram_model_burst_verilator.sv" \
 "$burst/../moonbub_tile_transpose.sv" "$fpga/rtl/moonshine_core.sv" "$fpga/rtl/moonshine_lcd.sv" "${files[@]}"
"${CXX:-g++}" -std=c++17 -O2 -I"$fpga/vendor/core_jpeg/c_model" "$root/host/evidence/jpeg-c-model-fixed-color-main.cpp" -o "$build/cmodel"
ulimit -c 0
for phase in 0 250000 768338; do
 mkdir "$build/dumps-$phase"
 timeout 180s "$build/obj/Vtb_jpeg720_phase_sensitivity" "+FIXTURE_DIR=$build/fixtures" "+DUMP_DIR=$build/dumps-$phase" +FRAMES=10 +STRICT_WINDOW=1 "+PHASE_CYCLES=$phase" | tee "$build/phase-$phase.log"
 grep -q '^TEST_PASS_JPEG720_PHASE frames=10 ' "$build/phase-$phase.log"
 for ((frame=0;frame<10;frame++)); do
  printf -v stem '%04d' "$frame"
  if [[ ! -f "$build/$stem.ppm" ]]; then "$build/cmodel" "$build/fixtures/$stem.jpg" "$build/$stem.ppm" > "$build/$stem-cmodel.log"; fi
  "${PYTHON:-python3}" "$burst/compare-frame.py" "$build/$stem.ppm" "$build/dumps-$phase/$stem-rgb565.txt" --exact > "$build/$phase-$stem-compare.json"
 done
done
printf 'All 30 phase experiment frames matched related C-model output: %s\n' "$build"
