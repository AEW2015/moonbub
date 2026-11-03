#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
: "${FPGA_DIR:?}" "${BUILD_DIR:?}"
yosys=${YOSYS:-yosys};src=$FPGA_DIR/vendor/core_jpeg/src_v
mkdir -p "$(dirname "$BUILD_DIR")";mkdir "$BUILD_DIR"
python3 "$here/../cycle-proof/prepare.py" "$src/jpeg_idct_transpose.v" "$BUILD_DIR/audit-transpose.v"
"$yosys" -V > "$BUILD_DIR/version.txt"
sha256sum "$here"/{miter.v,reach.py,run.sh} "$here/../cycle-proof/prepare.py" "$src"/{jpeg_idct_transpose.v,jpeg_idct_transpose_ram.v} "$BUILD_DIR/audit-transpose.v" > "$BUILD_DIR/source-sha256.txt"
script="read_verilog -formal $BUILD_DIR/audit-transpose.v $src/jpeg_idct_transpose_ram.v $here/miter.v; prep -top miter -flatten; opt_clean; sat -seq 3 -prove-asserts -set-assumes -verify"
timeout 30s "$yosys" -p "$script" > "$BUILD_DIR/miter.log" 2>&1
grep -q 'SAT proof finished - no model found: SUCCESS!' "$BUILD_DIR/miter.log"
sed 's/ri<=ri+1/ri<=ri+2/' "$here/miter.v" > "$BUILD_DIR/mutant.v"
script="read_verilog -formal $BUILD_DIR/audit-transpose.v $src/jpeg_idct_transpose_ram.v $BUILD_DIR/mutant.v; prep -top miter -flatten; opt_clean; sat -seq 3 -prove-asserts -set-assumes -verify"
set +e; timeout 30s "$yosys" -p "$script" > "$BUILD_DIR/mutant.log" 2>&1; status=$?;set -e
[[ $status == 1 ]] && grep -q 'proof did fail' "$BUILD_DIR/mutant.log"
python3 "$here/reach.py" --gap 2 > "$BUILD_DIR/gap2.log"
set +e;python3 "$here/reach.py" --gap 1 > "$BUILD_DIR/gap1-negative.log";status=$?;set -e
[[ $status == 1 ]] && grep -q '^REJECT gap=1' "$BUILD_DIR/gap1-negative.log"
echo VARIABLE_GAP_PROOF_PASS
verilator=${VERILATOR:-verilator}
"$verilator" --version > "$BUILD_DIR/verilator-version.txt"
python3 "$here/vectors.py" "$BUILD_DIR/vectors.txt"
"$verilator" --binary --timing -Wno-fatal --top-module crosscheck --Mdir "$BUILD_DIR/obj" "$BUILD_DIR/audit-transpose.v" "$src/jpeg_idct_transpose_ram.v" "$here/miter.v" "$here/crosscheck.sv" > "$BUILD_DIR/build.log" 2>&1
timeout 30s "$BUILD_DIR/obj/Vcrosscheck" "+VECTORS=$BUILD_DIR/vectors.txt" > "$BUILD_DIR/crosscheck.log" 2>&1
grep -q 'MODEL_CROSSCHECK_PASS transitions=16384' "$BUILD_DIR/crosscheck.log"
sha256sum "$here"/{vectors.py,crosscheck.sv} >> "$BUILD_DIR/source-sha256.txt"
echo MODEL_CROSSCHECK_WRAPPER_PASS
