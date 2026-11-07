# V97 compact transport and bounded native gateway

This is an opt-in transport study. Production `MSV1`, its worker and existing
FPGA JPEG register protocol retain their behavior. Exporting this Rust module
does not install a UDP worker, identify a compatible FIFO register, allocate
ESP-IDF DMA memory, or qualify Wi-Fi throughput. The C ABI connects the actual
portable Rust state machine to the isolated V97C RTL boundary for native tests.
It does not execute ESP32 instructions or model SPI pin timing.

Run `python3 scripts/cu66-v97/run_protocol.py` and
`python3 scripts/cu66-v97/build_ffi.py` from the repository root. Both retain
unique immutable attempt directories, bounded subprocess logs, source/input
SHA256s, native binaries, memory pressure gates and failure attempts. Existing
`gamebub-esp32-dev` supplies the offline native Rust compiler. No installation or
flashing occurs; each compile runs alone with one codegen unit and a watchdog.
`index.json` and `ffi-index.json` select the latest successful receipts. Failed
attempts do not replace a successful pointer.

## Wire grammar, all integers big endian

The 40-byte setup request/ACK is `!4sBBHIIHHIHHIII`:

| Offset | Bytes | Meaning |
|---|---:|---|
| 0 | 4 | New magic `MB97`, never MSV1 |
| 4 | 1 | Version 97 |
| 5 | 1 | Request 1, ACK 2 |
| 6 | 2 | Exact setup length 40 |
| 8 | 4 | Nonzero session epoch |
| 12 | 4 | Profile: JPEG 1, or explicit research ASCII CS92/94/95/96 |
| 16 | 2 | Width 720 |
| 18 | 2 | Height 480 |
| 20 | 4 | JPEG cap 262144, research cap 49152 |
| 24 | 2 | Exact negotiated fragment payload 1024 or 1400 |
| 26 | 2 | Flags, must be zero |
| 28 | 4 | Required sink capability: JPEG 1, opaque research 2 |
| 32 | 4 | Nonzero sink core generation |
| 36 | 4 | Reserved, must be zero |

The sender refuses to packetize before an exact ACK matches its request. The
receiver default accepts JPEG only. Research requires a separately constructed
`SinkConfig(opaque_profile=<same profile>)` and explicit sink capability 2. The
sender cannot authorize the receiver by asserting a capability itself. Extra
capability bits, unknown profiles and mismatched caps reject. Opaque framing
proves byte preservation, not decoding, reference reset or publication.
These research profiles are never advertised by a runtime worker.

Every fragment begins with the 12-byte `!IIHBB`: epoch/u32, frame ID/u32,
fragment index/u16, kind/u8=3, flags/u8. Only SOF=1 and EOF=2 exist. Index zero
requires SOF and adds exactly 16 bytes `!IIQ`: total payload length/u32,
IEEE CRC32/u32 and capture microseconds/u64. There is no extra descriptor packet.
The payload count is derived from datagram length and must equal
`min(negotiated_payload, total - index * negotiated_payload)`, strictly positive.
EOF is required exactly when this count exhausts the frame. A single-fragment
frame has both flags. Maximum UDP datagram bytes are 1428 (12+16+1400).

A start requires a strictly newer frame ID with modulo-2^32 delta in
`1..0x7fffffff`; `0xffffffff -> 0` works and the half-space tie rejects.
A new epoch uses the same ordering rule, must be nonzero, and clears frame ID
history. Exact setup retransmission is idempotent and preserves history; reuse
of an epoch with changed limits rejects. Reset/disconnect retains the retired
epoch so its replay cannot reopen a session. Stale epochs, unknown flags,
truncation, duplicates, loss/reordering, unexpected final lengths and CRC failure
invalidate the incomplete frame. No arbitrary reorder window or frame queue
exists. A lost final requires a caller-driven finite timeout and abort fence.

## Rust state and callback contract

`Receiver` parses bytes and maintains metadata/streaming CRC only. Its
`crc_complete` is not commit permission. `Gateway` adds two fixed 1400-byte,
4-byte-aligned staging arrays and one frame context. It never buffers an entire
frame. The caller additionally reserves one aligned 1432-byte receive buffer
(including four spare bytes beyond the largest datagram).

1. Install setup only after verifying the actual sink capability/core generation.
   `setup` returns ACK bytes. The adapter must establish sink epoch/profile state
   and any supported reference reset before transmitting that ACK. A changed
   busy session requires abort/drain; idle replacement may use the previous
   authoritative ingress ACK as its accepted-byte fence.
