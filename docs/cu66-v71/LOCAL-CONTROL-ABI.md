# CU71 local hardware control ABI v1

Status: implemented RTL component, tested by `local-control03`; board/SDK link
integration pending. This is a local key/P diagnostic loader, not a negotiated
CU66 UDP format or a 25/30 fps capability. HC70/HR70 remains the processor
semantic ABI; this typed CSR link carries its real results and memory service.

The existing QSPI core window is `0xE0000000 + byte offset`. Require magic
`0x43553731` at0x000 and ABI`0x00010000` at0x004 before **any** write. Readback
must use the existing guarded-clock driver and its dummy-cycle contract.
The FPGA BIT USERCODE/USR_ACCESS will both be `43553731`.

## Mailbox and immutable staging

| Offset | Meaning |
|---|---|
| 0x008 | Local capability mask7: staging, CU66 owner, typed HUD. No network/rate claim |
| 0x00c | Bits0..7: command idle, upload ready, sealed, staging active, frame active, HUD pending, software pending, quarantine |
| 0x020 | Host command sequence, writable; monotonically increasing nonzero u32 |
| 0x024 | Command doorbell, low8 opcode |
| 0x028 / 0x02c / 0x030 | Last completed sequence / status / data |
| 0x034 | Rejected concurrent/invalid sequence count |
| 0x040 / 0x044 | Command generation low/high32 |
| 0x048 / 0x04c | Frame / reference ID |
| 0x050..0x05c | ARG0..ARG3 |
| 0x060..0x06c | TAG0..TAG3: byte0 is TAG0 bits31:24; all16 raw tag bytes in order |
| 0x100 | Upload packed word: first byte bits7:0; final word uses only remaining bytes |
| 0x104 / 0x108 / 0x10c | Actual stored byte count / packet length / actual IEEE CRC32 |
| 0x110 | Sticky staging command/bounds fault flags |
| 0x114 / 0x118 | Staging generation low/high32 |
| 0x200 / 0x204 | Write owner diagnostic byte address / read its32-bit value |

Write all fields, then sequence, then doorbell. The command captures its fields
atomically. Poll0x028 for that sequence, then read status/data. Status0 is
success;1 is pending; `0x80000001..0x8000000c` are explicit command rejections.
A retry of the last completed sequence does not execute again. Sequence wrap
fails closed. Do not modify a live command or infer completion from SPI send.

| Opcode | Operation / arguments |
|---|---|
| 1 | BEGIN: new generation; ARG0=packet bytes1..49,152, ARG1=whole-packet CRC |
| 2 | SEAL: matching generation and original ARG1 CRC; all bytes must be stored |
| 3 | START: matching sealed generation, strictly newer than prior admitted generation |
| 4 | DISCARD: matching generation, only unowned LOADING/SEALED with upload drained |
| 5 | ABORT: only busy precommit stages0..8; owner still drains and reconciles |
| 6 | CLEAR_FAULT: diagnostics only; never reset/free/reuse ownership |
| 16 | HUD_RESULT: exact request generation/frame/reference; ARG0 success bit, ARG1 word count; TAG actual semantic result |
| 17 | HUD_WRITE: exact HUD identity; ARG0 candidate word offset0..21,119, ARG1 word value |
| 18 | HUD_READ: exact HUD identity; ARG0 word offset; returned data is actual SDRAM word |
| 19 | HUD_DRAIN: exact HUD identity; ARG0 success, ARG1 words, ARG2 candidate bank; TAG verified readback tag |
| 20 | SOFTWARE_ACK: exact software request generation/frame/reference; ARG0 matching opcode, ARG1 actual endpoint success |
| 21 | PACKET_READ32: matching active staging generation; ARG0 byte address with4 bytes available; first returned byte bits7:0 |

Only upload when0x00c bit1 is set, respecting the CDC write FIFO and checking
stored count, CRC and fault counters. START locks staging; upload cannot modify
it while active. The root releases it only after the owner was busy and has
finished and its non-LCD operations/packet responses have drained. No software
release command exists. For a final partial packet read, use a prior four-byte
window and extract the desired bytes; reject attempts beyond the packet end.

## Stable processor request snapshots

| Offset | Meaning |
|---|---|
| 0x300 | HUD ticket |
| 0x304 / 0x308 | HUD generation low/high32 |
| 0x30c / 0x310 | HUD frame/reference IDs |
| 0x314 | High16 HU length, low16 original HU offset within packet |
| 0x318 | Bits1:0 candidate bank, bit2 key |
| 0x31c..0x328 | Expected tag, same raw-byte order as command TAG registers |
| 0x330 / 0x334 | Software ticket / opcode |
| 0x338 / 0x33c | Software generation low/high32 |
| 0x340 / 0x344 | Software frame/reference IDs |
| 0x350 | Bit0 busy, bits8:1 full stage, bits16:9 owner error code |
| 0x354 / 0x358 / 0x35c / 0x360 | Accepted / presented / rejected / LCD underruns |

Check pending flags and ticket before and after copying a request snapshot.
The FPGA automatically captures each ready request; the SDK must perform the
real native PREPARE/COMMIT/ABORT, not return fabricated success. Bound every
HC70/HR70 response to its request identity and check status-body identity too.

For HUD: decode original HU, verify the semantic result, transfer all21,120
words via completed HUD_WRITE operations, read them back, and compare **every**
word with the native sealed candidate. Only after complete verified equality
may the SDK use the native candidate tag in the external-write-drain ACK.
Incomplete reads, mismatches, timeouts and wrong identities must not emit a
successful drain. The FPGA additionally checks contiguous completed writes.

Lost processor COMMIT replies require STATUS/idempotent retry. Never ABORT or
RESET an irreversible commit. Memory requests that were accepted complete
normally before leases are released. No pixel-only or command-only reset is
provided by this lab ABI. A clock/transport fault quarantines new admission;
reconfiguration requires both domains/adapters flushed and a fresh generation.

## First SDK fixture worker

Use two flash-resident **original CU66 packets**, with actual original HU bytes
and the actual bounded native endpoint. Upload the key, service its HUD and
software request snapshots, verify acceptance/presentation/readback, then
repeat for its dependent P. Retain JPEG/AV defaults; use an explicit guarded
USB diagnostic command with no network capability advertisement. Do not run
this worker alongside the CPU-only W probe or an active legacy stream.

Measure upload, packet-complete, HUD CPU, transfer/readback, commit/presentation,
free/largest heap and task stack. The current scalar HUD CSR service is a
correctness bring-up path; it is not the final high-throughput burst interface.
