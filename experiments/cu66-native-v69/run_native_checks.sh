#!/usr/bin/env bash
set -euo pipefail
study_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
build_dir=${BUILD_DIR:-/build/native-cmake}
cmake -S "$study_dir" -B "$build_dir" -DCMAKE_BUILD_TYPE=Release
cmake --build "$build_dir" -j2
"$build_dir/test_native" "$study_dir"
"$build_dir/ab38_check" "$study_dir/planes.tsv"
"$build_dir/test_entropy_directed" "$study_dir/entropy-directed.tsv"
"$build_dir/test_hud_directed" "$study_dir/hud-directed.tsv"
"$build_dir/fuzz_native" "$study_dir"
"$build_dir/native_decoder" "$study_dir/index.tsv" 1
