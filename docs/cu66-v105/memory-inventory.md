# V105 baseline memory inventory

Baseline: `afc073e36f813cbcedaec9b21b61cda239453a5b`, retaining V102 admission and reconstruction-predicate sources. This inventories the implemented `cs88_pipeline_v91k` component, with 49,152-byte packet bounds, 720×480 full-grid addresses and the synchronous child ingress. The declaration sizes below are source capacities, not BRAM estimates. A read marked combinational has no additional source register; surrounding state/handshake latency still applies.

## Admission arrays and exact V105 scope

Source: `fpga/experiments/cu66-v102-memory/cs88_admission_v91i2a.sv` (SHA-256 `c300f1bd819a906bfebd64e47648fe08d71f072d88d25cccc15c9a197d305187`). All six arrays are retained at their original depth and width.

| Array | Depth × width | Source write/read accesses | Reset and initialization | Read latency / same-edge behavior |
| --- | ---: | --- | --- | --- |
| `memory` | 49,152 × 8 | One byte write from accepted RX; one selected read, stage fetch taking priority over replay | No reset; packet bytes written before parsing | One clocked read, output holds when disabled; nonblocking RTL read sees old word on same-address write/read. V102 focused forced-collision evidence is separate from physical primitive behavior. |
| `header` | 128 × 8 | One byte write in HEADER_BYTE; multiple combinational h16/h32 and byte selections during validation | No reset; transaction header overwritten before validation | Combinational selects; parser states separate writes and reads. |
| `qbuffer` | 354 × 8 | One byte write in Q_BYTE; fixed header selections and dynamic Q_RUN read | No reset; qmap bytes written before use | Combinational selects; FSM separates population and reads. |
| `active_cell` | 1,350 × 1 | Clear or residual-mark write in distinct parser branches; one dynamic scan read | No reset; ACTIVE_CLEAR clears all 1,350 cells before parsing | Combinational scan; legitimate writing/scan states exclusive. |
| `modes` | **8,100 × 2** | Baseline five assignment sites: clear, key, mixed bit, hidden/copy group, residual group; one FINISHED lookup | **No reset**. ACTIVE_CLEAR writes all 8,100 entries to 1 for a new packet. Reset/abort retain contents. | **One clocked lookup**, held without FINISHED request, including reset/start/abort. Lookup addresses 8,100–8,191 remain unspecified/unqualified. |
| `scales` | 1,350 × 2 | External cache write plus Q_FILL write in the same clocked process; one FINISHED lookup | No reset; external preload or parser fills before qualified use | One clocked lookup, held when disabled. Same-address simultaneous external write/read returns old value in RTL. External write and Q_FILL can target distinct addresses; if same address, later Q_FILL assignment wins in source. **Unchanged by V105.** |

V105 changes only `modes`: it gives the five mutually exclusive source writes a prioritized combinational enable/address/data mux and one clocked write statement; the existing FINISHED-only registered mode read moves into that RAM process. Full-width address addition followed by the original 13-bit cast, state boundaries, guards, memory capacity and read cycle are preserved. No RAM attribute is added. The mode RAM is never reset.

Mode write/read concurrency is excluded by the source states for legitimate transactions: writes are ACTIVE_CLEAR, KEY_TILE, MODE_BIT or GROUP_TILE; reads require FINISHED. This is a source/control argument and bounded behavioral observation, **not mapped-netlist collision proof**. No physical same-address collision policy is claimed for a future mapping.

## Other instantiated buffering

Read/write counts below describe source operations and data paths, not promised primitive ports. Clocked output registers and small metadata arrays can become FFs or distributed memory; only native reports establish mapping.

