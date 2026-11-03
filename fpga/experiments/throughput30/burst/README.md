# Isolated SDR SDRAM burst-write experiment

This is an unintegrated research candidate. It does not change the production
controller or bitstream, prove 30 fps, validate physical SDRAM timing, or
establish that the design fits or meets timing on Game Bub hardware.

`moonshine_sdram_burst.sv` is derived from the existing controller. Its write
request carries eight 16-bit words packed least-significant word first. It
selects sequential BL8, CAS 3, programmed write bursts via mode `0x033`, and
drives eight write beats before write recovery and the next request. The
requester **must** supply an eight-word-aligned address and the entire stable
payload at handshake. The candidate does not yet enforce alignment, support
partial or masked bursts, have an input FIFO, expose fault/abort semantics, or
integrate the pixel transpose and line-scan arbiter. Do not use it in hardware.
The candidate's mode-register value, command/data alignment, tWR, tRFC,
refresh budget and all other timing must be checked against the actual fitted
SDRAM datasheet and constraints.

`sdram_model_burst.sv` extends the repository's simplified functional model to
record eight sequential words per write command and checks alignment, bank
activation and basic command conditions. It is **not an independent vendor
model or electrical/timing signoff**. The bench sends 1,200 aligned bursts in
a deterministic permutation over 9,600 addresses, checks every resulting
word, then reads 40 eight-word bursts through the controller read path and
compares each word. It exercises row transitions and frequent refreshes; all
addresses use bank 0, so bank switching is not covered. The bench does not
exercise LCD scanout, partial/unaligned bursts, abort, stalled input payload,
real clock-domain crossings or write/read turnaround at the full integration
boundary. The functional model does not fully check SDRAM burst and timing
specifications. Verilator is 2-state; XSim provides a separate 4-state check.

Observed bounded self-checking behavioral runs:

- Verilator 5.020: `TEST_PASS_BURST writes=9600 bursts=1200 refreshes=305`.
- Vivado XSim 2025.2: same result with generic `xck24` project part (the
  installed tool lacks the actual Artix-7 part). Not place/route evidence.

Reproduce Verilator with `./run-verilator.sh` and Verilator 5.x, GNU timeout,
make and C++ compiler installed. Pass a directory via `BUILD_DIR` if desired.
XSim should compile these three files with `SIMULATION` defined and top
`tb_sdram_burst`, with a 10 ms simulation-time watchdog. PASS requires the
terminal marker and no errors, fatals or timeout. Logs are alongside sources.

Next integrate aligned tile groups and arbitration, verify faults/abort and
row/bank/refresh/read-write corner cases against a datasheet-based memory
model, then run sustained frame traces with actual concurrent LCD scanout.
Report write latency and every displayed frame ID; only then can this candidate
be assessed against the 33.33 ms budget. Finally evaluate the real FPGA device
and timing before any hardware test.

## Full-frame burst candidate with concurrent LCD fetch

`moonshine_memory_burst.sv` is a **test-only** collector and arbiter. It
collects aligned 8-word runs emitted by the actual tile transpose and gives
LCD line reads priority over starting a write. It latches a protocol fault for
misaligned or noncontiguous input and reports non-idle until its collected
burst drains. This is a research wrapper, not the production memory controller.

`tb_burst_memory_throughput.sv` uses the real tile transpose and LCD RTL, the
new candidate writer/arbiter and the functional SDRAM model. It preinitializes
the fixed front buffer, warms LCD fetch for 2,000,000 cycles, then feeds the
same 345,600-pixel decoded fixture as fast as accepted. It poisons and verifies
every back-buffer pixel and counts physical model write beats and LCD
underruns. At 100 MHz memory and ~29.362 MHz pixel clock:

| Simulation | Write cycles | Write time | Checked pixels | Modeled underruns |
| --- | ---: | ---: | ---: | ---: |
| XSim, original test clock/model | 2,165,697 | 21.65697 ms | 345,600 | 0 |
| XSim, verification-only clock workaround | 2,165,697 | 21.65697 ms | 345,600 | 0 |
| Verilator 5.020, same workaround | 2,165,697 | 21.65697 ms | 345,600 | 0 |

The nominal 33.333 ms/frame memory budget is met in **this one-frame test**;
46.17/s is only the reciprocal of write-service time, not displayed FPS. Only
one LCD boundary occurred in the timed part. The front image remains fixed;
JPEG decode, ingress and frame swaps are omitted. This result cannot establish
continuous streaming, actual display output, multi-frame buffer ownership,
physical SDRAM timing or Artix-7 fit. The other functional-model limitations
and unsupported reset/partial writes described above still apply.

