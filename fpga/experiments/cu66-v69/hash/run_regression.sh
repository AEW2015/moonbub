#!/bin/sh
set -eu
TASK_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
TASK_CONTAINER=${TASK_CONTAINER:-gamebub-cu66-v69-build}
TASK_PYTHON=${TASK_PYTHON:-python3}
"$TASK_PYTHON" "$TASK_DIR/export_fixtures.py" > "$TASK_DIR/export.log" 2>&1
{
 docker exec "$TASK_CONTAINER" verilator --version
 docker exec "$TASK_CONTAINER" g++ --version
 docker exec "$TASK_CONTAINER" yosys -V
 docker inspect --format '{{.Image}}' "$TASK_CONTAINER"
} > "$TASK_DIR/environment.log" 2>&1
for TASK_BANKS in 1 2; do
 docker exec "$TASK_CONTAINER" verilator --cc --exe --build -j 2 --Wall --top-module cu66_sha256_bytes -GBUFFER_BLOCKS="$TASK_BANKS" --Mdir "/build/hash$TASK_BANKS" -CFLAGS '-O2 -std=c++17' -LDFLAGS '-lz' "$TASK_DIR/cu66_sha256_bytes.sv" "$TASK_DIR/tb_hash.cpp" > "$TASK_DIR/build-banks$TASK_BANKS.log" 2>&1
 docker exec "$TASK_CONTAINER" yosys -Q -p "read_verilog -sv $TASK_DIR/cu66_sha256_bytes.sv; chparam -set BUFFER_BLOCKS $TASK_BANKS cu66_sha256_bytes; hierarchy -check -top cu66_sha256_bytes; proc; check; stat" > "$TASK_DIR/yosys-banks$TASK_BANKS.log" 2>&1
 docker exec "$TASK_CONTAINER" "/build/hash$TASK_BANKS/Vcu66_sha256_bytes" "$TASK_DIR/fixtures.tsv" 6901 0 > "$TASK_DIR/banks$TASK_BANKS-ideal.log" 2>&1
 for TASK_SEED in 6901 6902 6903; do
  docker exec "$TASK_CONTAINER" "/build/hash$TASK_BANKS/Vcu66_sha256_bytes" "$TASK_DIR/fixtures.tsv" "$TASK_SEED" 1 > "$TASK_DIR/banks$TASK_BANKS-seed$TASK_SEED.log" 2>&1
 done
done
"$TASK_PYTHON" "$TASK_DIR/audit_results.py" > "$TASK_DIR/verify.log" 2>&1
