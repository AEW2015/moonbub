set -eu
source /opt/gamebub-openxc7-20261021/oss-cad-suite/environment
cd /mnt/c/mb70
verilator --version
verilator --cc --exe --build -j 2 --Wall -Wno-PROCASSINIT --top-module cu71_direct_scanout --Mdir /tmp/cu71-direct-owner-1793950394549475100 -CFLAGS '-O2 -std=c++17' -I/mnt/c/mb70/fpga/experiments/cu66-v71/memory/evidence/direct-fast01 /mnt/c/mb70/fpga/experiments/cu66-v71/direct-display/cu71_direct_scanout.sv /mnt/c/mb70/fpga/experiments/cu66-v71/direct-display/cu71_cache_dma.sv /mnt/c/mb70/fpga/experiments/cu66-v71/direct-display/cu71_direct_cache.sv /mnt/c/mb70/fpga/experiments/cu66-v71/direct-display/cu71_yuv_pixel_pipe.sv /mnt/c/mb70/fpga/experiments/cu66-v71/direct-display/cu71_lcd_lines_direct.sv /mnt/c/mb70/fpga/experiments/cu66-v71/direct-display/tb_direct_scanout.cpp
