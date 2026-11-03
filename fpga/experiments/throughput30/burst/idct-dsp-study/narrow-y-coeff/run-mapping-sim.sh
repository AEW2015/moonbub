#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
: "${ORIGINAL:?Set ORIGINAL to jpeg_idct_y.v}"
: "${BUILD_DIR:?Set BUILD_DIR to a new path}"
yosys=${YOSYS:-yosys};verilator=${VERILATOR:-verilator}
mkdir -p "$(dirname "$BUILD_DIR")";mkdir "$BUILD_DIR";build=$(cd "$BUILD_DIR" && pwd)
"$yosys" -V > "$build/yosys-version.txt";"$verilator" --version > "$build/verilator-version.txt"
for kind in original candidate;do
 top=jpeg_idct_y;src=$ORIGINAL;if [[ $kind = candidate ]];then top=jpeg_idct_y_coeff;src=$here/jpeg_idct_y_coeff.v;fi
 timeout 180s "$yosys" -p "read_verilog $src; synth_xilinx -family xc7 -top $top -run begin:coarse; stat" > "$build/$kind-map.log" 2>&1
 grep -q 'End of script' "$build/$kind-map.log";grep 'DSP48E1' "$build/$kind-map.log" | tail -1
done
"$verilator" --binary --timing --assert -Wno-fatal --top-module tb_narrow_y --Mdir "$build/obj" "$here/tb_narrow_y.sv" "$ORIGINAL" "$here/jpeg_idct_y_coeff.v" > "$build/sim-build.log" 2>&1
timeout 60s "$build/obj/Vtb_narrow_y" > "$build/sim.log" 2>&1
grep -q '^NARROW_Y_COEFF_EQ_PASS cycles=100000' "$build/sim.log"
echo NARROW_Y_MAPPING_AND_SIM_PASS
