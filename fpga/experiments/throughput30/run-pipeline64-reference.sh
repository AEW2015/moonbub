#!/usr/bin/env bash
set -euo pipefail
# Optional PYTHON points to a Python with Pillow installed.
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
fpga=$(cd -- "$here/../.." && pwd)
root=$(cd -- "$fpga/.." && pwd)
build_dir=${BUILD_DIR:-$(mktemp -d)}
mkdir -p "$build_dir"
build_dir=$(cd -- "$build_dir" && pwd)
cp "$fpga/sim/pipeline64-420.jpg" "$build_dir/"
verilator --version
verilator --binary --timing --assert -Wno-fatal -DSIMULATION \
  --top-module tb_pipeline64_reference --Mdir "$build_dir/obj" \
  "$here/tb_pipeline64_reference.sv" "$fpga/rtl/moonshine_core.sv" \
  "$fpga/rtl/moonshine_memory.sv" "$fpga/rtl/moonshine_sdram.sv" \
  "$fpga/sim/sdram_model.sv" "$fpga"/vendor/core_jpeg/src_v/*.v
(cd "$build_dir" && timeout 180s "$build_dir/obj/Vtb_pipeline64_reference")
"${PYTHON:-python3}" "$root/experiments/fixture30/compare-rtl-pillow.py" \
  "$fpga/sim/pipeline64-420.jpg" "$build_dir/pipeline64-rtl-rgb565.txt"

# The fixed-color C model is a separately executed shared-algorithm oracle.
# It is not an independent JPEG implementation; the Pillow comparison above is.
"${CXX:-g++}" -std=c++17 -O2 -I"$fpga/vendor/core_jpeg/c_model" \
  "$root/host/evidence/jpeg-c-model-fixed-color-main.cpp" -o "$build_dir/cmodel"
"$build_dir/cmodel" "$fpga/sim/pipeline64-420.jpg" "$build_dir/fixed.ppm"
"${PYTHON:-python3}" "$root/experiments/fixture30/compare-rtl-pillow.py" \
  "$build_dir/fixed.ppm" "$build_dir/pipeline64-rtl-rgb565.txt" --require-exact
