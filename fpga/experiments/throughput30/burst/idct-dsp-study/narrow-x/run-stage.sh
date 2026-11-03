#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
fpga=$(cd -- "$here/../../../../.." && pwd)
build=${BUILD_DIR:-$(mktemp -d)}
if [[ -d $build && -n $(ls -A "$build") ]]; then echo 'BUILD_DIR must be empty' >&2;exit 2;fi
mkdir -p "$build";build=$(cd "$build" && pwd)
yosys=${YOSYS:-yosys}; "$yosys" -V
for impl in original candidate; do
 top=jpeg_idct_x;src=$fpga/vendor/core_jpeg/src_v/jpeg_idct_x.v
 if [[ $impl == candidate ]]; then top=jpeg_idct_x_narrow;src=$here/jpeg_idct_x_narrow.v;fi
 timeout 600s "$yosys" -p "read_verilog $src; synth_xilinx -family xc7 -top $top -run begin:coarse; stat" > "$build/$impl-map.log" 2>&1
 grep -q 'End of script' "$build/$impl-map.log"
 grep 'DSP48E1' "$build/$impl-map.log" | tail -1
done
verilator --binary --timing --assert -Wno-fatal --top-module tb_narrow_x --Mdir "$build/obj" \
 "$here/tb_narrow_x.sv" "$fpga/vendor/core_jpeg/src_v/jpeg_idct_x.v" "$here/jpeg_idct_x_narrow.v" > "$build/build.log" 2>&1
timeout 180s "$build/obj/Vtb_narrow_x" | tee "$build/sim.log"
grep -q '^NARROW_X_EQ_PASS cycles=100000' "$build/sim.log"
