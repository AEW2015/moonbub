# V91c: full BR88 chunk ingress and packed coefficient scratch

Parent: `9073cd7c99fc7d7f0fd75bc1e3c186be4c935c88` (V91b).
This checkpoint advances E1's packet integration and E6's memory-layout work.
It preserves BR88 wire bytes, quantization and intended coefficients. No board,
firmware or deployed bitstream is changed.

**Two results:** complete residual-chunk packet control now runs in RTL, and a
Python packed-scratch prototype reduces peak temporary storage from **658,432 B
to 134,352 B** across the retained corpus. These are separate qualified components;
the packed store is not connected RTL, and neither result establishes complete
frame decoding or physical 30 fps.

## Complete residual-chunk packets in RTL

The [packet wrapper](../../fpga/experiments/cu66-v91c/br88_packet.sv) receives
actual bytes, stages a bounded 49,152-byte packet, calculates CRC32 and checks
the complete BR88 header and four stream descriptors. It then autonomously
replays DC/AC contexts through the unchanged V91b controller and V91 Rice
parser. Its raw fallback emits every raster coefficient, including zeros.
External ports supply no CPU-parsed context descriptors or symbol requests.

CRC/header trust here covers a **BR88 residual-chunk packet**, not the outer
CS88 frame, reference/HUD data or publication seal. The 49,152-byte staging cap
is an explicit profile bound; it does not establish a physical BRAM ceiling or
guarantee a whole frame fits. A valid packet's outputs remain provisional until
all context ends and output acceptances succeed. The sink must discard that
epoch after a late semantic failure, reset, abort or replacement start.

Two seeds, 910232 and 910233, each pass:

- 12 actual chunk packets from four selected sources plus four synthetic coded
  and raw packets, in eight serial/word, 16/32-bit, ready/stalled configurations.
- **675,112 output/epoch comparisons** (84,389 per configuration).
- **200 directed checks** for malformed headers/CRC, length overflow, stream
  bounds/EOF/padding, runs/ranges, zero-event contexts, raw fields/ranges, the
  staging boundary, held output, cancellation edges and replacement/reset.

Seed 910233, actual packets only:

| Replay width / service | Serial cycles | Word cycles | Serial / word |
| --- | ---: | ---: | ---: |
| 32-bit, all ready | 1,003,493 | 751,062 | 1.336× |
| 32-bit, matched seeded stalls | 1,054,177 | 801,489 | 1.315× |
| 16-bit, all ready | 1,017,459 | 762,741 | 1.334× |
| 16-bit, matched seeded stalls | 1,067,898 | 813,300 | 1.313× |

The 32-bit ready result uses **25.16% fewer cycles** than its matched serial
control, and the stalled result uses 23.97% fewer. Counts aggregate 12 chunks
from four sources; they are not the latency of one complete frame. Identical
cycle-indexed input-offer/output-ready schedules drive the controls, and offered
bytes remain stable until accepted. Timing includes every edge after start
through packet completion, including byte ingress, CRC finalization, descriptors,
all context transitions and consumer stalls.

Compared with V91b's 685,304 word-context cycles on these inputs, packet ingress
and control add **65,758 cycles**, including 65,602 accepted bytes. The same
65,758-cycle addition appears on the serial side. This charges a newly executed
component rather than subtracting a speed ratio from an unrelated frame model.

**Memory-port qualification remains necessary.** The behavioral staging array
provides combinational header lookups and indexed replay reads. Its concurrent
accesses are not a demonstrated synchronous 1R1W BRAM schedule. Real banking,
read latency and arbitration may add cycles and change timing/fit; V100–V105
must map and remeasure them. Runtime serial/word modes and diagnostic counters
also remain in one experimental top. No clock frequency or resource fit follows
from these cycle counts.

- [RTL contract and reproduction](../../fpga/experiments/cu66-v91c/README.md)
- [Selected RTL receipt and retained attempts](../../fpga/experiments/cu66-v91c/results.json)
- [Frozen V88 packet goldens](../../experiments/python-gamebub-v91c/packet-vectors/index.json)

## Packed scratch designed around the FPGA consumer

