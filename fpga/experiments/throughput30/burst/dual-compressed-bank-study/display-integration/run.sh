#!/usr/bin/env bash
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
study=$(cd "$here/.." && pwd)
burst=$(cd "$study/.." && pwd)
fpga=$(cd "$burst/../../.." && pwd)
root=$(cd "$fpga/.." && pwd)
: "${BUILD_DIR:?set BUILD_DIR to an empty scratch directory}"
: "${JPEG0:?set JPEG0 path}"
: "${JPEG1:?set JPEG1 path}"
if [[ -d "$BUILD_DIR" && -n "$(ls -A "$BUILD_DIR")" ]]; then echo 'BUILD_DIR must be empty' >&2; exit 2; fi
mkdir -p "$BUILD_DIR/obj"; BUILD_DIR=$(cd "$BUILD_DIR" && pwd)
JPEG0=$(realpath "$JPEG0"); JPEG1=$(realpath "$JPEG1")
files=();for f in "$fpga"/vendor/core_jpeg/src_v/*.v; do [[ "$f" == */jpeg_input.v ]] || files+=("$f");done
verilator --binary --timing --assert -Wno-fatal -DSIMULATION --top-module tb_bank_display --Mdir "$BUILD_DIR/obj" "$here/tb_bank_jpeg.sv" "$study/word-reader-rtl/word_reader.sv" "$study/bank-storage-rtl/two_bank_storage.sv" "$study/bank-storage-rtl/two_bank_control_storage.sv" "$burst/marker-followup/jpeg_input_followup.v" "$burst/../moonbub_tile_transpose.sv" "$burst/moonshine_memory_burst.sv" "$burst/moonshine_sdram_burst.sv" "$burst/sdram_model_burst_verilator.sv" "$fpga/rtl/moonshine_lcd.sv" "${files[@]}" > "$BUILD_DIR/build.log" 2>&1
${CXX:-g++} -std=c++17 -O2 -I"$fpga/vendor/core_jpeg/c_model" "$root/host/evidence/jpeg-c-model-fixed-color-main.cpp" -o "$BUILD_DIR/cmodel"
ulimit -c 0
timeout 180s "$BUILD_DIR/obj/Vtb_bank_display" "+JPEG0=$JPEG0" "+JPEG1=$JPEG1" "+DUMP0=$BUILD_DIR/out0.txt" "+DUMP1=$BUILD_DIR/out1.txt" | tee "$BUILD_DIR/run.log"
grep -q '^TEST_PASS_BANK_DISPLAY$' "$BUILD_DIR/run.log"
for n in 0 1; do jpeg=$JPEG0; [[ $n == 1 ]] && jpeg=$JPEG1
 "$BUILD_DIR/cmodel" "$jpeg" "$BUILD_DIR/model$n.ppm" > "$BUILD_DIR/cmodel$n.log"
 python3 "$here/compare.py" "$BUILD_DIR/model$n.ppm" "$BUILD_DIR/out$n.txt" > "$BUILD_DIR/comparison$n.json"
 python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); assert d["pixels"] == d["exact_rgb565_pixels"] == 345600' "$BUILD_DIR/comparison$n.json"
done
sha256sum "$JPEG0" "$JPEG1" "$here/tb_bank_jpeg.sv" "$study/word-reader-rtl/word_reader.sv" "$study/bank-storage-rtl/two_bank_storage.sv" "$study/bank-storage-rtl/two_bank_control_storage.sv" "$burst/marker-followup/jpeg_input_followup.v" "$burst/../moonbub_tile_transpose.sv" "$burst/moonshine_memory_burst.sv" "$burst/moonshine_sdram_burst.sv" "$burst/sdram_model_burst_verilator.sv" "$fpga/rtl/moonshine_lcd.sv" "${files[@]}" > "$BUILD_DIR/sha256.txt"
echo BANK_DISPLAY_CMODEL_PASS
