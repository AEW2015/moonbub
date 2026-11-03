#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
fpga=$(cd -- "$here/../../../.." && pwd)
root=$(cd -- "$fpga/.." && pwd)
build=${BUILD_DIR:-$(mktemp -d)}
mkdir -p "$build"
build=$(cd -- "$build" && pwd)
"${PYTHON:-python3}" "$root/experiments/fixture30/generate.py" "$build/fixtures" --frames 7
verilator --version
ulimit -c 0
for mode in guarded candidate; do
 if [[ $mode == guarded ]]; then src="$here/../jpeg_input_guarded.v"; else src="$here/jpeg_input_candidate.v"; fi
 verilator --binary --timing --assert -Wno-fatal --top-module tb_stale_eoi --Mdir "$build/obj-$mode" "$here/tb_stale_eoi.sv" "$src"
 for blocked in 0 1; do
  set +e
  timeout 30s "$build/obj-$mode/Vtb_stale_eoi" "+BLOCK=$blocked" "+JPEG_FILE=$build/fixtures/0006.jpg" > "$build/$mode-$blocked.log" 2>&1
  status=$?
  set -e
  if [[ $mode == guarded ]]; then
   if [[ $status == 0 || $status == 124 ]] || ! grep -Eq 'stale EOI changed parser state|unaccepted EOI asserted image end' "$build/$mode-$blocked.log"; then cat "$build/$mode-$blocked.log"; exit 1; fi
  else
   if [[ $status != 0 ]] || ! grep -q 'TEST_PASS_STALE_EOI' "$build/$mode-$blocked.log"; then cat "$build/$mode-$blocked.log"; exit 1; fi
  fi
  printf '%s blocked=%s expected-result PASS\n' "$mode" "$blocked"
 done
done
printf 'Logs: %s\n' "$build"
