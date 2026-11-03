# Packet-level transport and queue study

This is a **software event model**, not an ESP32 run, FPGA simulation, Wi-Fi
measurement or proof of 30 fps. It extends the prior fixed-rate RTL experiment
with the actual Python `host/moonshine/protocol.py` MSV1 packet generator and
strict one-frame `Reassembler`, hypothetical network service, and analytical
sender/presentation queues. The host implementation is a protocol reference,
not proof that the running Rust receiver, DMA, FPGA or radio behaves identically.
The model's one-frame receiver queue is hypothetical: current firmware streams
packets to the FPGA and drops when it is busy; this study does not implement an
ESP32 queue. The test source is 1,800 captures at exactly 30 Hz, **repeating
the same ten synthetic q65 JPEGs** from the fixture generator. It is not a
60-second RTL simulation or 1,800 unique gameplay frames.

## Model and boundaries

- The sender has one in-flight frame and at most one waiting frame; on a new
  capture the pending frame is replaced with the latest. An already transmitting
  frame is not interrupted. The sender drops a waiting frame older than 100 ms.
- Each JPEG is packetized using the actual MSV1 packetizer (1,024-byte payload
  maximum, CRC and frame IDs). Per-packet serialization counts the 40-byte
  MSV1, 28-byte IPv4/UDP headers and payload, but excludes Wi-Fi MAC/PHY,
  retries, encryption, fragmentation, audio and controller traffic. The link
  is a single serialized service. For a variable-service scenario the rate is
  sampled at each packet's start and held for that packet.
- The loss/jitter tests use deterministic independent random events, not a
  measured radio model. Jitter adds a uniformly chosen packet delay in
  `[0,1200]` microseconds; it can reorder packets. The loss scenario uses a
  0.5% independent chance per datagram. The burst case selects a 2 Mb/s packet
  service rate during the first 80 ms of each second, otherwise 8 Mb/s.
- Successfully reassembled frames enter a conceptual one-frame *latest*
  presentation queue with 100 ms maximum age. Frames that cannot be processed
  immediately may be replaced. Each selected frame uses the corresponding one of
  ten previously measured RTL JPEG upload/decode durations, then waits for an
  ideal 65.0755 Hz LCD swap boundary. Durations repeat regardless of scene,
  queue phase or contention. The reference service still assumes the fast
  register bus, excludes ESP32/QSPI/CRC computation and uses an experimental
  parser and burst controller; neither the queue nor the RTL is deployed.
- CRC/reassembly runs in the real reference code, but its execution time is
  taken as zero. Source/encode time, QSPI, actual framebuffer pixels, frame
  capture latency, processor load, operating system and real radio are omitted.
  `packet_rejects` counts rejected **datagrams**, not rejected frames.

## Deterministic run (seed 13)

| Assumed link | Sent / captured | Complete / captured | Presented / captured | Sender replacements | Max modeled capture-to-swap |
| --- | ---: | ---: | ---: | ---: | ---: |
| 12 Mb/s, no loss | 1800 / 1800 | 1800 / 1800 | 1800 / 1800 | 0 | 56.7 ms |
| 8 Mb/s, no loss | 1800 / 1800 | 1800 / 1800 | 1800 / 1800 | 0 | 66.3 ms |
| 4 Mb/s, no loss | 1051 / 1800 | 1051 / 1800 | 1051 / 1800 | 749 | 126.5 ms |
| 8 Mb/s, jitter 0–1.2 ms | 1800 / 1800 | 1289 / 1800 | 1289 / 1800 | 0 | 67.3 ms |
| 8 Mb/s, 0.5% packet loss | 1800 / 1800 | 1561 / 1800 | 1561 / 1800 | 0 | 66.3 ms |
| 8 Mb/s, periodic 2 Mb/s burst | 1740 / 1800 | 1740 / 1800 | 1740 / 1800 | 60 | 127.7 ms |

The loss and jitter results illustrate the cost of strict in-order MSV1 with
these **synthetic assumptions**; they do not measure real packet loss or prove
a need for any specific recovery feature. Reordering, buffering, retransmits,
FEC and sender adaptation must be compared against measured traces and a fixed
total link/latency budget. The max age can exceed the queue's 100 ms *start*
deadline because an already started frame runs to completion. Approximate
IPv4+UDP+MSV1 overhead here is 6.35% of these modeled wire bytes; real wireless
overhead will differ.

## Calibration against prior RTL

As a check, `calibrate.py` switches the same network model to count payload
bytes only and replays ten frames with the 8 Mb/s assumptions used in the
[prior RTL link test](../link-study/README.md). Nine presentation timestamps
match within one 100 MHz cycle; frame 4 is **1,536,677 cycles (15.36677 ms)**
later than that RTL run. Reusing measured per-frame service times does not
capture phase-dependent memory and display contention. This one-refresh
mismatch makes long-run numbers sensitivity studies rather than precise timing
predictions. The prior RTL test itself is also an idealized model, not hardware.

## Reproduce

With Python, Pillow, and the project host dependencies installed:

```sh
fpga/experiments/throughput30/burst/transport-followup/run.sh
```

The runner uses an empty temporary output directory (or `OUTPUT_DIR`), runs six
unit tests covering packet-byte accounting, overload, deadlines, complete loss,
reordering and invalid configuration, generates the ten synthetic JPEGs,
runs the 1,800-capture scenarios, then runs the RTL comparison. `results.json`
contains the scenario parameters and full counters, and `calibration.json`
records timestamp differences. The checks are reproducible for the specified
fixtures, seed and timing inputs. Source is in `model.py`; no production code
or bitstream is modified.
