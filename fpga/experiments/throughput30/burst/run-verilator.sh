#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
build=${BUILD_DIR:-$(mktemp -d)}
mkdir -p "$build"
verilator --version
verilator --binary --timing --assert -Wno-fatal -DSIMULATION --top-module tb_sdram_burst --Mdir "$build" "$here/tb_sdram_burst.sv" "$here/moonshine_sdram_burst.sv" "$here/sdram_model_burst.sv"
timeout 30s "$build/Vtb_sdram_burst"
