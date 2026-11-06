#!/bin/bash
set -eu
source /opt/gamebub-openxc7-20261021/oss-cad-suite/environment
cd /mnt/c/mb70
verilator --cc --exe --build -j 2 --Wall --top-module cu71_scanout --Mdir /tmp/cu71-scanout-build03 -CFLAGS '-O2 -std=c++17' fpga/experiments/cu66-v71/display/cu71_scanout.sv fpga/experiments/cu66-v71/display/cu71_lcd_lines.sv /mnt/c/mb70/fpga/experiments/cu66-v71/display/tb_scanout.cpp
