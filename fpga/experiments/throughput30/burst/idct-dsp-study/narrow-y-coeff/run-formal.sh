#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
: "${ORIGINAL:?Set ORIGINAL to the original jpeg_idct_y.v}"
: "${CANDIDATE:?Set CANDIDATE to jpeg_idct_y_coeff.v}"
: "${BUILD_DIR:?Set BUILD_DIR to a new path}"
yosys=${YOSYS:-yosys}
mkdir -p "$(dirname "$BUILD_DIR")"
mkdir "$BUILD_DIR"
build=$(cd "$BUILD_DIR" && pwd)
python3 "$here/generate.py" "$ORIGINAL" "$CANDIDATE" "$build/generated" > "$build/generate.log"
"$yosys" -V > "$build/version.txt"
run() { local label=$1 script=$2; timeout 120s "$yosys" -p "$script" > "$build/$label.log" 2>&1; grep -q 'End of script' "$build/$label.log"; }
p="$build/generated";h="$here"
run operand "read_verilog -formal $p/operand-original.v $p/operand-candidate.v $h/operand-miter.v; prep -top operand_miter -flatten; opt_clean -purge; chformal -lower; sat -set-init-zero -seq 2 -tempinduct -maxsteps 8 -prove-asserts -verify"
grep -q 'Induction step proven: SUCCESS!' "$build/operand.log"
run operand-reset "read_verilog -formal $p/operand-original.v $p/operand-candidate.v $h/operand-reset-miter.v; prep -top operand_miter -flatten; opt_clean -purge; chformal -lower; sat -seq 2 -set-at 1 rst 1 -set-at 1 check 0 -set-at 2 check 1 -prove-asserts -verify"
grep -q 'SAT proof finished - no model found: SUCCESS!' "$build/operand-reset.log"
run product "read_verilog -formal $h/product.v; prep -top product -flatten; opt; chformal -lower; sat -prove-asserts -verify"
grep -q 'SAT proof finished - no model found: SUCCESS!' "$build/product.log"
run state "read_verilog -formal $p/state-original.v $p/state-candidate.v $h/state-miter.v; prep -top state_miter -flatten; memory_map; opt; opt_clean -purge; chformal -lower; sat -set-init-zero -seq 2 -tempinduct -maxsteps 4 -prove-asserts -verify"
grep -q 'Induction step proven: SUCCESS!' "$build/state.log"
run state-reset "read_verilog -formal $p/state-original.v $p/state-candidate.v $h/state-reset-miter.v; prep -top state_miter -flatten; memory_map; opt; opt_clean -purge; chformal -lower; sat -seq 2 -set-at 1 rst 1 -set-at 1 check 0 -set-at 2 check 1 -prove-asserts -verify"
grep -q 'SAT proof finished - no model found: SUCCESS!' "$build/state-reset.log"
negative() { local label=$1 script=$2 code=0; timeout 90s "$yosys" -p "$script" > "$build/$label.log" 2>&1 || code=$?; if [[ $code == 0 || $code == 124 ]]; then echo "negative $label did not produce a counterexample" >&2; exit 1; fi; grep -q 'SAT proof finished - model found: FAIL!' "$build/$label.log"; grep -q 'proof did fail' "$build/$label.log"; }
negative operand-mutant "read_verilog -formal $p/operand-original.v $p/operand-mutant.v $h/operand-miter.v; prep -top operand_miter -flatten; opt_clean -purge; chformal -lower; sat -set-init-zero -seq 3 -prove-asserts -verify"
negative state-mutant "read_verilog -formal $p/state-original.v $p/state-mutant.v $h/state-miter.v; prep -top state_miter -flatten; memory_map; opt; opt_clean -purge; chformal -lower; sat -set-init-zero -seq 3 -prove-asserts -verify"
printf 'COMPOSITIONAL_EQUIVALENCE_OBLIGATIONS_PASS\n'
