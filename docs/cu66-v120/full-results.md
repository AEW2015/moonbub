# V120 range A: full decoder and actual transport results

The isolated range-prefix candidate passed the full decoder and actual V97 RTL transport campaign. An independent read-only audit completed **392 checks** against retained files, current sources, consumed snapshots and exact prior controls. No additional simulation or implementation jobs were launched by the audit.

Evidence:

- Selector: `experiments/python-gamebub-v120/integrated-study/spatial/results.json`
- Terminal receipt: `experiments/python-gamebub-v120/integrated-study/spatial/attempts/20261109T185659349890Z/receipt.json`
- Independent audit: `experiments/python-gamebub-v120/audit/full-terminal.json`
- Audit SHA-256: `ed880be1709d530130544b54e6bbe16fc7ec9a8c210bb4cf0f05c2f69bb21ba5`

## Selected source and verification scope

All 18 production source origins match the selected V119 map except `br88_packet_ingress_sync_v91h.sv`. Its V120 SHA-256 is `82f6e3be050d0848e0d9e29439ac31a1a78e981f3a5b9f74f2b6180925c6a2e4`. The only production change is the signed-16-bit range-prefix predicate at the existing RAW output-valid and error-5 rejection sites. Optional address-owner and context-terminal proposals are not selected in this campaign.

The audit verified 59 current source pins, their 59 consumed snapshots, 64 retained artifact pins, 22 actual compile input files, both executed binaries, expanded vectors, and the byte-exact split/reassembly of the admission source. The V119 full bench, transport adapter, admission monitor and derived clock-hook header are unchanged. Their adaptations from the older frozen bench reverse exactly; original checks remain present.

Two RTL models were compiled freshly: `cs88_pipeline_v91k` and `v97_forward`. Both use `--assert -Wall`, fatal warnings and compile parallelism 1. The decoder bench and standalone transport adapter carry explicit `-std=c++17 -O2 -Wall -Wextra -Werror`; generated Verilator support retains normal generator flags. All three compile logs are clear of RTL warnings/errors. Container commands retain the 2-CPU, 8-GiB RAM, 8-GiB RAM-plus-swap limits and launch memory gates. The pinned runner persists the actual-run flag before invoking a model; intermediate receipt writes were not independently sampled.

## Measured results

| Executed stream | Seed | Case/profile coverage | Ordered event records |
| --- | --- | --- | ---: |
| Full decoder | 107601 | 22 case/profile records; 21 directed checks | 378,996 |
| Full decoder | 107602 | 22 case/profile records; 21 directed checks | 378,996 |
| Actual V97 transport into decoder | 107601 | 12 successful profiles; 2 abort/reset retries | 326,646 |
| Actual V97 transport into decoder | 107602 | 12 successful profiles; 2 abort/reset retries | 326,646 |

For **all four streams**, stdout is byte-identical to V119, and decompressed accepted-event files are byte-identical, including ordering and cycle fields. All 1,411,284 retained event records therefore preserve the prior schedule. Terminal verdicts, held-output checks, wrong-token rejection, command ownership, error paths, finite memory-service checks and physical-drain checks remain exact. Each transport seed reports 16 command accepts, registered child deliveries, poisoned command tuples, wrong DMA tokens and wrong completion tokens.

Every stream produced 12 canonical records of 518,400 pixel bytes each. All **48 records / 24,883,200 pixel bytes** match both the retained V113 canonical bytes and the independent per-fixture golden values. These repeat six controlled fixtures across two memory profiles, two seeds and two adapters; they are not 48 distinct gameplay frames.

## Remaining qualification

This establishes functional and cycle equivalence for the prefix-only A map in simulation. It does not establish a routed 125-MHz clock, hardware 30 fps, or under-10-ms physical decoding. Native Sunshine execution, ESP32 firmware/Wi-Fi/QSPI, complete publication/session handling, panel output and physical memory timing are outside this campaign. Native timing, live-parent qualification and any separately qualified proposal remain independent gates.
