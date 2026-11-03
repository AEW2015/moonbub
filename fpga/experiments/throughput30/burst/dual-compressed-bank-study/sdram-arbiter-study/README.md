# Synthetic four-client SDRAM arbitration experiment

This **isolated command-level simulation** explores adding JPEG staging to the
existing experimental BL8 SDRAM controller. It is not production RTL, a real
LCD/decoder/ESP32 integration, an SDRAM timing model, target implementation or
hardware test. It does not prove 30 fps or general scanout deadlines. The
related [address and average-bandwidth model](../sdram-storage-model/README.md)
motivated this bounded contention test.

`staging_arbiter.sv` accepts four synchronous, eight-word-aligned BL8 clients:
display read, decoded-pixel write, compressed-frame write and compressed-frame
read. Display has strict priority when a new command can start; the other three
use round-robin selection. A command already in flight is not preempted. Only
one read is outstanding, and its eight response beats route to the selected
read client before another request is granted. Both read sinks must always be
ready; there is **no response backpressure, FIFO, CDC, runtime reordering,
transaction generation, abort or write-drain ACK** in this prototype. An
unaligned selected request or response without an owner raises a sticky fault.
The arbiter does not check that a client's address lies inside its assigned
range; range and ownership enforcement must precede any integration.
Sustained display requests can starve every background client; round-robin does
not establish a bounded fairness guarantee against the priority client.

The test instantiates the existing `moonshine_sdram_burst` and the related
`sdram_model_burst_verilator`. The latter is a bounded behavioral model, not an
independent vendor timing model. It uses the existing model's 1,048,576 16-bit
word array, representative simulated clock/data delays, CAS latency and
refresh checks. The bench preinitializes the displayed and JPEG-read regions;
this models neither frame construction nor initialization on the real board.

## Bounded test and result

The synthetic display producer issues 60 BL8 reads for each of 24 sequential
480-word lines. A new line is scheduled every **1,843 core-clock cycles**, and
all 480 words must return before the next synthetic deadline, including for
the last line. The baseline project's 100 MHz/29.361979 MHz clocks and 541
pixel clocks per raster line correspond arithmetically to about **1,842.52 core
cycles per line**; the test rounds up by about 0.48 cycle each line. It is a
simple periodic producer and deadline, not `moonshine_lcd`'s actual two-line
prefetch, blanking, FIFO, frame ownership or CDC behavior.

Three always-ready synthetic background producers concurrently request 200 BL8
pixel writes, 200 compressed writes and 200 compressed reads, to disjoint
word ranges corresponding to framebuffer 1 and the candidate JPEG bank gaps.
Each compressed direction is only 3,200 bytes in this test: it is not a full
JPEG or a representative sustained 30 fps workload. Display and compressed
read data are compared word-for-word against deterministic preinitialized
patterns. All written words and the guard words adjoining both output ranges
are checked after the controller drains.

The recorded test passed with:

* **24 / 24** synthetic lines completed, **11,520** checked display words;
  worst line completion was **1,025 cycles** against the 1,843-cycle synthetic
  deadline in this one workload.
* All 200 requests per background client completed, with **1,600** compressed
  read words checked and **3,200** written words checked across the two write
  clients. All four neighboring guard words remained intact.
* The bench observed **15,895 cycles** with the display and at least one
  background client simultaneously requesting service; it asserts no lower
  priority client is granted while display is requesting. The functional memory
  model recorded **58 refresh commands**, including initialization refreshes.

This shows the measured priorities, data routing and limited deadlines only for
the modeled addresses, request pattern, phase and always-ready sinks. It does
not establish general starvation bounds, backpressure safety, physical
electrical operation or sustained video throughput. In particular it does not
test changing JPEG lengths, CRC/commit, simultaneous frame swaps, overflow,
recovery, display-line FIFO underflow or actual Sunshine packet timing.

## Verification and reproduction

Three deliberately unfavorable controls must fail at their specific checks:

* Reducing the synthetic line period to **850 cycles** triggers the display
  deadline assertion.
* Flipping one compressed-write payload bit triggers the memory-data check.
* Misaligning one compressed write request triggers the sticky protocol fault.

The normal and expected-failure logs, source hashes, tool versions and generic
Yosys elaboration/check log are in `results/`. The Yosys check is not FPGA
technology mapping or timing. Set `BUILD_DIR` to a new empty scratch directory
and run `./run.sh` with Verilator 5.x, C++ and optional Yosys; the script
validates pinned source hashes, compiles/runs all four cases, and checks the
specific negative outcomes. The full recorded output is
`/home/lori/gamebub-tools/staging-arbiter-wrapper-v1/`.

Further work must connect the actual LCD line-fetch and decoder/transpose
interfaces, model bounded ingress/decoder queues and response backpressure,
establish transaction identity and physical drain on abort/reset, use
representative JPEG/video traces, and verify fitted SDRAM geometry, timing and
actual target FPGA implementation. A fuller integrated simulation must test
deadline and data integrity across clock phases, row conflicts and refresh;
hardware instrumentation remains necessary.
