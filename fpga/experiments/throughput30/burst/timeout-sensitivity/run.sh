#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
: "${FIXTURE_DIR:?Set FIXTURE_DIR to fixture30 output from network-rtl-study}"
out=${OUTPUT:-$(mktemp)}
python3 "$here/test_study.py"
python3 "$here/study.py" --fixtures "$FIXTURE_DIR" --frames 300 --seeds 10 --rate 8000000 --output "$out"
printf 'Wrote %s\n' "$out"
