#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
fpga=$(cd -- "$here/../.." && pwd)
burst="$fpga/experiments/throughput30/burst"
: "${BUILD_DIR:?Set new empty build directory}"
mkdir -p "$BUILD_DIR"
if [[ -n "$(ls -A "$BUILD_DIR")" ]]; then echo 'BUILD_DIR must be empty' >&2; exit 2; fi
files=();for f in "$fpga"/vendor/core_jpeg/src_v/*.v;do [[ "$f" == */jpeg_input.v ]] || files+=("$f");done
verilator --binary -j 2 --timing --assert -Wno-fatal -DSIMULATION --top-module tb_sync_adapter --Mdir "$BUILD_DIR/obj" \
 "$here/tb_sync_adapter.sv" "$burst/cdc-credit/moonshine_qspi_endpoint_credit.sv" "$burst/cdc-credit/moonshine_bus_cdc_credit.sv" \
 "$burst/moonshine_memory_burst.sv" "$burst/moonshine_sdram_burst.sv" "$burst/sdram_model_burst_verilator.sv" \
 "$burst/marker-followup/jpeg_input_followup.v" "$burst/../moonbub_tile_transpose.sv" "$fpga/rtl/moonshine_core.sv" \
 "$fpga/rtl/moonshine_lcd.sv" "${files[@]}" "$here/replay_dpi.cpp"