| Instance / storage | Depth × width | Write/read shape | Reset and latency / collision contract |
| --- | ---: | --- | --- |
| Child synchronous ingress `memory` | 49,152 × 8 | One byte RX write; one gated synchronous fetch read | Array unreset; one-clock data read, valid cleared on cancel/context failure; source read-first on simultaneous access. RECEIVE and FETCH states separate qualified writes/reads. |
| Child `fetch_bytes` | 46 × 8 | One indexed response write; multiple combinational metadata/word reads | All 46 bytes reset on reset/abort; no extra read register; response collection precedes consumption. |
| Child `lengths`, `counts`, `offsets`, `sizes` | Each 4 × 32 | Header/descriptor-selected registers; multiple combinational selects | All entries reset on reset/abort; old register values used in a same edge. |
| Child `k0s`, `k1s` | Each 4 × 8 | Descriptor-selected write; combinational context select | Reset on reset/abort; values qualified by descriptor FSM. |
| Rice decoder `reservoir` | 1 × 64 | Packed append and consume register paths | Reset/start sets 0; combinational extraction, clocked refill/consume; source gives input-load path precedence over parser stepping. |
| Context `ZIGZAG` | 64 × 6 constant | No writes; selected combinational lookup | Compile-time constant, no runtime reset/collision. |
| Refill queue `data`, `last` | 2 × 8 and 2 × 1 | One response push at tail; combinational head read | Storage unreset; head/tail/count/pending reset or cancelled. Occupied + pending ≤ 2; simultaneous push/pop uses pre-edge head data. No independent physical RAM guarantee. |
| Packed scratch `tile` | 2 banks × 64 × 16 | One coefficient or serial-clear word write; selected combinational emitter read | Payload unreset; per-bank 64-bit validity reset/cleared before use; invalid positions emit zero. Owned-bank/validity protocol controls collisions. |
| Scratch `tile_valid` | 2 × 64 | Full-bank clear and per-coefficient bit set; combinational selection | Reset/cancel clears masks; selected old mask consumed at a clock edge. |
| Scratch `bank_block`, `bank_epoch` | 2 × 16 and 2 × 32 | Preparation metadata write; emitter select | Payload tags not globally reset; bank-ready ownership invalidated on cancel. |
| Scratch `cache_data`, `cache_address` | 4 × 128 and 4 × 18 | Indexed accepted memory-response write; selected combinational read_word/read_half | Data/tags unreset; valid/prefetch masks reset/cancelled. Response/FSM ownership determines valid access; no external memory timing inferred. |
| Scratch `counts`, `starts` | Each 4 × 32 | Begin-frame metadata loads; combinational segment selection | Loaded on accepted begin, stale entries fenced by running/ownership state. |
| Scratch `heads`, `cursors` | Each 3 × 32, indices 1–3 | Accepted sparse-word cache and cursor advances | Head-valid mask cleared on reset/begin; cursors loaded 0 on begin. Combinational reads with source-ordered clocked updates. |
| Scratch transfer staging | `assembler` 128, `transfer_data` 128, `descriptor_low` 128, `pending_record` 32 bits | Packed scalar registers, not frame stores; one transfer at a time plus held offer | Valid/owner controls cleared on cancellation; accepted external transactions drain rather than being discarded. No modeled fixed SDRAM latency. |
| Inverse stream `coefficients` | 2 × 1,024 (64 × 16 per bank) | One 16-bit part-select coefficient write; full selected bank read to dequant | Payload unreset; FREE/FILL/READY/ACTIVE ownership reset/cancelled. Completed bank held until math ownership releases. |
| Inverse `epochs`, `child_epochs`, `tokens` | Each 2 × 32 | Metadata capture at first coefficient; combinational bank select | Tags not reset; bank states invalidated. |
| Inverse `planes`, `scales`, `blocks`, `tiles`, `cells` | 2 × 2, 2 × 2, 2 × 16, 2 × 13, 2 × 11 | Same per-bank metadata capture/select | Payload tags unreset; owner validity gates use. |
| Dequant captured coefficients / output | 1 × 1,024 and 1 × 1,280 (64 × 20) | Full-tile input capture; eight output lanes per MULTIPLY edge | Both reset/abort to 0. Output held until ready. Variable eight-lane coefficient read is combinational; no source RAM port inferred by inspection. |
| IDCT `source_tile`, `intermediate`, output tile | 1 × 1,280; 64 × 24; 1 × 1,536 | Full source capture; first-pass 16 intermediate samples written per terminal accumulation edge; eight combinational samples selected for second pass; full/partial output writes | Source/output reset to 0; intermediate **unreset**, but first pass completes before second-pass use. Source-scheduled states exclude intended cross-pass collision. |
| IDCT `products`, `even_sum`, `odd_sum` | 8 × 38; 8 × 40 each | Parallel arithmetic pipeline registers | Reset/abort to 0; clocked multiply/accumulate. These are arithmetic registers, not independently addressable RAM. |
| Reconstruction `residual`, `reference_pixels` | 1 × 1,536 and 1 × 512 | One residual sample part-select write; full reference tile capture; combinational full-tile math input | Reset/cancel/start to 0; captured reference requires matched owner tags. |
| Reconstruction `residual_block` | 3 × 16 | Per-plane accepted residual tag update; selected counter use | Reset/cancel/start to 0; clocked update/combinational select. |
| Reconstruct tile `out_pixels` | 1 × 512 | Full 64-pixel elastic result register | Reset/abort to 0; one-edge result acceptance, held on output stall. |

