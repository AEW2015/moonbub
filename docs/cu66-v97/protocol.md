# V97 transport and forwarding contract

This is a candidate protocol and portable component contract. MSV1/JPEG remains
the deployed worker path. A setup ACK from the V97 parser/adapter is required
before any V97 data. Exporting `protocol97` in the firmware module does not wire
it into the Wi-Fi worker or install a new FPGA core.

## Setup and capability agreement

All wire fields are big endian. SETUP and ACK each occupy exactly 40 bytes:

| Offset | Bytes | Meaning |
|---:|---:|---|
| 0 | 4 | Magic `MB97` |
| 4 | 1 | Version 97 |
| 5 | 1 | Kind: 1 SETUP, 2 ACK |
| 6 | 2 | Exact setup length 40 |
| 8 | 4 | Nonzero session epoch |
| 12 | 4 | Profile ID |
| 16 | 2 | Coded width 720 |
| 18 | 2 | Coded height 480 |
| 20 | 4 | Complete payload cap |
| 24 | 2 | Fragment payload, 1,024 or 1,400 |
| 26 | 2 | Flags, zero |
| 28 | 4 | Sink capability agreement |
| 32 | 4 | Nonzero core generation |
| 36 | 4 | Reserved, zero |

The normal parser configuration supports JPEG profile 1 with a 262,144-byte
cap and JPEG capability 1. Opaque CS92/CS94/CS95/CS96 IDs use their ASCII four-byte
value, a 49,152-byte cap and capability 2 only when the receiver is explicitly
configured for that exact research profile. This does not implement any custom
decoder, reference recovery or publication. The runtime does not advertise them.
An unknown profile, unsupported canvas/cap/flags, malformed length or wrong core
generation is rejected. The host requires an exact matching ACK. Repeating an
identical setup preserves history; changing it requires the epoch/drain contract.

A real firmware adapter must obtain and validate actual core identity, version,
FIFO capability/capacity and generation **before** acknowledging setup. The
standalone RTL exposes the `V97C` capability contract; it is not mapped into the
existing production QSPI register interface. The old core's `BASE+0x0c` is bytes
remaining in the current JPEG frame, never a true FIFO-free measurement.

## Data datagrams

The common fragment header is 12 bytes: epoch/u32, frame ID/u32,
fragment index/u16, kind/u8 (3 DATA), flags/u8. SOF=1 and EOF=2; other flag bits
reject. Index zero additionally carries complete length/u32, CRC32/u32 and
capture timestamp/u64, totaling 16 extra bytes once per frame. There is no
standalone frame-start dependency.

The offset is `index * negotiated_payload_size`. Payload length must equal the
minimum of that size and the exact remaining bytes, including the final tail.
SOF is legal exactly at index zero; EOF must match exact complete length.
Fragments are strictly ordered. Loss, reordering, duplication, invalid lengths,
wrong epoch or CRC failure invalidate the incomplete frame and require a
proper downstream abort/drain. Frame IDs and session epochs use wrap-aware
half-range ordering. A session reset must not revive old readbacks or ACKs.

The streaming Rust receiver retains metadata and two fixed aligned 1,400-byte
stages, rather than a compressed frame. Four-byte storage alignment can add zero
padding internally, but `transfer_bytes` exposes **exact logical length**.
Padding is not codec data and must not be sent by SPI. PC preparation can retain
complete encoded frames; its latest-unsent queue holds one and replaces stale
work. That PC policy is synchronous, not the production capture/UDP worker.

## Credits, completions and abort

FIFO credits must account for ready, reserved and in-flight logical bytes.
A completion frees a staging slot; it does not manufacture FIFO capacity.
Credit queries bind the current epoch and core generation. Asynchronous query
responses use single-use probes and conservatively charge outstanding data plus
bytes completed since the query was issued. Invalid, stale or oversized status
must not inflate available credit. A real asynchronous SPI implementation still
needs to preserve the query/issue ordering specified by that API.

The standalone FPGA ingress has 2,048 bytes of actual FIFO storage and two
held descriptor slots, with a maximum 1,400-byte logical DMA. Its tokens are
separate from the Rust gateway's serial numbers; the bridge must map and retain
both identities. ACK retirement and sink consumption are explicit events.

A successful Rust completion means authoritative acceptance of the exact logical
bytes at the advertised downstream boundary, in issue order. Merely submitting
a host DMA or leaving data in an unaccounted CDC queue does not satisfy it.
After CRC completion and all transfers retire, `take_commit` authorizes an
**ingress commit request**. It retains frame ownership until a matching epoch,
frame ID and core-generation commit ACK. That ACK is distinct from a complete
codec's C2/HUD/root/seal validation, accepted reference or display publication.
The RTL also requires exact byte count, matching CRC, drain and retired ACKs.

Abort, timeout, core replacement and reconnect stop new work, invalidate pending
commit permission, and fence old completions until the downstream drain/reset
contract closes. Already accepted data may have reached a provisional consumer;
the sink cancellation signal must invalidate that partial transaction. Neither
side may treat partial drained data as a published frame.

A caller receiving `WouldBlock` must retain the current datagram and retry it
before reading later packets. A UDP socket cannot backpressure the radio merely
by withholding this call. The future adapter must bound its receive/mailbox
storage, pace the host and account for drops, CPU/UI/audio/input contention and
loss recovery. The portable API and native loopback tests do not measure those
services.

## Verification boundary

Python packetization, independently compiled native Rust parsing/gateway state
and actual Verilator FIFO/CRC/credit logic have separate receipts. Open-loop
Rust operation traces test replay only. An interactive C-ABI bridge additionally
feeds actual RTL credits/ACKs back into the portable Rust gateway; its native
host execution is not an ESP32-S3 emulator. The bridge is a test adapter, not a
QSPI/ESP-IDF driver.

No Renode ESP32-S3 firmware run, Wi-Fi/FreeRTOS execution, target heap fit,
physical DMA allocation, QSPI electrical timing/CDC signoff, complete decoder
latency or hardware cadence follows from these tests. Those remain integration
and calibration gates.
