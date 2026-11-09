# V119 A final native mapping audit

The 125 MHz component target remains open. Its completed route has WNS −2.105 ns and 14,720 failing setup endpoints. The first 100 MHz route passes its internal setup, hold, pulse-width, clock-coverage and routing gates, with only +0.024 ns setup margin. A separate fresh positive repeat subsequently passed all internal gates at the same margins; see the [final handoff](handoff.md). These are final routed reports, not placement estimates.

| Fixed component target | WNS | TNS | Setup failing / total | WHS | WPWS | Internal unconstrained endpoints | Routing errors |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 125 MHz | -2.105 ns | -6185.906 ns | 14,720 / 103,689 | +0.082 ns | 2.750 ns | 0 | 0 |
| 100 MHz | +0.024 ns | 0.000 ns | 0 / 103,178 | +0.028 ns | 3.750 ns | 0 | 0 |

V118 A125 had WNS −1.499 ns and TNS −4,570.194 ns; V119 A125 is worse at the target despite preserving all tested functional schedules. V118 A100 had +0.061 ns setup margin, compared with V119 A100 +0.024 ns. This campaign does not label 125 MHz closed, change the timing period to hide the failure, or select a new B candidate.

## All 50 retained paths, grouped by actual endpoints

Each table accounts for exactly 50 paths. Counts reflect replicated endpoints and the vendor report bound; they are not counts of independent logical defects. An absent family is absent only from these retained 50 paths.

### 125 MHz

| Actual source → endpoint family | Count | Worst slack | Ranks |
| --- | ---: | ---: | --- |
| base kill to ingress prepared request addr D | 5 | -2.105 ns | 1, 2, 3, 4, 9 |
| ingress raw coefficient to scratch transfer data CE | 10 | -1.852 ns | 5, 6, 7, 8, 10, 11, 20, 42, 45, 46 |
| context emitted to error D | 2 | -1.808 ns | 12, 32 |
| base kill to parser out consumed CE | 6 | -1.803 ns | 13, 14, 38, 39, 40, 41 |
| base kill to parser state D | 1 | -1.800 ns | 15 |
| context emitted to position sel BRAM EN | 6 | -1.799 ns | 16, 17, 18, 19, 43, 44 |
| base kill to parser reservoir CE | 13 | -1.774 ns | 21, 22, 23, 26, 27, 28, 29, 30, 31, 47, 48, 49, 50 |
| admission qbuffer to state D | 1 | -1.764 ns | 24 |
| base kill to admission memory ENBWREN | 1 | -1.761 ns | 25 |
| base kill to parser cached remaining CE | 4 | -1.743 ns | 33, 34, 35, 36 |
| ingress raw coefficient to scratch transfer address CE | 1 | -1.737 ns | 37 |

### 100 MHz

| Actual source → endpoint family | Count | Worst slack | Ranks |
| --- | ---: | ---: | --- |
| ingress raw mode to scratch state | 2 | +0.024 ns | 1, 2 |
| scratch request epoch to assembler R | 26 | +0.115 ns | 3, 4, 5, 6, 7, 8, 9, 27, 28, 29, 30, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50 |
| refill offset to admission memory ENBWREN | 1 | +0.121 ns | 10 |
| transform accepted value to coefficient bank D | 2 | +0.122 ns | 11, 35 |
| producer state to ingress prepared request addr D | 3 | +0.129 ns | 12, 15, 22 |
| refill pending addr to ingress buffer bytes CE | 6 | +0.142 ns | 13, 14, 23, 24, 25, 26 |
| refill pending addr to ingress fetch index CE | 6 | +0.143 ns | 16, 17, 18, 19, 20, 21 |
| producer state to parser cached remaining CE | 4 | +0.168 ns | 31, 32, 33, 34 |

The A125 worst path is `base_kill_authorized_reg/C` → ingress `prepared_request_addr_reg[23]/D`: 14 LUT levels, no CARRY4, and 10.052 ns data delay (2.254 ns logic, 7.798 ns routing). The source FF itself has fanout 2 on this path. Its downstream eligibility/reset/ready cone crosses nets with fanouts 368, 259, 1,031 and 207. Registering the global kill again would change transaction revocation timing; the next study must separate safe payload preparation from immediate logical cancellation. See [the next ingress-control study](ingress-control-next.md).

