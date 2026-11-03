#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
: "${FPGA_DIR:?}" "${BUILD_DIR:?}"
yosys=${YOSYS:-yosys};src=$FPGA_DIR/vendor/core_jpeg/src_v
mkdir -p "$(dirname "$BUILD_DIR")";mkdir "$BUILD_DIR"
python3 "$here/prepare.py" "$src/jpeg_idct_transpose.v" "$BUILD_DIR/audit-transpose.v"
sha256sum "$here"/{prepare.py,harness.v} "$src"/{jpeg_idct_transpose.v,jpeg_idct_transpose_ram.v} "$BUILD_DIR/audit-transpose.v" > "$BUILD_DIR/source-sha256.txt"
"$yosys" -V > "$BUILD_DIR/version.txt"
script="read_verilog -formal $BUILD_DIR/audit-transpose.v $src/jpeg_idct_transpose_ram.v $here/harness.v; prep -top harness -flatten; opt_clean; sat -seq 268 -prove-asserts -set-init-zero -verify"
timeout 90s "$yosys" -p "$script" > "$BUILD_DIR/proof.log" 2>&1
grep -q 'SAT proof finished - no model found: SUCCESS!' "$BUILD_DIR/proof.log"
echo CYCLE_PROOF_BOUNDED_PASS
sed 's/remaining<=2/remaining<=1/' "$here/harness.v" > "$BUILD_DIR/gap1-mutant.v"
sed 's/snapshot_control<=control/snapshot_control<=control ^ 16\x27h0001/' "$here/harness.v" > "$BUILD_DIR/snapshot-mutant.v"
for mutant in gap1 snapshot;do
 script="read_verilog -formal $BUILD_DIR/audit-transpose.v $src/jpeg_idct_transpose_ram.v $BUILD_DIR/$mutant-mutant.v; prep -top harness -flatten; opt_clean; sat -seq 268 -prove-asserts -set-init-zero -verify"
 set +e
 timeout 90s "$yosys" -p "$script" > "$BUILD_DIR/$mutant-negative.log" 2>&1
 status=$?
 set -e
 if [[ $status != 1 ]] || ! grep -q 'proof did fail' "$BUILD_DIR/$mutant-negative.log";then echo "negative control $mutant inconclusive exit=$status" >&2;exit 1;fi
 echo "NEGATIVE_CONTROL_PASS $mutant"
done
