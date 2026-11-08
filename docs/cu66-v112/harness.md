# V112 clocked source adapter and JPEG RTL harness

This is an **explicit deterministic source adapter**, not a synchronized ESP32
firmware execution. The source-side bytes derive from the V111 guest-accepted
fixture: all 28 original event messages are reconstructed and SHA-256 matched
to V111's retained actual guest event audit before scheduling. The new bridge
relabels sequence and frame IDs for ten presentations of **one repeated
720×480 JPEG**, preserving payload and frame CRC. The corruption control
intentionally changes one payload byte. This does not demonstrate ten distinct
encoded images or current Sunshine output.

[Runner](../../scripts/cu66-v112/harness/run.py),
[bench](../../fpga/experiments/cu66-v112-harness/tb_sync_adapter.sv), and
[DPI adapter](../../fpga/experiments/cu66-v112-harness/replay_dpi.cpp) use the
actual existing experimental QSPI endpoint, credit CDC, JPEG decoder, tile
transpose, BL8 memory controller, functional SDRAM, and LCD scanout. There is
no behavioral codec substitution. The DUT is the existing experimental
integration, not a new complete production top or CS88 custom decoder.

The [selected result](../../experiments/python-gamebub-v112/harness/results.json)
binds [attempt 20261108T193646980851Z](../../experiments/python-gamebub-v112/harness/attempts/20261108T193646980851Z/receipt.json),
receipt SHA-256 `05e2ef8ea47a4e63ba6e147e404e1729f9d1bacaf87b3ad695d322ca8d5bd804`.
Its 49 source pins match the current sources and retained snapshots.

| Executed check | Result |
| --- | --- |
| Ten repeated-fixture frame presentations | PASS, 3,456,000 exact decoder pixels and presented SDRAM words |
| Actual QSPI credit reads | 4,340; no transport overflow, extra underrun or dropped frame |
| Scheduled source idle | 6,288,825 core edges yielded; final SDRAM refresh count 54,466 |
| Bounded-source backpressure | PASS, maximum offered-to-accept delay 3,651,950,000 ps |
| Partial frame abort, actual DUT reset, complete retry | PASS, 1,024 bytes discarded, then 345,600 exact pixels presented |
| One corrupted JPEG payload byte | PASS, actual core fault count 1 and zero pixels/publications |
| 1,040-byte record against 1,039-byte cap | PASS, expected process failure before writing bounded storage |
| [Six causal trace rejection controls](../../experiments/python-gamebub-v112/harness/trace-controls/results.json) | PASS; mutated inputs retained |

The ten-frame simulation ended at 414,905,490,000 ps. The run took 100.87 host
seconds; abort/reset/retry took 24.16 seconds and corruption 7.07 seconds.
These host costs are simulator observations, not target performance. The
compile emitted **44 warnings**, including inherited code and new bench
width conversions; all diagnostics are retained.

## Time, ownership, and bounded transport

The Verilator scheduler's **64-bit integer picosecond counter** is the sole
adapter/RTL time authority. The adapter's offered schedule is external source
input. One event (at most 1,039 bytes including its header) may be resident;
the next event is not read before the previous acknowledgement. The schedule
file is consumed incrementally, with no full-event array loaded into the
bridge. Oversized records are rejected before writing that bounded storage.
C library file buffering is host input I/O, not an emulated firmware FIFO.

An early offered deadline means the source is blocked until the prior event
finishes; no unseen queue of elapsed arrivals is claimed. The JSONL trace
records offered deadline, actual acceptance, completion, service duration,
source backpressure, capacity and highwater for every event.
A separate forced RTL FIFO-credit-exhaustion scenario is not claimed. These are
synthetic offered deadlines, not host capture/encode timestamps. The source
is released at 25 ms initially and at a configured 40 ms separation per
repeated frame. Those assumptions are not measured system throughput.

The adapter never waits on a socket. A not-yet-due source event makes the
bench yield to the next core-clock edge. Core/memory run at 100 MHz, QSPI
service at 200 MHz, and pixel clock has the existing exact 17,029 ps half
period. SDRAM read phase, refresh, LCD line requests and frame boundaries
continue during source idle and while publication waits. These are simulation
clock assumptions, not new routed clock qualifications.

Actual QSPI pins carry register headers, data and responses. DATA service
reads the actual remaining-byte count and FIFO credit, and bounds each write
by returned credit. COMMIT waits for actual core publication and reads the
presented-frame ID. ABORT writes the real control register and reads ready status/drop count and checks idle,
zero partial publication, no pixels/writes and the actual drop counter. The
DPI acknowledgement records the bench's completed validation; it is not a
guest SPI completion IRQ or fabricated hardware protocol response.

Each normal frame checks all 345,600 decoder pixels against a freshly compiled
fixed-color C JPEG model, unique coordinates, exact pixel/write/burst
conservation, and all 345,600 presented SDRAM words against the same oracle.
The C model is algorithmically related to the JPEG RTL: it supplies an external
reference for this integration, not independent codec conformance. LCD
underrun, transport overflow and core fault/drop counters remain checked.
The memory frame is verified at publication; this is not a pixel-by-pixel
comparison of an entire subsequent LCD scan.

## Reproduction and evidence

Run from the repository:

```sh
python3 scripts/cu66-v112/harness/run.py
python3 scripts/cu66-v112/harness/audit_controls.py
```

The runner creates a new immutable source snapshot and source-hash manifest,
compiles RTL and the C reference fresh, and retains logs, explicit offered
schedule bytes, event hashes, causal traces and a receipt under
`experiments/python-gamebub-v112/harness/attempts/`. External binaries and
large reference data stay in the recorded build directory. Runs are serialized
inside Docker with two CPUs, 8 GiB memory equal to memory+swap, no additional
swap, no network, and command watchdogs. The legacy builder retains
`-Wno-fatal`; warning counts are recorded and this is not the stricter
warning-free component qualification.

The first attempt `20261108T193144067344Z` is retained **FAIL**. Its SystemVerilog
real-to-integer time conversion overflowed; the monotonic completion assertion
stopped the run before any frame committed. The corrected adapter reads the
simulator's full 64-bit integer context time directly. No DUT or oracle was
changed to resolve that failure. The prior passing attempt
`20261108T193232891986Z` remains retained; the selected final run removes
unused inherited declarations and adds actual QSPI abort-status/drop readback.

## Remaining fidelity gaps

No ESP32 guest executes in this new replay. Guest instruction/cycle time is
absent, not calibrated or synchronized; there are no actual GP-SPI registers,
DMA descriptors, completion interrupts, Wi-Fi service, or full production app
startup. V111's previous guest execution remains separate historical evidence.
The new deterministic adapter solves the old frozen-RTL socket wait only for
its own source/RTL path. Actual guest/RTL time coordination, successful full
app boot and GP-SPI/DMA, production memory accounting, native Sunshine
integration, distinct-frame traffic, 60/600-second campaigns, full-parent fit,
125-MHz timing and hardware validation remain open. Do not infer FPS, target
CPU utilization, RF service or input-to-display latency from these runs.
