# V91l: timed tiled writes and bounded prefill retention RTL

Two former Python proposals now have separately qualified RTL component comparisons. Tile8×8 physical placement reduces candidate writes through the real controller's timed pin model. A three-plane row-retention reader halves conversion fetches under the existing converter's source-derived chroma-prefill order. The controls, native golden bytes, codec syntax and frozen SDRAM controller are preserved.

See the [summary](../../experiments/python-gamebub-v91l-tiled/summary.json), [tiled pin audit](../../experiments/python-gamebub-v91l-tiled/audit-tiled.json), [retention audit](../../experiments/python-gamebub-v91l-tiled/audit-rowpair.json), [independent geometry/order model](../../experiments/python-gamebub-v91l-tiled/audit-models.json) and [prefill contract](prefill-contract.md).

## Timed candidate writes

Both static variants use the frozen pipelined controller and pin model. Raster uses the frozen eight-byte bridge; tile8×8 changes only physical address translation and adds a mapping assertion. It keeps logical response addresses, four-word credits, cancellation prefixes, final idle drain and held-response behavior.

| Native frame | Raster placement | Tile8×8 placement | Native ACT commands, raster → tiled |
|---|---:|---:|---:|
| Key | 1,271,369 cycles / 12.71369 ms | 937,045 cycles / 9.37045 ms | 42,441 → 1,786 |
| Delta | 1,271,364 cycles / 12.71364 ms | 937,040 cycles / 9.37040 ms | 42,450 → 1,786 |

This is **26.30% fewer cycles**, or about **1.357× faster candidate writes**, at the same assumed 100 MHz. Both seeds reproduce the timing; their random unit payloads differ but the two native source frames are fixed. Each native frame writes 560,640 bytes through 70,080 eight-byte rows and 280,320 physical x16 commands. All eight complete inverse-mapped bank images match the prior canonical-plus-HUD goldens.

The first accepted native row → last matching physically drained response fence includes bridge/client scheduling, ACT/PRE/refresh and write recovery. It is replay of previously decoded bytes. **9.37 ms is not complete validated decoding latency.** Entropy, inverse/reconstruction, native HUD semantics, hashing/publication, scratch/reference/conversion/scanout traffic and arbitration with those clients are outside this window.

The final matrix is two layouts × two seeds × 2-/7-ns selected read delays. The 2-ns modes additionally replay both complete native frames; 7-ns modes are unit probes. There are 220 check entries, 320 exact controller read words, 2,242,560 native physical writes and 32 rejected corrupted trace controls. The audit replays accepted logical/physical owners, pin commands/data/timing, final drain, exact cancellation prefixes and immutable offered responses. Raw read probes include all four hardware banks and an aligned burst across adjacent mapped tile rows.

The new mapping stores Y 720×480, Cb 360×240 and Cr 360×240 as row-major 8×8 tiles within each plane, at the unchanged plane bases. HUD bytes at 518,400..560,639 remain linear. There is no new padding or candidate-bank allocation. Bank IDs 0..2 retain the old physical apertures; the caller must grant a provisional bank. This component does not enforce reference/front ownership or publish frames. The bridge derivation records the exact edits and generator; original/controller/control files are unchanged.

Divisions are literal constant 720/360 operations in separate luma/chroma branches, rather than a variable-width divider. Their combinational implementation has not been mapped or timed. The [existing manufacturer timing contract](../cu66-v91l-writepipe/timing-contract.md) still applies: single-word writes, BL8/CAS3 reads, unchanged recovery/read phase and selected functional command checks. Timed pins are not vendor/PVT simulation, routed I/O timing or board validation.

## Retention reader RTL

The [reader](../../fpga/experiments/cu66-v91l-rowpair/tile_rowpair_reader.sv) accepts tagged 16-byte canonical client requests and returns exact 16-byte logical data. It maps each request's two eight-byte fragments to aligned physical BL8 reads. In tile8×8 storage a burst contains two adjacent eight-byte rows from one tile. Retain its unused next-row fragment instead of fetching it again.

The real converter's source order interleaves Cb, Cr and Y. This replaces the earlier monotonic-plane **752-byte proposal** with three independent retention contexts:

| Data storage | Bytes |
|---|---:|
| Y next-row fragments | 720 |
| Cb next-row fragments | 360 |
| Cr next-row fragments | 360 |
| Physical burst scratch | 16 |
| Logical response | 16 |
| **Total retained-mode data** | **1,472** |

There are also 180 fragment-valid bits, row/plane tags, cursors, request/lease fields, counters and control. Existing converter buffers are additional; no reuse or whole-design resource fit is claimed. Independent mode disables retention and invalidates its one-burst scratch at each logical request, retaining 32 data bytes for scratch/output.

For both actual canonical frames and both seeds:

