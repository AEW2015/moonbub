#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
burst=$(cd -- "$here/.." && pwd)
fpga=$(cd -- "$here/../../../.." && pwd)
root=$(cd -- "$fpga/.." && pwd)
build=${BUILD_DIR:-$(mktemp -d)}
mkdir -p "$build"; build=$(cd -- "$build" && pwd)
"${PYTHON:-python3}" "$root/experiments/fixture30/generate.py" "$build/fixtures" --frames 10
verilator --version
verilator --binary --timing --assert -Wno-fatal --top-module tb_entropy_backpressure --Mdir "$build/obj" \
 "$here/tb_entropy_backpressure.sv" "$burst/marker-followup/jpeg_input_followup.v"
ulimit -c 0
"${PYTHON:-python3}" "$here/run_entropy_stress.py" --sim "$build/obj/Vtb_entropy_backpressure" \
 --fixtures "$build/fixtures" --frames 10 --seeds "${SEEDS:-30}" --output "$build/results.json"
printf 'Results: %s\n' "$build/results.json"
