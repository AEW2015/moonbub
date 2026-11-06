set -eu
source /opt/gamebub-openxc7-20261021/oss-cad-suite/environment
cd /mnt/c/mb70
verilator --version
verilator --cc --exe --build -j 2 --Wall -Wno-PROCASSINIT --top-module cu71_scanout_banked --Mdir /tmp/cu71-bl8-scanout-1793944558721048600 -CFLAGS '-O2 -std=c++17' /mnt/c/mb70/fpga/experiments/cu66-v71/display/cu71_scanout_banked.sv /mnt/c/mb70/fpga/experiments/cu66-v71/display/cu71_lcd_lines.sv /mnt/c/mb70/fpga/experiments/cu66-v71/display/tb_scanout_banked_metrics.cpp
