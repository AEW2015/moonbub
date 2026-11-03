#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
: "${FPGA_DIR:?}" "${BUILD_DIR:?}"
yosys=${YOSYS:-yosys};src=$FPGA_DIR/vendor/core_jpeg/src_v
mkdir -p "$(dirname "$BUILD_DIR")";mkdir "$BUILD_DIR"
"$yosys" -V > "$BUILD_DIR/version.txt"
sha256sum "$here/restart-negative.v" "$src"/jpeg_idct*.v > "$BUILD_DIR/source-sha256.txt"
script="read_verilog -formal $src/jpeg_idct_ram.v $src/jpeg_idct_ram_dp.v $src/jpeg_idct_x.v $here/restart-negative.v; prep -top harness -flatten; opt_clean; sat -seq 100 -prove-asserts -set-init-zero -show-all -dump_vcd $BUILD_DIR/restart.vcd"
timeout 60s "$yosys" -p "$script" > "$BUILD_DIR/restart.log" 2>&1
grep -q 'SAT proof finished - model found: FAIL!' "$BUILD_DIR/restart.log"
test -s "$BUILD_DIR/restart.vcd"
echo UNCONSTRAINED_RESTART_COUNTEREXAMPLE_FOUND
