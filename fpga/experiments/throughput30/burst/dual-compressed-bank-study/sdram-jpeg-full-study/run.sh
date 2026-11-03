#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
reader=$(cd "$here/../sdram-jpeg-reader-study" && pwd)
staging=$(cd "$here/../sdram-lcd-decoder-study" && pwd)
writer=$(cd "$here/../sdram-jpeg-writer-study" && pwd)
base=$(cd "$here/../qspi-scanout-integration" && pwd)
: "${BUILD_DIR:?Set BUILD_DIR to a new empty scratch directory}"
: "${JPEG0:?Set JPEG0 to the pinned fixture}"
: "${JPEG1:?Set JPEG1 to the pinned fixture}"
if [[ -d "$BUILD_DIR" && -n "$(ls -A "$BUILD_DIR")" ]];then echo 'BUILD_DIR must be empty' >&2;exit 2;fi
mkdir -p "$BUILD_DIR";build=$(cd "$BUILD_DIR" && pwd);cd "$here"
sha256sum -c sources.sha256 > "$build/source-check.log"
(cd "$reader" && sha256sum -c sources.sha256) > "$build/reader-source-check.log"
(cd "$writer" && sha256sum -c sources.sha256) > "$build/writer-source-check.log"
(cd "$staging" && sha256sum -c sources.sha256) > "$build/staging-source-check.log"
python3 "$staging/make_tb.py" "$base/tb_bank_jpeg.sv" "$build/intermediate.sv"
python3 "$reader/make_decoder_tb.py" "$build/intermediate.sv" "$build/sdram-tb.sv"
python3 "$here/make_full_tb.py" "$build/sdram-tb.sv" "$build/full-tb.sv"
python3 - "$base/run.sh" "$build/wrapper.sh" <<'PY'
from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text()
for old,new,count in [
 ('here=$(cd "$(dirname "$0")" && pwd)', 'here=${BASE_DIR:?}',1),
 ('"$here/tb_bank_jpeg.sv"','"${STUDY_TB:?}"',2),
 ('"$burst/moonshine_memory_burst.sv"','"${STUDY_MEMORY:?}" "${STUDY_ARBITER:?}"',2),
 ('"$study/word-reader-rtl/word_reader.sv"','"$study/word-reader-rtl/word_reader.sv" "${SD_READER:?}" "${SD_WRITER:?}"',2),
 ('timeout 180s ', 'timeout 600s ',1),
]:
 assert s.count(old)==count,(old,s.count(old))
 s=s.replace(old,new)
Path(sys.argv[2]).write_text(s)
PY
export BASE_DIR="$base" STUDY_TB="$build/full-tb.sv" STUDY_MEMORY="$staging/moonshine_memory_staging.sv"
export STUDY_ARBITER="$here/../sdram-arbiter-study/staging_arbiter.sv" SD_READER="$reader/sdram_jpeg_reader.sv" SD_WRITER="$writer/sdram_jpeg_writer.sv" BUILD_DIR="$build/run"
bash "$build/wrapper.sh" | tee "$build/wrapper.log"
grep -q '^STAGING_DRAIN_PASS ' "$build/run/run.log"
grep -q '^SDRAM_WRITER_READER_INTEGRATION_PASS ' "$build/run/run.log"
grep -q '^BANK_QSPI_SCANOUT_CMODEL_PASS$' "$build/wrapper.log"
ulimit -c 0
code=0;timeout 600s "$build/run/obj/Vtb_bank_qspi_scanout" "+JPEG0=$JPEG0" "+JPEG1=$JPEG1" "+DUMP0=$build/mutant0.txt" "+DUMP1=$build/mutant1.txt" +STAGE_CORRUPT > "$build/mutant.log" 2>&1 || code=$?
[[ $code != 0 && $code != 124 ]];grep -q 'predecode staging drain mismatch' "$build/mutant.log"
! grep -q '^SDRAM_WRITER_READER_INTEGRATION_PASS' "$build/mutant.log"
echo 'SDRAM_WRITER_READER_LCD_PASS with corruption guard (bounded simulation only)'