The [Python store](../../experiments/python-gamebub-v91c/scratch.py) receives
the same sparse coefficient tuples, with one held input credit. It writes a
32-byte descriptor, a dense signed16 DC segment and three sparse AC segments.
Each segment is aligned and padded to 16 bytes for an explicit burst ledger.
RAW uses a dense signed16 segment. No wire syntax changes.

Each AC record reuses the block/raster address already calculated by V91b:

| Record bits | Meaning |
| --- | --- |
| 31:19 | 13-bit block index |
| 18:13 | 6-bit raster coefficient index |
| 12:0 | Signed two's-complement coefficient, restricted to -2048..2048 |

The profile supports **1–8,192 blocks** per chunk; this is narrower than BR88's
65,536-block grammar and must be explicitly negotiated/admitted. The record
avoids repeating band-width division and zigzag conversion in the proposed
scratch reader. Three bounded AC lookahead heads merge with DC into one
64-coefficient tile. Unmentioned coefficients become local zeros, rather than
external-memory clears. This merge still needs real tile-selection, transfer,
transform and stall cycles when implemented in RTL.

The prototype reuses poisoned backing storage without clearing it. It verifies
that every fetched 16-byte line belongs to the current transaction. These
line-epoch tags are host assertions, not proposed hardware RAM tags. Header and
segment completion, strict write ordering and counts establish the intended
hardware ownership contract. Scratch reads require a sealed epoch; replacement
or abort invalidates old reads. This is a single-transaction temporary store,
not an accepted reference/display frame bank.

Full-corpus qualification:

| Check | Result |
| --- | ---: |
| Sources / residual chunks | 457 / 1,371 |
| Coefficient values exactly matched | 86,444,480 |
| Sparse accepted writes | 6,393,038 |
| Packed memory-image hashes independently rebuilt | 1,371 / 1,371 |
| Maximum packed allocation, descriptor and padding included | 134,352 B |
| Maximum dense coefficient reservation | 658,432 B |
| Total segment padding across all chunks | 30,454 B |
| Maximum pending writes / write assembler | 1 / 16 B |
| Directed model campaigns / valid synthetic cases | 11 / 4 |

The two maxima occur in different chunks (C3/f28/Y packed; C0/f0/Y dense).
Their peak-to-peak reduction is 79.60%; it is not a per-chunk uniform ratio.
The selected run includes 12,785,945 seeded false-ready hold samples, then
acceptance of each write. These are functional service samples, not FPGA clock
cycles or a calibrated ESP32/network model. Four synthetic packets also compare
all-ready and stalled runs, including dense raw zeros and signed extremes.

| Logical scratch budget | Packed chunks fitting | Dense chunks fitting |
| --- | ---: | ---: |
| 64 KiB | 1,249 / 1,371 | 800 / 1,371 |
| 128 KiB | 1,368 / 1,371 | 1,022 / 1,371 |
| 256 KiB | 1,371 / 1,371 | 1,095 / 1,371 |
| 512 KiB | 1,371 / 1,371 | 1,336 / 1,371 |

The 256-KiB budget is an experimental per-chunk allocation, not proof that an
unused region exists in the board's SRAM/BRAM or controller. Arbitrary future
chunks may exceed it; admission fails before writes and needs an explicit host
split/fallback policy. Whole-system fit includes the separate 49,152-byte packet
buffer, reference/display memory, transport, transforms and all retained logic.

Logical working data is bounded at 252 B: four 16-byte read caches, one 16-byte
write assembler, a 128-byte tile, three four-byte AC heads and a 32-byte
descriptor. This excludes control, lookup tables and host proof instrumentation;
it is not a primitive/resource report.

## Memory work: capacity and bandwidth are separate decisions

Across one complete corpus replay, each stored packed line is written once and
read once: **1,434,068 16-byte bursts in each direction**, or 45,890,176 bus bytes.
This includes descriptors and padded tails, with four bounded read caches.
The selected model uses hypothetical 18-cycle reads and 16-cycle writes per
burst, giving a maximum **285,498 memory-service cycles per chunk**. This is
service work under stated assumptions, not completion latency or physical SDRAM
timing. It excludes refresh/turnaround variations, other clients, tile delivery,
computation and publication.

