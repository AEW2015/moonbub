#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
: "${OUTPUT:?Set OUTPUT to a writable result JSON path}"
python3 "$here/test_audit.py"
python3 "$here/audit.py" "$OUTPUT"
