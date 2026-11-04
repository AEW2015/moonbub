# ESP32 gateway: firmware facts and bounded packet sensitivity

This study adds **ESP32-specific bounds** missing from the generic link budget.
It extracts checked-in firmware/build settings and runs a packet-level Python
sensitivity model. It is not ESP32 instruction emulation, Renode, a firmware
execution trace or Wi-Fi/QSPI hardware qualification.

## Source facts, not assumed performance

`facts.py` checks the Rust source, sdkconfig defaults, retained compiled header,
FPGA SPI driver, firmware README and build manifest. The retained facts are:

| Checked firmware/build setting | Value |
| --- | --- |
| Configured CPU clock | 240 MHz |
| External PSRAM enabled | No; no PSRAM assumed |
| Accepted transport/video | Strictly ordered MSV1, JPEG only |
| Payload/header bytes | 1,024 / 40 |
| Internal DMA working allocation | 1,065 bytes, one packet |
| Streaming/main stack reservations | 16,384 / 20,480 bytes |
| lwIP UDP receive mailbox | Six datagrams |
| Wi-Fi static/dynamic RX buffer counts | 10 / 32 |
| CRC32 source loop | Eight bitwise steps per payload byte |
| QSPI write/read clock caps | 40 MHz / 16 MHz |
| Shared Device access | Try-lock; busy access drops frame |
| Abort retry loop | Up to about 100 ms, 1 ms sleep between failed accesses |

The source supports **neither AR02 nor GF02**. Its two-command worker queue is
not two ESP reassembly frames. The two ingress slots in the codec studies belong
to a hypothetical FPGA/receiver path, not ESP heap. No full compressed or decoded
frame is allocated on ESP by this streaming worker. Its register `0x0c` gives
bytes remaining in the current frame, **not free FIFO entries**. That check does
not guarantee FIFO safety. The retained build manifest says incomplete because
hardware execution has not occurred. SoC PSRAM capability macros are not an
external-memory enable or proof of a fitted/available PSRAM device.

## What the model assumes

Four workloads comprise three actual admitted v16 AR02 frame **size** profiles
and an explicit cap stress workload of sixty hypothetical maximum-size
49,152-byte frames. These bytes are split using MSV1-shaped 1,024-byte payloads,
40-byte headers and 28 IPv4/UDP bytes. This framing is a port-design sensitivity,
not packets the installed firmware will accept or a GF02 packet-size claim.
Original capture IDs and holes are retained: the three regression windows each
span 180 capture IDs/six seconds, but have 177/160/163 admitted packets/frames.
They are rescheduled from source IDs at 30 Hz, not their actual encoder-completion
times. This is **not a joint codec+ESP+FPGA simulation** and cannot add its results
to the finite codec FPS. Native sources were already precompressed/offline.

One serialized gateway task receives a datagram into one working DMA buffer,
pays CRC/copy/parse CPU work, polls identity/credit, and blocks during SPI service.
Six mailbox entries queue separately from that in-flight working packet; driver,
Wi-Fi and lwIP buffer allocations remain outside the mailbox. Packets can arrive
in deterministic bursts after assumed link serialization. No PHY/MAC contention,
retransmission, TCP/IP ISR, cache or dual-core scheduling is emulated.

Unmeasured cycle costs are explicit parameters. Nominal grants 60% of one 240 MHz
CPU, five cycles per CRC bit-step, two copies at two cycles/byte and 2,000 fixed
cycles/packet; optimistic uses 80%, three cycles/bit-step, 500 fixed cycles and
smaller driver/poll costs; conservative uses 35%, ten cycles/bit-step and 4,000
fixed cycles. These are not benchmarks of Xtensa instructions or IDF/lwIP.
Wi-Fi/UI contention is represented only by that CPU share plus periodic lock
busy intervals; it does not establish real task placement or responsiveness.

SPI wire counts follow the source driver's command/address/dummy/data phases:
read-u32 uses 8 single-line command clocks plus 8+16+8 quad clocks; payload write
uses 8+8+2×payload clocks. Three reads approximate normal identity+credit polling.
Frame begin adds four reads/five writes and commit two reads/one write. Driver
call latency, jitter, those control paths and blocking behavior are modeled
approximations; 40/16 MHz are caps, not measured actual selected clocks/goodput.
CRC work is conservatively charged even on some sequence-invalid packets that
Rust rejects earlier; invalid-path costs are not exact firmware execution.

Abort recovery is separately charged: zero assumed wait optimistically, 1 ms
nominally and a 100 ms sensitivity case, plus approximate identity/control SPI
service. The 100 ms source bound does not mean every abort waits 100 ms. Sustained
lock ownership and retry wakeups require measurement. An unfinished prior frame
also incurs abort work on replacement. The initial regression fixture failed to
hit its intended lock interval; `failed-initial-tests.log` retains that failed
setup. Final guards separately check that a fresh begin lock failure charges no
abort, and that a mid-frame forward failure charges recovery and can overflow
the mailbox. All eleven tests pass.

