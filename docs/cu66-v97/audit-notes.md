# V97 initial transport and fidelity audit

Status: read-only source audit at baseline `bd8fcc49c1c6b069432dd1ae93109640359fea8e`.
No runtime code, tested RTL or generated evidence was changed. These notes
bound V97 proposals to the checked-in interfaces; they are not a qualification
of firmware throughput or hardware behavior.

## Existing transport and resource facts

- The actual standalone network receiver in
  `firmware/handheld/src/streaming/protocol.rs` accepts only 40-byte `MSV1`
  headers and 1..1,024 payload bytes per datagram. Resolution is fixed at
  720×480; frame length is 1..262,144 bytes (256 KiB). Chunks are strictly
  sequential, frame metadata must agree, CRC32 is checked before the receiver
  reports completion, and wrap-aware stale IDs are rejected. A malformed,
  missing, duplicate or reordered chunk invalidates the active frame. It has
  no full-frame payload allocation; receiver state is under 128 bytes in its
  existing test.
- `streaming/mod.rs` allocates one `HEADER + CHUNK + 1` (1,065-byte) buffer with
  `MALLOC_CAP_DMA | MALLOC_CAP_INTERNAL`, receives each UDP packet into that
  buffer and forwards only the payload slice. FPGA bitstream loading separately
  uses a 16 KiB internal DMA buffer. This source establishes these explicit
  allocations, not total Wi-Fi/IDF stack heap use, worst-case heap headroom,
  scheduling cost, or a target-memory budget. There is no PSRAM requirement in
  this path; do not claim no-PSRAM feasibility for the complete application
  without measuring remaining IDF/Wi-Fi and concurrent UI allocations.
- The production core parameter defaults to `MAX_BYTES=262144` and contains a
  262,144-byte compressed array in FPGA block RAM (`moonshine_core.sv`). The
  proposed custom study profile's 49,152-byte CP27 admission limit is a
  separate profile/bound, not the JPEG limit and not evidence the existing
  FPGA JPEG core accepts CP27.
- The implemented `MSV1` parser/receiver and standalone Rust/Wi-Fi gateway are
  distinct layers. An MSV2 gateway, packet parser, or host-native bridge does
  not add a custom MSV2 codec decoder to the FPGA, nor establish actual Xtensa
  instruction timing, ESP-IDF/Wi-Fi behavior, QSPI DMA arbitration, or target
  memory use. The existing FPGA endpoint shown here is the JPEG core.

## Register and transaction contract

- Firmware's `forward()` reads `BASE + 0x0c` before every `spi_write`, checks
  `credits >= payload.len()`, then sends the payload at `BASE + 0x100` using
  an 8-bit, non-incrementing QSPI write at 40 MHz. In production RTL,
  register `0x0c` is `receiving ? length - received : 0`: remaining frame
  capacity in bytes. It is not free FIFO entries, generic backpressure credit,
  decoder progress, or permission to account for bytes that have not yet been
  accepted. Keep frame-byte bounds and any queued-write/FIFO credits as
  separate quantities.
- The experimental FIFO-credit endpoint documents a separate local address,
  `0xe0000054`, for conservative free entries in its 64-slot asynchronous
  write FIFO. That register and sub-burst policy are absent from production
  RTL and firmware. Its experiment itself says an initial FIFO credit cannot
  authorize a 1,024-byte burst; it also retains the production `0x0c` meaning.
- `begin()` accepts only the existing FPGA identity and protocol major 1,
  checks JPEG capability and idle status, writes frame ID/length/dimensions/
  CRC, then command bit 0 at `BASE + 0x24`. It rejects when the decoder is
  busy; when prior receive/decode fault bits are set, it first issues abort
  bit 1 and rechecks status. Completion command bit 2 is sent only after the
  Rust receiver reports whole-frame CRC success. FPGA then independently
  requires exact received length, its own CRC, and JPEG SOI/EOI before decode.
