# Experimental source-domain FIFO credits

This isolated candidate investigates an actual free-entry status for the
64-slot asynchronous host-write FIFO. The current `0x0c` register reports
remaining JPEG bytes, not free FIFO entries. No production RTL or firmware is
changed, and the candidate is **not ready for hardware**.

`moonshine_bus_cdc_credit.sv` derives a conservative source-clock `spi_free`
from the producer write pointer and the synchronized Gray-coded consumer read
pointer. It reports `63 - used` because the existing full condition reserves
one slot, clamps an unexpected computed occupancy above 63 to zero, and uses
no unsynchronized consumer pointer in the candidate logic. A companion
experimental endpoint maps this status locally at **0xe0000054** and avoids
issuing a core mailbox read for that local status. This experimental register
is not implemented in the production design or firmware. The status counts FIFO
entries, and applies to this producer in the same source-clock/reset domain.
A safe sender must limit each subsequent write burst to the returned free count
and ensure no other writer can consume credits between the read and write.
An initial credit read cannot authorize a 1,024-byte burst into a 63-entry
queue; use sub-bursts, a real hardware handshake, or another proven scheme.

Two independent digital testbenches run in Verilator 5.020:

1. `tb_cdc_credit` offers 3,000 ordered words at an aggressive 200 MHz source
   clock against modeled 100, 50 and 25 MHz consumers, checks each delivered word and
   validates at every source negative edge that reported credits never exceed
   a testbench-only oracle reading actual pointer occupancy. At 100 MHz it records 8,755
   credit-blocked source cycles (20,504 at 50 MHz; 44,010 at 25 MHz), zero
   lost writes and 63 free entries after drain; pointer counters wrap repeatedly.
2. `tb_qspi_credit` exercises the actual experimental QSPI endpoint at 40 MHz
   quad writes / 16 MHz reads, a 200 MHz sampler and intentionally slowed 25 MHz
   core; it reads the experimental status and limits each write to those
   credits. All 26,159 ordered payload bytes arrive over 416 sub-bursts, with
   no modeled overflow; maximum observed occupancy was 26 entries, and the
   digital transfer including status reads took 3.80665 ms in the zero-phase
   run. This artificial clock mix and synthetic consumer are stress conditions,
   not a production throughput measurement. It also checks `0x0c` remains
   frame-bytes-remaining and the status read does not break other mailbox reads.

The checked-in `credit-repro-summary.log` records a complete runner execution
at four sampled start phases. Reproduce with Verilator 5.x, make, C++, GNU timeout:

```sh
fpga/experiments/throughput30/burst/cdc-credit/run-verilator.sh
```

Open issues before integration: endpoint and FIFO reset ordering, partial
transactions and disconnects, multiple producers, asynchronous metastability,
all relevant clock phases/frequencies, counters under overflow, intentional
fault injection, status read during reset, finite precision and wrap proofs,
actual target timing/area, interaction with overlay/host traffic and the
firmware protocol. The source-domain value must be carried/read coherently and
its relationship to accepted writes proved for real SPI transaction boundaries.
The firmware has not been changed to use it. Verilator's two-state functional
checks do not establish physical CDC correctness or 30 fps. A real device
requires formal CDC/timing review and hardware validation.

Vivado XSim 2025.2 also passed the 100 MHz core / 200 MHz source standalone
credit stress with the same 3,000 words, 8,755 blocked cycles and zero losses;
see `credit-core-xsim.log`. The isolated behavioral project used an available
`xck24` part because the installed tool lacks the target Artix-7 support. This
is a four-state behavioral cross-check, not target-device synthesis, timing or
proof of metastability safety. XSim reported that existing RTL reads pointer
`rp` before its declaration; it compiled and ran, but the warning remains a
candidate cleanup item.

## Ten-frame full FPGA-side pipeline experiment

A separate Verilator test connects the experimental credit endpoint and CDC
FIFO to the actual JPEG core with the later isolated EOI guard, the
experimental tile/burst path, and the active LCD. Ten distinct 720×480 JPEGs
are scheduled at 30 Hz. The source has an abstract upstream one-frame queue
and uses QSPI at 40 MHz writes / 16 MHz reads. It reads both remaining bytes
and experimental FIFO credits and writes no more than the reported credits in
one transaction. It reports ten presentation IDs, 3,456,000 pixel writes, no
modeled drops, FIFO loss or LCD underruns, and 4,252 credit reads. The ten
coordinate dumps are byte-identical to previous outputs checked against the
related C decoder (`jpeg720-ten-hashes.json`). The longest modeled
arrival-to-presentation age is 38.66702 ms; nine output intervals span 307.33531
ms (29.284 fps in this short phase-sensitive window). The extra status reads
cost time: frame 10's synthetic-QSPI upload used 389,590 cycles, or 3.8959 ms
at 100 MHz. All figures are modeled.

`run-jpeg720-ten-verilator.sh` generates the ten fixtures, builds the
experiment, bounds execution and checks every output against the related C
model. The full wrapper was rerun successfully, including ten exact related-C-model
comparisons. The external queue, CRC/setup CPU
time, ESP32 firmware, radio, security, physical QSPI/CDC timing, SDRAM timing,
actual Artix-7 fit and LCD hardware are not modeled or proven. The experimental
status endpoint and sub-burst policy are **not implemented in production**;
this is not a sustained 30 fps result or a deployment recommendation.