The A125 raw-coefficient family starts in the ingress `raw_coefficient_reg[1]`, passes LUT `dbg_coef_valid_INST_0_i_18`, CARRY4s `dbg_coef_valid_INST_0_i_11` and `dbg_coef_valid_INST_0_i_4`, then context reset/running and scratch transfer enables. The worst listed payload CE has fanout 128 and 9.563 ns data delay, 72.999% routing. The actual ingress source still uses signed −2048 through +2048 comparisons at lines 474 and 642. An isolated rewrite of the scratch phase comparator would miss this upstream validity cone. The subsequent [checkpoint diagnostic](checkpoint-diagnostic-results.md) resolves the actual operands: lower `i_11/CO[3]` is `OR(raw_coefficient[9:0])`, and upper `i_4/CO[2]` is `signed16(raw_coefficient) > 2048`. The recorded fifteen LUT2 INIT values and two CARRY4 networks match those expressions for all 65,536 inputs. The general reset/abort query remains partial, and no improved RTL mapping or timing is claimed.

At A100 the worst two paths still start at upstream ingress `raw_mode_reg` and end in scratch state replicas, with three CARRY4 levels. Local scratch compare-before-select therefore did not prove removal of the upstream raw-mode mux/control family. It does not appear in the bounded A125 top 50 after routing; that does not establish its elimination.

## Output-plan mapping

Both actual routes retain **19 FDREs**, rather than the source struct’s 88 bits: one `last_block`, sixteen `next_block` and two `next_state` bits. The epoch, block identifier, block limit and raw-mode certificate fields optimize away. Each route’s matching output-plan cone contains 6 CARRY4, 5 LUT6, 2 LUT1 and 1 LUT4 cells in addition to those 19 FDREs. Those preparation arithmetic cells must not be described as removed.

No `output_plan` endpoint or old `output_block` → `return_state` path appears in either retained top 50. This supports deprioritizing another output-plan rewrite until a routed causal path justifies it. It does not establish a bound on every output-plan path.

## Retained evidence and scope

The [machine mapping audit](../../experiments/python-gamebub-v119/audit/native-mapping.json) passes 43 checks. It retains all 100 ranked paths, source/destination names, logic and routing delays, carry pins, data-net fanouts, family ranks/counts, actual mapped FF rows and SHA256 pins. It verifies final route receipts, fixed clock-before-synthesis, unchanged source/recipe snapshots, real synthesis, successful tool exits and matching retained report hashes.

- 125 MHz: [receipt](../../experiments/python-gamebub-v119/integrated-study/native/20261109T171305710307Z/receipt.json), [final setup paths](../../experiments/python-gamebub-v119/integrated-study/native/20261109T171305710307Z/reports/route-setup-paths.rpt), [mapped predicates](../../experiments/python-gamebub-v119/integrated-study/native/20261109T171305710307Z/reports/route-local-predicates.tsv), [timing summary](../../experiments/python-gamebub-v119/integrated-study/native/20261109T171305710307Z/reports/route-timing-summary.rpt).

- 100 MHz: [receipt](../../experiments/python-gamebub-v119/integrated-study/native/20261109T171312690398Z/receipt.json), [final setup paths](../../experiments/python-gamebub-v119/integrated-study/native/20261109T171312690398Z/reports/route-setup-paths.rpt), [mapped predicates](../../experiments/python-gamebub-v119/integrated-study/native/20261109T171312690398Z/reports/route-local-predicates.tsv), [timing summary](../../experiments/python-gamebub-v119/integrated-study/native/20261109T171312690398Z/reports/route-timing-summary.rpt).

Both receipts are `COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN`. The internal component pass on A100 is distinct from complete design signoff: this OOC top deliberately lacks external board I/O timing, and no bitstream or hardware test was performed. Functional evidence remains the exact tested V118 public bytes/events/cycles in the full and LIVE campaigns. It does not establish an actual 100/125 MHz full LIVE parent, sustained hardware 30 fps, or validated under-10-ms decoding. The completed positive A100 repeat is recorded separately in the [handoff](handoff.md) and final native audit.

A subsequent [read-only checkpoint diagnostic](checkpoint-diagnostic-results.md) resolves the measured two-CARRY raw-coefficient cone specifically as `signed16(raw_coefficient) > 2048`, using actual LUT INIT values and wiring plus exhaustive 65,536-value interpretation. Its general reset/abort connectivity remains partial, while the two carry-input networks and all twelve selected control-net load counts are complete. This refines the earlier source hypothesis without changing any native source, recipe or physical result.
