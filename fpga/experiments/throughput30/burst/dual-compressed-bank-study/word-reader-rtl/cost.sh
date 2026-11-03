#!/usr/bin/env bash
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
storage="$here/../bank-storage-rtl"
: "${BUILD_DIR:?set BUILD_DIR to an empty scratch directory}"
mkdir -p "$BUILD_DIR/obj"
verilator --binary --timing --assert -Wno-fatal --top-module tb_word_cost --Mdir "$BUILD_DIR/obj" "$here/tb_word_cost.sv" "$here/word_reader.sv" "$storage/two_bank_storage.sv" "$storage/two_bank_control_storage.sv" > "$BUILD_DIR/build.log" 2>&1
timeout 90s "$BUILD_DIR/obj/Vtb_word_cost" | tee "$BUILD_DIR/run.log"
python3 "$here/verify_cost.py" "$BUILD_DIR/run.log"
