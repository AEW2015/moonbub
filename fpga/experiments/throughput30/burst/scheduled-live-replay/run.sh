#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
burst=$(cd -- "$here/.." && pwd)
fpga=$(cd -- "$burst/../../.." && pwd)
: "${BASE_BUILD_DIR:?Set BASE_BUILD_DIR to completed network-rtl-study build}"
: "${BUILD_DIR:?Set BUILD_DIR to a new empty directory}"
base=$(cd -- "$BASE_BUILD_DIR" && pwd)
if [[ -d "$BUILD_DIR" && -n "$(ls -A "$BUILD_DIR")" ]];then echo 'BUILD_DIR must be empty' >&2;exit 2;fi
mkdir -p "$BUILD_DIR";build=$(cd -- "$BUILD_DIR" && pwd)
python3 "$here/prepare_schedule.py" "$build/schedule.bin"
files=();for f in "$fpga"/vendor/core_jpeg/src_v/*.v;do [[ "$f" == */jpeg_input.v ]] || files+=("$f");done
verilator --binary --timing --assert -Wno-fatal -DSIMULATION --top-module tb_scheduled_guest --Mdir "$build/obj" \
 "$here/tb_scheduled_guest.sv" "$burst/cdc-credit/moonshine_qspi_endpoint_credit.sv" "$burst/cdc-credit/moonshine_bus_cdc_credit.sv" \
 "$burst/moonshine_memory_burst.sv" "$burst/moonshine_sdram_burst.sv" "$burst/sdram_model_burst_verilator.sv" \
 "$burst/marker-followup/jpeg_input_followup.v" "$burst/../moonbub_tile_transpose.sv" "$fpga/rtl/moonshine_core.sv" \
 "$fpga/rtl/moonshine_lcd.sv" "${files[@]}" "$here/record_dpi.cpp"
ulimit -c 0
for mode in no-stall stall;do
 mkdir -p "$build/$mode/dumps";stall=0; [[ "$mode" == stall ]] && stall=1000000
 timeout 400s "$build/obj/Vtb_scheduled_guest" "+TRACE_FILE=$build/schedule.bin" "+DUMP_DIR=$build/$mode/dumps" "+STALL_CYCLES=$stall" > "$build/$mode/run.log"
 python3 "$here/verify.py" "$build/$mode/run.log" "$build/schedule.bin" "$mode"
 ids=(2);[[ "$mode" == no-stall ]] && ids=(0 2)
 for id in "${ids[@]}";do
  fixture=$(printf '%04d' "$id");"$base/cmodel" "$base/fixtures/$fixture.jpg" "$build/$mode/$id.ppm" > "$build/$mode/$id-cmodel.log"
  python3 "$burst/compare-frame.py" "$build/$mode/$id.ppm" "$build/$mode/dumps/frame-$id-rgb565.txt" --exact > "$build/$mode/$id-comparison.json"
 done
done
printf 'PASS: offline bounded scheduled guest-data replay %s\n' "$build"
