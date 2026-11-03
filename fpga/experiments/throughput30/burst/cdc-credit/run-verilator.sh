#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
build=${BUILD_DIR:-$(mktemp -d)}
mkdir -p "$build";build=$(cd -- "$build" && pwd)
verilator --version
verilator --binary --timing --assert -Wno-fatal --top-module tb_cdc_credit --Mdir "$build/core" "$here/tb_cdc_credit.sv" "$here/moonshine_bus_cdc_credit.sv"
ulimit -c 0
for half in 5000 10000 20000; do
 timeout 120s "$build/core/Vtb_cdc_credit" "+CORE_HALF_PS=$half" | tee "$build/core-$half.log"
 grep -q '^CDC_CREDIT_PASS ' "$build/core-$half.log"
done
verilator --binary --timing --assert -Wno-fatal --top-module tb_qspi_credit --Mdir "$build/qspi" "$here/tb_qspi_credit.sv" "$here/moonshine_bus_cdc_credit.sv" "$here/moonshine_qspi_endpoint_credit.sv"
for phase in 0 1250 2500 3750; do
 timeout 180s "$build/qspi/Vtb_qspi_credit" "+PHASE_PS=$phase" | tee "$build/qspi-$phase.log"
 grep -q '^QSPI_CREDIT_PASS ' "$build/qspi-$phase.log"
done