A configurable hypothetical FPGA FIFO drains at an assumed byte rate. The
current-credit case detects/drops overflowing chunks **in the model**; this is
not an installed firmware overflow fix or behaviorally exact FPGA simulation.
A separate bounded-wait case assumes a new true-FIFO-credit/backpressure contract;
it blocks the gateway and can overflow the UDP mailbox upstream. A whole chunk
is conservatively reserved at a transfer boundary; actual word/clock CDC service
is not modeled. Abort does not secretly erase the modeled FIFO. AR02 reference
feedback, decode/publication dependencies and display are outside this gateway.
Begin and forward lock failures are distinct: failed fresh begin never marks the
FPGA transfer active or charges its abort. Transport queue/worker drain is not
full protocol drain. `active_incomplete_frame_at_end` is retained separately; the
firmware's **500 ms idle-frame timeout** and its final abort are not simulated.

## Retained results

There are 32 principal workload/scenario cases, a 20-case link/burst sweep,
three RAM-reservation scenarios and 13 source hashes. These are deterministic
assumption sweeps, not newly measured target service. `verify.py` reruns every
principal scenario and checks conservation, queue bounds and source facts.

| Initial-only actual-size workload | Strict / eventual gateway frames, of 177 admitted | Mailbox drops |
| --- | ---: | ---: |
| Nominal paced 8 Mb/s | 176 / 177 | 0 |
| Conservative CPU/service | 69 / 69 | 379 |
| Nominal, nearly simultaneous bursts of eight | 0 / 0 | 460 |
| Nominal, 0.5 ms periodic device-lock busy | 156 / 157 | 0 |
| Same lock pattern, 100 ms abort wait sensitivity | 97 / 98 | 1,484 |

The nominal initial-only window needs **6.019856 Mb/s** IPv4/UDP service on average.
Its maximum gateway completion age is 43.547 ms; all admitted frames eventually
complete, but this is not all 180 original captures and not decoded/displayed FPS.
The no-contention mean packet-service payload ceiling is 17.123 Mb/s under these
CPU/SPI assumptions, excluding per-frame begin/commit and failure recovery; it is
an upper bound, not sustainable RF/firmware goodput. The raw quad payload rate is
160 Mb/s, which omits CRC, copies, polling, transaction overhead and CPU contention.

At assumed 4 Mb/s, the same 177 frames eventually pass with zero mailbox loss but
age exceeds three seconds. That cannot sustain the six-second input schedule
for interactive play. Eight- or twelve-packet near-instant delivery bursts
exceed the six queued plus one working packet bound and lose frames even at
higher average link rates. More advertised PHY rate does not fix burst tolerance.
With a slow 400 kB/s FPGA drain, both current-credit and hypothetical bounded-wait
cases fail all frames: the first exposes modeled FIFO overflow, while the latter
moves stalls upstream and loses UDP data. Backpressure must cover the whole path.

The cap stress requires **12.57984 Mb/s** IPv4/UDP service at 30 Hz. At nominal
8 Mb/s it completes only 38/60 within the two-second capture horizon; all sixty
finish during drain with maximum age 1,178.845 ms. Eventual delivery is not 30 fps
sustainability. Complete/strict counts and drain time are retained separately.

## RAM and qualification gates

The illustrative reserve sums to **275,545 bytes**: stream/main stacks, one DMA
packet, assumed 1,600-byte Wi-Fi buffers at configured static/dynamic maxima,
six mailbox payload reserves, descriptors, a 96 KiB UI reserve and 64 KiB other
runtime reserve. Against assumed available internal budgets 256/320/384 KiB,
margins are −13,401 / 52,135 / 117,671 bytes. None is a measured free-heap value.
Wi-Fi/lwIP/mailbox payloads may alias; independently reserving them can double
count. Buffer sizes, task/runtime heap and UI reservations are assumptions, not
an exact ESP-IDF allocation map. No 512 KiB all-free pool or PSRAM is credited.

A positive total margin cannot establish an internal DMA-capable contiguous
1,065-byte allocation, fragmentation or largest-free-block availability. The RAM
model checks an assumed largest block separately and always leaves `fit_proven`
false. Measure free/internal/DMA heap, minimum watermark, largest block and worker
stack high-water marks with Wi-Fi, Slint/UI, input and SPI active concurrently.

Next instrument packet-service distributions and CRC cycles on the actual build,
mailbox/pbuf drops, lock/abort durations, DMA issue/completion, true FIFO occupancy
and overflow counters. Negotiate/implement AR02/GF02 forwarding separately, pace
host bursts to bounded receiver capacity, and replace remaining-frame credit with
an actual safe FIFO/drain contract. Then combine measured ESP traces with codec
capture/admission and FPGA memory/decode/scanout models before a full 30 fps claim.

```sh
python -m unittest -v test_gateway.py
python verify.py
python benchmark.py    # regenerates deterministic assumption evidence
```

Only Python files/evidence in this new study were added; firmware is unchanged.
