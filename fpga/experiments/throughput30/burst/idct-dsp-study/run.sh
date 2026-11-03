#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
fpga=$(cd -- "$here/../../../.." && pwd)
build=${BUILD_DIR:-$(mktemp -d)}
mkdir -p "$build"; build=$(cd -- "$build" && pwd)
yosys=${YOSYS:-yosys}
"$yosys" -V | tee "$build/version.txt"
cd "$fpga/vendor/core_jpeg/src_v"
sha256sum jpeg_idct_x.v jpeg_idct_y.v > "$build/sources.sha256"
for axis in x y; do
 timeout 600s "$yosys" -p "read_verilog jpeg_idct_$axis.v; synth_xilinx -family xc7 -top jpeg_idct_$axis -run begin:coarse; stat" > "$build/$axis.log" 2>&1
 grep -q 'End of script' "$build/$axis.log"
 grep 'DSP48E1' "$build/$axis.log" | tail -1
done
printf 'Intermediate mapping logs: %s\n' "$build"