2. `observe_fifo_free(epoch, core_generation, actual_free)` admits only a
   matching synchronous FIFO snapshot in `0..2048`. `0x0c` in the production
   core means remaining frame bytes and is not such a source. For asynchronous
   reads, use `credit_probe` / `credit_response`; responses are single use and
   latest-query only. Their debt includes all current reservations plus bytes
   completed since query issuance, including bytes no longer in local staging.
3. `receive` first validates in a bounded metadata copy. Legitimate
   `WouldBlock` leaves parser/history unchanged. The caller must retain that
   datagram in its one receive buffer and retry it before consuming the next
   UDP datagram. A one-pass UDP sender cannot itself prevent socket loss during
   prolonged local stalls. Bounded buffering, pacing/retransmission and timeout
   policy remain worker integration work.
4. `transfer_bytes` returns only the exact logical payload span, with an aligned
   pointer. `Transfer.logical_len` is the SPI byte count. `staging_storage` and
   `storage_len` expose zero-filled alignment padding for diagnostics only.
   Never transmit that diagnostic span. Type alignment does not prove the
   allocation lies in ESP32 internal DMA-capable memory. Keep the gateway at a
   fixed address until drain; a real adapter must pin its DMA storage. The
   native C ABI uses a stable boxed gateway allocation.
5. `issue` enforces received transfer order. Queued and in-flight bytes remain
   reserved. `complete(token,true)` means the sink accepted every exact logical
   byte in issue order with no hidden queue before its commit boundary. DMA
   submission or an early completion before a CDC queue drains is insufficient.
   ACK releases the staging slot; it never creates FIFO credit. Tokens increase
   across reset and old/duplicate/out-of-order completion callbacks reject.
6. CRC-good final data plus all ordered transfer ACKs allow `take_commit` once.
   Its returned frame only authorizes a downstream commit request. The sole frame
   context stays fenced until `commit_complete(epoch,id,core_generation,true)`
   acknowledges ingress commit. Wrong tuples/replays do not mutate that context;
   matching negative ACK aborts. Publication/reference acceptance is a later
   boundary not proved by this transport API.
7. Error, timeout, reset and core change require a downstream abort. Ready slots
   may be discarded but in-flight buffers cannot be reused until their explicit
   ACKs arrive. `drained` requires zero in-flight transfers and the caller's
   authoritative abort/flush ACK. No elapsed timeout can manufacture this fence.
   Object destruction/recreation is allowed only after drain, so its token
   lifetime cannot overlap callbacks from a deleted object.

The fixed FIFO capacity is the isolated V97C experiment's 2048-byte contract,
not a capability inferred from the production JPEG FPGA. The portable methods
have no clock, scheduler, sockets or PSRAM dependencies. The adapter must supply
finite timeout/abort policy and actual status/completion callbacks.

## Evidence and limits

`vectors.tsv` is one frozen byte corpus consumed by independent Python and Rust
readers; `vectors.json` lists cases and outcomes. It covers both payload sizes,
maximum JPEG length, all setup truncations, malformed fields, explicit research
admission/rejection, start/final loss, CRC corruption, stale IDs/epochs, wrap,
timeout, core change and recovery after errors. Legacy Python MSV1 controls and
the unchanged Rust MSV1 tests execute in the same campaign.

Native tests additionally exercise bounded/aligned storage, exact 1/2/3-byte
final lengths, two outstanding staging slots, held/out-of-order ACKs, FIFO debt,
stale asynchronous status, backpressure retries, every reset phase and explicit
ingress commit ACK fencing. Native `Gateway` size plus 1432-byte receive budget
is reported in `native-metrics.json`; this is the host ABI, excludes thread
stack/socket/RTOS/DMA descriptor overhead, and is not measured ESP32 RAM use.

The ordinary protocol trace compares independently retained golden payloads
against the actual Rust stages. The FFI campaign also pins real 720x480 host
JPEGs and a retained CS92 packet, with research admission explicit. Its C ABI is
specified in `protocol97_c.h`; valid pointer/storage lifetime rules apply and
null/length guards and unwind containment protect ordinary malformed calls.
Native host checksum/packetization/copy costs use real retained payload bytes;
source capture and codec preparation are not measured by this protocol runner.
The separate host preparation study supplies its own scope and measurements.

No result here establishes 30 fps hardware service, less than 10 ms device
latency, safe path MTU, Wi-Fi retries, ESP32 interrupt contention, PSRAM effects,
QSPI arbitration, audio/UI/input service, decoder correctness or frame
publication. Those remain integration/calibration gates.