`tb_burst_memory_throughput_verilator.sv` and
`sdram_model_burst_verilator.sv` are verification-only variants of the same
bench/model. They express delayed simulation clocks as event-triggered
nonblocking assignments to avoid a Verilator 5.020 delayed-continuous-assign
scheduler problem; neither changes the candidate DUT. The matching XSim
original/workaround results provide a cross-check for this one workload, not
proof of general 2-state/4-state equivalence. Logs are
`memory-xsim-original.log`, `memory-xsim-workaround.log` and
`memory-verilator.log`. Run `./run-memory-verilator.sh` with Verilator 5.x,
make, C++ and GNU timeout installed; it locates the repository's fixture and
sets a 180-second wall-clock bound. Optional plusargs such as
`+PIXELS=64 +WARMUP_CYCLES=1000` can shorten a diagnostic run but are not the
reported full-frame result. XSim can use the original testbench and model (or
the workaround pair), `SIMULATION`, the existing LCD and tile RTL, the two
candidate RTL modules, `+TRACE_FILE=<path-to-decoded-rgb565.txt>`, a bounded
500 ms simulation-time watchdog, and the `tb_burst_memory_throughput` top.

## Real JPEG, burst writer and LCD integration

`tb_jpeg64_burst.sv` and `tb_jpeg720_burst.sv` are isolated single-frame
integration tests. The actual `moonshine_core` receives one checked-in JPEG
through its register interface, decodes it using the checked-in JPEG RTL and
feeds the experimental tile/BL8 path while the actual LCD module scans the
initialized front buffer. Core `memory_idle` is gated on both the tile buffer
and the burst/memory stages being empty so a frame is not published before the
last buffered pixels drain. The test checks one actual front-buffer ownership
transition, presented ID, zero new modeled scanout underruns, expected burst
and write totals, every unique decoder coordinate, and the entire back-buffer
image against accepted decoder pixels. It uses the verification-only clock
workaround model described above. This setup is **not production integration**:
the tile abort is tied inactive, so reset/abort/error handling and recovery
across a partially collected frame have not been designed or verified.

Both Verilator 5.020 and XSim 2025.2 passed the same benches, with exact
cycle counts and byte-identical coordinate-tagged RGB565 outputs across
simulators:

| Input | Pixels | Write bursts | Decode-to-presentation | New modeled underruns |
| --- | ---: | ---: | ---: | ---: |
| `fpga/sim/pipeline64-420.jpg`, 64×64 | 4,096 | 512 | 1,051,533 cycles = 10.51533 ms | 0 |
| `host/fixtures/pattern-720x480-420-q65.jpg`, 720×480 | 345,600 | 43,200 | 2,537,677 cycles = 25.37677 ms | 0 |

The 100 MHz measurement begins when the **already-uploaded compressed frame**
is committed for decoding and ends at its actual LCD frame-boundary swap. It
includes this run's swap wait and excludes JPEG capture/encoding, network,
QSPI/ESP32, compressed-frame upload and any subsequent frame. The LCD is fed
from a fixed initialized front buffer until that swap. Thus a single frame
under budget is promising evidence for this configuration, **not a sustained
30 displayed fps result**, nor a latency or hardware timing guarantee. The
full-resolution fixture is a synthetic pattern, not representative gameplay.

The output dump matches the fixed-color C model for the JPEG core at every
pixel in both tests (4,096/4,096 and 345,600/345,600). This is a
**shared-algorithm** reference rather than an independent implementation. A
separate Pillow RGB decode yielded 1,593/4,096 exact RGB565 pixels with maximum
component difference 2 quantized units for 64×64; for the 720×480 input it
produced 224,931/345,600 exact pixels and a maximum component difference of
15 quantized units. The full error histograms are in the `*-pillow-compare.json`
files. These differences require interpretation and visual-quality review;
the C-model match is not proof of exact agreement with an independent decoder.

Use `./run-jpeg64-verilator.sh` or `./run-jpeg720-verilator.sh`; each requires
Verilator 5.x, make, C++, GNU timeout and Python with Pillow, accepts an optional
`BUILD_DIR` and runs a shared-algorithm exact C-model check plus an independent
Pillow comparison. The two corresponding `jpeg*-verilator.log` and
`jpeg*-xsim.log` transcripts capture the observed test markers. XSim projects
used `SIMULATION`, the verification-only SDRAM model, the actual JPEG core
sources, a bounded simulation watchdog, and the appropriate `tb_jpeg*_burst`
top. The 64×64 and 720×480 fixtures SHA-256 are respectively
`d66a628c9f58872d1e39c7730602bf83f3e2af71d538ad83439b9e9905ca71af` and
`8cc99ea7d50d1d20255e41ff7247b0770b3349e705c27152a41817418ce5c9de`.

Next, implement and verify safe abort/overflow/reset handling across all
buffered stages and test sustained **distinct** frames at a controlled cadence,
including real ingress/receiver timing, swaps, content checks and a vendor
SDRAM timing model. Obtain actual Artix-7 synthesis, constraints and timing
before any hardware use. Do not interpret the present one-frame PASS as that
next gate.

## Ten-frame 30 Hz study and decoder fault

A deterministic generator creates ten **distinct synthetic**, 720×480 4:2:0
JPEGs at q65; they are not gameplay. The manifest records all SHA-256 hashes
and sizes; these ten frames are 26,159–27,300 bytes. The FPGA testbenches
feed them at 30 Hz in simulated time, count actual LCD frame-boundary swaps
and validate all decoded pixel addresses and all SDRAM words. These are short
functional experiments, not evidence for sustained 60-second performance.

