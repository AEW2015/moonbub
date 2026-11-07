# ESP32 compact streaming transport notes

Status: [V97 portable software and native-Rust/RTL checkpoint](cu66-v97/README.md)
implemented and tested; production UDP/QSPI integration and flashing remain
open. The deployed worker still uses JPEG/MSV1 and the frozen handoffs remain
available. The new exported Rust module is not selected by that worker. The
inverse-transform/complete decoder path remains a separate integration item.

V97 now specifies actual 40-byte setup/ACK and 12+16-byte data framing, bounded
two-stage forwarding, tokenized true-FIFO observations and ingress commit-ACK
fences. The live native/RTL join uses a synchronous parallel test adapter,
not ESP32 instruction execution or physical QSPI. Its independent header audit
charges setup and reports 3.528% fewer IPv4/UDP bytes for the tested set.
[Results and limitations](cu66-v97/results.md) retain the device-calibration gates.

## Verified current behavior

The Rust receiver in `firmware/handheld/src/streaming/protocol.rs` and host
packetizer in `host/moonshine/protocol.py` use a 40-byte MSV1 header for every
payload chunk of at most 1,024 bytes. Width/height, codec/version, full frame
length, full-frame CRC and 64-bit capture timestamp are repeated per chunk.
The receiver is bounded and requires sequential offsets; a missing/reordered
chunk aborts the incomplete frame. It rejects stale frame IDs with wrap-aware
comparison and validates the complete CRC before the final commit request.

`firmware/handheld/src/streaming/mod.rs` already strips the network header
before forwarding the payload slice to the FPGA. It already sends completion
feedback per frame, with additional error/input/heartbeat messages. There is no
existing per-fragment success ACK to claim as a removable firmware cost.
The study's PC18/FG19 packet-credit accounting is a separate prospective model.

## Proposed versioned network format

Introduce a newly negotiated transport version; do not reinterpret MSV1 bytes.
Change the host sender and ESP32 parser together. For legacy JPEG payloads the
existing FPGA begin/payload/commit register interface can remain the boundary.
Transport support alone does not install the custom GM27 decoder in the FPGA.

1. **Session setup:** negotiate codec, dimensions, maximum frame size, fragment
   payload size, features and a session epoch. Acknowledge setup and retransmit
   it as needed. Invalidate cached context on disconnect, reset or FPGA change.
   Preserve each profile's actual bound: MSV1's 256 KiB maximum and the custom
   study's 49,152-byte CP27 cap are different contracts.
2. **Common fragment header target: 12 bytes:** session epoch/u32, frame ID/u32,
   fragment index/u16, packet kind/u8 and flags/u8. This is a proposal requiring
   a byte-level specification and malformed-input tests before implementation.
3. **Frame-start metadata target: 16 extra bytes once per frame:** complete
   payload length/u32, whole-frame CRC32/u32 and capture timestamp/u64. Carry
   this in the first data datagram, so loss of a standalone descriptor does not
   create a separate dependency. A lost first datagram still invalidates the
   incomplete frame; never infer missing context from a later fragment.
4. **Continuation packets:** derive offset from the negotiated fragment size
   and index, and count from UDP datagram length. Check overflow, exact remaining
   length, partial-final-fragment rules, session/frame identity and all flags.
5. **Payload experiment:** test approximately 1,400 data bytes per packet,
   checking actual path MTU, socket receive limits and FPGA credits. Avoid IP
   fragmentation and do not assume larger datagrams are loss-free or faster.

Keep frame completion distinct from receipt of an arbitrary final fragment.
Preserve CRC, active epoch/frame checks, bounded lengths, loss recovery, credits,
and commit-on-completion. Custom predicted streams additionally require their
reference-reset/key-frame policy; JPEG's independent-frame recovery is not a
substitute. Treat reordering tolerance as an explicit optional window with a
measured memory bound, not an unbounded frame queue.

## Example wire-budget estimate

For a 24 KiB payload at 30 frames/s:

| Application framing | Header bytes/frame |
| --- | ---: |
| Current: 24 fragments × 40 bytes | 960 |
| Proposed: 18 fragments × 12 bytes + 16 start bytes | 232 |

This saves 728 application-header bytes/frame, or 0.17472 Mb/s. It excludes
session setup, feedback, IP/UDP, Wi-Fi MAC overhead and retries. It is arithmetic
under the proposed layout, not measured firmware throughput. The HEVC/AV1 codec
comparison used body bytes excluding this network framing; transport savings
do not remove that compression gap.

## Other firmware work worth measuring

- Cache stable FPGA identity/capabilities until reset/core replacement, while
  preserving the app-switch/stream-stop ownership contract. The present forward
  path performs identity and free-credit reads for each chunk.
- Reserve conservative byte credits per bounded burst, subtracting every issued
  byte and accounting for queued DMA. Refresh credits before exhaustion; never
  infer extra space from expected decoder progress or speculative FIFO drains.
- Use a small bounded aligned DMA pipeline, measuring copies, receive wait,
  SPI setup/status traffic and transfer time separately. Espressif documents
  [queued SPI transfers and DMA requirements](https://docs.espressif.com/projects/esp-idf/en/v5.3.2/esp32s3/api-reference/peripherals/spi_master.html).
  Preserve exact logical lengths for the final partial transfer; padding must
  not become extra codec bytes or alter CRC/commit behavior.
- Keep prompt input/error traffic and frame-level completion feedback. Any
  cumulative credit/ACK change needs its own outstanding-byte and wrap/reset
  tests. Do not trade controller latency for smaller control traffic blindly.

Consolidating GM27/HU25/CP27's inner frame metadata, tags or CRCs is a separate
versioned host/FPGA parser change. The ESP32 must not silently remove fields the
negotiated downstream decoder expects. The exact HUD is image data rather than
transport header overhead.

## Implementation and simulation gates

1. Freeze byte layouts, session state transitions, bounds and golden vectors.
2. Add a Python sender/receiver model and Rust parser/receiver tests using the
   same vectors. Preserve MSV1 tests as compatibility controls.
3. Inject truncated headers, malformed lengths, overflow, wrong sessions, stale
   IDs, wrap, duplicate/reordered/missing fragments, lost setup/start/final data,
   CRC corruption and sender/FPGA resets at every transfer phase.
4. Verify bounded memory, exact payload/CRC, credit accounting and zero commits
   for incomplete/corrupt frames. Replay valid frames after every error.
5. Simulate the actual QSPI/credit/abort/commit boundary with backpressure,
   partial DMA and core replacement. Compare payload hashes and presented IDs.
6. Hardware A/B test MSV1 versus the compact mode: bytes/frame, packet rate,
   CPU service, internal DMA heap, drops, recovery, input latency and frame age.
   Report MTU and Wi-Fi conditions. No firmware speedup is established yet.
