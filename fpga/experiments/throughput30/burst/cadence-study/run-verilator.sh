#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
burst=$(cd -- "$here/.." && pwd)
fpga=$(cd -- "$here/../../../.." && pwd)
root=$(cd -- "$fpga/.." && pwd)
build=${BUILD_DIR:-$(mktemp -d)}
mkdir -p "$build"
build=$(cd -- "$build" && pwd)
if [[ -e "$build/fixtures" ]]; then echo 'Use a new or empty BUILD_DIR' >&2; exit 2; fi
"${PYTHON:-python3}" "$root/experiments/fixture30/generate.py" "$build/fixtures" --frames 10
mkdir "$build/dump65" "$build/dump60"
files=(); for f in "$fpga"/vendor/core_jpeg/src_v/*.v; do
 [[ "$f" == */jpeg_input.v ]] || files+=("$f")
done
verilator --version
verilator --binary --timing --assert -Wno-fatal -DSIMULATION --top-module tb_cadence --Mdir "$build/obj" \
 "$here/tb_cadence.sv" "$burst/moonshine_memory_burst.sv" "$burst/moonshine_sdram_burst.sv" \
 "$burst/sdram_model_burst_verilator.sv" "$burst/jpeg_input_guarded.v" \
 "$burst/../moonbub_tile_transpose.sv" "$fpga/rtl/moonshine_core.sv" "$fpga/rtl/moonshine_lcd.sv" "${files[@]}"
ulimit -c 0
for hz in 65 60; do
 if [[ "$hz" == 65 ]]; then half=17.029; else half=18.470; fi
 timeout 300s "$build/obj/Vtb_cadence" "+FIXTURE_DIR=$build/fixtures" "+DUMP_DIR=$build/dump$hz" "+PCLK_HALF_NS=$half" | tee "$build/$hz.log"
 grep -q '^TEST_PASS_JPEG720_TEN_FRAMES ' "$build/$hz.log"
 "${PYTHON:-python3}" "$here/replay.py" "$build/$hz.log" --half-ns "$half" --frames 1800 > "$build/replay-$hz.json"
done
for ((frame=0; frame<10; frame++)); do
 printf -v stem '%04d' "$frame"
 cmp "$build/dump65/$stem-rgb565.txt" "$build/dump60/$stem-rgb565.txt"
done
printf 'Decoded pixel dumps match between clocks for all 10 frames; results in %s\n' "$build"
