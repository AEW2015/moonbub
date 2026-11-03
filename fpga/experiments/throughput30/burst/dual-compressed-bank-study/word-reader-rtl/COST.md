# Isolated reader cycle measurement

`cost.sh` builds the experimental synchronous byte RAM, ownership controller and
word reader with Verilator, then checks the simulation log using `verify_cost.py`.
Set `BUILD_DIR` to scratch space and provide Verilator on PATH. The source bytes
are a deterministic pattern, not JPEG payloads; the first length matches the
26,159-byte fixture and the second fills the 49,152-byte bank. The test checks
all byte values, little-endian words and strobes against that pattern and checks
byte requests, responses and word counts. Ingress and CRC commit occur before
timing starts. `out_ready` is permanently asserted and the granted bank stays
owned throughout. Cycles are measured from the start-accept edge through each
output handshake; the final handshake and `frame_done` coincide.

| Bytes | Words | First word | Total cycles | Full-word gap | Final strobe/gap | Time at assumed 100 MHz |
|---:|---:|---:|---:|---:|---:|---:|
| 26,159 | 6,540 | 13 cycles | 85,017 | 13 cycles | 0x7 / 10 cycles | 0.85017 ms |
| 49,152 | 12,288 | 13 cycles | 159,744 | 13 cycles | 0xf / 13 cycles | 1.59744 ms |

There is one request and one response per byte. The final gap for the shorter
frame is 10 cycles because the final word holds three bytes. Clock conversion is
arithmetic using an assumed 100 MHz, not a synthesis timing result. This excludes
network, QSPI, bank fill, decode, presentation and backpressure; it establishes
neither target throughput nor FPGA fit. Single-clock simulation does not validate
CDC or production integration. The clean wrapper output is recorded in
`cost-results.log`.
