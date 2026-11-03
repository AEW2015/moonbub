#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
build=${BUILD_DIR:-$(mktemp -d)}
mkdir -p "$build";build=$(cd -- "$build" && pwd)
"${RUSTC:-rustc}" --edition=2021 --test --cfg 'feature="esp_idf"' "$here/heap_profile.rs" -o "$build/heap-tests"
"$build/heap-tests"