- `abort()` retries the FPGA abort command (bit 1) for up to 100 ms while
  checking identity. Malformed transport data, a new start while a frame is
  active, forwarding errors, receive timeout, socket error and session exit
  lead to abort/recovery. The QSPI frame is single-owner: the production core
  has one compressed buffer and remains not-ready through receive, decode,
  pending publication and drain. The experimental dual-bank study requires
  explicit bank generations/ownership and independent credits before any
  overlap claim; merely adding storage is not sufficient.
- Existing identity is polled from the streaming worker at core setup and by
  each abort/forward path; status/identity operations also occur around frame
  setup/commit. `exit_to_menu()` requests stop and waits for `ACTIVE` to clear
  before restoring the other FPGA image. Any cached identity/capability plan
  must preserve this app-switch ownership boundary and invalidate on reset,
  reconnect, bitstream replacement or session epoch change.
- There is currently one whole-frame completion reply (`MSF1`) after a
  successful CRC/commit request, plus errors/input/heartbeat. Do not describe
  an existing per-fragment success ACK or remove one as an optimization.
  Completion reports network receive/commit submission, not FPGA decode or
  display; those are separate counters/observations.

## V97 proposal guardrails

1. Keep MSV1 byte-compatible as the legacy JPEG profile. A new MSV2 format
   needs explicit negotiation/admission: codec and decoder capability,
   geometry, per-profile frame cap, fragment size, features, and session epoch.
   Unsupported modes must be rejected or never selected by the sender.
2. Keep the profile bounds distinct: JPEG/MSV1 max is 262,144 bytes;
   custom CP27 is 49,152 bytes. Do not infer custom-decoder support from the
   existence of Rust gateway code or research packet grammars.
3. Define credits as bounded accepted FIFO slots/bytes for actual queued DMA
   and writes, with reservations subtracted until completion/abort and reset
   semantics explicit. Never treat remaining frame length (`0x0c`) as FIFO
   free space, or infer credit from decoder progress. Track logical payload
   length separately from aligned/padded DMA transfer length; only logical
   bytes affect CRC, frame completion and FPGA accepted-byte count.
4. Preserve the current final CRC gate and FPGA commit semantics. A transport
   ACK or final fragment receipt alone must not commit a frame. A custom
   predictive profile additionally needs explicit accepted-reference
   generation/reset policy; JPEG independent-frame recovery does not supply
   that contract.
5. Keep legacy JPEG usable during rollout. Capability negotiation must be
   truthful to the decoder image actually loaded, and profile changes/core
   replacement must invalidate cached session state. Preserve single-frame
   abort/drain ownership unless a banked protocol and decoder implementation
   independently qualify overlap.
6. Compare CPU, internal DMA heap and bounded buffers using measurements on
   target. Source-level buffer sizes are not an ESP-IDF whole-system memory
   budget. Queued DMA needs owner tokens, explicit logical pad length and
   completion/abort drain before buffer reuse.

## Emulation availability and evidence boundary

At audit time, `renode`/`Renode` is not on `PATH`; no checked-in `.repl` or
`.resc` Game Bub platform manifest was found in the scoped repository search.
No installation was attempted. Follow the existing Renode assessment: a
generic Xtensa example is not an ESP32-S3 board model, and Renode plus
Verilator alone does not supply calibrated Wi-Fi ingress, IDF timing, QSPI/DMA
arbitration or physical display/memory behavior. V97c should report the exact
configured model and substitute boundary; do not imply ESP32/Wi-Fi fidelity
from a host-native receiver or behavioral queue.

## Reviewed sources

- `docs/gamebub-v91-v110-development-plan.md` (V97 row and emulation gate)
- `docs/esp32-compact-transport-plan.md`
- `docs/renode-verilator-assessment.md`
- `firmware/handheld/src/streaming/protocol.rs`
- `firmware/handheld/src/streaming/mod.rs`
- `firmware/handheld/src/device/drivers/fpga/mod.rs`
- `fpga/rtl/moonshine_core.sv`
- `fpga/experiments/throughput30/burst/cdc-credit/README.md`
- `host/PROTOCOL.md`
