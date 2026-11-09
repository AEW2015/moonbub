# V120 admission equality payload: focused results

The admission equality candidate passed both asserted RTL seeds. An independent terminal audit passed **305 checks** and reran all four unchanged Python replay oracles for each seed against the retained traces. Every returned coordinate, quant, scale and mode dictionary matched the recorded result.

Evidence:

- Selector: `experiments/python-gamebub-v120/admission-match/results.json`
- Receipt: `experiments/python-gamebub-v120/admission-match/attempts/20261109T201353867710Z/results.json`
- Independent audit: `experiments/python-gamebub-v120/audit/admission-match-terminal.json`
- Audit SHA-256: `ad78384d89f83a56d53d0729cf36ef6f24f5c7689d1bc3378077c79a07a8643f`

The fresh reference is the current V119 admission body. The candidate adds one unreset source payload bit for the full35 packet-total equality and changes its existing header-check consumer. The reversible production and verification recipes, all eight original RTL assertion blocks, 76 legacy and 28 owner `require` expressions, source/snapshot/artifact pins, consumed compile units and executed binary were checked. Strict asserted Verilator compilation and both successful model invocations were verified.

| Coverage | Per seed, 120501 and 120502 |
| --- | ---: |
| Original packet cases / directed checks | 86 / 44 |
| Original chunk boundary cases / cancellations | 25,344 / 294 |
| Original mode-owner cases | 540 |
| Full35 capture contexts, including random samples | 67,664 / 65,536 random |
| Canceled capture edges | 59,206 |
| Coherent prepared header consumes | 4,096 |
| Independently checked writer edges | 278,850 |
| Reset/IDLE payload-hold edges | 135,328 |
| Separately counted fixture predecessor clocks | 240,458 |
| New natural malformed packets / clean nonreset retries | 36 / 36 |

The two legacy preparation call sites execute a genuine final `HEADER_BYTE127` edge in both models before synthetic `HEADER_CHECK` consumption. They do not force the predicate or restore poststate, error or counters. These added fixture clocks are explicit and are not added natural packet latency. Original natural traces remain intact for the four Python replay oracles; new malformed-packet traces are retained separately.

The full35 tests are finite samples, not exhaustive testing of all 2^35 values. Raw capture contexts reset before consumption; coherent prepared consumes and natural packets are separate test domains. Only one additional **source payload bit** is established here: physical FF count, synthesis replication, routing, full-component/peer/LIVE qualification and hardware throughput remain separate measurements. A100 handoff qualification remains independent.
