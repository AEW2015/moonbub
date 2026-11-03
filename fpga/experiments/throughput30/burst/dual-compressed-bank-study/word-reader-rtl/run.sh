#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
storage=$(cd -- "$here/../bank-storage-rtl" && pwd)
: "${BUILD_DIR:?Set BUILD_DIR to a new empty directory}"
if [[ -d "$BUILD_DIR" && -n "$(ls -A "$BUILD_DIR")" ]];then echo 'BUILD_DIR must be empty' >&2;exit 2;fi
mkdir -p "$BUILD_DIR/normal";build=$(cd -- "$BUILD_DIR" && pwd)
python3 - <<'PY'
import zlib
expected={1:0x83dcefb7,2:0xaf86add3,3:0x7b11c773,5:0xee85c166,6:0x1a3b3bcc,7:0xbc73d251,49149:0xa12b3b5d,49150:0xd378b5b0,49151:0xbbd755c6,49152:0x7b05968b}
for n,v in expected.items():assert zlib.crc32(bytes((i*7+0x31)&255 for i in range(n)))==v
assert zlib.crc32(bytes(((i*7+0x31)&255)^0x80 for i in range(5)))==0x8534c724
print('REFERENCE_CRC_PASS',len(expected)+1,'vectors')
PY
verilator --binary --timing --assert -Wno-fatal --top-module tb_word_reader --Mdir "$build/normal" "$here/tb_word_reader.sv" "$here/word_reader.sv" "$storage/two_bank_storage.sv" "$storage/two_bank_control_storage.sv" > "$build/normal-build.log" 2>&1
ulimit -c 0
timeout 90s "$build/normal/Vtb_word_reader" > "$build/normal.log" 2>&1
grep -Eq '^TEST_PASS_WORD_READER frames=12 bytes=196634 words=49164 stalls=[1-9][0-9]* cap=49152' "$build/normal.log"
if [[ -n "${YOSYS:-}" ]];then
 (cd "$build";timeout 90s "$YOSYS" -p "read_verilog -sv \"$here/word_reader.sv\"; hierarchy -check -top word_reader; proc; opt; check; stat") > "$build/yosys.log" 2>&1
 grep -q 'Found and reported 0 problems' "$build/yosys.log";grep -q 'End of script' "$build/yosys.log"
fi
python3 - "$here/word_reader.sv" "$build" <<'PY'
from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text();out=Path(sys.argv[2])
changes=[('endian','<< (lane*8)','<< ((3-lane)*8)',2),('strobe',"2'd2:strobe=4'b0111","2'd2:strobe=4'b1111",1),('owner','if(active && !owned)',"if(1'b0)",1)]
for name,old,new,n in changes:
 if s.count(old)!=n:raise SystemExit('mutation anchor mismatch '+name)
 (out/f'{name}-word_reader.sv').write_text(s.replace(old,new))
PY
for mode in endian strobe owner;do
 mkdir -p "$build/$mode"
 verilator --binary --timing --assert -Wno-fatal --top-module tb_word_reader --Mdir "$build/$mode" "$here/tb_word_reader.sv" "$build/$mode-word_reader.sv" "$storage/two_bank_storage.sv" "$storage/two_bank_control_storage.sv" > "$build/$mode-build.log" 2>&1
 status=0;timeout 90s "$build/$mode/Vtb_word_reader" > "$build/$mode.log" 2>&1 || status=$?
 if [[ "$status" == 0 || "$status" == 124 ]];then echo "unexpected $mode mutant status $status" >&2;exit 1;fi
 case "$mode" in endian|strobe) grep -q 'word mismatch' "$build/$mode.log";; owner) grep -q 'released bank word not cancelled' "$build/$mode.log";; esac
 if grep -q '^TEST_PASS_WORD_READER' "$build/$mode.log";then echo 'mutant unexpectedly passed' >&2;exit 1;fi
done
printf 'WORD_READER_PASS normal plus endian/strobe/ownership negative controls; output %s\n' "$build"
