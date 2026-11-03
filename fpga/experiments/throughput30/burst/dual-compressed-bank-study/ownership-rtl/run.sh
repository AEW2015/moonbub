#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
: "${BUILD_DIR:?Set BUILD_DIR to a new empty directory}"
if [[ -d "$BUILD_DIR" && -n "$(ls -A "$BUILD_DIR")" ]];then echo 'BUILD_DIR must be empty' >&2;exit 2;fi
mkdir -p "$BUILD_DIR/normal" "$BUILD_DIR/mutant";build=$(cd -- "$BUILD_DIR" && pwd)
verilator --binary --timing --assert -Wno-fatal --top-module tb_two_bank --Mdir "$build/normal" "$here/tb_two_bank.sv" "$here/two_bank_control.sv" > "$build/normal-build.log" 2>&1
ulimit -c 0
timeout 60s "$build/normal/Vtb_two_bank" > "$build/normal.log" 2>&1
grep -q '^TEST_PASS_TWO_BANK accepted=7 dropped=8 writes=49185 final_front=60' "$build/normal.log"
if [[ -n "${YOSYS:-}" ]];then
 timeout 60s "$YOSYS" -p "read_verilog -sv \"$here/two_bank_control.sv\"; hierarchy -check -top two_bank_control; proc; opt; check; stat" > "$build/yosys.log" 2>&1
 grep -q 'Found and reported 0 problems' "$build/yosys.log"
 grep -q 'End of script' "$build/yosys.log"
fi
python3 - "$here/two_bank_control.sv" "$build" <<'PY2'
from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text();out=Path(sys.argv[2])
for name,old,new in [('crc', 'else if((~recv_crc)!=frame_crc[recv_bank])',"else if(1'b0)"),('vblank','if(vblank && pending)begin','if(vblank && pending && !abort_valid)begin')]:
 if s.count(old)!=1:raise SystemExit('mutation anchor mismatch '+name)
 (out/f'{name}-control.sv').write_text(s.replace(old,new))
PY2
for mode in crc vblank;do
 mkdir -p "$build/$mode"
 verilator --binary --timing --assert -Wno-fatal --top-module tb_two_bank --Mdir "$build/$mode" "$here/tb_two_bank.sv" "$build/$mode-control.sv" > "$build/$mode-build.log" 2>&1
 status=0
 timeout 60s "$build/$mode/Vtb_two_bank" > "$build/$mode.log" 2>&1 || status=$?
 if [[ "$status" == 0 || "$status" == 124 ]];then echo "unexpected $mode mutant status $status" >&2;exit 1;fi
 case "$mode" in crc) grep -q 'CRC/length rejection mismatch' "$build/$mode.log";; vblank) grep -q 'simultaneous abort/vblank lost pending frame' "$build/$mode.log";; esac
 if grep -q '^TEST_PASS_TWO_BANK' "$build/$mode.log";then echo "mutant $mode unexpectedly passed" >&2;exit 1;fi
done
printf 'TWO_BANK_CONTROL_PASS normal plus CRC and vblank mutation controls; output %s\n' "$build"
