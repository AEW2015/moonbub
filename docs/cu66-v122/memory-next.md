# From retained row accounting to a memory implementation

The current guarded parent uses aligned 8-byte candidate writes, a 16-bit abstract
data bus and one physical request lease. Each request is expanded and checked
byte-for-byte against independent canonical/HUD data. Hash delivery requires
the matching epoch's successfully ACK-committed memory contents; commit waits
for all physical writes and hash fences. These obligations stay authoritative.
See [the actual service/checking code](../../fpga/experiments/cu66-v117-live-guard/tb_keyframe.cpp)
and the [measured baseline](stall-baseline.md).

## What the observations establish

- Both row profiles write 560,640 bytes using 70,080 requests. Data service is
 280,320 edges. Fast overhead is 140,160 edges; stalled overhead is 840,385.
- The stalled post-input latency is 1,553,197 cycles. Its reconstruction interval
 alone is 1,359,332 cycles; the remaining tail is 193,865 cycles.
- Phase-edge totals use one priority-selected phase per edge. They partition
 the instrumented interval but do not identify every concurrent hardware activity.
 Wait-condition counts overlap and cannot be added as exclusive latency.

At an assumed 125 MHz complete-parent clock, the reconstruction interval alone is
10.874656 ms. An ideal fully overlapped validation tail therefore cannot by itself
meet strict <10 ms. The existing clock and service models are not physical timing
measurements.

At an assumed 100 MHz complete-parent clock, the strict limit would instead be
999,999 cycles. The same fast/stalled traces project to 11.451040/15.531970 ms
and need 145,105/553,198 cycles saved. Source B's qualified 100 MHz component
clock does not qualify the complete parent or turn these projections into
hardware decode measurements.

## Candidate hardware work, with prerequisites

1. **Gather contiguous writes.** Evaluate 16/32/64-byte bursts after recording
   actual candidate addresses. Larger logical groups are not automatically
   contiguous physical rows. If production order is strided, gather completed
   fragments in a small row/stripe cache with byte-valid bits and epoch tags.
   Account for fill delay, partial-row flush, plane/HUD boundaries and memory
   ports; never read or publish unfilled bytes.
2. **Decouple command and completion.** Explore a two-entry request queue only
   if the actual controller can overlap command preparation with its 16-bit data
   service. Two requests do not create two independent memory buses. Reserve
   credits at acceptance; keep every accepted write until its authoritative ACK
   or cancellation/drain completion. Preserve immutable front/reference banks.
3. **Stream validation where possible.** Overlap ordered content/HUD validation
   with reconstruction and ACKed writes, preserving the exact root/seal semantics.
   The join must still wait for the final matching write ACK and every required
   digest. Do not replace a digest or subtract tail cycles as if work disappeared.
4. **Reserve scanout service.** Add actual refresh/row-conflict/turnaround and
   scanout reservations before claiming a usable bandwidth or deadline bound.
   Keep the memory domain at its separately qualified clock when the decoder
   targets 125 MHz. Model CDC and finite queue occupancy explicitly.

The 20 burst-sensitivity cases hold average command overhead per transaction
fixed and vary an explicitly hypothetical unhidden fraction. They are useful
for selecting experiments, not predicting hardware FPS. For example, a 32-byte
case needs at least 48.10% of its modeled saved service edges to translate into
post-input latency savings to cover the 303,198-cycle deficit. The model omits
new buffering, address gather, control/ACK and physical timing costs.

## Instrumentation and proof before performance claims

The [wait-trace schema and validator](wait-trace.md) provide a starting contract
for successful single-epoch row traces. Its self-tests use synthetic data only.
Actual per-edge instrumentation, source provenance and physical calibration are
still required. Abort/retry accounting needs a separately versioned trace scope.

Add edge-level priority-resolved wait owners and trace their overlapping raw
conditions. Distinguish producer blocking, physical request/response service,
hash delivery, software HUD and actual reconstruction activity. Assert that
exclusive owner totals equal the measured interval and retain timestamps at
every fence. Use FPGA edge counters for the RTL path; any later real ESP32 CPU
task timing needs its own calibrated timebase. A C++ simulator's wall time is
not CPU or FPGA decode timing.

Use actual producer events where available. A replay of accepted output times
already contains backpressure from the original service policy; changing service
under that fixed schedule does not predict how the producer would accelerate.
To measure a new policy, drive a fresh latency-aware parent model with the same
content and deterministic external service traces, prove identical pixels,
ownership, digests and publication, then compare total cycles and queue ages.
Do not silently weaken the existing exact-cycle control to accommodate a new
performance architecture.

Finally qualify the complete board clocks/I/O/CDC and attach device evidence for
1,800 distinct frames/60 s and 18,000/600 s, then every packet-complete → validated
publication sample strictly below 10 ms. None of this iteration's analytical
sensitivity cases passes those hardware gates.
