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
# Higher than the currently documented 40 MHz is simulation stress only.
for half_ps in 12500 10000 8333 6250; do
 for phase in 0 1250 2500 3750; do
  timeout 180s "$build/obj/Vtb_qspi_frame" "+PHASE_PS=$phase" "+WRITE_HALF_PS=$half_ps" | tee "$build/phase-$half_ps-$phase.log"
  grep -q '^QSPI_FRAME_PASS ' "$build/phase-$half_ps-$phase.log"
 done
done
