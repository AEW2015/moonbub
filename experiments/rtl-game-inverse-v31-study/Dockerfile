FROM ubuntu:24.04
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends verilator iverilog yosys g++ make python3 ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /work
