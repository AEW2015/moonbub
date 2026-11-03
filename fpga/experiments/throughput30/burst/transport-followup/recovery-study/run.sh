#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
root=$(cd -- "$here/../../../../../.." && pwd)
build=${OUTPUT_DIR:-$(mktemp -d)}
if [[ -d "$build" && -n "$(ls -A "$build")" ]]; then echo 'OUTPUT_DIR must be empty' >&2; exit 2; fi
mkdir -p "$build";build=$(cd -- "$build" && pwd)
python=${PYTHON:-python3};rustc=${RUSTC:-rustc}
cp "$here/rust_replay.rs" "$root/firmware/handheld/src/streaming/protocol.rs" "$build/"
"$rustc" --version
"$rustc" --edition=2021 -O "$build/rust_replay.rs" -o "$build/rust-replay"
REPLAY_EXE="$build/rust-replay" "$python" "$here/test_recovery.py" -v
"$python" "$root/experiments/fixture30/generate.py" "$build/fixtures" --frames 10
"$python" "$here/diagnose_sof.py" --fixtures "$build/fixtures" --out "$build/sof-diagnosis.json"
for spec in '8 100' '8 33' '10 100'; do
 read -r rate deadline <<<"$spec"
 timeout 180s "$python" "$here/study.py" --fixtures "$build/fixtures" --rust-replay "$build/rust-replay" --frames 600 --seeds 5 --wire-mbps "$rate" --deadline-ms "$deadline" --out "$build/results-${rate}mbps-${deadline}ms.json"
done
printf 'Artifacts in %s\n' "$build"
