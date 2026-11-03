#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
burst=$(cd -- "$here/../.." && pwd)
fpga=$(cd -- "$burst/../../.." && pwd)
root=$(cd -- "$fpga/.." && pwd)
build=${BUILD_DIR:-$(mktemp -d)}
if [[ -d $build && -n $(ls -A "$build") ]]; then echo 'BUILD_DIR must be empty' >&2;exit 2;fi
mkdir -p "$build";build=$(cd "$build" && pwd)
python=${PYTHON:-python3}
if [[ -n ${FIXTURE_DIR:-} ]]; then fixture=$(cd "$FIXTURE_DIR" && pwd); checker=$burst/gameplay-study/check-gameplay.py; else
 checker=$burst/qspi-longrun/stream-check-qspi.py
 "$python" "$burst/longrun-study/generate-jpegs.py" "$build/fixtures" --frames 1;fixture=$build/fixtures
fi
# Rename only the candidate copy to satisfy the unchanged JPEG-core instance.
sed 's/module jpeg_idct_x_narrow$/module jpeg_idct_x/' "$here/jpeg_idct_x_narrow.v" > "$build/jpeg_idct_x.v"
files=();for f in "$fpga"/vendor/core_jpeg/src_v/*.v;do [[ $f == */jpeg_input.v || $f == */jpeg_idct_x.v ]] || files+=("$f");done
verilator --binary --timing --assert -Wno-fatal -DSIMULATION --top-module tb_scanout_check --Mdir "$build/obj" \
 "$burst/scanout-study/tb_scanout_check.sv" "$fpga/rtl/moonshine_qspi_endpoint.sv" "$fpga/rtl/moonshine_bus_cdc.sv" \
 "$burst/marker-followup/jpeg_input_followup.v" "$burst/moonshine_memory_burst.sv" "$burst/moonshine_sdram_burst.sv" \
 "$burst/sdram_model_burst_verilator.sv" "$burst/../moonbub_tile_transpose.sv" "$fpga/rtl/moonshine_core.sv" \
 "$fpga/rtl/moonshine_lcd.sv" "$build/jpeg_idct_x.v" "${files[@]}" > "$build/build.log" 2>&1
"${CXX:-g++}" -std=c++17 -O2 -I"$fpga/vendor/core_jpeg/c_model" "$root/host/evidence/jpeg-c-model-fixed-color-main.cpp" -o "$build/jpeg-cmodel"
ulimit -c 0
"$python" "$checker" --binary "$build/obj/Vtb_scanout_check" --fixtures "$fixture" \
 --work "$build/checked" --cmodel "$build/jpeg-cmodel" --compare "$burst/compare-frame.py" --frames 1 --timeout 900 --strict 0 | tee "$build/stream.log"
grep -q '^SCANOUT_CHECK_PASS pixels=345600$' "$build/checked/simulation.log"
echo "NARROW_X_PIPELINE_PASS output=$build"
