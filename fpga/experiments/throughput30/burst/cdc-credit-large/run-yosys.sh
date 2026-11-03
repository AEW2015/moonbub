#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
build=${BUILD_DIR:-$(mktemp -d)}
mkdir -p "$build"; build=$(cd -- "$build" && pwd)
yosys=${YOSYS:-yosys}
"$yosys" -V
(cd "$here/../cdc-credit" && "$yosys" -p 'read_verilog -sv moonshine_bus_cdc_credit.sv; synth_xilinx -family xc7 -top moonshine_bus_cdc_credit; stat' > "$build/small.log")
(cd "$here" && "$yosys" -p 'read_verilog -sv moonshine_bus_cdc_credit_large.sv; synth_xilinx -family xc7 -top moonshine_bus_cdc_credit_large; stat' > "$build/large.log")
printf 'Yosys logs: %s\n' "$build"
