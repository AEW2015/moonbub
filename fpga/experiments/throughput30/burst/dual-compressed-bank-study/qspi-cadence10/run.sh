#!/usr/bin/env bash
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
study=$(cd "$here/.." && pwd)
burst=$(cd "$study/.." && pwd)
fpga=$(cd "$burst/../../.." && pwd)
root=$(cd "$fpga/.." && pwd)
: "${BUILD_DIR:?set BUILD_DIR to an empty scratch directory}"
: "${FIXTURE_DIR:?set FIXTURE_DIR path}"
if [[ -d "$BUILD_DIR" && -n "$(ls -A "$BUILD_DIR")" ]]; then echo 'BUILD_DIR must be empty' >&2; exit 2; fi
mkdir -p "$BUILD_DIR/obj" "$BUILD_DIR/dumps"; BUILD_DIR=$(cd "$BUILD_DIR" && pwd); FIXTURE_DIR=$(cd "$FIXTURE_DIR" && pwd)
(cd "$root" && sha256sum -c "$here/sources.sha256") > "$BUILD_DIR/source-check.log"
(cd "$FIXTURE_DIR" && sha256sum -c "$here/fixtures.sha256") > "$BUILD_DIR/fixture-check.log"
files=();for f in "$fpga"/vendor/core_jpeg/src_v/*.v; do [[ "$f" == */jpeg_input.v ]] || files+=("$f");done
verilator --binary --timing --assert -Wno-fatal -DSIMULATION --top-module tb_bank_qspi_cadence10 --Mdir "$BUILD_DIR/obj" "$here/tb_bank_jpeg.sv" "$burst/cdc-credit/moonshine_qspi_endpoint_credit.sv" "$burst/cdc-credit/moonshine_bus_cdc_credit.sv" "$study/word-reader-rtl/word_reader.sv" "$study/bank-storage-rtl/two_bank_storage.sv" "$study/bank-storage-rtl/two_bank_control_storage.sv" "$burst/marker-followup/jpeg_input_followup.v" "$burst/../moonbub_tile_transpose.sv" "$burst/moonshine_memory_burst.sv" "$burst/moonshine_sdram_burst.sv" "$burst/sdram_model_burst_verilator.sv" "$fpga/rtl/moonshine_lcd.sv" "${files[@]}" > "$BUILD_DIR/build.log" 2>&1
${CXX:-g++} -std=c++17 -O2 -I"$fpga/vendor/core_jpeg/c_model" "$root/host/evidence/jpeg-c-model-fixed-color-main.cpp" -o "$BUILD_DIR/cmodel"
ulimit -c 0
timeout 600s "$BUILD_DIR/obj/Vtb_bank_qspi_cadence10" "+FIXTURE_DIR=$FIXTURE_DIR" "+DUMP_DIR=$BUILD_DIR/dumps" | tee "$BUILD_DIR/run.log"
grep -q '^TEST_PASS_BANK_QSPI_CADENCE10$' "$BUILD_DIR/run.log"
for dump in "$BUILD_DIR"/dumps/*.txt; do
 id=$(basename "$dump" .txt)
 "$BUILD_DIR/cmodel" "$FIXTURE_DIR/$id.jpg" "$BUILD_DIR/model$id.ppm" > "$BUILD_DIR/cmodel$id.log"
 python3 "$here/compare.py" "$BUILD_DIR/model$id.ppm" "$dump" > "$BUILD_DIR/comparison$id.json"
done
python3 "$here/check.py" "$BUILD_DIR/run.log" "$BUILD_DIR/dumps"
echo BANK_QSPI_CADENCE10_CMODEL_PASS
