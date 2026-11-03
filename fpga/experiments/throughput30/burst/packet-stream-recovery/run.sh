#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
burst=$(cd -- "$here/.." && pwd)
fpga=$(cd -- "$burst/../../.." && pwd)
: "${BASE_BUILD_DIR:?Set BASE_BUILD_DIR to a completed network-rtl-study build}"
base=$(cd -- "$BASE_BUILD_DIR" && pwd)
build=${BUILD_DIR:-$(mktemp -d)}
if [[ -d "$build" && -n "$(ls -A "$build")" ]];then echo 'BUILD_DIR must be empty' >&2;exit 2;fi
mkdir -p "$build/dumps";build=$(cd -- "$build" && pwd)
python3 "$here/packet_trace.py" --fixtures "$base/fixtures" --output "$build/trace.txt"
files=();for f in "$fpga"/vendor/core_jpeg/src_v/*.v;do [[ "$f" == */jpeg_input.v ]] || files+=("$f");done
verilator --binary --timing --assert -Wno-fatal -DSIMULATION --top-module tb_packet_recovery --Mdir "$build/obj" \
 "$here/tb_packet_recovery.sv" "$burst/cdc-credit/moonshine_qspi_endpoint_credit.sv" "$burst/cdc-credit/moonshine_bus_cdc_credit.sv" \
 "$burst/moonshine_memory_burst.sv" "$burst/moonshine_sdram_burst.sv" "$burst/sdram_model_burst_verilator.sv" \
 "$burst/marker-followup/jpeg_input_followup.v" "$burst/../moonbub_tile_transpose.sv" "$fpga/rtl/moonshine_core.sv" \
 "$fpga/rtl/moonshine_lcd.sv" "${files[@]}"
ulimit -c 0
timeout 400s "$build/obj/Vtb_packet_recovery" "+FIXTURE_DIR=$base/fixtures" "+DUMP_DIR=$build/dumps" "+TRACE_FILE=$build/trace.txt" > "$build/run.log"
python3 "$here/verify.py" "$build/run.log" "$build/trace.txt"
for spec in 'preload 0002' 'recovery 0001';do
 read -r name id <<< "$spec"
 "$base/cmodel" "$base/fixtures/$id.jpg" "$build/$name.ppm" > "$build/$name-cmodel.log"
 python3 "$burst/compare-frame.py" "$build/$name.ppm" "$build/dumps/$name-rgb565.txt" --exact > "$build/$name-comparison.json"
done
printf 'PASS: original-core partial receive abort and next-frame recovery; output %s\n' "$build"
