# MSV1 reordering, burst loss and recovery experiment

This is a **host-only event simulation**, not an ESP32 firmware change, radio
measurement, FPGA/video pipeline simulation, or 30 displayed fps proof. It uses
the **unmodified Rust `firmware/handheld/src/streaming/protocol.rs` receiver**
in a host replay executable. The same stream also runs through the Python MSV1
reference, and every `partial`/`done`/`error` result must match Rust. In the
8 Mb/s, 100 ms report, 1,576,886 packet and explicit abort events were compared
with zero mismatches.
This validates those packet-state outcomes on the host; the ESP-IDF thread,
actual socket, forwarding SPI, DMA and board are not executed.

Current firmware validates datagrams in order, then forwards chunks directly to
the FPGA. It aborts the active transfer on error. The **full-frame reorder and
FEC staging below are hypothetical additions**, not current receiver behavior.
They would change buffering, protocol and firmware/FPGA integration.

## Workload and assumptions

Each run captures 600 frames at 30 Hz, cycling **ten synthetic q65 JPEGs**;
seeds 71–75 give 3,000 source frames per table row. The source is repeated,
not direct game footage. The sender has one frame in flight and one waiting
latest-frame slot; it never preempts an in-flight frame and expires a waiting
frame older than 100 ms. Wire service is fixed at the specified 8 or 10 Mb/s
for **IPv4+UDP+MSV1+proposed parity bytes**, including a hypothetical 24-byte
parity-group envelope. Wi-Fi MAC/PHY, retries, encryption, audio, and control
traffic are excluded. A rate here is an assumption, not measured throughput.

Every packet in the `jitter`, `iid` and `bursty` cases receives independent
uniform 0–1.2 ms additional delay, which can reorder adjacent datagrams.
`iid` also drops each transmitted packet with 0.5% independent probability.
`bursty` uses a packet-stepped Gilbert–Elliott process: good→bad 0.002,
bad→good 0.25, loss probability 0.0005 in good and 0.5 in bad. The realized
bursty loss fraction here is about 0.41–0.42%; burst length and transition
probabilities are synthetic, not calibrated to the Game Bub link. `clean` has
zero loss and zero jitter. Parity packets also receive jitter and loss. No
packet corruption, actual FEC coding/decoding time or retransmission is modeled.

Five receivers are compared:

1. **Strict:** deliver arrived data packets in network order to the actual
   Rust MSV1 state machine; missing, reordered or malformed packet sequences
   abort a frame. Parity is disabled.
2. **Window4:** an experimental four-datagram, 2 ms gap-deadline reorder
   window forwards only contiguous data to the Rust receiver. A timeout aborts
   the receiver. It cannot handle a fragment that arrives before SOF, or a lost
   SOF. The host replay represents explicit Rust `Receiver::abort()` calls with
   a zero-length sentinel in its private test stream; the sentinel is not MSV1.
3. **Window4+pre-SOF:** the same reorder window with one additional datagram
   slot retained for up to 2 ms before a matching SOF. It only admits a plausible
   next frame with a bounded offset, validates packet metadata before storage,
   and never forwards the staged fragment until the matching SOF arrives. This
   is a hypothetical design, not authenticated, audited or deployed. It still
   cannot repair a SOF which never arrives, two pre-SOF datagrams, or long gaps.
4. **Reorder:** an experimental one-frame buffer collects data fragments in
   any order and releases a complete frame to that same Rust state machine in
   order. A newer frame evicts an incomplete older frame; no repair is possible.
5. **XOR/8:** an experimental one-frame buffer additionally receives one XOR
   parity datagram per up to eight whole MSV1 datagrams and reconstructs one
   missing or delayed packet per group. Reconstructed data must pass the real
   Rust receiver, CRC and a fixture byte comparison. The parity envelope has no
   implemented protocol, negotiated layout, authentication, anti-replay or
   resource admission. A testbench oracle supplies grouping and frame metadata;
   a real implementation must encode and validate them. Two missing packets in
   one group cannot be recovered. A delayed packet reconstructed before it
   arrives also counts as a reconstruction.

Each case sees the same configured peak L3 service rate and JPEG quality;
parity consumes real modeled transmission slots, so it is not free bandwidth.
The data-only strict/reorder policies replay exactly the same data arrivals.
FEC inserts packets and changes PRNG steps, so equal initial seeds **do not**
mean paired identical erasures across FEC/non-FEC policies. Only five seeds
are used; use real traces and more seeds before generalizing.

## Results at 8 Mb/s, 100 ms capture-to-reassembly deadline

