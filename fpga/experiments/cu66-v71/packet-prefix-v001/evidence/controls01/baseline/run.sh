#!/bin/bash
set -euo pipefail
source /opt/gamebub-openxc7-20261021/oss-cad-suite/environment
cd '/mnt/c/mb70/fpga/experiments/cu66-v71/packet-prefix-v001/evidence/controls01/baseline'
verilator --cc --exe --build -j 2 -Wall --top-module cu71_packet_prefix -I. --Mdir obj cu71_packet_prefix.sv tb_packet.cpp -CFLAGS '-std=c++17 -O2' >build.log 2>&1
obj/Vcu71_packet_prefix cases.tsv 6910 >seed6910.log
obj/Vcu71_packet_prefix cases.tsv 6911 >seed6911.log
