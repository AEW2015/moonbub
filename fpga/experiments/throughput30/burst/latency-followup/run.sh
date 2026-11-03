#!/usr/bin/env bash
set -euo pipefail
# Reuses clean artifacts from network-rtl-study/run.sh: fixtures, clean trace, cmodel.
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
burst=$(cd -- "$here/.." && pwd)
fpga=$(cd -- "$burst/../../.." && pwd)
: "${BASE_BUILD_DIR:?Set BASE_BUILD_DIR to a completed network-rtl-study build}"
build=${BUILD_DIR:-$(mktemp -d)}
if [[ -d "$build" && -n "$(ls -A "$build")" ]]; then echo 'BUILD_DIR must be empty' >&2; exit 2; fi
mkdir -p "$build";build=$(cd -- "$build" && pwd)
base=$(cd -- "$BASE_BUILD_DIR" && pwd)
files=(); for f in "$fpga"/vendor/core_jpeg/src_v/*.v; do [[ "$f" == */jpeg_input.v ]] || files+=("$f"); done
verilator --binary --timing --assert -Wno-fatal -DSIMULATION --top-module tb_network_latency --Mdir "$build/obj" \
 "$here/tb_network_latency.sv" "$burst/cdc-credit/moonshine_qspi_endpoint_credit.sv" "$burst/cdc-credit/moonshine_bus_cdc_credit.sv" \
 "$burst/moonshine_memory_burst.sv" "$burst/moonshine_sdram_burst.sv" "$burst/sdram_model_burst_verilator.sv" \
 "$burst/marker-followup/jpeg_input_followup.v" "$burst/../moonbub_tile_transpose.sv" "$fpga/rtl/moonshine_core.sv" \
 "$fpga/rtl/moonshine_lcd.sv" "${files[@]}"
ulimit -c 0
python3 "$burst/network-rtl-study/generate_trace.py" --fixtures "$base/fixtures" --rust-replay "$base/rust-replay" --output "$build/faster-link" --channel none --rate-bps 12000000
for kind in baseline optimistic guarded faster-link; do
 phase=0; trace="$base/clean"; case "$kind" in optimistic) phase=1425000;; guarded) phase=1350000;; faster-link) trace="$build/faster-link";; esac
 mkdir -p "$build/$kind/dumps"
 timeout 400s "$build/obj/Vtb_network_latency" "+FIXTURE_DIR=$base/fixtures" "+DUMP_DIR=$build/$kind/dumps" "+TRACE_FILE=$trace/frame-trace.txt" "+PHASE_CYCLES=$phase" > "$build/$kind/run.log"
 python3 "$burst/network-rtl-study/check_trace.py" --manifest "$trace/trace-manifest.json" --log "$build/$kind/run.log" --fixtures "$base/fixtures" --dumps "$build/$kind/dumps" --cmodel "$base/cmodel" --output "$build/$kind/comparison.json"
done
python3 "$here/summarize.py" "$build/baseline/run.log" "$build/optimistic/run.log" "$build/guarded/run.log" "$build/faster-link/run.log"
printf 'Latency phase comparison complete: %s\n' "$build"
