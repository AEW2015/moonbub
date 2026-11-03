#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
burst=$(cd -- "$here/.." && pwd)
fpga=$(cd -- "$here/../../../.." && pwd)
root=$(cd -- "$fpga/.." && pwd)
build=${BUILD_DIR:-$(mktemp -d)}
mkdir -p "$build"; build=$(cd -- "$build" && pwd)
"${PYTHON:-python3}" "$root/experiments/fixture30/generate.py" "$build/fixtures" --frames 7
ulimit -c 0
verilator --version
for mode in previous followup; do
 if [[ "$mode" == previous ]]; then src="$burst/marker-audit/jpeg_input_candidate.v"; else src="$here/jpeg_input_followup.v"; fi
 verilator --binary --timing --assert -Wno-fatal --top-module tb_real_eoi_last --Mdir "$build/obj-$mode" "$here/tb_real_eoi_last.sv" "$src"
 set +e
 timeout 30s "$build/obj-$mode/Vtb_real_eoi_last" "+JPEG_FILE=$build/fixtures/0006.jpg" > "$build/$mode.log" 2>&1
 status=$?
 set -e
 if [[ "$mode" == previous ]]; then
  if [[ "$status" == 0 || "$status" == 124 ]] || ! grep -q 'unaccepted EOI asserted data_last while blocked' "$build/$mode.log"; then cat "$build/$mode.log"; exit 1; fi
 else
  if [[ "$status" != 0 ]] || ! grep -q 'TEST_PASS_REAL_EOI_LAST' "$build/$mode.log"; then cat "$build/$mode.log"; exit 1; fi
 fi
 echo "$mode: expected result observed"
done
printf 'Logs: %s\n' "$build"
