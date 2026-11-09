# Next budget: validated commit, not decoder-only completion

The byte-at-a-time candidate-write/ACK join is a larger immediate latency
obstacle than the proposed IDCT DSP MAC. Its current four-state single-byte
ownership protocol alone requires at least 2,242,560 cycles for the frame's
560,640 canonical/HUD bytes, even with an ideal decoder, memory response and
hash sink. At an **assumed** 125 MHz that is 17.94048 ms. Consequently a faster
IDCT alone cannot produce validated under-10-ms completion with this join
unchanged. This is a source-derived lower bound, not a newly measured design.

## Observed case and evidence boundary

The retained failed campaign at
`experiments/python-gamebub-v115/live-parent/attempts/20261109T021132736264Z`
contains an actual `live_case` PASS and RTL terminal TEST_PASS for c0_f0 /
actual_001 / seed 115701 / fast profile. The whole campaign remains **FAIL**
because its host-side elastic discard accounting was wrong. It is an observed
case, not a selected qualified result; the corrected retry is separate evidence.
No failed receipt or selected result is changed by this note.


Selected-evidence update: corrected campaign
`live-parent/attempts/20261109T024515202542Z/receipt.json` is now PASS, SHA-256
`0a4b07a9509a89100764f8d9c791a63bac8b53a2b5a9b38cc1646060e69e8663`.
Its fast first-outer-byte-to-validated-commit interval remains 3,092,122 cycles;
bounded stalled service takes 5,772,781 cycles. Each completed 1,025 actual SHA
jobs and 560,640 matching write ACKs/hash deliveries, plus the wrong-ACK retained
owner/drain and no-reset clean retry test. This upgrades the separate selected
live-parent evidence; it does not rewrite the historical failed campaign above.
The byte-join architectural floor and all larger-parent/physical-clock limits
below are unchanged.

| Observed fence/work | Actual value |
| --- | ---: |
| First accepted outer byte → validated commit | 3,092,122 cycles |
| Start → validated commit | 3,100,226 cycles |
| Canonical bytes / semantic HUD bytes | 518,400 / 42,240 |
| Candidate byte requests / matching ACKs / hash deliveries | 560,640 each |
| SHA message bytes / padded compression blocks / jobs | 628,815 / 10,298 / 1,025 |
| Commit after producer done | 271,149 cycles |

The first interval converts to 24.736976 ms only if this complete parent really
operates at 125 MHz. No such achieved clock is established. The 18-body component
native runs exclude the SHA core, validator, write/hash join, candidate-memory
path and bank publication. This live simulation uses software HUD decoding,
abstract ACK-committed memory and abstract publication; it is not physical SDRAM,
Sunshine capture, Wi-Fi, ESP32 CPU/DMA or a real display timing measurement.

The [pinned source/derivation record](../../experiments/python-gamebub-v115/inventory/validated-budget-next.json)
identifies the exact failed-run snapshots, log and arithmetic. Its SHA-256 is
`364cec6118a928c5e30c7fc517a8565b935e4b9d23f3e2d38b4b5aa3d8a5bfb5`.
It also separates the later current host driver from the failed driver snapshot.

## What the actual SHA implementation does

`cu66_sha256_bytes.sv` processes one round micro-operation on each `C_ROUND`
edge, with 64 such edges per block. A `C_IDLE` edge initializes the working
state, and `C_ADD` adds the result into the chaining state. Thus continuous
compression needs at least **66 edges per block**, not 64. The round includes
the combinational message-schedule update and T1/T2 add/XOR/rotate logic; it is
not a measured 125-MHz primitive.

The validator already instantiates `BUFFER_BLOCKS=2`. Byte absorption and
compression overlap through bounded ping-pong banks; recommending the second
bank as a new improvement would be incorrect. The frontend still accepts at
most one message or padding byte per edge. A full bank remains unavailable
until compression retires it. For long jobs with a ready source, 64-byte fills
must follow the 66-edge compression pace.

The source-defined work reconstructs the reported counters exactly:

| Job class | Messages | Message bytes per job | Compression blocks total |
| --- | ---: | ---: | ---: |
| Full 16-tile leaves | 505 | 1,075 | 8,585 |
| Partial 8-/6-tile leaves | 1 / 2 | 563 / 435 | 23 |
| Empty leaves | 4 | 52 | 4 |
| Internal Merkle nodes | 511 | 82 | 1,022 |
| HUD | 1 | 42,240 | 661 |
| Frame seal | 1 | 157 | 3 |
| Total | 1,025 | 628,815 aggregate | 10,298 |

There are 659,072 padded bytes, including 30,257 padding bytes; the round count
also happens to be 659,072 because both blocks and rounds have size 64. The
compression launch/round/add work is 679,668 edges. Since jobs are serialized
through one engine, each new job must first fill its own initial block. Adding
64 initial fill edges per job gives a conservative **745,268-edge backend
floor**, before start/result boundaries and exposed padding transitions.
An ideal-source schedule including those boundaries is about 747,322 edges.
These are source budgets, not executed optimized measurements. Do not sum all
659,072 absorption edges and 679,668 compression edges: most overlap within a
job. Decoder, byte writes and hashing also overlap with one another.

