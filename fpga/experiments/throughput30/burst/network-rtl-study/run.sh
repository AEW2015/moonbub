#!/usr/bin/env bash
set -euo pipefail
# Verilator 5.x, make, host rustc, g++, Python/Pillow and GNU timeout.
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
burst=$(cd -- "$here/.." && pwd)
fpga=$(cd -- "$burst/../../.." && pwd)
root=$(cd -- "$fpga/.." && pwd)
build=${BUILD_DIR:-$(mktemp -d)}
if [[ -d "$build" && -n "$(ls -A "$build")" ]]; then echo 'BUILD_DIR must be empty' >&2; exit 2; fi
mkdir -p "$build";build=$(cd -- "$build" && pwd)
python=${PYTHON:-python3};rustc=${RUSTC:-rustc}
cp "$burst/transport-followup/recovery-study/rust_replay.rs" "$root/firmware/handheld/src/streaming/protocol.rs" "$build/"
"$rustc" --edition=2021 -O "$build/rust_replay.rs" -o "$build/rust-replay"
"$python" "$root/experiments/fixture30/generate.py" "$build/fixtures" --frames 10
for kind in clean loss; do
 channel=none; [[ $kind == loss ]] && channel=iid
 "$python" "$here/generate_trace.py" --fixtures "$build/fixtures" --rust-replay "$build/rust-replay" --output "$build/$kind" --channel "$channel"
 mkdir "$build/$kind/dumps"
done
files=(); for f in "$fpga"/vendor/core_jpeg/src_v/*.v; do [[ "$f" == */jpeg_input.v ]] || files+=("$f"); done
verilator --version
verilator --binary --timing --assert -Wno-fatal -DSIMULATION --top-module tb_network_qspi_jpeg --Mdir "$build/obj" \
 "$here/tb_network_qspi_jpeg.sv" "$burst/cdc-credit/moonshine_qspi_endpoint_credit.sv" "$burst/cdc-credit/moonshine_bus_cdc_credit.sv" \
 "$burst/moonshine_memory_burst.sv" "$burst/moonshine_sdram_burst.sv" "$burst/sdram_model_burst_verilator.sv" \
 "$burst/marker-followup/jpeg_input_followup.v" "$burst/../moonbub_tile_transpose.sv" "$fpga/rtl/moonshine_core.sv" \
 "$fpga/rtl/moonshine_lcd.sv" "${files[@]}"
"${CXX:-g++}" -std=c++17 -O2 -I"$fpga/vendor/core_jpeg/c_model" "$root/host/evidence/jpeg-c-model-fixed-color-main.cpp" -o "$build/cmodel"
ulimit -c 0
for kind in clean loss; do
 timeout 400s "$build/obj/Vtb_network_qspi_jpeg" "+FIXTURE_DIR=$build/fixtures" "+DUMP_DIR=$build/$kind/dumps" "+TRACE_FILE=$build/$kind/frame-trace.txt" | tee "$build/$kind/run.log"
 grep -q '^TEST_PASS_NETWORK_QSPI_TRACE' "$build/$kind/run.log"
 "$python" "$here/check_trace.py" --manifest "$build/$kind/trace-manifest.json" --log "$build/$kind/run.log" --fixtures "$build/fixtures" --dumps "$build/$kind/dumps" --cmodel "$build/cmodel" --output "$build/$kind/comparison.json"
done
printf 'Trace and related C-model checks completed; artifacts: %s\n' "$build"
