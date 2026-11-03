#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
: "${BUILD_DIR:?Set BUILD_DIR to a new empty scratch directory}"
if [[ -d "$BUILD_DIR" && -n "$(ls -A "$BUILD_DIR")" ]];then echo 'BUILD_DIR must be empty' >&2;exit 2;fi
mkdir -p "$BUILD_DIR";build=$(cd "$BUILD_DIR" && pwd)
cd "$here"
sha256sum -c sources.sha256 > "$build/source-check.log"
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v > "$build/python-tests.log" 2>&1
PYTHONDONTWRITEBYTECODE=1 python3 scenarios.py > "$build/scenarios.json"
verilator --version > "$build/tool-version.txt"
verilator --binary --timing --assert -Wno-fatal -DSIMULATION --top-module tb_sdram_rowhit \
 --Mdir "$build/obj" tb_sdram_rowhit.sv ../../../../../rtl/moonshine_sdram.sv ../../moonshine_sdram_burst.sv > "$build/build.log" 2>&1
ulimit -c 0
timeout 60s "$build/obj/Vtb_sdram_rowhit" > "$build/rowhit.log" 2>&1
grep -q '^SDRAM_TIMING_PASS hit_baseline=6,15 hit_burst=13,15 switch_baseline=14,23 switch_burst=21,23 write_samples=4 read_samples=5 activate=12 writes=12 reads=12$' "$build/rowhit.log"
echo 'SDRAM_MODEL_PASS arithmetic and isolated controller command spacing only'
