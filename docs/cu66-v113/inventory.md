# V113 read-only source and harness inventory

Inventory only: no RTL was added, and no simulation, synthesis, implementation, native build, board access, or hardware result was produced. Machine-generated source and evidence SHA-256 pins are in [`baseline.json`](../../experiments/python-gamebub-v113/inventory/baseline.json). The pins were computed from the checked-out files and the frozen V112 native input card; all 17 read-order source aliases resolve to bodies matching their recorded hashes. The source card contains 17 `.sv` sources plus one included `.svh` (18 bodies total).

## Frozen custom decoder card and actual timing cones

The routed top is `cs88_pipeline_v91k` for `xc7a100tcsg324-1`, built out of context. Its V112 card derives from V110 Count with exactly two body changes:

- `packed_scratch_v91g2.sv`: V110 cursor snapshot → `fpga/experiments/cu66-v112-control/packed_scratch_v91g2.sv` (per-bank scratch validation).
- `cs88_admission_v91i2a.sv`: V107 tables snapshot → `fpga/experiments/cu66-v112-control/cs88_admission_v91i2a.sv` (prepared admission visibility).

The remaining 16 bodies retain the V110 Count source origins. V111's rejected header variant is absent. The ordered aliases, resolved source paths, recorded/current hashes, and V112 canonical composition delta are in the JSON. The full canonical V112 proof passed for both seeds, preserving its stated public-event scope and consumed-start precondition; this is not an all-private-state equivalence or latency-changing pipeline proof.

| Actual source-bound component result | Worst routed setup path | WNS / TNS | Setup failures |
| --- | --- | ---: | ---: |
| V110 Count, 100 MHz / 10 ns | synchronous ingress `fetch_bytes_reg[23][0]/C` → `counts_reg[1][5]/CE`, 10.769 ns, 15 levels | −1.022 / −1,125.069 ns | 4,620 |
| V111 Count, 125 MHz / 8 ns | scratch `read_segment_reg[1]/C` → `busy_owned_reg/D`, 11.211 ns, 15 levels | −3.264 / −40,607.203 ns | 34,864 |
| V112 local cuts, 100 MHz / 10 ns | transform `fill_bank_reg/C` → coefficient bank word `value_reg[12]/CE`, 10.745 ns, 10 levels | −1.034 / −2,028.748 ns | 5,607 |
| V112 local cuts, 125 MHz / 8 ns | ingress context `sel_rep[1]/C` → `out_block_reg[15]/D`, 10.792 ns, 16 levels | −2.844 / −32,490.680 ns | 33,323 |

All four are component OOC results, and all listed setup results fail their target. V111 did not rerun 100 MHz; V110's 100 MHz result remains the measured control. There is no production 125 MHz decoder clock, complete CS88 parent route, or physical-rate result.

## What can drive CS88 today

The V112 harness is the closest reusable wire-level harness: [`tb_sync_adapter.sv`](../../fpga/experiments/cu66-v112-harness/tb_sync_adapter.sv) plus [`replay_dpi.cpp`](../../fpga/experiments/cu66-v112-harness/replay_dpi.cpp) serialize QSPI traffic through the actual experimental credit endpoint and bus CDC, then drive the JPEG core, tile transpose, burst memory, SDRAM model, and LCD. It bounds source residency to one event (1,039 bytes including record header), polls actual remaining-byte/FIFO-credit registers, and checks commit/abort/status. It uses ten repetitions of one JPEG fixture. **It does not instantiate CS88.** The endpoint register meanings are JPEG-specific; `0x0c` is bytes remaining in the current JPEG frame, not a generic credit contract.

The CS88 side is available as `cs88_pipeline_v91k` with its actual coefficient/ingress, inverse, reconstruction, and public memory/request interfaces. The existing [V97 transport](../cu66-v97/protocol.md) provides a useful bounded packet contract and portable Rust/Python gateway: 40-byte setup/ACK, 12-byte common fragment header, 16-byte first-fragment metadata, 1,024/1,400-byte fragment payload choices, opaque custom profile cap 49,152 bytes, and exact logical DMA lengths. Its standalone [forwarding ingress](../../fpga/experiments/cu66-v97-forward/README.md) has a 2,048-byte FIFO, two descriptor slots, cancellation/drain and ingress-only commit. It is a synchronous parallel command/DMA boundary: it is not attached to the production QSPI register map, does not serialize pins, and does not decode or publish a frame. Protocol 97 custom-profile support is research-only; it does not install a CS88 decoder.

For a bounded V113 custom run, adapt the V112 schedule/credit/transaction machinery to a separate custom sink that presents actual CS88 ingress handshakes and observes actual CS88 outputs/requests. Give the sink explicit custom-profile setup, credit, byte count, abort/reset generation, ingress-drain, frame identity, and commit/publication semantics. Retain the existing JPEG harness as its independent comparison. Do not route protocol 97 fragments into the JPEG register meanings or treat ingress commit as codec validation/publication. This is the missing adapter boundary, not existing executable functionality.

Useful retained custom-decoder fixtures and oracles include V112's two-seed canonical event logs and canonical tables, plus V110 Count's complete canonical result set. These are deterministic generated protocol/RTL traces and canonical outputs; they are not Sunshine custom-encoded frame captures. V112 harness fixtures are JPEG only. Keep fixture identities and content hashes from the pinned artifacts; do not claim distinct-content playback from repeated fixtures.

## Physical memory and lane inventory

The retained JPEG `moonshine_top` report uses 113 RAMB36 + 15 RAMB18 and 32 DSP48E1. The actual V110 custom Count OOC route uses 32 RAMB36 + 12 RAMB18 and 42 DSP48E1. The V112 local-control OOC route reports 32 RAMB36 + 4 RAMB18 and 42 DSP48E1. These are separate implementation scopes and tools/vintages. They cannot be added together or treated as available device allocation. There is no complete custom-decoder parent report showing replacement, sharing, or simultaneous JPEG fallback fit.

The selected custom component has two coefficient banks and one inverse math/result owner in the measured schedule; V110 event analysis observed peak one launched-but-unretired transform identity, while input assembly can overlap math. Two finite 64-sample result slots are a proposed V113 overlap experiment, not currently instantiated storage. The physical reports map 17 ingress/context DSPs, 8 dequant DSPs, and 17 IDCT DSPs. Existing BRAM configurations are recorded per primitive in the route RAM config TSV; the presence of two BRAM ports is not automatically two independent compute lanes because address banking, same-address conflicts, read latency, fill/write traffic, output storage, and arbitration determine usable ports.

Accordingly, 1 lane is the only existing measured compute schedule. For 2 and 4 lanes, first map the real storage banks and simultaneous accesses, then implement explicit banking/replication/arbitration and finite results, and report stalls and utilization. No per-lane throughput or synthetic-rate-to-hardware claim is supported by current reports. The board parent has one 16-bit SDRAM bus, current 100 MHz core/memory and existing 200 MHz QSPI; two SDRAM chips on that bus do not establish independent bandwidth. A future 125 MHz decoder requires a qualified CDC boundary into the memory/display domains.

## Evidence boundaries

The pinned JSON includes the V110/V111/V112 native reports, source-card mapping, JPEG parent report/bindings, V112 harness receipt, V97 protocol sources, and retained V109/V112 canonical event/golden artifacts. V112's selected full canonical proof is a source/functional result; the selected native route audits establish negative setup timing. Neither establishes whole-parent resource fit, physical QSPI/DMA execution for CS88, 125 MHz board timing, sustained 30 fps, or validated decode under 10 ms.
