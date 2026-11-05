#!/bin/sh
set -eu
TASK_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
TASK_CONTAINER=${TASK_CONTAINER:-gamebub-cu66-v69-build}
TASK_PYTHON=${TASK_PYTHON:-python3}
TASK_SHA="$TASK_DIR/../hash/cu66_sha256_bytes.sv"
"$TASK_PYTHON" "$TASK_DIR/export_fixtures.py" > "$TASK_DIR/export.log" 2>&1
{
 docker exec "$TASK_CONTAINER" verilator --version
 docker exec "$TASK_CONTAINER" g++ --version
 docker exec "$TASK_CONTAINER" yosys -V
 docker inspect --format '{{.Image}}' "$TASK_CONTAINER"
} > "$TASK_DIR/environment.log" 2>&1
for TASK_STRIPS in 1 2; do
 docker exec "$TASK_CONTAINER" verilator --cc --exe --build -j 2 --Wall --top-module cu66_tile_rows -GSTRIP_BANKS="$TASK_STRIPS" --Mdir "/build/rows$TASK_STRIPS" -CFLAGS '-O2 -std=c++17' -LDFLAGS '-lz' "$TASK_DIR/cu66_tile_rows.sv" "$TASK_DIR/tb_rows.cpp" > "$TASK_DIR/build-rows$TASK_STRIPS.log" 2>&1
 docker exec "$TASK_CONTAINER" yosys -Q -p "read_verilog -sv $TASK_DIR/cu66_tile_rows.sv; chparam -set STRIP_BANKS $TASK_STRIPS cu66_tile_rows; hierarchy -check -top cu66_tile_rows; proc; opt; memory_dff; opt_clean; memory_collect; check; stat; write_json /build/rows$TASK_STRIPS-memory.json" > "$TASK_DIR/yosys-rows$TASK_STRIPS.log" 2>&1
 docker exec "$TASK_CONTAINER" cat "/build/rows$TASK_STRIPS-memory.json" | "$TASK_PYTHON" -c 'import sys,zlib;sys.stdout.buffer.write(zlib.compress(sys.stdin.buffer.read(),9))' > "$TASK_DIR/yosys-rows$TASK_STRIPS.json.zlib"
 docker exec "$TASK_CONTAINER" /build/rows$TASK_STRIPS/Vcu66_tile_rows "$TASK_DIR/fixtures.tsv" 6901 0 > "$TASK_DIR/rows$TASK_STRIPS-ideal.log" 2>&1
 for TASK_SEED in 6901 6902 6903; do
  docker exec "$TASK_CONTAINER" /build/rows$TASK_STRIPS/Vcu66_tile_rows "$TASK_DIR/fixtures.tsv" "$TASK_SEED" 1 > "$TASK_DIR/rows$TASK_STRIPS-seed$TASK_SEED.log" 2>&1
 done
 for TASK_HASH in 1 2; do
  docker exec "$TASK_CONTAINER" verilator --cc --exe --build -j 2 --Wall --top-module cu66_rows_sha256 -GSTRIP_BANKS="$TASK_STRIPS" -GHASH_BLOCKS="$TASK_HASH" --Mdir "/build/rows_sha$TASK_STRIPS$TASK_HASH" -CFLAGS '-O2 -std=c++17 -DROWS_HASH' -LDFLAGS '-lz' "$TASK_DIR/cu66_tile_rows.sv" "$TASK_SHA" "$TASK_DIR/cu66_rows_sha256.sv" "$TASK_DIR/tb_rows.cpp" > "$TASK_DIR/build-combined$TASK_STRIPS$TASK_HASH.log" 2>&1
  docker exec "$TASK_CONTAINER" /build/rows_sha$TASK_STRIPS$TASK_HASH/Vcu66_rows_sha256 "$TASK_DIR/fixtures.tsv" 6901 0 > "$TASK_DIR/combined$TASK_STRIPS$TASK_HASH-ideal.log" 2>&1
  for TASK_SEED in 6901 6902 6903; do
   docker exec "$TASK_CONTAINER" /build/rows_sha$TASK_STRIPS$TASK_HASH/Vcu66_rows_sha256 "$TASK_DIR/fixtures.tsv" "$TASK_SEED" 1 > "$TASK_DIR/combined$TASK_STRIPS$TASK_HASH-seed$TASK_SEED.log" 2>&1
  done
 done
done
"$TASK_PYTHON" "$TASK_DIR/audit_memory.py" "$TASK_DIR/yosys-rows1.json.zlib" "$TASK_DIR/yosys-rows2.json.zlib" > "$TASK_DIR/memory-verify.log" 2>&1
"$TASK_PYTHON" "$TASK_DIR/audit_results.py" > "$TASK_DIR/verify.log" 2>&1
