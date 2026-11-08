#!/bin/bash
set -euo pipefail
export XILINX_VIVADO=/opt/amd-tools/2026.1/Vivado
"$XILINX_VIVADO/bin/vivado" -mode batch -nojournal -nolog -notrace -source run.tcl -tclargs "$PWD"
cd results
"$XILINX_VIVADO/bin/xvlog" --sv mapped.v ../tb_tables_unit.sv "$XILINX_VIVADO/data/verilog/src/glbl.v" >xvlog.log 2>&1
"$XILINX_VIVADO/bin/xelab" tb_tables_unit glbl -L unisims_ver -s tables_snapshot -mt 2 >xelab.log 2>&1
"$XILINX_VIVADO/bin/xsim" tables_snapshot -runall -log xsim.log
if ! grep -q TEST_PASS_TABLES_UNIT xsim.log; then exit 2; fi
