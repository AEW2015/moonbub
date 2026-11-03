#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
: "${FPGA_DIR:?Set FPGA_DIR to the original FPGA tree}"
: "${BUILD_DIR:?Set BUILD_DIR to a new directory}"
verilator=${VERILATOR:-verilator};fpga=$(cd "$FPGA_DIR" && pwd);src=$fpga/vendor/core_jpeg/src_v
mkdir -p "$(dirname "$BUILD_DIR")";mkdir "$BUILD_DIR";build=$(cd "$BUILD_DIR" && pwd)
"$verilator" --version > "$build/version.txt"
sha256sum "$src"/jpeg_idct*.v > "$build/source-sha256.txt"
"$verilator" --binary --timing --assert -Wno-fatal --top-module tb_storage --Mdir "$build/obj-storage" \
 "$src/jpeg_idct_ram.v" "$src/jpeg_idct_ram_dp.v" "$src/jpeg_idct_transpose.v" "$src/jpeg_idct_transpose_ram.v" "$src/jpeg_idct_fifo.v" "$here/tb_storage.sv" > "$build/build-storage.log" 2>&1
ulimit -c 0
timeout 30s "$build/obj-storage/Vtb_storage" +DROP=0 > "$build/complete.log" 2>&1
timeout 30s "$build/obj-storage/Vtb_storage" +DROP=0 +SEPARATE=1 > "$build/separate-storage.log" 2>&1
grep -q 'STORAGE_RESET_TEST_PASS drop=0' "$build/separate-storage.log"
timeout 30s "$build/obj-storage/Vtb_storage" +BUSY=1 > "$build/busy.log" 2>&1
grep -q 'TRANSPOSE_FORCED_BUSY_PASS accepted=128 rejected_offer=1' "$build/busy.log"
timeout 30s "$build/obj-storage/Vtb_storage" +DROP=1 > "$build/missing.log" 2>&1
grep -q 'TRANSPOSE_COMPLETE_BLOCK_PASS valid_cycles=64 differing_cycles=0' "$build/complete.log"
grep -q 'TRANSPOSE_MISSING_INDEX_DETECTED valid_cycles=64 differing_cycles=4' "$build/missing.log"
grep -q 'INPUT_SPARSE_MASK_PASS valid_cycles=64' "$build/complete.log"
grep -q 'FIFO_VALID_ID_PASS' "$build/complete.log"
"$verilator" --binary --timing --assert -Wno-fatal --top-module tb_idct_reset --Mdir "$build/obj-idct" "$src"/jpeg_idct*.v "$here/tb_idct_reset.sv" > "$build/build-idct.log" 2>&1
timeout 60s "$build/obj-idct/Vtb_idct_reset" > "$build/idct.log" 2>&1
timeout 60s "$build/obj-idct/Vtb_idct_reset" +SEPARATE=1 > "$build/separate-idct.log" 2>&1
grep -q 'IDCT_RESET_SPARSE_FRAME_PASS valid_outputs=64' "$build/separate-idct.log"
grep -q 'CONNECTED_X_ACCEPT_AND_COMPLETE_PASS x=64 transpose=64' "$build/idct.log"
grep -q 'CONNECTED_X_ACCEPT_AND_COMPLETE_PASS x=64 transpose=64' "$build/separate-idct.log"
grep -q 'RESET_EDGE_POISON_WRITE_OBSERVED' "$build/idct.log"
grep -q 'IDCT_RESET_SPARSE_FRAME_PASS valid_outputs=64' "$build/idct.log"
echo STORAGE_RESET_WRAPPER_PASS