A wider SHA input may reduce frontend/control overhead, but does not eliminate
10,298 compressions. The current 66-edge compressor would remain the long-message
ceiling. Timing a modified SHA round, changing context scheduling, or adding an
engine requires its own exact-hash, resource and native timing proof.

## Why batching writes is the first useful parent experiment

`cu66_write_hash_join_v91l.sv` accepts one byte in IDLE, offers its tagged request
in OFFER, retains the accepted physical owner in WAIT_ACK, then holds the byte
in DELIVER until the validator accepts it. The next byte cannot enter until the
following IDLE edge. Even the earliest legal response therefore gives one input
per four edges. The fast test supplies a response one modeled cycle after
request acceptance; there is no hidden multi-request pipeline.

A useful next candidate packs **eight logical bytes of one 8-pixel tile row**,
with three small finite row slots so filling, a physical write owner and
ACK-retired hash delivery can overlap. Payload capacity is only 24 bytes plus
bounded descriptors. Hashing must consume the original canonical byte order,
and only after the matching successful physical ACK commits those bytes.
This is different from a serialized row wrapper that first collects eight
bytes, waits for ACK and then emits eight bytes: that would still spend roughly
18 edges per row before other overhead, almost the entire 1.25M-cycle budget.
Burst width alone is insufficient; ownership and phases must overlap.

Eight-byte transactions reduce the logical request count from 560,640 to 70,080.
A 16-byte version can reduce it to 35,040 **if** it uses the existing tile-major
physical mapping. Logical raster addresses of two successive tile rows are
separated by 720 or 360 bytes; simply issuing a contiguous 16-byte raster write
would be wrong. The existing `row_to_sdram.sv` maps canonical raster addresses
into tile-major physical storage, making those two rows contiguous physically.
Reusing that layout requires its matching reference/scanout address contract.
Alignment must be checked after physical mapping; a tile row can start at an
8-byte-offset logical raster address while its physical tile base is 16-byte aligned.
A raster-storage alternative needs coalescing/masks and special chroma row
boundaries; it is not equivalent to dividing the byte count by 16.

The existing physical candidate is not a one-cycle wide SDRAM write engine.
`row_to_sdram.sv` accepts an eight-byte logical owner, issues four x16 writes and
waits for `ctrl_idle` before returning its row response. Its controller uses
single-word writes and burst8 reads, with same-open-row write following and
refresh/recovery fences. A 16-byte logical transaction would still need eight
accepted x16 writes and their drain fence unless the controller itself changes.
The current live case includes neither adapter nor its physical controller.
Controller 100-MHz timing and a proposed 125-MHz codec domain must not be silently
collapsed into one clock; any CDC bridge must retain the same owner/drain proof.

For either width, the transaction tuple must include epoch, token, bank, base,
length/byte mask and logical byte ordinals. A wrong ACK cannot release its slot;
a matching late/error ACK must drain an aborted owner without feeding hashes or
publishing the bank. Reset cannot forget accepted writes. Multiple slots must
retire hash bytes in original logical order even if an implementation permits
out-of-order physical ACKs. Keep a finite count of accepted owners and queued
ACK-retired bytes, with exact conservation. Preserve the original single-byte
mode and its tests; add burst-mode expanded-byte value/ACK/hash checks rather
than weakening the old 560,640-byte requirement to a request-count comparison.

## The remaining tail and a concrete next gate

The current validator finishes all leaves, then four empty leaves and all 511
internal nodes, then HUD, then the seal, before commit. The observed 271,149-edge
post-producer tail is consistent with roughly 101.7k ideal empty/node edges,
169k serialized HUD byte-join edges and the seal. This is a source scheduling
explanation, not an independently instrumented attribution; a prefetched HUD
byte and job boundaries alter exact counts.

Even after an ideal overlapped row join, this same sequential validation policy
has about 145.7k edges of empty/node, HUD-SHA and seal work after canonical input,
plus final-leaf and commit fences. A practical 125-MHz source-budget target is
therefore roughly **1.10M cycles to the last canonical ACK/hash delivery**, with
full validated commit strictly below 1,250,000. A decoder-only 1.25M target leaves
no space for that tail. Incremental Merkle reduction as child digests arrive,
and a separately scheduled HUD context, could move some tail work under decode;
they must preserve the existing C2 domains, leaf grouping, child order, HUD
receipt equality and frame-seal inputs. Merely trusting the supplied HUD hash
would remove a validation check, not optimize its implementation.

The next gate should be one bounded actual-RTL row-join experiment integrated
with the existing validator, SHA and real candidate-memory owner model. Retain
all canonical bytes and the exact original C2 root, HUD digest and seal. Exercise
wrong/duplicate/stale/error ACKs, every occupied-slot abort/reset position,
backpressure, row/plane boundaries and same-object clean retries. Record first
outer byte, last canonical input/ACK/hash delivery, root/HUD/seal completion,
all drains, commit and presentation separately. Add per-state join and SHA
occupancy/stall counts so the next comparison attributes saved cycles.

Only then compare the same full parent against the current byte mode, first
under deterministic fast ACKs and then bounded memory/refresh contention. Route
that exact larger parent and physical memory/CDC integration; a component-only
clock result cannot validate this budget. Sustained distinct-frame publication
and hardware measurements remain later gates. No new RTL, simulation, timing
run or measured improvement was introduced by this study.