`q[8]` (8 bits), `scaled[8]` (9), dequant `products[8]` (25), IDCT `samples[8]` (24), `next_even[8]`/`next_odd[8]` (40), and reconstruct `combined[64]` (25) are **combinational temporary arrays**, not persistent buffers. Dequant `base_quant` is a 128-entry × 8 constant case function (two 64-entry tables); IDCT basis is a fixed function. Fork block/offset/length arrays (3 × 32 each), fork entropy (3 × 2), top debug arrays and statistics arrays wire through instance outputs rather than allocating a second copy of payload storage. Scalar control counters/tags are registers, not additional video buffers.

The historical asynchronous `br88_packet_ingress` file is present in the source manifest but lies in the unselected `SYNC_STAGING==0` generate branch. Its 49,152 × 8 array is **not a third implemented packet RAM** in this baseline. The selected native hierarchy confirms the synchronous branch. No canonical frame bank, RGB565 scanout store, display line store, SDRAM controller, transport CDC or actual ESP32 storage is included in this OOC decoder component. Their capacity and service timing must be qualified in the board integration separately.

## Native V102 mapping ledger

Retained measured evidence: `experiments/python-gamebub-v102/native/20261107T213234207776Z/reports/route-ram-config.tsv`, `route-utilization.rpt`, and `route-capacity.rpt`. V105 `memory-inventory.json` pins these report hashes, source declarations and all primitive rows.

| Hierarchy | Total LUT | Logic LUT | LUTRAM | FF | RAMB36 | RAMB18 | DSP |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Top | 48,522 | 45,804 | 2,718 | 34,795 | 32 | 0 | 28 |
| Coefficients | 31,378 | 29,814 | 1,564 | 22,869 | 32 | 0 | 4 |
| Admission | 18,138 | 16,614 | 1,524 | 9,161 | 16 | 0 | 1 |
| Child | 12,724 | 12,692 | 32 | 12,684 | 16 | 0 | 3 |
| Reconstruction | 4,640 | 4,640 | 0 | 3,754 | 0 | 0 | 0 |
| Transform | 12,156 | 11,002 | 1,154 | 8,170 | 0 | 0 | 24 |

Exactly 16 RAMB36E1 instances are named `coefficients/admission/memory_reg_*`; 16 are under `coefficients/child/packet_decoder/synchronous.ingress`. All 32 ledger rows report TDP, A/B width 1, `READ_FIRST` on A, `WRITE_FIRST` on B, disabled primitive output registers and `DELAYED_WRITE` collision configuration. Source registered read latency is still one clock despite disabled optional primitive output registers. These observed settings alone do not establish all collision behaviors in a technology-timed netlist.

Hierarchy rows overlap; do not sum them. Source-bit totals do not predict primitive count. The device has 63,400 total LUTs, 126,800 FF, 135 BRAM36 equivalents and 240 DSP; LUTRAM-compatible sites share the LUT pool. V102 WNS −13.976 ns at the 10 ns comparison clock means timing signoff remains open.


## Completed V105 synthesis-only mapping

The root-owned Vivado 2026.1 build `native/20261107T233717813389Z` completed with `SYNTHESIS_ONLY_FINISHED_SIGNOFF_OPEN`, exit 0, on `xc7a100tcsg324-1`. Its post-synthesis primitive ledger contains **33 block-RAM primitives**: the original two groups of 16 RAMB36E1 packet stores plus exactly **one `coefficients/admission/modes_reg` RAMB18E1**. This verifies the mode-store BRAM inference in the synthesized component, beyond the earlier RTL-memory statistics. Original source capacity remains 8,100 × 2; the preliminary tool table's rounded “7 K × 2” label is not a source capacity change.

| Mode primitive property | Synthesized value |
| --- | --- |
| Instance | `coefficients/admission/modes_reg` |
| Primitive / mode | `RAMB18E1` / `TDP` |
| Read width A / B | 2 / 2 |
| Write width A / B | 2 / 2 |
| Write mode A / B | `READ_FIRST` / `WRITE_FIRST` |
| Optional output registers A / B | 0 / 0 |
| Collision configuration | `DELAYED_WRITE` |

