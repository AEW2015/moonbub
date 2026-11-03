#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
root=$(cd "$here/../../../../../.." && pwd)
src=$root/fpga/vendor/core_jpeg/src_v
: "${BUILD_DIR:?Set BUILD_DIR to a new path}"
yosys=${YOSYS:-yosys}
mkdir -p "$(dirname "$BUILD_DIR")";mkdir "$BUILD_DIR";build=$(cd "$BUILD_DIR" && pwd)
"$yosys" -V > "$build/version.txt"
timeout 90s "$yosys" -p "read_verilog $src/jpeg_idct*.v; hierarchy -check -top jpeg_idct; proc; write_json $build/elab.json" > "$build/elab.log" 2>&1
grep -q 'End of script' "$build/elab.log"
python3 "$here/audit.py" "$build/elab.json" | tee "$build/audit.log"

# Negative control must find the expected counterexample: equal initial RAMs,
# reset high, different writes; RAM read data differs by step 3.
timeout 90s "$yosys" -p "read_verilog -formal $src/jpeg_idct_transpose_ram.v $here/reset-ram-control.v; hierarchy -top reset_ram_control; proc -noopt; flatten; opt_expr; opt_clean; memory_collect; memory_map; opt_expr; opt_clean; sat -set-init-zero -seq 3 -set rst 1 -prove mismatch 0 -show mismatch" > "$build/reset-control.log" 2>&1
grep -q 'SAT proof finished - model found: FAIL!' "$build/reset-control.log"
grep -Eq '^ *1 +\\mismatch +0 ' "$build/reset-control.log"
grep -Eq '^ *3 +\\mismatch +1 ' "$build/reset-control.log"
echo RESET_RAM_NEGATIVE_CONTROL_PASS