| Synthetic channel | Strict | Window4 | Window4+pre-SOF | Full-frame reorder | XOR/8 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Clean | 3000 / 3000 | 3000 / 3000 | 3000 / 3000 | 3000 / 3000 | 3000 / 3000 |
| Jitter, no loss | 2171 / 3000 | 2995 / 3000 | 3000 / 3000 | 3000 / 3000 | 3000 / 3000 |
| Jitter + IID loss | 1938 / 3000 | 2618 / 3000 | 2635 / 3000 | 2635 / 3000 | 2992 / 3000 |
| Jitter + bursty loss | 2099 / 3000 | 2837 / 3000 | 2844 / 3000 | 2844 / 3000 | 2927 / 3000 |

Average modeled wire use over the 20-second capture interval is 6.857 Mb/s
for data-only and 7.928 Mb/s with XOR/8, about **15.6% more**. Across cases,
the model's peak stored MSV1/parity bytes are 3,460 for the four-slot window,
3,460 for the pre-SOF variant, 28,380 for full-frame reordering and 32,732
for parity. The respective theoretical data-slot caps for the two small-window
models are 4×1,064=4,256 and 5×1,064=5,320 bytes; these exclude metadata. These are sample data bytes and hypothetical parity metadata only;
exclude allocator structures, socket queues, DMA memory and the additional
full-frame bytearray in the Python reference. They are **not measured ESP32
RAM**. In this test FEC sometimes reconstructs a delayed packet which later
arrives; duplicate/metadata/security handling needs a real design.

The worst per-seed p95 capture-to-reassembly age was about 30.0 ms for data-only
and 33.4 ms for XOR/8 under jitter/loss. These are conditional on frames which
complete and omit capture/encode, CPU, QSPI, decode, LCD and presentation.
Losses/failures do not get an artificial zero-latency value.

## Deadline and rate tradeoff

Keeping all assumptions the same but requiring complete reconstruction by
**33 ms from capture** changes the jitter-only results to: strict 2171/3000,
window4 2995/3000, window4+pre-SOF 3000/3000, full-frame reorder 3000/3000,
and XOR/8 **2366/3000**. For IID loss they are 1938, 2618, 2635, 2635 and
2303 respectively; under bursty loss 2099, 2837, 2844, 2844 and 2302. The parity method
can miss the tighter deadline merely because its extra bytes occupy the link.
This is a packet-reassembly deadline, not a gaming latency target or a claim
about final display time. The 10 Mb/s, 100 ms results are included separately; the plain four-slot
window delivered 2899/3000 jitter-only frames, whereas the pre-SOF variant
completed 3000/3000. `sof-diagnosis.json` records that all 101 failed frames
in the plain-window sample saw a non-SOF packet first; the pre-SOF candidate
addresses that specific case but adds security and resource concerns.
independent jitter produces different reorder frequencies at different packet
serialization rates. Quantization, bitrate reduction or other parity layouts
were not tested; these comparisons keep the same JPEG quality.

## Engineering implications and next validation

- Measure timestamped actual packet arrivals, reordering, burst loss, queue
  pressure, RAM headroom and concurrent QSPI goodput on hardware. Do not treat
  independent uniform jitter or a particular Gilbert–Elliott parameter as a
  real measurement.
- Prototype a tightly bounded in-order reorder window and expiration using the
  actual Rust receiver, with frame/session identity, SOF-lost behavior, late
  packet and sequence wrap checks. A full-frame buffer is only a theoretical
  upper-bound experiment; the firmware must fit in actual internal RAM and
  account for DMA, decoder ownership, aborts and QSPI credits.
- If FEC is considered, specify and authenticate its actual metadata, use the
  same constrained bandwidth including headers/retries/audio, and compare at
  matched visible quality and deadlines. Test multiple loss bursts per group,
  parity loss, stale session packets, corruption and feedback/backoff before
  attempting deployment. Adaptive parity must not worsen congestion.
- Correlate receiver completion with actual FPGA presentation IDs and frame
  age; this experiment reports **received complete frames**, not displayed fps.

## Reproduce and tests

Install Python/Pillow and `rustc`, then run from the repository root:

```sh
fpga/experiments/throughput30/burst/transport-followup/recovery-study/run.sh
```

`OUTPUT_DIR` can point to a new or empty location; `PYTHON` and `RUSTC` select
the tools. The runner copies the checked-in **unmodified** Rust receiver to a
private build directory, compiles the `rust_replay.rs` host shim, runs fifteen
unit tests (including real Rust checks, pre-SOF, reorder, loss, parity and deadline
cases), generates ten validated fixtures and reproduces the three reports.
`results-8mbps.json`, `results-8mbps-33ms.json` and `results-10mbps.json`
record exact source/fixture hashes, seeds, counters and Rust/Python comparison.
The model does not synchronize or send any packets to physical devices.

The complete `run.sh` was executed in the existing development container with
Python 3.12.3, Pillow 10.4.0 and its Rust toolchain. All fifteen tests passed.
An independent Python 3.14.4 replay is also checked against the recorded
summaries and per-run counters for these fixtures and seeds; this does not
guarantee cross-version reproducibility in general.
