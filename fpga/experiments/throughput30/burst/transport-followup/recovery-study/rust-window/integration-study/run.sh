#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
root=$(cd -- "$here/../../../../../../../.." && pwd)
build=${OUTPUT_DIR:-$(mktemp -d)}
if [[ -d "$build" && -n "$(ls -A "$build")" ]]; then echo 'OUTPUT_DIR must be empty' >&2; exit 2; fi
mkdir -p "$build"; build=$(cd -- "$build" && pwd)
rustc=${RUSTC:-rustc}
cp "$root/firmware/handheld/src/streaming/protocol.rs" "$here/../window.rs" "$here/model.rs" "$here/fixture.rs" "$build/"
cat > "$build/lib.rs" <<'RS'
#![cfg_attr(not(test), no_std)]
#[path="protocol.rs"] pub mod protocol;
#[path="window.rs"] pub mod window;
#[path="model.rs"] pub mod model;
RS
cat > "$build/Cargo.toml" <<'TOML'
[package]
name="msv1-window-integration-research"
version="0.1.0"
edition="2021"
[lib]
path="lib.rs"
TOML
"$rustc" --version | tee "$build/rustc-version.log"
"$rustc" --edition=2021 --test "$build/lib.rs" -o "$build/tests"
timeout 60s "$build/tests" --nocapture | tee "$build/host-tests.log"
"$rustc" --edition=2021 -O "$build/fixture.rs" -o "$build/fixture"
timeout 60s "$build/fixture" "$root/host/fixtures/pattern-720x480-420-q65.jpg" | tee "$build/fixture.log"
sha256sum "$build/protocol.rs" "$build/window.rs" "$build/model.rs" "$root/host/fixtures/pattern-720x480-420-q65.jpg" > "$build/sources.sha256"
if [[ ${CROSS_XTENSA:-0} == 1 ]]; then
 cargo=${CARGO:-cargo}; toolchain=${CROSS_TOOLCHAIN:-esp193}
 for target in xtensa-esp32s3-none-elf xtensa-esp32s3-espidf; do
  (cd "$build" && timeout 300s "$cargo" "+$toolchain" build -Z build-std=core --target "$target" --release) 2>&1 | tee "$build/cross-$target.log"
 done
fi
printf 'Outputs retained at %s\n' "$build"
