#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
: "${BUILD_DIR:?Set BUILD_DIR to a new empty scratch directory}"
if [[ -d "$BUILD_DIR" && -n "$(ls -A "$BUILD_DIR")" ]];then echo 'BUILD_DIR must be empty' >&2;exit 2;fi
mkdir -p "$BUILD_DIR";build=$(cd "$BUILD_DIR" && pwd);cd "$here"
sha256sum -c sources.sha256 > "$build/source-check.log"
verilator --version > "$build/tool-versions.txt"
ulimit -c 0
for name in normal deadline corrupt unaligned;do
 opts=()
 case "$name" in
  deadline) opts=(-GLINE_PERIOD=850);;
  corrupt) opts=(-GCORRUPT_PAYLOAD=1);;
  unaligned) opts=(-GMISALIGN_REQUEST=1);;
 esac
 verilator --binary --timing --assert -Wno-fatal -DSIMULATION "${opts[@]}" --top-module tb_staging_arbiter --Mdir "$build/$name-build" \
  tb_staging_arbiter.sv staging_arbiter.sv ../../moonshine_sdram_burst.sv ../../sdram_model_burst_verilator.sv > "$build/$name-build.log" 2>&1
 code=0;timeout 120s "$build/$name-build/Vtb_staging_arbiter" > "$build/$name-sim.log" 2>&1 || code=$?
 if [[ "$name" == normal ]];then
  [[ $code == 0 ]];grep -Eq '^STAGING_ARBITER_PASS lines=24 display_words=11520 max_line_cycles=[0-9]+ period_cycles=1843 pixel=200 jwrite=200 jread=200 refreshes=[0-9]+ contention_cycles=[1-9][0-9]*$' "$build/$name-sim.log"
 else
  [[ $code != 0 && $code != 124 ]]
  case "$name" in deadline) needle='display line deadline';; corrupt) needle='compressed write mismatch';; unaligned) needle='arbiter protocol fault';;esac
  grep -q "$needle" "$build/$name-sim.log"
  ! grep -q '^STAGING_ARBITER_PASS' "$build/$name-sim.log"
 fi
done
if command -v yosys >/dev/null;then
 yosys -V >> "$build/tool-versions.txt"
 timeout 90s yosys -T -l "$build/yosys.log" -p 'read_verilog -sv staging_arbiter.sv; hierarchy -check -top staging_arbiter; proc; opt; check; stat' > "$build/yosys-stdout.log" 2>&1
 grep -q 'Found and reported 0 problems' "$build/yosys.log"
fi
echo 'STAGING_ARBITER_STUDY_PASS normal and three expected failures; bounded synthetic controller simulation only'
