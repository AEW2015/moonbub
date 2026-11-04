# Bounded prospective host pacing and consumed-packet credits

This Python study closes two gaps in the v16 gateway sensitivity model: implicit
unbounded producer/link backlog and burst delivery beyond the ESP32's six-entry
UDP mailbox. It tests a **prospective transport controller**, not installed
firmware, a new encoded video syntax, or ESP32 instruction/RF emulation. The
source-size workloads retain the 720×480 coded / 720×405 active / 30 Hz target.

**These are opaque body-size traces, not decoder-valid replay.** They include
already encoded key/promotion/P histories. Dropping one can invalidate later
references; packet-consumed credits do not establish decoded YUV publication.
Gateway completion counts below are not displayed FPS, cannot be added to the
codec model's FPS, and do not prove 30 distinct decoded frames/s. Live admission
must integrate before encoder candidate commit, or use safe transaction expiry/
reference fallback and content-bound decode ACKs. Reference publications need a
separate protected policy. No such codec integration is implemented here.

## Controller and resource contract

The host owns at most one active frame plus one latest pending source frame.
When a new source arrives, it replaces only the unadmitted pending source. The
controller estimates completion from the complete body size, remaining forward
wire service, configured CPU/driver allowance, FIFO-drain allowance, packet
pacing, credit round trips and aggregation allowance. It admits the complete
frame only if the estimate fits a declared 120 ms age budget. This uses known
configuration and ready body size, not receiver queue/FIFO/future state. The
estimate is not a deadline guarantee or a predictor of a not-yet-encoded size.

Every admitted non-faulted frame attempts every chunk; there is no intentional
partial-frame quality mode. Admission can drop original input IDs. Feedback
failure can leave an admitted frame partly issued: that unresolved work is
reported rather than mislabeled as drain/success. Once admitted, a late/failed
frame is not silently shortened to improve the completed-ID count.

There are six logical data tokens, each identified by session, slot and a
monotonic per-slot sequence. A token is released only by a matching consumed-
packet ACK/NACK produced **after** the gateway worker finishes. A stale/duplicate
reply cannot release a reused slot; foreign-session feedback is ignored. These
logical fields are not a serialized or authenticated wire implementation.

The receiver retains six fixed ledger entries, one per token. Reusing a token
with a newer sequence confirms receipt of its old reply and replaces its ledger
entry. A lost feedback message triggers a bounded explicit ledger query. Queries
travel on the forward wire, share the same six-entry mailbox and serialized
worker, and pay an assumed control CPU cost. One extra reserved control token
limits all data+query messages to seven: one working packet plus six queued.
The host allows at most one control query in flight; a reply releases it. Query
loss does not cause permit invention. Total feedback loss leaves six data tokens
and one query outstanding and safely stops forwarding while latest sources drop.
This is a bounded stop, not recovery or successful full protocol drain.

The sender window, source queue, active body, receiver mailbox, credit ledger and
query queue are explicitly bounded. Event input arrays are offline test stimuli,
not a claim about target process memory. Network/lwIP driver allocations, Python
objects and codec/framebuffer scratch are outside these logical counts. This is
not an ESP heap/BRAM fit result.

## Framing is budgeted, not free

The current firmware has 40-byte MSV1 headers and 1,024-byte payloads. A prospective
16-byte credit extension budgets session-u32, slot-u16, reserved-u16 and sequence-
u64, making the modeled header **56 bytes**. Payload falls to **1,008 bytes** so
the maximum UDP datagram remains **1,064 bytes**, fitting the existing 1,065-byte
internal DMA allocation. IP/UDP adds 28 wire bytes. Credit replies use 64+28 bytes;
queries use 32+28. Both reply duplicates and query traffic are counted.

This is not current MSV1 or GF02 compatibility. No framing bytes are serialized,
no real checksum/negotiation parser is supplied, and actual driver allocations
still need measurement. The model adopts v16's source-shaped CPU, bitwise CRC,
copy/poll/QSPI/lock/abort costs as declared assumptions. True-FIFO waiting is a
new hypothetical backpressure contract; installed remaining-frame credit remains
a separate unsafe scenario. The six-token bound prevents mailbox overflow but
cannot repair a faulty FIFO contract or make a slow decoder drain faster.

