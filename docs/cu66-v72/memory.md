# V72 masked-burst memory adapters

The V72 wrapper preserves generation-qualified canonical-tile completion,
auxiliary abort/drain, exact scalar read replies and the V71 independent LCD
reader. It changes the controller transport to aligned BL8 writes with explicit
byte enables. Every successful write response means the accepted physical burst has drained
and write recovery has completed; no response merely acknowledges queueing.

## Interface

`cu72_word_bridge` retains the p0/p1 scalar `valid`, `ready`, `write`, `addr[23:0]`,
`data[15:0]` and held scalar response ports. Each client additionally drives:

| Input | Meaning |
| --- | --- |
| `pN_burst` | One for an explicit burst write; zero for a legacy scalar read/write |
| `pN_burst_data[127:0]` | Eight x16 words; word i occupies bits 16i through 16i+15 |
| `pN_byte_enable[15:0]` | Bit 2i enables word i's low byte; bit 2i+1 enables its high byte |

For explicit bursts, the request address must be eight-word aligned, the mask
must be nonzero, `write` must be one and every enabled physical word must belong
to the public memory map. Invalid requests return an error without a controller
command. The mask uses enable-one semantics; the controller converts it to
active-high SDRAM DQM suppression.

With `burst=0`, scalar writes align the controller address down to eight words,
place the x16 payload in its selected word and enable exactly those two bytes.
Scalar reads retain the one-word return contract over a cached BL8 read. Legacy
clients must actively drive the new burst fields to zero; unconnected inputs
are not an implicit compatibility mode.

`cu72_memory_system` exposes the corresponding auxiliary fields
`aux_req_burst`, `aux_req_burst_data` and `aux_req_byte_enable`. It snapshots all
fields at admission. Abort before issue cancels the request. Abort after issue
drains its accepted response, suppresses the normal reply and then signals
`aux_aborted`. An already accepted write burst is indivisible at this boundary.

## Canonical four-word rows

A 64-byte canonical tile contains eight rows of eight u8 pixels. Each row packs
into four x16 words. `cu72_tile_memory` emits one aligned, masked BL8 write per
row, reducing tile writes from 32 scalar commands to **eight physical commands**.
The row address selects mask `0x00ff` or `0xff00`; the 64 data bits shift into the
matching half of the 128-bit payload. Chroma pitch is 180 words, so alternate
rows can occupy opposite halves. All four words in the other half remain
unchanged. Reads retain the previous 32 scalar-word sequence and stored-reference
semantics.

Tile completion retains generation, bank, plane and tile index. An abort drains
an accepted row burst but issues no later row and exposes no partial tile as a
successful completion. Physical candidate words already written are not rolled
back; the outer owner must keep the aborted candidate unpublished.

## Coherency and LCD service

Writes invalidate every scalar cache entry matching the physical BL8 tag. P0
retains one cache line and p1 retains four associative lines. The independent
LCD port keeps its eight-entry elastic response buffer, at most four consecutive
LCD grants while scalar clients wait and one finite post-completion grace clock
for an adapter request gap. Scalar service resumes after finite grace even when
the LCD producer stops. Global idle remains false while an accepted response is
held.

The new controller performs eight physical beats even for a scalar fallback or
a four-word canonical row. Thus fewer commands do not mean fewer bus beats:
canonical rows use half the write beats, and scalar fallback uses one eighth.
`completed_writes` counts fully completed controller write transactions;
`model.writes` counts active-word updates, while `model.write_commands` and
`model.write_bus_beats` retain command and physical traffic accounting.

## Verification

Run `python3 scripts/cu66-v72/run_memory.py` in the existing tool-container setup.
The adapter suite exercises both Verilator and Icarus, tAC 2 ns and 7 ns, seeds
7101/7102 and continuous, request-gap and same-bank backslot-conflict traffic,
plus reset/held-response probes. Actual controller commands reach the checked
32 MiB SDRAM model; the model array is an assertion oracle and never supplies
a separate golden reference path to the DUT.

The suite checks full, half, low-byte and high-byte writes; immutable payload
snapshots; bad masks/alignment/write flags/ranges; actual eight-command tile
writes; adjacent-half sentinel preservation for both tile columns and all
planes; accepted-burst abort at all eight physical beat boundaries; the original
43 tile/auxiliary abort probes; scalar and LCD response stability; refresh;
physical high addresses; cache invalidation and bounded arbitration. A separate
direct bridge bench checks both p0 and p1 cache invalidation after masked writes
from either client, scalar fallback neighbor preservation and reset of a held
cached response.

Qualified counts, clocks, commands and source/log hashes are recorded in
`fpga/experiments/cu66-v72/memory/adapters/results.json`. These are bounded
functional simulations. They establish neither physical SDRAM timing, routed
FPGA frequency/fit, sustained 30 fps nor sub-10-ms validated target decoding.

The final reset-gated-controller campaign passes **28 adapter executions plus
four direct cache executions**. Each of the 24 normal adapter runs records 9,078
checks, 237 tile operations, 6,751 auxiliary operations, 43 original abort
probes and eight additional accepted-wide-write abort boundaries. It also checks
23 explicit burst/half-row probes and 250 LCD bursts / 2,000 returned words.
The four reset runs each hold and flush four response positions for 32 clocks,
then require four fresh bursts. Each direct cache run performs 19 checked
operations; backend/corner results agree.

| Concurrent LCD pattern | Best line | Worst line |
| --- | ---: | ---: |
| Continuous requests | 1,432 clocks | 1,440 clocks |
| One-clock adapter gap | 1,475 clocks | 1,481 clocks |
| Gap plus same-bank backslot conflicts | 1,586 clocks | 1,590 clocks |

The configured 100 MHz memory clock makes the worst tested line **15.90 µs**,
within the native **18.425378 µs** period. Each run asserts a conservative
integer limit of 1,842 clocks. This bound covers the stated traffic and response
assumptions, not arbitrary stalled consumers or physical real-time behavior.

Each normal run records 7,143 active-word updates, 3,700 write commands and 29,600
physical write beats. Those totals include accepted aborted work and the extra
mask/neighbor probes; they are not a codec frame bandwidth measurement. The
explicit half-row probes require exactly eight controller write commands per
valid canonical tile while verifying untouched adjacent words through scalar
readback.

`build-first.log` preserves the initial bench-only unused trace-field lint
failure. `recovery-probe-first.log` preserves an overstrict probe: the controller
had completed write recovery and legitimately started refresh before the held
auxiliary reply was observed. The final probe checks completion of the physical
write burst and tWR rather than requiring the controller to remain idle while a
response consumer waits. Neither bench correction changed adapter RTL.
