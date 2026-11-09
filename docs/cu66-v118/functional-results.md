# V118 full-component functional results

The fresh18-source V118 composition passed both the full canonical decoder bench and the actual V97 forwarding RTL/custom transport adapter using strict Verilator assertions and compiler warnings. This verifies the new residual pipeline and four-beat copy together with the spatial scratch changes. The new schedule is explicit: accepted residual E, registered validation E+1, commit E+2; four real128-bit canonical writes replace a single512-bit copy. Exact V117 cycle equality is not claimed.

| Evidence | Result |
| --- | --- |
| Actual source contract |17 SystemVerilog modules plus quantization ROM,18 aliases |
| Full decoder profiles |44 across seeds107601 and107602 |
| Full decoder directed checks |42, including held outputs, cancel/reset, physical debt and retry |
| Actual V97/custom transport successful profiles |24 |
| Transport abort/reset retry cases |4 |
| Complete canonical output records |48 ×518400 bytes =24883200 exact bytes |
| Successful accepted semantic events independently compared |1306584 |
| Decoder dense/dequant/residual comparisons |4058368 per metric per seed |
| Transport maximum descriptors / reserved bytes |2 /2048 |

The independent expert audit verified every selected source, snapshot and artifact hash; all18 aliases and their source origins; the unchanged established whole-component bench; strict compile flags; and successful raw terminal records. Every complete canonical record was compared directly to the independent pixel golden, including order and all518400 bytes.

Successful event records matched V117 exactly after removing only cycle timestamps. The audit additionally checked event order separately within each type/stage/frame/profile stream, retaining transform assembly/dequantization/residual, canonical and reference-request ownership/value records. Interstage interleaving is allowed to change with the declared pipeline. Existing independent ordered data, held tuple, first-fault, physical acknowledgement and retry checks in the compiled bench remained active. The old exact-cycle checker remains unchanged in its V117 location.

For context, the fast `actual_001` full-component case took1006697 cycles and `actual_031` took1322195 cycles from each fixture's command/begin boundary to component completion. These intervals include input feeding and bounded ingress/memory service. They differ from the milestone interval of last accepted outer byte to validated parent commit in LIVE and cannot adjudicate that milestone. No achieved FPGA clock is implied. LIVE currently tests a single `actual_001` key-frame/recovery fixture; broader gameplay and stalled-service coverage remain necessary. These results also do not establish sustained hardware30fps, ESP32 execution, Sunshine integration, physical QSPI/SDRAM behavior or display output.

Selected full-component receipt: `experiments/python-gamebub-v118/integrated-study/spatial/attempts/20261109T144734759289Z/receipt.json`. Independent190-check audit: `experiments/python-gamebub-v118/audit/full-terminal-expert.json`. Full-parent LIVE publication, routed timing and hardware measurements are separate qualification stages.
