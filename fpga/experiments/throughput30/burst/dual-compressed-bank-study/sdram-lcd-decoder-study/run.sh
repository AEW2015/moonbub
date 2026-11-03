#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
base=$(cd "$here/../qspi-scanout-integration" && pwd)
: "${BUILD_DIR:?Set BUILD_DIR to a new empty scratch directory}"
: "${JPEG0:?Set JPEG0 to the pinned fixture}"
: "${JPEG1:?Set JPEG1 to the pinned fixture}"
if [[ -d "$BUILD_DIR" && -n "$(ls -A "$BUILD_DIR")" ]];then echo 'BUILD_DIR must be empty' >&2;exit 2;fi
mkdir -p "$BUILD_DIR";build=$(cd "$BUILD_DIR" && pwd);cd "$here"
sha256sum -c sources.sha256 > "$build/source-check.log"
python3 make_tb.py "$base/tb_bank_jpeg.sv" "$build/staging-tb.sv"
python3 - "$base/run.sh" "$build/wrapper.sh" <<'PY'
from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text()
for old,new in [
 ('here=$(cd "$(dirname "$0")" && pwd)', 'here=${BASE_DIR:?}'),
 ('"$here/tb_bank_jpeg.sv"','"${STUDY_TB:?}"'),
 ('"$burst/moonshine_memory_burst.sv"','"${STUDY_MEMORY:?}" "${STUDY_ARBITER:?}"'),
 ('timeout 180s ', 'timeout 600s '),
]:
 n=s.count(old)
 # Both file paths occur in the compiler and output-source hash commands.
 assert n==(2 if old in ('"$here/tb_bank_jpeg.sv"','"$burst/moonshine_memory_burst.sv"') else 1),(old,n)
 s=s.replace(old,new)
Path(sys.argv[2]).write_text(s)
PY
export BASE_DIR="$base" STUDY_TB="$build/staging-tb.sv" STUDY_MEMORY="$here/moonshine_memory_staging.sv"
export STUDY_ARBITER="$here/../sdram-arbiter-study/staging_arbiter.sv" BUILD_DIR="$build/run"
bash "$build/wrapper.sh" | tee "$build/wrapper.log"
grep -q '^STAGING_OVERLAP_PASS ' "$build/run/run.log"
grep -q '^BANK_QSPI_SCANOUT_CMODEL_PASS$' "$build/wrapper.log"
ulimit -c 0
code=0
timeout 600s "$build/run/obj/Vtb_bank_qspi_scanout" "+JPEG0=$JPEG0" "+JPEG1=$JPEG1" "+DUMP0=$build/mutant0.txt" "+DUMP1=$build/mutant1.txt" +STAGE_CORRUPT > "$build/mutant.log" 2>&1 || code=$?
[[ $code != 0 && $code != 124 ]]
grep -q 'staging memory mismatch' "$build/mutant.log"
! grep -q '^STAGING_OVERLAP_PASS' "$build/mutant.log"
echo 'SDRAM_LCD_DECODER_STAGING_PASS and corruption negative control (decoder still reads BRAM; synthetic staging clients)'
