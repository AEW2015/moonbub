#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
: "${FPGA_DIR:?}" "${BUILD_DIR:?}"
verilator=${VERILATOR:-verilator}; src=$FPGA_DIR/vendor/core_jpeg/src_v
mkdir -p "$(dirname "$BUILD_DIR")"; mkdir "$BUILD_DIR"
"$verilator" --version > "$BUILD_DIR/version.txt"
sha256sum "$here/tb_accept_stress.sv" "$src"/jpeg_idct*.v > "$BUILD_DIR/source-sha256.txt"
"$verilator" --binary --timing --assert -Wno-fatal --top-module tb_accept_stress --Mdir "$BUILD_DIR/obj" "$src"/jpeg_idct*.v "$here/tb_accept_stress.sv" > "$BUILD_DIR/build.log" 2>&1
ulimit -c 0
for mode in 0 1; do for seed in 1 2 3 4; do
 timeout 60s "$BUILD_DIR/obj/Vtb_accept_stress" +MODE=$mode +SEED=$seed > "$BUILD_DIR/mode-$mode-seed-$seed.log" 2>&1
 grep -q "ACCEPT_STRESS_PASS seed=$seed mode=$mode blocks=256 accepted=16384 rejected=0" "$BUILD_DIR/mode-$mode-seed-$seed.log"
done; done
echo ACCEPT_STRESS_WRAPPER_PASS
