#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
build=${BUILD_DIR:-$(mktemp -d)}
mkdir -p "$build";build=$(cd "$build" && pwd)
yosys=${YOSYS:-yosys}
"$yosys" -V
timeout 300s "$yosys" -p "read_verilog -formal $here/formal_mul.v; prep -top formal_mul -flatten; opt; chformal -lower; sat -set-assumes -prove-asserts -verify" > "$build/formal-mul.log" 2>&1
grep -q 'SAT proof finished - no model found: SUCCESS!' "$build/formal-mul.log"
grep -q 'End of script' "$build/formal-mul.log"
printf 'ARITHMETIC_FORMAL_PASS log=%s\n' "$build/formal-mul.log"
