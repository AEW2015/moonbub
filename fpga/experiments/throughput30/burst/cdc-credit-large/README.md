# Larger FIFO and source-domain drain fence: isolated study

This experiment explores the transaction overhead of the 63-entry credit
candidate. It changes the test-only bridge to 2,048 physical entries (2,047
usable under the existing full rule), extends credit to 12 bits and preserves
the isolated `0xe0000054` source-domain credit register. These modules are not
production RTL; neither firmware nor hardware has been modified. A bigger
FIFO and its new register require a reviewed protocol and real CDC/timing work.

## A mailbox hazard found by negative test

With 40 MHz QSPI writes and a deliberately slow 25 MHz simulated core,
`tb_qspi_credit_large` sends 1,024-byte bursts using credits but does **not**
wait for the FIFO to drain before the existing core-mailbox `0x0c` read. After
the first 1,024 bytes, the mailbox returns zero rather than the expected 25,135
remaining bytes; only 673 payload bytes had been consumed and the bridge read
state was still waiting for drain. The negative test intentionally fails and
its log is `unfenced-25-expected-failure.log`. With a 100 MHz core the same
unfenced test passes in this limited workload. This is not a hardware failure
observation: it demonstrates that a deeper FIFO can increase the time before
an existing fixed-dummy-cycle status read receives its response. Larger FIFO
alone is therefore not a complete or safe flow-control fix.

The separate testbench-only fenced driver polls the conservative source-domain
free count until all 2,047 usable entries are free, then requests the ordinary
core status. Under the test's single-producer/reset assumptions, this prevents
its read from racing queued writes. It passes 26,159 ordered bytes in 26
bursts at four sampled start phases, with no modeled overflow:

| Modeled core clock | Fence polls | Maximum FIFO occupancy | Modeled transfer time |
| --- | ---: | ---: | ---: |
| 100 MHz | 27 | 1 | 1.53955 ms |
| 25 MHz stress | 308 | 386 | 2.29825 ms |

The write and status clocks are 40 and 16 MHz respectively, sampled at
200 MHz. Intervals include the serial testbench's modeled transactions, but
exclude ESP32 computation, driver/DMA scheduling and network. The fence is
not implemented in firmware and its serial polling costs have not been
measured on the device. Only these clock ratios, four phase offsets, one frame
size and a synthetic consumer were tested. Reset/disconnect, multiple writers,
CDC metastability, actual DMA/QSPI timing and correct acknowledgments remain
unverified. Any real protocol must specify bounded timeout and recovery.

## Local resource estimate

Yosys 0.52 `synth_xilinx -family xc7` mapped the **standalone bridge** with the
63-entry candidate to one RAMB36E1, and the larger candidate to five RAMB18E1
cells. The larger candidate produced 34 port-resizing warnings during mapping;
see `yosys-stat.log` for the final counts and warning count. This is an
isolated mapping estimate, not Vivado synthesis, a whole-design delta, a
place/route fit or timing signoff. Existing whole-device BRAM and timing are
already constrained; synthesis and implementation on the actual Artix-7 are
required before selecting a depth.

`run-verilator.sh` checks three core rates, the expected unfenced failure and
fenced cases at four phases; it requires Verilator 5.x, make, C++ and timeout.
`run-yosys.sh` regenerates standalone Yosys mapping logs. Saved evidence is
`verilator-summary.log`, `unfenced-25-expected-failure.log` and
`yosys-stat.log`. No real board, ESP32, JPEG pipeline or 30 fps is tested.
