set -eu
source /opt/gamebub-openxc7-20261021/oss-cad-suite/environment
cd /mnt/c/mb70
verilator --version
verilator --cc --exe --build -j 2 --Wall --top-module cu71_yuv_pixel_pipe --Mdir /tmp/cu71-pixel-pipe-1793947215599603400 -CFLAGS '-O2 -std=c++17' /mnt/c/mb70/fpga/experiments/cu66-v71/direct-display/cu71_yuv_pixel_pipe.sv /mnt/c/mb70/fpga/experiments/cu66-v71/direct-display/tb_pixel_pipe.cpp
