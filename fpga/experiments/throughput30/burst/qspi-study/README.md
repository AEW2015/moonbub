# QSPI frame-sized payload component test

This standalone digital test drives the existing `moonshine_qspi_endpoint`
and `moonshine_bus_cdc` at their actual modeled pin interfaces. It sends
26,159 ordered payload bytes (the size of the checked-in q65 fixture) in 26
chunks, issuing a modeled register read before each chunk, plus one final
count read. It uses 40 MHz four-lane writes, 16 MHz four-lane reads, a 200 MHz
endpoint clock and 100 MHz core clock. A synthetic core counts and checks
every received byte and models register `0x0c` as remaining frame bytes.
The endpoint and CDC are real RTL; the synthetic core is not the real JPEG
core and no compressed JPEG is decoded here.

Four start phases at 0, 1.25, 2.5 and 3.75 ns pass in Verilator 5.020: all
26,159 bytes arrive in order, the CDC overflow flag remains clear, and the
measured simulated interval from the first per-chunk read through the final
count read is 1.39645 ms. A read uses the endpoint's 64 dummy bits. Clock
setup and modeled task overhead are in this interval. The result is a
component-level functional simulation with ideal pin timing; it does not
include ESP32 execution, CPU CRC, mutex scheduling, real DMA, Wi-Fi, other
peripherals, signal integrity, timing closure, actual firmware register
execution or real-device measurements. The count returned by 0x0c is NOT
FIFO credit. Four phases are a small sample and do not establish all CDC or
physical clock phase/timing behavior.

Reproduce with Verilator 5.x, make, C++, GNU timeout:

```sh
fpga/experiments/throughput30/burst/qspi-study/run-verilator.sh
```

The runner compiles in a new temporary directory by default, runs all four
phases with bounded wall time and requires the terminal PASS marker.
`verilator.log` contains the recorded outputs. This test does not prove the
full continuous video path or 30 fps.

## Single full-resolution JPEG through QSPI, decoder and LCD

A separate testbench connects the actual modeled QSPI endpoint and CDC bridge
to the actual JPEG core and the isolated burst/tile candidate, functional
SDRAM and active LCD. It uses the existing SOF-only research guard and a
single checked-in q65 JPEG. Metadata and payload pass over QSPI using 40 MHz
writes in 26 chunks, with a 16 MHz read of remaining frame bytes before every
chunk. A counter and actual core receive-length read check the data path; the
CDC's lost-word counter is synchronized as in the top-level RTL. It verifies
345,600 unique decoder coordinates and SDRAM words, 43,200 write bursts, one
actual presentation ID, zero new modeled LCD underruns and zero CDC loss.

Verilator 5.020 reports 140,045 core cycles (1.40045 ms) from starting the
metadata writes to issuing the COMMIT transaction, and 2,449,960 cycles
(24.49960 ms) from that point to presentation at 100 MHz. The latter includes
COMMIT's own QSPI transaction and display-boundary wait. These intervals are
measured at the testbench, not end-to-end game latency. The RGB565 coordinate
dump is SHA-256 `c087e502623218aa8be0669aab3e634d9b6d22fff6b59bfceee8f5c8322de3f0`,
identical to the earlier 720×480 run checked against the related fixed-color
C decoder. The runner rebuilds the C model and checks every pixel exactly;
this model shares upstream JPEG algorithms and is not an independent design.
The Pillow quality differences described in the other studies remain.

Reproduce with Verilator 5.x, make, C++, GNU timeout and Python/Pillow:

```sh
fpga/experiments/throughput30/burst/qspi-study/run-jpeg720-verilator.sh
```

This one-frame behavioral experiment models FPGA pins and finite QSPI bit
clocks, but not actual ESP32 code, capture, network, host/firmware scheduling,
CRC calculation cost, DMA setup, multi-frame contention, packet loss, display
signal integrity, SDRAM timing signoff, or Artix-7 place/route. The metadata
read returned by `0x0c` remains frame bytes remaining, not FIFO capacity; no
new credit scheme is claimed. No physical hardware was programmed. A single
success does not prove sustained 30 fps.

As a **simulation stress experiment only**, the same test also completed at
50, approximately 60 and 80 MHz QSPI write clocks at those four phase offsets;
the read clock remains 16 MHz. The 80 MHz case took 0.737275 ms for the same
modeled payload and read transactions. See `frequency-sweep-verilator.log`
and reproduce with `run-frequency-sweep.sh`. These are ideal digital signals
with one fixed 200 MHz sampling clock and do not establish physical timing,
metastability margin, SPI-driver operation, all phase offsets or actual device
capability. The currently documented firmware write cap remains 40 MHz; no
faster operating rate is recommended or enabled by this experiment.

## Ten-frame QSPI integration experiment

A separate Verilator 5.020 bench connects QSPI and the CDC bridge to the
experimental burst/LCD pipeline and the later isolated EOI guard. It schedules
ten distinct generated 720×480 JPEGs at rational 30 Hz, each instantly present
in an abstract one-frame upstream queue. Each frame is uploaded via modeled
40 MHz QSPI in 1,024-byte chunks with a 16 MHz 0x0c read per chunk. It checks
all 3,456,000 decoder/SDRAM pixel words, ordered presentation IDs, lost-word
counter, no reported decoder drops, queue overflow or LCD underruns. The ten
outputs are byte-identical to the earlier related-C-model-checked frames;
`jpeg720-ten-hashes.json` records hashes. First-to-last presentation spans
307.33531 ms over nine intervals, or 29.284 fps for this short, phase-sensitive
window; maximum arrival-to-presentation age is 36.06722 ms. Upload intervals
are about 1.4 ms per frame for this ideal digital QSPI driver.

Run `run-jpeg720-ten-verilator.sh` to generate inputs, run a bounded test and
compare all outputs to the related C model. There is no Wi-Fi, actual ESP32,
CPU processing, DMA-driver scheduling or modeled receiver memory allocation;
the external buffer does not exist in production firmware. The QSPI parser is
the actual RTL, but the source directly follows its pin protocol. Ten frames do
not establish sustained FPS, physical timing, or a stable hardware service.
