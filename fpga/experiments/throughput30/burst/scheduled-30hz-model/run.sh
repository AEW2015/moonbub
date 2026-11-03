#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
: "${OUTPUT:?Set OUTPUT to a writable output JSON path}"
python3 "$here/test_model.py"
python3 "$here/model.py" --output "$OUTPUT"
