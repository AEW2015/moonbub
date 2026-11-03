#!/usr/bin/env bash
set -u
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
: "${FPGA_DIR:?}" "${BUILD_DIR:?}"
yosys=${YOSYS:-yosys};src=$FPGA_DIR/vendor/core_jpeg/src_v
mkdir -p "$(dirname "$BUILD_DIR")";mkdir "$BUILD_DIR" || exit 1
"$yosys" -V > "$BUILD_DIR/version.txt"
sha256sum "$here/harness.v" "$src/jpeg_idct_transpose.v" "$src/jpeg_idct_transpose_ram.v" > "$BUILD_DIR/source-sha256.txt"
for gap in 0 1 2 3;do
 script="read_verilog -formal $src/jpeg_idct_transpose.v $src/jpeg_idct_transpose_ram.v $here/harness.v; chparam -set GAP $gap harness; prep -top harness -flatten; opt_clean; sat -seq 300 -prove-asserts -set-init-zero -show-all -dump_vcd $BUILD_DIR/gap-$gap.vcd"
 timeout 60s "$yosys" -p "$script" > "$BUILD_DIR/gap-$gap.log" 2>&1
 echo "gap=$gap exit=$?"
done
