set -eu
source /opt/gamebub-openxc7-20261021/oss-cad-suite/environment
verilator --version
verilator --cc --exe --build -j 2 --Wall --top-module cu71_ab38_decoder_cfgpipe --Mdir /tmp/cu71-entropy-cfgpipe-1793947012836816900 -CFLAGS '-O2 -std=c++17' -LDFLAGS '-lz' /mnt/c/mb70/fpga/experiments/cu66-v71/entropy/evidence/regression01/source.sv /mnt/c/mb70/fpga/experiments/cu66-v71/entropy/evidence/regression01/tb.cpp
g++ -O2 -std=c++17 -pthread -I/opt/gamebub-openxc7-20261021/oss-cad-suite/share/verilator/include -I/tmp/cu71-entropy-cfgpipe-1793947012836816900 /mnt/c/mb70/fpga/experiments/cu66-v71/entropy/evidence/regression01/cfg.cpp /tmp/cu71-entropy-cfgpipe-1793947012836816900/Vcu71_ab38_decoder_cfgpipe__ALL.a /tmp/cu71-entropy-cfgpipe-1793947012836816900/verilated.o /tmp/cu71-entropy-cfgpipe-1793947012836816900/verilated_threads.o -o /tmp/cu71-entropy-cfgpipe-1793947012836816900/cfg_sweep
