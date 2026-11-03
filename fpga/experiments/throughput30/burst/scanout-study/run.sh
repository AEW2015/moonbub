#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
burst=$(cd -- "$here/.." && pwd)
fpga=$(cd -- "$burst/../../.." && pwd)
root=$(cd -- "$fpga/.." && pwd)
build=${BUILD_DIR:-$(mktemp -d)}
if [[ -d $build && -n $(ls -A "$build") ]]; then echo 'BUILD_DIR must be empty' >&2;exit 2;fi
mkdir -p "$build";build=$(cd "$build" && pwd)
python=${PYTHON:-python3}
"$python" "$burst/longrun-study/generate-jpegs.py" "$build/fixtures" --frames 1
files=(); for f in "$fpga"/vendor/core_jpeg/src_v/*.v; do [[ $f == */jpeg_input.v ]] || files+=("$f"); done
verilator --binary --timing --assert -Wno-fatal -DSIMULATION --top-module tb_scanout_check --Mdir "$build/obj" \
 "$here/tb_scanout_check.sv" "$fpga/rtl/moonshine_qspi_endpoint.sv" "$fpga/rtl/moonshine_bus_cdc.sv" \
 "$burst/marker-followup/jpeg_input_followup.v" "$burst/moonshine_memory_burst.sv" "$burst/moonshine_sdram_burst.sv" \
 "$burst/sdram_model_burst_verilator.sv" "$burst/../moonbub_tile_transpose.sv" "$fpga/rtl/moonshine_core.sv" \
 "$fpga/rtl/moonshine_lcd.sv" "${files[@]}" > "$build/build.log" 2>&1
"${CXX:-g++}" -std=c++17 -O2 -I"$fpga/vendor/core_jpeg/c_model" "$root/host/evidence/jpeg-c-model-fixed-color-main.cpp" -o "$build/jpeg-cmodel"
ulimit -c 0
"$python" "$burst/qspi-longrun/stream-check-qspi.py" --binary "$build/obj/Vtb_scanout_check" --fixtures "$build/fixtures" \
 --work "$build/checked" --cmodel "$build/jpeg-cmodel" --compare "$burst/compare-frame.py" --frames 1 --timeout 900 --strict 0 | tee "$build/stream.log"
grep -q '^SCANOUT_CHECK_PASS pixels=345600$' "$build/checked/simulation.log"
printf 'Scanout output check complete: %s\n' "$build"