- **Stock core, strict unbuffered arrival:** three frames presented; at the
  fourth 30 Hz arrival the core remained pending. Frame 3 arrived at cycle
  8,686,703 but was presented at 12,293,425; frame 4 was due at 12,020,037.
  The test failed rather than silently delaying that arrival. See
  `ten-frame-strict-stock-fail.log`.
- **Stock core plus hypothetical one-frame external queue:** the first six
  frames presented, but frame 7 faulted in the JPEG core. The burst staging
  fault and modeled LCD-underrun counters remained zero; see
  `ten-frame-queue1-stock-fail.log`.
- **Experimental guarded JPEG parser plus that hypothetical queue:** ten
  frames entered at 30 Hz and ten unique IDs were presented; 3,456,000 pixels
  and SDRAM words were checked, with no model-reported queue overflow, core
  drop/overflow or LCD underrun. First and last presentation were 30,733,531
  cycles apart: **29.284 displayed frames/s over the nine measured intervals**,
  not 30 fps. Maximum modeled arrival-to-presentation age was 3,606,722 cycles
  (36.06722 ms). XSim reproduced the same frame IDs and timing; all ten
  output dumps match byte-for-byte between XSim and Verilator. Results:
  `ten-frame-queue1-guarded-verilator.log`, `ten-frame-queue1-guarded-xsim.log`
  and `ten-frame-cross-simulator-dump-hashes.json`.

The queue exists **only in the testbench**. It assumes an entire JPEG is
instantly available at each scheduled arrival and retains at most one frame
identity while the core is busy. Its byte capacity, receiver RAM use, CPU
CRC time, packetization, Wi-Fi, QSPI, actual backpressure and security are
not simulated. The register bus then uploads one byte in two modeled 100 MHz
cycles with no QSPI or CPU overhead. Frame waiting time is included in the
reported arrival-to-presentation age; the test does not prove the ESP32 can
supply this rate. It also omits audio/input, physical SDRAM timing, implementation
fit and other error recovery. The short synthetic run's PASS marker means its
internal assertions passed, **not that the 30 displayed fps target is met**.

### Stale marker diagnosis and isolated candidate

Fixture `0006.jpg`, SHA-256
`013dc842ef06b249da968c009c57bff4905728d40c6166f22147302a37af6e38`,
reproduces the failure even as the first and only frame. At cycle 3,109,390,
JPEG input is in entropy state 14 with `valid=0`, `accept=0`, `byte_idx=0`,
`last_b=ff`, `data_r=c0` and stale word `ff1465c0`. An ungated SOF0 token
clears width and height despite no accepted byte. The actual bytes at offsets
`0x2134..0x2139` are `c0 65 14 ff 00 26`: `ff 00` is legal entropy byte
stuffing; this location is not an SOF marker. The core then rejected a decoder
pixel because the dimensions had become zero after 170,176 accepted pixels.
The decoder watchdog was only 1,035,630 of its 50,000,000 cycle limit. The
complete diagnostic is in `frame6-stock-diagnostic-fail.log`.

`jpeg_input_guarded.v` is an **experimental copy**, not a modification of the
production decoder. It qualifies the SOF0 state transition and eleven header
metadata reset sites on a valid, accepted SOF0 in header state. A directed test
with fixture 0006 observes the stale token twice and checks that the header
metadata remains unchanged; it completes the whole frame in both XSim and
Verilator. Their decoded pixel dumps are byte-identical and match the related
fixed-color C model exactly. `frame6-guarded-directed-{verilator,xsim}.log`
records the runs. Other tokens—including SOI/EOI state/end side effects—are
not fully audited by this narrow change; it must not be treated as a complete
JPEG parser fix or deployed without further review and regression.

All ten guarded-queue output dumps matched the related shared-algorithm C model
exactly for all 345,600 pixels per frame. These checks are not independent
implementations. Independent Pillow comparisons and their full error
histograms are recorded in `jpeg720-queue1-guard-comparisons.json`; every frame
has a worst component difference of 15 quantized units in that comparison.
No subjective-quality threshold has been approved.

Reproduce with `./run-directed-guard-verilator.sh` and
`MODE=queue1 JPEG_DECODER=guarded ./run-ten-frames-verilator.sh`; both require
Verilator 5.x, a C++ compiler, make, GNU timeout and Python with Pillow. They
generate new fixtures under `BUILD_DIR` and refuse to overwrite an existing
fixture directory. `MODE=strict JPEG_DECODER=stock` reproduces the unbuffered
failure; `MODE=queue1 JPEG_DECODER=stock` reproduces the stock decoder fault.
Both expected-failure runs return nonzero. The scripts set `ulimit -c 0` and
bound wall-clock runtime. The guard, queue, burst write controller and tile
arbiter are all research artifacts; production RTL has not been changed.
