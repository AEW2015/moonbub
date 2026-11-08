#!/bin/bash
set -euo pipefail
/opt/amd-tools/2026.1/Vivado/bin/vivado -mode batch -nojournal -nolog -notrace -source run.tcl -tclargs "$PWD"
