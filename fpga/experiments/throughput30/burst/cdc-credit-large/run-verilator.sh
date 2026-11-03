#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
build=${BUILD_DIR:-$(mktemp -d)}
mkdir -p "$build"; build=$(cd -- "$build" && pwd)
verilator --version
verilator --binary --timing --assert -Wno-fatal --top-module tb_cdc_credit_large --Mdir "$build/core" \
 "$here/tb_cdc_credit_large.sv" "$here/moonshine_bus_cdc_credit_large.sv"
ulimit -c 0
for half in 5000 10000 20000; do
 timeout 180s "$build/core/Vtb_cdc_credit_large" "+CORE_HALF_PS=$half" | tee "$build/core-$half.log"
 grep -q '^CDC_LARGE_CREDIT_PASS ' "$build/core-$half.log"
done
verilator --binary --timing --assert -Wno-fatal --top-module tb_qspi_credit_large --Mdir "$build/unfenced" \
 "$here/tb_qspi_credit_large.sv" "$here/moonshine_bus_cdc_credit_large.sv" "$here/moonshine_qspi_endpoint_credit_large.sv"
timeout 180s "$build/unfenced/Vtb_qspi_credit_large" +CORE_HALF_PS=5000 | tee "$build/unfenced-100.log"
grep -q '^QSPI_LARGE_CREDIT_PASS ' "$build/unfenced-100.log"
set +e
timeout 180s "$build/unfenced/Vtb_qspi_credit_large" +CORE_HALF_PS=20000 > "$build/unfenced-25.log" 2>&1
rc=$?
set -e
if [[ $rc -eq 0 || $rc -eq 124 ]] || ! grep -q 'remaining length mismatch' "$build/unfenced-25.log"; then
 echo "Expected stale mailbox failure missing (exit $rc); see $build/unfenced-25.log" >&2; exit 1
fi
printf 'EXPECTED_FAILURE unfenced mailbox at 25 MHz; see %s\n' "$build/unfenced-25.log"
verilator --binary --timing --assert -Wno-fatal --top-module tb_qspi_credit_large_fenced --Mdir "$build/fenced" \
 "$here/tb_qspi_credit_large_fenced.sv" "$here/moonshine_bus_cdc_credit_large.sv" "$here/moonshine_qspi_endpoint_credit_large.sv"
for half in 5000 20000; do
 for phase in 0 1250 2500 3750; do
  timeout 180s "$build/fenced/Vtb_qspi_credit_large_fenced" "+CORE_HALF_PS=$half" "+PHASE_PS=$phase" | tee "$build/fenced-$half-$phase.log"
  grep -q '^QSPI_LARGE_FENCE_PASS ' "$build/fenced-$half-$phase.log"
 done
done
