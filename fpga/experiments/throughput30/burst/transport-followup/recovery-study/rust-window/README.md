# Isolated no_std MSV1 4+1 reorder adapter

This is a **research prototype**, not an integrated Game Bub firmware change.
It wraps the repository's actual, unmodified Rust MSV1 `Receiver`; it buffers
up to four post-SOF datagrams and one pre-SOF datagram, then feeds only
contiguous, validated packets to the real receiver. It does not read sockets,
write QSPI, manage real FPGA credits, implement FEC, or prove throughput or
30 fps. The caller owns networking, timer scheduling, security, memory placement,
and a `Sink` that implements the FPGA transaction.

## Interface and behavior

- `Window::new(session)` creates the bounded state. `ingest(session, now_us,
  packet, sink)` validates the MSV1 header, rejects stale session/time and
  sequence information, and returns an `Outcome`; forward callbacks happen
  only after the **actual `Receiver::accept`** succeeds. The `Sink::packet`
  receives the accepted header, payload and final/CRC-passed flag.
- Four slots hold valid out-of-order packets up to 4×1,024 bytes ahead of the
  next expected offset. One additional slot holds one plausible new-frame
  non-SOF packet for up to 2,000 microseconds. It is released only if a matching
  SOF arrives; actual SOF loss, two pre-SOF arrivals, or a longer gap may fail.
  Duplicate and partially overlapping buffered ranges, gaps outside the window,
  invalid headers or same-frame metadata conflicts are rejected; an active
  partial sink transaction is aborted where required. A stale SOF is rejected
  before disturbing the current valid frame. Exact behavior is in `window.rs`.
- `tick(session, now_us, sink)` expires a pending gap or pre-SOF at **>=2,000
  microseconds**. The caller must schedule `tick` even when no datagrams arrive;
  there is no internal timer and polling late cannot enforce a precise deadline.
  Time must be monotonic in one local clock domain; a regression is rejected.
- `Sink::abort` must reliably invalidate any partially forwarded FPGA frame.
  The adapter aborts a prior in-progress sink transaction before forwarding a
  newer SOF. A sink callback or abort failure poisons the local session; a
  `start_session` requires a successful abort before clearing that state.
  A CRC mismatch does not forward the invalid final datagram or report done.
- Local session labels prevent accidental calls with an old caller label; they
  **do not authenticate MSV1 packets**. MSV1 carries no session ID. After a
  session reset, old network data relabeled as current is indistinguishable
  from valid data. A directed test demonstrates this. Caller-side peer/session
  binding, authentication, replay prevention and reconnect semantics are still
  required before any deployment. The prototype can be denial-of-service'd by
  malformed packets and is not a hardened network endpoint.

## Memory and target build

The five packet arrays provide 5×1,064 = 5,320 bytes of packet storage. A
`size_of::<Window>()` symbol-size probe in both isolated
`xtensa-esp32s3-none-elf` and `xtensa-esp32s3-espidf` release builds returned
`0x15a0` = **5,536 bytes**, including the adapter's fixed metadata and wrapped
receiver state. This is a compiler/ABI result, not measured available heap or
runtime use. It excludes task stack, initial construction temporaries, DMA
buffers, socket buffers, callback state and the rest of the firmware. Decide
safe static/heap placement and measure headroom before integration; don't put
this automatically on a small task stack. No board was programmed.

## Tests and limitations

- `host-tests.log`: 24 host tests passed (15 adapter, 9 existing receiver),
  covering in-order, variable-size overlapping/duplicate packets, four-slot
  overflow, pre-SOF and expiry, exact 2 ms deadline, stale/wrapped frame IDs,
  local session reset and its wire-auth limitation, monotonic clock rejection,
  receiver CRC failure and sink-failure poisoning/recovery.
- `crosscheck.json`: six 600-frame synthetic event replays at hypothetical 8
  and 10 Mb/s, with uniform 0–1.2 ms per-packet delay and three loss cases.
  The compiled Rust adapter's **93,262 ordered forwarding/abort callbacks**
  agree exactly with the separate Python bounded-window model across 95,840
  received data datagrams. These are two software models of the same design;
  neither runs ESP32-S3 hardware, QSPI or the display. Test traffic omits FEC,
  malicious packet injection and real network characteristics. Where a new
  SOF supersedes an incomplete Python frame, the comparison explicitly expects
  a sink abort; this models the necessary FPGA transaction action absent from
  the reference reassembler's implicit reset. All modeled packet timestamps are
  within the Python model's 100 ms capture deadline; the Rust adapter itself
  does **not** enforce capture-to-presentation or remote clock deadlines.
- `cross-none.log`, `cross-espidf.log` and `xtensa-size.txt` record isolated
  library builds with `esp193` Rust 1.93 nightly. A library cross-compile proves
  compilation, not a linked ESP-IDF application, live execution, memory safety
  under all traffic, timer accuracy, hardware FIFO safety, or a performance gain.

## Reproduce

Use Python/Pillow, a host `rustc` and a C++/Rust-capable development machine:

```sh
fpga/experiments/throughput30/burst/transport-followup/recovery-study/rust-window/run.sh
```

The script creates a new temporary build directory (or empty `OUTPUT_DIR`),
copies the current production `protocol.rs` without modifying it, runs host
unit tests, generates the ten synthetic fixtures and compares Rust callbacks to
the analytical Python model. To also compile the no_std library for both
ESP32-S3 targets, set `CROSS_XTENSA=1`, `CROSS_TOOLCHAIN` to an installed
Espressif Rust toolchain, and `XTENSA_NM` to its `xtensa-esp32s3-elf-nm`.
An existing development container execution of the **whole runner**, including
both targets, passed. `rustc`/toolchain and dependency versions matter.

Before production use, integrate the adapter with the actual receive loop and
DMA/QSPI abort path under a separate reviewed change; measure queue memory and
CPU time on hardware; add authenticated per-session transport; verify reset,
feedback, frame-CRC/sequence wrap, Wi-Fi burst/reorder and timeout races; and
compare displayed-frame outcomes with exact input traces. Until then, this is
an isolated verification artifact.
