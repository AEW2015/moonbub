#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
: "${BUILD_DIR:?Set BUILD_DIR to a new empty directory}"
if [[ -d "$BUILD_DIR" && -n "$(ls -A "$BUILD_DIR")" ]];then echo 'BUILD_DIR must be empty' >&2;exit 2;fi
mkdir -p "$BUILD_DIR/normal";build=$(cd -- "$BUILD_DIR" && pwd)
python3 - "$here/../ownership-rtl/two_bank_control.sv" "$here/two_bank_control_storage.sv" <<'PY'
from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text()
changes=[('module two_bank_control #(', 'module two_bank_control_storage #('),('output reg decode_grant,output reg decode_bank,output reg [31:0] decode_id,','output reg decode_grant,output reg decode_bank,output reg [31:0] decode_id,output reg [15:0] decode_length,'),('decode_grant<=0;decode_bank<=0;decode_id<=0;present<=0;', 'decode_grant<=0;decode_bank<=0;decode_id<=0;decode_length<=0;present<=0;'),('decode_bank<=ready_bank;decode_id<=frame_id[ready_bank];','decode_bank<=ready_bank;decode_id<=frame_id[ready_bank];decode_length<=frame_length[ready_bank];')]
for a,b in changes:
 if s.count(a)!=1:raise SystemExit('control copy anchor mismatch')
 s=s.replace(a,b)
if s!=Path(sys.argv[2]).read_text():raise SystemExit('control copy contains unexplained changes')
print('CONTROL_COPY_PASS')
PY
python3 - <<'PY'
import zlib
assert zlib.crc32(bytes(i & 255 for i in range(1024)))==0xb70b4c26
assert zlib.crc32(bytes((3*i+7) & 255 for i in range(1536)))==0x93737851
assert zlib.crc32(bytes(49152))==0x16d13407
print('REFERENCE_CRC_PASS')
PY
verilator --binary --timing --assert -Wno-fatal --top-module tb_two_bank_storage --Mdir "$build/normal" "$here/tb_two_bank_storage.sv" "$here/two_bank_storage.sv" "$here/two_bank_control_storage.sv" > "$build/normal-build.log" 2>&1
ulimit -c 0
timeout 90s "$build/normal/Vtb_two_bank_storage" > "$build/normal.log" 2>&1
grep -q '^TEST_PASS_BANK_STORAGE reads=51715 overlap=1024 cap=49152 final_front=60' "$build/normal.log"
if [[ -n "${YOSYS:-}" ]];then
 (cd "$build"; timeout 90s "$YOSYS" -p "read_verilog -sv \"$here/two_bank_control_storage.sv\" \"$here/two_bank_storage.sv\"; hierarchy -check -top two_bank_storage; proc; opt; memory_collect; check; stat; write_json generic.json") > "$build/yosys.log" 2>&1
 grep -q 'Found and reported 0 problems' "$build/yosys.log";grep -q 'End of script' "$build/yosys.log"
 python3 - "$build/generic.json" <<'PY'
import json,sys
j=json.load(open(sys.argv[1]));c=j['modules']['two_bank_storage']['cells']
for name in ('compressed0','compressed1'):
 m=c[name];assert m['type']=='$mem_v2' and int(m['parameters']['SIZE'],2)==49152 and int(m['parameters']['WIDTH'],2)==8
print('GENERIC_MEMORY_SHAPE_PASS two 49152x8 abstract memory cells')
PY
fi
python3 - "$here/two_bank_storage.sv" "$build" <<'PY'
from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text();out=Path(sys.argv[2])
changes=[('bounds','read_addr<owner_length',"1'b1"),('bank','if(owner_bank)read_data<=compressed1[read_addr]','if(owner_bank)read_data<=compressed0[read_addr]')]
for name,old,new in changes:
 if s.count(old)!=1:raise SystemExit('mutation anchor mismatch '+name)
 (out/f'{name}-storage.sv').write_text(s.replace(old,new))
PY
for mode in bounds bank;do
 mkdir -p "$build/$mode"
 verilator --binary --timing --assert -Wno-fatal --top-module tb_two_bank_storage --Mdir "$build/$mode" "$here/tb_two_bank_storage.sv" "$build/$mode-storage.sv" "$here/two_bank_control_storage.sv" > "$build/$mode-build.log" 2>&1
 status=0;timeout 90s "$build/$mode/Vtb_two_bank_storage" > "$build/$mode.log" 2>&1 || status=$?
 if [[ "$status" == 0 || "$status" == 124 ]];then echo "unexpected $mode mutant status $status" >&2;exit 1;fi
 case "$mode" in bounds) grep -q 'read bound rejection' "$build/$mode.log";; bank) grep -q 'read data mismatch' "$build/$mode.log";; esac
 if grep -q '^TEST_PASS_BANK_STORAGE' "$build/$mode.log";then echo 'mutant unexpectedly passed' >&2;exit 1;fi
done
printf 'BANK_STORAGE_PASS normal plus bounds and wrong-bank negative controls; output %s\n' "$build"
