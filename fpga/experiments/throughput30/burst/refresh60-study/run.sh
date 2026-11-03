#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
burst=$(cd -- "$here/.." && pwd);fpga=$(cd -- "$burst/../../.." && pwd);root=$(cd -- "$fpga/.." && pwd)
: "${FIXTURE_DIR:?Provide an existing compatible fixture directory}"
: "${BUILD_DIR:?Provide a new empty output directory}"
if [[ -d $BUILD_DIR && -n $(ls -A "$BUILD_DIR") ]];then echo 'BUILD_DIR must be empty' >&2;exit 2;fi
mkdir -p "$BUILD_DIR"; build=$(cd "$BUILD_DIR" && pwd);fixture=$(cd "$FIXTURE_DIR" && pwd)
frames=${FRAMES:-300};python=${PYTHON:-python3}
files=(); for f in "$fpga"/vendor/core_jpeg/src_v/*.v;do [[ $f == */jpeg_input.v ]] || files+=("$f");done
verilator --binary --timing --assert -Wno-fatal -DSIMULATION --top-module tb_qspi_refresh60 --Mdir "$build/obj" \
 "$here/tb_qspi_refresh60.sv" "$fpga/rtl/moonshine_qspi_endpoint.sv" "$fpga/rtl/moonshine_bus_cdc.sv" \
 "$burst/marker-followup/jpeg_input_followup.v" "$burst/moonshine_memory_burst.sv" "$burst/moonshine_sdram_burst.sv" \
 "$burst/sdram_model_burst_verilator.sv" "$burst/../moonbub_tile_transpose.sv" "$fpga/rtl/moonshine_core.sv" "$fpga/rtl/moonshine_lcd.sv" "${files[@]}" > "$build/build.log" 2>&1
"${CXX:-g++}" -std=c++17 -O2 -I"$fpga/vendor/core_jpeg/c_model" "$root/host/evidence/jpeg-c-model-fixed-color-main.cpp" -o "$build/jpeg-cmodel"
ulimit -c 0
"$python" "$burst/gameplay-study/check-gameplay.py" --binary "$build/obj/Vtb_qspi_refresh60" --fixtures "$fixture" --work "$build/checked" \
 --cmodel "$build/jpeg-cmodel" --compare "$burst/compare-frame.py" --frames "$frames" --timeout "${TIMEOUT_SECONDS:-6000}" --strict 1 | tee "$build/stream.log"
printf 'REFRESH60_SCHEDULE_PASS output=%s\n' "$build"
