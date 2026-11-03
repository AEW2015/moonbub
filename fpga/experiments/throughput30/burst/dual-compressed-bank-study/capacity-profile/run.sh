#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
: "${GAMEPLAY_MANIFEST:?Set GAMEPLAY_MANIFEST to local 300-frame JPEG manifest}"
: "${COMBAT_MANIFEST:?Set COMBAT_MANIFEST to local accelerated 90-frame combat JPEG manifest}"
: "${SYNTHETIC_MANIFEST:?Set SYNTHETIC_MANIFEST to local synthetic long-run JPEG manifest}"
: "${OUTPUT:?Set OUTPUT to a writable JSON path}"
python3 "$here/test_analyze.py"
python3 "$here/analyze.py" --gameplay-manifest "$GAMEPLAY_MANIFEST" --synthetic-manifest "$SYNTHETIC_MANIFEST" --combat-manifest "$COMBAT_MANIFEST" --output "$OUTPUT"
