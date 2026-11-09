# V120 combined range and ingress payload unit results

The unselected combined range/address candidate passed its fresh focused RTL qualification. This closes the proposed two-field ingress payload lifetime proof for the tested domain; it does not select a physical B candidate or establish a 125 MHz implementation, sustained hardware 30 fps, or hardware decoding below 10 ms.

- Candidate: `fpga/experiments/cu66-v120-control-proposal/combined/br88_packet_ingress_sync_v91h.sv` (SHA-256 `a6a8191a8bd2ea7bcb451a88020641b0a4b6299b8a9dc73e94882a23cba7bd23`).
- Receipt: [`receipt.json`](../../experiments/python-gamebub-v120/control-proposal/attempts/20261109T192014852347Z/receipt.json) (SHA-256 `7f765b058444915f5148b09e6d862cefcc1fcf386fa8296a12869034fc83b020`).
- Selector: [`results.json`](../../experiments/python-gamebub-v120/control-proposal/results.json).
- Author summary: [`control-unit-terminal-summary.json`](../../experiments/python-gamebub-v120/audit/control-unit-terminal-summary.json). This summary is not an independent audit.

## Actual execution

All seven recorded commands exited zero. Fresh ingress models ran seeds 117901 and 117902; fresh caller models ran seeds 118001 and 118002. Assertions and original public pair checks remained enabled, and no candidate model was reused. Total qualification time was 1082.77 seconds.

| Observation | Per seed / aggregate |
| --- | --- |
| Every-edge old/new address and bounds writer checks | 86,720,225 aggregate |
| Complete live owned request tuples | 6,728,708 aggregate |
| Independent accepted-request cache captures and owned WAIT checks | 6,725,826 each aggregate |
| Synthetic canceled-unowned full32 wrap cases | 11,424 per ingress seed |
| Held replay speculative writer edges | 53,689,652 aggregate |
| Canceled initial calls / first request-response cases | 24 + 24 per ingress seed |
| Natural context error cases / nonreset retries | 32 / 80 per ingress seed |
| Inherited ingress public cycle comparisons | 59,264,449 aggregate |
| Caller dense comparisons | 9,003,776 aggregate |
| Public cycle differences / skipped pair edges | 0 / 0 |

Each ingress seed also retained the old 259 successful-packet and 84 cancellation-retry checks, 6,272 initial cases, 21,860 ready cases, and 1,920 bytecount cases. Each seed ran all 65,536 signed16 range contexts (4,097 accepted, 61,439 rejected), 36 natural range-boundary packets, and 27 prepared-RAW cancellation cases. Each caller seed passed 20 packets across two configurations, 40 case rows, 56 directed checks, 18 caller-preparation checks, and nine sync-staging checks. All four initial fetch call domains and reset/start/abort, bad-descriptor, context-fault, context-done, and held-replay speculative writer domains were observed.

## Explicit private lifetime contract

The only old candidate comparison changed was one unconditional comparison covering the two previously unreset private fields `prepared_request_addr` and `prepared_request_in_bounds`. Their unowned values may now change at phase-local writer edges under rejection or cancellation. The candidate is therefore **not** claimed to preserve every private value on every edge.

The replacement independently checks the old and candidate writers on every edge and the complete owned fetch tuple, including epoch, kind, count, base, six-bit index, continuation, band, full32 address, bounds, descriptor length and tail. The cache shadow is born only on an actual physical request, uses independent full32 address arithmetic, and validates owned WAIT consumption. No expected cache or candidate poststate is forced. The unchanged old unconditional equality still has its separate frozen A control proof, pinned by the receipt. Descriptor-tail equality, all other private comparisons, public comparisons, and old RTL assertions remain retained.

The 11,424 full32 wrap cases per seed are explicitly synthetic canceled/unowned prestates, not reachable gameplay frame claims. They exercise address wrapping without issuing physical requests or granting work. Natural packet and physical-debt tests remain separate and retain their original oracles.

## Remaining gates

Actual isolated A125 route results must justify any physical selection. A selected composition still requires its own full, peer, parent and native implementation qualification; this unit result is not substituted for those gates. The separate context-terminal predicate proposal has its own source, owner proof and unit run and is not included in this combined ingress result. The remaining global kill-to-parser enables require a separately justified ownership repair rather than reset removal or relaxed public counter checks.
