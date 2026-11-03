#!/usr/bin/env bash
set -euo pipefail
# Run from the FPGA source directory with Verilator and C++ tools on PATH.
# SIMULATION uses the behavioral SDRAM model, not physical SDRAM timing.
root=$(cd "$(dirname "$0")/../../../.." && pwd)
cd "$root"
build=${BUILD_DIR:-/tmp/moonbub-abort-study}
fixture=${JPEG_FILE:-$root/sim/pipeline64-420.jpg}
mkdir -p "$build"
ulimit -c 0
shopt -s nullglob
sources=(vendor/core_jpeg/src_v/*.v)
vendor=()
for f in "${sources[@]}"; do [[ $f == */jpeg_input.v ]] || vendor+=("$f"); done
base=experiments/throughput30/burst
for test in partial staging full inflight; do
  for flush in 0 1; do
    # The inflight case tests the candidate; a partial staging control exists separately.
    [[ ( $test == inflight || $test == full ) && $flush == 0 ]] && continue
    name=tb_abort_$test
    parameter=FLUSH_COLLECTOR
    memory=$base/abort-study/moonshine_memory_burst_abort.sv
    if [[ $test == partial ]]; then parameter=FLUSH_ON_ABORT; memory=$base/moonshine_memory_burst.sv; fi
    out=$build/$test-$flush
    verilator --binary --timing --assert -Wno-fatal -DSIMULATION -G${parameter}=$flush --top-module "$name" --Mdir "$out" \
      "$base/abort-study/$name.sv" "$memory" "$base/moonshine_sdram_burst.sv" \
      "$base/sdram_model_burst_verilator.sv" "$base/marker-followup/jpeg_input_followup.v" \
      experiments/throughput30/moonbub_tile_transpose.sv rtl/moonshine_core.sv rtl/moonshine_lcd.sv \
      "${vendor[@]}" > "$build/$test-$flush.build.log" 2>&1
    set +e
    timeout 180s "$out/V$name" +JPEG_FILE="$fixture" > "$build/$test-$flush.run.log" 2>&1
    status=$?
    set -e
    if [[ $flush == 0 ]]; then
      [[ $status != 0 && $status != 124 ]] || { echo "Unexpected control status: $test $status" >&2; exit 1; }
      if [[ $test == partial ]]; then expected=RECOVERY_FAULT; else expected=ABORT_STAGING_NOT_DRAINED; fi
      grep -q "$expected" "$build/$test-$flush.run.log"
    else
      [[ $status == 0 ]] && grep -q "TEST_PASS_ABORT_${test^^}" "$build/$test-$flush.run.log"
    fi
    echo "$test flush=$flush checked (exit $status)"
  done
done
# Directed simultaneous-abort/vblank control: the original core exhibits
# publication; the isolated candidate gives the abort priority.
for variant in original candidate; do
  core=rtl/moonshine_core.sv
  [[ $variant == candidate ]] && core=$base/abort-study/moonshine_core_abort_priority.sv
  out=$build/vblank-$variant
  verilator --binary --timing --assert -Wno-fatal -DSIMULATION -GFLUSH_COLLECTOR=1 --top-module tb_abort_vblank --Mdir "$out" \
    "$base/abort-study/tb_abort_vblank.sv" "$base/abort-study/moonshine_memory_burst_abort.sv" \
    "$base/moonshine_sdram_burst.sv" "$base/sdram_model_burst_verilator.sv" \
    "$base/marker-followup/jpeg_input_followup.v" experiments/throughput30/moonbub_tile_transpose.sv \
    "$core" rtl/moonshine_lcd.sv "${vendor[@]}" > "$build/vblank-$variant.build.log" 2>&1
  set +e
  timeout 180s "$out/Vtb_abort_vblank" +JPEG_FILE="$fixture" > "$build/vblank-$variant.run.log" 2>&1
  status=$?
  set -e
  if [[ $variant == original ]]; then
    [[ $status != 0 && $status != 124 ]] && grep -q ABORT_VBLANK_PUBLISHED_ABORTED_FRAME "$build/vblank-$variant.run.log"
  else
    [[ $status == 0 ]] && grep -q TEST_PASS_ABORT_VBLANK "$build/vblank-$variant.run.log"
  fi
  echo "vblank $variant checked (exit $status)"
done
