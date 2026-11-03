#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
: "${BUILD_DIR:?Set BUILD_DIR to a new empty scratch directory}"
if [[ -d "$BUILD_DIR" && -n "$(ls -A "$BUILD_DIR")" ]];then echo 'BUILD_DIR must be empty' >&2;exit 2;fi
mkdir -p "$BUILD_DIR";build=$(cd "$BUILD_DIR" && pwd);cd "$here"
sha256sum -c sources.sha256 > "$build/source-check.log"
python3 make_mutants.py sdram_jpeg_writer.sv "$build"
python3 make_controller_tb.py tb_sdram_jpeg_writer.sv "$build/controller-tb.sv"
verilator --version > "$build/tool-versions.txt";ulimit -c 0
for n in normal padding drain hold address capacity controller;do
 src="$here/sdram_jpeg_writer.sv";tb="$here/tb_sdram_jpeg_writer.sv";opts=();extra=()
 case "$n" in
  normal) ;;
  controller) tb="$build/controller-tb.sv";opts=(-DSIMULATION);extra=(../../moonshine_sdram_burst.sv ../../sdram_model_burst_verilator.sv);;
  *) src="$build/$n.sv";;
 esac
 verilator --binary --timing --assert -Wno-fatal "${opts[@]}" --top-module tb_sdram_jpeg_writer --Mdir "$build/$n-build" \
  "$tb" "$src" "${extra[@]}" > "$build/$n-build.log" 2>&1
 code=0;timeout 180s "$build/$n-build/Vtb_sdram_jpeg_writer" > "$build/$n-sim.log" 2>&1||code=$?
 case "$n" in
  normal|controller)
   [[ $code == 0 ]]; marker=SDRAM_WRITER_PASS;[[ "$n" == normal ]]||marker=SDRAM_WRITER_CONTROLLER_PASS
   if [[ "$n" == normal ]];then
    grep -q "^$marker lengths=24 max_bytes=262144 tails=0..15 abort_drain=1 stalled_abort=1 stalled_fault=1 fault_drain=1$" "$build/$n-sim.log"
   else
    grep -Eq "^$marker lengths=24 max_bytes=262144 tails=0..15 abort_drain=1 stalled_abort=1 stalled_fault=1 fault_drain=1 refreshes=[1-9][0-9]* write_bursts=[1-9][0-9]*$" "$build/$n-sim.log"
   fi;;
  *)
   [[ $code != 0 && $code != 124 ]]
   case "$n" in padding) needle='payload/padding mismatch';; drain) needle='completion before drain';; hold) needle='write changed under backpressure';; address) needle='write address/order';; capacity) needle='begin result';;esac
   grep -q "$needle" "$build/$n-sim.log";! grep -q '^SDRAM_WRITER_PASS' "$build/$n-sim.log";;
 esac
done
if command -v yosys >/dev/null;then
 yosys -V >> "$build/tool-versions.txt"
 timeout 120s yosys -T -l "$build/yosys.log" -p 'read_verilog -sv sdram_jpeg_writer.sv; hierarchy -check -top sdram_jpeg_writer; proc; opt; check; stat' > "$build/yosys-stdout.log" 2>&1
 grep -q 'Found and reported 0 problems' "$build/yosys.log"
fi
echo 'SDRAM_JPEG_WRITER_STUDY_PASS two positive benches and five expected failures; physical drain/CRC/CDC unproven'
