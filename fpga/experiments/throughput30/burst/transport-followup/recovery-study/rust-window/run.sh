#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
root=$(cd -- "$here/../../../../../../.." && pwd)
build=${OUTPUT_DIR:-$(mktemp -d)}
if [[ -d "$build" && -n "$(ls -A "$build")" ]]; then echo 'OUTPUT_DIR must be empty' >&2; exit 2; fi
mkdir -p "$build"; build=$(cd -- "$build" && pwd)
rustc=${RUSTC:-rustc}; python=${PYTHON:-python3}
cp "$root/firmware/handheld/src/streaming/protocol.rs" "$here/window.rs" "$here/replay.rs" "$build/"
cat > "$build/lib.rs" <<'RS'
#![cfg_attr(not(test), no_std)]
#[path="protocol.rs"] pub mod protocol;
#[path="window.rs"] pub mod window;
#[used]
#[no_mangle]
pub static MSV1_WINDOW_SIZE_PROBE: [u8; core::mem::size_of::<window::Window>()] = [0; core::mem::size_of::<window::Window>()];
RS
cat > "$build/Cargo.toml" <<'TOML'
[package]
name="msv1-window-research"
version="0.1.0"
edition="2021"
[lib]
path="lib.rs"
TOML
"$rustc" --version
"$rustc" --edition=2021 --test "$build/lib.rs" -o "$build/tests"
"$build/tests" --nocapture | tee "$build/host-tests.log"
"$rustc" --edition=2021 -O "$build/replay.rs" -o "$build/replay"
"$python" "$root/experiments/fixture30/generate.py" "$build/fixtures" --frames 10
timeout 180s "$python" "$here/crosscheck.py" --fixtures "$build/fixtures" --executable "$build/replay" --out "$build/crosscheck.json"
if [[ ${CROSS_XTENSA:-0} == 1 ]]; then
  cargo=${CARGO:-cargo}; toolchain=${CROSS_TOOLCHAIN:-esp193}
  : "${XTENSA_NM:?Set XTENSA_NM to an xtensa-esp32s3-elf-nm executable}"
  for target in xtensa-esp32s3-none-elf xtensa-esp32s3-espidf; do
    (cd "$build" && timeout 300s "$cargo" "+$toolchain" build -Z build-std=core --target "$target" --release)
    "$XTENSA_NM" -S --size-sort "$build/target/$target/release/libmsv1_window_research.rlib" 2>/dev/null | grep 'MSV1_WINDOW_SIZE_PROBE'
  done
fi
printf 'Outputs retained at %s\n' "$build"
