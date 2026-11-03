#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
burst=$(cd -- "$here/.." && pwd)
fpga=$(cd -- "$burst/../../.." && pwd)
build=${BUILD_DIR:-$(mktemp -d)}
if [[ -d $build && -n $(ls -A "$build") ]]; then echo 'BUILD_DIR must be empty' >&2;exit 2;fi
mkdir -p "$build";build=$(cd -- "$build" && pwd)
fixture=${JPEG_FILE:-$fpga/sim/pipeline64-420.jpg}
files=(); for f in "$fpga"/vendor/core_jpeg/src_v/*.v; do [[ $f == */jpeg_input.v ]] || files+=("$f"); done
verilator --binary --timing --assert -Wno-fatal -DSIMULATION -GFLUSH_COLLECTOR=1 --top-module tb_abort_sweep --Mdir "$build/obj" \
 "$here/tb_abort_sweep.sv" "$here/moonshine_memory_burst_abort.sv" "$burst/moonshine_sdram_burst.sv" \
 "$burst/sdram_model_burst_verilator.sv" "$burst/marker-followup/jpeg_input_followup.v" \
 "$burst/../moonbub_tile_transpose.sv" "$fpga/rtl/moonshine_core.sv" "$fpga/rtl/moonshine_lcd.sv" "${files[@]}" > "$build/build.log" 2>&1
ulimit -c 0
for mode in 0 1; do for target in $(seq 0 63); do
 timeout 120s "$build/obj/Vtb_abort_sweep" "+JPEG_FILE=$fixture" "+MODE=$mode" "+TARGET=$target" > "$build/latest.log" 2>&1
 grep -q "SWEEP_BEFORE_ABORT mode=$mode target=$target" "$build/latest.log"
 grep -q TEST_PASS_ABORT_SWEEP "$build/latest.log"
 echo "PASS mode=$mode target=$target" | tee -a "$build/summary.log"
done; done
