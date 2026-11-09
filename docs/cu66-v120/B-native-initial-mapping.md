# V120 B: initial native results and mapped timing cut

B’s initial 100-MHz implementation passes internal OOC timing. Its 125-MHz implementation fails. The 100-MHz result still requires the independently launched same-source repeat before handoff qualification.

An independent terminal audit passed **1,505 checks** across both sealed initial runs, including source/snapshot/tool/recipe/proof pins, 220 retained and 166 external artifacts, and 900 bounded timing-path records.

Evidence:

- B125 receipt: `experiments/python-gamebub-v120/repair-study/native/20261109T205145239583Z/receipt.json`
- B100 receipt: `experiments/python-gamebub-v120/repair-study/native/20261109T205145534717Z/receipt.json`
- Audit: `experiments/python-gamebub-v120/audit/B-native-initial.json`
- Audit SHA-256: `fcbdd8a6a97d1072f4a8faf50abf5bf3e6a95848f39faae3fe1612a7d243a7b9`

| Metric | B100 initial | B125 initial |
| --- | ---: | ---: |
| Period | 10.000 ns | 8.000 ns |
| WNS | **+0.174 ns** | **−1.517 ns** |
| TNS | 0 ns | −3,931.934 ns |
| Failing setup endpoints | 0 | 10,524 |
| Hold slack / failing endpoints | +0.028 ns / 0 | +0.082 ns / 0 |
| Pulse-width slack / failing endpoints | +3.750 ns / 0 | +2.750 ns / 0 |
| Routing errors | 0 | 0 |

Both runs use the same 18-source B map and frozen Vivado 2026.1 implementation recipe. Each starts from RTL with its declared clock loaded before synthesis. No source change, timing exception, strategy sweep or guessed I/O delay was introduced.

## What survived mapping

Both synthesis and routing retain exactly **one named `prepared_header_total_matches_reg` FDRE** per clock. Its routed locations are `SLICE_X10Y127` at 100 MHz and `SLICE_X63Y113` at 125 MHz. This establishes the named predicate-register count; it does not infer a whole-design register delta from the source bit count.

The full35 equality arithmetic remains. Three named writer CARRY4 cells, ending `_reg_i_2`, `_reg_i_4` and `_reg_i_9`, appear in both synthesis and route inventories. Each complete routed design still contains **4,198 CARRY4 primitives**. B places the equality result behind the existing header-byte phase boundary; it does not remove all arithmetic from the FPGA.

The original literal total comparison is replaced only at the header-check consumer. Neither `header_packet_total` nor the new predicate register appears as a source/destination in either bounded extended top-200 sample. This demonstrates a changed critical-path ranking, not that every writer/consumer path is positive at 125 MHz. No additional targeted timing query was run.

## Remaining critical cones

At **125 MHz**, the worst path is refill queue `issued[1]` to admission RAM `ENBWREN`. It crosses request-address arithmetic (`offset + issued`), admission replay-address bounds/readiness and the RAM read-enable. Its 8.990-ns data path contains seven CARRY4 stages and five LUTs: 3.203 ns logic and 5.787 ns route.

The former header-total global worst is absent from the retained top 200, but other failures remain. B125 improves WNS by 0.330 ns and TNS by 4,813.769 ns versus A125; failing setup endpoints decrease by 7,750. These improvements do not close 125 MHz.

At **100 MHz**, the worst path is scratch `emit_bank` to a replicated scratch state-register D pin through raw/prefetch control. Its data delay is 9.771 ns: 2.189 ns logic and 7.582 ns route, with two CARRY4 stages and eight LUTs. This is the actual measured implementation result; B does not directly rewrite scratch prefetch logic.

| Source-family sample | B100 worst slack | B125 worst slack |
| --- | ---: | ---: |
| Kill | +0.622 ns | −1.357 ns |
| RAW mode | +0.214 ns | −1.462 ns |
| RAW coefficient | +0.768 ns | −0.862 ns |
| Context emitted | +0.515 ns | −1.386 ns |

The normal-50, extended-200 and four family-50 reports overlap; 900 records across the two runs do not enumerate every design path.

## Qualification boundary

The four initial source/clock trials use two compositions. The negative 125-MHz result is not repeated. Root’s watcher owns the positive B100 fresh-repeat dispatch; this audit launched no native or simulator jobs.

Until that repeat passes, B100 remains an initial timing pass. If it cannot be repeat-qualified, retain the stable V118100 source handoff. Neither result establishes complete board timing, a programmed bitstream, sustained hardware 30 fps or validated under-10-ms decoding.

The later [100 MHz handoff](handoff.md) records the separate positive fresh repeat and final qualification. This document retains the initial-run audit boundary.
