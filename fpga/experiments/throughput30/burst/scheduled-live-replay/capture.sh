#!/usr/bin/env bash
# Capture actual emulator-emitted, adapter-validated event bodies; loopback only.
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
: "${GUEST_INPUT_DIR:?directory with guest.elf, guest-flash.bin and fixture.trace}"
: "${ESP_EMU:?esp-emu executable}"
: "${RTL_BINARY:?multiframe Vtb_live_multiframe executable}"
: "${OUTPUT_DIR:?new nonexistent output directory}"
if [[ -e "$OUTPUT_DIR" ]];then echo 'OUTPUT_DIR must not exist' >&2;exit 2;fi
mkdir -p "$OUTPUT_DIR/dumps";out=$(cd -- "$OUTPUT_DIR" && pwd)
cp "$GUEST_INPUT_DIR"/{guest.elf,guest-flash.bin,fixture.trace} "$out/"
pid=''
cleanup(){ if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null;then kill "$pid" 2>/dev/null || true;wait "$pid" 2>/dev/null || true;fi; }
trap cleanup EXIT
python3 -u "$here/record-adapter.py" "$out" "$ESP_EMU" > "$out/adapter.log" 2>&1 & pid=$!
for _ in {1..300};do grep -q '^BRIDGE_LISTENING' "$out/adapter.log" && break;kill -0 "$pid" 2>/dev/null || { echo 'adapter failed' >&2;exit 1; };sleep 0.1;done
grep -q '^BRIDGE_LISTENING' "$out/adapter.log"
ulimit -c 0
BRIDGE_PORT=15536 timeout 400s "$RTL_BINARY" "+DUMP_DIR=$out/dumps" > "$out/rtl.log" 2>&1
for _ in {1..100};do kill -0 "$pid" 2>/dev/null || break;sleep 0.1;done
if kill -0 "$pid" 2>/dev/null;then echo 'adapter did not exit' >&2;exit 1;fi
wait "$pid";pid=''
grep -q '^MULTI_ADAPTER_PASS events=84 commits=2 aborts=1' "$out/adapter.log"
grep -q 'MULTI_GUEST_PASS events=84 commits=2 aborts=1' "$out/guest.log"
grep -q '^TEST_PASS_LIVE_MULTIFRAME' "$out/rtl.log"
python3 - "$out" <<'PY'
import hashlib,json,struct,sys
from pathlib import Path
p=Path(sys.argv[1]);raw=(p/'guest-events.bin').read_bytes();rows=[json.loads(x) for x in (p/'adapter-events.jsonl').read_text().splitlines()];pos=0;seq=0
while pos<len(raw):
 if pos+4>len(raw):raise ValueError('truncated length')
 n=struct.unpack_from('>I',raw,pos)[0];pos+=4
 if not 9<=n<=1039 or pos+n>len(raw):raise ValueError('bad length')
 b=raw[pos:pos+n];pos+=n;a=rows[seq]
 if a['seq']!=seq or a['length']!=n or a['sha256']!=hashlib.sha256(b).hexdigest():raise ValueError('event audit mismatch')
 seq+=1
if seq!=len(rows) or seq!=84:raise ValueError('event count')
print('GUEST_CAPTURE_PASS',seq,'events',hashlib.sha256(raw).hexdigest())
PY
