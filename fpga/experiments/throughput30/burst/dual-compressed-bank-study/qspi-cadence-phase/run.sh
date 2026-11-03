#!/usr/bin/env bash
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
: "${BUILD_DIR:?}" "${FIXTURE_DIR:?}" "${RUN_DIR:?}"
frames=${FRAMES:-300}; jitter=${JITTER_CYCLES:-0}; pclk=${PCLK_HALF_PS:-17029}; phase=${CAPTURE_PHASE_CYCLES:-0}; wall=${TIMEOUT_SECONDS:-5400}
if [[ -d "$RUN_DIR" && -n "$(ls -A "$RUN_DIR")" ]]; then echo 'RUN_DIR must be empty' >&2; exit 2; fi
mkdir -p "$RUN_DIR/dumps"; RUN_DIR=$(cd "$RUN_DIR" && pwd);FIXTURE_DIR=$(cd "$FIXTURE_DIR" && pwd);BUILD_DIR=$(cd "$BUILD_DIR" && pwd)
sha256sum "$FIXTURE_DIR/manifest.json" > "$RUN_DIR/fixture-manifest.sha256"
ulimit -c 0
timeout "$wall" stdbuf -oL "$BUILD_DIR/obj/Vtb_bank_qspi_cadence10" "+FIXTURE_DIR=$FIXTURE_DIR" "+DUMP_DIR=$RUN_DIR/dumps" "+FRAMES=$frames" "+JITTER_CYCLES=$jitter" "+PCLK_HALF_PS=$pclk" "+CAPTURE_PHASE_CYCLES=$phase" > "$RUN_DIR/run.log" 2>&1
for dump in "$RUN_DIR"/dumps/*.txt; do
 id=$(basename "$dump" .txt)
 "$BUILD_DIR/cmodel" "$FIXTURE_DIR/$id.jpg" "$RUN_DIR/model$id.ppm" > "$RUN_DIR/cmodel$id.log"
 python3 "$here/compare.py" "$RUN_DIR/model$id.ppm" "$dump" > "$RUN_DIR/comparison$id.json"
 rm "$RUN_DIR/model$id.ppm"
done
python3 "$here/analyze.py" "$RUN_DIR" "$FIXTURE_DIR" --output "$RUN_DIR/analysis.json"
echo CADENCE_ANALYSIS_PASS
