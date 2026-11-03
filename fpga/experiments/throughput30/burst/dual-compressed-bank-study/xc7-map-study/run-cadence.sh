#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
cadence=$(cd "$here/../qspi-cadence10" && pwd)
storage=$(cd "$here/../bank-storage-rtl" && pwd)
: "${BUILD_DIR:?Set BUILD_DIR to a new empty scratch directory}"
: "${FIXTURE_DIR:?Set FIXTURE_DIR to the pinned JPEG fixtures}"
if [[ -d "$BUILD_DIR" && -n "$(ls -A "$BUILD_DIR")" ]]; then echo 'BUILD_DIR must be empty' >&2;exit 2;fi
mkdir -p "$BUILD_DIR";build=$(cd "$BUILD_DIR" && pwd)
(cd "$here" && sha256sum -c sources.sha256) > "$build/source-check.log"
python3 "$here/make_candidate.py" "$storage/two_bank_storage.sv" "$build/candidate.sv"
python3 - "$cadence/run.sh" "$build/wrapper.sh" <<'PY'
from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text()
changes=[('here=$(cd "$(dirname "$0")" && pwd)', 'here=${CADENCE_DIR:?}'),
 ('"$study/bank-storage-rtl/two_bank_storage.sv"','"${CANDIDATE_SOURCE:?}"')]
for a,b in changes:
 assert s.count(a)==1,a
 s=s.replace(a,b)
Path(sys.argv[2]).write_text(s)
PY
export BUILD_DIR="$build/run" CADENCE_DIR="$cadence" CANDIDATE_SOURCE="$build/candidate.sv"
bash "$build/wrapper.sh"
