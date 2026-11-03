#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
fpga=$(cd -- "$here/../.." && pwd)
root=$(cd -- "$fpga/.." && pwd)
build_dir=${BUILD_DIR:-$(mktemp -d)}
mkdir -p "$build_dir"
build_dir=$(cd -- "$build_dir" && pwd)
# The generator refuses to overwrite an existing fixture directory.
"${PYTHON:-python3}" "$root/experiments/fixture30/generate-small.py" "$build_dir/fixtures"
verilator --version
verilator --binary --timing --assert -Wno-fatal -DSIMULATION \
  --top-module tb_pipeline64_multiframe --Mdir "$build_dir/obj" \
  "$here/tb_pipeline64_multiframe.sv" "$fpga/rtl/moonshine_core.sv" \
  "$fpga/rtl/moonshine_memory.sv" "$fpga/rtl/moonshine_sdram.sv" \
  "$fpga/sim/sdram_model.sv" "$fpga"/vendor/core_jpeg/src_v/*.v
(cd "$build_dir/fixtures" && timeout 180s "$build_dir/obj/Vtb_pipeline64_multiframe") | tee "$build_dir/run.log"
grep -q '^MULTIFRAME64_PASS ' "$build_dir/run.log"
