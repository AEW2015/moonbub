#!/usr/bin/env bash
set -u
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
: "${FPGA_DIR:?}" "${BUILD_DIR:?}"
yosys=${YOSYS:-yosys};src=$FPGA_DIR/vendor/core_jpeg/src_v
mkdir -p "$(dirname "$BUILD_DIR")";mkdir "$BUILD_DIR" || exit 1
"$yosys" -V > "$BUILD_DIR/version.txt"
sha256sum "$here/harness.v" "$src"/jpeg_idct*.v > "$BUILD_DIR/source-sha256.txt"
base="read_verilog -formal $src/jpeg_idct_ram.v $src/jpeg_idct_ram_dp.v $src/jpeg_idct_x.v $here/harness.v; prep -top harness -flatten; opt_clean"
timeout 90s "$yosys" -p "$base; sat -seq 200 -prove-asserts -set-init-zero -verify" > "$BUILD_DIR/bmc.log" 2>&1
echo "BMC_EXIT=$?"
timeout 90s "$yosys" -p "$base; sat -seq 10 -tempinduct -maxsteps 100 -prove-asserts -set-init-zero -verify" > "$BUILD_DIR/induct.log" 2>&1
echo "INDUCT_EXIT=$?"
