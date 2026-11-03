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
: "${FIXTURE_DIR:?Provide an existing 90-frame fixture directory}"
fixture=$(cd "$FIXTURE_DIR" && pwd);checker=$burst/gameplay-study/check-gameplay.py
# Rename only the candidate copy to satisfy the unchanged JPEG-core instance.
sed 's/module jpeg_idct_x_narrow$/module jpeg_idct_x/' "$here/jpeg_idct_x_narrow.v" > "$build/jpeg_idct_x.v"
files=();for f in "$fpga"/vendor/core_jpeg/src_v/*.v;do [[ $f == */jpeg_input.v || $f == */jpeg_idct_x.v ]] || files+=("$f");done
verilator --binary --timing --assert -Wno-fatal -DSIMULATION --top-module tb_scanout_multiframe --Mdir "$build/obj" \
 "$burst/scanout-multiframe/tb_scanout_multiframe.sv" "$fpga/rtl/moonshine_qspi_endpoint.sv" "$fpga/rtl/moonshine_bus_cdc.sv" \
 "$burst/marker-followup/jpeg_input_followup.v" "$burst/moonshine_memory_burst.sv" "$burst/moonshine_sdram_burst.sv" \
 "$burst/sdram_model_burst_verilator.sv" "$burst/../moonbub_tile_transpose.sv" "$fpga/rtl/moonshine_core.sv" \
 "$fpga/rtl/moonshine_lcd.sv" "$build/jpeg_idct_x.v" "${files[@]}" > "$build/build.log" 2>&1
"${CXX:-g++}" -std=c++17 -O2 -I"$fpga/vendor/core_jpeg/c_model" "$root/host/evidence/jpeg-c-model-fixed-color-main.cpp" -o "$build/jpeg-cmodel"
ulimit -c 0
"$python" "$checker" --binary "$build/obj/Vtb_scanout_multiframe" --fixtures "$fixture" \
 --work "$build/checked" --cmodel "$build/jpeg-cmodel" --compare "$burst/compare-frame.py" --frames 90 --timeout 3600 --strict 0 | tee "$build/stream.log"
grep -q '^MULTIFRAME_SCANOUT_PASS scans=[0-9]* checked_ids=90 last_id=90$' "$build/checked/simulation.log"
echo "NARROW_X_MULTIFRAME_PASS output=$build"
