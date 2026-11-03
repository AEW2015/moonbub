#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
: "${RTL_BINARY:?Set RTL_BINARY to Vtb_live_qspi}"
: "${FIXTURE_JPEG:?Set FIXTURE_JPEG to 0000.jpg}"
: "${OUTPUT_DIR:?Set OUTPUT_DIR to an empty output directory}"
mkdir -p "$OUTPUT_DIR"
port=${BRIDGE_PORT:-15535}
sender_pid=''
cleanup(){ if [[ -n "$sender_pid" ]] && kill -0 "$sender_pid" 2>/dev/null;then kill "$sender_pid" 2>/dev/null || true;wait "$sender_pid" 2>/dev/null || true;fi; }
trap cleanup EXIT
ulimit -c 0
for mode in badseq disconnect oversize truncate;do
 mkdir -p "$OUTPUT_DIR/$mode/dumps"
 python3 "$here/mock_sender.py" "$FIXTURE_JPEG" --port "$port" --mode "$mode" > "$OUTPUT_DIR/$mode/sender.log" 2>&1 & sender_pid=$!
 for _ in {1..100};do grep -q '^MOCK_LISTENING' "$OUTPUT_DIR/$mode/sender.log" && break; kill -0 "$sender_pid" 2>/dev/null || { echo 'sender failed' >&2;exit 1; };sleep 0.1;done
 grep -q '^MOCK_LISTENING' "$OUTPUT_DIR/$mode/sender.log"
 status=0
 BRIDGE_PORT="$port" timeout 60s "$RTL_BINARY" "+DUMP_DIR=$OUTPUT_DIR/$mode/dumps" > "$OUTPUT_DIR/$mode/rtl.log" 2>&1 || status=$?
 for _ in {1..100};do kill -0 "$sender_pid" 2>/dev/null || break;sleep 0.1;done
 if kill -0 "$sender_pid" 2>/dev/null;then echo "sender did not exit in $mode" >&2;exit 1;fi
 wait "$sender_pid";sender_pid=''
 if [[ "$status" == 0 || "$status" == 124 ]];then echo "unexpected RTL status $status in $mode" >&2;exit 1;fi
 grep -q 'MOCK_SENDER_PASS' "$OUTPUT_DIR/$mode/sender.log"
 case "$mode" in
  badseq) grep -q 'sequence expected=0 got=1' "$OUTPUT_DIR/$mode/rtl.log";;
  disconnect) grep -q 'bridge socket read error -2' "$OUTPUT_DIR/$mode/rtl.log";;
  oversize) grep -q 'bridge socket read error -3' "$OUTPUT_DIR/$mode/rtl.log";;
  truncate) grep -q 'bridge socket read error -4' "$OUTPUT_DIR/$mode/rtl.log";;
 esac
 if grep -q 'TEST_PASS_LIVE_QSPI' "$OUTPUT_DIR/$mode/rtl.log";then echo "unexpected pass marker $mode" >&2;exit 1;fi
 echo "NEGATIVE_PASS $mode status=$status"
done
