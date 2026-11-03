#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
full=$(cd "$here/../sdram-jpeg-full-study" && pwd)
: "${BUILD_DIR:?Set BUILD_DIR to a new empty scratch directory}"
: "${JPEG0:?Set JPEG0 to the pinned fixture}"
: "${JPEG1:?Set JPEG1 to the pinned fixture}"
if [[ -d "$BUILD_DIR" && -n "$(ls -A "$BUILD_DIR")" ]];then echo 'BUILD_DIR must be empty' >&2;exit 2;fi
mkdir -p "$BUILD_DIR";build=$(cd "$BUILD_DIR" && pwd);cd "$here"
sha256sum -c sources.sha256 > "$build/source-check.log"
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v > "$build/python-tests.log" 2>&1
python3 - "$full/run.sh" "$build/instrumented-wrapper.sh" <<'PY'
from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text()
items=[('here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)', 'here=${FULL_DIR:?}'),
 ('python3 "$here/make_full_tb.py" "$build/sdram-tb.sv" "$build/full-tb.sv"',
  'python3 "$here/make_full_tb.py" "$build/sdram-tb.sv" "$build/full-tb.sv"\npython3 "${METRICS_TOOL:?}" "$build/full-tb.sv" "$build/metric-tb.sv"'),
 ('STUDY_TB="$build/full-tb.sv"','STUDY_TB="$build/metric-tb.sv"')]
for a,b in items:
 assert s.count(a)==1,a
 s=s.replace(a,b)
Path(sys.argv[2]).write_text(s)
PY
export FULL_DIR="$full" METRICS_TOOL="$here/add_metrics.py" BUILD_DIR="$build/full-run"
bash "$build/instrumented-wrapper.sh" > "$build/wrapper.log" 2>&1
grep -q '^SDRAM_WRITER_READER_LCD_PASS' "$build/wrapper.log"
python3 "$here/analyze.py" "$build/full-run/run/run.log" > "$build/timing.json"
echo 'SDRAM_STAGE_TIMING_PASS one instrumented behavioral fixture; no physical timing claim'
