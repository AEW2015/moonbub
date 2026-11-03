#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
: "${FPGA_DIR:?Set FPGA_DIR to the original FPGA tree}"
: "${FIXTURE_DIR:?Set FIXTURE_DIR to the gameplay fixture directory}"
: "${BUILD_DIR:?Set BUILD_DIR to a new directory}"
verilator=${VERILATOR:-verilator};python=${PYTHON:-python3};fpga=$(cd "$FPGA_DIR" && pwd);burst=$fpga/experiments/throughput30/burst;root=$(cd "$fpga/.." && pwd)
mkdir -p "$(dirname "$BUILD_DIR")";mkdir "$BUILD_DIR";build=$(cd "$BUILD_DIR" && pwd)
"$python" - "$FIXTURE_DIR" "$build" <<'PY'
from pathlib import Path
import hashlib,json,shutil,sys
src=Path(sys.argv[1]);dst=Path(sys.argv[2])/'fixtures';dst.mkdir()
m=json.loads((src/'manifest.json').read_text());m['frames']=m['frames'][:3]
expected=['6540d2531cf49453fc43b38a07c329c6ddec5fd4619dac3f26ed4c75fceaa149','1674cec81028d6730e6c61a6f23eded7e2f260d843c9cc46edf277b8afd9a641','680bbeea3c45a5308ee72f243d704047afad35eedd15e46f77ce326facf7a479']
if len(m['frames'])!=3:raise SystemExit('missing fixture manifest entries')
for i,(entry,want) in enumerate(zip(m['frames'],expected)):
 p=src/f'{i:04}.jpg'
 if entry['id']!=i or entry['jpeg_sha256']!=want or hashlib.sha256(p.read_bytes()).hexdigest()!=want:raise SystemExit(f'fixture mismatch {i}')
 shutil.copyfile(p,dst/p.name)
(dst/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
PY
files=();for f in "$fpga"/vendor/core_jpeg/src_v/*.v;do [[ $f == */jpeg_input.v ]] || files+=("$f");done
"$verilator" --version > "$build/version.txt"
sha256sum "$here/tb_qspi_x_accept_monitor.sv" "$fpga/rtl/moonshine_qspi_endpoint.sv" "$fpga/rtl/moonshine_bus_cdc.sv" "$burst/marker-followup/jpeg_input_followup.v" "$burst/moonshine_memory_burst.sv" "$burst/moonshine_sdram_burst.sv" "$burst/sdram_model_burst_verilator.sv" "$burst/../moonbub_tile_transpose.sv" "$fpga/rtl/moonshine_core.sv" "$fpga/rtl/moonshine_lcd.sv" "$root/host/evidence/jpeg-c-model-fixed-color-main.cpp" "${files[@]}" > "$build/source-sha256.txt"
"$verilator" --binary --timing --assert -Wno-fatal -DSIMULATION --top-module tb_qspi_x_accept_monitor --Mdir "$build/obj" \
 "$here/tb_qspi_x_accept_monitor.sv" "$fpga/rtl/moonshine_qspi_endpoint.sv" "$fpga/rtl/moonshine_bus_cdc.sv" \
 "$burst/marker-followup/jpeg_input_followup.v" "$burst/moonshine_memory_burst.sv" "$burst/moonshine_sdram_burst.sv" \
 "$burst/sdram_model_burst_verilator.sv" "$burst/../moonbub_tile_transpose.sv" "$fpga/rtl/moonshine_core.sv" \
 "$fpga/rtl/moonshine_lcd.sv" "${files[@]}" > "$build/build.log" 2>&1
"${CXX:-g++}" -std=c++17 -O2 -I"$fpga/vendor/core_jpeg/c_model" "$root/host/evidence/jpeg-c-model-fixed-color-main.cpp" -o "$build/jpeg-cmodel"
ulimit -c 0
"$python" "$burst/gameplay-study/check-gameplay.py" --binary "$build/obj/Vtb_qspi_x_accept_monitor" --fixtures "$build/fixtures" \
 --work "$build/checked" --cmodel "$build/jpeg-cmodel" --compare "$burst/compare-frame.py" --frames 3 --timeout 900 --strict 0 > "$build/check.log"
grep -q '^STREAM_CHECK_PASS ' "$build/check.log"
grep -q 'X_ACCEPT_MONITOR accepted=1555926 rejected=0 excluded_reset_start_cycles=6001353' "$build/checked/simulation.log"
echo X_ACCEPT_GAME_MONITOR_PASS
