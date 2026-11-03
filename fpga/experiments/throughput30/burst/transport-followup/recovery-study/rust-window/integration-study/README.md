# Isolated reorder-to-FPGA transaction mock

This is a **software mock**, not the FPGA RTL, ESP-IDF receive loop, live
hardware, Wi-Fi, QSPI/DMA implementation or a proof of 30 fps. It exercises
the actual, unmodified Rust MSV1 `Receiver` and the adjacent research 4+1
reorder `Window` against a deliberately simplified sink with fixed buffers.
The sink models begin, byte forwarding, CRC/SOI/EOI-gated commit, abort,
busy and a separately triggered autonomous `vblank`. Its buffers hold the
**compressed JPEG bytes**, not the FPGA's decoded pixel framebuffer. It cannot
prove electrical, memory, IRQ, scheduling, reset or atomicity behavior of the
actual FPGA. No production source or bitstream is changed.

## Findings: session replacement and ambiguous failure

The bare reorder `Window` finishes its own frame when the last datagram passes
CRC. At that moment its `active` field is empty, while a real sink may still
have that frame committed and awaiting decode/presentation. Calling the bare
`Window::start_session()` cannot see that downstream pending frame and does
not abort it. The directed `bare_window_reset_does_not_cancel_committed_pending_sink`
test shows the modeled old pending frame appearing at the next modeled vblank.
This is a **boundary-of-responsibility issue**, not evidence of a defect in the
existing production firmware, which has not integrated this research adapter.

The isolated `Driver::replace_session()` mock therefore calls the sink's
`abort()` **unconditionally** before resetting the input window, even when the
window has no active frame. If the window had an active frame it may call abort
a second time; this mock assumes abort is idempotent. The corresponding tests
check both committed-pending and partially received frames: when abort succeeds
and occurs before vblank, the previous front bytes and ID remain unchanged, and
only a subsequently accepted new-session frame can be modeled as presented.
The session label is local only: unauthenticated MSV1 has no wire session ID,
so stale packets relabeled as current remain indistinguishable.

An ambiguous commit acknowledgment exposes a hard limit: if commit reaches the
sink but its acknowledgment fails, then an attempted abort also fails, software
quarantine alone cannot stop autonomous FPGA vblank. The deliberately passing
**counterexample** `failed_abort_cannot_guarantee_front_is_preserved_at_autonomous_boundary`
models that condition and shows the pending frame being presented. It is not a
safety pass. A real system needs a verified transaction/epoch mechanism or
confirmed hardware abort/quiesce, accounting for abort-vblank races and recovery.
The mock assumes sequential function calls and does not settle real clock-domain
ordering or prove that hardware abort is effective.

A related test shows that a sink rejecting a **new begin while a valid prior
frame is pending** causes the current `Window`'s conservative forced abort to
remove that prior pending frame. The old front remains intact in the mock, but
a valid pending frame is lost and the session becomes quarantined. The current
production firmware has different busy/error handling; do not infer that it
behaves like this experiment. A reviewed integration should distinguish a
provably side-effect-free busy result from an ambiguous command failure.

## Reproduced tests

The exact `run.sh` wrapper ran in the existing development container:

- **37 host tests passed:** 13 integration tests, 15 existing adapter tests and
  9 existing unmodified receiver tests. These include explicit 1,999/2,000 μs
  gap ticks, packet reordering, duplicate/CRC failure, busy begin, partial write,
  session replacement, sink failure, and the abort-failure counterexample.
- `fixture.rs` split the checked-in **26,159-byte** synthetic JPEG into 26
  actual MSV1 datagrams, reordered the first pair and another pair, passed it
  through the adapter into the mock sink, and verified byte-exact reconstruction
  and explicit modeled presentation. It then corrupted a follow-up frame and
  checked abort/front preservation, and canceled a third committed-pending
  frame on session replacement. `fixture.log` records the terminal marker.
- The isolated `no_std` library cross-compiled for both
  `xtensa-esp32s3-none-elf` and `xtensa-esp32s3-espidf` with the installed
  Espressif Rust toolchain. This is only a **library compile**; there is no
  target link, flash, stack/runtime measurement, timer or QSPI verification.

`MockFpga<262144>` in the host fixture runner allocates two large buffers to
represent external sink state in software. They are not an estimate of device
heap or FPGA resource use, and this mock must not be copied into the ESP32
firmware as an allocation plan. The previously measured 5,536-byte reorder
adapter footprint also excludes task stack, DMA and socket buffers.

## Reproduce

With a host `rustc` and the checked-in fixture:

```sh
fpga/experiments/throughput30/burst/transport-followup/recovery-study/rust-window/integration-study/run.sh
```

The runner creates a new empty temporary output directory, copies the actual
`protocol.rs`, adapter and mock sources, runs tests and the fixture, and saves
source SHA-256 hashes. Set `OUTPUT_DIR` for retained files. For optional
ESP32-S3 library cross-compiles set `CROSS_XTENSA=1` and `CROSS_TOOLCHAIN`
(default `esp193`) to an installed Espressif Rust toolchain. Saved logs are in
this directory; source hashes are in `sources.sha256`.

Before any hardware integration, define authoritative sink states and error
codes, implement actual session binding and authenticated packets, verify
whether an abort really clears decoder/pending state and what happens at a
simultaneous vblank, establish reset/quiesce recovery when acknowledgment is
ambiguous, and exercise the actual Rust/FPGA boundary with QSPI loss and
backpressure. A UART/ILA/RTL trace and board-level test are necessary; this mock
cannot certify the actual front buffer's behavior.