Forward and reverse service use separate serialized virtual links at assumed
rates. They are not independent physical Wi-Fi channels; shared airtime,
retransmission, radio/OS batching, ISR/cache/task scheduling and actual packet
loss are not simulated. Aggregation buckets are synthetic delivery stress.
The copied gateway's 500 ms idle timeout is also outside this controller.

## Retained results

The campaign has **36 cases**: three retained admitted v16 size profiles and a
60-frame maximum-body stress, each under nine policies/service scenarios.
Original source IDs and holes remain. The first workload has 177 actual body
sizes spanning 180 original capture IDs/six seconds. Bodies are rescheduled at
sourceID/30, not actual encoder-completion times, and no pixels are decoded.

| Initial-only size workload | Admitted | Strict / eventual gateway completion | Maximum observed age ms | Source IDs dropped |
| --- | ---: | ---: | ---: | ---: |
| Paced, no delivery aggregation | 176 | 175 / 176 | 68.367 | 1 |
| Two-ms aggregation | 176 | 175 / 176 | 65.427 | 1 |
| Eight-ms aggregation | 142 | 141 / 142 | 90.308 | 35 |
| Twenty-ms feedback latency | 43 | 42 / 43 | 77.570 | 134 |
| Lost first credit + stale/foreign replies | 176 | 175 / 176 | 65.427 | 1 |
| Conservative CPU/driver service | 156 | 155 / 156 | 76.288 | 21 |
| Slow FPGA with true FIFO waiting | 102 | 101 / 102 | 91.254 | 75 |

All 36 cases have **zero modeled data/control mailbox overflow**. The credit
invariant holds despite aggregation and slow service; it trades throughput and
admission for bounded occupancy. It does not make an over-budget input rate
sustainable. Delay and loss must be reported alongside those zero-overflow counts.
Eight-ms aggregation is a bucket model, different from v16's fixed bursts of
eight; this is not a one-variable matched physical-RF comparison with v16.

One lost data credit recovers through one explicit query. The late duplicate and
foreign-session reply are ignored; all 176 admitted bodies are fully issued.
A feedback blackhole issues only six data chunks and one control query, leaves
credit ownership unresolved and completes zero frames. No false credit appears.
Slow FPGA with installed remaining-frame credit completes zero initial-only
frames; mailbox safety does not imply FIFO correctness or valid video.

For sixty 49,152-byte bodies, paced admission accepts/completes 35 and drops 25
before transmission (latest replacement/deadline admission). Maximum age is
78.830 ms. That is not 30 fps. New framing requires 53,268 IP/UDP bytes per full
body, or **12.78432 Mb/s at 30 Hz**, before reverse credits and Wi-Fi overhead.
An 8 Mb/s link cannot carry that average load. The controller bounds backlog and
age by dropping complete source candidates instead of retaining seconds of
implicit wire backlog. Different framing/admission means the prior v16 cap
stress is context, not a matched compression or end-to-end speedup comparison.

## Verification

Eleven tests pass: nominal packet progress, slow-worker/aggregation bounds, lost
feedback queries, stale/foreign-session rejection, safe total-feedback-loss stop,
complete-body cap admission, FIFO waiting, capture-ID holes, long-feedback drain
horizon timestamps and invalid limits.
Fourteen source/dependency snapshots are pinned before generation and checked
after. They include the retained input-size artifact and conservative firmware
fact snapshots, not exclusively executed files. `verify.py` recomputes all cases
and checks queue/token bounds, conservation, complete admissions and scope flags.

```sh
python -m unittest -v test_model.py
python verify.py
```

Use the project Python environment from this directory. Verification is
standard-library replay; it requires neither hardware nor the external video.
`benchmark.py` regenerates deterministic assumption evidence. This contains no
new measured host/ESP32 service timings or quality scores. Sources from v16 are
unchanged. Next integrate candidate admission and real reference publication,
serialize/version the credit protocol, then calibrate shared RX/QSPI/control
service and heap on the remote ESP32 before a physical rate claim.
