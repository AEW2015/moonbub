# V70 receiver diagnostics

The owner exposes a combinational read-only `diag_address[9:0]` /
`diag_data[31:0]` interface. Offsets are bytes, aligned to four. A board control
bus still needs to connect this interface; it is not an installed MMIO driver.
`clear_fault` explicitly clears the sticky first fault; it does not reset bank
ownership, abort work or authorize generation reuse.

| Offset | Meaning |
|---|---|
| 0x000 | Magic `0x43553730`, ASCII CU70 |
| 0x004 | Diagnostic ABI version `0x00010000` |
| 0x008 | Fixed prototype capability mask `0x3f`; not live backend negotiation |
| 0x00c | Bits1:0 low two stage bits; bit2 busy; bit3 bank-aborting; bit4 error; bit5 first-fault-valid; bits15:8 last attempt's error code |
| 0x010 / 0x014 | Active generation low/high u32 |
| 0x018 / 0x01c / 0x020 | Active / accepted-reference / front frame IDs |
| 0x024 / 0x028 / 0x02c / 0x030 | Accepted / presentation-ACK / rejected / stale-completion counts |
| 0x034 | Active transaction age in memory clocks |
| 0x038 / 0x03c / 0x040 | Packet byte reads / base-stage cycles / base accepted tiles |
| 0x044 | First fault's last observed request context (24-bit address or tile tag) |
| 0x048 | First fault: bit16 valid, bits15:8 full stage, bits7:0 owner reason |
| 0x04c / 0x050 / 0x054 | Fault frame ID / generation low / generation high |
| 0x058 / 0x05c | Event sequence / overwritten event entries |
| 0x060 / 0x064 | Arrival timestamp low/high |
| 0x068 / 0x06c | Packet/metadata acceptance timestamp low/high |
| 0x070 / 0x074 | Base-tag success timestamp low/high |
| 0x078 / 0x07c | HUD semantic+transfer flags observed complete, timestamp low/high |
| 0x080 / 0x084 | Painter success timestamp low/high |
| 0x088 / 0x08c | Global commit timestamp low/high |
| 0x090 / 0x094 | Latest qualified presentation-ACK timestamp low/high |
| 0x098..0x0a4 | Accepted canonical tag, low u32 first |
| 0x0a8 | Parsed motion block size |
| 0x0ac | Packed plane block widths and low five block-size bits (diagnostic) |
| 0x0b0 | Base writer's frame ID |
| 0x0b4 | Bits5:0: read-bank-valid, bank-committed pulse, bank-aborted pulse, parser-done pulse, base-write-last, pending-valid |
| 0x0b8 | Pending frame ID |
| 0x0bc | Bytes high→low: first-fault child detail, current parser reason, current base reason, current bank reason |
| 0x100..0x1fc | Eight circular event records, 32 bytes each |
| 0x200..0x21c | Last base full SHA-256, low u32 first |
| 0x220..0x22c | Parsed canonical reference tag, low u32 first |
| 0x230..0x23c | Parsed HUD reference tag, low u32 first |

The separate `stage[7:0]` output is the authoritative full live stage. The
compact status word exposes only its low two bits; do not use those bits alone
to distinguish twelve states. The stage values are 0 IDLE, 1 PARSER_START,
2 METADATA, 3 WAIT_BANK, 4 BASE_START, 5 BASE_RUN, 6 WAIT_RGB, 7 PAINT_START,
8 PAINT_RUN, 9 COMMIT_READY, 10 COMMIT_ACK, 11 DRAIN.

Timestamps use the owner's free-running 64-bit memory-clock counter. Phase
timestamps describe the current/latest attempt; presentation may refer to a
previous accepted frame that completes independently. Bind observations to
the event generation/frame IDs, not to adjacent read times. Read a stable
snapshot or use a high-low-high sequence to detect counter rollover; no
multi-register snapshot/transport coherency is implemented here.

## Event record

For sequence `n`, read physical slot `n & 7`; verify its stored sequence still
equals `n`. Words0..7 contain sequence, timestamp low/high, generation low/high,
frame ID, `{stage,event,reason,flags}` and `{reserved8,last_request_context24}`.
Event IDs1..10 are start, metadata, base tag, HUD drain, painter result,
commit, presentation ACK, abort completion, fatal fault, software COMMIT ACK.

Only one event is stored per clock; higher-priority events replace lower-
priority simultaneous events. This is a bounded diagnostic aid, not a complete
transaction trace. It records overwrites after eight entries. Dedicated phase
timestamps and counters retain their own accounting. Captured context is the
last observed byte request or plane/tile tag; it is not always the physical
address that caused a late integrity failure.

## Error and recovery interpretation

Owner reasons include 0x01 invalid start generation/length, 0x70 HUD semantics,
0x71 HUD transfer/fence, 0x72 painter result, 0x73 reference-memory error,
0x74 qmap response identity, 0x75 packet address bounds and 0x7f watchdog.
Parser/bank reasons are stage-coded in the owner byte; retain the full child
detail at0x0bc for diagnosis. A manual precommit abort records0x80 without
classifying it as a fatal decoder error.

The first-fault record survives later attempts and faults until cleared.
Watchdog failure stops admission and enters DRAIN; it does not free an
outstanding memory operation. COMMIT_ACK can retry indefinitely after an
irreversible commit, preserving accepted state until processor reconciliation.
Neither a timer nor clearing diagnostics permits unsafe bank reuse.

`owner-control/results.json` qualifies the public records and event ring with
618 assertions. The native wire endpoint and board control driver must preserve
these distinctions when adapting the prototype to actual hardware.
