# V73 wide reference rows and p0 working-set cache

V73 retains V72's masked BL8 controller/model, write service, byte order and
memory map. The change is the reference-side service: one accepted operation
returns the aligned eight-word line, and the tile adapter consumes its four
useful words together. An eight-row fully associative cache retains the working
set needed by adjacent 8×8 tiles. Controller commands still serialize with the
existing elastic LCD client and guarded auxiliary client.

## Interfaces and ordering

`cu73_memory_system` preserves the V72 external tile, auxiliary and LCD ports.
`P0_CACHE_LINES` selects 1 or 8, default 8, and is passed to `cu73_word_bridge`.
The one-line setting provides an A/B control with the same wide-row protocol.
The controller and model remain frozen `cu72_sdram_controller` and
`cu72_sdram_model`; this iteration does not change the physical write protocol.

The bridge adds:

| Signal | Contract |
| --- | --- |
| `p0_read_burst` | Marks a wide reference-row read. It is illegal with write or write-burst flags. |
| `p0_addr[23:0]` | Actual four-word row start, whose low bits are 0 or 4. The containing BL8 goes to the controller aligned to eight words. |
| `p0_rsp_burst_data[127:0]` | All eight aligned words, low-address word in bits 15:0. It is valid with the normal p0 response and remains held until response consumption. |
| `p0_rsp_data[15:0]` | The selected scalar word remains available and agrees with the row start in the wide payload. |

A rejected wide request returns an error and a zero wide payload without issuing
an SDRAM read or write. The containing eight words must be within the mapped
allocations. Scalar p0 reads and scalar/wide writes remain supported.

A miss captures all eight returned beats, including the final beat, before
exposing the response. A hit copies all eight words from the selected cache line
into the held response snapshot. The read pointer advances only after the full
response handshake. Writes invalidate every aliasing physical BL8 tag in all
p0 and p1 cache entries before issuing the accepted write, and later requests
cannot overtake that transaction. The p0 cache uses round-robin replacement on
miss; hits do not alter its replacement pointer.

The tile reader makes eight row requests instead of 32 scalar requests for one
64-byte tile. Each reply contributes the lower or upper four words according to
the actual row address's bit 2, which matters for chroma pitch 180. The tile
writer still makes eight masked four-word row writes. Tile metadata and the
512-bit final result remain generation/bank/plane/index qualified. Abort drains
an accepted operation and suppresses normal completion; reset flushes the whole
adapter/cache/response state. No accepted operation is reported complete merely
because it was queued.

The one-line cache uses explicitly sized data/way indices. An initial strict
cache-one lint run detected five width-truncation diagnostics; the final casts
select three data-index bits and one way-index bit for that configuration and
six/three bits for eight lines. The default-eight behavior is unchanged. The
failed logs and the root's superseded source/result archive are retained.

## Profiling

All nine added counters are unsigned memory-clock counters, reset by global
reset. They do not affect arbitration, data or completion.

| Counter | Exact event |
| --- | --- |
| `p0_cache_hits`, `p0_cache_misses` | Valid p0 cache read hit / controller-backed read miss, scalar or wide |
| `p1_cache_hits`, `p1_cache_misses` | Corresponding p1 read events |
| `p0_row_reads` | Accepted p0 requests flagged as wide-row reads, including rejected malformed flag combinations |
| `p0_wait_cycles` | p0 request valid while its ready is false |
| `p0_service_cycles` | Bridge transaction active for p0, excluding LCD ownership; includes response holds |
| `p0_read_wait_cycles` | p0 wide-row request valid while ready is false |
| `p0_read_service_cycles` | Active non-write p0 transaction, excluding LCD ownership; includes response holds |

The per-client hit and miss sums equal the existing aggregate counters. The full
system's valid reference traffic can use row counts and wait/service intervals
directly. A scalar-to-wide comparison must not compare hit ratios in isolation:
V72 counted three scalar hits within an already-fetched four-word row; V73 removes
those requests. Compare actual miss commands, returned bytes and charged cycles.

The declared p0 cache payload grows from 16 bytes to 128 bytes; its held wide
response adds 16 bytes. Tags, valid bits, counters and control storage are
additional. These are source-level capacities, not inferred FPGA BRAM or FF
counts, mapped resources or a fit/Fmax result.

## Regression

Run `python3 scripts/cu66-v73/run_memory.py` using the existing shared tool
container. The runner retains source pins, exact commands, raw logs and normal
terminal result counts, and uses one compile job per distinct build directory.
It reuses the checked 32 MiB controller model rather than injecting golden
reference pixels or a modeled always-ready memory service.

The V72-derived campaign retains 24 concurrency schedules, four coordinated
reset schedules and four masked-cache-alias runs over Verilator/Icarus and tAC
2/7 ns. Additional row-working-set tests cover cache capacities 1/8 on both
simulators and both corners. They initialize memory through actual controller
writes, test held 128-bit snapshots for 32 clocks, selected-word consistency,
last-beat capture, row reuse and round-robin eviction, mixed-byte cross-client
invalidation, invalid requests with no controller issue, and reset followed by
fresh read progress.

For eight luma rows at pitch 360, the first tile requires eight read bursts.
Its adjacent tile reuses all eight lines with the eight-line cache, while the
one-line control requires eight new bursts. Chroma pitch 180 alternates halves:
the adjacent tile requires four new bursts with eight lines and eight with one.
These are bounded component traces, not a physical frame rate or a universal
worst-case deadline proof. Full packet/reference/HUD/painter/LCD integration and
its cadence and target timing scopes are reported separately by the root.

The directed row probes intentionally hold each response for 32 clocks; their
`first_cycles`/`second_cycles` fields are test durations including that hold,
not decoder latency. Their first/second luma and chroma miss counts are captured
before the final reset. The printed p0/cache/controller counters at the end are
post-reset fresh-read counters, not totals for the entire probe. This explains
why the final row record can show one miss and zero hits even when its saved
adjacent-tile miss count proves cache reuse earlier in that same execution.

## Final component evidence

All **40 executions pass**: 28 adapter/reset, four masked scalar/cache alias,
and eight wide-row/cache-capacity runs. Both simulators and both tAC corners
agree for each identical input schedule. The final source/log audit rehashed
10 source pins and 56 qualified command logs.

Each normal adapter execution retains 9,078 checks, 237 tile operations,
6,751 auxiliary operations, 43 original abort probes, eight accepted-wide-write
abort boundaries, 23 masked/half-row probes and 250 LCD bursts / 2,000 words.
The wide-row cases each perform 68 checked operations and 42 flagged wide-read
requests across reuse, eviction, invalid requests and reset.

| Concurrent LCD scenario | Minimum line clocks | Maximum line clocks |
| --- | ---: | ---: |
| continuous | 1412 | 1440 |
| bubble | 1468 | 1491 |
| bank3-conflict | 1562 | 1594 |

The worst tested line is **1,594 clocks / 15.94 µs**, within the configured
**1,842.5378 clocks / 18.425378 µs** native line period. Each normal run also
asserts the conservative integer bound of 1,842 clocks. The result is bounded
functional component evidence, not arbitrary-access or physical deadline proof.

The final bridge SHA-256 is
`c9c920bad93d5b4315263ae8b6d146194f0760d954802f7f890a178bff16ad3b`.
`memory/adapters/results.json` contains the commands, hashes and all result rows.
