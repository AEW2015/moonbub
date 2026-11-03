#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
burst=$(cd -- "$here/.." && pwd)
fpga=$(cd -- "$burst/../../.." && pwd)
: "${BASE_BUILD_DIR:?Set BASE_BUILD_DIR to a completed network-rtl-study build}"
base=$(cd -- "$BASE_BUILD_DIR" && pwd)
build=${BUILD_DIR:-$(mktemp -d)}
if [[ -d "$build" && -n "$(ls -A "$build")" ]]; then echo 'BUILD_DIR must be empty' >&2; exit 2; fi
mkdir -p "$build/dumps" "$build/corrupt-dumps" "$build/missing-dumps";build=$(cd -- "$build" && pwd)
python3 "$here/packet_trace.py" --fixtures "$base/fixtures" --output "$build/trace.txt"
files=();for f in "$fpga"/vendor/core_jpeg/src_v/*.v;do [[ "$f" == */jpeg_input.v ]] || files+=("$f");done
verilator --binary --timing --assert -Wno-fatal -DSIMULATION --top-module tb_packet_stream --Mdir "$build/obj" \
 "$here/tb_packet_stream.sv" "$burst/cdc-credit/moonshine_qspi_endpoint_credit.sv" "$burst/cdc-credit/moonshine_bus_cdc_credit.sv" \
 "$burst/moonshine_memory_burst.sv" "$burst/moonshine_sdram_burst.sv" "$burst/sdram_model_burst_verilator.sv" \
 "$burst/marker-followup/jpeg_input_followup.v" "$burst/../moonbub_tile_transpose.sv" "$fpga/rtl/moonshine_core.sv" \
 "$fpga/rtl/moonshine_lcd.sv" "${files[@]}"
ulimit -c 0
timeout 400s "$build/obj/Vtb_packet_stream" "+FIXTURE_DIR=$base/fixtures" "+DUMP_DIR=$build/dumps" "+TRACE_FILE=$build/trace.txt" > "$build/run.log"
python3 "$here/verify.py" "$build/run.log" "$build/trace.txt"
"$base/cmodel" "$base/fixtures/0000.jpg" "$build/cmodel.ppm" > "$build/cmodel.log"
python3 "$burst/compare-frame.py" "$build/cmodel.ppm" "$build/dumps/0000-rgb565.txt" --exact > "$build/comparison.json"
if timeout 400s "$build/obj/Vtb_packet_stream" "+FIXTURE_DIR=$base/fixtures" "+DUMP_DIR=$build/corrupt-dumps" "+TRACE_FILE=$build/trace.txt" +CORRUPT_OFFSET=1000 > "$build/corrupt.log" 2>&1;then
 echo 'corrupt control unexpectedly passed' >&2;exit 1
fi
grep -q 'invalid packet completion or CRC' "$build/corrupt.log"
if grep -q '^TEST_PASS_PACKET_STREAM' "$build/corrupt.log";then echo 'corrupt control contained PASS' >&2;exit 1;fi
timeout 400s "$build/obj/Vtb_packet_stream" "+FIXTURE_DIR=$base/fixtures" "+DUMP_DIR=$build/missing-dumps" "+TRACE_FILE=$build/trace.txt" +DROP_PACKET=5 > "$build/missing.log"
python3 "$here/verify_missing.py" "$build/missing.log" "$build/trace.txt"
printf 'PASS: streaming packet/CRC and exact related C-model checks; output: %s\n' "$build"