| Read component | Independent gathers | Retained rows |
|---|---:|---:|
| Logical 16-byte client requests/frame | 32,400 | 32,400 |
| Physical BL8 reads/frame | 64,800 | 32,400 |
| Physical payload bytes/frame | 1,036,800 | 518,400 |
| Measured component cycles, four frame/seed samples | 1,025,784–1,026,327 | 593,795–594,408 |

Cycle reduction is 42.06–42.14% under the **declared logical service actor**: eight payload cycles plus 1..5 seeded wait cycles and seeded request-ready stalls. This reader is **not joined to the real SDRAM controller or the actual converter top**. Its frame fence is after the start handshake, before the first request offer → after the last logical response ACK; driver offer/hold/ready behavior is included. It is not a packet-to-publication or hardware deadline. Do not add this table to the timed-write table or infer integrated FPS.

The ordered 32,400-address fixture is derived from the frozen converter FSM and line-reader tags. It reproduces chroma row 0/1 prefill, later interleaved chroma fills, raster luma, 360-wide chroma row crossings and the bottom-edge alias. It is not captured per-address RTL traffic. Python independently checks all 518,400 mapped bytes, the complete source byte/line order, both canonical goldens, and line-level retention counts. The C++/RTL test then consumes that exact fixture with backpressure and compares complete output bytes.

The reader owns an immutable bank/epoch/generation lease. Each plane's aligned logical requests must advance sequentially, while plane interleaving is allowed. Unsupported order, bad range/alignment or mismatched lease returns an error and invalidates the session. Cancellation/warm reset invalidates cache state, stops new requests, drains an already accepted matching burst and returns an error. Responses already offered remain immutable. A wrong physical generation cannot release the accepted owner; a later matching response drains it. Finish has priority over a simultaneous new request.

Four matched modes pass 17 checks each, including two full native outputs per mode, invalid starts/requests, generation and content changes, bank/plane interleaving, memory error, wrong response generation, cancellation before/after physical acceptance, held success/error responses and finish priority. The same-bank generation test spans a 24,480-byte prefix that includes the first differing native byte (23,293), and checks invalid validity bits at each start. The independent audit reconciles 271,528 logical and 407,244 physical transactions across all four modes and rejects 32 deliberately corrupted receipts. These are component simulation results, not formal or hardware proof.

## Next integration checkpoint

1. Implement a 16-byte BL8 read bridge to the frozen actual controller: one accepted read, all eight x16 response beats staged, immutable identity and physical idle/data-release fence before ACK or reuse. Retain cancel/drain and wrong-tag behavior. Qualify at both selected read phases/delays and under reads after writes/writes after reads.
2. Join the retained reader to that timed bridge and the frozen `canonical_rgb565_lines` converter through a bank/generation lease wrapper. Preserve full native RGB565 goldens, chroma interpolation, cancellation and all line/output backpressure. This closes an actual consumer/controller boundary, instead of repeating a logical latency estimate.
3. Share one physical controller among candidate writes, accepted-reference reads, coefficient/scratch, hash/validation and conversion/scanout. Define a finite arbitration/credit policy, display deadlines and ownership. Reuse the actual tile8×8 frame layout consistently across all consumers. Byte-control masking/RMW, RTL HUD decode/overlay and mixed-entropy fallback remain open.
4. Run the live decoder at fixed 30-Hz source cadence with distinct complete frame identities, then complete V100–V110 exact-device mapping, placement/routing, I/O/CDC timing and board tests. Sustained hardware 30 fps and every complete validated decode below 10 ms remain open.

Sunshine encoding, wire format, ESP32 execution costs and HEVC/AV1 rate/quality comparisons are unchanged.

## Reproduce

The existing `gamebub-cu66-v69-build` container supplies Verilator 5.020 and GCC 13.3.0. Tiled pins use strict timed SystemVerilog; the retention lane uses clocked C++ driving of cycle-based RTL. Both use assertions, `-Wall`, strict C++20 warnings and two compile jobs. No new warning/assertion waiver is introduced. All selected runs pin current and snapshot sources, inputs, commands, tool versions, exits, output bytes and compressed event receipts.

```sh
python3 scripts/cu66-v91l-tiled/run_comparison.py
python3 experiments/python-gamebub-v91l-tiled/verify_tiled.py
python3 experiments/python-gamebub-v91l-tiled/prefill_model.py --check
python3 experiments/python-gamebub-v91l-tiled/verify_models.py
python3 scripts/cu66-v91l-rowpair/run_comparison.py
python3 experiments/python-gamebub-v91l-tiled/verify_rowpair.py
python3 scripts/cu66-v91l-tiled/summarize.py
```

Early strict-lint/compile diagnostics and intermediate snapshots are retained. Width/unused-signal and packed-parameter issues were corrected and the final sources rebuilt; no failed attempt qualifies the result. The raster layout label's packed-string padding is stripped only when parsing that exact label; compile-time parameters and address/data behavior are checked independently.
