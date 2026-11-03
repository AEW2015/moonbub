#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
: "${FIXTURE_DIR:?Set FIXTURE_DIR to generated fixture30 directory}"
: "${OUTPUT:?Set OUTPUT to result JSON path}"
python3 "$here/test_clean.py"
python3 "$here/clean-study.py" --fixtures "$FIXTURE_DIR" --output "$OUTPUT"
