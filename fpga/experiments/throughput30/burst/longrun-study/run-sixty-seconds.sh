#!/usr/bin/env bash
set -euo pipefail
# 1800 full-resolution RTL frames: several hours; no hardware involved.
# Requires Verilator 5.x, make, C++, GNU timeout, Python 3 and Pillow.
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
burst=$(cd -- "$here/.." && pwd)
fpga=$(cd -- "$here/../../../.." && pwd)
root=$(cd -- "$fpga/.." && pwd)
build=${BUILD_DIR:-$(mktemp -d)}
mkdir -p "$build"; build=$(cd -- "$build" && pwd)
if [[ -e "$build/fixtures" || -e "$build/checked" ]]; then echo 'fixture/check directories already exist' >&2; exit 2; fi
frames=${FRAMES:-1800}; wall=${TIMEOUT_SECONDS:-18000}; strict=${STRICT_WINDOW:-1}
if [[ ! "$frames" =~ ^[0-9]+$ ]] || (( frames < 1 || frames > 1800 )); then echo 'FRAMES must be 1..1800' >&2; exit 2; fi
if [[ ! "$wall" =~ ^[0-9]+$ ]] || (( wall < 1 )); then echo 'invalid wall timeout' >&2; exit 2; fi
if [[ "$strict" != 0 && "$strict" != 1 ]]; then echo 'STRICT_WINDOW must be 0 or 1' >&2; exit 2; fi
printf 'Run artifacts: %s\n' "$build"
verilator --version | tee "$build/tool-version.txt"
"${PYTHON:-python3}" --version | tee -a "$build/tool-version.txt"
sha256sum "$here/tb_jpeg720_sixty_seconds.sv" "$burst/marker-audit/jpeg_input_candidate.v" \
 "$burst/moonshine_memory_burst.sv" "$burst/moonshine_sdram_burst.sv" "$burst/sdram_model_burst_verilator.sv" \
 "$burst/../moonbub_tile_transpose.sv" "$fpga/rtl/moonshine_core.sv" "$fpga/rtl/moonshine_lcd.sv" \
 "$here/generate-jpegs.py" "$here/stream-check.py" "$burst/compare-frame.py" > "$build/source-sha256.txt"
"${PYTHON:-python3}" "$here/generate-jpegs.py" "$build/fixtures" --frames "$frames" | tee "$build/generation.log"
files=()
for f in "$fpga"/vendor/core_jpeg/src_v/*.v; do [[ "$f" == */jpeg_input.v ]] || files+=("$f"); done
sha256sum "${files[@]}" "$root/host/evidence/jpeg-c-model-fixed-color-source.cpp" "$root/host/evidence/jpeg-c-model-fixed-color-main.cpp" "$fpga"/vendor/core_jpeg/c_model/*.h >> "$build/source-sha256.txt"
"${PYTHON:-python3}" -c "import PIL; print("Pillow " + PIL.__version__)" | tee -a "$build/tool-version.txt"
verilator --binary --timing --assert -Wno-fatal -DSIMULATION --top-module tb_jpeg720_sixty_seconds --Mdir "$build/obj" \
 "$here/tb_jpeg720_sixty_seconds.sv" "$burst/marker-audit/jpeg_input_candidate.v" \
 "$burst/moonshine_memory_burst.sv" "$burst/moonshine_sdram_burst.sv" "$burst/sdram_model_burst_verilator.sv" \
 "$burst/../moonbub_tile_transpose.sv" "$fpga/rtl/moonshine_core.sv" "$fpga/rtl/moonshine_lcd.sv" "${files[@]}"
"${CXX:-g++}" -std=c++17 -O2 -I"$fpga/vendor/core_jpeg/c_model" \
 "$root/host/evidence/jpeg-c-model-fixed-color-main.cpp" -o "$build/jpeg-cmodel"
ulimit -c 0
"${PYTHON:-python3}" "$here/stream-check.py" --binary "$build/obj/Vtb_jpeg720_sixty_seconds" \
 --fixtures "$build/fixtures" --work "$build/checked" --cmodel "$build/jpeg-cmodel" \
 --compare "$burst/compare-frame.py" --frames "$frames" --timeout "$wall" --strict "$strict" | tee "$build/stream.log"
