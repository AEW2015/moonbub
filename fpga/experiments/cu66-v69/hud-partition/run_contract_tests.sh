#!/usr/bin/env bash
set -euo pipefail
study_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
native_dir=$(cd -- "$study_dir/../../../../experiments/cu66-native-v69" && pwd)
build_dir=${BUILD_DIR:-/build/hud-partition}
mkdir -p "$build_dir"
g++ -std=c++17 -O3 -Wall -Wextra -Wconversion -Werror "$study_dir/test_hud_gate.cpp" -o "$build_dir/test_hud_gate"
"$build_dir/test_hud_gate" "$native_dir"
g++ -std=c++17 -O3 -Wall -Wextra -Wconversion -Werror "$native_dir/test_hud_directed.cpp" -o "$build_dir/test_hud_directed_from_frozen"
"$build_dir/test_hud_directed_from_frozen" "$native_dir/hud-directed.tsv"
g++ -std=c++17 -O1 -g -Wall -Wextra -Wconversion -Werror -fsanitize=address,undefined -fno-omit-frame-pointer "$study_dir/test_hud_gate.cpp" -o "$build_dir/test_hud_gate_sanitized"
"$build_dir/test_hud_gate_sanitized" "$native_dir"
