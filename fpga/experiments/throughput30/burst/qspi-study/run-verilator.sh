#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
fpga=$(cd -- "$here/../../../.." && pwd)
build=${BUILD_DIR:-$(mktemp -d)}
mkdir -p "$build";build=$(cd -- "$build" && pwd)
verilator --version
verilator --binary --timing --assert -Wno-fatal --top-module tb_qspi_frame --Mdir "$build/obj" \
 "$here/tb_qspi_frame.sv" "$fpga/rtl/moonshine_qspi_endpoint.sv" "$fpga/rtl/moonshine_bus_cdc.sv"
ulimit -c 0
for phase in 0 1250 2500 3750; do
 timeout 180s "$build/obj/Vtb_qspi_frame" "+PHASE_PS=$phase" | tee "$build/phase-$phase.log"
 grep -q '^QSPI_FRAME_PASS ' "$build/phase-$phase.log"
done
