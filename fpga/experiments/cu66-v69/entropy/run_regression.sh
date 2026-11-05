#!/bin/sh
# Run from any directory. Host Python must contain NumPy; RTL tools live in Docker.
set -eu
TASK_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
TASK_ROOT=$(CDPATH= cd -- "$TASK_DIR/../../../.." && pwd)
TASK_CONTAINER=${TASK_CONTAINER:-gamebub-cu66-v69-build}
TASK_PYTHON=${TASK_PYTHON:-python3}
"$TASK_PYTHON" "$TASK_DIR/export_fixtures.py" > "$TASK_DIR/export.log" 2>&1
{
 docker exec "$TASK_CONTAINER" verilator --version
 docker exec "$TASK_CONTAINER" g++ --version
 docker exec "$TASK_CONTAINER" yosys -V
 docker inspect --format '{{.Image}}' "$TASK_CONTAINER"
} > "$TASK_DIR/environment.log" 2>&1
docker exec "$TASK_CONTAINER" verilator --cc --exe --build -j 2 --Wall --top-module cu66_ab38_decoder --Mdir /build/entropy -CFLAGS '-O2 -std=c++17' -LDFLAGS '-lz' "$TASK_DIR/cu66_ab38_decoder.sv" "$TASK_DIR/tb_entropy.cpp" > "$TASK_DIR/build.log" 2>&1
docker exec "$TASK_CONTAINER" yosys -Q -p "read_verilog -sv $TASK_DIR/cu66_ab38_decoder.sv; hierarchy -check -top cu66_ab38_decoder; proc; check; stat" > "$TASK_DIR/yosys-proc.log" 2>&1
for TASK_SEED in 6901 6902; do
 docker exec "$TASK_CONTAINER" /build/entropy/Vcu66_ab38_decoder "$TASK_DIR/actual.tsv" "$TASK_SEED" 1371 > "$TASK_DIR/actual-seed$TASK_SEED.log" 2>&1
done
for TASK_SEED in 6901 6902 6903; do
 docker exec "$TASK_CONTAINER" /build/entropy/Vcu66_ab38_decoder "$TASK_DIR/directed.tsv" "$TASK_SEED" 31 --abort-tests > "$TASK_DIR/directed-seed$TASK_SEED.log" 2>&1
 docker exec "$TASK_CONTAINER" /build/entropy/Vcu66_ab38_decoder "$TASK_DIR/stress.tsv" "$TASK_SEED" 120 --abort-tests > "$TASK_DIR/stress-seed$TASK_SEED.log" 2>&1
done
"$TASK_PYTHON" "$TASK_DIR/audit_results.py" > "$TASK_DIR/verify.log" 2>&1
