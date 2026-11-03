#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
: "${BUILD_DIR:?Set BUILD_DIR to a new empty scratch directory}"
if [[ -d "$BUILD_DIR" && -n "$(ls -A "$BUILD_DIR")" ]];then echo 'BUILD_DIR must be empty' >&2;exit 2;fi
mkdir -p "$BUILD_DIR";build=$(cd "$BUILD_DIR" && pwd);cd "$here"
sha256sum -c sources.sha256 > "$build/source-check.log"
python3 - "$here/sdram_jpeg_reader.sv" "$build" <<'PY'
from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text();out=Path(sys.argv[2])
for n,a,b in [('tail',"word_bytes==3?4'b0111","word_bytes==3?4'b1111"),
              ('address','BASE_WORDS+block_number*8','BASE_WORDS+block_number*4'),
              ('revoke','if(active&&!owned)',"if(1'b0 && active&&!owned)")]:
 assert s.count(a)==1,n
 (out/(n+'.sv')).write_text(s.replace(a,b))
PY
verilator --version > "$build/tool-versions.txt";ulimit -c 0
for n in normal tail address revoke;do
 src="$here/sdram_jpeg_reader.sv";[[ "$n" == normal ]]||src="$build/$n.sv"
 verilator --binary --timing --assert -Wno-fatal --top-module tb_sdram_jpeg_reader --Mdir "$build/$n-build" \
  tb_sdram_jpeg_reader.sv "$src" > "$build/$n-build.log" 2>&1
 code=0;timeout 120s "$build/$n-build/Vtb_sdram_jpeg_reader" > "$build/$n-sim.log" 2>&1||code=$?
 if [[ "$n" == normal ]];then
  [[ $code == 0 ]];grep -q '^SDRAM_READER_PASS lengths=14 max_bytes=262144 tail_strobes=1,2,3,4 revoke_drain=1 unsolicited_fault=1$' "$build/$n-sim.log"
 else
  [[ $code != 0 && $code != 124 ]]
  case "$n" in tail) needle='word/strobe mismatch';; address) needle='request address/order';; revoke) needle='revocation not reported';;esac
  grep -q "$needle" "$build/$n-sim.log";! grep -q '^SDRAM_READER_PASS' "$build/$n-sim.log"
 fi
done
if command -v yosys >/dev/null;then
 yosys -V >> "$build/tool-versions.txt"
 timeout 120s yosys -T -l "$build/yosys.log" -p 'read_verilog -sv sdram_jpeg_reader.sv; hierarchy -check -top sdram_jpeg_reader; proc; opt; check; stat' > "$build/yosys-stdout.log" 2>&1
 grep -q 'Found and reported 0 problems' "$build/yosys.log"
fi
echo 'SDRAM_JPEG_READER_UNIT_PASS and three expected failures; no physical/CDC guarantee'