The source-to-primitive match is supported by the named instance in `synth-ram-config.tsv`, the `modes_reg` inference rows in `vivado.log`, and the admission utilization row changing from 1,524 LUTRAMs and no RAMB18 to zero LUTRAMs and one RAMB18. Unchanged packet stores retain their exact hierarchy groups and widths. The source mode output still has its original registered read cycle; disabled optional BRAM output registers do not remove the primitive's synchronous read.

| Synthesis hierarchy | V102 LUT / LUTRAM / FF / RAMB36 / RAMB18 / DSP | V105 memory LUT / LUTRAM / FF / RAMB36 / RAMB18 / DSP |
| --- | --- | --- |
| Top | 49,040 / 3,854 / 34,689 / 32 / 0 / 28 | 47,482 / 2,330 / 34,672 / 32 / 1 / 28 |
| Coefficients | 30,643 / 1,566 / 22,784 / 32 / 0 / 4 | 29,071 / 42 / 22,766 / 32 / 1 / 4 |
| Admission | 18,127 / 1,524 / 9,153 / 16 / 0 / 1 | 18,041 / 0 / 9,135 / 16 / 1 / 1 |
| Child | 11,982 / 32 / 12,679 / 16 / 0 / 3 | 10,495 / 32 / 12,679 / 16 / 0 / 3 |
| Reconstruction | 4,648 / 0 / 3,754 / 0 / 0 / 0 | 4,660 / 0 / 3,754 / 0 / 0 / 0 |
| Transform | 13,371 / 2,288 / 8,149 / 0 / 0 / 24 | 13,373 / 2,288 / 8,150 / 0 / 0 / 24 |

Top delta is −1,558 LUTs, −1,524 LUTRAMs, −17 FFs, +1 RAMB18, unchanged RAMB36 and DSP count. Admission logic LUTs rise from 16,603 to 18,041 while distributed memory disappears; source-template changes also affect synthesis optimization in other hierarchy rows. Report whole-component deltas rather than treating every logic delta as an isolated RAM-cell cost. At the same 10 ns OOC clock, **synthesis WNS improves from −12.181 ns to −11.728 ns** (0.453 ns), but remains negative. This is a like-for-like **synthesis-stage** comparison, separate from the earlier V102 routed figures above.

Candidate placement and routing were not run in this lane. The primitive configuration does not establish physical read/write collision behavior, routed timing, board clock closure, external SDRAM service, sustained hardware 30 fps or under-10-ms complete decoding. Machine ledger `memory-inventory.json` pins the completed native receipt, synthesis reports, all 33 primitive rows and both same-stage hierarchy tables. Production RTL, focused bench, runner, independent auditor and seven-edit recipe remain unchanged.


## Locality composition after routing

Root-owned native locality receipt `native/20261108T001325640117Z/receipt.json` completed `COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN`, exit 0, in 809.85 seconds. Its **post-route** RAM ledger still contains exactly one `coefficients/admission/modes_reg` **RAMB18E1**, plus the unchanged 32 packet-store RAMB36E1 primitives. Mode RAM properties remain TDP, both ports' read/write widths 2, `READ_FIRST`/`WRITE_FIRST`, optional output registers disabled, and `DELAYED_WRITE`. Thus the mode-store mapping survives placement and routing in this composed candidate.

Locality combines the coordinate admission, reconstruction control, dequant DSP and mode-store experiments. Routed top utilization is 47,966 LUTs (46,772 logic plus 1,194 LUTRAM), 34,827 FFs, 32 RAMB36, one RAMB18 and 28 DSPs. Admission itself has 20,145 LUTs, **zero LUTRAM**, 9,201 FFs, 16 RAMB36, one RAMB18 and zero DSPs. Routed WNS is **−13.956 ns**, so signoff remains open; whole-component differences include every composed edit and cannot be attributed to the isolated mode-store patch.

`memory-inventory.json` field `v105_locality_route` pins the terminal receipt, input-source manifest, routed timing/utilization/primitive reports, all 33 primitive rows and complete routed hierarchy. This confirms component mapping after route; it does not establish physical collision behavior, actual external-memory timing, board I/O signoff, hardware 30 fps or complete under-10-ms decoding.
