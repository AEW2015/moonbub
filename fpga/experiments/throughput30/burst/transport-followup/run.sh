#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
root=$(cd -- "$here/../../../../.." && pwd)
output=${OUTPUT_DIR:-$(mktemp -d)}
mkdir -p "$output"
if [[ -e "$output/fixtures" ]]; then echo 'fixture output already exists' >&2; exit 2; fi
python=${PYTHON:-python3}
"$python" "$here/test_model.py" -v
"$python" "$root/experiments/fixture30/generate.py" "$output/fixtures" --frames 10
"$python" "$here/model.py" --fixtures "$output/fixtures" --frames 1800 --out "$output/results.json"
"$python" "$here/calibrate.py" --fixtures "$output/fixtures" --output "$output/calibration.json"
printf 'Saved outputs to %s\n' "$output"
