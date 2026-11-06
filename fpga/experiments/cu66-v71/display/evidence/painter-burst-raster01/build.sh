set -eu
source /opt/gamebub-openxc7-20261021/oss-cad-suite/environment
cd /mnt/c/mb70
verilator --version
verilator --cc --exe --build -j 2 --Wall --top-module cu71_painter_burst_test --Mdir /tmp/cu71-painter-bram-1793944969067070200 -CFLAGS '-O2 -std=c++17 -DUSE_STRIP' /mnt/c/mb70/fpga/experiments/cu66-v71/display/cu71_painter_burst_test.sv /mnt/c/mb70/fpga/experiments/cu66-v71/display/cu71_painter_strip_burst.sv /mnt/c/mb70/fpga/experiments/cu66-v71/display/tb_painter_burst.cpp
