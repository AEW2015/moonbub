set -eu
source /opt/gamebub-openxc7-20261021/oss-cad-suite/environment
verilator --version
verilator --cc --exe --build -j 2 --Wall --top-module cu71_ab38_decoder_cfgpipe --Mdir /tmp/cu71-entropy-cfgpipe-1793947062375123000 -CFLAGS '-O2 -std=c++17' -LDFLAGS '-lz' /mnt/c/mb70/fpga/experiments/cu66-v71/entropy/evidence/regression02/cu71_ab38_decoder_cfgpipe.sv /mnt/c/mb70/fpga/experiments/cu66-v71/entropy/evidence/regression02/tb.cpp
g++ -O2 -std=c++17 -pthread -I/opt/gamebub-openxc7-20261021/oss-cad-suite/share/verilator/include -I/tmp/cu71-entropy-cfgpipe-1793947062375123000 /mnt/c/mb70/fpga/experiments/cu66-v71/entropy/evidence/regression02/cfg.cpp /tmp/cu71-entropy-cfgpipe-1793947062375123000/Vcu71_ab38_decoder_cfgpipe__ALL.a /tmp/cu71-entropy-cfgpipe-1793947062375123000/verilated.o /tmp/cu71-entropy-cfgpipe-1793947062375123000/verilated_threads.o -o /tmp/cu71-entropy-cfgpipe-1793947062375123000/cfg_sweep
