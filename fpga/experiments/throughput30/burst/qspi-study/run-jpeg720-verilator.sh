#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
burst=$(cd -- "$here/.." && pwd)
fpga=$(cd -- "$burst/../../.." && pwd)
root=$(cd -- "$fpga/.." && pwd)
build=${BUILD_DIR:-$(mktemp -d)}
mkdir -p "$build"; build=$(cd -- "$build" && pwd)
fixture="$root/host/fixtures/pattern-720x480-420-q65.jpg"
files=()
for f in "$fpga"/vendor/core_jpeg/src_v/*.v; do [[ "$f" == */jpeg_input.v ]] || files+=("$f"); done
verilator --version
verilator --binary --timing --assert -Wno-fatal -DSIMULATION --top-module tb_qspi_jpeg720 --Mdir "$build/obj" \
 "$here/tb_qspi_jpeg720.sv" "$fpga/rtl/moonshine_qspi_endpoint.sv" "$fpga/rtl/moonshine_bus_cdc.sv" \
 "$burst/moonshine_memory_burst.sv" "$burst/moonshine_sdram_burst.sv" "$burst/sdram_model_burst_verilator.sv" \
 "$burst/jpeg_input_guarded.v" "$burst/../moonbub_tile_transpose.sv" "$fpga/rtl/moonshine_core.sv" \
 "$fpga/rtl/moonshine_lcd.sv" "${files[@]}"
ulimit -c 0
timeout 300s "$build/obj/Vtb_qspi_jpeg720" "+JPEG_FILE=$fixture" "+DUMP_FILE=$build/pixels.txt" | tee "$build/run.log"
grep -q '^QSPI_JPEG720_PASS ' "$build/run.log"
"${CXX:-g++}" -std=c++17 -O2 -I"$fpga/vendor/core_jpeg/c_model" \
 "$root/host/evidence/jpeg-c-model-fixed-color-main.cpp" -o "$build/cmodel"
"$build/cmodel" "$fixture" "$build/cmodel.ppm" > "$build/cmodel.log"
"${PYTHON:-python3}" "$burst/compare-frame.py" "$build/cmodel.ppm" "$build/pixels.txt" --exact
