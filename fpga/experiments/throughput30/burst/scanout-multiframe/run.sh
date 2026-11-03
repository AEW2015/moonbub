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
if [[ -n ${FIXTURE_DIR:-} ]]; then fixture=$(cd "$FIXTURE_DIR" && pwd); checker=$burst/gameplay-study/check-gameplay.py; else
 checker=$burst/qspi-longrun/stream-check-qspi.py
 "$python" "$burst/longrun-study/generate-jpegs.py" "$build/fixtures" --frames 10; fixture=$build/fixtures
fi
files=(); for f in "$fpga"/vendor/core_jpeg/src_v/*.v; do [[ $f == */jpeg_input.v ]] || files+=("$f"); done
verilator --binary --timing --assert -Wno-fatal -DSIMULATION --top-module tb_scanout_multiframe --Mdir "$build/obj" \
 "$here/tb_scanout_multiframe.sv" "$fpga/rtl/moonshine_qspi_endpoint.sv" "$fpga/rtl/moonshine_bus_cdc.sv" \
 "$burst/marker-followup/jpeg_input_followup.v" "$burst/moonshine_memory_burst.sv" "$burst/moonshine_sdram_burst.sv" \
 "$burst/sdram_model_burst_verilator.sv" "$burst/../moonbub_tile_transpose.sv" "$fpga/rtl/moonshine_core.sv" \
 "$fpga/rtl/moonshine_lcd.sv" "${files[@]}" > "$build/build.log" 2>&1
"${CXX:-g++}" -std=c++17 -O2 -I"$fpga/vendor/core_jpeg/c_model" "$root/host/evidence/jpeg-c-model-fixed-color-main.cpp" -o "$build/jpeg-cmodel"
ulimit -c 0
"$python" "$checker" --binary "$build/obj/Vtb_scanout_multiframe" --fixtures "$fixture" \
 --work "$build/checked" --cmodel "$build/jpeg-cmodel" --compare "$burst/compare-frame.py" --frames 10 --timeout 1200 --strict 0 | tee "$build/stream.log"
grep -q '^MULTIFRAME_SCANOUT_PASS scans=[0-9]* checked_ids=10 last_id=10$' "$build/checked/simulation.log"
printf 'Multi-frame scanout check complete: %s\n' "$build"
