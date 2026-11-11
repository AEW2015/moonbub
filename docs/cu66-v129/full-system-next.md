# V129: path to a negotiated host-to-device stream

The next integration milestone is an explicitly enabled, versioned session
between a host and the actual Game Bub worker, with the selected FPGA decoder
identified and its transport contract verified. The existing native protocol
results are useful building blocks; they do not establish that this system runs
on hardware or meets 30 fps or the under-10-ms FPGA decode goal.

## Current boundaries

* In the neighboring Sunshine checkout, commit
  `3d49c6fe87753eb5b35d693991fdff0365e4bbbf`, the experimental
  [MSV1 packetizer](../../../sunshine-30fps-study/src/gamebub/msv1.h)
  serializes bounded JPEG-labelled frames. It does not send packets, capture
  frames or negotiate a codec. Its [build option](../../../sunshine-30fps-study/cmake/prep/options.cmake)
  defaults to off. This path assumes the neighboring checkout is present; it is
  not part of this repository.
* The [active ESP32 streaming worker](../../firmware/handheld/src/streaming/mod.rs)
  creates the MSV1 `protocol::Receiver`, listens on UDP 5533 and forwards its
  payload. The standalone [MSV1 receiver](../../firmware/handheld/src/streaming/protocol.rs)
  checks codec label `1`, but does not prove payloads are JPEG. The
  [receiver test](negotiation-boundary.md) documents this distinction.
* The separate [V97 Python host](../../host/moonshine/protocol97.py) and
  [portable Rust receiver and gateway](../../firmware/handheld/src/streaming/protocol97.rs)
  implement explicit setup and ACK with JPEG and opt-in opaque profiles. Their
  [native exchange](v97-negotiation.md) passes protocol controls; it does not
  execute the active worker, Sunshine, ESP32, Wi-Fi, QSPI or FPGA. The test's
  payload is synthetic and does not establish JPEG validity.
* V97 names opaque research profiles `CS92`, `CS94`, `CS95` and `CS96`. None
  identifies the selected CS88 decoder or establishes its wire format and
  hardware compatibility. Configuring an opaque profile is not decoder
  capability discovery.

## Implementation sequence

1. **Define a CS88 contract before integration.** Specify a versioned profile ID
   and exact bitstream syntax, 720×480 pixel layout, frame limits, encoder and
   decoder compatibility, core identity/generation and reset/reference
   semantics. Verify the actual target's capabilities; do not reuse an opaque
   research ID as evidence of CS88 compatibility. Define explicit rejection
   and JPEG fallback when both endpoints and the attached core support it.
2. **Prove the host endpoint in isolation.** Add a separately enabled V97
   session/transport adapter to the Sunshine fork, retaining existing behavior
   by default. Exercise its actual serialized setup, exact ACK gate and
   packetizer against the portable receiver with shared byte fixtures and
   malformed, stale, unsupported and mismatched responses. The existing Python
   host is an oracle and prototype; it is not a running Sunshine capture path.
3. **Integrate a bounded device adapter.** Add a separately enabled worker path
   using V97 setup and gateway, without silently changing the MSV1 path. Check
   actual core identity and establish the selected sink state before sending an
   ACK. Ensure payload storage and DMA allocation meet real ESP32 constraints.
   Exercise duplicate, reordered, missing and malformed datagrams, loss of ACK,
   reset, core replacement and busy profile changes.
4. **Connect real flow control and ownership.** Follow the
   [V97 gateway contract](../../experiments/python-gamebub-v97/protocol/README.md):
   use an authoritative FIFO-free observation, preserve bytes while backpressured,
   fence abort/drain and in-flight DMA, and distinguish CRC completion, ordered
   transfer completion, ingress commit acknowledgement and display publication.
   The gateway's 2048-byte FIFO capacity is a standalone experiment, not a
   measured production FPGA capability. Resolve actual registers, queue depths,
   callback ordering, pacing and recovery against the target before enabling it.
5. **Verify the integrated system in stages.** First run source-bound host,
   worker and decoder simulations with identical protocol fixtures and negative
   controls; then test the connected board's negotiation, JPEG fallback and CS88
   decode. Record source and bitstream identities, counters, packet loss,
   sustained frames per second and latency measurement endpoints. Prove 30 fps
   over a sustained representative workload and separately measure complete
   FPGA decode below 10 ms; do not infer either result from an isolated clock or
   transport test.

This plan does not modify or restart the existing Sunshine service or active
device firmware.
