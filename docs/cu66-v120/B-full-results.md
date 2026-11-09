# V120 B: full decoder and actual transport results

Range-plus-admission B passed the fresh full-decoder and actual V97 RTL transport campaign. An independent audit passed **395 checks**. All four stdout and expanded event streams match V119 byte-for-byte, including ordering and cycle fields. All 48 canonical records match V113 and the independent fixture goldens.

Evidence:

- Selector: `experiments/python-gamebub-v120/repair-study/spatial/results.json`
- Receipt: `experiments/python-gamebub-v120/repair-study/spatial/attempts/20261109T202426689356Z/receipt.json`
- Audit: `experiments/python-gamebub-v120/audit/B-full-terminal.json`
- Audit SHA-256: `0b851e64bc09b6fce5a28dde134c8703c5bf7c920d94c94502e56d46cfb22ef2`

The selected 18-source map differs from A only in admission: SHA-256 `275071538fd2de34246bad17ddbeb170f356e8f41e6162969b7a97ab3f45ef3f`. B retains range A, adds the existing-phase full35 header-total equality payload and replaces its original header-check consumer. It selects neither the address nor context-terminal proposal.

The audit verified 59 current source pins and consumed snapshots, 64 retained artifacts, 22 actual compile input files, lossless admission packaging and both executed binaries. The focused admission PASS is pinned to the same source. Original full-bench, transport, admission-monitor and clock-hook source hashes remain identical to V119; reversible historical adaptations and original checks remain intact. Both fresh RTL models use assertions and fatal warnings; the decoder bench and standalone transport adapter retain explicit C++17/O2/Wall/Wextra/Werror flags.

| Executed stream | Seed | Coverage | Ordered event records |
| --- | --- | --- | ---: |
| Full decoder | 107601 | 22 profiles; 21 directed checks | 378,996 |
| Full decoder | 107602 | 22 profiles; 21 directed checks | 378,996 |
| Actual V97 transport into decoder | 107601 | 12 successful profiles; 2 abort/reset retries | 326,646 |
| Actual V97 transport into decoder | 107602 | 12 successful profiles; 2 abort/reset retries | 326,646 |

All **1,411,284 retained event records** preserve exact prior bytes and scheduling. Terminal verdicts and original held-transfer, owner, error-priority, finite-memory-service and physical-drain checks remain exact. Each transport seed retains 16 command accepts, child deliveries, poisoned command tuples, wrong DMA tokens and wrong completion tokens.

Every stream produces 12 canonical records containing 518,400 pixel bytes each. The total is **48 records / 24,883,200 pixel bytes**, repeating six controlled fixtures across two memory profiles, two seeds and two adapters. These are not 48 distinct gameplay frames. Natural full-decoder traffic gains no priming clocks; the explicit prepared-fixture predecessor clocks belong to the separate focused unit proof.

This establishes functional and public-cycle equivalence for B in the tested models. Its single additional source payload bit is not a measured physical FF count. LIVE-parent qualification and the declared B100/B125 implementations remain separate gates; no routed clock, board bitstream, sustained hardware 30 fps or under-10-ms decoding claim follows from this PASS. Native Sunshine, ESP32 firmware/Wi-Fi/QSPI, real memory and panel timing remain outside this campaign.
