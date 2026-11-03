#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
: "${BUILD_DIR:?Set BUILD_DIR to a new empty scratch directory}"
if [[ -d "$BUILD_DIR" && -n "$(ls -A "$BUILD_DIR")" ]];then echo 'BUILD_DIR must be empty' >&2;exit 2;fi
mkdir -p "$BUILD_DIR";build=$(cd "$BUILD_DIR" && pwd)
cd "$here"
sha256sum -c sources.sha256 > "$build/source-check.log"
python3 make_control.py ../ownership-rtl/two_bank_control.sv "$build/controller.sv"
python3 make_mutants.py tagged_gateway.sv "$build"
python3 make_fault_test.py "$build/controller.sv" tb_tagged_gateway.sv "$build/controller-fault.sv" "$build/tb-fault.sv"
python3 - "$here/tagged_gateway.sv" "$build/no-commit-guard.sv" <<'PY'
from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text();old='else if(c_commit_accept)'
assert s.count(old)==1
Path(sys.argv[2]).write_text(s.replace(old,"else if(1'b1)"))
PY
verilator --version > "$build/tool-versions.txt"
ulimit -c 0
for name in normal stale_generation no_replay;do
 source="$here/tagged_gateway.sv";[[ "$name" == normal ]] || source="$build/$name.sv"
 verilator --binary --timing --assert -Wno-fatal --top-module tb_tagged_gateway --Mdir "$build/$name-build" \
  tb_tagged_gateway.sv "$source" "$build/controller.sv" > "$build/$name-build.log" 2>&1
 code=0; timeout 90s "$build/$name-build/Vtb_tagged_gateway" > "$build/$name-sim.log" 2>&1 || code=$?
 if [[ "$name" == normal ]];then
  [[ $code == 0 ]];grep -Eq '^TEST_PASS_TAGGED_GATEWAY acks=38 writes=10 cycles=[0-9]+$' "$build/$name-sim.log"
 else
  [[ $code != 0 && $code != 124 ]]; grep -q 'bad ack' "$build/$name-sim.log"
  ! grep -q '^TEST_PASS_TAGGED_GATEWAY' "$build/$name-sim.log"
 fi
done
for name in fault_guarded fault_mutant;do
 source="$here/tagged_gateway.sv";[[ "$name" == fault_guarded ]] || source="$build/no-commit-guard.sv"
 verilator --binary --timing --assert -Wno-fatal --top-module tb_tagged_gateway --Mdir "$build/$name-build" \
  "$build/tb-fault.sv" "$source" "$build/controller-fault.sv" > "$build/$name-build.log" 2>&1
 code=0; timeout 90s "$build/$name-build/Vtb_tagged_gateway" > "$build/$name-sim.log" 2>&1 || code=$?
 if [[ "$name" == fault_guarded ]];then
  [[ $code == 0 ]];grep -q '^TEST_PASS_CONTROLLER_ACCEPT_FAULT no_false_success=1 fault_latched=1$' "$build/$name-sim.log"
 else
  [[ $code != 0 && $code != 124 ]];grep -q 'bad ack' "$build/$name-sim.log"
  ! grep -q '^TEST_PASS_CONTROLLER_ACCEPT_FAULT' "$build/$name-sim.log"
 fi
done
if command -v yosys >/dev/null;then
 yosys -V >> "$build/tool-versions.txt"
 timeout 120s yosys -T -l "$build/yosys.log" -p "read_verilog -sv tagged_gateway.sv $build/controller.sv; hierarchy -check -top tagged_gateway; proc; opt; check; stat" > "$build/yosys-stdout.log" 2>&1
 grep -q 'Found and reported 0 problems' "$build/yosys.log"
fi
echo 'TAGGED_GATEWAY_PASS normal, acceptance-fault guard plus three rejected mutants; single-clock control only'