| Scratch architecture/control | Corpus byte ledger | Capacity implication |
| --- | ---: | --- |
| Dense clear + sparse scatter + dense read | 358,563,996 useful bytes, before burst inefficiency | Dense address reservation peaks at 658,432 B |
| Dense values with zero-default bitmap | 25,572,152 useful external value bytes; separate 10,805,560 bitmap-clear bytes | Retains dense address reservation and bitmap/port costs |
| Packed DC/AC segments | 45,890,176 addressed burst bytes | Packed peak 134,352 B; append/read streams and finite caches |

Packed storage cuts modeled bus bytes 87.20% against the dense-clear control's
ideal useful-byte count. Dense values plus a bitmap offer lower useful external
value traffic, with a larger address reservation and different control/port
requirements. Select between these using measured controller service and the
actual available memory. This study does not claim a universal bandwidth winner.

Temporary coefficient scratch is only one memory client. These counts cannot
replace V88/V90's reference-pixel, reconstruction, hash/HUD or display traffic,
or be subtracted from their complete-frame timing results.

- [Scratch results and layout/traffic ledger](../../experiments/python-gamebub-v91c/scratch-results.json)
- [Independent frozen-corpus/RTL/memory-image audit](../../experiments/python-gamebub-v91c/audit.json)
- [Combined evidence](../../experiments/python-gamebub-v91c/summary.json)

## Next integration and milestones

1. Connect packet-validated block/count/raw metadata to an RTL scratch allocator.
   The current packet top holds that metadata internally; the Python store
   obtains it from a qualified software parser. Add an explicit metadata/credit
   handshake and reject over-budget chunks before accepting sparse writes.
2. Implement the packed assembler and three-head tile merge over finite memory
   request/response ports. Test bank reuse, partial bursts, cancellation and long
   stalls with real memory latency. Include DC/AC/raw and exact memory-image
   goldens, then feed the actual reconstruction/validation consumers.
3. Advance V92's finer AB38/BR88 selection and group sizes with these memory
   costs. Preserve V91's existing native CPU reader; its word-reader candidate
   was slower on the host.
4. Keep V100–V110 for the requested 7-series mapping, placement, routing and
   timing closure. The packet buffer's read ports and scratch's controller are
   explicit work items, alongside DSP48E1 arithmetic and continuous scanout.

**720×480 sustained hardware 30 fps and complete validated FPGA decoding
strictly under 10 ms remain open.** This one related precompressed walkthrough
family and four-source RTL selection do not establish held-out content or live
ESP32/Wi-Fi/QSPI behavior. Pixel reconstruction, reference/HUD/seal service and
display are outside this checkpoint. No hardware test was performed.

## Reproduction and retained attempts

Run from the repository root. Python requires no extra packages; RTL uses the
existing `gamebub-cu66-v69-build` container with assertions, fatal Verilator
warnings, C++ `-Werror`, two build jobs and bounded watchdogs.

```sh
python3 scripts/cu66-v91c/build_vectors.py
python3 scripts/cu66-v91c/run_scratch.py
python3 scripts/cu66-v91c/run_rtl.py --seed 910232
python3 scripts/cu66-v91c/run_rtl.py --seed 910233
python3 experiments/python-gamebub-v91c/verify_results.py
python3 scripts/cu66-v91c/summarize.py --write-manifest
python3 scripts/cu66-v91c/summarize.py --check
```

Failed setup/compile attempts and successful intermediate source revisions are
retained separately. The first scratch attempt used a linear-position record;
the selected address-record version removes redundant drain address conversion.
The next receipt revision adds packed-image hashes. These are the same source
corpus, not additional gameplay coverage. Original reports and snapshots remain
unchanged. Regeneration creates new attempts; rebuild the audit and manifest to
bind them. Historical manifests describe their committed trees; shared roadmap
documents evolve on later commits.

The failed compile's duplicate text fixture is retained as its pinned compressed
input plus an exact serializer, preserving the original receipt hash without a
large redundant text diff. Existing local text is ignored and remains on disk.
`python3 scripts/cu66-v91c/retain_vectors.py --restore` recreates it; the bundle
checker verifies this representation against the original failed receipt.
