#!/usr/bin/env bash
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd);study=$(cd "$here/.." && pwd);burst=$(cd "$study/.." && pwd);fpga=$(cd "$burst/../../.." && pwd)
: "${BUILD_DIR:?set BUILD_DIR to empty scratch directory}"
if [[ -d "$BUILD_DIR" && -n "$(ls -A "$BUILD_DIR")" ]];then echo 'BUILD_DIR not empty' >&2;exit 2;fi
mkdir -p "$BUILD_DIR/obj"
(cd "$fpga/.." && sha256sum -c "$here/sources.sha256") > "$BUILD_DIR/source-check.log"
files=();for f in "$fpga"/vendor/core_jpeg/src_v/*.v;do [[ "$f" == */jpeg_input.v ]] || files+=("$f");done
verilator --binary --timing --assert -Wno-fatal -DSIMULATION --top-module tb_live_multiframe --Mdir "$BUILD_DIR/obj" "$here/tb_bank_jpeg.sv" "$burst/cdc-credit/moonshine_qspi_endpoint_credit.sv" "$burst/cdc-credit/moonshine_bus_cdc_credit.sv" "$study/word-reader-rtl/word_reader.sv" "$study/bank-storage-rtl/two_bank_storage.sv" "$study/bank-storage-rtl/two_bank_control_storage.sv" "$burst/marker-followup/jpeg_input_followup.v" "$burst/../moonbub_tile_transpose.sv" "$burst/moonshine_memory_burst.sv" "$burst/moonshine_sdram_burst.sv" "$burst/sdram_model_burst_verilator.sv" "$fpga/rtl/moonshine_lcd.sv" "${files[@]}" "$burst/live-multiframe-bridge/socket_dpi.cpp" > "$BUILD_DIR/build.log" 2>&1
